#!/usr/bin/env python3
"""Regenerate every part's ``.gb`` from its canonical ``<slug>.json``.

The ``.gb`` is a *generated* projection of the JSON spine (bench-format, still a
first-class downloadable artifact that the catalog/RDF builders read). Run this
after editing any ``<slug>.json``; CI guards that the committed ``.gb`` files are
up to date, the same way it guards ``catalog.json``.

Usage:
    python tools/build_gb.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from part_json import write_gb_from_json  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    n = 0
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for jf in sorted(d.glob("*.json")):
            data = json.loads(jf.read_text(encoding="utf-8"))
            write_gb_from_json(data, jf.with_suffix(".gb"))
            n += 1
    print(f"regenerated {n} .gb from canonical JSON")


if __name__ == "__main__":
    main()
