"""One-time, idempotent migration: retire ``review_status`` -> the claim trust model.

Drops the three-tier ``review_status`` ladder (record- and claim-level) in favour of
the orthogonal axes decided in ``proposals/cross-check/CLAIM-MODEL.md``:

* record level   -- ``review_status`` removed (a record's trust is now a build-time
                    roll-up of its claims' ``analysis_status``, not a stored field).
* claim level    -- ``review_status`` removed; every claim gains
                    ``analysis_status="pending"`` and ``cross_checked=false`` unless it
                    already carries them. ``usefulness`` / ``comment`` / ``last_checked``
                    are NOT invented here -- the cross-check pass writes those when it
                    actually analyses a claim.

Idempotent: re-running is a no-op once a file is migrated. New keys are inserted right
after ``confidence`` so diffs stay readable. Stdlib only; dry-run by default.
"""
from __future__ import annotations

import argparse
import json
from collections import OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PART_DIRS = [ROOT / "parts" / "validated", ROOT / "parts" / "candidate"]


def _migrate_claim(claim: dict) -> tuple[dict, bool]:
    """Return ``(new_claim, changed)`` with review_status dropped and the lifecycle
    axes ensured. Key order preserved; new keys inserted just after ``confidence``."""
    had_rs = "review_status" in claim
    has_status = "analysis_status" in claim
    has_xc = "cross_checked" in claim
    if not had_rs and has_status and has_xc:
        return claim, False

    out: "OrderedDict[str, object]" = OrderedDict()
    inserted = False

    def _insert_axes() -> None:
        nonlocal inserted
        if inserted:
            return
        out.setdefault("analysis_status", claim.get("analysis_status", "pending"))
        out.setdefault("cross_checked", claim.get("cross_checked", False))
        inserted = True

    for key, val in claim.items():
        if key == "review_status":
            continue  # dropped
        if key in ("analysis_status", "cross_checked"):
            continue  # re-emitted in canonical position below
        out[key] = val
        if key == "confidence":
            _insert_axes()
    _insert_axes()  # records with no confidence key still get the axes
    return dict(out), True


def migrate_record(rec: dict) -> tuple[dict, bool]:
    changed = False
    if "review_status" in rec:
        rec = {k: v for k, v in rec.items() if k != "review_status"}
        changed = True
    claims = rec.get("functional_claims")
    if isinstance(claims, list):
        new_claims = []
        for c in claims:
            nc, ch = _migrate_claim(c)
            changed = changed or ch
            new_claims.append(nc)
        if changed:
            rec["functional_claims"] = new_claims
    return rec, changed


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="apply changes (default: report what would change)")
    args = ap.parse_args()

    touched = 0
    total = 0
    for d in PART_DIRS:
        for path in sorted(d.glob("*.json")):
            total += 1
            rec = json.loads(path.read_text(encoding="utf-8"))
            migrated, changed = migrate_record(rec)
            if not changed:
                continue
            touched += 1
            if args.write:
                path.write_text(
                    json.dumps(migrated, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
            print(f"{'migrated' if args.write else 'would migrate'}: {path.relative_to(ROOT)}")

    verb = "migrated" if args.write else "to migrate"
    print(f"\n{touched}/{total} part files {verb}"
          + ("" if args.write else "  (re-run with --write to apply)"))


if __name__ == "__main__":
    main()
