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

# Sequence Ontology accessions for GenBank feature types (verified against OLS4).
# A feature carries its SO term in catalog.json (read from a /db_xref="SO:..."
# if present, else derived here from the feature type / regulatory_class).
_SO_BY_REG = {
    "minus_35_signal": ("SO:0000175", "minus_35_signal"),
    "minus_10_signal": ("SO:0000176", "minus_10_signal"),
    "ribosome_binding_site": ("SO:0000139", "ribosome_entry_site"),
    "promoter": ("SO:0000167", "promoter"), "terminator": ("SO:0000141", "terminator"),
    "TATA_box": ("SO:0000174", "TATA_box"), "operator": ("SO:0000057", "operator"),
    "enhancer": ("SO:0000165", "enhancer"), "silencer": ("SO:0000625", "silencer"),
    "attenuator": ("SO:0000140", "attenuator"),
    "polyA_signal_sequence": ("SO:0000551", "polyA_signal_sequence"),
}
_SO_BY_TYPE = {
    "promoter": ("SO:0000167", "promoter"), "CDS": ("SO:0000316", "CDS"),
    "terminator": ("SO:0000141", "terminator"), "RBS": ("SO:0000139", "ribosome_entry_site"),
    "rep_origin": ("SO:0000296", "origin_of_replication"), "oriT": ("SO:0000724", "oriT"),
    "protein_bind": ("SO:0000410", "protein_binding_site"),
    "protein_domain": ("SO:0000417", "polypeptide_domain"),
    "misc_RNA": ("SO:0000655", "ncRNA"), "regulatory": ("SO:0005836", "regulatory_region"),
    "minus_35_signal": ("SO:0000175", "minus_35_signal"),
    "minus_10_signal": ("SO:0000176", "minus_10_signal"),
    "sig_peptide": ("SO:0000418", "signal_peptide"),
    "mat_peptide": ("SO:0000419", "mature_protein_region"),
    "gene": ("SO:0000704", "gene"), "misc_feature": ("SO:0000110", "sequence_feature"),
}
_SO_NAMES = {acc: name for d in (_SO_BY_REG, _SO_BY_TYPE) for acc, name in d.values()}
_SO_NAMES.update({"SO:0000315": "TSS", "SO:0000552": "Shine_Dalgarno_sequence"})


def _so_derive(feature_type, regulatory_class=None, label=None):
    if regulatory_class and regulatory_class in _SO_BY_REG:
        return _SO_BY_REG[regulatory_class]
    lab = (label or "").lower()
    if lab.startswith("+1") or "transcription start" in lab or lab.strip() == "tss":
        return ("SO:0000315", "TSS")
    if feature_type == "protein_bind" and (
            "operator" in lab or any(t in lab for t in ("teto", "laco", "arao", "pho"))):
        return ("SO:0000057", "operator")
    if feature_type == "RBS" and ("shine" in lab or "dalgarno" in lab or lab.strip() == "sd"):
        return ("SO:0000552", "Shine_Dalgarno_sequence")
    return _SO_BY_TYPE.get(feature_type)


def _so_term(feature):
    """(SO accession, SO name) for a feature: an explicit /db_xref="SO:..." wins,
    else derive from the feature type / regulatory_class / label."""
    for x in feature.qualifiers.get("db_xref", []):
        if str(x).startswith("SO:"):
            return str(x), _SO_NAMES.get(str(x), "")
    rc = (feature.qualifiers.get("regulatory_class") or [None])[0]
    label = (feature.qualifiers.get("label") or [""])[0]
    return _so_derive(feature.type, rc, label) or (None, None)


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
        "so_term": main_so_id,
        "so_name": main_so_name,
        "synonyms": list(q.get("synonym", [])),
        "description": (q.get("note") or [""])[0],
        "length": len(seq),
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


def _so_link(so_id, so_name) -> str:
    if not so_id:
        return "—"
    url = f"http://sequenceontology.org/browser/current_release/term/{so_id}"
    return f"[{so_name or so_id}]({url})"


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


def render_part_page(part: dict) -> str:
    slug, name = part["slug"], part["name"]
    syn = (" · synonyms: " + ", ".join(part["synonyms"])) if part["synonyms"] else ""
    so = part.get("so_term")
    so_part = f" · {_so_link(so, part.get('so_name'))}" if so else ""
    head = [
        f"# {name}\n",
        f"`{part['feature_type']}`{so_part} · {part['length']} bp{syn}\n",
        f"[Download GenBank](files/{slug}.gb){{ .md-button }} "
        f"[Download FASTA](files/{slug}.fasta){{ .md-button }}\n",
        f'<div class="part-map" data-part="{slug}" data-gb="files/{slug}.gb"></div>\n',
    ]
    md_path = VALIDATED_DIR / f"{slug}.md"
    contrib = "https://github.com/dbikard/dna-parts-catalog/blob/main/CONTRIBUTING.md"
    if part["documented"]:
        body = md_path.read_text(encoding="utf-8").strip() + "\n"
        # Structured feature table up top, then the curated prose (which carries
        # its own References section).
        return ("\n".join(head) + "\n" + AI_WIP_WARNING + "\n"
                + _feature_table(part) + "\n" + body)
    note = part["description"] or "_No curated documentation page yet._"
    note += (f"\n\n*This part has no curated documentation yet — "
             f"[contribute one]({contrib}).*\n")
    return ("\n".join(head) + "\n" + AI_WIP_WARNING + "\n" + note + "\n"
            + _feature_table(part) + "\n" + _reference_list(part["references"]))


def render_index(validated: list[dict], n_candidate: int) -> str:
    repo = "https://github.com/dbikard/dna-parts-catalog"
    lines = [
        "# DNA parts catalog\n",
        AI_WIP_WARNING,
        f"An open, community-curated catalog of standard DNA parts (promoters, "
        f"CDSs, terminators, RBSs, …) as annotated GenBank files. The "
        f"**{len(validated)}** *validated* parts below each carry a curated "
        f"documentation page; use the search box to find one.\n",
        f"A further **{n_candidate}** *candidate* parts (annotated GenBank, "
        f"awaiting a curated documentation page) are available in "
        f"[`catalog.json`]({repo}/blob/main/catalog.json) and the "
        f"[`parts/candidate/`]({repo}/tree/main/parts/candidate) directory.\n",
        "| Part | Type | Length |",
        "|---|---|---|",
    ]
    for p in sorted(validated, key=lambda x: x["name"].lower()):
        lines.append(f"| [{p['name']}](parts/{p['slug']}.md) | "
                     f"{p['feature_type']} | {p['length']} bp |")
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

    # Manifest covers every part (validated + candidate), with the internal
    # sequence field stripped.
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "n_parts": len(parts),
        "n_validated": sum(p["status"] == "validated" for p in parts),
        "n_candidate": sum(p["status"] == "candidate" for p in parts),
        "n_documented": sum(p["documented"] for p in parts),
        "parts": [{k: v for k, v in p.items() if k != "_seq"}
                  for p in sorted(parts, key=lambda x: x["name"].lower())],
    }
    (ROOT / "catalog.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                       encoding="utf-8")

    # Website publishes validated parts only (pages + downloadable files).
    validated = [p for p in parts if p["status"] == "validated"]
    n_candidate = manifest["n_candidate"]
    if PARTS_PAGES.exists():
        shutil.rmtree(PARTS_PAGES)
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    (DOCS_DIR / "index.md").write_text(render_index(validated, n_candidate),
                                       encoding="utf-8")
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
