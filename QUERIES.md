# Querying the catalog (SPARQL cookbook)

The catalog ships an RDF graph — [`catalog.ttl`](catalog.ttl) (Turtle) and
[`catalog.jsonld`](catalog.jsonld) (JSON-LD), also published next to the
[website](https://dbikard.github.io/dna-parts-catalog/). Load it into any triple
store, or locally:

```python
import rdflib
g = rdflib.Graph().parse("catalog.ttl", format="turtle")
```

All queries below are tested against the published graph (`tests/test_queries.py`).
Common prefixes:

```sparql
PREFIX sbol: <http://sbols.org/v3#>
PREFIX so:   <https://identifiers.org/SO:>
PREFIX sbo:  <https://identifiers.org/SBO:>
PREFIX cat:  <https://w3id.org/bioparts/ns#>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```

## Promoters and the transcription factors that regulate them
```sparql
SELECT ?promoter ?tf WHERE { ?promoter cat:regulatedBy ?tf . }
```
The full SBOL3 form (with inhibition/activation polarity) is via
`sbol:hasInteraction` → `sbol:Interaction` (`sbol:type` SBO:0000169 inhibition /
SBO:0000170 stimulation).

## Find every IPTG-inducible promoter
```sparql
SELECT ?part WHERE {
  ?part cat:hasFunctionalClaim ?c .
  ?c cat:inducer ?inducer .
  FILTER(CONTAINS(?inducer, "IPTG"))
}
```
…or group the whole catalog by inducer:
```sparql
SELECT ?inducer (COUNT(?part) AS ?n) WHERE {
  ?part cat:hasFunctionalClaim ?c . ?c cat:inducer ?inducer .
} GROUP BY ?inducer ORDER BY DESC(?n)
```

## Selection markers and what they confer
```sparql
SELECT ?part ?statement WHERE {
  ?part cat:hasFunctionalClaim ?c .
  ?c cat:claimType "function" ; rdfs:label ?statement .
}
```

## Functional claims with their evidence and trust
```sparql
SELECT ?part ?statement ?confidence ?review ?source WHERE {
  ?part cat:hasFunctionalClaim ?c .
  ?c rdfs:label ?statement ; cat:confidence ?confidence ;
     cat:reviewStatus ?review ; prov:wasDerivedFrom ?source .
}
```

## A part's annotated sub-features (with Sequence Ontology roles)
```sparql
SELECT ?label ?role WHERE {
  <https://w3id.org/bioparts/part/PphlF> sbol:hasFeature ?f .
  ?f dcterms:title ?label ; sbol:role ?role .
}
```

## Members of each collection
```sparql
SELECT ?collection ?member WHERE {
  ?collection a sbol:Collection ; sbol:member ?member .
}
```

## Protein parts and their UniProt entries
```sparql
SELECT ?part ?uniprot WHERE {
  ?part a sbol:Component ; rdfs:seeAlso ?uniprot .
  FILTER(STRSTARTS(STR(?uniprot), "http://purl.uniprot.org/uniprot/"))
}
```

## Federate with UniProt (illustrative — needs network)
Because protein parts link out with `rdfs:seeAlso` to UniProt's own entity IRIs
(`purl.uniprot.org`), you can join the catalog to UniProt's SPARQL endpoint to
pull authoritative protein facts you deliberately *don't* duplicate here:

```sparql
PREFIX up: <http://purl.uniprot.org/core/>
SELECT ?part ?proteinName WHERE {
  ?part rdfs:seeAlso ?uniprot .
  FILTER(STRSTARTS(STR(?uniprot), "http://purl.uniprot.org/uniprot/"))
  SERVICE <https://sparql.uniprot.org/sparql> {
    ?uniprot up:recommendedName ?n . ?n up:fullName ?proteinName .
  }
}
```
