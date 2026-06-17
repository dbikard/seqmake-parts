# Authoring a part

**This is the single source of truth for what a part is and how it is defined,
added, and validated** — the standard operating procedure for the `/add-part`
agent and for human contributors alike. [`CONTRIBUTING.md`](CONTRIBUTING.md) is
the practical on-ramp (how to submit a contribution) and
[`schema/part.schema.json`](schema/part.schema.json) is the machine contract for a
record; both defer to this document for the rules. When they disagree, this wins.

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

**What a part is (the principle the rest derives from).** A part is a sequence that is
both **functionally coherent** — it performs *one* functional class, whether as a single
element or as a coherent ensemble of same-class elements acting as one unit — **and**
**used as a unit** — deployed on its own in synthetic constructs, recurrently, ideally
across multiple distinct contexts. Both are required, and each rules out a failure the
other can't:
- *Function without usage* → you'd mint every −10 box and every terminator hairpin. An
  element that is only ever used *inside* a larger unit is a **sub-feature/annotation**
  of that part, not a part of its own.
- *Usage without function* → you'd admit chimeric cloning fragments that merely recur (a
  binding site fused to a terminator fused to an MCS). A span that isn't one coherent
  function is a **bad record**, not a part — re-delimit it to the functional unit or
  flag it (step 1).

The catalog represents a sequence at **every granularity that independently satisfies
both**, *additively* and linked by composition — so an element and the larger unit it
belongs to can both be parts at once (e.g. `rrnBT1`, `rrnBT2`, **and** a `rrnBT1T2`
double-terminator). This one principle drives granularity in **both** directions — extract
a sub-part *or* compose a larger one (step 4) — and underlies the coherence check in
step 1. Evidence that a span is "used as a unit": a registry/standard identifier or
conventional name, primary literature or common constructs deploying *just* that span, or
a recognized minimal/standard form — in **≥2 independent contexts**. A **composite part**
is one contiguous sequence deployed as a single unit; a **collection**
(`collections.json`) is a browse-together family that is never itself one sequence — same
function ≠ a part unless it ships as one sequence.

A part is a **candidate** (a bare sequence + minimal info) until it becomes a
**curated record** — sourced provenance, SO-typed main feature, located sub-features,
references and functional_claims — *and* gains a curated `.md`; then it moves to
`parts/validated/` and is **validated**. `tools/validate_parts.py` enforces the
*machine-checkable* part of that bar: sourced provenance, an SO-typed main
feature, ≥1 cited reference, ≥1 functional_claim with a cited source, and a
non-empty `.md`. Located sub-features are an authoring expectation, not gated.
The authoring agent writes that `.md`, so a full `/add-part` run yields a validated
part directly; a part dropped in with only a sequence stays a candidate. Independently,
every `functional_claim` (and the record) carries a `review_status` (`ai-generated` →
`ai-cross-checked` → `expert-reviewed`): a part can be validated yet still
`ai-generated`.

## Hard rules

- **Sequence from a cited source — never from memory.** Take the sequence from a
  primary paper or a registry (Addgene, iGEM, SEVA, UniProt/NCBI) and record
  where, in `provenance.sequence_source`. A part without a sourced sequence is not
  acceptable. **If a needed source is access-blocked** (paywall/login/403), don't
  guess — record it in `sourcing/REQUESTS.md` and stop; resume once the human has
  dropped the document in `sourcing/incoming/`, byte-verifying against it and citing
  it in `provenance.sequence_source` (see `sourcing/README.md`).
- **One functional class per part** (atomic). A promoter and an RBS are two
  parts, not one (a span bundling >1 SO functional class always splits — see the
  atomicity note in step 4).
- **Coding parts are protein-canonical and defer biology to UniProt.** A `CDS` /
  `protein_domain` is stored as its amino-acid sequence (begins with `M`) with a
  **required** `UniProt:…` (or `NCBI:…`) accession on the main feature. Do **not**
  *hand-author* residue-level features (domains, active sites, binding residues,
  PTMs). Instead **import** them from UniProt with
  `python tools/import_uniprot_features.py <slug>` — that caches a provenance-
  tagged `uniprot_features` projection that gets baked into the generated `.gb`
  (so GenBank consumers like seqmake get authoritative, attributed features) and
  emits a first-class `rdfs:seeAlso` to the UniProt entry. Author only the
  engineering layer — role, functional_claims, cognate partners, collections.
  (DNA parts keep their hand-authored sub-features: −35/−10/operator, etc.)
- **Resolve a non-exact sequence in this order.** When the part sequence isn't an
  exact match to its accession, the importer: (1) if `variant_rationale` is set,
  **keeps** the intentional variant (e.g. dCas9 = D10A/H840A); else (2) asks
  **UniParc** whether the exact sequence exists under a *different* UniProt
  accession and, if so, **re-points** the part to that accession (it's a real
  protein, just mis-accessioned); else (3) for a close same-length variant,
  **normalizes** to the assigned accession's canonical sequence (UniProt is the
  reference); else (4) records it as **wrong accession** / divergent / isoform and
  does not import. So normalization is a last resort, not the default.
- **Lab- and tool-agnostic prose.** Describe what the part *is*; never name a
  consuming tool, a using lab, or an internal plasmid. `tools/check_content.py`
  enforces this.
- **Sequence Ontology typing.** Type the part and each sub-feature at the
  **functional-class** level — promoter `SO:0000167`, ribosome_entry_site
  `SO:0000139`, terminator `SO:0000141`, CDS `SO:0000316`, operator `SO:0000057`,
  origin_of_replication `SO:0000296`, `-35` `SO:0000175`, `-10` `SO:0000176`. Use
  the class, not a more specific term (an RBS is `SO:0000139`, not
  `bacterial_RNApol_promoter`); a finer term like `Shine_Dalgarno_sequence`
  `SO:0000552` is used only as an explicit `db_xref` on a dedicated sub-feature,
  never inferred from a label. `tools/new_part.py` stamps the main feature's
  `db_xref`; otherwise `tools/build_catalog.py` derives `so_term` from the feature
  type / `regulatory_class` (an explicit `db_xref` wins), and the website index
  groups validated parts by the main feature's `so_term`.
- **Carry all relevant synonyms.** Record every name the part is known by —
  literature names, registry IDs (iGEM / Addgene / SEVA), related-plasmid or gene
  names, and common abbreviations — in the main feature's `synonym` qualifier
  (`tools/new_part.py --synonym`). Synonyms drive search and dedup; when an
  overlapping part is deduped, **fold its synonyms into the canonical one** (e.g.
  `pMB1` / `pBR322 ori` / `pUC ori` now live on `ColE1`).
- **Claims cite their evidence.** Each `functional_claim` carries a `source`
  (PMID/DOI) and, where possible, a verbatim `quote` and a `figure`/`table`/`page`
  locator — prefer a quote from the **primary** source (`quote_source: primary`);
  if you only transcribe the catalog's own prose, mark `quote_source:
  catalog-doc`. Never invent a figure number you have not read.
- **Cross-link cognate partners.** A promoter names its transcription-factor
  part(s) with a repeatable `regulated_by="<TF>"` qualifier on its main feature
  (use a name/synonym already in the catalog); the build resolves it and derives
  the inverse ("regulates") on the TF's page, so the link is authored once and
  shown both ways. Composition cross-links (`component` ↔ `sub_region_of`, step 4)
  work the same way.
- **Declare collection membership on the part.** A part joins a family (a vector
  series, a promoter set, an inducible-sensor kit) with a repeatable
  `collection="<id>"` qualifier on its main feature — membership always lives on
  the parts, never in a central file. Give the collection its display prose in the
  top-level `collections.json` keyed by the same `<id>` (`name`, `description`,
  `source`, optional `references` and `resources`); the build groups members into a
  collection page and a "Browse by collection" hub.

## Procedure

1. **Check it isn't already there — and that it's a part at all.** Search `catalog.json`
   and `parts/` for the name and its synonyms, and run
   `python tools/catalog_overlap.py --slug <slug>` (or `--seq …`) to detect **sequence**
   overlap/containment with existing parts. If a part's sequence **overlaps** yours (a
   sub/superset, near-identical sibling, or a boundary variant of the same element),
   **refine that part** rather than adding a near-duplicate; only add a new part for a
   genuinely distinct functional unit. (Re-delimiting a boundary is **not** trivial — see
   step 4.) Apply the **coherence test** (per *What a part is*): does this span map to one
   coherent function? A migrated/candidate sequence may be **chimeric, mis-trimmed, or
   mislabeled** — a span that fuses unrelated functions (e.g. a binding site + a
   terminator + an MCS, betrayed by vector/restriction-site context or an *unexpected
   cross-part homology* — never dismiss one; `catalog_overlap` localizes it) is a **bad
   record**, not a part: re-delimit to the functional unit or flag it for re-sourcing, do
   not annotate it as-is. Then place the span on the granularity axis — its own part, a
   **sub-feature** of a larger part (coherent but never used standalone), or a member of a
   **composite** (step 4).
2. **Source the sequence + literature.** Run
   `python tools/source_finder.py --slug <slug> [--refs <canonical accessions>]`:
   - a **protein** part gets its source from the verified `uniprot_import` (its
     UniProt accession) — no BLAST;
   - a **DNA** part is BLASTed (date-bracketed, so old deposits aren't hidden by the
     score-ranked top-N) for the **oldest reputable 100% deposited carrier**, plus a
     **divergence** report vs each `--refs` accession (% identity, diff positions,
     edge-vs-internal). The NCBI BLAST is queued — run it in the background.

   **Act on the divergence:** 100% to a reputable canonical deposit → cite it; an
   **internal** diff → either **refine** the sequence to the canonical reference, or —
   if the differing form is itself common/old (gauge with `tools/blast.py --entrez`
   date-bracketing) — carry it as a **labelled sibling part** (e.g. `ColE1` vs
   `ColE1_AT`) with a `sequence_variant` claim noting the difference is benign; an
   **edge** diff is a **boundary** question — and boundaries need *experimental*
   grounding, not just alignment (see step 4). A sequence that matches only odd/modern
   deposits but diverges from the canonical reference is likely non-canonical — prefer
   the reference. For Addgene plasmids,
   `python tools/addgene.py search "<name>"` / `fetch <id> --out <file.gb>` (needs an
   `ADDGENE_TOKEN`, Catalog scope, https://www.addgene.org/developers/). Record the
   chosen deposit (a GenBank accession is best) in `provenance.sequence_source` and as a
   `GenBank:<acc>` db_xref (→ a nuccore cross-link in the docs/RDF).
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
   **Cross-reference an annotated deposit:** if the source (or an independent) GenBank
   record annotates the region, byte-verify against it and **reconcile your sub-feature
   coordinates / boundaries to the author annotation** — this caught the PCymRC 86→90 bp
   boundary and confirmed its −35/−10.

   **Boundaries are not a trivial bioinformatic call.** A part's start/end and a
   sub-feature's extent are frequently poorly defined by sequence or consensus alone;
   the authoritative basis is **experimental** — mutational scanning, progressive
   5′/3′ truncation, or genetic dissection of the minimal functional element. When
   (re)delimiting a boundary: (a) prefer coordinates supported by such experiments and
   **cite that paper**; (b) if you only have consensus / alignment / deposit-annotation
   support, set a **lower `confidence`** and note the boundary is provisional; (c)
   actively look for a paper carrying truncation / mutagenesis / genetics data — **use
   it if accessible, otherwise add it to `sourcing/REQUESTS.md`** (with what it would
   resolve) for a human to provide. Do not silently tighten or extend a boundary on
   sequence evidence alone.

   **Part granularity — split *and* merge, both additive (from *What a part is*).**
   Granularity is wherever a span jointly satisfies **functional coherence** *and*
   **standalone use** — and that can be several nested levels at once, so the same
   principle runs in **both** directions. Hold *every* level that independently passes the
   test, linked by composition; nothing is either/or.
   - **Split / extract (downward):** a *sub-region* independently passes both tests (its
     own coherent function + used standalone). Mint it **and KEEP the composite** — both
     coexist as a deliberate subset/superset overlap (an explicit exception to step 1's
     "overlap → dedup", alongside the `ColE1`/`ColE1_AT` variant siblings). e.g. `Pbla` =
     the full bla promoter region; `Pbla_P3` = the standalone strong P3 core.
   - **Merge / compose (upward):** an *adjacent ensemble* of same-class parts is itself
     used as one unit (one shared function + deployed together recurrently). Mint the
     **composite** and **KEEP the atoms** — e.g. the rrnB `T1`+`T2` tandem → a `rrnBT1T2`
     double terminator. A composite's sequence is **sourced fresh from the native /
     canonical deposit** (per the sequence-from-a-source rule), *not* assembled by
     concatenating member parts — assembly inherits member errors and drops the native
     junction/spacer.
   - **Evidence of standalone use (either direction):** a registry/standard identifier or
     conventional name (iGEM BioBrick, SEVA, …), primary literature / common constructs
     deploying *just* that span, or a recognized minimal/standard form — in **≥2
     independent contexts**. Absent that evidence, do **not** mint: keep the sub-region a
     sub-feature (don't split) or leave the atoms uncomposed (don't merge), and emit a
     `split` / `merge` **recommendation** instead — the conservative default is the form
     already attested.
   - **Naming & links:** the composite keeps the base slug; an extracted sub-part is
     `<base>_<element>` (`Pbla_P3`, `Pbla_P1`); a composed unit names the whole
     (`rrnBT1T2`). Link both ways — the composite's main feature lists its `component`
     part(s), each member records `sub_region_of` the composite (cross-link qualifiers,
     mirroring the promoter↔TF `regulated_by` link); fold shared synonyms onto the form
     they name.
   - **Boundaries still need experimental grounding** (truncation / mapping / mutagenesis),
     not consensus — else provisional + lower `confidence` (above). The two-criterion test
     decides *whether* a span is a part and *at what level*; experiment decides its *exact
     endpoints*.

   This is distinct from **atomicity**: a composite is a coherent ensemble of the **same**
   functional class acting as one unit; a span bundling *different* SO classes (a promoter
   *and* an RBS) is still split into atomic parts regardless of usage, because a part is
   one functional class.
5. **Set provenance.** Replace `provenance.sequence_source` with the real source.
6. **Add functional knowledge.** For any inducer / dynamic range / strength /
   host range claim, append a `functional_claims[]` entry with `type`, `label`,
   `value`, `source` (+ `quote`/`figure`), `confidence`, and `review_status`.
7. **Validate it (candidate).** Run the full gate suite in one command — this
   mirrors CI exactly, so passing locally means passing CI:
   ```bash
   python tools/check_all.py
   ```
   It runs, in order: the content / requests / link guards, JSON-schema
   validation (`validate_parts.py`), regeneration of every generated artifact
   (`build_gb.py` → `build_catalog.py` → `build_rdf.py`) with a staleness check,
   the SHACL shapes (`pyshacl`), and the tests (`pytest`). Run any one directly
   while iterating; run `check_all.py` before you commit.
8. **Promote to validated.** When the record clears the completeness bar (sourced
   provenance, SO-typed main feature, located sub-features where the part has
   internal structure, ≥1 cited reference, ≥1 functional_claim with a cited
   source), move the `.json` to `parts/validated/` and write the curated
   `parts/validated/<slug>.md` (sections: Origin, Properties, Use, References) — the
   agent writes this, so a fully-researched part is validated, not left a candidate.
   Re-run step 7 (`validate_parts.py` enforces the bar). Leave a part in
   `candidate/` only when it is genuinely bare (sequence + minimal info).
9. **Commit + open a PR** with the `<slug>.json`, the generated `.gb`,
   `catalog.json`, and `catalog.ttl`/`.jsonld`. An expert review promotes claims
   to `review_status: expert-reviewed`.

## Autonomy — auto-apply vs human review

Automate every change that can be **mechanically verified**; ask a human only when a
decision is genuinely hard. The engine already emits the signals that separate the two —
classify each proposed change after the merge dry-run + gates.

**Auto-apply** (write → gates → commit, no human gate) when ALL hold — the change is
*additive, verified, and reversible*:
- **Sourced**: the sequence is source-verified (independent re-fetch + compare), or
  unchanged for an existing part.
- **Verified**: `ready_to_apply` — every kept sub-feature passed the JS coordinate +
  adversarial citation checks.
- **Non-destructive merge**: `tools/merge_part.py` reports **no `flagged_superseding`** and
  **no `flags`** — it only adds claims / references / provenance / synonyms or overwrites
  an `ai-generated` claim; it never alters an `ai-cross-checked` / `expert-reviewed` claim
  or a validated `.md`.
- **No structural decision**: no `redelimit` / `split` / `merge`-or-`compose` /
  `new_part`-extract / `rename` recommendation is being applied — only `metadata` / `note`
  / feature-annotation
  refinements.
- **Gates pass**: `validate_parts` · `build_gb` · `build_catalog` · `build_rdf` ·
  `check_content` · `pyshacl` · `pytest` all green.

Because every change is git-reversible and fully verified, an auto-apply change may be
**committed without asking** — to `main` where direct commits are permitted, otherwise via
an auto-merged PR per the repo's push policy.

**Escalate to a human** when ANY holds — the decision is *hard* or *not cleanly
reversible*:
- source **unverified / access-blocked** (→ `sourcing/REQUESTS.md`);
- any **verification failure** (a coordinate / subsequence / citation check failed);
- the merge would **overwrite or supersede reviewed knowledge** (`flagged_superseding`) or
  hits a **sequence / provenance conflict** (`flags`);
- a **structural / identity / boundary decision** — `redelimit`, `split`,
  `merge`/`compose`, `new_part`-extract, `rename` — these change *what the part is*, need
  experimental
  grounding, and aren't cleanly reversible once the part is cited or composed into
  constructs (even a `verified: true` structural recommendation waits for a human);
- a **gate fails** that re-synthesis cannot fix.

In short: the mechanically-verifiable additive layer (sourcing, annotation, claims,
synonyms, notes) **auto-lands**; only part-identity / boundary judgments and verification
failures need a human.

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
