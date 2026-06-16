# RDF / semantic-web knowledge base

> **Status:** Phases 0 (canonical JSON spine) and 1 (structural RDF projection)
> implemented. Phase 2 (functional-knowledge layer) is implemented as **plumbing
> + verified exemplars** — the schema, the nanopub-shaped RDF projection, SHACL,
> and a few claims transcribed from curated `.md` prose; bulk extraction across
> the catalog is the remaining work. Phase 3 (public nanopublications) is
> designed below as a follow-up. The authoritative builds are `tools/build_gb.py`
> (JSON → `.gb`) and `tools/build_rdf.py` (→ RDF).

## Namespace & resolution (`w3id.org/seqmake/parts`)

The catalog's IRIs live under a permanent, host-independent base:
**`https://w3id.org/seqmake/parts/`** (`part/<slug>`, `collection/<id>`, local
vocabulary at `ns#`). A [w3id.org](https://w3id.org) redirect — defined in
[`w3id/seqmake/.htaccess`](w3id/seqmake/.htaccess) — forwards these to the
current GitHub Pages site, so the hosting (and even the repo name) can change
without breaking any IRI that has been published or cited ("cool URIs don't
change"). The redirect maps `part/<slug>` and `collection/<id>` to their pages
and `ns` to `catalog.ttl`.

To register or update it, submit `w3id/seqmake/` as a PR to
[`perma-id/w3id.org`](https://github.com/perma-id/w3id.org) (see
[`w3id/README.md`](w3id/README.md)). The base lives in one place,
`tools/build_rdf.py` (`BASE`/`PART`/`COLL`/`CAT`); changing it regenerates the
graph, and `tools/shapes.ttl` + the tests pin the same IRIs.

## Canonical record & build pipeline (Phase 0)

The authored source of truth for each part is `parts/<status>/<slug>.json` — a
full-fidelity record (every GenBank feature + qualifier verbatim, all references,
the sequence) plus the home for the functional-knowledge layer
(`functional_claims` / `provenance` / `review_status`). It is validated against
`schema/part.schema.json`. The `.gb` is a *generated* projection (still a
first-class, downloadable bench artifact); the existing readers consume it
unchanged:

```
<slug>.json  ──build_gb──►  <slug>.gb  ──build_catalog/build_rdf──►  catalog.json · site · catalog.ttl/.jsonld
   (canonical)              (generated)                              (generated)
```

Prose stays in the sibling `<slug>.md`. JSON↔GenBank is lossless (CI guards that
`.gb` is regenerable from JSON, like the `catalog.json` staleness guard).

The catalog is, underneath, already a semantic graph: every part carries a
[Sequence Ontology](https://www.ebi.ac.uk/ols4/ontologies/so) accession, typed
parent/child sub-features, synonyms, citations, cognate-regulator cross-links,
and collection membership. This document describes how that graph is projected
into standards-based **RDF** so AI agents and SPARQL clients can query the parts
knowledge base, and how the knowledge base is meant to **self-correct over
time**.

## Principles

1. **GenBank/JSON is authored; RDF is generated.** Curators and agents never
   hand-write RDF. The RDF is a deterministic projection built by
   `tools/build_rdf.py` from the same parse that produces `catalog.json`
   (`parse_part()` in `tools/build_catalog.py`). A deterministic generator +
   validation gate matters *more*, not less, when the author is a stochastic
   agent: it is the place where consistency and term-correctness are enforced.
2. **Reuse standards, invent almost nothing.** Structure comes from **SBOL3**,
   functional roles from **SO**, regulation from **SBO**, descriptive metadata
   from **Dublin Core / SKOS / PROV-O**. The only locally-minted vocabulary is a
   small `cat:` namespace for catalog-specific facts (curation status,
   regulation shortcut, provenance) that no standard covers.
3. **Two layers, two trust classes.** *Structural* facts (sequence, coordinates,
   SO type) are objective and projected deterministically. *Functional* claims
   (inducer, fold-change, strength, host range) are context-dependent and
   error-prone, so each carries its own provenance and confidence (Phase 2).
4. **Mutable by git, permanent only when settled.** The catalog starts with
   AI-agent mistakes and improves as smarter agents revisit claims. Git is the
   mutable correction/provenance layer (every fix is a commit). Permanent public
   nanopublications (Phase 3) are minted only for reviewed, stable claims.

## Identity (URIs)

| Thing | URI pattern |
|---|---|
| Catalog namespace | `https://w3id.org/seqmake/parts/` |
| A part (Component) | `…/part/<slug>` |
| Its sequence | `…/part/<slug>_sequence` |
| A sub-feature | `…/part/<slug>_feature_<n>` |
| Local vocabulary | `…/ns#` (prefix `cat:`) |
| A publication | `https://identifiers.org/pubmed:<pmid>` (or the DOI URL) |
| An SO / SBO term | `https://identifiers.org/SO:<id>` / `…/SBO:<id>` |

## Layer 1 — structural graph (SBOL3 + SO + SBO)

| Catalog concept | RDF |
|---|---|
| A part | `sbol:Component` |
| Molecule type | `sbol:type` → SBO (`SBO:0000251` DNA / `SBO:0000252` protein) |
| Functional role | `sbol:role` → the part's SO accession, verbatim |
| Sequence | `sbol:Sequence` (`sbol:elements` + `sbol:encoding` EDAM `format_1207`/`1208`) |
| Sub-feature | `sbol:SequenceFeature` + `sbol:hasLocation` a `sbol:Range` (1-based `start`/`end`, `sbol:inline`/`reverseComplement`) |
| Name / description | `dcterms:title` / `dcterms:description` |
| Synonyms | `skos:altLabel` |
| Citations | `dcterms:references` → PubMed/DOI URI |
| Collections | `sbol:Collection` + `sbol:member` |
| Curation status, slug, source accession | `cat:curationStatus`, `cat:slug`, `cat:sourceAccession` |

The exact SBOL3/SBO/EDAM IRIs are pinned in `tools/build_rdf.py` from the
official **pySBOL3** constants (e.g. `sbol3.SBO_DNA`, `sbol3.IUPAC_DNA_ENCODING`,
`sbol3.SBO_INHIBITION`), so they cannot drift from the spec.

### Regulation as SBOL3 Interactions

`Interaction`s and `Participation`s are scoped **inside a context Component**, and
a participant must reference a `Feature` of that same Component. So for "PhlF
represses PphlF" the projection emits, on the **promoter** `:PphlF` as context:

- a `sbol:SubComponent` of `:PphlF` whose `sbol:instanceOf` → the TF `:PhlF`;
- the inhibited target as a `Feature` of the promoter — its operator
  `SequenceFeature` when present, else a whole-length feature;
- an `sbol:Interaction` typed **SBO:0000169** (inhibition; **SBO:0000170**
  stimulation for activators) with two `Participation`s: inhibitor
  (**SBO:0000020**) → the TF SubComponent, inhibited (**SBO:0000642**) → the
  operator feature.

A denormalized `cat:regulatedBy` / `cat:regulates` triple is **also** emitted as
a shortcut for simple SPARQL (and is the only form when the named TF is not a
catalog part). The inhibition-vs-stimulation polarity is, in Phase 1, a
**heuristic** (default inhibition; a small known-activator set for AraC/ChnR/XylS
/…), logged at build time. In Phase 2 it becomes a provenance-bearing functional
claim.

### Worked example — PphlF

```turtle
@prefix sbol: <http://sbols.org/v3#> .
@prefix so:   <https://identifiers.org/SO:> .
@prefix sbo:  <https://identifiers.org/SBO:> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix pubmed: <https://identifiers.org/pubmed:> .
@prefix cat:  <https://w3id.org/seqmake/parts/ns#> .
@prefix :     <https://w3id.org/seqmake/parts/part/> .

:PphlF a sbol:Component ;
    sbol:displayId "PphlF" ; dcterms:title "PphlF" ;
    sbol:type sbo:0000251 ; sbol:role so:0000167 ;
    sbol:hasSequence :PphlF_sequence ;
    sbol:hasFeature :PphlF_feature_2 , :PphlF_sub_PhlF ;
    sbol:hasInteraction :PphlF_interaction_PhlF ;
    cat:curationStatus "validated" ; cat:regulatedBy :PhlF ;
    dcterms:references pubmed:24316737 , pubmed:27034378 .

:PphlF_sequence a sbol:Sequence ;
    sbol:encoding <https://identifiers.org/edam:format_1207> ;
    sbol:elements "tctgattcgttaccaattgacatgatacgaaacgtaccgtatcgttaaggt" .

:PphlF_feature_2 a sbol:SequenceFeature ;          # the phO operator
    dcterms:title "phO" ; sbol:role so:0000057 ;
    sbol:hasLocation [ a sbol:Range ; sbol:sequence :PphlF_sequence ;
        sbol:start 22 ; sbol:end 51 ; sbol:orientation sbol:inline ] .

:PphlF_sub_PhlF a sbol:SubComponent ; sbol:instanceOf :PhlF .
:PphlF_interaction_PhlF a sbol:Interaction ; sbol:type sbo:0000169 ;
    sbol:hasParticipation
        [ a sbol:Participation ; sbol:role sbo:0000020 ; sbol:participant :PphlF_sub_PhlF ] ,
        [ a sbol:Participation ; sbol:role sbo:0000642 ; sbol:participant :PphlF_feature_2 ] .
```

## Layer 2 — functional knowledge (Phase 2)

The richest knowledge lives in the `.md` prose, not the GenBank: PphlF's `.md`
records ~80× fold repression, inducer = DAPG, the J23119 scaffold, the
mechanism. These become typed claims in each part's canonical JSON
(`functional_claims`), each carrying **source** (PMID/DOI), **extraction
provenance** (method, asserting agent, source doc), **confidence**, and
**review_status** (`ai-generated` → `ai-cross-checked` → `expert-reviewed`), plus
a **supersedes** pointer for corrections. `tools/build_rdf.py` projects them into
RDF in the **nanopublication shape** — each claim an assertion node with
`prov:wasDerivedFrom` its source and `prov:wasGeneratedBy` its extraction
activity — queryable alongside Layer 1 and SHACL-validated. They stay mutable in
git; nothing permanent is minted (that is Phase 3).

A claim's **source is as granular as possible**: beyond a PMID/DOI it carries a
verbatim `quote` (with `quote_source` = `primary` for the paper or `catalog-doc`
for the curated `.md`) and a `figure` / `table` / `page` / `section` locator, so a
reviewer can find the evidence rather than just the paper. These project to
`cat:sourceQuote` / `cat:sourceFigure` / … on the claim. Figure-level locators
into the primary PDFs are filled "when possible" — the exemplars quote the curated
`.md` (the text actually read) and leave paper figure numbers for the
review / PDF-extraction pass rather than guessing them.

Ontology mapping is **lazy**: a claim names its inducer/unit/host as a label and
fills the ChEBI / OM / NCBI-Taxonomy IRI only when verified (`null` otherwise) —
no guessed IRIs. Worked claims live on `PphlF` (DAPG inducer + ~80× repression)
and `PtetA` (aTc inducer). Bulk extraction across the catalog, gated by review,
is the remaining Phase 2 work.

## Mutability & correction model

Git is the version/provenance/correction layer: the current graph is always the
best answer; every correction is a commit (which agent/model, when, why) with
full history and revert. Claims self-describe `confidence` and the asserting
model so successor agents can find and re-check the weakest ones — the KB carries
its own to-do list. **Public nanopublications are immutable and permanent**, so
they are minted (Phase 3) only for reviewed/stable claims, where permanence is a
feature, not a liability.

## Storage & querying

1. **Static files (current):** `catalog.ttl` + `catalog.jsonld` are generated,
   committed, and published next to the site. Load with `rdflib` and run local
   SPARQL — no server.
2. *(future)* Oxigraph single-binary SPARQL endpoint, if a live endpoint is
   needed.
3. *(future)* SynBioHub, to federate SBOL3 with the wider community.

## Validation

`tools/shapes.ttl` (SHACL, run with `pyshacl`) enforces the invariants the
catalog already assumes: every Component has a role + a sequence; ranges fall
within the sequence; every Interaction is typed with ≥2 typed Participations;
`cat:regulatedBy` resolves to a known part. CI also guards that the committed
`catalog.ttl` / `catalog.jsonld` are up to date (the same git-diff pattern used
for `catalog.json`).

## Build

```bash
pip install -r requirements.txt
python tools/validate_parts.py     # JSON spine vs schema/part.schema.json
python tools/build_gb.py           # canonical JSON -> .gb
python tools/build_catalog.py      # catalog.json + site
python tools/build_rdf.py          # catalog.ttl + catalog.jsonld
pyshacl -s tools/shapes.ttl catalog.ttl
```
