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
