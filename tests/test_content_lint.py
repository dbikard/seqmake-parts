"""The content guard: catalog part text is lab-agnostic and tool-agnostic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from check_content import FORBIDDEN, scan  # noqa: E402


def test_catalog_part_content_is_clean():
    problems = scan()
    assert problems == [], "forbidden content in part files:\n" + "\n".join(problems)


def test_guard_catches_known_violations():
    # Every anti-pattern the guard exists to stop must be detected.
    for text in (
        "annotated by seqmake as the variant",        # names the consuming tool
        "The Bikard-lab lineage carries a variant",   # internal lineage
        "we use this in our lab for tuning",          # the using lab
        "This is **not** the PLtetO-1 promoter",      # definition by negation
        "whereas it shares only the operator dyad",   # comparison framing
    ):
        assert any(rx.search(text) for rx, _ in FORBIDDEN), f"not caught: {text!r}"


def test_guard_allows_legitimate_science():
    # Scientific provenance and mechanistic negation must NOT be flagged.
    for text in (
        "the Bujard-lab pZ expression system",        # originating-lab attribution
        "RNA-based control; no protein operator is encoded here",
        "removal of the disulfide does not abolish catalysis",
        "this part spans the -35/-10 core only",
    ):
        assert not any(rx.search(text) for rx, _ in FORBIDDEN), f"false positive: {text!r}"
