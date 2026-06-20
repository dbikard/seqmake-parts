#!/usr/bin/env python3
"""Batch helper for the protein-tag series — merge one engine proposal into a
candidate part, the verified-additive way, and promote it to validated.

NOT a catalog tool; batch scaffolding for proposals/protein-tags. Encapsulates the
recipe proven on GST/6xHis/FLAG/S-tag/Strep_tag (see memory protein-tags-batch):
  * normalize engine claims -> full nanopub shape (provenance/review_status/supersedes)
  * map refs -> schema shape (pubmed_id + comment=doi:..)
  * main feature: protein_domain + db_xref [SO:0000417] (+UniProt/NCBI if --accession),
    carry synonyms + the engine note + citation
  * merge_part --replace-features --write   (additive, review-status-safe)
  * set top-level description (merge_part does not)
  * if new_part.py left a placeholder sequence_source, promote sequence_source_proposed
  * write parts/validated/<slug>.md from report_markdown (prepend '# <slug>' if missing)
  * promote: move json to validated/, drop the orphan candidate .gb

Usage:
  python proposals/protein-tags/merge_tag.py --slug HA --result /tmp/HA.result.json \
      [--synonyms "HA-tag,influenza HA epitope"] [--accession UniProt:P03437] [--dry-run]
"""
import argparse, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


_SRC_FIELDS = {"pmid", "doi", "url", "quote", "quote_source",
               "figure", "table", "page", "section"}


def norm_claim(c):
    # schema source has additionalProperties:false — keep only allowed fields
    # (engine runs sometimes emit a stray 'journal'/'authors' on the source)
    src = {k: v for k, v in (c.get("source") or {}).items() if k in _SRC_FIELDS}
    q = src.get("quote_source", "")
    return {
        "id": c["id"], "type": c["type"], "label": c["label"],
        "value": c.get("value", {}), "source": src,
        "provenance": {"method": "ai-extraction",
                       "from": "primary" if q == "primary" else "secondary",
                       "agent": "annotate-part-engine"},
        "confidence": c.get("confidence", "medium"),
        "review_status": "ai-generated", "supersedes": None,
    }


def map_ref(x):
    return {"authors": x.get("authors", ""), "title": x.get("title", ""),
            "journal": f"{x.get('journal','')} ({x.get('year','')})".strip(),
            "pubmed_id": str(x.get("pmid", "")),
            "comment": f"doi:{x.get('doi','')}" if x.get("doi") else ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--result", required=True, help="extracted proposal dict JSON")
    ap.add_argument("--synonyms", default="")
    ap.add_argument("--accession", default="", help="UniProt:.. / NCBI:.. to add as a db_xref")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    r = json.load(open(a.result))
    slug = a.slug
    cand = ROOT / "parts" / "candidate" / f"{slug}.json"
    if not cand.exists():
        sys.exit(f"candidate {cand} does not exist (scaffold a new part with new_part.py first)")

    seq = r["sequence"]
    existing0 = json.load(open(cand))
    if seq != existing0["sequence"]:
        sys.exit(f"SEQUENCE MISMATCH for {slug}: engine proposes {len(seq)} aa "
                 f"({seq[:16]}..) but candidate holds {len(existing0['sequence'])} aa "
                 f"({existing0['sequence'][:16]}..). This is a sequence correction -> "
                 f"ESCALATE (do not auto-merge); handle like HaloTag.")
    if not r.get("ready_to_apply", False):
        sys.exit(f"{slug}: ready_to_apply is false -> ESCALATE, do not auto-merge.")
    refs = [map_ref(x) for x in r["references"]]
    claims = [norm_claim(c) for c in r["functional_claims"]]
    # canonical feature type + SO term: full-protein CDS vs short peptide tag
    ftype = r.get("feature_type", "protein_domain")
    so = "SO:0000316" if ftype == "CDS" else "SO:0000417"
    db_xref = [so] + ([a.accession] if a.accession else [])
    existing = json.load(open(cand))
    syn = list(existing["features"][0]["qualifiers"].get("synonym", []))
    for s in [x.strip() for x in a.synonyms.split(",") if x.strip()]:
        if s not in syn:
            syn.append(s)
    note = r["features"][0].get("note", "")
    feat = {"type": ftype, "start": 0, "end": len(seq), "strand": 1,
            "qualifiers": {"label": [slug], "synonym": syn,
                           "note": [note] if note else [],
                           "citation": [f"[{i+1}]" for i in range(len(refs))],
                           "db_xref": db_xref}}
    proposed = {"description": r["description"], "features": [feat], "references": refs,
                "provenance": {"sequence_source": r["provenance"]["sequence_source"]},
                "functional_claims": claims, "review_status": "ai-generated"}
    pj = ROOT / f"/tmp/{slug}.proposed.json"
    pj = Path(f"/tmp/{slug}.proposed.json")
    json.dump(proposed, open(pj, "w"), indent=2)

    args = ["python3", str(ROOT / "tools" / "merge_part.py"), "--into", str(cand),
            "--proposed", str(pj), "--replace-features"]
    rep = subprocess.run(args, capture_output=True, text=True).stdout
    report = json.loads(rep)
    print(f"[{slug}] claims+={report['claims']['added']} refs+={len(report['references_added'])} "
          f"flags={report['flags']} superseding={report['claims']['flagged_superseding']}")
    if a.dry_run:
        return

    subprocess.run(args + ["--write"], capture_output=True, text=True)
    # set description + promote any placeholder sequence_source
    d = json.load(open(cand))
    d["description"] = r["description"]
    prov = d.get("provenance", {})
    if "sequence_source_proposed" in prov:
        prov["sequence_source"] = prov.pop("sequence_source_proposed")
    if str(prov.get("sequence_source", "")).startswith("FILL IN"):
        prov["sequence_source"] = r["provenance"]["sequence_source"]
    d["provenance"] = prov
    json.dump(d, open(cand, "w"), indent=2)

    # .md
    md = r.get("report_markdown", "")
    if not md.lstrip().startswith("#"):
        md = f"# {slug}\n\n" + md
    (ROOT / "parts" / "validated" / f"{slug}.md").write_text(md, encoding="utf-8")
    # promote json + drop orphan candidate .gb
    (ROOT / "parts" / "validated" / f"{slug}.json").write_text(
        json.dumps(d, indent=2), encoding="utf-8")
    cand.unlink()
    gb = ROOT / "parts" / "candidate" / f"{slug}.gb"
    if gb.exists():
        gb.unlink()
    print(f"[{slug}] promoted -> validated (claims {len(claims)}, refs {len(refs)}, "
          f"src ok: {not d['provenance']['sequence_source'].startswith('FILL IN')})")


if __name__ == "__main__":
    main()
