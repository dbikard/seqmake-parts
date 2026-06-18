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
from Bio.SeqUtils.CheckSum import crc64

ROOT = Path(__file__).resolve().parent.parent

# UniProt feature type -> (GenBank feature type, SO accession or None). Only the
# types useful for annotation are imported; the rest (e.g. Chain, Region) are
# skipped to keep the part focused.
_TYPE_MAP: dict[str, tuple[str, str | None]] = {
    "Domain": ("protein_domain", "SO:0000417"),
    "Active site": ("misc_feature", "SO:0000110"),
    "Binding site": ("binding", "SO:0000409"),
    "Metal binding": ("binding", "SO:0000409"),
    "Signal": ("sig_peptide", "SO:0000418"),
    "Transit peptide": ("transit_peptide", None),
    "Propeptide": ("propeptide", None),
    "Site": ("misc_feature", "SO:0000110"),
    "Modified residue": ("modified_residue", None),
    "Disulfide bond": ("disulfide_bond", "SO:0001088"),
    "Motif": ("protein_domain", "SO:0000417"),
    "Zinc finger": ("protein_domain", "SO:0000417"),
}


def _get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "seqmake-parts/uniprot-import"})
    with urllib.request.urlopen(req, timeout=60) as r:  # noqa: S310
        return json.loads(r.read().decode("utf-8"))


def _fetch(accession: str) -> dict:
    return _get_json(f"https://rest.uniprot.org/uniprotkb/{accession}.json")


def parse_uniparc(data: dict, seq: str) -> list[tuple[str, bool]]:
    """From a UniParc search response, the active UniProtKB accessions whose
    sequence is EXACTLY ``seq`` (reviewed/Swiss-Prot first). Pure / testable."""
    out: list[tuple[str, bool]] = []
    seen: set[str] = set()
    for r in data.get("results", []):
        if (r.get("sequence") or {}).get("value") != seq:   # guard checksum collisions
            continue
        for x in r.get("uniParcCrossReferences", []):
            db, acc = x.get("database", ""), x.get("id", "")
            if x.get("active") and db.startswith("UniProtKB") and acc not in seen:
                seen.add(acc)
                out.append((acc, "Swiss-Prot" in db))
    out.sort(key=lambda t: (not t[1], t[0]))     # reviewed first, then by accession
    return out


def uniparc_exact_accessions(seq: str) -> list[tuple[str, bool]]:
    """Active UniProtKB accessions whose sequence is exactly ``seq`` (via UniParc,
    keyed on the CRC64 checksum). Empty if none -- network step."""
    checksum = crc64(seq).removeprefix("CRC-")
    url = ("https://rest.uniprot.org/uniparc/search?"
           f"query=checksum:{checksum}&format=json&size=50")
    return parse_uniparc(_get_json(url), seq)


def _set_accession(data: dict, new_acc: str) -> None:
    """Replace the part's UniProt db_xref on the main feature with ``new_acc``."""
    main = next(f for f in data["features"] if "parent" not in f["qualifiers"])
    xrefs = main["qualifiers"].get("db_xref", [])
    main["qualifiers"]["db_xref"] = [x for x in xrefs if not x.startswith("UniProt:")] + \
        [f"UniProt:{new_acc}"]


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


def variant_disposition(data: dict) -> str:
    """For a close-variant part: 'keep' it when it declares a variant_rationale
    (an intentional/functional variant like dCas9), else 'normalize' it to the
    UniProt canonical sequence."""
    return "keep" if (data.get("variant_rationale") or "").strip() else "normalize"


def import_part(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["molecule_type"] != "protein":
        return "skip (not protein)"
    acc = _accession(data)
    if not acc:
        return "skip (no UniProt accession)"
    entry = _fetch(acc)
    up_seq = (entry.get("sequence") or {}).get("value", "")
    seq = data["sequence"]
    cmp = classify_sequences(seq, up_seq)
    today = _dt.date.today().isoformat()

    def do_import(entry2: dict, prov: dict, result: str) -> str:
        feats = features_from_uniprot(entry2)
        data["uniprot_features"] = feats
        data["uniprot_import"] = {"fetched": today, **prov}
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return f"imported {len(feats)} features [{result}]"

    # 1) Exact match to the assigned accession.
    if cmp["status"] == "match":
        return do_import(entry, {"accession": f"UniProt:{acc}", "status": "match",
                                 "identity": 1.0, "sequence_match": True,
                                 "uniprot_entry_version": entry.get("entryAudit", {}).get("entryVersion")},
                         "match")

    # 2) Intentional variant (declared) -> keep, import the reference's features.
    rationale = (data.get("variant_rationale") or "").strip()
    if cmp["status"] == "variant" and rationale:
        return do_import(entry, {"accession": f"UniProt:{acc}", "status": "variant",
                                 "identity": cmp["identity"], "sequence_match": False,
                                 "variants": cmp["variants"], "variant_rationale": rationale,
                                 "uniprot_entry_version": entry.get("entryAudit", {}).get("entryVersion")},
                         f"variant KEPT ({len(cmp['variants'])} SNP(s), "
                         f"{cmp['identity']*100:.1f}% id) -- {rationale[:50]}")

    # 3) Not exact & not intentional: is the sequence an EXACT match to a DIFFERENT
    #    UniProt accession? If so the part is a real protein under that ID -> re-point
    #    to it (don't overwrite the sequence).
    hits = [h for h in uniparc_exact_accessions(seq) if h[0] != acc]
    if hits:
        new_acc, reviewed = hits[0]
        entry2 = _fetch(new_acc)
        _set_accession(data, new_acc)
        tag = "" if reviewed else ", TrEMBL"
        return do_import(entry2, {"accession": f"UniProt:{new_acc}", "status": "reaccessioned",
                                  "identity": 1.0, "sequence_match": True,
                                  "previous_accession": f"UniProt:{acc}", "reviewed": reviewed,
                                  "uniprot_entry_version": entry2.get("entryAudit", {}).get("entryVersion")},
                         f"RE-ACCESSIONED {acc} -> {new_acc} (exact UniProt match{tag})")

    # 4a) No exact match anywhere, but a close same-length variant -> normalize.
    if cmp["status"] == "variant":
        data["sequence"] = up_seq
        return do_import(entry, {"accession": f"UniProt:{acc}", "status": "normalized_to_canonical",
                                 "identity": cmp["identity"], "sequence_match": True,
                                 "normalized_substitutions": cmp["variants"],
                                 "uniprot_entry_version": entry.get("entryAudit", {}).get("entryVersion")},
                         f"normalized to canonical (no exact match; replaced "
                         f"{len(cmp['variants'])} residue(s))")

    # 4b) No exact match and not a close variant -> record the finding, don't import.
    data.pop("uniprot_features", None)
    prov = {"accession": f"UniProt:{acc}", "fetched": today,
            "uniprot_entry_version": entry.get("entryAudit", {}).get("entryVersion"), **cmp}
    data["uniprot_import"] = prov
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    idpct = f"{cmp['identity']*100:.1f}% id"
    if cmp["status"] == "wrong_accession":
        return (f"WRONG-ACCESSION {acc}: only {idpct}, no exact match anywhere in "
                "UniProt -- likely the wrong ID; recorded, not imported")
    if cmp["status"] == "length_variant":
        return (f"LENGTH-VARIANT vs {acc}: same protein, different length "
                f"({cmp['part_len']} vs {cmp['uniprot_len']} aa, {idpct}) "
                "-- recorded, not imported")
    return (f"DIVERGENT from {acc}: {idpct}, no exact match "
            "-- review; recorded, not imported")


def main() -> None:
    slugs = set(sys.argv[1:])
    paths = []
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for jf in sorted(d.glob("*.json")):
            if not slugs or jf.stem in slugs:
                paths.append(jf)
    counts = {"imported": 0, "normalized": 0, "variant_kept": 0, "reaccessioned": 0,
              "length_variant": 0, "divergent": 0, "wrong_accession": 0, "error": 0}
    wrong: list[str] = []
    for jf in paths:
        try:
            msg = import_part(jf)
        except Exception as exc:  # noqa: BLE001 - report and continue
            msg = f"ERROR: {exc}"
        if msg.startswith("imported"):
            counts["imported"] += 1
            if "normalized to canonical" in msg:
                counts["normalized"] += 1
            elif "variant KEPT" in msg:
                counts["variant_kept"] += 1
            elif "RE-ACCESSIONED" in msg:
                counts["reaccessioned"] += 1
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
    print(f"\ndone -- imported {counts['imported']} "
          f"(normalized {counts['normalized']}, variant-kept {counts['variant_kept']}, "
          f"re-accessioned {counts['reaccessioned']}), "
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
