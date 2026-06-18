"""The validated-tier completeness gate (tools/validate_parts._completeness_problems).

A *validated* part must be a curated record — sourced provenance, >=1 reference and
>=1 functional_claim — not just a sequence. Legacy GenBank-migrated parts are
grandfathered on the sourcing criterion only. Candidates (bare parts) are exempt.
SO typing of every feature is a separate, all-parts gate (_so_coverage_problems),
also exercised here. See CONTRIBUTING.md (curation tiers) + AUTHORING.md."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from validate_parts import (  # noqa: E402
    _claim_tier_problems, _completeness_problems, _coordinate_problems,
    _so_coverage_problems)


def test_out_of_range_coordinates_are_flagged():
    assert _coordinate_problems("X.json",
        {"sequence": "ACGTACGTAC", "features": [{"type": "x", "start": 0, "end": 5}]}) == []
    # start == end (empty/inverted)
    assert _coordinate_problems("X.json",
        {"sequence": "ACGT", "features": [{"type": "x", "start": 2, "end": 2}]})
    # end past the sequence
    assert _coordinate_problems("X.json",
        {"sequence": "ACGT", "features": [{"type": "x", "start": 0, "end": 99}]})
    # uniprot_features are bounded too (residue space)
    assert _coordinate_problems("X.json",
        {"sequence": "MKV", "uniprot_features": [{"type": "d", "start": 0, "end": 9}]})


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


def test_missing_claim_or_reference_each_flagged():
    d = _complete(); d["functional_claims"] = []
    assert any("functional_claim" in p for p in _completeness_problems("X.json", d))
    d = _complete(); d["references"] = []
    assert any("reference" in p for p in _completeness_problems("X.json", d))


def test_so_coverage_gate():
    # A derivable type with no stored SO db_xref still passes -- part_json
    # injects the SO term at .gb-build time.
    d = _complete(); d["features"][0]["qualifiers"]["db_xref"] = []
    assert _so_coverage_problems("X.json", d) == []
    # An unmappable type with no explicit SO db_xref is flagged.
    d = _complete()
    d["features"][0]["type"] = "totally_made_up"
    d["features"][0]["qualifiers"]["db_xref"] = []
    assert any("no SO mapping" in p for p in _so_coverage_problems("X.json", d))
    # ...unless the author pins an explicit SO db_xref (the override path).
    d["features"][0]["qualifiers"]["db_xref"] = ["SO:0000110"]
    assert _so_coverage_problems("X.json", d) == []
    # uniprot_features are covered too: a mapped type passes, unmapped is flagged.
    d = _complete()
    d["uniprot_features"] = [{"type": "binding", "start": 0, "end": 3,
                             "label": "site"}]
    assert _so_coverage_problems("X.json", d) == []
    d["uniprot_features"] = [{"type": "made_up", "start": 0, "end": 3,
                             "label": "site"}]
    assert any("uniprot_feature" in p for p in _so_coverage_problems("X.json", d))


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


def test_content_free_reference_or_claim_does_not_pass():
    # Non-empty lists with empty objects must not clear the bar.
    d = _complete(); d["references"] = [{}]
    assert any("reference" in p for p in _completeness_problems("X.json", d))
    d = _complete(); d["functional_claims"] = [{"id": "x", "type": "t", "label": "L",
        "source": {}, "provenance": {}, "confidence": "low",
        "review_status": "ai-generated"}]
    assert any("functional_claim" in p for p in _completeness_problems("X.json", d))


def test_review_tier_must_be_earned():
    # ai-generated needs nothing extra.
    assert _claim_tier_problems("X.json", _complete()) == []
    # ai-cross-checked with a catalog-doc quote is rejected.
    d = _complete()
    d["functional_claims"][0]["review_status"] = "ai-cross-checked"
    d["functional_claims"][0]["source"] = {"pmid": "1", "quote": "q",
                                           "quote_source": "catalog-doc"}
    assert any("primary source" in p for p in _claim_tier_problems("X.json", d))
    # ...but a primary-sourced, quoted, cited claim is accepted at the higher tier.
    d["functional_claims"][0]["source"] = {"pmid": "1", "quote": "q",
                                           "quote_source": "primary"}
    assert _claim_tier_problems("X.json", d) == []
    # expert-reviewed is held to the same bar.
    d["functional_claims"][0]["review_status"] = "expert-reviewed"
    d["functional_claims"][0]["source"] = {"pmid": "1", "quote": "q",
                                           "quote_source": "catalog-doc"}
    assert _claim_tier_problems("X.json", d)
