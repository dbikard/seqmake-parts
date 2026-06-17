"""build_gb.py: the .gb writer + the regenerate-all entrypoint.

The pure JSON->.gb text transform is covered by test_part_json.py; this guards
the bits build_gb.py adds on top — writing the file and walking both part
directories — plus that a freshly written .gb is parseable and a fixed point.
"""
import importlib
import json
import sys
from pathlib import Path

from Bio import SeqIO

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from part_json import gb_text_from_json, record_to_json, write_gb_from_json  # noqa: E402


def _sample(slug="Ptest"):
    return {
        "schema_version": "1.0",
        "slug": slug, "locus": slug, "id": slug,
        "description": "synthetic test promoter",
        "molecule_type": "DNA",
        "locus_annotations": {"topology": "linear"},
        "sequence": "tctgatttaatctgtatcaggctgaaaatcttctctcatccgccaaaaca",
        "references": [],
        "features": [
            {"type": "promoter", "start": 0, "end": 50, "strand": 1,
             "qualifiers": {"label": [slug], "db_xref": ["SO:0000167"]}},
            {"type": "regulatory", "start": 16, "end": 22, "strand": 1,
             "qualifiers": {"label": ["-35"], "parent": [slug],
                            "db_xref": ["SO:0000175"]}},
        ],
    }


def test_write_gb_matches_text(tmp_path):
    """write_gb_from_json writes exactly what gb_text_from_json renders."""
    data = _sample()
    out = tmp_path / "Ptest.gb"
    write_gb_from_json(data, out)
    assert out.read_text(encoding="utf-8") == gb_text_from_json(data)


def test_generated_gb_is_parseable_and_faithful(tmp_path):
    """A freshly written .gb parses as GenBank and preserves seq + main label."""
    data = _sample()
    out = tmp_path / "Ptest.gb"
    write_gb_from_json(data, out)
    rec = SeqIO.read(out, "genbank")
    assert str(rec.seq).lower() == data["sequence"].lower()
    labels = [f.qualifiers.get("label", [None])[0] for f in rec.features]
    assert "Ptest" in labels and "-35" in labels


def test_json_gb_json_is_a_fixed_point(tmp_path):
    """JSON -> .gb -> parse -> JSON -> .gb does not drift (re-build is stable)."""
    data = _sample()
    out = tmp_path / "Ptest.gb"
    write_gb_from_json(data, out)
    reparsed = record_to_json(SeqIO.read(out, "genbank"), "Ptest")
    assert gb_text_from_json(reparsed) == gb_text_from_json(data)


def test_main_regenerates_both_part_dirs(tmp_path, monkeypatch, capsys):
    """build_gb.main() walks parts/validated + parts/candidate and writes a .gb
    next to every .json, without touching the real repo."""
    import build_gb
    importlib.reload(build_gb)
    for status, slug in [("validated", "Pone"), ("candidate", "Ptwo")]:
        d = tmp_path / "parts" / status
        d.mkdir(parents=True)
        (d / f"{slug}.json").write_text(json.dumps(_sample(slug)), encoding="utf-8")
    monkeypatch.setattr(build_gb, "ROOT", tmp_path)
    build_gb.main()
    assert (tmp_path / "parts" / "validated" / "Pone.gb").exists()
    assert (tmp_path / "parts" / "candidate" / "Ptwo.gb").exists()
    assert "regenerated 2" in capsys.readouterr().out
    assert str(SeqIO.read(tmp_path / "parts" / "validated" / "Pone.gb", "genbank").seq).lower() \
        == _sample()["sequence"].lower()
