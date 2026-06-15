#!/usr/bin/env python3
"""Detect overlap between a part (or sequence) and the existing catalog.

Before adding a new part, check whether its sequence already overlaps one in the
catalog — a sub/superset, a near-identical sibling, or a partial overlap — so you can
**refine the existing part rather than add a near-duplicate** (the catalog's
"overlap → refine" policy; cf. ColE1 / ColE1_AT). Local and fast (no NCBI): a
strand-independent k-mer pre-filter plus an exact-containment check on both strands.

A flagged overlap is a prompt to decide refine-vs-add — and remember that **part
boundaries are not a trivial bioinformatic call** (see AUTHORING.md): re-delimiting a
part should rest on experimental data (truncation / mutational scanning / genetics),
not sequence overlap alone.

Usage::

    python tools/catalog_overlap.py --slug ColE1_AT
    python tools/catalog_overlap.py --seq ACGT... [--min-overlap 30] [--k 16]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_COMP = str.maketrans("ACGT", "TGCA")


def _rc(s: str) -> str:
    return s.translate(_COMP)[::-1]


def canon_kmers(seq: str, k: int = 16) -> set[str]:
    """Strand-independent k-mer set (each k-mer canonicalized to min(self, revcomp))."""
    s = seq.upper()
    return {min(s[i:i + k], _rc(s[i:i + k])) for i in range(len(s) - k + 1)}


def containment(query: str, subject: str) -> str | None:
    """Exact, strand-aware containment relation of query vs subject (or None)."""
    q, s = query.upper(), subject.upper()
    qr = _rc(q)
    if q == s or qr == s:
        return "identical"
    if q in s or qr in s:
        return "contained_by"          # the whole query sits inside subject
    if s in q or _rc(s) in q:
        return "contains"              # the whole subject sits inside query
    return None


def relation(query: str, subject: str, k: int = 16, min_overlap: int = 30) -> dict | None:
    """Classify how query overlaps subject, or None if they don't meaningfully overlap."""
    exact = containment(query, subject)
    qk, sk = canon_kmers(query, k), canon_kmers(subject, k)
    shared = len(qk & sk)
    if shared == 0 and exact is None:
        return None
    qf = shared / max(len(qk), 1)
    sf = shared / max(len(sk), 1)
    est = shared + k - 1 if shared else min(len(query), len(subject))
    rel = exact
    if rel is None:
        if qf >= 0.9 and sf >= 0.9:
            rel = "near_identical"
        elif sf >= 0.9:
            rel = "contains_approx"       # subject ~entirely within query
        elif qf >= 0.9:
            rel = "contained_by_approx"   # query ~entirely within subject
        elif est >= min_overlap:
            rel = "overlap"
        else:
            return None
    return {"relation": rel, "shared_kmers": shared,
            "q_frac": round(qf, 3), "p_frac": round(sf, 3),
            "est_overlap_bp": int(est), "exact": exact is not None}


def load_catalog() -> list[tuple[str, str, str]]:
    out = []
    for status in ("validated", "candidate"):
        for jf in sorted((ROOT / "parts" / status).glob("*.json")):
            d = json.loads(jf.read_text(encoding="utf-8"))
            if d.get("molecule_type") == "protein":
                continue                  # nucleotide overlap only
            out.append((d["slug"], status, d["sequence"].upper()))
    return out


def scan(query: str, exclude: str | None = None, k: int = 16, min_overlap: int = 30) -> list[dict]:
    hits = []
    for slug, status, seq in load_catalog():
        if slug == exclude:
            continue
        r = relation(query, seq, k, min_overlap)
        if r:
            hits.append({"slug": slug, "status": status, "len": len(seq), **r})
    hits.sort(key=lambda h: -h["shared_kmers"])
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description="Find catalog parts overlapping a part/sequence.")
    ap.add_argument("--slug")
    ap.add_argument("--seq")
    ap.add_argument("--k", type=int, default=16)
    ap.add_argument("--min-overlap", type=int, default=30)
    a = ap.parse_args()

    seq, exclude = (a.seq or "").upper(), None
    if a.slug:
        for status in ("validated", "candidate"):
            p = ROOT / "parts" / status / f"{a.slug}.json"
            if p.exists():
                seq = json.loads(p.read_text(encoding="utf-8"))["sequence"].upper()
                exclude = a.slug
                break
        else:
            sys.exit(f"part {a.slug!r} not found")
    if not seq:
        sys.exit("need --slug or --seq")
    if len(seq) < a.k:
        sys.exit(f"sequence shorter than k={a.k}")

    hits = scan(seq, exclude, a.k, a.min_overlap)
    print(json.dumps({"query": a.slug, "qlen": len(seq), "k": a.k,
                      "n_overlaps": len(hits), "overlaps": hits[:25]}, indent=2))


if __name__ == "__main__":
    main()
