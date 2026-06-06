# DNA Parts Catalog

An open, community-curated catalog of **standard DNA parts** for molecular
cloning and synthetic biology — promoters, CDSs, terminators, ribosome binding
sites, operators, and more — each stored as an **annotated GenBank file** with
hierarchical sub-features (e.g. a promoter's −35 / −10 / operator) and literature
references.

A growing subset of parts also carries a **curated documentation page**
(`<part>.md`) describing its origin, properties, and use, with references.

**Browse the catalog:** https://dbikard.github.io/dna-parts-catalog/

## What's here

```
parts/<name>.gb     annotated GenBank part (one main feature + sub-features)
parts/<name>.md     optional curated documentation page (origin / properties / use)
catalog.json        machine-readable manifest (every part + its metadata)
tools/build_catalog.py   regenerates catalog.json + the website pages
docs/               generated website source (mkdocs Material)
```

## Using the catalog

- **Browse / cite** individual parts on the website above, or download a part's
  `.gb` / FASTA from its page.
- **Programmatic access:** read `catalog.json` (schema in
  [`CONTRIBUTING.md`](CONTRIBUTING.md)) or parse the `.gb` files with any GenBank
  reader (e.g. BioPython).
- This catalog is a standalone, reusable dataset with no external dependencies.

## Contributing

New parts and documentation pages are welcome — see
[`CONTRIBUTING.md`](CONTRIBUTING.md). Adding a part is a single `.gb` file (plus
an optional `.md`); CI validates it and rebuilds the manifest.

## License

Catalog data and documentation are licensed **CC BY 4.0** (see [`LICENSE`](LICENSE)).
You may share and adapt the material with attribution.
