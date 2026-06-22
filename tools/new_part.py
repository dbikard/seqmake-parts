#!/usr/bin/env python3
"""Scaffold a schema-valid canonical part JSON skeleton.

The deterministic first step of the authoring workflow (see ``AUTHORING.md``):
given a name, feature type and a sequence sourced from a cited reference, it
writes ``parts/<status>/<slug>.json`` with the boilerplate filled in correctly
(schema version, slug/locus, molecule type, the main feature with its Sequence
Ontology ``db_xref``). The author then adds sub-features, references, and
functional_claims, and — to validate the part — a sibling ``<slug>.md``.

Usage:
    python tools/new_part.py --name PphlF --type promoter --sequence tctga...
    python tools/new_part.py --name bla --type CDS --sequence-file bla.txt \
        --source-accession UniProt:P62593
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from part_json import SCHEMA_VERSION  # noqa: E402
from so_terms import so_for  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def slugify(name: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9.\-]+", "_", name).strip("_")
    return slug or "part"


def build_skeleton(name: str, feature_type: str, sequence: str, *,
                   synonyms: list[str] | None = None, note: str = "",
                   source_accession: str = "",
                   regulated_by: list[str] | None = None,
                   collections: list[str] | None = None) -> dict:
    """A schema-valid canonical-record dict with only the main feature filled in.

    ``sequence`` must come from a cited source (never from memory); the
    provenance block records a placeholder for that citation to force the author
    to fill it. Sub-features / references / functional_claims start empty."""
    seq = sequence.strip()
    if not seq:
        raise ValueError("a part needs a sequence (sourced from a cited reference)")
    is_protein = bool(set(seq.upper()) - set("ACGTUN"))
    slug = slugify(name)
    q: dict[str, list[str]] = {"label": [name]}
    if synonyms:
        q["synonym"] = list(synonyms)
    if note:
        q["note"] = [note]
    xrefs: list[str] = []
    so = so_for(feature_type)
    if so:
        xrefs.append(so[0])
    if source_accession:
        xrefs.append(source_accession)
    if xrefs:
        q["db_xref"] = xrefs
    if regulated_by:
        q["regulated_by"] = list(regulated_by)
    if collections:
        q["collection"] = list(collections)
    return {
        "schema_version": SCHEMA_VERSION,
        "slug": slug,
        "locus": slug[:16] or "part",
        "id": slug[:16] or "part",
        "description": note or name,
        "molecule_type": "protein" if is_protein else "DNA",
        "locus_annotations": {"topology": "linear"},
        "sequence": seq,
        "references": [],
        "features": [{
            "type": feature_type,
            "start": 0,
            "end": len(seq),
            "strand": 1,
            "qualifiers": q,
        }],
        "provenance": {
            "created_by": "add-part",
            "sequence_source": "FILL IN: cite the primary/registry source the sequence is from",
        },
        "functional_claims": [],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Scaffold a new canonical part JSON.")
    ap.add_argument("--name", required=True)
    ap.add_argument("--type", required=True,
                    help="GenBank feature type (promoter, CDS, terminator, RBS, ...)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sequence", help="the part sequence (DNA, or protein aa)")
    g.add_argument("--sequence-file", help="read the sequence from this file")
    ap.add_argument("--status", choices=["candidate", "validated"], default="candidate")
    ap.add_argument("--synonym", action="append", default=[])
    ap.add_argument("--note", default="")
    ap.add_argument("--source-accession", default="",
                    help="UniProt:Pxxxxx / NCBI:... for a coding part")
    ap.add_argument("--regulated-by", action="append", default=[])
    ap.add_argument("--collection", action="append", default=[])
    args = ap.parse_args()

    seq = (Path(args.sequence_file).read_text(encoding="utf-8")
           if args.sequence_file else args.sequence)
    seq = "".join(seq.split())  # tolerate wrapped/whitespaced input
    data = build_skeleton(
        args.name, args.type, seq, synonyms=args.synonym, note=args.note,
        source_accession=args.source_accession, regulated_by=args.regulated_by,
        collections=args.collection)
    if data["molecule_type"] == "protein" and not args.source_accession:
        print("WARNING: protein parts must defer biology to UniProt — re-run with "
              "--source-accession UniProt:Pxxxxx (or NCBI:...). Do NOT annotate "
              "residue-level features; link to UniProt/InterPro/AlphaFold instead.",
              file=sys.stderr)
    out = ROOT / "parts" / args.status / f"{data['slug']}.json"
    if out.exists():
        sys.exit(f"refusing to overwrite existing {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                   encoding="utf-8")
    print(f"wrote {out}")
    print("next: add sub-features / references / functional_claims (with sources); "
          "for a validated part add the sibling .md; then run tools/build_gb.py, "
          "tools/build_catalog.py, tools/build_rdf.py and tools/validate_parts.py.")


if __name__ == "__main__":
    main()
