#!/usr/bin/env python3
"""Guard: relative links inside tracked Markdown files resolve to real paths.

Catches link-rot — a doc pointing at a file/dir that was moved, renamed, removed,
or archived (the classic drift when a section is deleted or a file relocated).
Only *relative* targets are checked; http(s) / mailto / anchor-only links and
fenced code blocks are skipped.

Runs in CI and as part of the ``pre-push`` hook. Usage:
    python tools/check_links.py
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
_SKIP = ("http://", "https://", "mailto:", "tel:", "#")


def tracked_md() -> list[Path]:
    """Tracked Markdown files (so generated/gitignored docs are not scanned)."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "*.md"], cwd=ROOT,
            capture_output=True, text=True, check=True).stdout
        return [ROOT / line for line in out.splitlines() if line]
    except Exception:  # not a git checkout — fall back to a filtered walk
        skip = (str(ROOT / "docs"), str(ROOT / "site"), str(ROOT / ".git"))
        return [p for p in ROOT.rglob("*.md") if not str(p).startswith(skip)]


def broken_links(md: Path) -> list[tuple[int, str]]:
    """(line-number, target) for each relative link in ``md`` that does not exist."""
    out: list[tuple[int, str]] = []
    in_fence = False
    for i, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in _LINK.finditer(line):
            target = m.group(1).strip()
            if not target or target.startswith(_SKIP):
                continue
            target = target.split()[0]            # drop a `path "Title"` suffix
            path_part = target.split("#", 1)[0]    # drop a `#anchor`
            if not path_part:                      # pure in-page anchor
                continue
            if not (md.parent / path_part).resolve().exists():
                out.append((i, m.group(1).strip()))
    return out


def main() -> int:
    files = tracked_md()
    bad = [(md.relative_to(ROOT), ln, t) for md in files for ln, t in broken_links(md)]
    if bad:
        print("Broken relative Markdown links (target does not exist):")
        for rel, ln, target in bad:
            print(f"  {rel}:{ln}: {target}")
        return 1
    print(f"Link check passed ({len(files)} Markdown files).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
