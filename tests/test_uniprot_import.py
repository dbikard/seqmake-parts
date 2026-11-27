"""The UniProt sequence classifier: it must tell a few-SNP variant from a wrong
accession (and from an isoform), using sequence identity."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import pytest  # noqa: E402

from import_uniprot_features import (  # noqa: E402
    classify_sequences,
    _next_link,
    parse_uniparc,
    parse_uniparc_databases,
    variant_disposition,
)


def test_parse_uniparc_returns_the_exact_uniparc_ids():
    # the search response (2026 shape): no cross-references, only the UPI and
    # a bare accession list that carries no active flag
    seq = "MKVLAT" * 5
    data = {"results": [
        {"uniParcId": "UPI0000000001", "sequence": {"value": seq},
         "uniProtKBAccessions": ["P00000.1", "A0A111.1"]},
        {"uniParcId": "UPI0000000002", "sequence": {"value": "DIFFERENT"}},
    ]}
    assert parse_uniparc(data, seq) == ["UPI0000000001"]


def test_parse_uniparc_ignores_non_exact_sequences():
    # a checksum hit whose sequence differs (collision) must be ignored
    data = {"results": [{"uniParcId": "UPI0000000002", "sequence": {"value": "DIFFERENT"}}]}
    assert parse_uniparc(data, "MKVLAT" * 5) == []


def test_parse_uniparc_raises_on_an_unknown_response_shape():
    # an exact hit it cannot follow must not read as "no other accession": that
    # silently sent the importer on to normalize the part's residues
    seq = "MKVLAT" * 5
    data = {"results": [{"sequence": {"value": seq},
                         "uniParcCrossReferences": [
                             {"database": "UniProtKB/TrEMBL", "id": "A0A111", "active": True}]}]}
    with pytest.raises(ValueError):
        parse_uniparc(data, seq)


def test_parse_uniparc_databases_returns_active_uniprotkb_reviewed_then_oldest():
    data = {"results": [
        {"database": "UniProtKB/TrEMBL", "id": "A0A111", "active": True, "created": "2016-01-20"},
        {"database": "UniProtKB/Swiss-Prot", "id": "P99999", "active": True, "created": "2020-01-01"},
        {"database": "UniProtKB/Swiss-Prot", "id": "P00000", "active": False, "created": "1986-07-21"},
        {"database": "EnsemblBacteria", "id": "X1", "active": True},
        {"database": "UniProtKB/TrEMBL", "id": "A0A111", "active": True, "created": "2016-01-20"},
        {"database": "UniProtKB/TrEMBL", "id": "Q79DX9", "active": True, "created": "2004-07-05"},
        {"database": "UniProtKB/TrEMBL", "id": "Z9Z999", "active": True},
    ]}
    assert [h[:2] for h in parse_uniparc_databases(data)] == [
        ("P99999", True), ("Q79DX9", False), ("A0A111", False), ("Z9Z999", False)]


def test_next_link_reads_the_rel_next_url():
    hdr = '<https://rest.uniprot.org/uniparc/UPI1/databases?cursor=abc&size=500>; rel="next"'
    assert _next_link(hdr) == "https://rest.uniprot.org/uniparc/UPI1/databases?cursor=abc&size=500"
    assert _next_link(None) is None
    assert _next_link("") is None


def test_incidental_variant_is_normalized():
    assert variant_disposition({}) == "normalize"
    assert variant_disposition({"variant_rationale": "  "}) == "normalize"


def test_intentional_variant_is_kept():
    assert variant_disposition({"variant_rationale": "dCas9 D10A/H840A"}) == "keep"

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
