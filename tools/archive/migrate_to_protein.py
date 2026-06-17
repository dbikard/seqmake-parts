#!/usr/bin/env python3
"""Migrate a DNA coding part (CDS / protein_domain) to a protein-only record.

A coding part's canonical identity is its protein, not one codon realization.
This converts a DNA GenBank record into a protein record: the ``/translation``
becomes the record sequence, sub-features are remapped from bp to residue (aa)
coordinates (``start // 3``), the DNA is dropped, and an optional source
accession is stamped into the main feature's ``/db_xref`` (alongside any SO xref).

Usage:
    python tools/migrate_to_protein.py parts/validated/ChnR.gb --accession NCBI:AB006902
    python tools/migrate_to_protein.py parts/candidate/cas9.gb  --accession UniProt:Q99ZW2
"""
from __future__ import annotations

import argparse
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, SeqFeature
from Bio.SeqRecord import SeqRecord

CODING_TYPES = {"CDS", "protein_domain", "mat_peptide", "sig_peptide", "gene"}


def migrate(gb_path: Path, accession: str | None) -> str:
    record = SeqIO.read(str(gb_path), "genbank")
    main = next((f for f in record.features if "parent" not in f.qualifiers), None)
    if main is None:
        raise SystemExit(f"{gb_path}: no main feature")
    if main.type not in CODING_TYPES:
        raise SystemExit(f"{gb_path}: main feature {main.type!r} is not a coding part")
    seq = str(record.seq).upper()
    if set(seq) - set("ACGTUN"):
        raise SystemExit(f"{gb_path}: already a protein record")
    protein = (main.qualifiers.get("translation") or [None])[0]
    if not protein:
        raise SystemExit(f"{gb_path}: main CDS has no /translation")

    prot = SeqRecord(
        Seq(protein), id=record.id[:16], name=record.name[:16],
        description=record.description, annotations={"molecule_type": "protein"},
    )
    prot.annotations["references"] = record.annotations.get("references", [])

    main_quals = {k: list(v) for k, v in main.qualifiers.items()}
    main_quals.pop("translation", None)  # the record IS the protein now
    if accession:
        # keep SO xrefs, replace any prior source accession with the new one
        so = [x for x in main_quals.get("db_xref", []) if str(x).startswith("SO:")]
        main_quals["db_xref"] = so + [accession]
    prot.features.append(
        SeqFeature(FeatureLocation(0, len(protein), 1), type=main.type, qualifiers=main_quals)
    )

    n_dom = 0
    for f in record.features:
        if "parent" not in f.qualifiers:
            continue
        aa_start = int(f.location.start) // 3
        aa_end = min(int(f.location.end) // 3, len(protein))
        prot.features.append(
            SeqFeature(FeatureLocation(aa_start, aa_end, 1), type=f.type,
                       qualifiers={k: list(v) for k, v in f.qualifiers.items()})
        )
        n_dom += 1

    SeqIO.write([prot], str(gb_path), "genbank")
    acc = f", {accession}" if accession else ""
    return f"{gb_path.name}: {len(protein)} aa, {n_dom} domain(s){acc}"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--accession", default=None,
                    help='source accession, e.g. "UniProt:Q99ZW2" or "NCBI:AB006902"')
    args = ap.parse_args()
    for p in args.paths:
        print(migrate(p, args.accession))


if __name__ == "__main__":
    main()
