"""The pure analysis in tools/source_finder.py — divergence, location class, source
selection, protein sourcing. (The NCBI BLAST orchestration is not unit-tested.)"""
import sys
from pathlib import Path

from Bio.Seq import Seq

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from source_finder import (  # noqa: E402
    classify_location, divergence, looks_named, pick_best, protein_source)

Q = "ATGCAGTTCGGATCCGAATTCAAAGGTCTAGACCATGGCT"  # 40 bp, low internal repeat


def _mut(seq, pos, base):
    return seq[:pos] + base + seq[pos + 1:]


def test_classify_location():
    assert classify_location([], 40) == "exact"
    assert classify_location([20], 40) == "internal"
    assert classify_location([2], 40) == "edge"
    assert classify_location([38], 40) == "edge"
    assert classify_location([2, 20], 40) == "mixed"


def test_divergence_exact_substring():
    d = divergence(Q, "TTTTT" + Q + "GGGGG")
    assert d["location"] == "exact" and d["n_mismatch"] == 0
    assert d["identity_pct"] == 100.0 and d["strand"] == "+"


def test_divergence_internal_snp():
    b = "A" if Q[20] != "A" else "C"
    d = divergence(Q, _mut(Q, 20, b))
    assert d["n_mismatch"] == 1 and d["mismatch_positions"] == [20]
    assert d["location"] == "internal" and 95 < d["identity_pct"] < 100


def test_divergence_edge_snp():
    b = "A" if Q[3] != "A" else "C"
    d = divergence(Q, _mut(Q, 3, b))
    assert d["mismatch_positions"] == [3] and d["location"] == "edge"


def test_divergence_circular_wrap():
    rot = Q[25:] + Q[:25]            # Q spans the origin of the (doubled) subject
    d = divergence(Q, rot)
    assert d["location"] == "exact" and d["n_mismatch"] == 0


def test_divergence_reverse_complement():
    d = divergence(Q, str(Seq(Q).reverse_complement()))
    assert d["location"] == "exact" and d["strand"] == "-"


def test_looks_named():
    assert looks_named("Cloning vector pEX2")
    assert looks_named("Human ORFeome Gateway entry vector pENTR223-WDR4")
    assert not looks_named("Transposable P vector conferring G418 resistance in Drosophila")
    assert not looks_named("Escherichia coli genomic DNA")


def test_pick_best_prefers_oldest_then_named():
    c = [{"date": "1990/01/01", "title": "x", "named": False},
         {"date": "1986/01/01", "title": "Cloning vector pEX2", "named": True},
         {"date": "1986/01/01", "title": "raw fragment", "named": False}]
    assert pick_best(c)["title"] == "Cloning vector pEX2"
    assert pick_best([]) is None


def test_protein_source_from_uniprot_import():
    part = {"molecule_type": "protein",
            "features": [{"qualifiers": {"db_xref": ["SO:0000316", "UniProt:P03051"]}}],
            "uniprot_import": {"accession": "UniProt:P03051", "status": "match", "identity": 1.0}}
    s = protein_source(part)
    assert "UniProt:P03051" in s["sequence_source"] and s["match"] == "match"
