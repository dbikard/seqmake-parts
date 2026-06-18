---
description: Add or improve one or more catalog parts via the verified annotate-part engine — source (independent re-fetch + compare), research, locate, adversarially verify, then merge the proposal safely (protecting reviewed claims), validate, and build. The engine is proposal-only; the merge is human-reviewed.
argument-hint: <part slug> [more slugs / a related cluster] [feature type]
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch, Workflow
---

You add or improve parts in this DNA parts catalog by driving the **annotate-part**
research/verify engine (`.claude/workflows/annotate-part.js`) and then merging its
proposal safely. The SOP and record rules are in @AUTHORING.md (record format:
@schema/part.schema.json). The engine is **proposal-only** and is the single
research/verify path — there is **no** verification-skipping quick path; the engine
scales down on its own (no Locate without sub-feature geometry, no cluster sharing for a
singleton), but source-match + citation verification always run.

Part(s) to add/improve: **$ARGUMENTS**

`$ARGUMENTS` is **natural language** — a contributor types it however they'd say it
(e.g. `T7lac`, `aadA, from UniProt P0AG05 (see PMID 26527143)`, `the Anderson promoters
J23100, J23101, J23102`, or a part name followed by a pasted sequence). In step 1 you
parse it into the slug(s), any source/accession **or citation hint** (an accession, PMID,
or DOI → the engine's `refs`), the family/`source` for a cluster, and the feature type.
Also check `sourcing/incoming/` for any PDF/sequence the contributor dropped there and
feed it to the Source phase. Never make the contributor write JSON.

## Hard rules (the engine enforces these; you uphold them on merge)

- **Sequence from a cited source, never memory.** The engine's Source phase independently
  re-fetches + compares via `tools/source_finder.py`. If it could **not** verify
  (access-blocked, or no 100% deposit), the proposal is flagged unverified — do **not**
  promote it. Follow the `sourcing/REQUESTS.md` handoff (`sourcing/README.md`): the human
  drops the document in `sourcing/incoming/`, then re-run so the engine byte-verifies and
  cites it. **When you're driving a contributor's run, nudge them directly**: if sourcing is
  blocked, ask them for a canonical **accession** or, for a paywalled paper, to drop the
  **PDF** into `sourcing/incoming/` and re-run — note it's gitignored (the PDF stays local;
  only the citation + provenance are committed). Frame it as optional-but-better, not a
  blocker for trying.
- **Boundaries need experimental grounding** (truncation / mutational scanning / mapping /
  genetics), not consensus — else they stay provisional with a lower `confidence`. If the
  grounding paper is inaccessible, **ask the contributor for it** (same `sourcing/incoming/`
  drop) before settling for a provisional boundary.
- **Granularity follows usage** (AUTHORING step 4): a functional sub-region becomes its
  own part only when it is **used standalone**; splitting is **additive** (keep the
  composite), the sub-part is named `<base>_<element>` and cross-linked. See step 4 below.
- Keep prose **lab- and tool-agnostic** (`tools/check_content.py` enforces this); type
  features with **Sequence Ontology** terms; **carry all synonyms**; **protein/CDS parts
  defer biology to UniProt** (`tools/import_uniprot_features.py`, no hand-authored
  residue features).
- **Never clobber human-reviewed knowledge.** Merges are additive and monotonic in
  `review_status`: an `ai-generated` claim may be overwritten, but an
  `ai-cross-checked`/`expert-reviewed` claim is immutable (a differing proposal is
  appended as a flagged `<id>__v2` that supersedes it) and a validated `.md` is never
  touched. `tools/merge_part.py` enforces this.

## Procedure

1. **Classify (dedup → axis 1; structure → axis 2; coherence+granularity → axis 3).**
   Search `catalog.json` / `parts/` for the slug + synonyms and run
   `python tools/catalog_overlap.py --slug <slug>` (or `--seq`) to catch sequence overlap.
   Result → **new | candidate | validated** (drives the write/merge policy). Note
   structure — DNA-with-geometry / a related cluster / protein-CDS — which only selects
   *which engine machinery fires*, never whether verification runs. Apply AUTHORING's
   *What a part is* (functional coherence ∧ standalone use): **(a) coherence** — is this
   span one coherent function, or a chimeric/mis-trimmed/mislabeled record? An unexpected
   cross-part homology (`catalog_overlap` localizes it) or vector/restriction-site context
   is a **bad-record** signal — never dismiss it; flag for re-sourcing, don't annotate
   as-is. **(b) granularity** — is the span its own part, a **sub-feature** of a larger
   part, or a member of a **composite** that should be minted (e.g. a tandem
   double-terminator)? Splitting *and* composing are both additive. **State the chosen axes
   per part; the user can override.** If a *different* part's sequence overlaps a new one
   (sub/superset or boundary variant), prefer refining/extracting/composing per AUTHORING
   (granularity), not a near-duplicate.

2. **Run the engine.** Call the **Workflow** tool with `name: "annotate-part"`, passing the
   spec as `args`:
   - single: `"<slug>"` or `{ "name": "<slug>", "refs": ["<canonical accession>"] }` —
     seed `refs` with a known canonical carrier (e.g. a plasmid GenBank accession); it
     makes the Source phase robust to NCBI BLAST flakiness.
   - cluster (a related family that shares a source): `{ "source": "<hint>", "parts":
     [ <specs> ] }` — the literature is researched once and a `collections.json`-ready
     block falls out.

   The engine returns a `part.schema.json`-shaped **proposal** per part (sourced sequence
   + `provenance.sequence_source`, located + verified sub-features, checked citations,
   drafted `functional_claims`, a curated `.md` draft, and curation `recommendations`).
   It writes nothing.

3. **Merge / write per axis 1.**
   - **new** → scaffold with `tools/new_part.py` (which stamps the SO `db_xref` via
     `tools/so_terms.py`), then apply the proposal's `features` / `references` /
     `provenance.sequence_source` / `functional_claims`. Write the curated
     `parts/validated/<slug>.md` and place the `.json` in `validated/` when the record
     clears the completeness bar (sourced provenance, SO-typed main feature, ≥1
     reference, ≥1 functional_claim, non-empty `.md`); else leave it a **candidate**.
   - **candidate / validated** → write the proposal as a *proposed overlay* to
     `/tmp/<slug>.proposed.json` (only what you're contributing — typically
     `functional_claims` with stable type-derived ids, new `references`, `provenance`;
     `features` only if deliberately re-annotating). **Dry-run** then persist:
     ```bash
     python tools/merge_part.py --into parts/<status>/<slug>.json --proposed /tmp/<slug>.proposed.json   # report
     python tools/merge_part.py --into parts/<status>/<slug>.json --proposed /tmp/<slug>.proposed.json --write
     ```
     Read the report; surface every `flagged_superseding`. A **sequence mismatch is a
     hard error** — fix the sourcing, don't force it. Never touch a validated `.md`.
   - **coding parts:** run `python tools/import_uniprot_features.py <slug>` after writing.

4. **Act on curation recommendations.** The engine's *verified* recommendations
   (rename / redelimit / split / merge / compose / new_part / metadata) are for the
   curator. Granularity recs come in **both** directions and both are **additive**:
   - **extract `new_part`** (a standalone-used sub-region, e.g. `Pbla_P3`): if the
     standalone-use evidence is **solid** (≥2 independent contexts), mint it — run this
     procedure on `<slug>_<element>`, deriving its sequence from the composite, **keep**
     the composite, and add the two-way cross-link (composite gets a `component`
     qualifier; the sub-part a `sub_region_of`), showing the merge before writing.
   - **compose / `merge`** (an adjacent same-class ensemble used as one unit, e.g.
     `rrnBT1T2` from `rrnBT1`+`rrnBT2`): if the standalone-use evidence is **solid**, mint
     the composite — run this procedure on the composite slug, **sourcing its sequence
     fresh** from the native/canonical deposit (never by concatenating member parts),
     **keep** the atoms, and add the same two-way cross-link.
   If the standalone-use evidence is weak, **list it for the user** rather than minting.
   Never silently redelimit / extract / compose on consensus.

5. **Run every gate and make them pass:** `tools/validate_parts.py`, `tools/build_gb.py`,
   `tools/build_catalog.py`, `tools/build_rdf.py`, `tools/check_content.py`,
   `pyshacl -s tools/shapes.ttl -i rdfs catalog.ttl`, `pytest tests/ -q`. A
   `check_content` failure goes **back to the engine** (re-synthesis), not into
   hand-edited prose.

6. **Auto-apply or escalate** (see @AUTHORING.md → *Autonomy — auto-apply vs human
   review*). Once the gates pass, classify each part:
   - **Auto-apply** when the change is additive + source-verified + `ready_to_apply` + a
     clean `merge_part` report (no `flagged_superseding`, no `flags`) + **no** structural
     recommendation (`redelimit` / `split` / `merge` / `new_part`-extract / `rename`).
     Then **commit it without asking** and **finalize per step 7**, reporting a one-line
     summary of what landed.
   - **Escalate to me** when ANY hard signal is present — an **unverified / blocked
     source**, a **verification failure**, a `flagged_superseding` / sequence-or-provenance
     conflict, a **structural/identity/boundary** recommendation, or a gate that
     re-synthesis can't fix. Then show the new/changed `<slug>.json` (+ `.md`), the merge
     report, and the specific hard point — and do **not** commit.

   For a batch, classify per part (a cluster also yields a `collection` block); always
   surface a one-line per-part summary either way.

7. **Finalize — commit and open the pull request.** Stage the canonical `<slug>.json`(s),
   the curated `.md`, and the regenerated artifacts (`catalog.json`, `catalog.ttl`,
   `catalog.jsonld`, the `.gb`s), and commit with a clear message. Then open the PR with
   `gh`, **detecting the contributor's situation** — don't assume push access to the
   upstream `dbikard/seqmake-parts`:
   - **No upstream write access (the common case — an outside contributor):** they cloned
     with `gh repo fork … --clone`, so `origin` is *their fork* and `upstream` is the
     catalog. Create a branch (`add-part/<slug>`), push it to `origin`, and open the PR:
     ```bash
     git switch -c add-part/<slug> && git add -A && git commit -m "feat(parts): <slug> — <one-line>"
     git push -u origin add-part/<slug>
     gh pr create --repo dbikard/seqmake-parts --fill   # gh routes the cross-fork PR from the fork branch
     ```
     If no fork/remote is set up yet, create one first: `gh repo fork dbikard/seqmake-parts --remote`.
   - **Upstream write access (a maintainer):** commit on a branch and `gh pr create`, or
     push to `main` where the repo policy permits.
   Report the PR URL. The PR description should summarize the sourced sequence + cited
   claims so a reviewer can check provenance at a glance. **Never** force a push or open a
   PR when step 6 escalated (unverified source / verify failure / reviewed-claim conflict /
   structural decision) — surface the issue instead.

If anything is ambiguous (which sequence variant, which boundary, conflicting literature,
whether to mint an extract), ask me rather than guessing.
