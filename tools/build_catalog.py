#!/usr/bin/env python3
"""Build the catalog manifest (catalog.json) and the mkdocs site pages from
the GenBank parts in ``parts/``.

Standalone: depends only on BioPython — the catalog repo is
self-contained. A part is one ``.gb`` file (a single main feature with no
``/parent`` qualifier, plus optional sub-features carrying ``/parent``) and an
optional sibling ``<stem>.md`` documentation page.

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
    "    This catalog is a **work in progress** and much of its content "
    "(part annotations and documentation pages) is **largely AI-generated**. "
    "It may contain errors and has not been fully expert-reviewed — verify "
    "any part against the cited primary literature before relying on it.\n"
)

ROOT = Path(__file__).resolve().parent.parent
PARTS_DIR = ROOT / "parts"
# Parts are split by curation status: ``validated`` parts carry a ``.md``
# documentation page and are published to the website; ``candidate`` parts are
# ``.gb``-only and live in the repo / catalog.json but are not on the site.
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
    """External-resource links derived from a coding part's source accession.

    A UniProt accession links to UniProt + the AlphaFold structure + the
    InterPro family; an NCBI accession links to NCBI Protein. Empty if no
    accession.
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
    else:
        links = [f"[NCBI Protein](https://www.ncbi.nlm.nih.gov/protein/{ident})"]
    return " · ".join(links)


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
    """Link to a related part's page when it is validated (has a page), else
    show its name as plain text."""
    if item.get("slug") and item.get("documented"):
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


def _tags_for(part: dict) -> list[str]:
    """Facet tags for a part page (material/tags): its type, plus — for a
    promoter — one ``regulated by <TF>`` tag per cognate regulator, and a
    ``Transcription factors`` tag for any part that regulates one."""
    tags = [_group_key(part)[1]]
    for x in part.get("regulated_by") or []:
        nm = x["name"] if isinstance(x, dict) else x
        tags.append(f"regulated by {nm}")
    if part.get("regulates"):
        tags.append("Transcription factors")
    for c in part.get("collections_resolved") or []:
        tags.append(f"Collection: {c['name']}")
    # de-dup, preserve order
    seen: set[str] = set()
    return [t for t in tags if not (t in seen or seen.add(t))]


def _frontmatter(tags: list[str]) -> str:
    if not tags:
        return ""
    return "---\ntags:\n" + "".join(f"  - {t}\n" for t in tags) + "---\n\n"


def render_part_page(part: dict) -> str:
    slug, name = part["slug"], part["name"]
    syn = (" · synonyms: " + ", ".join(part["synonyms"])) if part["synonyms"] else ""
    so = part.get("so_term")
    so_part = f" · {_so_link(so, part.get('so_name'))}" if so else ""
    fasta_label = "Download protein FASTA" if part.get("kind") == "protein" else "Download FASTA"
    head = [
        f"# {name}\n",
        f"`{part['feature_type']}`{so_part} · {_len_label(part)}{syn}\n",
        f"[Download GenBank](files/{slug}.gb){{ .md-button }} "
        f"[{fasta_label}](files/{slug}.fasta){{ .md-button }}\n",
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
        build_molecule_json(VALIDATED_DIR / f"{slug}.gb")).replace("<", "\\u003c")
    head.append(
        f'<div data-part-view data-height="360">'
        f'<script type="application/json">{mol_json}</script></div>\n')
    fm = _frontmatter(_tags_for(part))
    md_path = VALIDATED_DIR / f"{slug}.md"
    contrib = "https://github.com/dbikard/dna-parts-catalog/blob/main/CONTRIBUTING.md"
    if part["documented"]:
        body = md_path.read_text(encoding="utf-8").strip() + "\n"
        # Structured feature table up top, then the curated prose (which carries
        # its own References section).
        return (fm + "\n".join(head) + "\n" + AI_WIP_WARNING + "\n"
                + _related_section(part) + "\n"
                + _feature_table(part) + "\n" + body)
    note = part["description"] or "_No curated documentation page yet._"
    note += (f"\n\n*This part has no curated documentation yet — "
             f"[contribute one]({contrib}).*\n")
    return (fm + "\n".join(head) + "\n" + AI_WIP_WARNING + "\n" + note + "\n"
            + _related_section(part) + "\n"
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


def _grouped(validated: list[dict]) -> list[tuple[tuple[str, str], list[dict]]]:
    """Validated parts grouped by type ((key, label) -> parts), in canonical
    display order (known SO terms first, then unknowns alphabetically)."""
    groups: dict[tuple[str, str], list[dict]] = {}
    for p in validated:
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
        "# DNA parts catalog\n",
        AI_WIP_WARNING,
        f"An open, community-curated catalog of standard DNA parts (promoters, "
        f"CDSs, terminators, RBSs, …) as annotated GenBank files, organised by "
        f"type. The **{n_validated}** *validated* parts each carry a curated "
        f"documentation page; use the search box to find one by name.\n",
        f"A further **{n_candidate}** *candidate* parts (annotated GenBank, "
        f"awaiting a curated documentation page) are available in "
        f"[`catalog.json`]({repo}/blob/main/catalog.json) and the "
        f"[`parts/candidate/`]({repo}/tree/main/parts/candidate) directory.\n",
        "## Browse by type\n",
    ]
    for (key, label), ps in grouped:
        so_note = (f" · {_so_link(key, _SO_NAMES.get(key) or label)}"
                   if key.startswith("SO:") else "")
        lines.append(f"- **[{label}](types/{_type_slug(label)}.md)** — "
                     f"{len(ps)} part{'s' if len(ps) != 1 else ''}{so_note}")
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
    """A page listing every validated part of one type, with descriptions."""
    lines = [
        f"# {label}\n",
        f"{_so_caption(key, label, len(parts))} · [← all types](../index.md)\n",
        "| Part | Description | Length |",
        "|---|---|---|",
    ]
    for p in sorted(parts, key=lambda x: x["name"].lower()):
        lines.append(f"| [{p['name']}](../parts/{p['slug']}.md) | "
                     f"{_short(p.get('description', ''))} | {_len_label(p)} |")
    return "\n".join(lines) + "\n"


def render_tags_page() -> str:
    """The faceted tag index. The ``material/tags`` marker tells the plugin
    where to render the per-tag listing."""
    return ("# Tags\n\n"
            "Browse parts by tag — the part **type**, and, for promoters, the "
            "**transcription factor** that regulates them.\n\n"
            "<!-- material/tags -->\n")


def _collection_member_link(part: dict) -> str:
    """Link a collection member to its part page when validated, else to its
    GenBank file in the repo (candidates have no published page)."""
    if part["status"] == "validated":
        return f"[{part['name']}](../parts/{part['slug']}.md)"
    url = f"{REPO_URL}/blob/main/parts/candidate/{part['slug']}.gb"
    return f"[{part['name']}]({url})"


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

    # Manifest covers every part (validated + candidate); internal fields stripped.
    _internal = {"_seq", "collections_resolved"}
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "n_parts": len(parts),
        "n_validated": sum(p["status"] == "validated" for p in parts),
        "n_candidate": sum(p["status"] == "candidate" for p in parts),
        "n_documented": sum(p["documented"] for p in parts),
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

    # Website publishes validated parts only (pages + downloadable files):
    # a landing hub, one page per type, one page per part, and a tag index.
    validated = [p for p in parts if p["status"] == "validated"]
    n_candidate = manifest["n_candidate"]
    grouped = _grouped(validated)
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
    for p in validated:
        (PARTS_PAGES / f"{p['slug']}.md").write_text(render_part_page(p),
                                                     encoding="utf-8")
        shutil.copyfile(VALIDATED_DIR / f"{p['slug']}.gb", FILES_DIR / f"{p['slug']}.gb")
        (FILES_DIR / f"{p['slug']}.fasta").write_text(
            _fasta(p["name"], p["_seq"]), encoding="utf-8")

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
