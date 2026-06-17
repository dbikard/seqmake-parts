"""tools/catalog_overlap.py — k-mer/containment overlap detection (no network)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from catalog_overlap import canon_kmers, containment, localize, relation, scan  # noqa: E402

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


# flanks chosen so no boundary base coincides on either strand (no spurious extension)
_BLOCK = "ATGCAGTTCGGATCCGAATTCAAAGGTCTAGACCATGGCTTTACGCATGC"  # 50 bp
_Q = "TTAGGTCA" + _BLOCK + "GACTTGAC"
_S_FWD = "CCGAATAC" + _BLOCK + "ATCGGTTA"


def test_localize_forward_span():
    bm = localize(_Q, _S_FWD, k=16)
    assert bm and bm["strand"] == 1 and bm["bp"] == len(_BLOCK)
    assert bm["subseq"] == _BLOCK and _Q[bm["q_start"]:bm["q_end"]] == _BLOCK
    assert _S_FWD[bm["s_start"]:bm["s_end"]] == _BLOCK


def test_localize_reverse_strand_span_maps_to_subject_coords():
    # the shared block sits on the REVERSE strand of the subject (the rrnBT1/attP case)
    s = _rc(_S_FWD)                                     # block is now reverse-complemented in s
    bm = localize(_Q, s, k=16)
    assert bm and bm["strand"] == -1 and bm["bp"] == len(_BLOCK)
    assert s[bm["s_start"]:bm["s_end"]] == _rc(_BLOCK)  # s_* are subject FORWARD coords
    assert relation(_Q, s, k=16)["best_match"]["strand"] == -1


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
