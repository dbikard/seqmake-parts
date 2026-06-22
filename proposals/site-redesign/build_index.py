#!/usr/bin/env python3
"""Extract a compact, search-ready index from catalog.json for the redesign prototype.

Writes data.js (window.CATALOG = {...}) next to this script so the prototype
is openable directly over file:// without a server. This is the same shape a
real client-side search index would take, built by tools/build_catalog.py.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from build_catalog import build_molecule_json  # noqa: E402  (the real widget contract)


def claim_payload(fcs):
    """Full functional_claims for the detail view (label + source + the scoring axes)."""
    out = []
    for c in fcs:
        s = c.get("source") or {}
        out.append({
            "id": c.get("id"), "type": c.get("type"), "label": c.get("label"),
            "value": c.get("value"),
            "source": {k: s.get(k) for k in
                       ("pmid", "doi", "url", "quote", "quote_source", "figure", "table", "page", "section")
                       if s.get(k)},
            "confidence": c.get("confidence"),
            # forward-looking axes (present once the corrector writes them; harmless if absent)
            "cross_checked": c.get("cross_checked"),
            "usefulness": c.get("usefulness"),
            "comment": c.get("comment"),
            "review_status": c.get("review_status"),
        })
    return out


def ref_payload(refs):
    out = []
    for r in refs or []:
        doi = None
        m = re.search(r"doi:(\S+)", r.get("comment", "") or "")
        if m:
            doi = m.group(1)
        out.append({"title": r.get("title"), "authors": r.get("authors"),
                    "journal": r.get("journal"), "pmid": r.get("pubmed_id"), "doi": doi})
    return out


def molecule_for(slug, status):
    gb = os.path.join(ROOT, "parts", "validated" if status == "validated" else "candidate", f"{slug}.gb")
    try:
        return build_molecule_json(gb)
    except Exception:
        return None

# SO type display order + the base/specimen hue assigned to each in the UI.
TYPE_ORDER = [
    "promoter", "ribosome_entry_site", "operator", "CDS", "polypeptide_domain",
    "terminator", "origin_of_replication", "oriT", "protein_binding_site",
    "ncRNA", "sequence_feature",
]


def tf_names(part):
    out = []
    for r in part.get("regulated_by", []) or []:
        if isinstance(r, dict):
            n = r.get("name")
        else:
            n = r
        if n:
            out.append(n)
    return out


def main():
    cat = json.load(open(os.path.join(ROOT, "catalog.json")))
    parts_out = []
    for p in cat["parts"]:
        fcs = p.get("functional_claims", []) or []
        review = sorted({fc.get("review_status") for fc in fcs if fc.get("review_status")})
        claim_types = sorted({fc.get("type") for fc in fcs if fc.get("type")})
        cols = []
        for col in p.get("collections", []) or []:
            cols.append(col.get("name") if isinstance(col, dict) else col)
        parts_out.append({
            "name": p["name"],
            "slug": p["slug"],
            "type": p["feature_type"],
            "so_name": p.get("so_name"),
            "so_term": p.get("so_term"),
            "kind": p.get("kind"),
            "status": p.get("status"),
            "documented": bool(p.get("documented")),
            "len": p.get("length"),
            "aa": p.get("protein_length_aa"),
            "syn": p.get("synonyms", []) or [],
            "desc": p.get("description") or "",
            "cols": cols,
            "acc": p.get("source_accession") or "",
            "tf": tf_names(p),
            "regs": [r.get("name") if isinstance(r, dict) else r
                     for r in (p.get("regulates", []) or [])],
            "nclaims": len(fcs),
            "claim_types": claim_types,
            "review": review,
            "nrefs": len(p.get("references", []) or []),
            "uniprot": (p.get("uniprot_import") or {}).get("accession"),
            # full detail payload (the page is a real detail view now, not a drawer preview)
            "claims": claim_payload(fcs),
            "refs": ref_payload(p.get("references")),
            "mol": molecule_for(p["slug"], p.get("status")),
        })

    # type taxonomy with counts (validated / total)
    types = {}
    for p in cat["parts"]:
        t = p["feature_type"]
        e = types.setdefault(t, {
            "type": t, "so_name": p.get("so_name"), "so_term": p.get("so_term"),
            "total": 0, "validated": 0,
        })
        e["total"] += 1
        if p.get("status") == "validated":
            e["validated"] += 1
    types_list = sorted(types.values(),
                        key=lambda e: (TYPE_ORDER.index(e["type"])
                                       if e["type"] in TYPE_ORDER else 99))

    out = {
        "meta": {
            "n_parts": cat["n_parts"],
            "n_validated": cat["n_validated"],
            "n_candidate": cat["n_candidate"],
            "n_documented": cat["n_documented"],
            "n_claims": cat["n_functional_claims"],
            "schema_version": cat.get("schema_version"),
        },
        "types": types_list,
        "collections": cat.get("collections", []),
        "parts": parts_out,
    }

    path = os.path.join(HERE, "data.js")
    with open(path, "w") as f:
        f.write("window.CATALOG = ")
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)
        f.write(";\n")
    print(f"wrote {path}  ({os.path.getsize(path)//1024} KB, {len(parts_out)} parts)")


if __name__ == "__main__":
    main()
