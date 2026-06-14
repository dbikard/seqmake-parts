"""The UniProt sequence classifier: match / same-length variant / mismatch."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from import_uniprot_features import classify_sequences  # noqa: E402


def test_exact_match():
    assert classify_sequences("MKLV", "MKLV") == {"status": "match"}


def test_same_length_point_variant_is_importable():
    # one substitution (e.g. N73D) -> coordinates still valid -> import as variant
    r = classify_sequences("MKLNV", "MKLDV")
    assert r["status"] == "variant"
    assert r["variants"] == [{"pos": 4, "part": "N", "uniprot": "D"}]


def test_too_many_substitutions_is_mismatch():
    r = classify_sequences("AAAAAAAAAA", "BBBBBBBBBB")
    assert r["status"] == "mismatch"
    assert r["n_substitutions"] == 10


def test_length_change_is_length_mismatch():
    r = classify_sequences("MKLV", "MKLVAA")
    assert r["status"] == "length_mismatch"
    assert (r["part_len"], r["uniprot_len"]) == (4, 6)
    assert r["first_diff"] == 5
