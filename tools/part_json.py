"""Canonical per-part JSON <-> GenBank conversion.

Phase 0 of the RDF knowledge base makes a **full-fidelity JSON record** the
canonical authored artifact for each part; the ``.gb`` file becomes a *generated*
projection of it (bench-format, still first-class and downloadable), and the
existing readers (``build_catalog.py`` / ``build_rdf.py``) keep consuming the
``.gb`` unchanged. JSON is therefore the spine:

    <slug>.json  (canonical, authored)  --build_gb-->  <slug>.gb  --readers-->  catalog.json / RDF / site

The JSON captures the GenBank record losslessly (every feature + qualifier
verbatim, all references, the sequence) plus the home for the
functional-knowledge layer (``functional_claims`` / ``provenance`` /
``review_status``), which has no place in GenBank. Prose stays in the sibling
``<slug>.md`` (authored markdown), not duplicated into the JSON.

Pure BioPython (shared with publish_part / build_catalog); no other deps.
"""
from __future__ import annotations

import io
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, Reference as BioReference, SeqFeature
from Bio.SeqRecord import SeqRecord

SCHEMA_VERSION = "1.0"

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
        "review_status": "ai-generated",
        "provenance": {"migrated_from": "genbank"},
        "functional_claims": [],
    }
    return data


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
            qualifiers={k: list(v) for k, v in f["qualifiers"].items()}))
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
            if f.get("so_term"):
                q["db_xref"] = [f["so_term"]]
            rec.features.append(SeqFeature(
                FeatureLocation(int(f["start"]), int(f["end"]), strand=1),
                type=f["type"], qualifiers=q))
    return rec


def gb_text_from_json(data: dict) -> str:
    """The GenBank text for a part-JSON dict (with the catalog SOURCE convention)."""
    buf = io.StringIO()
    SeqIO.write([json_to_record(data)], buf, "genbank")
    return buf.getvalue().replace(_BIO_SOURCE, _CANON_SOURCE)


def write_gb_from_json(data: dict, path: Path) -> None:
    path.write_text(gb_text_from_json(data), encoding="utf-8")
