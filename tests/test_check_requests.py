"""The REQUESTS.md active-only guard (tools/check_requests.py)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from check_requests import REQUESTS, violations  # noqa: E402


def test_active_requests_pass():
    text = (
        "# Source documents needed\n\n"
        "## Cumate fold-change (PCymRC)\n"
        "- link: https://example.org/paper\n"
        "- would unblock: a PCymRC-specific induction fold-change claim\n"
        "- [ ] still need the Supplementary Information (paywalled)\n"
    )
    assert violations(text) == []


def test_resolved_heading_is_flagged():
    text = (
        "# Source documents needed\n\n"
        "## ✅ Resolved — PCymRC · closed 2026-06-15\n"
        "Unblocked by the human providing a token.\n"
    )
    assert violations(text)


def test_checked_box_is_flagged():
    assert violations("- [x] got the Meyer 2018 SI\n")


def test_strikethrough_heading_is_flagged():
    assert violations("## ~~old request~~\n")


def test_prose_word_done_is_not_flagged():
    # the marker words only matter on structural (heading/list) lines
    assert violations("This is what the request would get done eventually.\n") == []


def test_live_requests_file_is_active_only():
    assert violations(REQUESTS.read_text(encoding="utf-8")) == []
