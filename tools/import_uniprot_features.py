#!/usr/bin/env python3
"""Import protein features (domains, active/binding sites, signal peptides) from
UniProt into the canonical part JSON as a cached ``uniprot_features`` layer.

Protein parts defer their biology to UniProt (see AUTHORING.md): instead of
hand-authoring residue annotations, we cache a *projection* of UniProt's curated
features, with provenance, and bake them into the generated ``.gb`` so GenBank
consumers (e.g. seqmake plasmid annotation) get authoritative, attributed
features. Re-run this when UniProt updates; the result is a reviewable git diff.

Network: needs egress to ``rest.uniprot.org``. Run it where that is allowed;
the catalog build itself stays offline (it reads the committed cache).

Usage:
    python tools/import_uniprot_features.py            # all protein parts
    python tools/import_uniprot_features.py bla CmR    # specific slugs
"""
from __future__ import annotations

import datetime as _dt
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# UniProt feature type -> (GenBank feature type, SO accession or None). Only the
# types useful for annotation are imported; the rest (e.g. Chain, Region) are
# skipped to keep the part focused.
_TYPE_MAP: dict[str, tuple[str, str | None]] = {
    "Domain": ("protein_domain", "SO:0000417"),
    "Active site": ("misc_feature", "SO:0000110"),
    "Binding site": ("binding", None),
    "Metal binding": ("binding", None),
    "Signal": ("sig_peptide", "SO:0000418"),
    "Transit peptide": ("transit_peptide", None),
    "Propeptide": ("propeptide", None),
    "Site": ("misc_feature", "SO:0000110"),
    "Modified residue": ("modified_residue", None),
    "Disulfide bond": ("disulfide_bond", None),
    "Motif": ("protein_domain", "SO:0000417"),
    "Zinc finger": ("protein_domain", "SO:0000417"),
}


def _fetch(accession: str) -> dict:
    url = f"https://rest.uniprot.org/uniprotkb/{accession}.json"
    req = urllib.request.Request(url, headers={"User-Agent": "dna-parts-catalog/uniprot-import"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _label(uf: dict) -> str:
    t = uf.get("type", "feature")
    desc = (uf.get("description") or "").strip()
    if uf.get("type") == "Domain" and desc:
        return desc
    return f"{t}: {desc}" if desc else t


def features_from_uniprot(entry: dict) -> list[dict]:
    out = []
    for uf in entry.get("features", []):
        mapped = _TYPE_MAP.get(uf.get("type"))
        if not mapped:
            continue
        loc = uf.get("location", {})
        b = (loc.get("start") or {}).get("value")
        e = (loc.get("end") or {}).get("value")
        if b is None or e is None:
            continue
        gb_type, so = mapped
        out.append({
            "type": gb_type,
            "start": int(b) - 1,          # UniProt 1-based inclusive -> 0-based
            "end": int(e),                # -> end-exclusive
            "label": _label(uf),
            "so_term": so,
            "description": (uf.get("description") or "").strip(),
            "uniprot_type": uf.get("type"),
        })
    return out


def _accession(data: dict) -> str | None:
    main = next((f for f in data["features"] if "parent" not in f["qualifiers"]), None)
    if not main:
        return None
    for x in main["qualifiers"].get("db_xref", []):
        if x.startswith("UniProt:"):
            return x.split(":", 1)[1]
    return None


def import_part(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["molecule_type"] != "protein":
        return "skip (not protein)"
    acc = _accession(data)
    if not acc:
        return "skip (no UniProt accession)"
    entry = _fetch(acc)
    up_seq = (entry.get("sequence") or {}).get("value", "")
    if up_seq != data["sequence"]:
        return (f"MISMATCH: part sequence != UniProt {acc} "
                f"(len {len(data['sequence'])} vs {len(up_seq)}) -- not importing")
    feats = features_from_uniprot(entry)
    data["uniprot_features"] = feats
    data["uniprot_import"] = {
        "accession": f"UniProt:{acc}",
        "uniprot_release": entry.get("entryAudit", {}).get("entryVersion"),
        "fetched": _dt.date.today().isoformat(),
        "sequence_match": True,
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return f"imported {len(feats)} features (UniProt:{acc})"


def main() -> None:
    slugs = set(sys.argv[1:])
    paths = []
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for jf in sorted(d.glob("*.json")):
            if not slugs or jf.stem in slugs:
                paths.append(jf)
    for jf in paths:
        try:
            msg = import_part(jf)
        except Exception as exc:  # noqa: BLE001 - report and continue
            msg = f"ERROR: {exc}"
        if not msg.startswith("skip"):
            print(f"{jf.stem:18s} {msg}")
    print("done -- now run tools/build_gb.py + build_catalog.py + build_rdf.py and commit.")


if __name__ == "__main__":
    main()
