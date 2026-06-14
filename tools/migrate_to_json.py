#!/usr/bin/env python3
"""One-time migration: generate the canonical ``<slug>.json`` for every part from
its current ``.gb``. Idempotent and safe to re-run (it just re-derives the JSON
from the GenBank record). After this, ``<slug>.json`` is the source of truth and
``build_gb.py`` regenerates the ``.gb`` from it.

Usage:
    python tools/migrate_to_json.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from Bio import SeqIO

sys.path.insert(0, str(Path(__file__).resolve().parent))
from part_json import record_to_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    n = 0
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for gb in sorted(d.glob("*.gb")):
            rec = SeqIO.read(str(gb), "genbank")
            data = record_to_json(rec, gb.stem)
            gb.with_suffix(".json").write_text(
                json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8")
            n += 1
    print(f"migrated {n} parts to canonical JSON")


if __name__ == "__main__":
    main()
