# Authoring a part

How a part is created and validated in this repo. This is the agent-facing
standard operating procedure behind the `/add-part` command; humans can follow it
directly too. It complements [`CONTRIBUTING.md`](CONTRIBUTING.md) (conventions)
and [`schema/part.schema.json`](schema/part.schema.json) (the record format).

## The model

The catalog is **agent-authored over a deterministic, validated core**. You (the
agent) supply judgement — the sequence's source, the annotation, the prose, the
functional claims — and the repo's tools deterministically generate and check the
rest. Author content; never hand-edit generated files.

- **Canonical, authored:** `parts/<status>/<slug>.json` (structure + references +
  `functional_claims`) and, for a validated part, `parts/validated/<slug>.md`
  (prose). Prose lives in Markdown, *not* in the JSON.
- **Generated, never edited:** `<slug>.gb` (from the JSON), `catalog.json`,
  `catalog.ttl`, `catalog.jsonld`, and the `docs/` site.

A part is a **candidate** until it earns a curated `.md`, at which point it moves
to `parts/validated/` and is **validated**. Independently, every
`functional_claim` carries a `review_status` (`ai-generated` →
`ai-cross-checked` → `expert-reviewed`) so the knowledge base can self-correct.

## Hard rules

- **Sequence from a cited source — never from memory.** Take the sequence from a
  primary paper or a registry (Addgene, iGEM, SEVA, UniProt/NCBI) and record
  where, in `provenance.sequence_source`. A part without a sourced sequence is not
  acceptable.
- **One functional class per part** (atomic). A promoter and an RBS are two
  parts, not one. See `CONTRIBUTING.md` → *Part conventions*.
- **Coding parts are protein-canonical.** A `CDS` / `protein_domain` is stored as
  its amino-acid sequence (begins with `M`), residue-coordinate sub-features, and
  a `db_xref` provenance accession (`UniProt:…` preferred).
- **Lab- and tool-agnostic prose.** Describe what the part *is*; never name a
  consuming tool, a using lab, or an internal plasmid. `tools/check_content.py`
  enforces this.
- **Sequence Ontology typing.** Type the part and each sub-feature at the
  functional-class level (promoter `SO:0000167`, RBS `SO:0000139`, CDS
  `SO:0000316`, …); `tools/new_part.py` stamps the main feature's `db_xref`.
- **Claims cite their evidence.** Each `functional_claim` carries a `source`
  (PMID/DOI) and, where possible, a verbatim `quote` and a `figure`/`table`/`page`
  locator — prefer a quote from the **primary** source (`quote_source: primary`);
  if you only transcribe the catalog's own prose, mark `quote_source:
  catalog-doc`. Never invent a figure number you have not read.

## Procedure

1. **Check it isn't already there.** Search `catalog.json` and `parts/` for the
   name and its synonyms; if it exists, improve that record instead.
2. **Source the sequence + literature.** Find the sequence in a citable source;
   collect the key references (PMID/DOI).
3. **Scaffold the record:**
   ```bash
   python tools/new_part.py --name "<Name>" --type <promoter|CDS|...> \
       --sequence <seq>  [--synonym X ...] [--note "<one-line>"] \
       [--source-accession UniProt:Pxxxxx] [--regulated-by <TF>] \
       [--collection <id>]
   ```
   This writes `parts/candidate/<slug>.json` with the main feature + SO `db_xref`.
4. **Annotate sub-features.** Add child features to `features[]` (each with
   `qualifiers.parent = ["<Name>"]`, part-relative `start`/`end` (0-based,
   end-exclusive), a `label`, a `db_xref` SO term, and `citation` like `["[1]"]`).
   Add the matching `references[]` entries (DOI rides in `comment` as `doi:<id>`).
5. **Set provenance.** Replace `provenance.sequence_source` with the real source.
6. **Add functional knowledge.** For any inducer / dynamic range / strength /
   host range claim, append a `functional_claims[]` entry with `type`, `label`,
   `value`, `source` (+ `quote`/`figure`), `confidence`, and `review_status`.
7. **Validate it (candidate).** Run the gates:
   ```bash
   python tools/validate_parts.py      # JSON vs schema
   python tools/build_gb.py            # JSON -> .gb
   python tools/build_catalog.py       # catalog.json + site
   python tools/build_rdf.py           # catalog.ttl + .jsonld
   python tools/check_content.py       # agnostic-prose guard
   pyshacl -s tools/shapes.ttl -i rdfs catalog.ttl
   python -m pytest tests/ -q
   ```
8. **Promote to validated (optional, when curating prose).** Move the `.json` to
   `parts/validated/` and write `parts/validated/<slug>.md` (sections: Origin,
   Properties, Use, References). Re-run step 7.
9. **Commit + open a PR** with the `<slug>.json`, the generated `.gb`,
   `catalog.json`, and `catalog.ttl`/`.jsonld`. An expert review promotes claims
   to `review_status: expert-reviewed`.

## Minimal record shape

```jsonc
{
  "schema_version": "1.0",
  "slug": "Pxyz", "locus": "Pxyz", "id": "Pxyz",
  "description": "one-line summary",
  "molecule_type": "DNA",
  "locus_annotations": { "topology": "linear" },
  "sequence": "tctgatt...",
  "references": [
    { "authors": "Doe J", "title": "...", "journal": "J 2020", "pubmed_id": "12345",
      "comment": "doi:10.x/y" }
  ],
  "features": [
    { "type": "promoter", "start": 0, "end": 51, "strand": 1,
      "qualifiers": { "label": ["Pxyz"], "db_xref": ["SO:0000167"],
                      "regulated_by": ["SomeTF"], "citation": ["[1]"] } },
    { "type": "regulatory", "start": 16, "end": 22, "strand": 1,
      "qualifiers": { "label": ["-35"], "parent": ["Pxyz"],
                      "regulatory_class": ["minus_35_signal"],
                      "db_xref": ["SO:0000175"], "citation": ["[1]"] } }
  ],
  "review_status": "ai-generated",
  "provenance": { "sequence_source": "Doe 2020, Fig 1 (PMID 12345)" },
  "functional_claims": [
    { "id": "inducer", "type": "inducer",
      "label": "Induced by X.", "value": { "inducer": "X", "mode": "..." },
      "ontology": { "inducer_chebi": null },
      "source": { "pmid": "12345", "quote": "...", "quote_source": "primary", "figure": "Fig 2" },
      "provenance": { "method": "ai-extraction", "from": "primary", "agent": "ai-assistant" },
      "confidence": "medium", "review_status": "ai-generated", "supersedes": null }
  ]
}
```
