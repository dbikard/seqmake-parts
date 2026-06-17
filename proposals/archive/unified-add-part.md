# Proposal: unify `/add-part` + a research workflow into one researched-authoring capability

**Status:** substantially implemented (2026-06). The capability described here is
built and proven end-to-end on branch `feat/unified-add-part-engine`: the driver
`.claude/commands/add-part.md`, the proposal-only engine
`.claude/workflows/annotate-part.js`, and the supporting tools
(`tools/source_finder.py`, `tools/merge_part.py`, `tools/catalog_overlap.py`,
`tools/addgene.py`, `tools/blast.py`). This document is retained as the design
rationale / historical spec, not a pending to-do. Known remaining gaps:
batch/cluster runs not yet exercised end-to-end, and the `component` /
`sub_region_of` RDF projection in `build_rdf.py` is still pending.

## Why

Today there are two disconnected tools:

- **`/add-part`** (`.claude/commands/add-part.md`) — a single-agent slash command
  that runs the whole authoring lifecycle (source → annotate → claims → validate →
  build → write files), following `AUTHORING.md`. Because it researches with one
  in-context pass, a part is only as good as that pass: no adversarial check of
  sub-feature coordinates or citations, no parallel research, no shared research
  across a related cluster.
- **`annotate-part`** — a multi-agent **workflow** (lives in the seqmake repo at
  `~/seqmake/.claude/workflows/annotate-part.js`): Resolve → Research (parallel
  lenses, early-stop) → Locate → Verify (adversarial coord + citation checks) →
  Synthesize → (Collection for clusters). It is deep, cluster-aware, and
  proposal-only — but it is **seqmake-coupled** (`load_library()` + a lab-registry
  boundary scan), and speaks the **pre-weekend** `.gb`-centric data model, not this
  repo's JSON-canonical contract.

The result: `/add-part` can't produce a *well-researched* part because it doesn't
do the deep research, and the deep research engine can't author into this repo.

**Goal:** one capability — `/add-part` always yields well-researched, *verified*
parts; **never skips verification** on any path; supports **batch**; and is fully
self-contained in this repo (no seqmake dependency).

## Design — layer, don't merge

One user command on top of one research engine. The command **triages on two
independent axes** and then drives the engine; it does **no** research of its own.

```
/add-part  A, B, C                       ← catalog slash command (thin orchestrator)
   │
   ├─ dedup + classify each name  → new | candidate | validated   (axis 1: status)
   │                               → DNA-geometry? cluster? CDS?   (axis 2: structure)
   │
   ├─ fire the catalog-native annotate workflow (proposal-only, batch/cluster-aware)
   │     Source ── new:                discover + INDEPENDENTLY re-fetch & byte-compare
   │            └─ candidate/validated: re-verify the ALREADY-RECORDED seq vs its source
   │     Research → Locate (only if DNA sub-feature geometry) →
   │     Verify (coords + citations — ALWAYS, every part) → Synthesize → schema
   │     returns per-part VERIFIED records (sourced seq + provenance,
   │     located sub-features, checked PMIDs, drafted claims) + a collection block
   │
   └─ then (deterministic, human-in-the-loop): MERGE into each parts/<status>/<slug>.json
        (additive; never downgrade an existing review_status) ·
        import_uniprot_features for coding parts · run every gate ·
        per-part summary · commit on request
```

- **The command is thin**: it classifies, drives the engine, and *merges + validates*.
- **The workflow is the single research/verify engine**, proposal-only (never
  writes — preserves the human review gate, which matters for an AI-generated
  public KB). It is **cluster-aware**, so **batch is native**: one shared research
  pass across a *related* set, fan-out per part, and a `collection` falls out.
- **There is no verification-skipping "quick" path.** The old quick-vs-deep switch
  conflated two independent questions — *does this part need coordinate
  location?* and *does it have claims to verify?* — and let the cheap path skip the
  citation check on exactly the parts (CDS with claims, subtle accession choices)
  where sourcing errors hide. Instead the **engine scales down**: machinery you
  don't need simply doesn't fire (no Locate for a part with no sub-feature geometry,
  no cluster sharing for a singleton), but **source-match + citation verification
  always runs**. A genuinely trivial part (sequence in hand, CDS, residues deferred
  to UniProt) is therefore cheap *by construction* — small engine run, no bypass —
  which also removes the self-triage-overconfidence failure mode: no single agent is
  ever allowed to call its own work "trivial" and skip the check.

## The two triage axes

**Axis 1 — status (existence): decides what *Source* means and how conservatively we write.**
This is the output of the dedup check (command step 1). Re-running `/add-part` on a
part that already exists is a first-class mode, not an edge case.

| Status | In repo? | Source phase does… | Write policy |
|---|---|---|---|
| **new** | nothing | **Discover + verify**: find the sequence in a cited paper/registry and **independently re-fetch it and byte-compare** to what we'll store; emit `provenance.sequence_source`. | create `parts/candidate/<slug>.json` |
| **candidate** | `parts/candidate/<slug>.json` | **Re-verify**: the sequence already exists; re-resolve its *recorded* `provenance.sequence_source` (re-fetch the cited accession/registry id) and byte-compare to the stored sequence — confirm provenance still holds. Then deepen annotation/claims. | merge into the existing `.json`; **additive** — never overwrite or downgrade a `functional_claim` whose `review_status` is `ai-cross-checked` or `expert-reviewed` (add a new claim with `supersedes` instead). |
| **validated** | `parts/validated/<slug>.json` + `.md` | same as candidate | same as candidate, **plus** never touch the curated `.md` and never overwrite an `expert-reviewed` claim; additions only. Improving prose stays a human act. |

So "verify a candidate" and "add a new part" run the **same downstream engine**
(Research → Locate → Verify → Synthesize); they differ only at the front (re-verify
a recorded source vs discover-and-verify a new one) and at the back (additive merge
that respects `review_status` vs a fresh write). This makes the proposal's own
phasing step 1 — "re-annotate an existing part" — the *candidate-verification* path,
not a throwaway test harness.

**Axis 2 — structure: decides which research machinery fires (orthogonal to axis 1).**

- **DNA with internal geometry** (−35/−10/operator/+1, overlapping/divergent
  architecture) → run **Locate** (map elements onto the real sequence, verify
  subsequences) + adversarial coordinate checks.
- **Part of a related cluster** → one shared **Research** pass over the set + a
  **Collection** block.
- **Protein/CDS** → defer residue biology to UniProt (import after write); the
  engine researches only the **engineering layer** (role, claims, cognate partners).

**Always, on every axis-1/axis-2 combination:** adversarial **citation
verification** of every `functional_claim`, and a **content-guard-clean** synthesis
(see below). Verification is never conditional.

## Part A — refactor the workflow to this repo's contract (the bulk of the work)

This is an **alignment to the new canonical model**, not a line-by-line port; reuse
the seqmake workflow's proven *structure* but re-target its schemas and phases.

| Today (seqmake `annotate-part`) | Target (catalog-native) |
|---|---|
| Resolves a part via seqmake `load_library()` | reads this repo's canonical `parts/<status>/<slug>.json` (the **candidate/validated** path); for a **new** part there is nothing to resolve |
| Assumes the sequence already exists | adds a front **Source** phase (see *Source* below) whose behavior is set by **axis 1**: discover-and-verify (new) vs re-verify the recorded source (candidate/validated) |
| Emits `FINAL_SCHEMA` + `report_markdown` | emits a record shaped by **`schema/part.schema.json`**: `features[]` (+ qualifiers, SO `db_xref`, `citation`), `references`, `provenance.sequence_source`, and `functional_claims[]` in the nanopub shape (`source`{quote, quote_source, figure/table/page}, `provenance`{method, agent}, `confidence`, `review_status: ai-generated`, `supersedes`) |
| Hand-researches protein domains | **defers protein biology to UniProt**: resolve the accession (+ UniParc variant logic per `AUTHORING.md`), do **not** hand-author residue features; the command runs `tools/import_uniprot_features.py` after writing. The workflow only researches the **engineering layer** |
| Has a lab-registry boundary scan | **drop it** — it reads lab plasmids, which must not inform a public KB (a correctness fix, not just a decoupling) |
| Unaware of the content guard | **bake `tools/check_content.py`'s rules into the synthesis prompts** *and* have the workflow run its own guard-clean self-check before returning — see *Guard loop* below |
| Single write step | returns a **proposal only**; the command performs an **additive merge** that respects `review_status` (axis 1) |

### Source phase (new code — design it, don't treat it as a table row)

The seqmake workflow assumes the sequence already exists, so this phase has **no
existing structure to reuse** and is the highest-risk new code: it is the one place
that can violate the repo's single inviolable rule (*sequence from a cited source,
never from memory*). It must not be "an agent reads the paper and agrees."

- **The check is an independent re-fetch + byte-compare**, not a judgement call.
  Resolve the candidate sequence's source to a *machine-fetchable* identifier — a
  UniProt/NCBI accession, an Addgene/iGEM/SEVA registry id, or a supplementary file
  — **fetch it through a second path**, and byte-compare (normalized case/whitespace)
  to the sequence we will store. Equal → record `provenance.sequence_source` with
  that identifier. Not equal → **stop and report the diff**; never store the
  unverified sequence.
- **Free-text-only sources** (a sequence printed in a paper figure with no fetchable
  accession) cannot be byte-verified automatically. Mark them
  `sequence_source` + a low `confidence` and **surface them to the human** as
  needing manual confirmation — do not silently treat "an agent transcribed it" as
  verified.
- **Candidate/validated re-verify** uses the *recorded* `provenance.sequence_source`
  as the identifier to re-fetch, so a candidate whose provenance has rotted (dead
  accession, sequence drift) is caught on the next `/add-part` pass.

### Unresolved sources → a human second pass (the access wall is the real bottleneck)

Sourcing a synthetic-biology part's sequence routinely hits **access walls**, not
research dead-ends. A live `/add-part` run on the cumate promoter (2026-06-15) was
blocked at *every* canonical source: `parts.igem.org` returned **403** to automated
fetch (HTML *and* the XML API); Addgene gates full sequences behind **login**; the
*Nat Chem Biol* Marionette paper (PMID 30478458) is **paywalled with no PMC copy**;
the open-access MIT DSpace mirror returned **405**. Web search yielded only the CuO
operator *consensus* and the −35/−10 *consensus* — not a coordinate-defined, citable
full promoter. The run correctly **stopped** rather than assemble a sequence from
motifs + memory.

The decision this grounds: **more agents don't defeat a paywall.** The deep
multi-agent workflow (Part A) would hit the identical wall, so the highest-leverage
investment here is a **human-in-the-loop document handoff**, not research
parallelism. The engine must therefore treat "couldn't access" as a *first-class,
resumable state*:

1. **Stop at the sourcing gate** (the existing "never from memory" rule) and emit a
   structured **`unresolved_sources`** report — each blocked source as
   `{ url_or_id, would_unblock, barrier: 403|login|paywall|not-in-pmc|405, tried[] }`,
   alongside what it *did* obtain (the citation, any consensus motifs).
2. **A human provides the documents** — paste the sequence, attach the supplementary
   PDF/table, give a local file path, or an Addgene/SnapGene export.
3. **Second pass:** re-run with the provided docs as a *trusted local source*,
   byte-verify the sequence against them, and set `provenance.sequence_source` to
   cite the human-supplied document (e.g. `"Meyer 2018 Suppl. Table 3, provided by
   curator 2026-06-15"`), then proceed normally.

`provenance.sequence_source` already accommodates a human-provided citation; the new
surface is the `unresolved_sources` block + a `--docs` second-pass entry on the
command. This also subsumes the earlier "free-text-only source → flag for human"
case: both are the same handoff.

*Implemented (the on-disk handoff surface): the agent writes its needs to
`sourcing/REQUESTS.md` (link · what it unblocks · barrier · save-as filename) and
stops; the human drops documents in `sourcing/incoming/` (gitignored — provided
PDFs/sequences stay local); on resume the agent reads `incoming/`, byte-verifies, and
cites the provided file in `provenance.sequence_source`. See `sourcing/README.md`.
The structured `unresolved_sources` JSON block remains for the eventual workflow
engine to emit programmatically.*

### Guard loop (the "thin" command can't fix prose — the engine must)

The command does no research, so it **cannot** repair a `check_content.py` failure
on synthesized notes (repair = re-synthesis = the engine's job). Therefore:

- Synthesis prompts carry the guard's rules (lab-/tool-agnostic, no
  definition-by-negation), **and** the workflow runs a final guard-clean self-check
  pass on its own emitted prose/notes and re-synthesizes on failure, so what it
  returns is already clean.
- The command still runs `check_content.py` as the enforcing gate (the guard, not
  the prompt, is the source of truth). On the rare residual failure the command
  **kicks the part back to the workflow**, it does not hand-edit prose to pass.

**Keep** (the good bones): the phase structure, model tiering (cheap workers,
top-model synthesis), the **adversarial coord + citation verification**, the
**cluster research-sharing** (what makes batch cheap), and the `collection` block
(maps straight to `collections.json`). Coordinates stay **0-based** `start`/`end`
(matches the `.json` features).

**Lives at:** `.claude/workflows/annotate-part.js` (this repo).

## Part B — slim `/add-part` to a triaging orchestrator

Rewrite `.claude/commands/add-part.md` to:

1. **Dedup + classify** each name + synonyms against `catalog.json` / `parts/` →
   **new | candidate | validated** (axis 1). This *is* the existence check; its
   result drives Source behavior and the merge policy.
2. **Classify structure** (axis 2): DNA-with-geometry? cluster? protein/CDS? This
   selects which engine machinery fires — never whether verification runs.
   - Default is the **full engine**; the engine scales down on its own when Locate
     or cluster-sharing isn't needed.
   - **State the chosen axes and why** for each part; the user can override.
     ("Self-decide" = "classify and tell me," never "quietly skip verification.")
3. Fire the workflow (single or cluster); take the verified per-part record(s).
4. **Merge / write** per axis 1:
   - new → `tools/new_part.py` + edits → `parts/candidate/<slug>.json`.
   - candidate/validated → **additive merge** into the existing `.json`: never
     overwrite or downgrade a claim with `review_status` ≥ `ai-cross-checked`; add
     superseding claims instead; never touch a validated part's curated `.md`.
   - run `tools/import_uniprot_features.py <slug>` for coding parts; write `.md`
     only when also authoring curated prose (→ validated).
5. **Run every gate and make them pass:** `validate_parts` · `build_gb` ·
   `build_catalog` · `build_rdf` · `check_content` · `pyshacl -s tools/shapes.ttl -i
   rdfs catalog.ttl` · `pytest tests/ -q`. A `check_content` failure goes **back to
   the workflow** (see *Guard loop*), not into hand-edited prose.
6. **Show** a per-part summary (status: new/candidate/validated · sourced-from +
   verify result · N sub-features · confidence · which claims were preserved vs
   added) and the new/changed `.json` (+ `.md`); commit only when asked. For a
   **batch**, summarize per part so review scales; a cluster also yields a
   `collection`.

Add `Workflow` to the command's `allowed-tools`.

## The additive merge — specified (implemented: `tools/merge_part.py`)

Step-4's candidate/validated merge is where a machine re-run can silently destroy
human-reviewed knowledge, so the policy is specified once and lives in one tested
place: `tools/merge_part.py` (a pure `merge_records(existing, proposed)` plus a
**dry-run-by-default** CLI). The workflow proposes; this is the only thing that
writes claims into an existing record.

**Trust order.** `ai-generated (0) < ai-cross-checked (1) < expert-reviewed (2)`.

**Claim identity = `id`.** The schema makes `functional_claims[].id` a "stable id
unique within the part"; the workflow reuses **type-derived stable ids** (`inducer`,
`repression_dynamic_range`, … exactly as `PphlF.json` does) so a re-run's claims
line up with the prior pass by id. Two claims are *content-equal* when
`(type, label, value, source)` match.

**Per proposed claim P, matched to existing E by `id`:**

- **no E** → **add** P (new knowledge) — unless P is content-equal to some existing
  claim (its id drifted) → **drop** as a duplicate.
- **E is `ai-generated`** (rank 0, machine-only, never human-touched) → **overwrite**
  E with P. The fresh extraction wins; this is the ordinary re-run case.
- **E is `ai-cross-checked`/`expert-reviewed`** (rank ≥ 1, human-touched) → **E is
  immutable.**
  - P content-equal to E → **drop** P (E already asserts it, at higher trust).
  - P differs → P is a *proposed correction*: **append** it as a new claim with a
    fresh unique id (`<id>__v2`, …) and `supersedes = E.id`, **flagged** for human
    review. E is never mutated.

So a machine merge **only ever overwrites an `ai-generated` claim**; against any
reviewed claim it can append a flagged, superseding proposal but cannot change it.
Promoting a claim to `expert-reviewed` stays a direct human edit, never a merge.

**Surrounding fields (conservative by default):**

- `sequence` — must be identical; a mismatch is a **hard error** (`MergeError`). A
  merge must never rewrite a stored, sourced sequence — the Source phase owns
  sequence changes.
- `provenance.sequence_source` — never silently overwritten; a differing proposed
  value is parked under `sequence_source_proposed` and flagged.
- `references` — **union** (key on pmid, else the `doi:` in `comment`, else title).
- `features` — **kept by default**; a differing proposal is reported for deliberate
  application (`--replace-features` to opt in), so curated DNA sub-feature geometry
  isn't clobbered.
- record-level `review_status` — `max` by rank; **never downgraded**.

**Report.** `merge_records` returns `(merged, report)`; the report enumerates claims
`added` / `overwritten` / `preserved` / `flagged_superseding` / `dropped_duplicate`
and any `flags` (sequence/provenance/feature conflicts). That report *is* the
per-part review the command shows in Part B step 6.

## Trade-offs / decisions for the implementer

- **Cost — batch ≠ cluster.** Shared research only amortizes within a *related
  cluster* that shares a source. `/add-part A, B, C` for **unrelated** parts is N
  full engine runs with no amortization. Wire the token budget as a **per-part
  floor**, not just a global batch ceiling, or early parts will starve later ones.
  The engine-scales-down rule keeps trivial parts cheap without a verification
  bypass.
- **Review gate:** keep the workflow **proposal-only**; the command merges after
  showing you. Don't let the workflow write files directly.
- **Merge safety is the new correctness surface.** Re-running on a candidate/
  validated part must be **additive and monotonic in `review_status`**: an
  `ai-generated` re-run may add or `supersede`, but must **never** overwrite or
  downgrade an `ai-cross-checked`/`expert-reviewed` claim or a curated `.md`. For a
  KB whose value is `ai-generated → ai-cross-checked → expert-reviewed`
  self-correction, clobbering reviewed content is the worst failure mode — guard it
  with a test (phasing step 6).
- **Source verification is the other correctness surface.** Independent re-fetch +
  byte-compare; never "an agent agreed with the figure." Free-text-only sources are
  flagged for human confirmation, not auto-blessed.
- **Two diverging workflows.** Keep the seqmake-flavored `annotate-part` too — it
  keeps the lab-registry extend/truncate hint for seqmake-side work. The two **will
  diverge** (public-KB authoring here vs lab-aware annotation in seqmake); accept
  the fork explicitly rather than expecting the ~750-line files to stay in sync. If
  the coord/citation-verify helpers prove stable, factor those few shared bits;
  don't try to share the phase bodies.

## Suggested phasing (keep all gates green at each step)

1. **Engine, candidate-verify mode.** Port the workflow into this repo,
   lab-agnostic, emitting `part.schema.json`, reading `parts/<status>/<slug>.json`.
   Prove it by **re-verifying + re-annotating an existing candidate** end-to-end
   (e.g. a DNA regulatory part): re-fetch its recorded source, byte-compare,
   re-locate sub-features, → schema-valid JSON that passes every gate. *(This is
   axis-1 = candidate.)*
2. **Source phase — new parts.** Add discover + **independent re-fetch/byte-compare**
   verification → `provenance.sequence_source`; flag free-text-only sources for human
   confirmation. *(axis-1 = new.)*
2b. **Unresolved-source handoff + second pass.** When sourcing is access-blocked,
   emit the `unresolved_sources` report and stop; accept human-provided docs (or
   credentials, e.g. an Addgene token) and re-run (`--docs`) to finish, byte-verifying
   against and citing the provided document in `provenance.sequence_source`.
3. **Protein/UniProt path.** Accession resolution + UniParc variant logic; hand off
   residue features to `import_uniprot_features`. *(axis-2 = CDS.)*
4. **Functional claims + additive merge.** Emit nanopub-shaped claims with honest
   `review_status`/`confidence` and granular sources; implement the
   review-status-monotonic merge.
5. **Guard loop.** Workflow self-checks `check_content` rules and re-synthesizes;
   command kicks residual failures back rather than hand-editing.
6. **Rewire `/add-part`.** Two-axis triage + drive workflow + merge/write + gates;
   single and **batch**. *(Partly done: the command now classifies new vs
   candidate/validated and merges into existing records via `tools/merge_part.py`
   — protecting reviewed claims; still single-agent research. Driving the
   multi-agent workflow + batch remain.)*
7. **Tests.** The workflow's JS coord/citation checks; a generated part passes all
   gates; **a re-run does not downgrade an `expert-reviewed` claim or overwrite a
   validated `.md`** (merge-safety); a source-mismatch **fails** rather than stores;
   a batch/cluster test.

## Pointers

- This repo: `.claude/commands/add-part.md` · `AUTHORING.md` ·
  `schema/part.schema.json` · `tools/{new_part,merge_part,import_uniprot_features,validate_parts,build_gb,build_catalog,build_rdf,check_content}.py` · `tools/shapes.ttl`
  (`merge_part.py` + `tests/test_merge_part.py` are done — the rest is pending.)
- Source to port: `~/seqmake/.claude/workflows/annotate-part.js` (phase structure,
  schemas, model tiering, adversarial verify, cluster sharing, collection block).
- Work from a **catalog-rooted session** with a catalog venv (`requirements.txt`).
