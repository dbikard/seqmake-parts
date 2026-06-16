# SeqMake Parts

> A machine-readable, provenance-tracked knowledge base of standard biological
> parts. Part of the **SeqMake** tooling family; IRIs live under
> [`w3id.org/seqmake/parts`](w3id/README.md). Not to be confused with JBEI's
> [BioParts](https://bioparts.org) search portal — see
> [`LANDSCAPE.md`](LANDSCAPE.md) for how the two differ.

> [!WARNING]
> **Work in progress — use at your own risk.** This is an experimental,
> **AI-generated** knowledge base under active development. Nothing here has been
> fully expert-reviewed and it may contain errors. What we offer instead of
> guarantees is transparency: every claim carries its source, confidence, and a
> review status — check those, and verify against the cited primary literature,
> before relying on anything.

A machine-readable, provenance-tracked **knowledge base of standard biological
parts** for molecular cloning and synthetic biology — promoters, CDSs,
terminators, RBSs, operators, origins, selection markers, regulators, and more.
Each part is an annotated record with **Sequence Ontology** typing, hierarchical
sub-features, literature references, and **prose-derived functional claims** that
carry their own source, confidence, and review status.

The data is published three ways from one canonical source: an **annotated
GenBank file**, the **`catalog.json`** manifest, and an **RDF graph**
(`catalog.ttl` / `catalog.jsonld`; SBOL3 + Sequence Ontology + SBO) that is
SPARQL-queryable and federates with UniProt. Protein parts **link out to UniProt**
rather than duplicating its annotation.

**Browse:** https://dbikard.github.io/seqmake-parts/ · **Query:** see
[`QUERIES.md`](QUERIES.md) and [`RDF.md`](RDF.md)

## What's here

Parts are split by curation status:

- **Validated** parts (`parts/validated/`) carry a curated `.md` documentation
  page.
- **Candidate** parts (`parts/candidate/`) are awaiting a curated documentation
  page.

Every part is browsable on the website: validated parts show their curated prose,
candidates get a lightweight auto-generated page (sequence viewer, sub-features,
and downloads).

```
parts/validated/<name>.json canonical part record (authored source of truth)
parts/validated/<name>.gb   annotated GenBank part, generated from the .json
parts/validated/<name>.md   curated documentation page (origin / properties / use)
parts/candidate/<name>.json canonical record for a part awaiting a documentation page
parts/candidate/<name>.gb   generated GenBank part awaiting a documentation page
catalog.json                machine-readable manifest (every part + its metadata)
catalog.ttl / .jsonld       RDF projection of the catalog (SBOL3 + Sequence Ontology + SBO)
schema/part.schema.json     JSON Schema for a canonical part record
tools/build_gb.py           regenerates the .gb files from the canonical .json
tools/build_catalog.py      regenerates catalog.json + the website pages
tools/build_rdf.py          regenerates catalog.ttl + catalog.jsonld
docs/                       generated website source (mkdocs Material)
```

## Using the catalog

- **Browse / cite** individual parts on the website above, or download a part's
  `.gb` / FASTA from its page.
- **Programmatic access:** read `catalog.json` — the manifest of every part with
  its metadata and the **functional-knowledge layer** (claims with source,
  confidence, and review status) — or parse the `.gb` files with any GenBank
  reader (e.g. BioPython).
- **Semantic / SPARQL access:** load `catalog.ttl` (or `catalog.jsonld`) into any
  RDF store — each part is an `sbol:Component` with its Sequence Ontology role,
  sequence, sub-features, citations, collections, and promoter↔TF regulation as
  SBOL3 `Interaction`s, plus prose-derived **functional claims** (inducer,
  dynamic range, …) carried as nanopublication-shaped assertions with their
  source quote/figure, confidence, and review status. See [`RDF.md`](RDF.md) for
  the model and [`QUERIES.md`](QUERIES.md) for a SPARQL cookbook (incl. UniProt
  federation).
- This catalog is a standalone, reusable dataset with no external dependencies.

## How this fits the ecosystem

This is a curated, machine-readable **knowledge base** — not a registry platform,
search portal, or physical repository. For how it relates to ICE/BioParts,
SynBioHub, the iGEM Registry, and Addgene, and where it deliberately differs, see
the strategic review in [`LANDSCAPE.md`](LANDSCAPE.md).

## Contributing

New parts and documentation pages are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md). Each part's canonical record is a
`<slug>.json` (validated against [`schema/part.schema.json`](schema/part.schema.json));
the `.gb` is generated from it. Adding a `.md` page promotes a candidate to a
validated part. CI validates the JSON, regenerates the `.gb`, and rebuilds the
manifest + RDF.

## License

Catalog data and documentation are licensed **CC BY 4.0** (see [`LICENSE`](LICENSE)).
You may share and adapt the material with attribution.
