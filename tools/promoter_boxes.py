#!/usr/bin/env python3
"""Predict a sigma-70 promoter's -35 and -10 boxes by fixed criteria.

A promoter part may declare its -35 and -10 hexamers as sub-features with an
evidence level (``AUTHORING.md``, "Evidence for a sub-feature"):

* ``experimental`` -- a primary source gives the position; the child cites it.
* ``predicted`` -- the curator's reading of the sequence, allowed only when this
  module's criteria pick exactly one reading. Two curators running it on the
  same sequence get the same answer, and ``check_library.py`` re-runs it on
  every declared predicted box.

The criteria (owner's rule, 2026-11-17; spacing and start distance after Harley
& Reynolds 1987, PMID 3550697, who found 92% of 263 E. coli promoters with a
17 +/- 1 bp spacer and 75% of start points 7 +/- 1 bases after the -10):

1. a -35 and a -10 hexamer separated by a 16-18 bp spacer;
2. at least 4 of 6 consensus bases in each (TTGACA, TATAAT), 9 of 12 together;
3. the -10 carries the A at its position 2 and the T at its position 6 (TAtaaT);
4. if a transcription start is known, it lies 5-9 bases after the -10's last base;
5. no other reading in the part on the same strand scores as well or better
   (a competing reading of equal score makes the prediction ambiguous);
6. no positional source contradicts it (checked by the curator, recorded in the
   part's note).

Usage::

    python tools/promoter_boxes.py --slug Pcat            # a part, its own strand
    python tools/promoter_boxes.py --seq ACGT... [--tss 41]
    python tools/promoter_boxes.py --scan                 # parts that would gain boxes
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
M35, M10 = "TTGACA", "TATAAT"
SPACERS = (16, 17, 18)
START_GAP = range(5, 10)      # bases from the -10's last base to +1 (+1 is the 5th..9th)


@dataclass(frozen=True)
class Reading:
    """One -35/-10 pair, positions 0-based on the sequence as read 5'->3'."""
    start35: int
    start10: int
    box35: str
    box10: str

    @property
    def score35(self) -> int:
        return sum(a == b for a, b in zip(self.box35, M35))

    @property
    def score10(self) -> int:
        return sum(a == b for a, b in zip(self.box10, M10))

    @property
    def score(self) -> int:
        return self.score35 + self.score10

    @property
    def spacer(self) -> int:
        return self.start10 - (self.start35 + 6)


def readings(seq: str) -> list[Reading]:
    """Every -35/-10 pair with a 16-18 bp spacer, best score first."""
    s = seq.upper()
    out = []
    for i in range(len(s) - 5):
        for sp in SPACERS:
            j = i + 6 + sp
            if j + 6 <= len(s):
                out.append(Reading(i, j, s[i:i + 6], s[j:j + 6]))
    return sorted(out, key=lambda r: (-r.score, r.start35))


def qualifies(r: Reading, tss: int | None = None) -> bool:
    """Criteria 1-4 for one reading (``tss``: 0-based index of +1, if mapped)."""
    if r.score35 < 4 or r.score10 < 4 or r.score < 9:
        return False
    if r.box10[1] != "A" or r.box10[5] != "T":
        return False
    if tss is not None and (tss - (r.start10 + 5)) not in START_GAP:
        return False
    return True


def predict(seq: str, tss: int | None = None) -> tuple[Reading | None, str]:
    """The single reading the criteria allow, or None with the reason."""
    rs = readings(seq)
    ok = [r for r in rs if qualifies(r, tss)]
    if not ok:
        best = rs[0] if rs else None
        why = "no reading meets criteria 1-4"
        if best:
            why += (f"; best is {best.box35}..{best.box10} at {best.start35 + 1}/"
                    f"{best.start10 + 1} ({best.score35}+{best.score10}/12)")
        return None, why
    best = ok[0]
    rivals = [r for r in rs if r != best and r.score >= best.score]
    if rivals:
        r = rivals[0]
        return None, (f"ambiguous: {best.box35}..{best.box10} at {best.start35 + 1}/"
                      f"{best.start10 + 1} and {r.box35}..{r.box10} at {r.start35 + 1}/"
                      f"{r.start10 + 1} both score {best.score}/12")
    return best, (f"{best.box35} at {best.start35 + 1}-{best.start35 + 6}, {best.box10} at "
                  f"{best.start10 + 1}-{best.start10 + 6} (1-based), spacer {best.spacer}, "
                  f"{best.score35}+{best.score10}/12 consensus bases")


def _part(slug: str) -> dict:
    for st in ("validated", "candidate"):
        p = ROOT / "parts" / st / f"{slug}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
    sys.exit(f"no part {slug}")


def _has_boxes(d: dict) -> bool:
    """The part already declares a -35 or a -10 (by class or by label)."""
    for f in d["features"][1:]:
        q = f["qualifiers"]
        if (q.get("regulatory_class") or [""])[0] in ("minus_35_signal", "minus_10_signal"):
            return True
        if any(t in (q.get("label") or [""])[0] for t in ("-35", "-10")):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--slug")
    ap.add_argument("--seq")
    ap.add_argument("--tss", type=int, help="1-based position of +1 on the sequence")
    ap.add_argument("--scan", action="store_true",
                    help="list promoter parts without boxes that the criteria would give boxes")
    a = ap.parse_args()
    tss = a.tss - 1 if a.tss else None
    if a.scan:
        n = 0
        for jf in sorted(ROOT.glob("parts/*/*.json")):
            d = json.loads(jf.read_text(encoding="utf-8"))
            if d["features"][0]["type"] != "promoter" or d["molecule_type"] != "DNA" or _has_boxes(d):
                continue
            r, why = predict(d["sequence"])
            if r:
                n += 1
                print(f"{d['features'][0]['qualifiers']['label'][0]}: {why}")
        print(f"{n} promoter part(s) without boxes would gain predicted boxes")
        return 0
    seq = _part(a.slug)["sequence"] if a.slug else (a.seq or "")
    r, why = predict(seq, tss)
    print(("PREDICTED " if r else "NONE ") + why)
    return 0


if __name__ == "__main__":
    sys.exit(main())
