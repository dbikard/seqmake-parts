#!/usr/bin/env python3
"""Build the catalog manifest (catalog.json) and the mkdocs site pages from
the GenBank parts in ``parts/``.

The manifest is built with BioPython alone; building the site additionally emits
a per-part RDF download, which uses ``rdflib`` via ``build_rdf`` (lazy-imported).
A part is one ``.gb`` file (a single main feature with no ``/parent`` qualifier,
plus optional sub-features carrying ``/parent``) and an optional sibling
``<stem>.md`` documentation page.

Usage:
    python tools/build_catalog.py            # writes catalog.json + docs/
"""
from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

from Bio import SeqIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from so_terms import SO_BY_REG, SO_BY_TYPE, so_for  # noqa: E402

SCHEMA_VERSION = "1.0"

# Shown at the top of the site index and every part page. The catalog is a
# work in progress and much of its content (annotations, documentation prose)
# is AI-generated, so flag it prominently for anyone browsing.
AI_WIP_WARNING = (
    '!!! warning "Work in progress — AI-generated content"\n\n'
    "    This knowledge base is a **work in progress** and much of its content "
    "(part annotations, documentation, and functional claims) is **largely "
    "AI-generated**. It may contain errors and has not been fully expert-reviewed "
    "— verify any part against the cited primary literature before relying on it.\n"
)

ROOT = Path(__file__).resolve().parent.parent
PARTS_DIR = ROOT / "parts"
# Parts are split by curation status: ``validated`` parts carry a ``.md``
# documentation page; ``candidate`` parts await one. Both are published to the
# website -- validated with their curated prose, candidates as a lightweight
# auto-generated page (viewer + features + downloads).
VALIDATED_DIR = PARTS_DIR / "validated"
CANDIDATE_DIR = PARTS_DIR / "candidate"
DOCS_DIR = ROOT / "docs"
PARTS_PAGES = DOCS_DIR / "parts"
FILES_DIR = PARTS_PAGES / "files"
# One page per part type (grouped on SO accession), reached from the index and
# the left nav; plus a faceted tag index (material/tags).
TYPES_PAGES = DOCS_DIR / "types"
TAGS_FILE = DOCS_DIR / "tags.md"
# Collections group RELATED parts (a vector family, a promoter series, an
# inducible-sensor set) across types. Membership is self-declared on each part
# via a /collection qualifier on its main feature; collections.json supplies
# each collection's display name + description + source (prose only — NOT
# membership, which always lives with the parts).
COLLECTIONS_PAGES = DOCS_DIR / "collections"
COLLECTIONS_FILE = ROOT / "collections.json"
REPO_URL = "https://github.com/dbikard/dna-parts-catalog"

# SO accession -> name, for reverse lookup when a feature carries an explicit
# /db_xref="SO:...". The type/regulatory_class -> SO mapping itself lives in
# so_terms (shared with publish_part so the read and write sides can't drift);
# +1/TSS and Shine-Dalgarno are derive-only / explicit-only and added here only
# for the reverse lookup.
_SO_NAMES = {acc: name for d in (SO_BY_REG, SO_BY_TYPE) for acc, name in d.values()}
_SO_NAMES.update({"SO:0000315": "TSS", "SO:0000552": "Shine_Dalgarno_sequence"})


def _so_term(feature):
    """(SO accession, SO name) for a feature: an explicit /db_xref="SO:..." wins,
    else derive from the feature type / regulatory_class / label."""
    for x in feature.qualifiers.get("db_xref", []):
        if str(x).startswith("SO:"):
            return str(x), _SO_NAMES.get(str(x), "")
    rc = (feature.qualifiers.get("regulatory_class") or [None])[0]
    label = (feature.qualifiers.get("label") or [""])[0]
    return so_for(feature.type, rc, label) or (None, None)


def _pmid_url(pmid: str) -> str:
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _ref_url(ref: dict) -> str | None:
    if ref.get("pmid"):
        return _pmid_url(ref["pmid"])
    if ref.get("doi"):
        return f"https://doi.org/{ref['doi']}"
    return None


def _parse_references(record) -> list[dict]:
    """Turn BioPython REFERENCE blocks into citation dicts (1-based order)."""
    out = []
    for r in record.annotations.get("references", []):
        doi = ""
        m = re.search(r"doi:\s*(\S+)", getattr(r, "comment", "") or "", re.I)
        if m:
            doi = m.group(1).rstrip(".")
        pmid = (getattr(r, "pubmed_id", "") or "").strip()
        ref = {"authors": r.authors or "", "title": r.title or "",
               "journal": r.journal or "", "pmid": pmid, "doi": doi}
        ref["url"] = _ref_url(ref)
        out.append(ref)
    return out


def _citation_indices(qualifiers) -> list[int]:
    """`/citation=['[1]', '[2]']` -> [1, 2] (1-based reference indices)."""
    idx = []
    for c in qualifiers.get("citation", []):
        m = re.search(r"\d+", str(c))
        if m:
            idx.append(int(m.group()))
    return idx


def parse_part(gb_path: Path) -> dict | None:
    record = SeqIO.read(str(gb_path), "genbank")
    seq = str(record.seq).upper()
    main = next((f for f in record.features if "parent" not in f.qualifiers), None)
    if main is None:
        return None
    q = main.qualifiers
    name = (q.get("label") or [record.name or gb_path.stem])[0]
    # A protein-only coding part stores its amino-acid sequence directly; its
    # sub-feature coords are residues, and length is reported in aa.
    is_protein = bool(seq) and bool(set(seq) - set("ACGTUN"))
    source_accession = next(
        (str(x) for x in q.get("db_xref", []) if not str(x).startswith("SO:")), None)
    refs = _parse_references(record)
    children = []
    for f in record.features:
        if "parent" not in f.qualifiers:
            continue
        so_id, so_name = _so_term(f)
        children.append({
            "label": (f.qualifiers.get("label") or [""])[0],
            "feature_type": f.type,
            "so_term": so_id,
            "so_name": so_name,
            "start": int(f.location.start),
            "end": int(f.location.end),
            "strand": 1 if f.location.strand in (None, 1) else -1,
            "citations": _citation_indices(f.qualifiers),
        })
    md_path = gb_path.with_suffix(".md")
    documented = md_path.exists()
    main_so_id, main_so_name = _so_term(main)
    return {
        "name": name,
        "slug": gb_path.stem,
        "feature_type": main.type,
        "kind": "protein" if is_protein else "dna",
        "source_accession": source_accession,
        "so_term": main_so_id,
        "so_name": main_so_name,
        "synonyms": list(q.get("synonym", [])),
        # Collection membership is self-declared on the part's main feature
        # (one /collection per family it belongs to); prose comes from
        # collections.json. Resolved to display names in main().
        "collections": [str(x) for x in q.get("collection", [])],
        "description": (q.get("note") or [""])[0],
        "length": len(seq),
        "protein_length_aa": len(seq) if is_protein else None,
        # Cognate regulator(s): a promoter names the TF part(s) that control it
        # via /regulated_by; build_catalog resolves these + derives the inverse
        # ("regulates") on the TF's entry. Raw names here; resolved in main().
        "regulated_by": list(q.get("regulated_by", [])),
        "regulates": [],
        "documented": documented,
        "status": "validated" if documented else "candidate",
        "children": children,
        "references": refs,
        "main_citations": _citation_indices(q),
        "_seq": seq,  # stripped before serialising the manifest
    }


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def _fasta(name: str, seq: str) -> str:
    body = "\n".join(seq[i:i + 70] for i in range(0, len(seq), 70))
    return f">{name}\n{body}\n"


def _cite_links(indices: list[int], refs: list[dict]) -> str:
    out = []
    for i in indices:
        if 1 <= i <= len(refs):
            r = refs[i - 1]
            label = f"PMID {r['pmid']}" if r["pmid"] else (r["doi"] or f"ref {i}")
            out.append(f"[{label}]({r['url']})" if r.get("url") else label)
    return ", ".join(out)


def _revcomp(s: str) -> str:
    return s.translate(str.maketrans("ACGTacgt", "TGCAtgca"))[::-1]


def build_molecule_json(gb_path: Path) -> dict:
    """Serialize a part's GenBank record into the viewer's ``MoleculeInfo``
    shape — the contract the embedded part-view widget renders (sequence +
    features in feature coordinates). A protein part carries ``kind:
    'protein'`` and no crick strand; a DNA part gets the reverse-complement
    crick. Feature colors are omitted (the widget derives them from the type).
    """
    record = SeqIO.read(str(gb_path), "genbank")
    seq = str(record.seq).upper()
    is_protein = bool(seq) and bool(set(seq) - set("ACGTUN"))
    features = []
    for f in record.features:
        if f.type == "source":
            continue
        feat = {
            "type": f.type,
            "start": int(f.location.start),
            "end": int(f.location.end),
            "strand": -1 if f.location.strand == -1 else 1,
            "label": (f.qualifiers.get("label") or [f.type])[0],
            "qualifiers": {k: [str(x) for x in v] for k, v in f.qualifiers.items()},
        }
        parent = (f.qualifiers.get("parent") or [None])[0]
        if parent:
            feat["parent"] = parent  # main feature stays parent-less
        features.append(feat)
    main = next((f for f in features if "parent" not in f), None)
    return {
        "name": main["label"] if main else (record.name or gb_path.stem),
        "kind": "protein" if is_protein else "dna",
        "topology": "linear",
        "watson": seq,
        "crick": "" if is_protein else _revcomp(seq),
        "length_bp": len(seq),
        "strand_state": "single" if is_protein else "double",
        "features": features,
    }


def _so_link(so_id, so_name) -> str:
    if not so_id:
        return "—"
    url = f"http://sequenceontology.org/browser/current_release/term/{so_id}"
    return f"[{so_name or so_id}]({url})"


def _len_label(part: dict) -> str:
    """"NNN aa" for a protein part, "NNN bp" for a DNA part."""
    return f"{part['length']} {'aa' if part.get('kind') == 'protein' else 'bp'}"


def _resource_links(acc: str | None) -> str:
    """External-resource links derived from a part's source accession.

    A UniProt accession links to UniProt + the AlphaFold structure + the
    InterPro family; a GenBank/nucleotide accession links to NCBI Nucleotide
    (the deposited sequence record); any other NCBI accession links to NCBI
    Protein. Empty if no accession.
    """
    if not acc:
        return ""
    db, _, ident = acc.partition(":")
    if not ident:
        ident, db = db, ""
    if db.lower() == "uniprot":
        links = [
            f"[UniProt](https://www.uniprot.org/uniprotkb/{ident})",
            f"[AlphaFold](https://alphafold.ebi.ac.uk/entry/{ident})",
            f"[InterPro](https://www.ebi.ac.uk/interpro/protein/UniProt/{ident}/)",
        ]
    elif db.lower() in ("genbank", "nuccore", "insdc"):
        links = [f"[GenBank](https://www.ncbi.nlm.nih.gov/nuccore/{ident})"]
    else:
        links = [f"[NCBI Protein](https://www.ncbi.nlm.nih.gov/protein/{ident})"]
    return " · ".join(links)


def _load_uniprot_import(part: dict) -> dict:
    """A protein part's uniprot_import provenance block from its canonical JSON."""
    json_path = PARTS_DIR / part["status"] / f"{part['slug']}.json"
    if not json_path.exists():
        return {}
    return json.loads(json_path.read_text(encoding="utf-8")).get("uniprot_import") or {}


def _protein_defer_note(part: dict) -> str:
    """For a protein part, point to UniProt for residue-level biology instead of
    duplicating it, and flag when the part's sequence diverges from UniProt's
    canonical (so the imported coordinates' caveats are visible)."""
    if part.get("kind") != "protein" or not part.get("source_accession"):
        return ""
    imp = _load_uniprot_import(part)
    status = imp.get("status")
    acc = part["source_accession"]
    idpct = f"{imp.get('identity', 0) * 100:.0f}% identity" if imp.get("identity") is not None else ""
    if status == "wrong_accession":
        return ('!!! danger "Accession likely wrong"\n\n'
                f"    This part's sequence matches **{acc}** at only {idpct} — it "
                "appears to be a *different protein*, i.e. the accession is probably "
                "wrong. No features were imported; this needs review.\n")
    if status == "length_variant":
        return ('!!! warning "Sequence differs from UniProt (length)"\n\n'
                f"    Same protein as {acc} but a different length "
                f"({imp.get('part_len')} vs {imp.get('uniprot_len')} aa, {idpct}) — "
                "an isoform/fragment, so features were **not** imported (coordinates "
                "would shift). See the linked UniProt entry.\n")
    if status == "divergent":
        return ('!!! warning "Diverges from UniProt"\n\n'
                f"    This part is a distant allele/homolog of {acc} ({idpct}); "
                "features were **not** imported — review whether the accession is "
                "right. See the linked UniProt entry.\n")
    if status == "reaccessioned":
        prev = imp.get("previous_accession", "")
        return ('!!! note "Accession corrected"\n\n'
                f"    This part's sequence is an exact match to **{acc}**, so the "
                f"accession was corrected from {prev}. Domains / sites below are "
                "imported from the matching UniProt entry.\n")
    if status == "normalized_to_canonical":
        n = len(imp.get("normalized_substitutions") or [])
        return ('!!! note "Sequence normalized to UniProt"\n\n'
                f"    This part's sequence was set to the {acc} canonical sequence "
                f"(an incidental close variant, {n} residue(s) differed); domains / "
                "sites below are imported from that entry.\n")
    if status == "variant":
        vs = imp.get("variants") or []
        subs = ", ".join(f"{v['uniprot']}{v['pos']}{v['part']}" for v in vs[:6])
        more = "…" if len(vs) > 6 else ""
        rat = imp.get("variant_rationale")
        rat_s = f" — *{rat}*" if rat else ""
        return ('!!! note "Protein features from UniProt (kept variant)"\n\n'
                "    Domains / sites below are **imported from the linked UniProt "
                f"entry**; this part is an intentional variant of {acc} ({idpct}; "
                f"substitutions: {subs}{more}){rat_s}. See UniProt / InterPro / "
                "AlphaFold for the authoritative set.\n")
    return ('!!! note "Protein features from UniProt"\n\n'
            "    Any domains / sites below are **imported from the linked UniProt "
            "entry** (a cached projection, not hand-authored); see UniProt, "
            "InterPro and AlphaFold for the authoritative, complete set and "
            "structure.\n")


def _feature_table(part: dict) -> str:
    if not part["children"]:
        return ""
    seq, refs = part["_seq"], part["references"]
    lines = ["## Sub-features\n",
             "| Element | Type | SO | Position | Strand | Sequence | Citations |",
             "|---|---|---|---|---|---|---|"]
    for c in part["children"]:
        s, e = c["start"], c["end"]
        sub = seq[s:e]
        if c["strand"] == -1:
            sub = _revcomp(sub)
        strand = "+" if c["strand"] == 1 else "−"
        lines.append(f"| {c['label']} | `{c['feature_type']}` | "
                     f"{_so_link(c.get('so_term'), c.get('so_name'))} | {s + 1}..{e} | "
                     f"{strand} | `{sub}` | {_cite_links(c['citations'], refs)} |")
    return "\n".join(lines) + "\n"


def _load_claims(part: dict) -> list[dict]:
    """A part's functional_claims from its canonical JSON (empty if none)."""
    json_path = PARTS_DIR / part["status"] / f"{part['slug']}.json"
    if not json_path.exists():
        return []
    return json.loads(json_path.read_text(encoding="utf-8")).get("functional_claims", [])


def _functional_knowledge(part: dict) -> str:
    """The functional-knowledge section: prose-derived claims (from the canonical
    JSON), each shown with its granular source (quote/figure), confidence and
    review status -- the human view of the nanopublication-shaped layer."""
    claims = _load_claims(part)
    if not claims:
        return ""
    lines = ["## Functional knowledge\n",
             "*Prose-derived claims, each carrying its source, confidence and "
             "review status (a nanopublication-shaped assertion). Verify against "
             "the cited source.*\n",
             "| Claim | Source | Confidence | Review |",
             "|---|---|---|---|"]
    for c in claims:
        src = c.get("source") or {}
        bits = []
        if src.get("pmid"):
            bits.append(f"[PMID {src['pmid']}]({_pmid_url(src['pmid'])})")
        elif src.get("doi"):
            bits.append(f"[doi:{src['doi']}](https://doi.org/{src['doi']})")
        elif src.get("url"):
            bits.append(f"[link]({src['url']})")
        for k, lab in (("figure", "Fig"), ("table", "Table"),
                       ("page", "p."), ("section", "§")):
            if src.get(k):
                bits.append(f"{lab} {src[k]}")
        cell = " · ".join(bits)
        if src.get("quote"):
            tag = f" ({src['quote_source']})" if src.get("quote_source") else ""
            cell += f"<br>*“{_short(src['quote'], 120)}”{tag}*"
        lines.append(f"| {_short(c.get('label', ''), 140)} | {cell or '—'} | "
                     f"{c.get('confidence', '—')} | {c.get('review_status', '—')} |")
    return "\n".join(lines) + "\n"


def _reference_list(refs: list[dict]) -> str:
    if not refs:
        return ""
    lines = ["## References\n"]
    for i, r in enumerate(refs, 1):
        cite = f"{r['authors']}. *{r['title']}.* {r['journal']}".strip(". ")
        link = f" [PMID {r['pmid']}]({_pmid_url(r['pmid'])})" if r["pmid"] else (
            f" [doi:{r['doi']}](https://doi.org/{r['doi']})" if r["doi"] else "")
        lines.append(f"{i}. {cite}.{link}")
    return "\n".join(lines) + "\n"


def _crosslink_parts(parts: list[dict]) -> None:
    """Resolve each part's /regulated_by names to catalog parts and derive the
    inverse ("regulates") on the named regulator. Modifies parts in place; an
    unresolved name is kept (rendered as plain text, not a link)."""
    by_name: dict[str, dict] = {}
    for p in parts:
        by_name.setdefault(p["name"].lower(), p)
        for s in p["synonyms"]:
            by_name.setdefault(s.lower(), p)
    for p in parts:
        resolved = []
        for tf in p["regulated_by"]:
            t = by_name.get(tf.lower())
            resolved.append({"name": tf, "slug": t["slug"] if t else None,
                             "documented": bool(t and t["documented"])})
            if t:
                t["regulates"].append({"name": p["name"], "slug": p["slug"],
                                       "documented": p["documented"]})
        p["regulated_by"] = resolved


def _xlink(item: dict) -> str:
    """Link to a related part's page (validated and candidate parts both have
    one); a name not in the catalog at all (no slug) stays plain text."""
    if item.get("slug"):
        return f"[{item['name']}]({item['slug']}.md)"
    return item["name"]


def _related_section(part: dict) -> str:
    rb, rg = part.get("regulated_by") or [], part.get("regulates") or []
    if not rb and not rg:
        return ""
    lines = ["## Related parts\n"]
    if rb:
        lines.append("**Regulated by:** " + " · ".join(_xlink(x) for x in rb) + "\n")
    if rg:
        rgs = sorted(rg, key=lambda i: i["name"].lower())
        lines.append("**Regulates:** " + " · ".join(_xlink(x) for x in rgs) + "\n")
    return "\n".join(lines) + "\n"


def _function_tags(part: dict) -> list[str]:
    """Browse-by-function facet tags derived from a part's functional_claims:
    regulation mode, inducer, selection marker, and copy number."""
    tags: list[str] = []
    for c in _load_claims(part):
        v = c.get("value") or {}
        reg = v.get("regulation")
        if reg:
            tags.append(reg.capitalize())          # Inducible / Constitutive
        if v.get("inducer"):
            tags.append(f"Inducer: {v['inducer']}")
        if v.get("function") == "antibiotic resistance" or c.get("type") == "function":
            tags.append("Selection marker")
        if v.get("copy_number"):
            tags.append(f"Copy number: {v['copy_number']}")
    return tags


def _tags_for(part: dict) -> list[str]:
    """Facet tags for a part page (material/tags): its type; for a promoter one
    ``regulated by <TF>`` tag per cognate regulator and a ``Transcription
    factors`` tag for any part that regulates one; its collections; and
    browse-by-function tags from its functional claims."""
    tags = [_group_key(part)[1]]
    for x in part.get("regulated_by") or []:
        nm = x["name"] if isinstance(x, dict) else x
        tags.append(f"regulated by {nm}")
    if part.get("regulates"):
        tags.append("Transcription factors")
    for c in part.get("collections_resolved") or []:
        tags.append(f"Collection: {c['name']}")
    tags += _function_tags(part)
    if _load_uniprot_import(part).get("status") in ("wrong_accession", "divergent"):
        tags.append("UniProt accession review")
    # de-dup, preserve order
    seen: set[str] = set()
    return [t for t in tags if not (t in seen or seen.add(t))]


def _frontmatter(tags: list[str]) -> str:
    if not tags:
        return ""
    # Quote each tag so YAML-special characters (notably the ``:`` in a
    # ``Collection: <name>`` tag) stay a plain string, not a nested mapping.
    def _q(t: str) -> str:
        return '"' + t.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return "---\ntags:\n" + "".join(f"  - {_q(t)}\n" for t in tags) + "---\n\n"


def render_part_page(part: dict) -> str:
    slug, name = part["slug"], part["name"]
    part_dir = VALIDATED_DIR if part["status"] == "validated" else CANDIDATE_DIR
    syn = (" · synonyms: " + ", ".join(part["synonyms"])) if part["synonyms"] else ""
    so = part.get("so_term")
    so_part = f" · {_so_link(so, part.get('so_name'))}" if so else ""
    status_note = "" if part["documented"] else " · _candidate_"
    fasta_label = "Download protein FASTA" if part.get("kind") == "protein" else "Download FASTA"
    head = [
        f"# {name}\n",
        f"`{part['feature_type']}`{so_part} · {_len_label(part)}{status_note}{syn}\n",
        f"[Download GenBank](files/{slug}.gb){{ .md-button }} "
        f"[{fasta_label}](files/{slug}.fasta){{ .md-button }} "
        f"[Download RDF](files/{slug}.ttl){{ .md-button }}\n",
    ]
    res = _resource_links(part.get("source_accession"))
    if res:
        head.append(f"**{part['source_accession']}** · {res}\n")
    colls = part.get("collections_resolved") or []
    if colls:
        links = " · ".join(f"[{c['name']}](../collections/{c['id']}.md)" for c in colls)
        head.append(f"**Collection{'s' if len(colls) != 1 else ''}:** {links}\n")
    # Interactive feature/sequence view, hydrated by the embedded part-view
    # widget. The MoleculeInfo is inlined as a JSON child (parts are small) so
    # it needs no fetch and is robust to the site's base path / directory URLs.
    # `<` is escaped so a qualifier can never break out of the script tag.
    # Renders DNA and protein parts alike.
    mol_json = json.dumps(
        build_molecule_json(part_dir / f"{slug}.gb")).replace("<", "\\u003c")
    head.append(
        f'<div data-part-view data-height="360">'
        f'<script type="application/json">{mol_json}</script></div>\n')
    fm = _frontmatter(_tags_for(part))
    md_path = part_dir / f"{slug}.md"
    contrib = "https://github.com/dbikard/dna-parts-catalog/blob/main/CONTRIBUTING.md"
    if part["documented"]:
        body = md_path.read_text(encoding="utf-8").strip() + "\n"
        # Structured feature table up top, then the curated prose (which carries
        # its own References section).
        return (fm + "\n".join(head) + "\n" + AI_WIP_WARNING + "\n"
                + _related_section(part) + "\n"
                + _functional_knowledge(part) + "\n"
                + _protein_defer_note(part) + "\n"
                + _feature_table(part) + "\n" + body)
    note = part["description"] or "_No curated documentation page yet._"
    note += (f"\n\n*This part has no curated documentation yet — "
             f"[contribute one]({contrib}).*\n")
    return (fm + "\n".join(head) + "\n" + AI_WIP_WARNING + "\n" + note + "\n"
            + _related_section(part) + "\n"
            + _functional_knowledge(part) + "\n"
            + _protein_defer_note(part) + "\n"
            + _feature_table(part) + "\n" + _reference_list(part["references"]))


# The index groups parts by type, keyed on the SO accession (a controlled
# vocabulary — normalises inconsistent GenBank feature_type strings). This is
# the canonical display order + friendly plural label per SO term; unlisted SO
# terms fall back to their SO name and sort after these, alphabetically.
_TYPE_DISPLAY: list[tuple[str, str]] = [
    ("SO:0000167", "Promoters"),
    ("SO:0000057", "Operators"),
    ("SO:0000139", "Ribosome binding sites"),
    ("SO:0000316", "Coding sequences"),
    ("SO:0000417", "Protein domains"),
    ("SO:0000141", "Terminators"),
    ("SO:0000296", "Origins of replication"),
    ("SO:0000724", "Origins of transfer (oriT)"),
    ("SO:0000410", "Protein binding sites"),
    ("SO:0000655", "Non-coding RNAs"),
    ("SO:0000110", "Other features"),
]
_TYPE_ORDER = {so: i for i, (so, _) in enumerate(_TYPE_DISPLAY)}
_TYPE_LABEL = dict(_TYPE_DISPLAY)


def _group_key(part: dict) -> tuple[str, str]:
    """(grouping key, display label) for a part: group on the SO accession when
    present (canonical), else on the raw feature type."""
    so = part.get("so_term")
    if so:
        label = _TYPE_LABEL.get(so) or (part.get("so_name") or "Other").replace("_", " ").capitalize()
        return so, label
    ft = part.get("feature_type") or "other"
    return f"ft:{ft}", ft.replace("_", " ").capitalize()


def _anchor(text: str) -> str:
    """Slugify a heading the way python-markdown's toc does, so in-page jump
    links resolve."""
    s = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", s)


def _short(text: str, n: int = 80) -> str:
    text = (text or "").replace("|", "\\|").strip()
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


def _type_slug(label: str) -> str:
    """Filename slug for a type page (``Origins of replication`` ->
    ``origins-of-replication``), matching the index/nav links."""
    return _anchor(label)


def _grouped(parts: list[dict]) -> list[tuple[tuple[str, str], list[dict]]]:
    """Parts grouped by type ((key, label) -> parts), in canonical display order
    (known SO terms first, then unknowns alphabetically)."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for p in parts:
        groups.setdefault(_group_key(p), []).append(p)
    return sorted(
        groups.items(),
        key=lambda kv: (_TYPE_ORDER.get(kv[0][0], len(_TYPE_ORDER)), kv[0][1].lower()),
    )


def _so_caption(key: str, label: str, n: int) -> str:
    so_note = f"{_so_link(key, _SO_NAMES.get(key) or label)} · " if key.startswith("SO:") else ""
    return f"*{so_note}{n} part{'s' if n != 1 else ''}*"


def render_index(grouped, n_validated: int, n_candidate: int,
                 collections_summary: list[dict]) -> str:
    """The catalog landing page: intro + a 'Browse by type' hub linking each
    type's page, a 'Browse by collection' hub, plus a pointer to the tag index."""
    repo = REPO_URL
    lines = [
        "# Biological Parts Knowledge Base\n",
        AI_WIP_WARNING,
        f"A machine-readable knowledge base of standard biological parts — "
        f"promoters, CDSs, terminators, RBSs, origins, selection markers and "
        f"regulators — each an annotated record with Sequence Ontology typing, "
        f"literature-sourced functional claims, and links into UniProt. "
        f"**{n_validated}** parts carry a curated page; a further **{n_candidate}** "
        f"are auto-generated from annotated GenBank, awaiting curation. Every claim "
        f"carries its source and a review status — verify against the cited "
        f"literature before relying on it.\n",
        "## Use the data\n",
        f"- **[`catalog.json`]({repo}/blob/main/catalog.json)** — the full manifest "
        f"(every part, its metadata, and functional claims).",
        "- **[`catalog.ttl`](catalog.ttl)** / **[`catalog.jsonld`](catalog.jsonld)** "
        "— the same data as an RDF graph (SBOL3 + Sequence Ontology + SBO), "
        "SPARQL-queryable and federatable with UniProt.",
        f"- **[SPARQL cookbook]({repo}/blob/main/QUERIES.md)** — worked example "
        f"queries; see [the data model]({repo}/blob/main/RDF.md) for the shape.",
        "- Each part page also offers GenBank / FASTA / RDF downloads.",
        "",
        "## Browse by type\n",
    ]
    for (key, label), ps in grouped:
        so_note = (f" · {_so_link(key, _SO_NAMES.get(key) or label)}"
                   if key.startswith("SO:") else "")
        nval = sum(p["status"] == "validated" for p in ps)
        extra = f" ({nval} validated)" if nval and nval != len(ps) else ""
        lines.append(f"- **[{label}](types/{_type_slug(label)}.md)** — "
                     f"{len(ps)} part{'s' if len(ps) != 1 else ''}{extra}{so_note}")
    lines.append("")
    if collections_summary:
        lines.append("## Browse by collection\n")
        lines.append("Related parts grouped into families — vector series, "
                     "promoter sets, inducible-sensor kits — typically used "
                     "together (a collection may mix validated and candidate parts):\n")
        for c in collections_summary:
            lines.append(f"- **[{c['name']}](collections/{c['id']}.md)** — "
                         f"{c['n']} part{'s' if c['n'] != 1 else ''}")
        lines.append("")
    lines.append("Looking for a specific property? Browse the [**tags**](tags.md) — "
                 "for example, every promoter controlled by a given transcription "
                 "factor.\n")
    return "\n".join(lines) + "\n"


def render_type_page(key: str, label: str, parts: list[dict]) -> str:
    """A page listing every part of one type (validated + candidate), with
    descriptions and curation status. Validated parts sort first."""
    nval = sum(p["status"] == "validated" for p in parts)
    caption = _so_caption(key, label, len(parts))
    if nval and nval != len(parts):
        caption = caption[:-1] + f", {nval} validated*"
    lines = [
        f"# {label}\n",
        f"{caption} · [← all types](../index.md)\n",
        "| Part | Description | Length | Status |",
        "|---|---|---|---|",
    ]
    order = sorted(parts, key=lambda x: (x["status"] != "validated", x["name"].lower()))
    for p in order:
        lines.append(f"| [{p['name']}](../parts/{p['slug']}.md) | "
                     f"{_short(p.get('description', ''))} | {_len_label(p)} | "
                     f"{p['status']} |")
    return "\n".join(lines) + "\n"


def render_tags_page() -> str:
    """The faceted tag index. The ``material/tags`` marker tells the plugin
    where to render the per-tag listing."""
    return ("# Tags\n\n"
            "Browse parts by tag — the part **type**; **function** (inducible / "
            "constitutive, inducer, selection marker, copy number); the "
            "**transcription factor** that regulates a promoter; and "
            "**collection** membership.\n\n"
            "<!-- material/tags -->\n")


def _collection_member_link(part: dict) -> str:
    """Link a collection member to its part page (validated and candidate parts
    both have one)."""
    return f"[{part['name']}](../parts/{part['slug']}.md)"


def _ref_url(r: dict) -> str | None:
    """Best URL for a collection reference: explicit url, else PubMed/DOI."""
    if r.get("url"):
        return r["url"]
    if r.get("pmid"):
        return f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
    if r.get("doi"):
        return f"https://doi.org/{r['doi']}"
    return None


def _format_reference(r: dict) -> str:
    """One collection reference as a markdown bullet: the title (linked to its
    URL/PubMed/DOI when available) followed by an authors / journal / year tail."""
    title = r.get("title") or r.get("doi") or r.get("pmid") or "reference"
    url = _ref_url(r)
    head = f"[{title}]({url})" if url else title
    tail = " · ".join(str(r[k]) for k in ("authors", "journal", "year") if r.get(k))
    return f"- {head}" + (f" — {tail}" if tail else "")


def _collection_resource_lines(meta: dict) -> list[str]:
    """`## References` (papers) and `## Resources` (external links) sections for
    a collection page; each is emitted only when collections.json supplies it."""
    out: list[str] = []
    refs = meta.get("references") or []
    if refs:
        out += ["", "## References\n", *(_format_reference(r) for r in refs)]
    res = meta.get("resources") or []
    if res:
        out += ["", "## Resources\n"]
        for x in res:
            url, title = x.get("url"), (x.get("title") or x.get("url"))
            out.append(f"- [{title}]({url})" if url else f"- {title}")
    return out


def render_collection_page(cid: str, meta: dict, members: list[dict]) -> str:
    """A page for one collection: intro prose + a table of every member part
    (validated members link to their page, candidates to their .gb), then any
    References (papers) and Resources (external links) from collections.json."""
    name = meta.get("name") or cid.replace("-", " ").capitalize()
    source = meta.get("source")
    n = len(members)
    nval = sum(p["status"] == "validated" for p in members)
    caption = f"{n} part{'s' if n != 1 else ''}"
    if nval:
        caption += f", {nval} validated"
    if source:
        caption += f" · {source}"
    lines = [f"# {name}\n", f"*{caption}* · [← all collections](index.md)\n",
             AI_WIP_WARNING]
    if meta.get("description"):
        lines.append(meta["description"] + "\n")
    lines += ["## Parts in this collection\n",
              "| Part | Type | Length | Status |", "|---|---|---|---|"]
    for p in sorted(members, key=lambda x: x["name"].lower()):
        lines.append(f"| {_collection_member_link(p)} | `{p['feature_type']}` | "
                     f"{_len_label(p)} | {p['status']} |")
    lines += _collection_resource_lines(meta)
    return "\n".join(lines) + "\n"


def render_collections_index(summary: list[dict], coll_meta: dict) -> str:
    """The collections hub: every collection with its part count + a blurb."""
    lines = ["# Collections\n",
             "Related parts grouped into families — vector series, promoter "
             "sets, inducible-sensor kits — that are typically used together. "
             "A collection can mix validated and candidate parts.\n"]
    for c in summary:
        meta = coll_meta.get(c["id"]) or {}
        src = f" · {meta['source']}" if meta.get("source") else ""
        desc = _short(meta.get("description", ""), 140)
        lines.append(f"- **[{c['name']}]({c['id']}.md)** — {c['n']} part"
                     f"{'s' if c['n'] != 1 else ''}{src}"
                     + (f"  \n  {desc}" if desc else ""))
    return "\n".join(lines) + "\n"


def main() -> None:
    parts, skipped = [], []
    # ``validated/`` parts must carry a .md; ``candidate/`` parts must not.
    for status_dir, expect_doc in ((VALIDATED_DIR, True), (CANDIDATE_DIR, False)):
        for gb in sorted(status_dir.glob("*.gb")):
            try:
                p = parse_part(gb)
            except Exception as exc:  # noqa: BLE001 - report and continue
                skipped.append(f"{gb.name}: {exc}")
                continue
            if p is None:
                skipped.append(gb.name)
                continue
            if p["documented"] != expect_doc:
                want = "validated/ (needs a .md)" if expect_doc else "candidate/ (no .md)"
                skipped.append(f"{gb.name}: misplaced — {p['status']} part in {want}")
                continue
            parts.append(p)

    # Resolve promoter<->TF cross-links + derive the inverse across all parts.
    _crosslink_parts(parts)

    # Collections: group related parts (membership self-declared via the
    # /collection qualifier); collections.json supplies display prose only.
    coll_meta = json.loads(COLLECTIONS_FILE.read_text(encoding="utf-8")) \
        if COLLECTIONS_FILE.exists() else {}
    collections: dict[str, list[dict]] = {}
    for p in parts:
        for cid in p.get("collections", []):
            collections.setdefault(cid, []).append(p)

    def _coll_name(cid: str) -> str:
        return (coll_meta.get(cid) or {}).get("name") or cid.replace("-", " ").capitalize()

    # Attach resolved (id, name) to each member for back-links + tags on its page.
    for cid, members in collections.items():
        for p in members:
            p.setdefault("collections_resolved", []).append(
                {"id": cid, "name": _coll_name(cid)})
    coll_summary = [{"id": cid, "name": _coll_name(cid), "n": len(ms)}
                    for cid, ms in sorted(collections.items())]

    # Attach the functional-knowledge layer (from each part's canonical JSON) so
    # the manifest carries it too -- parity with the RDF graph, for non-RDF
    # programmatic consumers.
    for p in parts:
        p["functional_claims"] = _load_claims(p)
        imp = _load_uniprot_import(p)
        if imp:
            p["uniprot_import"] = imp

    # Manifest covers every part (validated + candidate); internal fields stripped.
    _internal = {"_seq", "collections_resolved"}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "n_parts": len(parts),
        "n_validated": sum(p["status"] == "validated" for p in parts),
        "n_candidate": sum(p["status"] == "candidate" for p in parts),
        "n_documented": sum(p["documented"] for p in parts),
        "n_functional_claims": sum(len(p["functional_claims"]) for p in parts),
        "parts": [{k: v for k, v in p.items() if k not in _internal}
                  for p in sorted(parts, key=lambda x: x["name"].lower())],
        "collections": [
            {"id": cid, "name": _coll_name(cid),
             "source": (coll_meta.get(cid) or {}).get("source", ""),
             "references": (coll_meta.get(cid) or {}).get("references", []),
             "resources": (coll_meta.get(cid) or {}).get("resources", []),
             "n_parts": len(ms),
             "n_validated": sum(p["status"] == "validated" for p in ms),
             "members": [p["slug"] for p in sorted(ms, key=lambda x: x["name"].lower())]}
            for cid, ms in sorted(collections.items())],
    }
    (ROOT / "catalog.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                       encoding="utf-8")

    # The website publishes every part: validated parts carry curated prose,
    # candidates get a lightweight auto-generated page (viewer + features +
    # downloads). A landing hub, one page per type, one page per part, a tag index.
    n_candidate = manifest["n_candidate"]
    grouped = _grouped(parts)
    for d in (PARTS_PAGES, TYPES_PAGES, COLLECTIONS_PAGES):
        if d.exists():
            shutil.rmtree(d)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    TYPES_PAGES.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "index.md").write_text(
        render_index(grouped, manifest["n_validated"], n_candidate, coll_summary),
        encoding="utf-8")
    TAGS_FILE.write_text(render_tags_page(), encoding="utf-8")
    for (key, label), ps in grouped:
        (TYPES_PAGES / f"{_type_slug(label)}.md").write_text(
            render_type_page(key, label, ps), encoding="utf-8")
    # Collection pages (validated + candidate members) + a hub, when any exist.
    if collections:
        COLLECTIONS_PAGES.mkdir(parents=True, exist_ok=True)
        for cid, ms in sorted(collections.items()):
            (COLLECTIONS_PAGES / f"{cid}.md").write_text(
                render_collection_page(cid, coll_meta.get(cid) or {}, ms),
                encoding="utf-8")
        (COLLECTIONS_PAGES / "index.md").write_text(
            render_collections_index(coll_summary, coll_meta), encoding="utf-8")
    # Per-part RDF (Turtle) for the page download button; reuses the RDF builder
    # (lazy import avoids a circular import — build_rdf imports from this module).
    from build_rdf import part_turtle  # noqa: E402
    by_slug = {p["slug"]: p for p in parts}
    for p in parts:
        src_dir = VALIDATED_DIR if p["status"] == "validated" else CANDIDATE_DIR
        (PARTS_PAGES / f"{p['slug']}.md").write_text(render_part_page(p),
                                                     encoding="utf-8")
        shutil.copyfile(src_dir / f"{p['slug']}.gb", FILES_DIR / f"{p['slug']}.gb")
        (FILES_DIR / f"{p['slug']}.fasta").write_text(
            _fasta(p["name"], p["_seq"]), encoding="utf-8")
        (FILES_DIR / f"{p['slug']}.ttl").write_text(
            part_turtle(p, by_slug), encoding="utf-8")

    print(f"catalog: {len(parts)} parts "
          f"({manifest['n_validated']} validated, {n_candidate} candidate); "
          f"skipped {len(skipped)}")
    for s in skipped:
        print("  skipped:", s)
    # A skipped part means an unparseable or misplaced .gb — fail so CI catches it.
    if skipped:
        sys.exit(1)


if __name__ == "__main__":
    main()
