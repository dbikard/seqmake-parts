#!/usr/bin/env python3
"""Content lint for the public catalog.

The catalog is a standalone, lab-agnostic, tool-agnostic public resource. Part
content describes what a part *is*. The lint scans the canonical record
(``parts/**/*.json`` — the authored source of truth, including the
``functional_claims`` prose that lives only there), the generated GenBank
(``parts/**/*.gb``), and the curated docs (``parts/**/*.md``). It must never:

  - name the consuming tool (``seqmake``) — the catalog stands on its own;
  - reference a specific lab, person, or internal/unpublished plasmid lineage
    (``our lab``, ``<name>-lab``, ``lab lineage/variant/strain``) — the catalog
    is lab-agnostic;
  - define a part by negation / comparison (``this is not the ...``,
    ``whereas it shares only ...``) — say what the part *is*.

This catches the clearly-codeable anti-patterns; it deliberately does NOT flag
legitimate scientific negation (mechanism descriptions like "RNA-based control,
no protein operator"), which is a review concern, not a machine one.

Run::

    python tools/check_content.py      # exit 1 on any violation

Wired into CI (``.github/workflows/validate.yml``) and the pre-push hook
(``scripts/hooks/pre-push``) so violations block a push.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PART_GLOBS = ("parts/**/*.json", "parts/**/*.gb", "parts/**/*.md")

# (compiled pattern, reason) — matched case-insensitively over each part file.
_RULES: tuple[tuple[str, str], ...] = (
    (r"seqmake",
     "names the consuming tool 'seqmake' (the catalog is tool-agnostic)"),
    # Internal-lab phrasing (possessive / lineage), NOT scientific attribution of
    # an originating lab (e.g. "the Bujard-lab pZ system" is legitimate provenance).
    (r"\bin our (?:lab|hands)\b|\bour lab\b|\bin-house\b|\blab (?:lineage|variant|strain|stock)\b",
     "references the using lab / an internal lineage (the catalog is lab-agnostic)"),
    (r"\bthis (?:part )?is \*{0,2}not\b|\bwhereas it shares only\b",
     "defines the part by negation/comparison (say what the part IS)"),
)
FORBIDDEN = tuple((re.compile(p, re.IGNORECASE), why) for p, why in _RULES)


def scan(root: Path = ROOT) -> list[str]:
    """Return a list of ``path:line: 'match' — reason`` violation strings."""
    problems: list[str] = []
    files = sorted({p for g in PART_GLOBS for p in root.glob(g)})
    for f in files:
        text = f.read_text(encoding="utf-8", errors="replace")
        for rx, why in FORBIDDEN:
            for m in rx.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                problems.append(f"{f.relative_to(root)}:{line}: '{m.group(0)}' — {why}")
    return problems


def main() -> int:
    files = sorted({p for g in PART_GLOBS for p in ROOT.glob(g)})
    problems = scan()
    if problems:
        print("Catalog content check FAILED — forbidden content in part files:\n")
        for p in problems:
            print("  " + p)
        print(
            f"\n{len(problems)} violation(s) across {len(files)} part files. "
            "Part content must describe what a part IS — lab-agnostic and tool-agnostic."
        )
        return 1
    print(f"Catalog content check passed ({len(files)} part files clean).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
