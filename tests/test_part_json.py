"""The canonical part-JSON spine: lossless round-trip to .gb + schema validity."""
import glob
import io
import sys
from pathlib import Path

from Bio import SeqIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from part_json import gb_text_from_json, record_to_json  # noqa: E402
from validate_parts import problems  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
GB_FILES = sorted(glob.glob(str(ROOT / "parts" / "*" / "*.gb")))


def test_every_part_has_canonical_json():
    jsons = sorted(glob.glob(str(ROOT / "parts" / "*" / "*.json")))
    assert len(jsons) == len(GB_FILES) > 0


def test_json_round_trips_to_committed_gb():
    """JSON -> .gb reproduces the committed .gb byte-for-byte (the .gb is a
    generated projection of the JSON spine)."""
    import json
    mismatched = []
    for gb in GB_FILES:
        data = json.loads(Path(gb).with_suffix(".json").read_text(encoding="utf-8"))
        if gb_text_from_json(data) != Path(gb).read_text(encoding="utf-8"):
            mismatched.append(gb)
    assert not mismatched, f"JSON->.gb drift: {mismatched[:5]}"


def test_record_json_record_is_faithful():
    """A GenBank record survives record_to_json -> json_to_record -> write."""
    for gb in GB_FILES[:20]:
        rec = SeqIO.read(gb, "genbank")
        data = record_to_json(rec, Path(gb).stem)
        buf = io.StringIO(); SeqIO.write([rec], buf, "genbank")
        # the regenerated text matches a plain SeqIO write (modulo SOURCE dot)
        assert gb_text_from_json(data) == buf.getvalue().replace(
            "SOURCE      \n", "SOURCE      .\n")


def test_uniprot_features_bake_into_gb():
    """Cached uniprot_features are emitted as source-tagged .gb sub-features."""
    data = {
        "schema_version": "1.0", "slug": "Tp", "locus": "Tp", "id": "Tp",
        "description": "t", "molecule_type": "protein",
        "locus_annotations": {"topology": "linear"},
        "sequence": "MKVLATREDGSIPYNQ",
        "references": [],
        "features": [{"type": "CDS", "start": 0, "end": 16, "strand": 1,
                      "qualifiers": {"label": ["Tp"],
                                     "db_xref": ["SO:0000316", "UniProt:P00001"]}}],
        "uniprot_import": {"accession": "UniProt:P00001"},
        "uniprot_features": [{"type": "protein_domain", "start": 1, "end": 10,
                              "label": "Test domain", "so_term": "SO:0000417"}],
    }
    gb = gb_text_from_json(data)
    assert "protein_domain" in gb
    assert '/parent="Tp"' in gb
    assert "source: UniProt:P00001" in gb


def test_all_json_valid_against_schema():
    assert problems() == []
