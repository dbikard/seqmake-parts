# Contributing a part

Thank you for helping grow the catalog! Adding a part is intentionally
low-friction: one GenBank file, plus a documentation page once it's validated.

Parts are split by curation status:

- **Candidate** (`parts/candidate/`) — annotated GenBank only, no documentation
  page yet. Not published to the website.
- **Validated** (`parts/validated/`) — carries a curated `.md` page and is
  published to the website.

## Add a part

1. Add `parts/candidate/<Name>.gb` — an annotated GenBank file with:
   - exactly **one main feature** spanning the whole sequence, carrying
     `/label="<Name>"` (this is the part's canonical name) and no `/parent`;
   - optional **sub-features**, each with `/parent="<Name>"` and a `/label`
     (e.g. a promoter's `-35`, `-10`, operator), in part-relative coordinates;
   - optional `REFERENCE` blocks with `PUBMED` / `doi:` and per-feature
     `/citation=[N]` linking a feature to reference *N*.
2. To **promote a part to validated**, move its `.gb` to `parts/validated/` and
   add a sibling `parts/validated/<Name>.md` documentation page (recommended
   sections: **Origin**, **Properties**, **Use**, **References**). Validated
   parts are marked `documented` (`status: "validated"`) and get a website page.
   A `.gb` in `parts/validated/` **must** have a `.md`, and a `.gb` in
   `parts/candidate/` **must not** — the build flags misplaced files.
3. Open a pull request. CI loads every `.gb` and rebuilds `catalog.json`; your
   PR must keep `catalog.json` up to date.

## Part conventions

- **Atomic — one functional class per part.** A part should be a single
  functional unit. A promoter and a ribosome binding site are *different* parts
  (different Sequence Ontology types) — don't bundle them into one "promoter"
  that includes an RBS; make two parts that compose. Likewise promoter + terminator,
  CDS + terminator, etc.
- **Sequence Ontology typing.** Each part + sub-feature is typed with a
  [Sequence Ontology](https://www.ebi.ac.uk/ols4/ontologies/so) accession in
  `catalog.json` (`so_term`). It is derived from the GenBank feature type /
  `regulatory_class` by `tools/build_catalog.py`; you may also stamp it
  explicitly as a `/db_xref="SO:0000167"` qualifier (an explicit value wins).
  Common terms: promoter `SO:0000167`, ribosome_entry_site `SO:0000139`,
  terminator `SO:0000141`, CDS `SO:0000316`, operator `SO:0000057`,
  origin_of_replication `SO:0000296`, `-35` `SO:0000175`, `-10` `SO:0000176`.

## Regenerate locally

```bash
pip install -r requirements.txt
python tools/build_catalog.py     # rebuilds catalog.json + docs/
mkdocs serve                      # preview the site at http://127.0.0.1:8000
```

Commit the updated `catalog.json` along with your part. The `docs/` tree is
generated (git-ignored) and rebuilt by CI.

## `catalog.json` schema (v1.0)

```jsonc
{
  "schema_version": "1.0",
  "n_parts": 211,
  "n_validated": 16,
  "n_candidate": 195,
  "n_documented": 16,
  "parts": [
    {
      "name": "PphlF", "slug": "PphlF",
      "feature_type": "promoter", "so_term": "SO:0000167", "so_name": "promoter",
      "synonyms": ["PhlF promoter"],
      "description": "…", "length": 51,
      "documented": true, "status": "validated",
      "children": [
        {"label": "-35", "feature_type": "regulatory",
         "so_term": "SO:0000175", "so_name": "minus_35_signal",
         "start": 16, "end": 22, "strand": 1, "citations": [1]}
      ],
      "references": [
        {"authors": "…", "title": "…", "journal": "…",
         "pmid": "24316737", "doi": "10.1038/…", "url": "https://pubmed…/"}
      ],
      "main_citations": [1, 2]
    }
  ]
}
```

`start`/`end` are 0-based, end-exclusive, part-relative. `citations` /
`main_citations` are 1-based indices into that part's `references`.

## Scope & licensing

Keep parts **lab-agnostic** and generally useful. By contributing you agree to
release your contribution under **CC BY 4.0** (the catalog's license). Only
contribute sequences/annotations you have the right to share.
