# Contributing a part

Thank you for helping grow the catalog! The canonical record of each part is a
schema-validated `<slug>.json`; the `.gb` is generated from it and prose lives in
a sibling `<slug>.md`.

To add a part with an agent, use the **`/add-part`** command (Claude Code), which
follows the standard operating procedure in [`AUTHORING.md`](AUTHORING.md) —
research a cited sequence, annotate, write claims with provenance, then validate
and build. To do it by hand, follow that same SOP; `tools/new_part.py` scaffolds
a valid skeleton.

Parts are split by curation status:

- **Candidate** (`parts/candidate/`) — no curated documentation page yet.
  Published to the website as a lightweight auto-generated page (sequence viewer,
  sub-features, downloads).
- **Validated** (`parts/validated/`) — carries a curated `.md` page, shown on its
  website page above the structured sections.

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
- **Coding parts are protein-canonical and defer biology to UniProt.** A `CDS` /
  `protein_domain` part is stored as a **protein** GenBank record (`LOCUS … aa`):
  the amino-acid sequence is the part, no DNA is stored — a gene is just one codon
  realization, and parts are matched/identified at the protein level. The
  N-terminus is the initiator methionine: in bacteria an alternative start codon
  (GTG/TTG) is still translated as fMet, so a coding part begins with **M** —
  never store the start codon's literal amino acid (a `V`/`L` start) or record it
  as a variant. A protein part **must** record a `/db_xref="UniProt:Pxxxxx"`
  (preferred) or `NCBI:…` accession on the main feature, and its residue-level
  features (domains, active sites, binding residues, PTMs) are **imported from
  UniProt**, not hand-authored: run `python tools/import_uniprot_features.py
  <slug>` to cache a provenance-tagged `uniprot_features` projection that is baked
  into the generated `.gb` (and emits `rdfs:seeAlso` to UniProt). Hand-author only
  the engineering layer (role, functional_claims, cognate partners, collections).
  For a non-exact sequence the importer keeps an intentional variant
  (`variant_rationale`), else re-points to a different accession whose sequence is
  an **exact** match (via UniParc), else normalizes a close variant to the
  assigned accession's canonical sequence, else flags a wrong accession. Regulatory DNA parts (promoter / terminator /
  operator / RBS / origin) keep their hand-authored sub-features.
- **Cross-links.** A promoter names its cognate transcription-factor part(s) with
  a `/regulated_by="<TF name>"` qualifier (repeatable) on its main feature. The
  build resolves each name to that part and derives the inverse on the TF's page
  ("regulates"), so the link is authored once but shown both ways (and lands in
  `catalog.json`). Use a name (or synonym) that already exists in the catalog.
- **Collections.** Related parts that belong to a family — a vector series, a
  promoter set, an inducible-sensor kit — declare membership on their main
  feature with a `/collection="<id>"` qualifier (repeatable; a part may join
  several). The build groups parts by that id into a dedicated **collection
  page** (members validated or candidate alike) and a "Browse by collection" hub.
  Give the collection display prose — `name`, `description`, `source` — in the
  top-level `collections.json`, keyed by the same `<id>`; membership itself
  always lives on the parts, never in that file. A collection entry may also
  carry **`references`** (a list of papers — each `{title, authors?, journal?,
  year?, pmid?, doi?, url?}`; the title links to its `url`, else PubMed/DOI) and
  **`resources`** (a list of external links — each `{title, url}`, e.g. a
  registry catalog page or a kit page). Both render as `## References` /
  `## Resources` sections at the foot of the collection page and land in
  `catalog.json`. Example: each Anderson promoter carries
  `/collection="anderson-promoters"`, and the collection cites the Kelly et al.
  2009 RPU paper plus the iGEM Registry catalog page.
- **Sequence Ontology typing.** Each part + sub-feature is typed with a
  [Sequence Ontology](https://www.ebi.ac.uk/ols4/ontologies/so) accession in
  `catalog.json` (`so_term`). It is derived from the GenBank feature type /
  `regulatory_class` by `tools/build_catalog.py`; you may also stamp it
  explicitly as a `/db_xref="SO:0000167"` qualifier (an explicit value wins).
  Common terms: promoter `SO:0000167`, ribosome_entry_site `SO:0000139`,
  terminator `SO:0000141`, CDS `SO:0000316`, operator `SO:0000057`,
  origin_of_replication `SO:0000296`, `-35` `SO:0000175`, `-10` `SO:0000176`.
  Type at the **functional-class level** for consistency — e.g. an RBS is
  `ribosome_entry_site` `SO:0000139` (just as a promoter is `SO:0000167`, not the
  more specific `bacterial_RNApol_promoter`). A finer sub-element term such as
  `Shine_Dalgarno_sequence` `SO:0000552` is used only as an explicit `/db_xref`
  on a dedicated sub-feature, never inferred from a part's label. The website's
  index groups validated parts **by their main feature's `so_term`**, so accurate
  typing also determines which section a part appears under on the catalog site.

## Regenerate locally

```bash
pip install -r requirements.txt
python tools/migrate_to_json.py   # (if you authored a .gb) -> canonical <slug>.json
python tools/build_gb.py          # regenerate every .gb from its canonical JSON
python tools/build_catalog.py     # rebuilds catalog.json + docs/
python tools/build_rdf.py         # rebuilds catalog.ttl + catalog.jsonld
mkdocs serve                      # preview the site at http://127.0.0.1:8000
```

**The canonical record of each part is `parts/<status>/<slug>.json`** (validated
against [`schema/part.schema.json`](schema/part.schema.json)); the `.gb` is a
*generated* projection of it (`tools/build_gb.py`), and `catalog.json` /
`catalog.ttl` / `catalog.jsonld` are generated in turn. You may author a part as
JSON directly, or add a `.gb` and run `tools/migrate_to_json.py` to derive the
JSON. Prose stays in the sibling `<slug>.md`. Commit the `<slug>.json`, the
generated `.gb`, `catalog.json`, and `catalog.ttl` / `catalog.jsonld` together —
CI fails if any is stale (and validates the JSON + the RDF SHACL shapes). Never
hand-edit the generated files; see [`RDF.md`](RDF.md) for the model. The `docs/`
tree is generated (git-ignored) and rebuilt by CI.

## Interactive part viewer

Each validated part page embeds an interactive feature/sequence view. It is a
self-contained, iframe-isolated widget at
[`docs/assets/seqmake-part-view.js`](docs/assets/seqmake-part-view.js) — a
**vendored build** of the upstream viewer widget, not hand-edited. `build_catalog.py`
inlines each part's `MoleculeInfo` (sequence + features) into the page as a
`<script type="application/json">` child of a `<div data-part-view>`, which the
widget hydrates on load. To refresh the widget, rebuild it from the viewer
source (`npm run build:widget`) and copy the resulting bundle over the vendored
file. (When the viewer ships as an npm package this becomes a CDN/package
reference instead of a vendored file.)

## Content guard

Part content is **lab-agnostic and tool-agnostic** — it describes what a part
*is*. `tools/check_content.py` enforces this over every `parts/**/*.md` and
`*.gb`, and it must pass before a push (it runs in CI and as a `pre-push` hook).
A part file must not:

- name a consuming tool;
- reference a specific *using* lab, person, or internal/unpublished plasmid
  lineage (naming the *originating* lab of a part — e.g. "the Bujard-lab pZ
  system" — is fine, like citing an author);
- define the part by negation/comparison ("this is not the …"). State what it
  *is*. (Legitimate scientific negation — "RNA-based control, no protein
  operator" — is fine.)

Enable the local push guard once per clone:

```bash
git config core.hooksPath scripts/hooks   # runs tools/check_content.py on push
```

## `catalog.json` schema (v1.0)

```jsonc
{
  "schema_version": "1.0",
  "n_parts": 228,
  "n_validated": 32,
  "n_candidate": 196,
  "n_documented": 32,
  "parts": [
    {
      "name": "PphlF", "slug": "PphlF",
      "feature_type": "promoter", "so_term": "SO:0000167", "so_name": "promoter",
      "synonyms": ["PhlF promoter"], "collections": [],
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
  ],
  "collections": [
    {"id": "anderson-promoters", "name": "Anderson promoters",
     "source": "iGEM Registry (Anderson promoter collection)",
     "references": [
       {"title": "…", "authors": "…", "journal": "…", "year": 2009,
        "pmid": "19298678", "doi": "10.1186/1754-1611-3-4"}],
     "resources": [
       {"title": "iGEM Registry — Anderson promoter collection",
        "url": "http://parts.igem.org/Promoters/Catalog/Anderson"}],
     "n_parts": 13, "n_validated": 0,
     "members": ["J23100", "J23101", "…"]}
  ]
}
```

`start`/`end` are 0-based, end-exclusive, part-relative. `citations` /
`main_citations` are 1-based indices into that part's `references`. A part's
`collections` lists the family ids it declares via `/collection`; the top-level
`collections` block resolves each id (prose from `collections.json`) to its
members.

## Scope & licensing

Keep parts **lab-agnostic** and generally useful. By contributing you agree to
release your contribution under **CC BY 4.0** (the catalog's license). Only
contribute sequences/annotations you have the right to share.
