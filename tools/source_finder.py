#!/usr/bin/env python3
"""Find the best reputable, oldest, 100%-identity deposited source for a part.

Automates the manual sourcing loop the ColE1 work exposed:

* **Protein part** -> its source is the verified UniProt accession (from the
  ``uniprot_import`` block); no BLAST needed.
* **DNA part** -> BLAST vs NCBI ``nt`` (via ``tools/blast.py``), **date-bracketed** so
  the score-ranked top-N can't hide old deposits, and return the *oldest* full-length
  100% carriers (with a name-quality flag). Then **diverge** the part against any
  reference accessions you pass (canonical plasmids): report ``% identity``, the diff
  **positions in part coordinates**, and whether they sit at the **edge** (a boundary
  question -> refine the boundaries) or **internal** (a real variant -> consider a
  sibling part, like ``ColE1_AT``). A part whose exact sequence matches only odd/modern
  vectors but diverges from the canonical reference is flagged as likely non-canonical.

Pure analysis (``divergence`` / ``classify_location`` / ``pick_best``) is unit-tested;
the BLAST orchestration reuses ``blast.py``. Needs ``requests`` + ``biopython``.

Usage::

    python tools/source_finder.py --slug ColE1 --refs J01749,L08752
    python tools/source_finder.py --slug bla                 # protein -> UniProt
    python tools/source_finder.py --seq ACGT... --window 1980:2005
    python tools/source_finder.py --slug ColE1 --rid <RID>   # re-fetch a finished BLAST
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))


# ---- part loading ----------------------------------------------------------
def load_part(slug: str) -> tuple[dict, str]:
    for status in ("validated", "candidate"):
        p = ROOT / "parts" / status / f"{slug}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8")), status
    sys.exit(f"part {slug!r} not found under parts/")


# ---- pure analysis (unit-tested) -------------------------------------------
def classify_location(positions: list[int], qlen: int, edge_margin: int = 12) -> str:
    """Where do the differences sit? exact (none) / edge / internal / mixed."""
    if not positions:
        return "exact"
    at_edge = [p < edge_margin or p >= qlen - edge_margin for p in positions]
    if all(at_edge):
        return "edge"
    if not any(at_edge):
        return "internal"
    return "mixed"


def divergence(query: str, subject: str, edge_margin: int = 12) -> dict:
    """How the part (``query``) diverges from a ``subject`` sequence.

    Local-aligns (handling a circular subject + both strands) and returns identity,
    gap count, the mismatch positions **in query coordinates**, and a location class
    (exact / edge / internal / mixed). ``subject`` may be a whole plasmid."""
    from Bio import Align
    from Bio.Seq import Seq

    q = query.upper()
    qlen = len(q)
    dbl = (subject + subject).upper()                  # circular
    aligner = Align.PairwiseAligner()
    aligner.mode = "local"
    aligner.match_score, aligner.mismatch_score = 2, -3
    aligner.open_gap_score, aligner.extend_gap_score = -5, -2

    best = None
    for strand, s in (("+", dbl), ("-", str(Seq(dbl).reverse_complement()))):
        try:
            aln = aligner.align(s, q)[0]
        except (ValueError, IndexError):
            continue
        sblocks, qblocks = aln.aligned[0], aln.aligned[1]
        mism, cov = [], 0
        for (ss, se), (qs, qe) in zip(sblocks, qblocks):
            cov += int(qe - qs)
            for i in range(int(qe - qs)):
                if q[qs + i] != s[ss + i]:
                    mism.append(int(qs + i))
        gap = (qblocks[-1][1] - qblocks[0][0] - cov) + \
              ((sblocks[-1][1] - sblocks[0][0]) - (se - ss if len(sblocks) == 1 else cov))
        score = cov - len(mism)
        if best is None or score > best["_score"]:
            best = {"_score": score, "strand": strand, "coverage_bp": int(cov),
                    "mismatch_positions": sorted(mism), "n_gap": int(max(gap, 0))}
    if best is None:
        return {"identity_pct": 0.0, "coverage_bp": 0, "qlen": qlen, "n_mismatch": 0,
                "n_gap": 0, "mismatch_positions": [], "location": "none", "strand": ""}
    best.pop("_score")
    n_mis = len(best["mismatch_positions"])
    full = best["coverage_bp"] >= qlen and best["n_gap"] == 0
    best.update({
        "qlen": qlen,
        "n_mismatch": n_mis,
        # Identity over the full query, penalizing gaps: matches / (qlen + gaps).
        # An indel (n_gap > 0) or any uncovered query base therefore drops this
        # below 100, so only a true full-length exact hit reports 100.0.
        "identity_pct": round(
            100 * (best["coverage_bp"] - n_mis) / (qlen + best["n_gap"]), 2),
        "location": classify_location(best["mismatch_positions"], qlen, edge_margin)
        if full else "partial",
    })
    return best


_NAMED = re.compile(r"\bp[A-Z][A-Za-z0-9._-]{1,}\b")


def looks_named(title: str) -> bool:
    """True if the deposit title names a recognizable plasmid (pXXX) vector."""
    t = title or ""
    return bool(_NAMED.search(t)) and ("vector" in t.lower() or "plasmid" in t.lower())


def pick_best(candidates: list[dict]) -> dict | None:
    """Pick the recommended source: the oldest deposit, preferring a *named* vector
    when several share the oldest date. ``candidates`` are dicts with date/title."""
    if not candidates:
        return None
    rows = sorted(candidates, key=lambda c: (c.get("date") or "9999",
                                             not c.get("named", looks_named(c.get("title", "")))))
    return rows[0]


# ---- protein source (no BLAST) ---------------------------------------------
def protein_source(part: dict) -> dict | None:
    imp = part.get("uniprot_import") or {}
    acc = imp.get("accession") or next(
        (x for x in (part["features"][0]["qualifiers"].get("db_xref") or [])
         if str(x).startswith(("UniProt:", "NCBI:"))), None)
    if not acc:
        return None
    return {"kind": "protein", "accession": acc,
            "match": imp.get("status"), "identity": imp.get("identity"),
            "sequence_source": (f"{acc} (canonical sequence; {imp.get('status', 'see UniProt')}"
                                f"{', identity ' + str(imp.get('identity')) if imp.get('identity') is not None else ''}),"
                                " verified by tools/import_uniprot_features.py")}


# ---- BLAST orchestration (reuses blast.py) ---------------------------------
def find_dna_sources(seq: str, window: str, rid: str | None, max_wait: int) -> dict:
    import blast
    if rid is None:
        rid, _ = blast.submit(seq, entrez=f"{window}[PDAT]")
        print(f"submitted RID={rid} (window {window})", file=sys.stderr)
        blast.wait(rid, max_wait)
    qlen, hits = blast.perfect_hits(blast.results_json(rid))
    md = blast._meta([a for a, _ in hits])
    cands = [{"accession": a,
              "date": md.get(a, {}).get("date", ""),
              "title": (md.get(a, {}).get("title") or t)[:90],
              "named": looks_named(md.get(a, {}).get("title") or t)} for a, t in hits]
    cands.sort(key=lambda c: c["date"] or "9999")
    return {"rid": rid, "qlen": qlen, "n_perfect": len(hits),
            "candidates_oldest_first": cands[:20], "recommended": pick_best(cands)}


def _fetch(acc: str) -> str:
    import urllib.request
    from io import StringIO
    from Bio import SeqIO
    u = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id="
         f"{acc}&rettype=gb&retmode=text")
    return str(SeqIO.read(StringIO(urllib.request.urlopen(u, timeout=60).read().decode()),
                          "genbank").seq)


def main() -> None:
    ap = argparse.ArgumentParser(description="Find the best 100%-identity deposited source for a part.")
    ap.add_argument("--slug")
    ap.add_argument("--seq")
    ap.add_argument("--refs", default="", help="comma-separated reference accessions to diverge against (e.g. J01749,L08752)")
    ap.add_argument("--window", default="1980:2010", help="ENTREZ deposit-date window for the oldest-source search")
    ap.add_argument("--rid", help="re-fetch a finished BLAST RID")
    ap.add_argument("--max-wait", type=int, default=300)
    a = ap.parse_args()

    part, seq = None, (a.seq or "").upper()
    if a.slug:
        part, _ = load_part(a.slug)
        seq = part["sequence"].upper()
    if not seq and not a.rid:
        sys.exit("need --slug, --seq, or --rid")

    out: dict = {"slug": a.slug, "qlen": len(seq)}

    # protein: the source is the UniProt accession, no BLAST
    if part and part.get("molecule_type") == "protein":
        out["protein"] = protein_source(part)
        print(json.dumps(out, indent=2))
        return

    out["dna_sources"] = find_dna_sources(seq, a.window, a.rid, a.max_wait)

    if a.refs:
        out["divergence_vs_refs"] = {}
        for acc in [r.strip() for r in a.refs.split(",") if r.strip()]:
            try:
                out["divergence_vs_refs"][acc] = divergence(seq, _fetch(acc))
            except Exception as exc:  # noqa: BLE001
                out["divergence_vs_refs"][acc] = {"error": str(exc)}
        # flag the ColE1-style situation: exact only in modern vectors, off from canonical
        canon_exact = any(d.get("location") == "exact"
                          for d in out["divergence_vs_refs"].values() if isinstance(d, dict))
        rec = out["dna_sources"].get("recommended") or {}
        if not canon_exact and rec.get("date", "9999") >= "2010":
            out["flag"] = ("exact match only to recent/odd deposits and NOT 100% to the "
                           "canonical references -> the stored sequence is likely non-canonical; "
                           "consider refining to a reference, or carry it as a labelled variant.")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
