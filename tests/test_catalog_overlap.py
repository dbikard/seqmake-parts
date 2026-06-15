"""tools/catalog_overlap.py — k-mer/containment overlap detection (no network)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from catalog_overlap import canon_kmers, containment, relation, scan  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
Q = "ATGCAGTTCGGATCCGAATTCAAAGGTCTAGACCATGGCTTTACGCATGCAAGCTTGGCA"  # 60 bp
_C = str.maketrans("ACGT", "TGCA")


def _rc(s):
    return s.translate(_C)[::-1]


def test_canon_kmers_strand_independent():
    assert canon_kmers(Q, 16) == canon_kmers(_rc(Q), 16)


def test_containment_relations():
    assert containment(Q, Q) == "identical"
    assert containment(Q, "TTTT" + Q + "GGGG") == "contained_by"
    assert containment("TTTT" + Q + "GGGG", Q) == "contains"
    assert containment(_rc(Q), "AAA" + Q + "CCC") == "contained_by"   # strand-aware
    assert containment(Q, "TTTTTTTTTTTTTTTTTTTT") is None


def test_relation_partial_overlap():
    common = "GACCTTAGCATCCGATTGCACGTAAGCTTGATCCGAATTCGT"     # 42 bp shared
    a = common + "AAAACCCCGGGGTTTTACACACACGTGTGTGTAGAGAGAGTC"
    b = "TTGGTTGGAACCAACCTCTCTCTCTAGAGAGAGCACACACAC" + common
    r = relation(a, b, k=16, min_overlap=30)
    assert r and r["relation"] == "overlap" and r["est_overlap_bp"] >= 30


def test_relation_none_when_unrelated():
    a = "AAAACCCCGGGGTTTTAAAACCCCGGGGTTTTAAAACCCC"
    b = "TGTGTGACACACGTGTACGTACGTGTACACACGTGTGTGT"
    assert relation(a, b, k=16) is None


def test_relation_near_identical_real_data():
    cole1 = json.loads((ROOT / "parts/validated/ColE1.json").read_text())["sequence"]
    cole1_at = json.loads((ROOT / "parts/validated/ColE1_AT.json").read_text())["sequence"]
    r = relation(cole1_at, cole1, k=16)
    assert r and r["relation"] == "near_identical" and r["q_frac"] > 0.9


def test_scan_surfaces_sibling_in_real_catalog():
    cole1_at = json.loads((ROOT / "parts/validated/ColE1_AT.json").read_text())["sequence"]
    hits = scan(cole1_at, exclude="ColE1_AT")
    cole1 = next((h for h in hits if h["slug"] == "ColE1"), None)
    assert cole1 is not None and cole1["relation"] == "near_identical"
