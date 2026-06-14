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
            if is_validated and not md.exists():
                out.append(f"{jf.name}: validated part missing its .md page")
            if not is_validated and md.exists():
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
