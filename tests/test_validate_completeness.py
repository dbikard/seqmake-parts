"""The validated-tier completeness gate (tools/validate_parts._completeness_problems).

A *validated* part must be a curated record — sourced provenance, an SO-typed main
feature, >=1 reference and >=1 functional_claim — not just a sequence. Legacy
GenBank-migrated parts are grandfathered on the sourcing criterion only. Candidates
(bare parts) are exempt. See CONTRIBUTING.md (curation tiers) + AUTHORING.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from validate_parts import _completeness_problems  # noqa: E402


def _complete():
    return {
        "slug": "X",
        "features": [{"type": "promoter", "start": 0, "end": 10, "strand": 1,
                      "qualifiers": {"label": ["X"], "db_xref": ["SO:0000167"]}}],
        "references": [{"pubmed_id": "1"}],
        "functional_claims": [{"id": "inducer", "type": "inducer", "label": "L",
                               "source": {"pmid": "1"}, "provenance": {},
                               "confidence": "low", "review_status": "ai-generated"}],
        "provenance": {"sequence_source": "Doe 2020 (PMID 1)"},
    }


def test_complete_validated_part_passes():
    assert _completeness_problems("X.json", _complete()) == []


def test_missing_claim_reference_or_so_each_flagged():
    d = _complete(); d["functional_claims"] = []
    assert any("functional_claim" in p for p in _completeness_problems("X.json", d))
    d = _complete(); d["references"] = []
    assert any("reference" in p for p in _completeness_problems("X.json", d))
    d = _complete(); d["features"][0]["qualifiers"]["db_xref"] = []
    assert any("SO db_xref" in p for p in _completeness_problems("X.json", d))


def test_missing_or_placeholder_source_is_flagged():
    d = _complete(); d["provenance"] = {"sequence_source": "FILL IN: ..."}
    assert any("sequence_source" in p for p in _completeness_problems("X.json", d))
    d = _complete(); d["provenance"] = {}
    assert any("sequence_source" in p for p in _completeness_problems("X.json", d))


def test_legacy_migrated_part_is_grandfathered_on_sourcing():
    d = _complete(); d["provenance"] = {"migrated_from": "genbank"}  # no sequence_source
    probs = _completeness_problems("X.json", d)
    assert not any("sequence_source" in p for p in probs), probs
    # but a migrated part still needs refs/claims/SO
    d2 = dict(d); d2["functional_claims"] = []
    assert any("functional_claim" in p for p in _completeness_problems("X.json", d2))
