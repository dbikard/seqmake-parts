#!/usr/bin/env python3
"""Guard: ``sourcing/REQUESTS.md`` lists ACTIVE source requests only.

A source request tracks a *blocked* part — the agent couldn't access a sequence /
boundary-evidence source and stopped (see ``sourcing/README.md``). The moment a
request is fulfilled it is **removed**: the permanent record is the part's
``provenance.sequence_source`` citation plus git history, not a growing pile of
closed tickets. This guard fails if a resolved/closed marker is left behind in
REQUESTS.md, so stale closed requests can't accumulate.

Runs in CI and as part of the ``pre-push`` hook. Usage:
    python tools/check_requests.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUESTS = ROOT / "sourcing" / "REQUESTS.md"

# A request is closed (and should have been removed) when its heading / list line
# carries one of these markers. Checked boxes (``[x]``) flag closed; unchecked
# boxes (``[ ]``) are fine — those are active. Scanned only on structural lines
# (headings / list items), never free prose, to avoid false positives.
_RESOLVED = re.compile(
    r"(✅|❌|~~|\[[xX]\]|\bresolved\b|\bclosed\b|\bfulfilled\b)",
    re.IGNORECASE,
)


def violations(text: str) -> list[tuple[int, str]]:
    """Return (line-number, line) for each closed-looking heading / list item."""
    out: list[tuple[int, str]] = []
    for i, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("#") or s.startswith(("- ", "* ", "+ ")):
            if _RESOLVED.search(s):
                out.append((i, line.rstrip()))
    return out


def main() -> int:
    if not REQUESTS.exists():
        return 0
    bad = violations(REQUESTS.read_text(encoding="utf-8"))
    if bad:
        print("sourcing/REQUESTS.md must list ACTIVE requests only — remove resolved entries.")
        print("(The permanent record is the part's provenance.sequence_source + git history.)")
        for ln, line in bad:
            print(f"  sourcing/REQUESTS.md:{ln}: {line}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
