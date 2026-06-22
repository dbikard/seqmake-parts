"""Autonomous applier for cross-check verdicts (the trust model's write side).

The cross-check engine (``.claude/workflows/cross-check.js``) re-verifies each
``functional_claim`` against its cited primary source and emits a verdict per claim
(see its ``VERDICT_SCHEMA``). This tool executes those verdicts against the canonical
part JSONs, turning ``analysis_status`` / ``cross_checked`` / ``confidence`` /
``usefulness`` into *earned* state instead of asserted labels. See the trust model in
``proposals/cross-check/CLAIM-MODEL.md``.

Guardrails (git is the only undo; *never destroy, always supersede*):

* **none / fix_metadata** -> in-place, reversible. A confirmed claim becomes
  ``verified`` and its quote is upgraded to the verbatim primary sentence the verifier
  read (``quote_source="primary"``); ``fix_metadata`` also re-points a wrong
  pmid/doi/section that the verifier corrected.
* **supersede** -> a NEW claim (``<id>__v2``) carrying the corrected label/value AND
  its own primary quote supersedes the old; the old is RETAINED, ``flagged`` and
  ``superseded_by`` the new (auditable in the data, not just in git). If the proposed
  correction can't be parsed into a clean label/value, it safely falls back to
  ``downgrade_comment`` rather than write a guess.
* **downgrade_comment** -> keep the claim, lower ``confidence``, attach the
  uncertainty note as ``comment``; ``flagged``.
* **source unreachable** (``source_accessed`` abstract/inaccessible, not verified) ->
  ``sources-pending`` + a ``sourcing/REQUESTS.md`` entry is filed via
  ``tools/papers.py request`` (store-aware + self-pruning) so the same
  ``/open-requests`` -> ``/incoming`` loop unblocks it. This is the only human step.

Dry-run by default (mirrors ``merge_part.py``); ``--write`` applies. Stdlib only.
"""
from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PART_DIRS = [ROOT / "parts" / "validated", ROOT / "parts" / "candidate"]

UNREACHABLE = {"abstract_only", "metadata_only", "inaccessible"}
SOURCE_FIELDS = {"pmid", "doi", "url", "section", "figure", "table", "page"}


# ----------------------------------------------------------------------------- io
def load_verdicts(path: Path) -> list[dict]:
    """Accept the workflow result in any of its shapes: a bare list, ``{verdicts}``,
    or the full task output ``{result: {verdicts}}``."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if isinstance(data.get("verdicts"), list):
            return data["verdicts"]
        res = data.get("result")
        if isinstance(res, dict) and isinstance(res.get("verdicts"), list):
            return res["verdicts"]
    raise SystemExit(f"no verdicts array found in {path}")


def _part_path(slug: str) -> Path | None:
    for d in PART_DIRS:
        p = d / f"{slug}.json"
        if p.exists():
            return p
    return None


# ------------------------------------------------------------------- field helpers
def _parse_field(field: str | None) -> tuple[str | None, str | None]:
    """Map a verdict ``proposed_change.field`` to a (root, key) we can safely set.
    root is 'source' or 'value'; unknown shapes return (None, None)."""
    if not field:
        return (None, None)
    f = str(field).strip()
    for prefix, root in (("source.", "source"), ("value.", "value"),
                         ("claim_value.", "value")):
        if f.startswith(prefix):
            return (root, f[len(prefix):])
    if f in SOURCE_FIELDS or f in ("quote", "quote_source"):
        return ("source", f)
    return (None, None)


def _fresh_id(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    n = 2
    while f"{base}__v{n}" in taken:
        n += 1
    return f"{base}__v{n}"


def _set_verified_quote(claim: dict, quote: str) -> None:
    """Upgrade a claim's quote to the verbatim primary sentence the verifier read."""
    src = claim.setdefault("source", {})
    src["quote"] = quote
    src["quote_source"] = "primary"


def _apply_source_fix(claim: dict, change: dict) -> str | None:
    """Apply a whitelisted source metadata correction (pmid/doi/section/...). Returns
    a human note describing what changed, or None."""
    root, key = _parse_field(change.get("field"))
    to = change.get("to")
    if root == "source" and key in SOURCE_FIELDS and to is not None:
        claim.setdefault("source", {})[key] = to
        return f"source.{key}->{to}"
    return None


def _corrected_label_value(claim: dict, change: dict) -> tuple[str, dict] | None:
    """Best-effort extraction of a corrected (label, value) from a supersede's
    free-form proposed_change. Returns None if nothing clean can be parsed (caller
    then falls back to downgrade_comment rather than writing a guess)."""
    label = change.get("new_label") or change.get("label")
    value = change.get("new_value")
    if value is None and isinstance(change.get("value"), dict):
        value = change["value"]
    base_value = dict(claim.get("value") or {})
    # A targeted value-field edit, e.g. {field: "value.Kd", to: "..."}.
    root, key = _parse_field(change.get("field"))
    if root == "value" and key and change.get("to") is not None:
        base_value[key] = change["to"]
        return (label or claim.get("label", ""), base_value)
    if label or value is not None:
        return (label or claim.get("label", ""),
                value if value is not None else base_value)
    return None


# ----------------------------------------------------------------------- requests
def _file_request(claim: dict, verdict: dict, *, write: bool, report: list) -> bool:
    """File a sourcing/REQUESTS.md entry for an unreachable claim source, reusing the
    store-aware tools/papers.py. Returns True if a request was (or would be) filed."""
    src = claim.get("source") or {}
    pmid, doi = src.get("pmid"), src.get("doi")
    if not (pmid or doi):
        report.append("    (no pmid/doi on claim -> cannot file a paper request)")
        return False
    unblocks = f"{verdict['part']}/{verdict['claim_id']}"
    barrier = verdict.get("source_accessed") or "paywall"
    report.append(f"    -> REQUESTS.md: unblocks {unblocks} "
                  f"({'pmid ' + pmid if pmid else 'doi ' + doi}, barrier {barrier})")
    if not write:
        return True
    cmd = [sys.executable, str(ROOT / "tools" / "papers.py"), "request",
           "--unblocks", unblocks, "--barrier", barrier]
    if pmid:
        cmd += ["--pmid", pmid]
    if doi:
        cmd += ["--doi", doi]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        report.append(f"    ! papers.py request failed: {res.stderr.strip()}")
        return False
    return True


# -------------------------------------------------------------------- core per-claim
def _annotate_axes(claim: dict, verdict: dict, date: str) -> None:
    """The always-applied orthogonal axes + re-typing (independent of correction)."""
    if verdict.get("usefulness"):
        claim["usefulness"] = verdict["usefulness"]
    if verdict.get("usefulness_rationale"):
        claim["usefulness_rationale"] = verdict["usefulness_rationale"]
    if verdict.get("recommended_confidence"):
        claim["confidence"] = verdict["recommended_confidence"]
    if verdict.get("claim_type_changed") and verdict.get("claim_type"):
        claim["type"] = verdict["claim_type"]
    claim["last_checked"] = date


def _verified_ok(verdict: dict) -> bool:
    """A claim can be marked verified only if the verifier confirmed it against the
    primary source AND captured a verbatim quote to satisfy the verified gate."""
    return bool(verdict.get("cross_checked")) and bool(verdict.get("evidence_quote"))


def _non_verified_status(verdict: dict, claim: dict, *, write: bool,
                         report: list, file_requests: bool) -> str:
    """Status for a claim that did not earn 'verified': sources-pending (+request) if
    the source was unreachable, else flagged."""
    if verdict.get("source_accessed") in UNREACHABLE:
        if file_requests:
            _file_request(claim, verdict, write=write, report=report)
        return "sources-pending"
    return "flagged"


def apply_verdict(rec: dict, verdict: dict, *, date: str, write: bool,
                  file_requests: bool, report: list):
    """Apply one verdict to its part record (mutated in place). Returns the outcome
    tag ('verified' / 'sources-pending' / 'flagged' / 'superseded') or ``False`` if
    the claim was not found. Appends human-readable lines to ``report``."""
    claims = rec.get("functional_claims") or []
    by_id = {c.get("id"): c for c in claims}
    cid = verdict.get("claim_id")
    claim = by_id.get(cid)
    head = f"  {verdict['part']}/{cid} [{verdict.get('correction_action')}]"
    if claim is None:
        report.append(f"{head}: SKIP (claim id not found)")
        return False

    action = verdict.get("correction_action") or "none"
    _annotate_axes(claim, verdict, date)
    quote = verdict.get("evidence_quote") or ""
    verified = _verified_ok(verdict)

    # ---- supersede: corrected NEW claim, old retained + flagged ----
    if action == "supersede":
        corrected = _corrected_label_value(claim, verdict.get("proposed_change") or {})
        if corrected is None:
            action = "downgrade_comment"  # nothing clean to write -> annotate instead
            report.append(f"{head}: supersede had no parseable correction "
                          f"-> downgrade_comment")
        else:
            taken = set(by_id)
            new_id = _fresh_id(f"{cid}__v2", taken)
            new = json.loads(json.dumps(claim))  # deep copy as the base
            new["id"] = new_id
            new["label"], new["value"] = corrected
            if verdict.get("claim_type"):
                new["type"] = verdict["claim_type"]
            if quote:
                _set_verified_quote(new, quote)
            new["supersedes"] = cid
            new["superseded_by"] = None
            new["analysis_status"] = ("verified" if verified
                                      else _non_verified_status(verdict, new,
                                           write=write, report=report,
                                           file_requests=file_requests))
            new["cross_checked"] = verified
            new["last_checked"] = date
            # the old claim is retained, deprecated and back-linked
            claim["analysis_status"] = "flagged"
            claim["cross_checked"] = False
            claim["superseded_by"] = new_id
            note = verdict.get("uncertainty_note") or "corrected"
            claim["comment"] = f"superseded by {new_id}: {note}"
            rec["functional_claims"].append(new)
            report.append(f"{head}: superseded -> {new_id} "
                          f"({new['analysis_status']}); old flagged")
            return "superseded"

    # ---- fix_metadata: in-place, reversible ----
    if action == "fix_metadata":
        fixnote = _apply_source_fix(claim, verdict.get("proposed_change") or {})
        if verified and quote:
            _set_verified_quote(claim, quote)
            claim["analysis_status"] = "verified"
            claim["cross_checked"] = True
        else:
            claim["analysis_status"] = _non_verified_status(
                verdict, claim, write=write, report=report,
                file_requests=file_requests)
            claim["cross_checked"] = False
            if verdict.get("uncertainty_note"):
                claim["comment"] = verdict["uncertainty_note"]
        report.append(f"{head}: {claim['analysis_status']}"
                      + (f"; {fixnote}" if fixnote else ""))
        return claim["analysis_status"]

    # ---- downgrade_comment: keep, lower confidence, attach note ----
    if action == "downgrade_comment":
        claim["comment"] = verdict.get("uncertainty_note") or claim.get("comment")
        claim["analysis_status"] = _non_verified_status(
            verdict, claim, write=write, report=report, file_requests=file_requests)
        claim["cross_checked"] = False
        report.append(f"{head}: {claim['analysis_status']} (comment attached)")
        return claim["analysis_status"]

    # ---- none: confirmed & clean -> verified, else status by reachability ----
    if verified and quote:
        _set_verified_quote(claim, quote)
        claim["analysis_status"] = "verified"
        claim["cross_checked"] = True
    else:
        claim["analysis_status"] = _non_verified_status(
            verdict, claim, write=write, report=report, file_requests=file_requests)
        claim["cross_checked"] = False
        if verdict.get("uncertainty_note") and claim["analysis_status"] == "flagged":
            claim["comment"] = verdict["uncertainty_note"]
    report.append(f"{head}: {claim['analysis_status']}")
    return claim["analysis_status"]


# ------------------------------------------------------------------------- driver
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--verdicts", required=True,
                    help="JSON file of cross-check verdicts (bare list, {verdicts}, "
                         "or the full workflow {result:{verdicts}})")
    ap.add_argument("--write", action="store_true",
                    help="apply changes (default: dry-run report)")
    ap.add_argument("--date", default=datetime.date.today().isoformat(),
                    help="last_checked date stamp (YYYY-MM-DD; default today)")
    ap.add_argument("--no-requests", action="store_true",
                    help="do not file sourcing/REQUESTS.md entries for unreachable sources")
    args = ap.parse_args()

    verdicts = load_verdicts(Path(args.verdicts))
    by_part: dict[str, list[dict]] = {}
    for v in verdicts:
        by_part.setdefault(v["part"], []).append(v)

    report: list[str] = []
    summary = {"parts": 0, "claims_changed": 0, "skipped": 0,
               "verified": 0, "sources_pending": 0, "flagged": 0, "superseded": 0}

    for slug in sorted(by_part):
        path = _part_path(slug)
        report.append(f"\n{slug}  ({path.parent.name if path else 'NOT FOUND'})")
        if path is None:
            summary["skipped"] += len(by_part[slug])
            report.append("  SKIP (part file not found)")
            continue
        rec = json.loads(path.read_text(encoding="utf-8"))
        changed_any = False
        for v in by_part[slug]:
            outcome = apply_verdict(rec, v, date=args.date, write=args.write,
                                    file_requests=not args.no_requests, report=report)
            if not outcome:
                summary["skipped"] += 1
                continue
            summary["claims_changed"] += 1
            changed_any = True
            summary[{"verified": "verified", "sources-pending": "sources_pending",
                     "flagged": "flagged", "superseded": "superseded"}[outcome]] += 1
        if changed_any:
            summary["parts"] += 1
            if args.write:
                path.write_text(json.dumps(rec, indent=2, ensure_ascii=False) + "\n",
                                encoding="utf-8")

    print("\n".join(report))
    print("\n" + ("APPLIED" if args.write else "DRY RUN") + " — "
          + ", ".join(f"{k}={v}" for k, v in summary.items()))
    if not args.write:
        print("re-run with --write to apply, then regenerate artifacts + run gates "
              "(python tools/check_all.py)")


if __name__ == "__main__":
    main()
