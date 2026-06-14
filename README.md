# DNA Parts Catalog

> [!WARNING]
> **Work in progress — largely AI-generated content.** This catalog is under
> active development and much of its content (part annotations and
> documentation pages) is **largely AI-generated**. It may contain errors and
> has not been fully expert-reviewed — verify any part against the cited
> primary literature before relying on it.

An open, community-curated catalog of **standard DNA parts** for molecular
cloning and synthetic biology — promoters, CDSs, terminators, ribosome binding
sites, operators, and more — each stored as an **annotated GenBank file** with
hierarchical sub-features (e.g. a promoter's −35 / −10 / operator) and literature
references.

A growing subset of parts also carries a **curated documentation page**
(`<part>.md`) describing its origin, properties, and use, with references.

**Browse the catalog:** https://dbikard.github.io/dna-parts-catalog/

## What's here

Parts are split by curation status:

- **Validated** parts (`parts/validated/`) carry a curated `.md` documentation
  page and are published to the website.
- **Candidate** parts (`parts/candidate/`) are annotated GenBank files awaiting
  a documentation page — present in the repo and `catalog.json`, but not yet on
  the site.

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
- **Programmatic access:** read `catalog.json` (schema in
  [`CONTRIBUTING.md`](CONTRIBUTING.md)) or parse the `.gb` files with any GenBank
  reader (e.g. BioPython).
- **Semantic / SPARQL access:** load `catalog.ttl` (or `catalog.jsonld`) into any
  RDF store — each part is an `sbol:Component` with its Sequence Ontology role,
  sequence, sub-features, citations, collections, and promoter↔TF regulation as
  SBOL3 `Interaction`s, plus prose-derived **functional claims** (inducer,
  dynamic range, …) carried as nanopublication-shaped assertions with their
  source quote/figure, confidence, and review status. See [`RDF.md`](RDF.md).
- This catalog is a standalone, reusable dataset with no external dependencies.

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
