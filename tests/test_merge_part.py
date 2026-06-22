"""The additive, verification-aware merge (tools/merge_part.py).

The contract that protects independently-verified knowledge from machine re-runs:
a claim that is not yet ``cross_checked`` may be overwritten in place; a
``cross_checked`` (verified) claim is immutable and a contesting proposal is
appended as a flagged, superseding claim instead. See AUTHORING.md and the trust
model in proposals/cross-check/CLAIM-MODEL.md."""
import json
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from merge_part import MergeError, merge_records  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "part.schema.json").read_text())


def _claim(cid, *, verified=False, label="L", value=None, pmid="1", ctype=None):
    """A claim. ``verified=True`` marks it cross_checked (the protected state);
    source stays minimal so content-equality (type/label/value/source) is testable."""
    c = {
        "id": cid, "type": ctype or cid, "label": label,
        "value": value if value is not None else {},
        "source": {"pmid": pmid}, "provenance": {"method": "ai-extraction"},
        "confidence": "medium",
        "analysis_status": "verified" if verified else "pending",
        "cross_checked": verified, "supersedes": None,
    }
    if verified:
        c["usefulness"] = "high"
    return c


def _rec(claims, *, seq="ACGTACGTAC", **extra):
    rec = {
        "schema_version": "1.0", "slug": "T", "locus": "T", "id": "T",
        "description": "d", "molecule_type": "DNA",
        "locus_annotations": {"topology": "linear"},
        "sequence": seq, "references": [],
        "features": [{"type": "promoter", "start": 0, "end": len(seq), "strand": 1,
                      "qualifiers": {"label": ["T"], "db_xref": ["SO:0000167"]}}],
        "provenance": {}, "functional_claims": claims,
    }
    rec.update(extra)
    return rec


def _ids(claims):
    return [c["id"] for c in claims]


def test_new_claim_is_added():
    existing = _rec([_claim("inducer")])
    proposed = _rec([_claim("inducer"), _claim("strength_class")])
    merged, report = merge_records(existing, proposed)
    assert report["claims"]["added"] == ["strength_class"]
    assert set(_ids(merged["functional_claims"])) == {"inducer", "strength_class"}


def test_unverified_claim_is_overwritten_in_place():
    existing = _rec([_claim("inducer", label="OLD")])
    proposed = _rec([_claim("inducer", label="NEW")])
    merged, report = merge_records(existing, proposed)
    assert report["claims"]["overwritten"] == ["inducer"]
    assert len(merged["functional_claims"]) == 1
    assert merged["functional_claims"][0]["label"] == "NEW"


def test_verified_claim_is_immutable_and_correction_is_appended_flagged():
    existing = _rec([_claim("inducer", verified=True, label="VERIFIED")])
    proposed = _rec([_claim("inducer", label="CONTRADICTS")])
    merged, report = merge_records(existing, proposed)

    # the verified claim is untouched
    original = next(c for c in merged["functional_claims"] if c["id"] == "inducer")
    assert original["label"] == "VERIFIED"
    assert original["cross_checked"] is True
    assert original["analysis_status"] == "verified"

    # the proposal is appended under a fresh id, superseding the verified claim
    sup = next(c for c in merged["functional_claims"] if c["id"] != "inducer")
    assert sup["supersedes"] == "inducer"
    assert sup["label"] == "CONTRADICTS"
    assert report["claims"]["flagged_superseding"] == [
        {"id": sup["id"], "supersedes": "inducer"}]
    assert report["flags"], "a contested verified claim must be flagged for a human"


def test_identical_proposal_against_verified_claim_is_dropped():
    existing = _rec([_claim("inducer", verified=True, label="SAME")])
    proposed = _rec([_claim("inducer", label="SAME")])  # same type/label/value/source
    merged, report = merge_records(existing, proposed)
    assert _ids(merged["functional_claims"]) == ["inducer"]
    assert report["claims"]["preserved"] == ["inducer"]
    assert merged["functional_claims"][0]["cross_checked"] is True


def test_content_duplicate_under_a_drifted_id_is_dropped():
    existing = _rec([_claim("inducer", label="SAME")])
    # same fact (type/label/value/source) but the id drifted
    proposed = _rec([_claim("inducer_v2", ctype="inducer", label="SAME")])
    merged, report = merge_records(existing, proposed)
    assert _ids(merged["functional_claims"]) == ["inducer"]
    assert report["claims"]["dropped_duplicate"] == [
        {"id": "inducer_v2", "duplicate_of": "inducer"}]


def test_proposed_claim_without_lifecycle_gets_defaults():
    # annotate-part emits claims without analysis_status/cross_checked; the merge
    # must fill the required lifecycle fields so the record stays schema-valid.
    bare = {"id": "inducer", "type": "inducer", "label": "L", "value": {},
            "source": {"pmid": "1"}, "provenance": {}, "confidence": "low"}
    merged, _ = merge_records(_rec([]), _rec([bare]))
    c = merged["functional_claims"][0]
    assert c["analysis_status"] == "pending"
    assert c["cross_checked"] is False


def test_producer_set_status_is_respected():
    # a sources-pending claim from annotate-part must not be downgraded to pending.
    sp = dict(_claim("inducer"), analysis_status="sources-pending")
    merged, _ = merge_records(_rec([]), _rec([sp]))
    assert merged["functional_claims"][0]["analysis_status"] == "sources-pending"


def test_sequence_mismatch_is_a_hard_error():
    existing = _rec([], seq="ACGTACGTAC")
    proposed = _rec([], seq="TTTTTTTTTT")
    with pytest.raises(MergeError):
        merge_records(existing, proposed)


def test_references_are_unioned():
    existing = _rec([], references=[{"pubmed_id": "111", "title": "A"}])
    proposed = _rec([], references=[{"pubmed_id": "111", "title": "A"},
                                    {"pubmed_id": "222", "title": "B"}])
    merged, report = merge_records(existing, proposed)
    assert [r["pubmed_id"] for r in merged["references"]] == ["111", "222"]
    assert report["references_added"] == ["222"]


def test_sequence_source_is_not_silently_overwritten():
    existing = _rec([], provenance={"sequence_source": "Doe 2020 (PMID 1)"})
    proposed = _rec([], provenance={"sequence_source": "Roe 2021 (PMID 9)"})
    merged, report = merge_records(existing, proposed)
    assert merged["provenance"]["sequence_source"] == "Doe 2020 (PMID 1)"
    assert merged["provenance"]["sequence_source_proposed"] == "Roe 2021 (PMID 9)"
    assert report["flags"]


def test_features_kept_by_default_and_replaced_on_request():
    existing = _rec([])
    proposed = _rec([])
    proposed["features"] = [dict(existing["features"][0],
                                 qualifiers={"label": ["T"], "db_xref": ["SO:0000167"],
                                             "note": ["new annotation"]})]
    kept, report = merge_records(existing, proposed)
    assert kept["features"] == existing["features"]
    assert "kept" in report["features"]

    replaced, _ = merge_records(existing, proposed, replace_features=True)
    assert replaced["features"] == proposed["features"]


def test_record_carries_no_review_status():
    # review_status is retired at the record level; a merge must not reintroduce it.
    merged, _ = merge_records(_rec([_claim("inducer")]), _rec([_claim("inducer")]))
    assert "review_status" not in merged


def test_inputs_are_not_mutated():
    existing = _rec([_claim("inducer", label="OLD")])
    snapshot = json.dumps(existing, sort_keys=True)
    merge_records(existing, _rec([_claim("inducer", label="NEW")]))
    assert json.dumps(existing, sort_keys=True) == snapshot


def test_merged_record_is_schema_valid():
    existing = _rec([_claim("inducer", verified=True, label="VERIFIED")])
    proposed = _rec([_claim("inducer", label="CONTRADICTS"),
                     _claim("strength_class", label="strong")])
    merged, _ = merge_records(existing, proposed)
    Draft202012Validator(SCHEMA).validate(merged)
