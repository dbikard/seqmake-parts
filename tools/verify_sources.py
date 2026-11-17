#!/usr/bin/env python3
"""Check that each part's cited record really contains the part's sequence.

``provenance.sequence_source`` is what makes a part *sourced* — the claim that
its bases were taken from a named deposit. This re-fetches every accession named
there (or in the main feature's ``db_xref``) and checks the part's sequence is
in it: as a substring on either strand for a DNA part, as a substring of the
protein for a protein part, and, for a protein part cited to a nucleotide
record, as a substring of that record's six-frame translation.

It needs the network, so it is **not** part of ``check_library.py`` / CI: run it
when sourcing a part, and when reviewing a change to sourcing. Only
``sequence_source`` and the main feature's ``db_xref`` are read: a related record
named for context (the natural protein a designed tag comes from) belongs in
``provenance.derived_from``, and a near-but-not-exact deposit in
``provenance.closest_deposit``; neither makes a part sourced.

Usage::

    python tools/verify_sources.py                 # every sourced part
    python tools/verify_sources.py --slug ColE1 --slug Pneo
    python tools/verify_sources.py --quiet         # only the failures
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / ".source-cache"          # git-ignored; a polite local record store
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
HEADERS = {"User-Agent": "seqmake-parts/1.0 (+https://github.com/dbikard/seqmake-parts)"}
TOOL = "seqmake-parts"

# Accessions as they appear in a provenance string or a db_xref.
NUC = re.compile(r"\b(?:[A-Z]{1}\d{5}|[A-Z]{2}\d{6}|[A-Z]{2}_\d{6,9}|[A-Z]{4}\d{8})(?:\.\d+)?\b")
PROT = re.compile(r"\b(?:(?:WP|NP|YP|XP|AP)_\d{6,9}|[A-Z]{3}\d{5,7})(?:\.\d+)?\b")
UNIPROT = re.compile(r"\b(?:UniProt:)?([OPQ][0-9][A-Z0-9]{3}[0-9]|[A-NR-Z][0-9](?:[A-Z][A-Z0-9]{2}[0-9]){1,2})\b")
IGEM = re.compile(r"\bBBa_[A-Za-z0-9]+\b")
_COMP = str.maketrans("ACGTacgt", "TGCAtgca")


def _rc(s: str) -> str:
    return s.translate(_COMP)[::-1]


def _get(url: str, params: dict | None = None) -> str:
    import requests
    for attempt in range(4):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r.text
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return ""


def fetch(kind: str, acc: str) -> str:
    """The sequence of one record (cached), as a bare uppercase string."""
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{kind}-{acc}.txt"
    if f.exists():
        return f.read_text(encoding="utf-8")
    if kind == "uniprot":
        txt = _get(f"https://rest.uniprot.org/uniprotkb/{acc}.fasta")
        seq = "".join(txt.splitlines()[1:])
    elif kind == "igem":
        txt = _get(f"https://api.registry.igem.org/v1/parts/slugs/"
                   f"{acc.lower().replace('_', '-')}")
        try:
            seq = (json.loads(txt).get("sequence") or "")
        except json.JSONDecodeError:
            seq = ""
    else:
        db = "protein" if kind == "protein" else "nuccore"
        txt = _get(EUTILS, {"db": db, "id": acc, "rettype": "fasta",
                            "retmode": "text", "tool": TOOL})
        seq = "".join(txt.splitlines()[1:])
    seq = seq.strip().upper()
    if seq:
        f.write_text(seq, encoding="utf-8")
    return seq


def _frames(dna: str):
    from Bio.Seq import Seq
    for s in (dna, _rc(dna)):
        for fr in range(3):
            chunk = s[fr:fr + 3 * ((len(s) - fr) // 3)]
            yield str(Seq(chunk).translate())


def accessions(data: dict) -> list[tuple[str, str]]:
    """(kind, accession) pairs cited by a part, in the order to try them."""
    src = str((data.get("provenance") or {}).get("sequence_source") or "")
    xrefs = " ".join(data["features"][0]["qualifiers"].get("db_xref", []))
    text = f"{src} {xrefs}"
    out: list[tuple[str, str]] = []
    for m in IGEM.findall(text):
        out.append(("igem", m))
    for m in PROT.findall(text):
        out.append(("protein", m))
    for m in UNIPROT.findall(text):
        if ("UniProt:" + m) in text or "UniProt" in text:
            out.append(("uniprot", m))
    for m in NUC.findall(text):
        if not any(m == a for _, a in out):
            out.append(("nuc", m))
    seen, uniq = set(), []
    for k, a in out:
        if (k, a) not in seen:
            seen.add((k, a))
            uniq.append((k, a))
    return uniq


def verify(data: dict) -> tuple[str, str]:
    """(verdict, detail) for one part: ok / FAIL / skipped."""
    seq = data["sequence"].upper()
    protein = data["molecule_type"] == "protein"
    accs = accessions(data)
    if not accs:
        return "skipped", "no accession in provenance.sequence_source"
    tried = []
    for kind, acc in accs:
        rec = fetch(kind, acc)
        if not rec:
            tried.append(f"{acc} (not fetched)")
            continue
        if protein:
            if seq in rec:
                return "ok", f"{acc} contains the {len(seq)} aa"
            if set(rec) <= set("ACGTUN") and any(seq in t for t in _frames(rec)):
                return "ok", f"{acc} encodes the {len(seq)} aa"
        else:
            circ = rec + rec[:len(seq)]
            if seq in circ or _rc(seq) in circ:
                return "ok", f"{acc} contains the {len(seq)} bp"
        tried.append(acc)
    return "FAIL", "not contained in " + ", ".join(tried)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--slug", action="append", default=[])
    ap.add_argument("--quiet", action="store_true", help="print only failures")
    a = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from part_json import is_sourced  # noqa: E402

    n = fails = 0
    for jf in sorted(ROOT.glob("parts/*/*.json")):
        data = json.loads(jf.read_text(encoding="utf-8"))
        if a.slug and data["slug"] not in a.slug:
            continue
        if not is_sourced(data):
            continue
        n += 1
        verdict, detail = verify(data)
        fails += verdict == "FAIL"
        if verdict != "ok" or not a.quiet:
            print(f"{verdict:8} {data['slug']}: {detail}")
    print(f"\n{n} sourced part(s) checked, {fails} failure(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
