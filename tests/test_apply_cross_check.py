"""The autonomous cross-check applier (tools/apply_cross_check.py).

Each correction_action drives a specific, safe edit to a claim's verification
lifecycle; verified is earned (primary quote), supersede never destroys, and an
unreachable source routes to sources-pending. See proposals/cross-check/CLAIM-MODEL.md."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from apply_cross_check import apply_verdict, load_verdicts  # noqa: E402
from validate_parts import _claim_verification_problems  # noqa: E402

DATE = "2026-06-22"


def _claim(cid="c1", ctype="mechanism"):
    return {"id": cid, "type": ctype, "label": "L", "value": {"x": 1},
            "source": {"pmid": "111", "quote": "old", "quote_source": "catalog-doc"},
            "provenance": {}, "confidence": "high",
            "analysis_status": "pending", "cross_checked": False}


def _rec(*claims):
    return {"slug": "P", "functional_claims": list(claims)}


def _v(cid="c1", **kw):
    base = {"part": "P", "claim_id": cid, "claim_type": "mechanism",
            "claim_type_changed": False, "usefulness": "high",
            "usefulness_rationale": "fills a datasheet slot",
            "source_accessed": "full_text", "quote_check": "verbatim_in_primary",
            "verdict": "confirmed", "evidence_strength": "strong",
            "primary_support": True, "recommended_confidence": "high",
            "cross_checked": True, "correction_action": "none", "proposed_change": {},
            "uncertainty_note": "", "evidence_quote": "Q from paper", "reasoning": "x"}
    base.update(kw)
    return base


def _apply(rec, verdict):
    return apply_verdict(rec, verdict, date=DATE, write=False,
                         file_requests=False, report=[])


# ----------------------------------------------------------------- none / verified
def test_confirmed_clean_claim_becomes_verified_and_earns_primary_quote():
    rec = _rec(_claim())
    assert _apply(rec, _v())
    c = rec["functional_claims"][0]
    assert c["analysis_status"] == "verified"
    assert c["cross_checked"] is True
    assert c["source"]["quote_source"] == "primary"
    assert c["source"]["quote"] == "Q from paper"
    assert c["usefulness"] == "high"
    assert c["last_checked"] == DATE
    # the result must satisfy the verified gate the validator enforces
    assert _claim_verification_problems("P", rec) == []


def test_confirmed_without_quote_cannot_be_verified():
    rec = _rec(_claim())
    assert _apply(rec, _v(evidence_quote=""))
    c = rec["functional_claims"][0]
    assert c["analysis_status"] != "verified"
    assert c["cross_checked"] is False


# --------------------------------------------------------------- sources-pending
def test_unreachable_source_routes_to_sources_pending():
    rec = _rec(_claim())
    assert _apply(rec, _v(verdict="partially_supported", cross_checked=False,
                          source_accessed="abstract_only",
                          recommended_confidence="low",
                          uncertainty_note="full text needed"))
    c = rec["functional_claims"][0]
    assert c["analysis_status"] == "sources-pending"
    assert c["cross_checked"] is False
    assert c["confidence"] == "low"


# ----------------------------------------------------------------- fix_metadata
def test_fix_metadata_repoints_pmid_and_verifies():
    rec = _rec(_claim())
    v = _v(correction_action="fix_metadata",
           proposed_change={"field": "source.pmid", "from": "111", "to": "222"})
    assert _apply(rec, v)
    c = rec["functional_claims"][0]
    assert c["source"]["pmid"] == "222"
    assert c["analysis_status"] == "verified"
    assert c["source"]["quote_source"] == "primary"


# ------------------------------------------------------------------- supersede
def test_supersede_creates_corrected_claim_and_flags_the_old_one():
    rec = _rec(_claim())
    v = _v(correction_action="supersede", verdict="partially_supported",
           cross_checked=False, source_accessed="full_text",
           uncertainty_note="value overstated",
           proposed_change={"field": "value.x", "to": 42})
    assert _apply(rec, v)
    claims = {c["id"]: c for c in rec["functional_claims"]}
    assert "c1" in claims and "c1__v2" in claims
    old, new = claims["c1"], claims["c1__v2"]
    # old retained but deprecated + back-linked
    assert old["analysis_status"] == "flagged"
    assert old["superseded_by"] == "c1__v2"
    assert "superseded by c1__v2" in old["comment"]
    # new carries the correction + its own primary quote, pointing back
    assert new["supersedes"] == "c1"
    assert new["value"]["x"] == 42
    assert new["source"]["quote_source"] == "primary"
    assert new["analysis_status"] == "flagged"  # not a clean confirm -> not verified


def test_supersede_with_new_label_and_value():
    rec = _rec(_claim())
    v = _v(correction_action="supersede", verdict="confirmed", cross_checked=True,
           proposed_change={"new_label": "Corrected L", "new_value": {"x": 9}})
    assert _apply(rec, v)
    new = [c for c in rec["functional_claims"] if c["id"] == "c1__v2"][0]
    assert new["label"] == "Corrected L"
    assert new["value"] == {"x": 9}
    assert new["analysis_status"] == "verified"  # confirmed + quote -> verified


def test_supersede_without_parseable_correction_falls_back_to_comment():
    rec = _rec(_claim())
    v = _v(correction_action="supersede", verdict="partially_supported",
           cross_checked=False, uncertainty_note="needs splitting",
           proposed_change={"reasoning": "this is prose, not a field edit"})
    assert _apply(rec, v)
    # no new claim was written
    assert [c["id"] for c in rec["functional_claims"]] == ["c1"]
    c = rec["functional_claims"][0]
    assert c["analysis_status"] == "flagged"
    assert c["comment"] == "needs splitting"


# --------------------------------------------------------------- downgrade_comment
def test_downgrade_comment_keeps_claim_and_attaches_note():
    rec = _rec(_claim())
    v = _v(correction_action="downgrade_comment", verdict="partially_supported",
           cross_checked=False, recommended_confidence="medium",
           uncertainty_note="figure not inspected")
    assert _apply(rec, v)
    c = rec["functional_claims"][0]
    assert c["analysis_status"] == "flagged"
    assert c["comment"] == "figure not inspected"
    assert c["confidence"] == "medium"


# -------------------------------------------------------------------- retyping
def test_claim_type_is_corrected_when_retyped():
    rec = _rec(_claim(ctype="strength"))
    assert _apply(rec, _v(claim_type="binding_affinity", claim_type_changed=True))
    assert rec["functional_claims"][0]["type"] == "binding_affinity"


def test_missing_claim_id_is_skipped():
    rec = _rec(_claim("c1"))
    assert _apply(rec, _v("does_not_exist")) is False


# --------------------------------------------------------------------- loader
def test_load_verdicts_accepts_workflow_result_shape(tmp_path):
    f = tmp_path / "v.json"
    f.write_text(json.dumps({"result": {"verdicts": [_v(), _v("c2")]}}))
    assert [v["claim_id"] for v in load_verdicts(f)] == ["c1", "c2"]
    f.write_text(json.dumps([_v("only")]))
    assert [v["claim_id"] for v in load_verdicts(f)] == ["only"]
