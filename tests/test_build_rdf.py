"""The RDF projection: structural SBOL3/SO/SBO graph generated from the parts."""
import sys
from pathlib import Path

import rdflib
from pyshacl import validate

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

from build_rdf import build_graph, load_graph  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SBOL = rdflib.Namespace("http://sbols.org/v3#")
CAT = rdflib.Namespace("https://dbikard.github.io/dna-parts-catalog/ns#")
PART = rdflib.Namespace("https://dbikard.github.io/dna-parts-catalog/part/")


def test_graph_builds_and_is_nonempty():
    g, parts = load_graph()
    assert len(parts) > 0
    assert len(g) > 0
    # Every part is a Component with a role and a sequence.
    comps = set(g.subjects(rdflib.RDF.type, SBOL.Component))
    assert len(comps) == len(parts)
    for c in comps:
        assert (c, SBOL.role, None) in g
        assert (c, SBOL.hasSequence, None) in g


def test_conforms_to_shacl_shapes():
    g, _ = load_graph()
    sg = rdflib.Graph().parse(str(ROOT / "tools" / "shapes.ttl"), format="turtle")
    conforms, _, text = validate(g, shacl_graph=sg, inference="rdfs")
    assert conforms, text


def test_regulation_is_modeled_both_ways():
    g, _ = load_graph()
    # Denormalized shortcut.
    assert (PART.PphlF, CAT.regulatedBy, PART.PhlF) in g
    # Full SBOL3 Interaction: PphlF has an inhibition interaction naming PhlF.
    q = """
    PREFIX sbol: <http://sbols.org/v3#>
    PREFIX sbo: <https://identifiers.org/SBO:>
    PREFIX part: <https://dbikard.github.io/dna-parts-catalog/part/>
    ASK {
      part:PphlF sbol:hasInteraction ?i .
      ?i sbol:type sbo:0000169 ;
         sbol:hasParticipation ?p .
      ?p sbol:participant ?sub .
      ?sub sbol:instanceOf part:PhlF .
    }
    """
    assert bool(g.query(q))


def test_functional_claims_are_projected_with_provenance():
    g, _ = load_graph()
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    # PphlF's DAPG inducer claim, with its source + confidence + review status.
    claim = PART["PphlF_claim_inducer"]
    assert (PART.PphlF, CAT.hasFunctionalClaim, claim) in g
    assert (claim, CAT.claimType, rdflib.Literal("inducer")) in g
    assert (claim, CAT.confidence, rdflib.Literal("high")) in g
    assert (claim, CAT.reviewStatus, rdflib.Literal("ai-cross-checked")) in g
    src = rdflib.URIRef("https://identifiers.org/pubmed:24316737")
    assert (claim, PROV.wasDerivedFrom, src) in g
    # granular source: a verbatim quote travels with the citation
    assert any(g.objects(claim, CAT.sourceQuote)), "claim should carry a source quote"
    # the dynamic-range claim exposes a typed numeric fold-change
    fold = PART["PphlF_claim_repression_dynamic_range"]
    assert (fold, CAT.foldChange, rdflib.Literal(80, datatype=rdflib.XSD.decimal)) in g


def test_serialization_is_deterministic():
    g1, _ = load_graph()
    g2, _ = load_graph()
    assert g1.serialize(format="turtle") == g2.serialize(format="turtle")


def test_committed_rdf_is_up_to_date():
    """catalog.ttl on disk matches a fresh build (the CI staleness guard)."""
    g, _ = load_graph()
    on_disk = (ROOT / "catalog.ttl").read_text(encoding="utf-8")
    assert g.serialize(format="turtle") == on_disk
