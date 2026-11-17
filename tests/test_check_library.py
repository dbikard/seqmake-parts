"""tools/check_library.py -- each check of the library quality gate can fail."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from check_library import findings, longest_orf  # noqa: E402

PROMOTER = "TTGACAATTAATCATCGGCTCGTATAATGTGTGGAATTGTGAGCGG"  # 46 bp, no long ORF
OPERATOR = "AATTGTGAGCGGATAACAATT"                             # 21 bp


def _part(slug, seq, ftype="promoter", status="candidate", synonyms=(), children=(),
          protein=False, refs=False, **links):
    q = {"label": [slug], "synonym": list(synonyms), **{k: [v] for k, v in links.items()}}
    feats = [{"type": ftype, "start": 0, "end": len(seq), "strand": 1, "qualifiers": q}]
    feats += [{"type": "protein_bind", "start": s, "end": e, "strand": 1,
               "qualifiers": {"label": [lab], "parent": [par or slug]}}
              for lab, s, e, par in children]
    return status, {"slug": slug, "molecule_type": "protein" if protein else "DNA",
                    "sequence": seq, "features": feats,
                    "references": [{"title": "t"}] if refs else []}


def _catalog(tmp_path, *parts, manifest=True):
    for status, d in parts:
        (tmp_path / "parts" / status).mkdir(parents=True, exist_ok=True)
        (tmp_path / "parts" / status / f"{d['slug']}.json").write_text(json.dumps(d))
    rows = [{"slug": d["slug"], "name": d["slug"], "status": st,
             "synonyms": d["features"][0]["qualifiers"]["synonym"],
             "sourced": bool(d["references"])} for st, d in parts]
    for f in ("catalog.json", "index.json"):
        (tmp_path / f).write_text(json.dumps({"parts": rows if manifest else rows[1:]}))
    return findings(tmp_path)


def _kinds(out):
    return sorted({line.split("]")[0] + "]" for line in out})


def test_clean_catalog_passes(tmp_path):
    assert _catalog(tmp_path, _part("Pa", PROMOTER), _part("Pb", OPERATOR + "GGCC")) == []


def test_shared_synonym_fails(tmp_path):
    out = _catalog(tmp_path, _part("Pa", PROMOTER, synonyms=["tet promoter"]),
                   _part("Pb", OPERATOR + "GGCC", synonyms=["TET promoter"]))
    assert _kinds(out) == ["[names]"]


def test_near_duplicate_fails_unless_linked(tmp_path):
    variant = PROMOTER[:20] + "G" + PROMOTER[21:]                 # 1 of 46 bp = 97.8%
    assert _catalog(tmp_path, _part("Pa", PROMOTER), _part("Pb", variant)) == []
    long_a, long_b = PROMOTER * 2, PROMOTER * 2
    long_b = long_b[:30] + "A" + long_b[31:]                      # 1 of 92 bp = 98.9%
    out = _catalog(tmp_path / "x", _part("Pa", long_a), _part("Pb", long_b))
    assert _kinds(out) == ["[duplicate]"]
    out = _catalog(tmp_path / "y", _part("Pa", long_a), _part("Pb", long_b, variant_of="Pa"))
    assert out == []


def test_containment_needs_a_child_or_link(tmp_path):
    outer = PROMOTER + OPERATOR
    out = _catalog(tmp_path, _part("Pa", outer), _part("lacO", OPERATOR, ftype="protein_bind"))
    assert _kinds(out) == ["[contains]"]
    # a child under another name does not declare it; one under its name does
    out = _catalog(tmp_path / "x", _part("Pa", outer, children=[("operator", 46, 67, None)]),
                   _part("lacO", OPERATOR, ftype="protein_bind"))
    assert _kinds(out) == ["[contains]"]
    out = _catalog(tmp_path / "y", _part("Pa", outer, children=[("lacO", 46, 67, None)]),
                   _part("lacO", OPERATOR, ftype="protein_bind"))
    assert out == []
    # every copy must be declared, on either strand
    rc = OPERATOR.translate(str.maketrans("ACGT", "TGCA"))[::-1]
    out = _catalog(tmp_path / "z", _part("Pa", outer + "CC" + rc, children=[("lacO", 46, 67, None)]),
                   _part("lacO", OPERATOR, ftype="protein_bind"))
    assert _kinds(out) == ["[contains]"]


def test_near_containment_fails_unless_declared(tmp_path):
    """The ts_ori101 shape: a part almost inside a longer one, under the
    duplicate threshold and not an exact containment."""
    inner = PROMOTER * 3                                   # 138 bp
    flank = "GGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGGCCTTAAGG"
    mutated = inner[:40] + "A" + inner[41:60] + "T" + inner[61:]   # 2 of 138 = 98.6%
    out = _catalog(tmp_path, _part("ori", flank + mutated + flank, ftype="rep_origin"),
                   _part("core", inner, ftype="rep_origin"))
    assert _kinds(out) == ["[near]"]
    # a link, or a child carrying the part's name, declares it
    out = _catalog(tmp_path / "x", _part("ori", flank + mutated + flank, ftype="rep_origin",
                                         variant_of="core"),
                   _part("core", inner, ftype="rep_origin"))
    assert out == []
    out = _catalog(tmp_path / "y",
                   _part("ori", flank + mutated + flank, ftype="rep_origin",
                         children=[("core", len(flank), len(flank) + len(inner), None)]),
                   _part("core", inner, ftype="rep_origin"))
    assert out == []
    # half of the part inside the longer one is neither a near-containment nor a duplicate
    out = _catalog(tmp_path / "z", _part("ori", flank + inner[:69] + flank, ftype="rep_origin"),
                   _part("core", inner, ftype="rep_origin"))
    assert out == []


def test_names_ignore_case_spaces_and_punctuation(tmp_path):
    out = _catalog(tmp_path, _part("Pcat", PROMOTER), _part("Pb", OPERATOR + "GGCC",
                                                            synonyms=["P-cat"]))
    assert _kinds(out) == ["[names]"]
    assert "'P-cat'" in out[0] and "'Pcat'" in out[0]
    # letters still count: a Greek suffix is a different name
    assert _catalog(tmp_path / "x", _part("lacZ", PROMOTER),
                    _part("lacZ\u03b1", OPERATOR + "GGCC")) == []


def test_orf_short_and_subfeature_fail(tmp_path):
    gene = "ATG" + "GCT" * 110 + "TAA"                           # 336 bp, one ORF
    assert longest_orf(gene) == len(gene)
    out = _catalog(tmp_path, _part("ori", gene, ftype="rep_origin"),
                   _part("site", "ACGTACGTAC", ftype="protein_bind"),
                   _part("Pa", PROMOTER, children=[("-10", 40, 50, None), ("x", 0, 5, "Pz")]))
    assert _kinds(out) == ["[orf]", "[short]", "[subfeature]"]
    assert _catalog(tmp_path / "x", _part("cds", gene, ftype="CDS")) == []


def test_manifest_and_status_fail(tmp_path):
    out = _catalog(tmp_path, _part("Pa", PROMOTER, status="validated"),
                   _part("Pb", OPERATOR + "GGCC"), manifest=False)
    assert _kinds(out) == ["[manifest]", "[status]"]


def test_predicted_boxes_must_be_what_the_criteria_give(tmp_path):
    """A predicted -35/-10 is re-derived from the sequence; a shifted or
    weak one, an unlabelled one, or an uncited experimental one fails."""
    seq = "GGATCCAAATAAAAAACTAGTTTGACAAATAACTCTATCAATGATATAATGTCAAC"   # 56 bp

    def promoter(boxes, label_suffix=" (predicted)", ev="predicted"):
        status, d = _part("Ptest", seq)
        for lab, start, kind in boxes:
            d["features"].append({"type": "regulatory", "start": start, "end": start + 6,
                                  "strand": 1, "qualifiers": {
                                      "label": [lab + label_suffix], "parent": ["Ptest"],
                                      "regulatory_class": [kind], "evidence": [ev]}})
        return status, d

    good = [("-35", 21, "minus_35_signal"), ("-10", 44, "minus_10_signal")]
    assert _catalog(tmp_path, promoter(good)) == []
    shifted = [("-35", 20, "minus_35_signal"), ("-10", 44, "minus_10_signal")]
    assert _kinds(_catalog(tmp_path / "a", promoter(shifted))) == ["[evidence]"]
    assert _kinds(_catalog(tmp_path / "b", promoter(good, label_suffix=""))) == ["[evidence]"]
    assert _kinds(_catalog(tmp_path / "c", promoter(good, ev="experimental"))) == ["[evidence]"]
    weak = "A" * 21 + "TTGTCC" + seq[27:44] + "TAGAGT" + seq[50:]          # 3/6 and 4/6
    status, d = promoter(good)
    d["sequence"] = weak
    assert _kinds(_catalog(tmp_path / "d", (status, d))) == ["[evidence]"]
