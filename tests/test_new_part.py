"""The authoring scaffold: a new part skeleton is schema-valid and buildable."""
import json
import sys
from pathlib import Path

from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from new_part import build_skeleton  # noqa: E402
from part_json import gb_text_from_json, json_to_record  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = json.loads((ROOT / "schema" / "part.schema.json").read_text())


def test_skeleton_is_schema_valid_and_typed():
    data = build_skeleton("Pxyz", "promoter", "TTGACAGGGGGGGGGGGGTATAAT",
                          synonyms=["Pxyz alt"], note="a test promoter",
                          regulated_by=["SomeTF"])
    assert Draft202012Validator(SCHEMA).is_valid(data)
    main = data["features"][0]
    assert "parent" not in main["qualifiers"]              # main feature
    assert main["qualifiers"]["db_xref"] == ["SO:0000167"]  # promoter SO term
    assert main["qualifiers"]["regulated_by"] == ["SomeTF"]
    assert data["molecule_type"] == "DNA"
    assert data["review_status"] == "ai-generated"
    assert "sequence_source" in data["provenance"]          # forces a citation


def test_skeleton_protein_is_detected():
    data = build_skeleton("Enz", "CDS", "MKVLATREDGSIPYNQ",
                          source_accession="UniProt:Q12345")
    assert data["molecule_type"] == "protein"
    assert data["features"][0]["qualifiers"]["db_xref"] == ["SO:0000316", "UniProt:Q12345"]


def test_skeleton_builds_a_genbank():
    data = build_skeleton("Pxyz", "promoter", "TTGACATATAAT")
    json_to_record(data)            # reconstructs without error
    assert gb_text_from_json(data).startswith("LOCUS")
