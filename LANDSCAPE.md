# Strategic landscape review

> Where this project sits among the existing biological-parts software ecosystem,
> what gap it fills, and how it should relate to the incumbents.

This review was prompted by Plahar *et al.*, **"BioParts: A Biological Parts
Search Portal and Updates to the ICE Parts Registry Software Platform"**
(*ACS Synth. Biol.* 2021, 10, 2649–2660,
[doi:10.1021/acssynbio.1c00263](https://doi.org/10.1021/acssynbio.1c00263)) and
extends the comparison to the wider ecosystem it situates itself in —
**SynBioHub**, the **iGEM Registry**, **Addgene**, and the commercial tools
(**Benchling**, **TeselaGen**). The goal is strategic, not a feature audit: to
state plainly what kind of artifact this project is, what it is *not*, and how it
should interoperate with the systems below rather than compete with them.

## TL;DR

The incumbents are **platforms** — multi-user servers that *store, share, and
search* parts contributed by many labs, optimized for breadth, deposition
workflow, and physical-sample logistics. This project is not a platform; it is a
small, deeply **curated, machine-readable knowledge base** optimized for the one
thing the platforms treat as a free-text afterthought: the **functional
knowledge** about a part (what induces it, its dynamic range, host range,
mechanism) carried as typed, individually **provenance-tracked, confidence-rated,
review-tiered claims**. The strategic position is *complementary, not
competitive*: we should be a high-quality, FAIR data **source** that the
incumbents' search portals index and the standards (SBOL3/RDF) let everyone
federate — not another server to run.

## What the BioParts / ICE paper describes

The paper has two parts, both from the JBEI/Agile BioFoundry group:

1. **ICE 5.9** — a modernization of JBEI-ICE (Inventory of Composable Elements),
   the open-source (BSD) parts-registry *platform* first published in 2012. ICE
   stores plasmids, strains, parts, seeds, and proteins with fine-grained access
   control, sample/LIMS tracking (incl. Addgene/GenScript links), bulk
   spreadsheet editing, audit history, BLAST auto-annotation, and import/export
   in GenBank/FASTA/**SBOL**/GFF3. The rewrite swapped Adobe Flex for
   **OpenVectorEditor** (TeselaGen's React sequence editor) and SOAP for a
   **REST API**.
2. **Web of Registries + BioParts (bioparts.org)** — ICE instances federate
   peer-to-peer via hashed secure tokens into a distributed parts database, and
   **bioparts.org** is a Google-style search portal that *indexes* >10 public
   sources (NCBI, iGEM, SynBioHub, Addgene, public ICE registries) and lets
   anyone search by **keyword or sequence fragment (BLAST)**, with a REST API and
   an autoannotation service. The indexer deliberately **does not duplicate
   sequences**; it points back to the source of record.

Their stated future work — SBOL support in BioParts, version control, and
**provenance tracking of entries** — is notable: it is exactly the territory this
project already treats as its core, not a roadmap item.

## The landscape, by what each thing actually *is*

| System | Kind | Optimized for | Data model | Hosting | Functional knowledge? |
|---|---|---|---|---|---|
| **JBEI-ICE** | Registry platform (server) | Lab/institution part+strain inventory, sample tracking, access control | Relational (Hibernate ORM); SBOL/GenBank I/O | Self-hosted instances, federated | Free-text fields / custom fields |
| **BioParts (bioparts.org)** | Federated **search portal** | Find a part across many registries by keyword/sequence | Index over external sources (no copy of record) | Single hosted portal + API | No — it ranks and links out |
| **SynBioHub** | **Design** repository | Storing/sharing SBOL designs, SPARQL over a triplestore | **SBOL2/3 → RDF** (Virtuoso), native | Self-hosted + federated; hub at synbiohub.org | Structured where SBOL captures it; mostly design structure |
| **iGEM Registry** (parts.igem.org) | Community catalog | BioBrick parts contributed by iGEM teams | Per-part wiki pages + characterization data | Single hosted site | Crowd-sourced, uneven free-text/datasheets |
| **Addgene** | **Physical** repository | Ordering real plasmid DNA; QC'd maps | Curated plasmid records + sequence | Single hosted service | Publication-linked, free-text |
| **NCBI (GenBank/RefSeq)** | Sequence archive | Authoritative sequence + feature records | GenBank/INSDC | Hosted | Feature qualifiers, not part-level function |
| **Benchling / TeselaGen** | Commercial DBTL suites | End-to-end design–build–test in industry | Proprietary | SaaS | Rich but closed/per-tenant |
| **This project** | Curated **knowledge base** (dataset) | *Trustworthy, queryable functional knowledge per part* | Canonical JSON → GenBank + **SBOL3/RDF**, with a claims layer | **Static files in git** (no server) | **Yes — first-class, per-claim provenance/confidence/review** |

Two structural observations fall out of the table:

- **Almost everything in the field is a *server*.** ICE, SynBioHub, iGEM,
  Addgene, Benchling are all multi-tenant applications you log into, deposit to,
  and search. Their hard problems are access control, deposition UX, federation,
  and sample logistics. BioParts is a server *about* those servers.
- **Functional knowledge is everywhere a second-class citizen.** Across the
  platforms, *what a part does* — its inducer, fold-change/dynamic range,
  strength class, host range, mechanism, and the **evidence** for each — lives in
  free-text descriptions, wiki prose, or attached datasheets. It is rarely
  typed, almost never carries machine-readable per-fact provenance and
  confidence, and is not independently queryable or correctable. SBOL/SynBioHub
  model design *structure* well; the *characterization* story is thinner and
  uneven.

That second observation is the gap this project is built around.

## Where this project sits

**SeqMake Parts** is deliberately **not** another registry platform, federated
search portal, or physical repository. It is a **standalone, reusable dataset** —
a provenance-tracked knowledge base of standard parts — with a few defining
choices that distinguish it from everything in the table above:

1. **Functional knowledge is the product, modeled as data.** Each part carries
   typed `functional_claims` (inducer, repression/induction dynamic range,
   strength class, host range, mechanism). Every claim is *self-describing*: it
   travels with its **source** (PMID/DOI plus a verbatim quote and a
   figure/table/page locator), its **extraction provenance** (method, asserting
   agent, source doc), a **confidence**, and a **review tier**
   (`ai-generated → ai-cross-checked → expert-reviewed`), with a `supersedes`
   pointer for corrections. This is the nanopublication idea applied to parts
   characterization — and it is the thing the incumbents leave in prose.

2. **One canonical source, three FAIR projections.** The authored truth is a
   schema-validated `<slug>.json`; from it we deterministically generate the
   downloadable **GenBank**, the `catalog.json` manifest, and an **RDF graph
   (SBOL3 + Sequence Ontology + SBO)** that is SPARQL-queryable and **federates
   with UniProt**. We *reuse standards and invent almost nothing* — exactly the
   SBOL/FAIR direction the BioParts authors point at as future work, treated here
   as the foundation.

3. **Git is the database; static files are the deployment.** No server to run,
   no instance to join, no access tokens. Correction and provenance are the git
   history; permanence (future public nanopublications) is minted only for
   settled claims. This sidesteps the entire operational burden that defines the
   platforms — at the cost of their multi-user/deposition/logistics features,
   which is a trade we *want* to make.

4. **Permanent, host-independent identity.** Parts and collections resolve under
   `https://w3id.org/seqmake/parts/`, so cited IRIs survive a change of hosting or
   repo name — a FAIR property the single-hosted portals don't guarantee.

5. **AI-authored, but transparent about it.** The KB is openly experimental and
   AI-generated, and turns that into a discipline: a deterministic generator +
   validation gate around a stochastic author, and per-claim trust metadata so a
   reader checks the source, confidence, and review tier rather than trusting the
   record wholesale. None of the incumbents surface trust at the granularity of a
   single fact.

In one sentence: **the platforms answer "where can I find/get this part?"; this
project answers "what does this part do, how confident are we, and what's the
evidence?" — as data, not prose.**

### The positioning axis

```
            broad / shallow / many depositors                deep / curated / few parts
            (storage, search, logistics)                     (verified functional knowledge)
  ICE ── iGEM ── Addgene ── NCBI ───── BioParts (search over all of them) ───────┐
                                                                                  │
                          SynBioHub (SBOL designs, RDF) ──────────── THIS PROJECT │ (claims + provenance)
                                                                                  ┘
        server / multi-tenant / login                          static files / git / no server
```

We compete with nobody on the left axis and shouldn't try. Our defensible ground
is the bottom-right: small, deeply annotated, every functional fact sourced and
trust-rated, shipped as standards-based FAIR files.

### Naming & identity

The project is named **SeqMake Parts** and mints its permanent IRIs under
`https://w3id.org/seqmake/parts/` — the parts dataset within the **SeqMake**
house brand (the same brand as the embedded part-view widget). This is a
deliberate move *away* from the working name "bioparts": JBEI's portal already
owns **BioParts / bioparts.org** in this exact field, so a near-identical name
would have read as "that portal's data" and blurred precisely the
knowledge-base-vs-registry distinction this review draws. Namespacing under
SeqMake instead inherits an existing identity, signals that the parts catalog is
one dataset in a wider tooling family, and keeps the IRI base free of the clash.
The base was changed *before* the w3id redirect was registered or any IRI was
externally cited, so no "cool URI" was broken — the cheap window to rename was
taken while it was still open.

## Strategic implications

### Opportunities

- **Be the source the portals index, not a portal.** BioParts indexes >10
  sources and links back to the record of origin without copying it. A clean,
  static, standards-based catalog with stable IRIs is an *ideal* such source.
  The strategic move is to make this catalog trivially indexable/harvestable
  (sitemap, stable per-part URLs, SBOL/GenBank download, an RDF dump) so it shows
  up *inside* the searches researchers already run.
- **Interoperate via SBOL3, federate via SynBioHub.** RDF.md already names a
  SynBioHub deposit as future work. Because our RDF is SBOL3-native, we can
  *publish into* SynBioHub (gaining discoverability + federation) while keeping
  git as the editable source of truth — getting reach without becoming a server.
- **Own the characterization/provenance layer the field under-serves.** The
  BioParts authors list "provenance tracking" as roadmap; SBOL models structure
  better than characterization. A well-modeled, queryable, nanopub-shaped claims
  layer with confidence and review tiers is a genuinely differentiated
  contribution the ecosystem lacks.
- **AI-agent-native consumption.** A SPARQL-queryable graph where every
  functional fact carries source + confidence is exactly what an LLM/agent needs
  to *cite* rather than hallucinate. As agent-driven design grows, "parts
  knowledge an agent can quote with evidence" is a sharpening advantage.

### Risks and honest weaknesses

- **Scale vs. the registries.** ~35 validated + ~200 candidate parts against
  registries with tens of thousands. We will never win on breadth, and shouldn't
  frame ourselves as trying to — the value is depth and trust per part. The risk
  is being dismissed on count by anyone who misreads the category.
- **Curation throughput is the bottleneck.** The whole value proposition rests
  on the claims layer, which RDF.md candidly notes is "plumbing + exemplars" with
  bulk extraction still to do, and review tiers that must be *earned*. If
  expert-reviewed coverage stays thin, we're a nicely-modeled but largely
  `ai-generated` dataset — credible only as far as the transparency carries it.
- **No deposition / collaboration / sample logistics.** Deliberate, but it means
  we're useless for the lab-inventory and physical-DNA jobs ICE/Addgene own. We
  must be explicit that we are an *upstream knowledge source*, not a LIMS.
- **Discoverability without a server.** Static files don't market themselves.
  Without active indexing (BioParts), federation (SynBioHub), and w3id
  resolution working end-to-end, even excellent data stays invisible.
- **Standards drift / single-maintainer continuity.** SBOL3, SO, and SBO evolve;
  pinning IRIs from pySBOL3 mitigates this, but a small/AI-driven project carries
  bus-factor and upkeep risk the institution-backed platforms don't.

## Recommendations

1. **Frame, everywhere, as a *knowledge base / data source*, not a registry or
   portal.** Keep the README's category-defining language; explicitly say what we
   are *not* (no deposition, no samples, no multi-user server) so we're judged on
   depth and provenance, not part count.
2. **Make the catalog first-class harvestable** so portals like bioparts.org can
   index it: stable per-part pages/IRIs (done via w3id), a discoverable RDF/SBOL3
   dump and GenBank/FASTA downloads (done), plus a sitemap and a documented
   "how to index this catalog" note.
3. **Prioritize the SynBioHub bridge** (already future work in RDF.md): a
   one-way SBOL3 publish from the generated graph buys federation and reach while
   git stays the editable source.
4. **Invest the marginal effort in the claims layer and review tiers, not in
   part count.** Depth of verified, expert-reviewed functional knowledge is the
   moat; breadth is a race we lose by design. Drive bulk claim extraction and
   move exemplars up the `ai-generated → expert-reviewed` ladder.
5. **Lean into agent-citable knowledge** as a distinct use case the platforms
   don't serve: "functional facts an AI can quote with a source, a confidence,
   and a review status."
6. **Track the incumbents' roadmaps as convergence, not threat.** If BioParts
   adds SBOL + provenance, that *validates* the direction and gives us a richer
   target to feed into; our edge stays the granularity and curation of the claims
   themselves, not the format.

## Sources

- Plahar, H. A.; Rich, T. N.; Lane, S. D.; *et al.* BioParts: A Biological Parts
  Search Portal and Updates to the ICE Parts Registry Software Platform.
  *ACS Synth. Biol.* **2021**, *10*, 2649–2660.
  [doi:10.1021/acssynbio.1c00263](https://doi.org/10.1021/acssynbio.1c00263)
- Ham, T. S.; *et al.* Design, implementation and practice of JBEI-ICE.
  *Nucleic Acids Res.* **2012**, *40*, e141.
- McLaughlin, J. A.; *et al.* SynBioHub: A Standards-Enabled Design Repository
  for Synthetic Biology. *ACS Synth. Biol.* **2018**, *7*, 682–688; and
  Mante, J.; *et al.* Extending SynBioHub's Functionality with Plugins.
  *ACS Synth. Biol.* **2020**, *9*, 1216–1220.
- McLaughlin, J. A.; *et al.* The Synthetic Biology Open Language (SBOL) v3.
  *Front. Bioeng. Biotechnol.* **2020**, *8*, 1009.
- Wilkinson, M. D.; *et al.* The FAIR Guiding Principles. *Sci. Data* **2016**,
  *3*, 160018.
- iGEM Registry of Standard Biological Parts (parts.igem.org); Addgene
  (addgene.org); bioparts.org.
- This repository: [`README.md`](README.md), [`RDF.md`](RDF.md),
  [`CONTRIBUTING.md`](CONTRIBUTING.md), [`AUTHORING.md`](AUTHORING.md),
  [`schema/part.schema.json`](schema/part.schema.json).
</content>
</invoke>
