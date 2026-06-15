"""Additive, review-status-aware merge of a proposed part record into an existing one.

The ``/add-part`` capability (see ``proposals/unified-add-part.md``) runs a
proposal-only research workflow and then MERGES its output into the canonical
``parts/<status>/<slug>.json``. Re-running on a candidate/validated part is where a
machine pass can silently destroy human-reviewed knowledge, so the merge policy is
specified once -- here -- and this is the only thing that writes claims into an
existing record.

Policy (full text in the proposal):

* Trust order: ``ai-generated (0) < ai-cross-checked (1) < expert-reviewed (2)``.
* ``functional_claims`` merge by stable ``id``; two claims are *content-equal* when
  ``(type, label, value, source)`` match. Per proposed claim P matched to existing E:

  - no E                       -> add (unless P duplicates an existing claim's content)
  - E is ``ai-generated``      -> overwrite in place (the fresh extraction wins)
  - E is reviewed (rank >= 1)  -> E is IMMUTABLE; a *differing* P is appended as a new
                                  claim (fresh id ``<id>__v2``) that ``supersedes`` E
                                  and is flagged; an *identical* P is dropped.

  So a machine merge only ever overwrites an ``ai-generated`` claim.
* ``sequence`` must match (a mismatch is a hard ``MergeError`` -- the Source phase,
  not a merge, changes sequences).
* ``provenance.sequence_source`` is never silently overwritten (a differing value is
  parked under ``sequence_source_proposed`` and flagged).
* ``references`` are unioned; ``features`` are kept by default
  (``replace_features=True`` to apply); record ``review_status`` is never downgraded.

Pure ``merge_records()`` + a dry-run-by-default CLI. Stdlib only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REVIEW_RANK = {"ai-generated": 0, "ai-cross-checked": 1, "expert-reviewed": 2}


class MergeError(ValueError):
    """A merge that must not proceed silently (e.g. a sequence mismatch)."""


def _rank(status: str | None) -> int:
    return REVIEW_RANK.get(status or "ai-generated", 0)


def _assertion(claim: dict) -> str:
    """Canonical key for a claim's substantive content.

    Ignores trust/provenance/id so a re-extraction of the same fact is recognised
    as content-equal regardless of how it was produced."""
    return json.dumps({k: claim.get(k) for k in ("type", "label", "value", "source")},
                      sort_keys=True, ensure_ascii=False)


def _doi(ref: dict) -> str:
    comment = ref.get("comment") or ""
    return comment[4:].strip() if comment.startswith("doi:") else ""


def _ref_key(ref: dict) -> str:
    return (ref.get("pubmed_id") or _doi(ref) or ref.get("title")
            or json.dumps(ref, sort_keys=True)).strip().lower()


def _fresh_id(base: str, taken: set[str]) -> str:
    if base not in taken:
        return base
    n = 2
    while f"{base}__v{n}" in taken:
        n += 1
    return f"{base}__v{n}"


def _copy(obj):
    return json.loads(json.dumps(obj))


def merge_records(existing: dict, proposed: dict, *,
                  replace_features: bool = False) -> tuple[dict, dict]:
    """Merge ``proposed`` into ``existing``; return ``(merged, report)``.

    ``existing`` is the on-disk canonical record; ``proposed`` is the workflow's
    schema-shaped output for the same slug. The merge is additive and monotonic in
    ``review_status`` (see the module docstring / the proposal). Neither input is
    mutated. Raises ``MergeError`` on a sequence mismatch."""
    merged = _copy(existing)
    report: dict = {
        "slug": existing.get("slug"),
        "claims": {"added": [], "overwritten": [], "preserved": [],
                   "flagged_superseding": [], "dropped_duplicate": []},
        "references_added": [],
        "flags": [],
    }

    # ---- sequence: must match -- never rewrite a stored, sourced sequence here ----
    ex_seq = (existing.get("sequence") or "").upper()
    pr_seq = (proposed.get("sequence") or "").upper()
    if pr_seq and ex_seq and pr_seq != ex_seq:
        raise MergeError(
            f"sequence mismatch for {existing.get('slug')!r}: the proposed sequence "
            f"differs from the stored one ({len(pr_seq)} vs {len(ex_seq)} bp). A merge "
            "must not rewrite a sourced sequence -- resolve it via the Source phase.")

    # ---- functional_claims: the heart ----
    out_claims = [_copy(c) for c in (existing.get("functional_claims") or [])]
    by_id = {c.get("id"): c for c in out_claims}
    ex_assertions = {_assertion(c): c for c in out_claims}
    taken_ids = {c.get("id") for c in out_claims}

    for p in (proposed.get("functional_claims") or []):
        pid = p.get("id")
        e = by_id.get(pid)
        if e is None:
            dup = ex_assertions.get(_assertion(p))
            if dup is not None:                       # same fact under a drifted id
                report["claims"]["dropped_duplicate"].append(
                    {"id": pid, "duplicate_of": dup.get("id")})
                continue
            out_claims.append(_copy(p))
            taken_ids.add(pid)
            report["claims"]["added"].append(pid)
            continue
        if _rank(e.get("review_status")) == 0:        # machine-only -> overwrite
            idx = next(i for i, c in enumerate(out_claims) if c.get("id") == pid)
            out_claims[idx] = _copy(p)
            report["claims"]["overwritten"].append(pid)
            continue
        # existing claim is human-reviewed -> immutable
        if _assertion(p) == _assertion(e):
            report["claims"]["preserved"].append(pid)  # identical, drop the proposal
            continue
        new_id = _fresh_id(pid, taken_ids)             # a contested correction
        sp = _copy(p)
        sp["id"] = new_id
        sp["supersedes"] = e.get("id")
        out_claims.append(sp)
        taken_ids.add(new_id)
        report["claims"]["flagged_superseding"].append(
            {"id": new_id, "supersedes": e.get("id")})
        report["flags"].append(
            f"claim {new_id!r} proposes a correction to reviewed claim "
            f"{e.get('id')!r} ({e.get('review_status')}); needs human review")

    if out_claims:
        merged["functional_claims"] = out_claims

    # ---- references: union ----
    refs = [_copy(r) for r in (existing.get("references") or [])]
    seen = {_ref_key(r) for r in refs}
    for r in (proposed.get("references") or []):
        key = _ref_key(r)
        if key not in seen:
            refs.append(_copy(r))
            seen.add(key)
            report["references_added"].append(key)
    if refs:
        merged["references"] = refs

    # ---- provenance: add new keys; protect sequence_source ----
    prov = dict(existing.get("provenance") or {})
    for key, val in (proposed.get("provenance") or {}).items():
        if key == "sequence_source" and prov.get(key) and prov[key] != val:
            prov["sequence_source_proposed"] = val
            report["flags"].append(
                f"provenance.sequence_source differs (kept {prov[key]!r}, proposed "
                f"{val!r}); recorded under sequence_source_proposed")
        elif key not in prov:
            prov[key] = val
    if prov:
        merged["provenance"] = prov

    # ---- features: kept by default ----
    if proposed.get("features") and proposed["features"] != existing.get("features"):
        if replace_features:
            merged["features"] = _copy(proposed["features"])
            report["features"] = "replaced"
        else:
            report["features"] = "kept (proposed differs; pass --replace-features to apply)"
            report["flags"].append(
                "proposed features differ from the stored annotation; kept existing")

    # ---- record-level review_status: never downgrade ----
    if _rank(proposed.get("review_status")) > _rank(merged.get("review_status")):
        merged["review_status"] = proposed["review_status"]

    return merged, report


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Additively merge a proposed part record into an existing "
                    "canonical .json (review-status-safe, dry-run by default).")
    ap.add_argument("--into", required=True,
                    help="the existing parts/<status>/<slug>.json to merge into")
    ap.add_argument("--proposed", required=True,
                    help="the workflow's proposed record JSON")
    ap.add_argument("--replace-features", action="store_true",
                    help="apply the proposed features (default: keep existing)")
    ap.add_argument("--write", action="store_true",
                    help="write the merge back to --into (default: print to stdout)")
    args = ap.parse_args()

    into = Path(args.into)
    existing = json.loads(into.read_text(encoding="utf-8"))
    proposed = json.loads(Path(args.proposed).read_text(encoding="utf-8"))
    try:
        merged, report = merge_records(existing, proposed,
                                       replace_features=args.replace_features)
    except MergeError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        sys.exit(1)

    if args.write:
        into.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        report["written"] = str(into)
    else:
        report["dry_run"] = True
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
