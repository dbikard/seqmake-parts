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
import math
import sys
import urllib.request
from pathlib import Path

from Bio.Align import PairwiseAligner

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


_ALIGNER = None


def _aligned_identity(a: str, b: str) -> float:
    """Global-alignment percent identity over aligned (ungapped) columns -- the
    signal that tells a real protein (variant/isoform, high identity) from a wrong
    accession (a different protein, low identity)."""
    global _ALIGNER
    if _ALIGNER is None:
        al = PairwiseAligner()
        al.mode = "global"
        al.match_score, al.mismatch_score = 1, 0
        al.open_gap_score, al.extend_gap_score = -1, -0.5
        _ALIGNER = al
    aln = _ALIGNER.align(a, b)[0]
    matches = cols = 0
    for (a0, a1), (b0, b1) in zip(*aln.aligned):
        for x, y in zip(a[a0:a1], b[b0:b1]):
            cols += 1
            matches += (x == y)
    return matches / cols if cols else 0.0


# Identity bands used to classify a part sequence against its UniProt accession.
_VARIANT_ID = 0.90   # >= this and same length -> SNP variant (coords valid -> import)
_SAME_PROTEIN_ID = 0.90  # >= this with a length change -> same protein, different form
_WRONG_ACC_ID = 0.60     # < this -> almost certainly the WRONG accession


def classify_sequences(part: str, up: str) -> dict:
    """Classify a part sequence against UniProt's canonical and, crucially,
    distinguish a few-SNP *variant* from a *wrong accession*. Pure / testable.

    Statuses:
      match          identical.
      variant        same length, high identity -> a handful of SNPs; coordinates
                     stay valid, so features are imported and the SNPs recorded.
      length_variant high identity but a length change (isoform/fragment): the
                     same protein, but coordinates shift -> not imported.
      divergent      moderate identity: a distant allele/homolog -> review.
      wrong_accession low identity: a different protein -> the accession is wrong.
    """
    if not up:
        return {"status": "wrong_accession", "identity": 0.0,
                "note": "UniProt returned no sequence"}
    if part == up:
        return {"status": "match", "identity": 1.0}
    same_len = len(part) == len(up)
    if same_len:
        diffs = [{"pos": i + 1, "part": part[i], "uniprot": up[i]}
                 for i in range(len(part)) if part[i] != up[i]]
        ident = 1 - len(diffs) / len(part)
        tol = max(3, math.ceil(0.02 * len(part)))   # a handful of SNPs
        if len(diffs) <= tol or ident >= _VARIANT_ID:
            return {"status": "variant", "identity": round(ident, 4),
                    "variants": diffs}
        if ident >= _WRONG_ACC_ID:
            return {"status": "divergent", "identity": round(ident, 4),
                    "n_substitutions": len(diffs)}
        return {"status": "wrong_accession", "identity": round(ident, 4),
                "n_substitutions": len(diffs)}
    # Length differs -> align to measure identity (tells isoform from wrong ID).
    ident = _aligned_identity(part, up)
    base = {"identity": round(ident, 4),
            "part_len": len(part), "uniprot_len": len(up)}
    if ident >= _SAME_PROTEIN_ID:
        return {"status": "length_variant", **base}
    if ident >= _WRONG_ACC_ID:
        return {"status": "divergent", **base}
    return {"status": "wrong_accession", **base}


def import_part(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["molecule_type"] != "protein":
        return "skip (not protein)"
    acc = _accession(data)
    if not acc:
        return "skip (no UniProt accession)"
    entry = _fetch(acc)
    up_seq = (entry.get("sequence") or {}).get("value", "")
    cmp = classify_sequences(data["sequence"], up_seq)
    prov = {
        "accession": f"UniProt:{acc}",
        "uniprot_release": entry.get("entryAudit", {}).get("entryVersion"),
        "fetched": _dt.date.today().isoformat(),
        "status": cmp["status"],
    }
    if cmp["status"] in ("match", "variant"):
        feats = features_from_uniprot(entry)
        data["uniprot_features"] = feats
        prov["sequence_match"] = cmp["status"] == "match"
        if cmp["status"] == "variant":
            prov["variants"] = cmp["variants"]
        data["uniprot_import"] = prov
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        if cmp["status"] == "variant":
            return (f"imported {len(feats)} features [variant, "
                    f"{len(cmp['variants'])} SNP(s), {cmp['identity']*100:.1f}% id]")
        return f"imported {len(feats)} features [match]"
    # Coordinates can't be trusted -> record the finding (durable) and don't import.
    data.pop("uniprot_features", None)
    prov.update({k: v for k, v in cmp.items() if k != "status"})
    data["uniprot_import"] = prov
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    idpct = f"{cmp['identity']*100:.1f}% id"
    if cmp["status"] == "wrong_accession":
        return (f"WRONG-ACCESSION {acc}: only {idpct} to this part "
                "-- likely the wrong UniProt ID; recorded, not imported")
    if cmp["status"] == "length_variant":
        return (f"LENGTH-VARIANT vs {acc}: same protein, different length "
                f"({cmp['part_len']} vs {cmp['uniprot_len']} aa, {idpct}) "
                "-- recorded, not imported")
    return (f"DIVERGENT from {acc}: {idpct} "
            "-- distant allele/homolog, review; recorded, not imported")


def main() -> None:
    slugs = set(sys.argv[1:])
    paths = []
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for jf in sorted(d.glob("*.json")):
            if not slugs or jf.stem in slugs:
                paths.append(jf)
    counts = {"imported": 0, "length_variant": 0, "divergent": 0,
              "wrong_accession": 0, "error": 0}
    wrong: list[str] = []
    for jf in paths:
        try:
            msg = import_part(jf)
        except Exception as exc:  # noqa: BLE001 - report and continue
            msg = f"ERROR: {exc}"
        if msg.startswith("imported"):
            counts["imported"] += 1
        elif msg.startswith("WRONG-ACCESSION"):
            counts["wrong_accession"] += 1
            wrong.append(jf.stem)
        elif msg.startswith("LENGTH-VARIANT"):
            counts["length_variant"] += 1
        elif msg.startswith("DIVERGENT"):
            counts["divergent"] += 1
        elif msg.startswith("ERROR"):
            counts["error"] += 1
        if not msg.startswith("skip"):
            print(f"{jf.stem:18s} {msg}")
    print(f"\ndone -- imported {counts['imported']}, "
          f"length-variant {counts['length_variant']}, divergent {counts['divergent']}, "
          f"WRONG-ACCESSION {counts['wrong_accession']}, errors {counts['error']}.")
    if wrong:
        print("::warning::Likely WRONG UniProt accession (different protein) for: "
              + ", ".join(wrong))
    # Fail only on fetch/HTTP errors with nothing imported (e.g. no network), so a
    # refresh doesn't commit an empty/broken result. Variants, length-variants,
    # divergent and wrong-accession are recorded findings, surfaced not fatal.
    if counts["imported"] == 0 and counts["error"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
