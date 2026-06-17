# Contributing a part

Thank you for helping grow the catalog! The canonical record of each part is a
schema-validated `parts/<status>/<slug>.json`; the `.gb` is *generated* from it
(`tools/build_gb.py`) and prose lives in a sibling `<slug>.md`.

> **The rules for what a part is — how it is sourced, typed, annotated, validated,
> and promoted — live in one place: [`AUTHORING.md`](AUTHORING.md)**, the single
> source of truth, written for the `/add-part` agent and human authors alike. This
> page covers only the *mechanics* of contributing; when in doubt, AUTHORING.md
> wins.

## Two ways to add a part

- **With an agent** — run the **`/add-part`** command (Claude Code). It executes
  the [`AUTHORING.md`](AUTHORING.md) procedure end to end: source a cited sequence,
  annotate sub-features, write functional claims with provenance, then validate and
  build.
- **By hand** — follow that same procedure. `tools/new_part.py` scaffolds a
  schema-valid `<slug>.json` skeleton (main feature + SO `db_xref`) to start from;
  edit the JSON, never the generated `.gb`.

Parts are split by **curation tier**: a **candidate** (`parts/candidate/`) is a
bare sourced sequence; a **validated** part (`parts/validated/`) clears the
completeness bar *and* carries a curated `<slug>.md`. The exact bar, the tiers, and
the separate `review_status` axis (`ai-generated → ai-cross-checked →
expert-reviewed`) are defined in [`AUTHORING.md`](AUTHORING.md);
`tools/validate_parts.py` enforces the machine-checkable part of it. A `.gb` in
`parts/validated/` **must** have a `.md`; one in `parts/candidate/` **must not** —
the build flags misplaced files.

## Open a pull request

Commit the `<slug>.json`, its generated `.gb`, the curated `<slug>.md` (for a
validated part), and the regenerated `catalog.json` + `catalog.ttl` / `.jsonld`
together. CI validates the JSON against the schema, regenerates the `.gb` / catalog
/ RDF and fails if any committed artifact is stale, checks the SHACL shapes, and
runs the content + requests guards. An expert review promotes claims to
`review_status: expert-reviewed`.

## Regenerate locally

```bash
pip install -r requirements.txt
python tools/build_gb.py          # regenerate every .gb from its canonical JSON
python tools/build_catalog.py     # rebuild catalog.json + docs/
python tools/build_rdf.py         # rebuild catalog.ttl + catalog.jsonld
mkdocs serve                      # preview the site at http://127.0.0.1:8000
```

**The canonical record of each part is `parts/<status>/<slug>.json`** (validated
against [`schema/part.schema.json`](schema/part.schema.json)); the `.gb`,
`catalog.json`, `catalog.ttl`, and `catalog.jsonld` are *generated* projections of
it. Never hand-edit a generated file — edit the JSON and regenerate. Prose stays in
the sibling `<slug>.md`. Commit the JSON and the regenerated artifacts together —
CI fails if any is stale. See [`RDF.md`](RDF.md) for the RDF model. The `docs/`
tree is generated (git-ignored) and rebuilt by CI.

## Content guard

Part content is **lab-agnostic and tool-agnostic** — it describes what a part
*is*. `tools/check_content.py` enforces this over the canonical `parts/**/*.json`
(including the `functional_claims` prose that lives only there), the generated
`*.gb`, and the curated `*.md`, and it must pass before a push (it runs in CI and
as a `pre-push` hook). A part record must not:

- name a consuming tool;
- reference a specific *using* lab, person, or internal/unpublished plasmid
  lineage (naming the *originating* lab of a part — e.g. "the Bujard-lab pZ
  system" — is fine, like citing an author);
- define the part by negation/comparison ("this is not the …"). State what it
  *is*. (Legitimate scientific negation — "RNA-based control, no protein
  operator" — is fine.)

A second guard, `tools/check_requests.py`, keeps `sourcing/REQUESTS.md` to active
requests only (see [`sourcing/README.md`](sourcing/README.md)). Enable both as a
local push guard once per clone:

```bash
git config core.hooksPath scripts/hooks   # runs the content + requests guards on push
```

## Interactive part viewer

Each validated part page embeds an interactive feature/sequence view. It is a
self-contained, iframe-isolated widget at
[`docs/assets/seqmake-part-view.js`](docs/assets/seqmake-part-view.js) — a
**vendored build** of the upstream viewer widget, not hand-edited. `build_catalog.py`
inlines each part's `MoleculeInfo` (sequence + features) into the page as a
`<script type="application/json">` child of a `<div data-part-view>`, which the
widget hydrates on load. The bundle is **auto-copied** from the viewer's source
repo on each new version; the copy step must also update the provenance sidecar
[`seqmake-part-view.version.json`](docs/assets/seqmake-part-view.version.json)
(source / version / commit / built / **sha256**). The bundle is minified and not
hand-reviewed, so the sidecar is how each update stays auditable, and
`tests/test_widget_bundle.py` fails in CI if the committed bundle doesn't match
the recorded `sha256` (a partial copy, or a forgotten sidecar update). (When the
viewer ships as an npm package this becomes a CDN/package reference instead.)

## `catalog.json` schema (v1.0)

```jsonc
{
  "schema_version": "1.0",
  // counts below are an illustrative snapshot — see catalog.json for live totals
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
