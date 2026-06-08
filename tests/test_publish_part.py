"""The authoring half of the catalog loop: proposal -> validated catalog part."""
import json
import sys
from pathlib import Path

import pytest
from Bio import SeqIO

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from publish_part import (  # noqa: E402
    PublishError,
    build_part_record,
    publish_part,
    _slugify,
)

PROPOSAL = {
    "part": "TestP",
    "sequence": "TTGACAGGGGGGGGGGGGTATAAT",  # 24 bp: -35 [0:6], -10 [18:24]
    "feature_type": "promoter",
    "children": [
        {"label": "-35 box", "feature_type": "regulatory", "start": 0, "end": 6,
         "strand": 1, "note": "Sigma70 -35 hexamer TTGACA. Verified.",
         "citation_pmids": ["111"]},
        {"label": "-10 box (Pribnow)", "feature_type": "regulatory", "start": 18,
         "end": 24, "strand": 1, "note": "Sigma70 -10. Extra detail.",
         "citation_pmids": ["111"]},
    ],
    "references": [
        {"pmid": "111", "doi": "10.x/y", "authors": "Doe J", "title": "T", "journal": "J 2020"},
        {"pmid": "222", "doi": "", "authors": "Roe R", "title": "Origin", "journal": "J 2019"},
    ],
    "report_markdown": "TestP is a synthetic promoter.\n\n## Origin\nbuilt for tests.\n",
    "regulated_by": ["LacI"],
}

STUB_TOOL = (
    "import json, pathlib\n"
    "root = pathlib.Path(__file__).resolve().parent.parent\n"
    "n = len(list((root/'parts'/'validated').glob('*.gb'))) "
    "+ len(list((root/'parts'/'candidate').glob('*.gb')))\n"
    "(root/'catalog.json').write_text(json.dumps({'schema_version': '1.0', 'n_parts': n}))\n"
    "print(f'catalog: {n} parts')\n"
)


def test_build_part_record_normalises_and_cites():
    rec = build_part_record(PROPOSAL, synonyms=["TP"])
    main = next(f for f in rec.features if "parent" not in f.qualifiers)
    kids = [f for f in rec.features if "parent" in f.qualifiers]
    assert main.qualifiers["label"] == ["TestP"]
    assert main.qualifiers["synonym"] == ["TP"]
    # description = report's first non-heading line
    assert main.qualifiers["note"] == ["TestP is a synthetic promoter."]
    # labels normalised (box/parenthetical stripped); regulatory_class stamped
    assert [f.qualifiers["label"][0] for f in kids] == ["-35", "-10"]
    assert kids[0].qualifiers["regulatory_class"] == ["minus_35_signal"]
    assert kids[1].qualifiers["regulatory_class"] == ["minus_10_signal"]
    # child note = first sentence only
    assert kids[0].qualifiers["note"] == ["Sigma70 -35 hexamer TTGACA."]
    # both refs kept; the uncited one (222) attaches to the main feature
    assert len(rec.annotations["references"]) == 2
    assert main.qualifiers.get("citation") and kids[0].qualifiers.get("citation")
    # Sequence Ontology /db_xref stamped on the part + each sub-feature
    assert main.qualifiers["db_xref"] == ["SO:0000167"]           # promoter
    assert kids[0].qualifiers["db_xref"] == ["SO:0000175"]        # -35
    assert kids[1].qualifiers["db_xref"] == ["SO:0000176"]        # -10
    # cognate regulator stamped for the catalog cross-link
    assert main.qualifiers.get("regulated_by") == ["LacI"]


def test_so_for_mapping():
    from so_terms import so_for
    assert so_for("promoter") == ("SO:0000167", "promoter")
    assert so_for("CDS") == ("SO:0000316", "CDS")
    assert so_for("RBS") == ("SO:0000139", "ribosome_entry_site")
    # regulatory_class is the most specific signal
    assert so_for("regulatory", "minus_10_signal") == ("SO:0000176", "minus_10_signal")
    # label refinements: operator, +1/TSS (genuine sub-elements)
    assert so_for("protein_bind", None, "lac operator O1")[0] == "SO:0000057"
    assert so_for("misc_feature", None, "+1 TSS")[0] == "SO:0000315"
    # an RBS is typed at the class level regardless of label — Shine_Dalgarno
    # (SO:0000552) is a sub-element, reached only via an explicit db_xref
    assert so_for("RBS", None, "Shine-Dalgarno") == ("SO:0000139", "ribosome_entry_site")
    assert so_for("totally_unknown_type") is None


def test_build_part_record_protein_canonical():
    """A protein sequence yields a protein record (LOCUS aa) with aa-coord
    children + the source accession; a DNA sequence stays a DNA record."""
    prop = {
        "part": "TestEnz", "feature_type": "CDS",
        "sequence": "MKVLATREDGSIPYNQWFCHKLMNDE",
        "source_accession": "UniProt:Q12345",
        "children": [{"label": "active site", "feature_type": "protein_domain",
                      "start": 2, "end": 8, "strand": 1, "citation_pmids": []}],
        "references": [], "report_markdown": "TestEnz is a test enzyme.\n",
    }
    rec = build_part_record(prop)
    assert rec.annotations["molecule_type"] == "protein"
    main = next(f for f in rec.features if "parent" not in f.qualifiers)
    assert main.qualifiers["db_xref"] == ["SO:0000316", "UniProt:Q12345"]
    kid = next(f for f in rec.features if "parent" in f.qualifiers)
    assert (int(kid.location.start), int(kid.location.end)) == (2, 8)
    # a DNA proposal is unaffected
    assert build_part_record({**prop, "sequence": "TTGACAGGGGGGTATAAT", "children": []}
                             ).annotations["molecule_type"] == "DNA"


def test_build_part_record_rejects_out_of_bounds():
    bad = {**PROPOSAL, "children": [
        {"label": "x", "feature_type": "misc_feature", "start": 0, "end": 999,
         "strand": 1, "citation_pmids": []}]}
    with pytest.raises(PublishError, match="out of bounds"):
        build_part_record(bad)


def test_publish_promotes_candidate_and_rebuilds(tmp_path):
    cat = tmp_path / "catalog"
    (cat / "parts" / "validated").mkdir(parents=True)
    (cat / "parts" / "candidate").mkdir(parents=True)
    (cat / "tools").mkdir()
    (cat / "tools" / "build_catalog.py").write_text(STUB_TOOL, encoding="utf-8")
    slug = _slugify("TestP")
    # seed a candidate (.gb only) with a synonym, to be promoted
    cand = build_part_record({**PROPOSAL, "report_markdown": ""},
                             name="TestP", synonyms=["TP_OLD"])
    SeqIO.write([cand], str(cat / "parts" / "candidate" / f"{slug}.gb"), "genbank")

    res = publish_part(PROPOSAL, cat)

    assert (cat / "parts" / "validated" / f"{slug}.gb").exists()
    assert (cat / "parts" / "validated" / f"{slug}.md").exists()
    assert not (cat / "parts" / "candidate" / f"{slug}.gb").exists()
    assert res["promoted_from_candidate"] and res["n_children"] == 2
    # synonyms carried over from the candidate
    main = next(f for f in SeqIO.read(str(cat / "parts" / "validated" / f"{slug}.gb"),
                                      "genbank").features if "parent" not in f.qualifiers)
    assert "TP_OLD" in main.qualifiers.get("synonym", [])
    # manifest rebuilt by the catalog's own generator
    assert json.loads((cat / "catalog.json").read_text())["n_parts"] == 1


def test_publish_requires_report(tmp_path):
    cat = tmp_path / "catalog"
    (cat / "parts" / "validated").mkdir(parents=True)
    with pytest.raises(PublishError, match="report_markdown"):
        publish_part({**PROPOSAL, "report_markdown": ""}, cat, rebuild=False)
