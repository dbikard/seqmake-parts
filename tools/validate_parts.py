#!/usr/bin/env python3
"""Validate every canonical ``<slug>.json`` against ``schema/part.schema.json``.

Run in CI as the write-side gate (the JSON is the authored source of truth).
Exits non-zero and lists every problem on failure.

Usage:
    python tools/validate_parts.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
from so_terms import so_for  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = ROOT / "schema" / "part.schema.json"
CLAIM_TYPES = ROOT / "schema" / "claim_types.json"


def _claim_vocab() -> tuple[set[str], set[str]]:
    """(canonical, aliases) claim-type strings from the controlled vocabulary."""
    v = json.loads(CLAIM_TYPES.read_text(encoding="utf-8"))
    return set(v.get("claim_types", {})), set(v.get("aliases", {}))


def _completeness_problems(name: str, data: dict) -> list[str]:
    """A *validated* part must be a curated record, not just a sequence: a real
    sourced provenance, an SO-typed main feature, >=1 reference and >=1
    functional_claim (the ``.md`` page is checked separately). A *candidate* is a
    bare part (sequence + minimal info) and is exempt.

    Legacy parts migrated from GenBank (``provenance.migrated_from`` with no
    ``sequence_source``) are grandfathered on the sourcing criterion only -- they
    were validated under the old rule; re-source them on next touch.
    """
    out: list[str] = []
    prov = data.get("provenance") or {}
    ss = str(prov.get("sequence_source") or "")
    grandfathered = bool(prov.get("migrated_from")) and not ss
    if (not ss or ss.startswith("FILL IN")) and not grandfathered:
        out.append(f"{name}: validated part needs a real provenance.sequence_source")
    # Require *substantive* records, not just non-empty lists: a reference must
    # identify a work, and a functional claim must cite a source -- otherwise an
    # empty {} placeholder would clear the bar (the schema allows content-free
    # reference/source objects).
    refs = [r for r in (data.get("references") or [])
            if r.get("title") or r.get("pubmed_id") or r.get("doi") or r.get("authors")]
    if not refs:
        out.append(f"{name}: validated part needs >=1 reference (with a title/PMID/DOI)")
    claims = [c for c in (data.get("functional_claims") or [])
              if (c.get("source") or {}).get("pmid")
              or (c.get("source") or {}).get("doi")
              or (c.get("source") or {}).get("url")]
    if not claims:
        out.append(f"{name}: validated part needs >=1 functional_claim with a cited source")
    # SO typing of the main (and every) feature is enforced for *all* parts by
    # _so_coverage_problems, so it is not repeated here.
    return out


def _so_coverage_problems(name: str, data: dict) -> list[str]:
    """Every feature the generated .gb will carry must resolve to a Sequence
    Ontology accession, so the .gb is uniformly SO-typed for downstream
    consumers (notably seqmake, which reads ``/db_xref="SO:..."`` from the .gb
    instead of recomputing it -- see tools/part_json._with_so_dbxref).

    A feature passes if it already carries an explicit SO ``/db_xref`` (an
    override) OR its type is mappable via ``tools/so_terms.so_for`` (which
    ``part_json`` then injects at .gb-build time). Otherwise the type needs an
    entry in ``so_terms.py`` (or the feature an explicit ``/db_xref="SO:..."``).
    Applies to every part -- this is the contract the catalog guarantees."""
    out: list[str] = []
    for f in data.get("features") or []:
        q = f.get("qualifiers") or {}
        if any(str(x).startswith("SO:") for x in q.get("db_xref", [])):
            continue
        rc = (q.get("regulatory_class") or [None])[0]
        lab = (q.get("label") or [None])[0]
        if so_for(f.get("type", ""), rc, lab) is None:
            out.append(f"{name}: feature type {f.get('type')!r} has no SO mapping "
                       f"(add it to tools/so_terms.py, or set an explicit "
                       f"/db_xref=\"SO:...\" on the feature)")
    for f in data.get("uniprot_features") or []:
        if f.get("so_term"):
            continue
        if so_for(f.get("type", "")) is None:
            out.append(f"{name}: uniprot_feature type {f.get('type')!r} has no SO "
                       f"mapping (add it to tools/so_terms.py and the import map)")
    return out


_ANALYSIS_STATES = ("pending", "verified", "sources-pending", "flagged")
_LEVELS = ("low", "medium", "high")


def _claim_verification_problems(name: str, data: dict) -> list[str]:
    """The verification lifecycle must be *coherent and earned* (replaces the old
    review-tier gate; see proposals/cross-check/CLAIM-MODEL.md):

    * ``analysis_status`` is one of pending/verified/sources-pending/flagged and
      ``cross_checked`` is a bool; the two agree (``cross_checked`` iff verified).
    * ``verified`` must be earned: the claim's evidence quote actually comes from the
      primary source (``source.quote_source == 'primary'`` with a verbatim quote) and it
      cites that source -- so the site's trust marker means a real verification happened.
    * ``sources-pending`` (the source could not be reached) must cite a source to fetch,
      and a sourcing/REQUESTS.md entry should exist for it (warned, not failed -- the
      handoff is checked by tools/check_requests.py).
    * once a claim has been analysed (status != pending) it carries a ``usefulness``
      score (low/medium/high) -- the cross-check pass always scores it.

    Applies to every part."""
    out: list[str] = []
    for c in data.get("functional_claims") or []:
        cid = c.get("id")
        status = c.get("analysis_status")
        xc = c.get("cross_checked")
        if status not in _ANALYSIS_STATES:
            out.append(f"{name}: claim {cid!r} has analysis_status {status!r} "
                       f"(not one of {'/'.join(_ANALYSIS_STATES)})")
        if not isinstance(xc, bool):
            out.append(f"{name}: claim {cid!r} cross_checked must be a boolean "
                       f"(got {xc!r})")
        elif (status == "verified") != xc:
            out.append(f"{name}: claim {cid!r} cross_checked={xc} contradicts "
                       f"analysis_status={status!r} (verified iff cross_checked)")

        src = c.get("source") or {}
        if status == "verified":
            if src.get("quote_source") != "primary":
                out.append(f"{name}: claim {cid!r} is 'verified' but its quote is not "
                           f"from the primary source (set quote_source to 'primary' after "
                           f"checking the paper, or use a non-verified status)")
            elif not src.get("quote"):
                out.append(f"{name}: claim {cid!r} is 'verified' but carries no verbatim "
                           f"source quote")
            if not (src.get("pmid") or src.get("doi") or src.get("url")):
                out.append(f"{name}: claim {cid!r} is 'verified' but cites no source "
                           f"(pmid/doi/url)")
        if status == "sources-pending" and not (src.get("pmid") or src.get("doi")
                                                or src.get("url")):
            out.append(f"{name}: claim {cid!r} is 'sources-pending' but cites no source "
                       f"to fetch (pmid/doi/url)")

        if status and status != "pending":
            u = c.get("usefulness")
            if u not in _LEVELS:
                out.append(f"{name}: claim {cid!r} is analysed ({status}) but has no "
                           f"valid usefulness score (low/medium/high; got {u!r})")
    return out


def _claim_type_problems(name: str, data: dict) -> list[str]:
    """Every functional_claim ``type`` must be in the controlled vocabulary
    (``schema/claim_types.json``): a canonical type, or a registered alias that
    grandfathers a historical string. Unknown types are rejected so the vocabulary
    can't drift again (the live data already had affinity/binding_affinity/affinity_binding,
    strength/strength_class, and two one-off *_dynamic_range siblings). Applies to every part."""
    canonical, aliases = _claim_vocab()
    allowed = canonical | aliases
    out: list[str] = []
    for c in data.get("functional_claims") or []:
        t = c.get("type")
        if t is not None and t not in allowed:
            out.append(f"{name}: claim {c.get('id')!r} has unknown type {t!r} "
                       f"(not in schema/claim_types.json; add a canonical type or alias)")
    return out


def _coordinate_problems(name: str, data: dict) -> list[str]:
    """Every feature must lie within the sequence: 0 <= start < end <= len(seq).
    The JSON Schema can bound start/end individually but can't compare them or
    check them against the sequence length, so do it here (catches inverted or
    out-of-range coordinates before they reach the .gb / RDF build)."""
    out: list[str] = []
    n = len(data.get("sequence") or "")
    for grp in ("features", "uniprot_features"):
        for f in data.get(grp) or []:
            s, e = f.get("start"), f.get("end")
            if not isinstance(s, int) or not isinstance(e, int):
                continue  # type errors are the schema's job
            if not (0 <= s < e <= n):
                tag = f.get("label") or (f.get("qualifiers", {}).get("label", [""]) or [""])[0] \
                    or f.get("type", "?")
                out.append(f"{name}: {grp} {tag!r} has out-of-range coordinates "
                           f"start={s} end={e} (sequence length {n})")
    return out


def problems() -> list[str]:
    validator = Draft202012Validator(json.loads(SCHEMA.read_text(encoding="utf-8")))
    out: list[str] = []
    for d in (ROOT / "parts" / "validated", ROOT / "parts" / "candidate"):
        for jf in sorted(d.glob("*.json")):
            data = json.loads(jf.read_text(encoding="utf-8"))
            # The first parent-less feature is the part; a validated part (under
            # validated/) must have a sibling .md, a candidate must not.
            for err in validator.iter_errors(data):
                out.append(f"{jf.name}: {err.message}")
            if data.get("slug") != jf.stem:
                out.append(f"{jf.name}: slug {data.get('slug')!r} != filename")
            # Enforced for every part: coordinates in-bounds, a coherent +
            # earned claim verification lifecycle, and full SO coverage of the
            # features the .gb will carry.
            out.extend(_coordinate_problems(jf.name, data))
            out.extend(_claim_verification_problems(jf.name, data))
            out.extend(_claim_type_problems(jf.name, data))
            out.extend(_so_coverage_problems(jf.name, data))
            md = jf.with_suffix(".md")
            is_validated = d.name == "validated"
            if is_validated:
                if not md.exists():
                    out.append(f"{jf.name}: validated part missing its .md page")
                elif not md.read_text(encoding="utf-8").strip():
                    out.append(f"{jf.name}: validated part's .md page is empty")
                out.extend(_completeness_problems(jf.name, data))
            elif md.exists():
                out.append(f"{jf.name}: candidate part must not have a .md page")
    return out


def main() -> None:
    probs = problems()
    n = sum(1 for _ in (ROOT / "parts").glob("*/*.json"))
    if probs:
        print(f"part JSON validation FAILED ({len(probs)} problems):")
        for p in probs:
            print("  ", p)
        sys.exit(1)
    print(f"part JSON validation passed ({n} files clean).")


if __name__ == "__main__":
    main()
