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
        children.append({
            "label": (f.qualifiers.get("label") or [""])[0],
            "feature_type": f.type,
            "start": int(f.location.start),
            "end": int(f.location.end),
            "strand": 1 if f.location.strand in (None, 1) else -1,
            "citations": _citation_indices(f.qualifiers),
        })
    md_path = gb_path.with_suffix(".md")
    documented = md_path.exists()
    return {
        "name": name,
        "slug": gb_path.stem,
        "feature_type": main.type,
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


def _feature_table(part: dict) -> str:
    if not part["children"]:
        return ""
    seq, refs = part["_seq"], part["references"]
    lines = ["## Sub-features\n",
             "| Element | Type | Position | Strand | Sequence | Citations |",
             "|---|---|---|---|---|---|"]
    for c in part["children"]:
        s, e = c["start"], c["end"]
        sub = seq[s:e]
        if c["strand"] == -1:
            sub = _revcomp(sub)
        strand = "+" if c["strand"] == 1 else "−"
        lines.append(f"| {c['label']} | `{c['feature_type']}` | {s + 1}..{e} | "
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
    head = [
        f"# {name}\n",
        f"`{part['feature_type']}` · {part['length']} bp{syn}\n",
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
