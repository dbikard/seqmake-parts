"""The local sequence-provenance store (tools/sequences.py): reading the formats a
human drops, classifying carrier-vs-standalone by role, and store keying."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from sequences import (  # noqa: E402
    classify_role, key_for, read_sequence_file)


def test_read_raw_txt_strips_whitespace(tmp_path):
    f = tmp_path / "frag.txt"
    f.write_text("ACGT acgt\nTTTT\n")
    p = read_sequence_file(f)
    assert p["sequence"] == "ACGTACGTTTTT"
    assert p["fmt"] == "raw" and p["n_features"] == 0 and p["length"] == 12


def test_read_fasta(tmp_path):
    f = tmp_path / "part.fasta"
    f.write_text(">myPart some description\nACGTACGTAC\nGTAC\n")
    p = read_sequence_file(f)
    assert p["sequence"] == "ACGTACGTACGTAC"
    assert p["fmt"] == "fasta" and p["name"] == "myPart"


def test_unknown_extension_falls_back_to_raw(tmp_path):
    f = tmp_path / "thing.seq"
    f.write_text("acgtACGT")
    assert read_sequence_file(f)["sequence"] == "ACGTACGT"


def test_classify_role_carrier_vs_standalone():
    # circular OR multi-feature -> carrier (contains a part; byte-verify, never /add-part)
    assert classify_role({"topology": "circular", "n_features": 0}) == "carrier"
    assert classify_role({"topology": "linear", "n_features": 5}) == "carrier"
    # a bare, linear, featureless sequence -> standalone (meant to BE a part)
    assert classify_role({"topology": "linear", "n_features": 0}) == "standalone"
    assert classify_role({"topology": "linear", "n_features": 1}) == "standalone"


def test_key_for_prefers_accession_then_name():
    assert key_for("pDONR221", "AB_123.4") == "acc-ab_123_4"
    assert key_for("pDONR 221", None) == "name-pdonr_221"
    try:
        key_for(None, None)
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("expected ValueError without a name or accession")
