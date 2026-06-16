#!/usr/bin/env python3
"""Validate every canonical ``<slug>.json`` against ``schema/part.schema.json``.

Run in CI as the write-side gate (the JSON is the authored source of truth).
Exits non-zero and lists every problem on failure.

Usage:
    python tools/validate_parts.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "part.schema.json"


def _completeness_problems(name: str, data: dict) -> list[str]:
    """A *validated* part must be a curated record, not just a sequence: a real
    sourced provenance, an SO-typed main feature, >=1 reference and >=1
    functional_claim (the ``.md`` page is checked separately). A *candidate* is a
    bare part (sequence + minimal info) and is exempt.

    Legacy parts migrated from GenBank (``provenance.migrated_from`` with no
    ``sequence_source``) are grandfathered on the sourcing criterion only -- they
    were validated under the old rule; re-source them on next touch.
    """
    out: list[str] = []
    prov = data.get("provenance") or {}
    ss = str(prov.get("sequence_source") or "")
    grandfathered = bool(prov.get("migrated_from")) and not ss
    if (not ss or ss.startswith("FILL IN")) and not grandfathered:
        out.append(f"{name}: validated part needs a real provenance.sequence_source")
    # Require *substantive* records, not just non-empty lists: a reference must
    # identify a work, and a functional claim must cite a source -- otherwise an
    # empty {} placeholder would clear the bar (the schema allows content-free
    # reference/source objects).
    refs = [r for r in (data.get("references") or [])
            if r.get("title") or r.get("pubmed_id") or r.get("doi") or r.get("authors")]
    if not refs:
        out.append(f"{name}: validated part needs >=1 reference (with a title/PMID/DOI)")
    claims = [c for c in (data.get("functional_claims") or [])
              if (c.get("source") or {}).get("pmid")
              or (c.get("source") or {}).get("doi")
              or (c.get("source") or {}).get("url")]
    if not claims:
        out.append(f"{name}: validated part needs >=1 functional_claim with a cited source")
    feats = data.get("features") or []
    main = next((f for f in feats if "parent" not in (f.get("qualifiers") or {})), None)
    so = [x for x in (main or {}).get("qualifiers", {}).get("db_xref", [])
          if str(x).startswith("SO:")] if main else []
    if not so:
        out.append(f"{name}: validated part's main feature needs an SO db_xref")
    return out


def _claim_tier_problems(name: str, data: dict) -> list[str]:
    """The review tier must be *earned*: a claim may only be ``ai-cross-checked``
    or ``expert-reviewed`` if its evidence quote actually comes from the primary
    source (``source.quote_source == "primary"``) and it cites that source. Until
    then it stays ``ai-generated`` -- so the tier (and the site's trust marker)
    means a real verification happened, not just a label. Applies to every part."""
    out: list[str] = []
    for c in data.get("functional_claims") or []:
        rs = c.get("review_status")
        if rs not in ("ai-cross-checked", "expert-reviewed"):
            continue
        cid = c.get("id")
        src = c.get("source") or {}
        if src.get("quote_source") != "primary":
            out.append(f"{name}: claim {cid!r} is '{rs}' but its quote is not from "
                       f"the primary source (set quote_source to 'primary' after "
                       f"checking the paper, or keep review_status 'ai-generated')")
        elif not src.get("quote"):
            out.append(f"{name}: claim {cid!r} is '{rs}' but carries no verbatim "
                       f"source quote")
        if not (src.get("pmid") or src.get("doi") or src.get("url")):
            out.append(f"{name}: claim {cid!r} is '{rs}' but cites no source "
                       f"(pmid/doi/url)")
    return out


def _coordinate_problems(name: str, data: dict) -> list[str]:
    """Every feature must lie within the sequence: 0 <= start < end <= len(seq).
    The JSON Schema can bound start/end individually but can't compare them or
    check them against the sequence length, so do it here (catches inverted or
    out-of-range coordinates before they reach the .gb / RDF build)."""
    out: list[str] = []
    n = len(data.get("sequence") or "")
    for grp in ("features", "uniprot_features"):
        for f in data.get(grp) or []:
            s, e = f.get("start"), f.get("end")
            if not isinstance(s, int) or not isinstance(e, int):
                continue  # type errors are the schema's job
            if not (0 <= s < e <= n):
                tag = f.get("label") or (f.get("qualifiers", {}).get("label", [""]) or [""])[0] \
                    or f.get("type", "?")
                out.append(f"{name}: {grp} {tag!r} has out-of-range coordinates "
                           f"start={s} end={e} (sequence length {n})")
    return out


def problems() -> list[str]:
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    out: list[str] = []
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for jf in sorted(d.glob("*.json")):
            data = json.loads(jf.read_text(encoding="utf-8"))
            # The first parent-less feature is the part; a validated part (under
            # validated/) must have a sibling .md, a candidate must not.
            for err in validator.iter_errors(data):
                out.append(f"{jf.name}: {err.message}")
            if data.get("slug") != jf.stem:
                out.append(f"{jf.name}: slug {data.get('slug')!r} != filename")
            # Enforced for every part: coordinates in-bounds + earned review tier.
            out.extend(_coordinate_problems(jf.name, data))
            out.extend(_claim_tier_problems(jf.name, data))
            md = jf.with_suffix(".md")
            is_validated = d.name == "validated"
            if is_validated:
                if not md.exists():
                    out.append(f"{jf.name}: validated part missing its .md page")
                elif not md.read_text(encoding="utf-8").strip():
                    out.append(f"{jf.name}: validated part's .md page is empty")
                out.extend(_completeness_problems(jf.name, data))
            elif md.exists():
                out.append(f"{jf.name}: candidate part must not have a .md page")
    return out


def main() -> None:
    probs = problems()
    n = sum(1 for _ in (ROOT / "parts").glob("*/*.json"))
    if probs:
        print(f"part JSON validation FAILED ({len(probs)} problems):")
        for p in probs:
            print("  ", p)
        sys.exit(1)
    print(f"part JSON validation passed ({n} files clean).")


if __name__ == "__main__":
    main()
