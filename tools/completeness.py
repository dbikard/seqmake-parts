#!/usr/bin/env python3
"""Datasheet-completeness audit — which parts are MISSING claims their peers have.

Correctness (does a claim hold?) is the cross-check engine's job; this is the orthogonal
question of COMPLETENESS (is an important claim absent?). Rather than hardcode a fuzzy
"expected slots per part class" table, it is **peer-derived**: parts are grouped by their
main feature type, and a datasheet slot counts as *expected* for that group when most peers
carry it. A part missing an expected slot is flagged. Self-tuning from the corpus; no LLM.

Only ``datasheet_slot`` claim types (from schema/claim_types.json) are considered — the
operational parameters a designer selects/operates by — so identity/origin chatter is ignored.
Claim types are canonicalised (aliases resolved) before counting.

This is a triage worklist: a flagged part is a candidate to send through ``/add-part`` (the only
engine that can SOURCE the missing claim). Use ``--json`` for tooling.

Usage:
    python tools/completeness.py                 # audit validated parts
    python tools/completeness.py --all           # include candidate parts
    python tools/completeness.py --threshold 0.5 --min-peers 3
    python tools/completeness.py --type promoter # one feature-type group
    python tools/completeness.py --json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAIM_TYPES = ROOT / "schema" / "claim_types.json"
PARTS_DIRS = {"validated": ROOT / "parts" / "validated",
              "candidate": ROOT / "parts" / "candidate"}


def _vocab() -> dict:
    return json.loads(CLAIM_TYPES.read_text(encoding="utf-8"))


def _main_feature_type(part: dict) -> str | None:
    """The first parent-less feature is the part itself (schema contract)."""
    for f in part.get("features", []):
        if "parent" not in (f.get("qualifiers") or {}):
            return f.get("type")
    feats = part.get("features") or [{}]
    return feats[0].get("type")


def _load_parts(include_candidate: bool) -> list[dict]:
    out = []
    dirs = ["validated"] + (["candidate"] if include_candidate else [])
    for d in dirs:
        for jf in sorted(PARTS_DIRS[d].glob("*.json")):
            p = json.loads(jf.read_text(encoding="utf-8"))
            p["_status"] = d
            out.append(p)
    return out


def audit(threshold: float, min_peers: int, include_candidate: bool,
          only_type: str | None) -> dict:
    voc = _vocab()
    canon = set(voc["claim_types"])
    alias = voc.get("aliases", {})
    slot = {t: voc["claim_types"][t].get("datasheet_slot") for t in canon}
    section = {t: voc["claim_types"][t].get("section") for t in canon}

    def canonical(t: str) -> str:
        return alias.get(t, t)

    parts = _load_parts(include_candidate)

    # Completeness is judged at the datasheet-SECTION level (so a promoter with an
    # `inducer` claim isn't flagged for "missing regulation" — same need, different slot);
    # the specific missing SLOT is named only as an actionable suggestion.
    psec: dict[str, set[str]] = {}     # sections a part has >=1 datasheet claim in
    pslot: dict[str, set[str]] = {}    # the datasheet slots a part has
    by_ftype: dict[str, list[str]] = defaultdict(list)
    meta: dict[str, dict] = {}
    for p in parts:
        slug = p.get("slug")
        ft = _main_feature_type(p) or "?"
        if only_type and ft != only_type:
            continue
        slots = {canonical(c.get("type")) for c in p.get("functional_claims", []) if c.get("type")}
        slots = {t for t in slots if slot.get(t)}
        pslot[slug] = slots
        psec[slug] = {section[t] for t in slots if section.get(t)}
        by_ftype[ft].append(slug)
        meta[slug] = {"feature_type": ft, "status": p["_status"],
                      "n_claims": len(p.get("functional_claims", []))}

    groups = []
    flagged: dict[str, list[dict]] = {}
    for ft, slugs in sorted(by_ftype.items()):
        n = len(slugs)
        if n < min_peers:
            groups.append({"feature_type": ft, "n_parts": n, "skipped": "too few peers",
                           "expected": [], "parts_with_gaps": []})
            continue
        sec_freq, slot_freq = Counter(), Counter()
        for s in slugs:
            sec_freq.update(psec[s])
            slot_freq.update(pslot[s])
        need = max(2, int(round(threshold * n)))
        expected = {sec: sec_freq[sec] for sec in sec_freq if sec_freq[sec] >= need}
        # within each section, rank the peer-common slots to suggest
        sec_slots: dict[str, list[str]] = defaultdict(list)
        for t, c in slot_freq.most_common():
            if section.get(t) in expected:
                sec_slots[section[t]].append(t)
        gaps_here = []
        for s in slugs:
            miss = []
            for sec in sorted(expected, key=lambda x: -expected[x]):
                if sec not in psec[s]:
                    miss.append({"section": sec, "coverage": f"{expected[sec]}/{n}",
                                 "suggest": sec_slots.get(sec, [])})
            if miss:
                flagged[s] = miss
                gaps_here.append({"part": s, "missing": miss})
        groups.append({
            "feature_type": ft, "n_parts": n, "peer_threshold": need,
            "expected_sections": [{"section": sec, "coverage": f"{expected[sec]}/{n}",
                                   "slots": sec_slots.get(sec, [])}
                                  for sec in sorted(expected, key=lambda x: -expected[x])],
            "parts_with_gaps": gaps_here,
        })

    return {"threshold": threshold, "min_peers": min_peers,
            "n_parts_audited": len(psec), "n_flagged": len(flagged),
            "groups": groups, "flagged": flagged, "meta": meta}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--threshold", type=float, default=0.6,
                    help="fraction of peers that must carry a slot for it to be 'expected' (default 0.6)")
    ap.add_argument("--min-peers", type=int, default=4,
                    help="min parts in a feature-type group to audit it (default 4)")
    ap.add_argument("--all", action="store_true", help="include candidate parts")
    ap.add_argument("--type", dest="only_type", help="restrict to one feature type")
    ap.add_argument("--json", action="store_true", help="print the full report as JSON")
    args = ap.parse_args()

    rep = audit(args.threshold, args.min_peers, args.all, args.only_type)
    if args.json:
        print(json.dumps(rep, indent=2))
        return 0

    print(f"Datasheet completeness — {rep['n_parts_audited']} part(s) audited, "
          f"{rep['n_flagged']} with gaps (by datasheet section; peer threshold "
          f"{int(args.threshold*100)}%).\n")
    for g in rep["groups"]:
        if g.get("skipped"):
            continue
        exp = ", ".join(f"{e['section']} ({e['coverage']})" for e in g["expected_sections"]) or "—"
        print(f"■ {g['feature_type']}  ({g['n_parts']} parts) — peers cover: {exp}")
        for pg in g["parts_with_gaps"]:
            for m in pg["missing"]:
                sug = f" → try: {', '.join(m['suggest'][:3])}" if m["suggest"] else ""
                print(f"    {pg['part']:26s} no «{m['section']}» claim  ({m['coverage']} peers have one){sug}")
        if not g["parts_with_gaps"]:
            print("    (all peers complete)")
        print()
    if rep["n_flagged"]:
        print("→ send flagged parts through /add-part to source the missing claims.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
