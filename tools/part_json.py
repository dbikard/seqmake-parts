"""Canonical per-part JSON <-> GenBank conversion.

Phase 0 of the RDF knowledge base makes a **full-fidelity JSON record** the
canonical authored artifact for each part; the ``.gb`` file becomes a *generated*
projection of it (bench-format, still first-class and downloadable), and the
existing readers (``build_catalog.py`` / ``build_rdf.py``) keep consuming the
``.gb`` unchanged. JSON is therefore the spine:

    <slug>.json  (canonical, authored)  --build_gb-->  <slug>.gb  --readers-->  catalog.json / RDF / site

The JSON captures the GenBank record losslessly (every feature + qualifier
verbatim, all references, the sequence) plus the home for the
functional-knowledge layer (``functional_claims`` with their verification
lifecycle / ``provenance``), which has no place in GenBank. Prose stays in the
sibling ``<slug>.md`` (authored markdown), not duplicated into the JSON.

Pure BioPython (shared with publish_part / build_catalog); no other deps.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, Reference as BioReference, SeqFeature
from Bio.SeqRecord import SeqRecord

sys.path.insert(0, str(Path(__file__).resolve().parent))
from so_terms import so_for  # noqa: E402

SCHEMA_VERSION = "1.0"

# The catalog's permanent base IRI for a part (w3id.org -> the live site). Stamped
# into the generated .gb so the downloadable bench file carries its own stable
# catalog identifier. Mirrors ``build_rdf.PART``; keep them in sync. It goes in
# COMMENT rather than the semantically-natural DBLINK because BioPython mangles
# URLs in DBLINK (inserts a space after ``https:``); COMMENT round-trips intact.
PART_IRI_BASE = "https://w3id.org/seqmake/parts/part/"

# BioPython writes an empty SOURCE as ``SOURCE      `` (no trailing dot); the
# catalog's established convention is ``SOURCE      .``. Normalise on write so a
# regenerated .gb is byte-stable against the existing corpus.
_BIO_SOURCE = "SOURCE      \n"
_CANON_SOURCE = "SOURCE      .\n"

# Reference attributes captured for a faithful round-trip (only non-empty ones
# are stored, so the JSON stays clean).
_REF_ATTRS = ("authors", "title", "journal", "pubmed_id", "medline_id",
              "consrtm", "comment")

# LOCUS-line annotations carried so the regenerated .gb is byte-faithful (e.g.
# the ``linear`` topology); only non-default values are stored.
_LOCUS_ANNOTS = ("topology", "data_file_division", "date")


def record_to_json(rec: SeqRecord, slug: str) -> dict:
    """Serialize a BioPython ``SeqRecord`` into the canonical part-JSON dict.

    Captures the record faithfully (id/locus/description/molecule_type, the
    sequence, every reference and feature with qualifiers verbatim) and seeds the
    functional-knowledge layer empty. Prose lives in the sibling ``.md``."""
    refs = []
    for r in rec.annotations.get("references", []):
        d = {a: getattr(r, a) for a in _REF_ATTRS if getattr(r, a, "")}
        refs.append(d)
    feats = []
    for f in rec.features:
        feats.append({
            "type": f.type,
            "start": int(f.location.start),
            "end": int(f.location.end),
            "strand": 1 if f.location.strand in (None, 1) else -1,
            "qualifiers": {k: [str(x) for x in v]
                           for k, v in f.qualifiers.items()},
        })
    data: dict = {
        "schema_version": SCHEMA_VERSION,
        "slug": slug,
        "locus": rec.name,
        "id": rec.id,
        "description": rec.description,
        "molecule_type": rec.annotations.get("molecule_type", "DNA"),
        "locus_annotations": {a: rec.annotations[a] for a in _LOCUS_ANNOTS
                              if rec.annotations.get(a)},
        "sequence": str(rec.seq),
        "references": refs,
        "features": feats,
        # Functional-knowledge layer (Phase 2) -- the home for prose-derived
        # claims that do not fit GenBank. Empty at migration time.
        "provenance": {"migrated_from": "genbank"},
        "functional_claims": [],
    }
    return data


def _with_so_dbxref(ftype: str, quals: dict) -> dict:
    """Ensure the feature's qualifiers carry a Sequence Ontology ``/db_xref``.

    The SO accession is a *derived projection* of the GenBank feature type
    (via ``so_terms.so_for``), so the generated .gb is uniformly SO-typed for
    downstream consumers (e.g. seqmake reads ``/db_xref="SO:..."`` rather than
    recomputing it). An SO db_xref already present is treated as an explicit
    per-feature override and kept verbatim; otherwise the derived accession is
    prepended (SO-first, matching ``publish_part``'s convention). A type with no
    mapping is left untouched -- ``validate_parts`` gates against that case."""
    db = list(quals.get("db_xref", []))
    if any(str(x).startswith("SO:") for x in db):
        return quals
    so = so_for(ftype, (quals.get("regulatory_class") or [None])[0],
                (quals.get("label") or [None])[0])
    if not so:
        return quals
    return {**quals, "db_xref": [so[0], *db]}


def json_to_record(data: dict) -> SeqRecord:
    """Reconstruct a BioPython ``SeqRecord`` from a canonical part-JSON dict
    (the inverse of ``record_to_json``)."""
    rec = SeqRecord(
        Seq(data["sequence"]),
        id=data["id"], name=data["locus"], description=data["description"],
        annotations={"molecule_type": data["molecule_type"],
                     **data.get("locus_annotations", {})})
    refs = []
    for r in data.get("references", []):
        br = BioReference()
        for a in _REF_ATTRS:
            if r.get(a):
                setattr(br, a, r[a])
        refs.append(br)
    if refs:
        rec.annotations["references"] = refs
    for f in data["features"]:
        rec.features.append(SeqFeature(
            FeatureLocation(int(f["start"]), int(f["end"]), strand=f["strand"]),
            type=f["type"],
            qualifiers=_with_so_dbxref(
                f["type"], {k: list(v) for k, v in f["qualifiers"].items()})))
    # Cached UniProt-imported protein features are baked into the .gb as
    # sub-features of the main feature (so GenBank consumers get them), tagged
    # with their source. They are a projection of UniProt, not authored here.
    uf = data.get("uniprot_features") or []
    if uf:
        main = next((g for g in rec.features
                     if "parent" not in g.qualifiers), None)
        main_label = (main.qualifiers.get("label") or [data["slug"]])[0] if main else data["slug"]
        acc = (data.get("uniprot_import") or {}).get("accession", "")
        src = f"source: {acc}" if acc else "source: UniProt"
        for f in uf:
            q = {"label": [f["label"]], "parent": [main_label], "note": [src]}
            so_acc = f.get("so_term")
            if not so_acc:
                m = so_for(f["type"])
                so_acc = m[0] if m else None
            if so_acc:
                q["db_xref"] = [so_acc]
            rec.features.append(SeqFeature(
                FeatureLocation(int(f["start"]), int(f["end"]), strand=1),
                type=f["type"], qualifiers=q))
    return rec


def gb_text_from_json(data: dict) -> str:
    """The GenBank text for a part-JSON dict (with the catalog SOURCE convention).

    Stamps the part's permanent catalog IRI into the record COMMENT so the
    downloadable .gb is self-identifying. The IRI is derived from the slug (so it
    is not stored in the JSON spine, only projected here)."""
    rec = json_to_record(data)
    slug = data.get("slug") or rec.id or rec.name
    if slug:
        rec.annotations["comment"] = (
            f"Permanent catalog identifier: {PART_IRI_BASE}{slug}")
    buf = io.StringIO()
    SeqIO.write([rec], buf, "genbank")
    return buf.getvalue().replace(_BIO_SOURCE, _CANON_SOURCE)


def write_gb_from_json(data: dict, path: Path) -> None:
    path.write_text(gb_text_from_json(data), encoding="utf-8")
