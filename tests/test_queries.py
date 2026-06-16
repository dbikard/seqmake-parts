"""The SPARQL cookbook (QUERIES.md) keeps working against the generated graph."""
from pathlib import Path

import pytest

rdflib = pytest.importorskip("rdflib")

ROOT = Path(__file__).resolve().parent.parent
TTL = ROOT / "catalog.ttl"

PREFIXES = """
PREFIX sbol: <http://sbols.org/v3#>
PREFIX cat:  <https://w3id.org/bioparts/ns#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
"""


@pytest.fixture(scope="module")
def g():
    graph = rdflib.Graph()
    graph.parse(str(TTL), format="turtle")
    return graph


def _slugs(rows):
    return {str(r[0]).rsplit("/", 1)[-1] for r in rows}


def test_promoter_regulator_links(g):
    rows = list(g.query(PREFIXES + "SELECT ?p ?tf WHERE { ?p cat:regulatedBy ?tf }"))
    assert len(rows) > 0


def test_iptg_inducible_promoters(g):
    rows = list(g.query(PREFIXES + """
        SELECT ?part WHERE { ?part cat:hasFunctionalClaim ?c .
            ?c cat:inducer ?i . FILTER(CONTAINS(?i, "IPTG")) }"""))
    slugs = _slugs(rows)
    assert {"Plac", "Ptac"} <= slugs       # known IPTG-inducible promoters


def test_selection_marker_statements(g):
    rows = list(g.query(PREFIXES + """
        SELECT ?p ?l WHERE { ?p cat:hasFunctionalClaim ?c .
            ?c cat:claimType "function" ; rdfs:label ?l }"""))
    assert len(rows) >= 10


def test_claims_carry_source_and_confidence(g):
    rows = list(g.query(PREFIXES + """
        SELECT ?p WHERE { ?p cat:hasFunctionalClaim ?c .
            ?c cat:confidence ?conf ; prov:wasDerivedFrom ?src }"""))
    assert len(rows) > 0


def test_part_subfeatures(g):
    rows = list(g.query(PREFIXES + """
        SELECT ?f ?role WHERE {
          <https://w3id.org/bioparts/part/PphlF> sbol:hasFeature ?f .
          ?f sbol:role ?role }"""))
    assert len(rows) >= 3                    # -35, -10, operator


def test_protein_parts_link_uniprot(g):
    rows = list(g.query(PREFIXES + """
        SELECT ?p ?u WHERE { ?p a sbol:Component ; rdfs:seeAlso ?u .
            FILTER(STRSTARTS(STR(?u), "http://purl.uniprot.org/uniprot/")) }"""))
    assert len(rows) > 0
