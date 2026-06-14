"""The UniProt sequence classifier: it must tell a few-SNP variant from a wrong
accession (and from an isoform), using sequence identity."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from import_uniprot_features import classify_sequences  # noqa: E402

# A realistic-length base protein so identities are meaningful.
BASE = ("MKVLAT" * 30)            # 180 aa


def test_exact_match():
    assert classify_sequences(BASE, BASE)["status"] == "match"


def test_few_snps_is_a_variant():
    v = list(BASE)
    v[10], v[50] = "D", "E"        # 2 substitutions -> ~99% identity
    r = classify_sequences("".join(v), BASE)
    assert r["status"] == "variant"
    assert len(r["variants"]) == 2
    assert r["identity"] > 0.98


def test_wrong_accession_is_flagged_distinctly():
    # a different protein of the same length -> very low identity
    other = ("WYFPGQ" * 30)
    r = classify_sequences(other, BASE)
    assert r["status"] == "wrong_accession"
    assert r["identity"] < 0.6


def test_length_variant_is_same_protein_not_wrong():
    # same protein, truncated (an isoform/fragment) -> high identity, length change
    r = classify_sequences(BASE[:150], BASE)
    assert r["status"] == "length_variant"
    assert r["identity"] >= 0.9
    assert (r["part_len"], r["uniprot_len"]) == (150, 180)


def test_wrong_accession_on_length_change_too():
    # different protein AND different length -> still wrong_accession, not isoform
    r = classify_sequences("WYFPGQ" * 20, BASE)   # 120 aa, unrelated
    assert r["status"] == "wrong_accession"
    assert r["identity"] < 0.6
