# Proposal: unify `/add-part` + a research workflow into one researched-authoring capability

**Status:** proposal / not yet implemented. Pick this up from a session rooted in
this repo.

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
  proposal-only — but it is **proposal-only**, **seqmake-coupled** (`load_library()`
  + a lab-registry boundary scan), and speaks the **pre-weekend** `.gb`-centric
  data model, not this repo's JSON-canonical contract.

The result: `/add-part` can't produce a *well-researched* part because it doesn't
do the deep research, and the deep research engine can't author into this repo.

**Goal:** one capability — `/add-part` always yields well-researched, *verified*
parts, supports **batch**, and is fully self-contained in this repo (no seqmake
dependency).

## Design — layer, don't merge

One user command on top of one research engine:

```
/add-part  A, B, C                       ← catalog slash command (thin orchestrator)
   │  triage per part/batch (quick vs deep; default deep; state choice; overridable)
   ├─ deep → fires the catalog-native annotate workflow (batch/cluster-aware)
   │           Source → Research → Locate → Verify(coords+citations) → Synthesize→schema
   │           returns per-part VERIFIED records (sourced seq + provenance,
   │           located sub-features, checked PMIDs, drafted claims) + a collection block
   │  quick → single-agent source+annotate (narrow, trivial cases only)
   │
   └─ then (deterministic, human-in-the-loop): write each <slug>.json ·
        import_uniprot_features for coding parts · run every gate · show a
        per-part summary · commit on request
```

- **The command is thin**: it triages, drives the engine, and *writes + validates*.
  It does **no** research of its own.
- **The workflow is the single research/verify engine**, proposal-only (never
  writes — preserves the human review gate, which matters for an AI-generated
  public KB). It is **cluster-aware**, so **batch is native**: one shared research
  pass across a related set, fan-out per part, and a `collection` falls out.

## Part A — refactor the workflow to this repo's contract (the bulk of the work)

This is an **alignment to the new canonical model**, not a line-by-line port; reuse
the seqmake workflow's proven *structure* but re-target its schemas and phases.

| Today (seqmake `annotate-part`) | Target (catalog-native) |
|---|---|
| Resolves a part via seqmake `load_library()` | reads this repo's canonical `parts/<status>/<slug>.json` (or, for a brand-new part, nothing to resolve) |
| Assumes the sequence already exists | adds a front **Source** phase: find the sequence in a cited paper/registry and **adversarially verify it matches the source**, emitting `provenance.sequence_source` (the "never from memory" rule, machine-checked) |
| Emits `FINAL_SCHEMA` + `report_markdown` | emits a record shaped by **`schema/part.schema.json`**: `features[]` (+ qualifiers, SO `db_xref`, `citation`), `references`, `provenance.sequence_source`, and `functional_claims[]` in the nanopub shape (`source`{quote, quote_source, figure/table/page}, `provenance`{method, agent}, `confidence`, `review_status: ai-generated`, `supersedes`) |
| Hand-researches protein domains | **defers protein biology to UniProt**: resolve the accession (+ UniParc variant logic per `AUTHORING.md`), do **not** hand-author residue features; the skill runs `tools/import_uniprot_features.py` after writing. The workflow only researches the **engineering layer** (role, functional_claims, cognate partners, collections) |
| Has a lab-registry boundary scan | **drop it** — it reads lab plasmids, which must not inform a public KB |
| Unaware of the content guard | **bake `tools/check_content.py`'s rules into the synthesis prompts** (lab-/tool-agnostic, no definition-by-negation) so the emitted `.json`/notes pass the guard (which now scans `.json` too) |

**Keep** (the good bones): the phase structure, model tiering (cheap workers,
top-model synthesis), the **adversarial coord + citation verification**, the
**cluster research-sharing** (what makes batch cheap), and the `collection` block
(maps straight to `collections.json`). Coordinates stay **0-based** `start`/`end`
(matches the `.json` features).

**Lives at:** `.claude/workflows/annotate-part.js` (this repo).

## Part B — slim `/add-part` to a triaging orchestrator

Rewrite `.claude/commands/add-part.md` to:

1. **Dedup-check** the name(s) + synonyms against `catalog.json` / `parts/`.
2. **Triage** each part (or the batch) — *conservative, transparent, overridable*:
   - **Deep (fire the workflow):** DNA regulatory part with internal structure to
     locate (−35/−10/operator/+1), overlapping/divergent architecture, a **related
     cluster**, uncertain sourcing, or conflicting literature.
   - **Quick (single-agent):** the sequence is **already in hand** *and* there's no
     sub-feature geometry to pin — or a **protein/CDS** part where UniProt import
     does the residue biology, so the only research is the right accession + the
     claims.
   - Default deep; **state the chosen path and why**; the user can override and set
     the bias. ("Self-decide" = "triage and tell me," never "quietly skip
     verification.")
3. Run the chosen path; take the verified per-part record(s).
4. **Write** each `parts/<status>/<slug>.json` (via `tools/new_part.py` + edits);
   run `tools/import_uniprot_features.py <slug>` for coding parts; write `.md` only
   when also authoring curated prose (→ validated).
5. **Run every gate and make them pass:** `validate_parts` · `build_gb` ·
   `build_catalog` · `build_rdf` · `check_content` · `pyshacl -s tools/shapes.ttl -i
   rdfs catalog.ttl` · `pytest tests/ -q`.
6. **Show** a per-part summary (sourced-from · N sub-features · confidence) and the
   new `.json` (+ `.md`); commit only when asked. For a **batch**, summarize per
   part so review scales; a cluster also yields a `collection`.

Add `Workflow` to the command's `allowed-tools`.

## Trade-offs / decisions for the implementer

- **Cost:** firing a multi-agent workflow per add is heavier than today's
  single-agent path. That's the right default for a provenance-tracked KB, and
  **batch amortizes** the shared research. Keep the quick path for genuinely trivial
  parts. The workflow has a token-budget mechanism — wire a sensible per-batch
  ceiling.
- **Review gate:** keep the workflow **proposal-only**; the command writes after
  showing you. Don't let the workflow write files directly.
- **Self-triage overconfidence** is the main risk — a single agent calling its own
  work "trivial" is exactly what the deep path guards against. Mitigate with narrow
  quick-path criteria + the "state the choice" rule + a user-set bias.
- **Keep the seqmake-flavored `annotate-part` too?** Probably yes — it keeps the
  lab-registry extend/truncate hint for seqmake-side work. The two diverge: public
  KB authoring (this repo) vs lab-aware annotation (seqmake).

## Suggested phasing (keep all gates green at each step)

1. **Engine, existing-part mode.** Port the workflow into this repo, lab-agnostic,
   emitting `part.schema.json`. Prove it by **re-annotating an existing part**
   end-to-end (e.g. a DNA regulatory part) → schema-valid JSON that passes every
   gate.
2. **Source phase.** Add new-part sequence sourcing + adversarial source-match
   verification → `provenance.sequence_source`.
3. **Protein/UniProt path.** Accession resolution + UniParc variant logic;
   hand off residue features to `import_uniprot_features`.
4. **Functional claims.** Emit nanopub-shaped claims with honest
   `review_status`/`confidence` and granular sources.
5. **Rewire `/add-part`.** Triage + drive workflow + write + gates; single and
   **batch**.
6. **Tests.** The workflow's JS coord/citation checks; a test that a generated
   part passes all gates; a batch/cluster test.

## Pointers

- This repo: `.claude/commands/add-part.md` · `AUTHORING.md` ·
  `schema/part.schema.json` · `tools/{new_part,import_uniprot_features,validate_parts,build_gb,build_catalog,build_rdf,check_content}.py` · `tools/shapes.ttl`
- Source to port: `~/seqmake/.claude/workflows/annotate-part.js` (phase structure,
  schemas, model tiering, adversarial verify, cluster sharing, collection block).
- Work from a **catalog-rooted session** with a catalog venv (`requirements.txt`).
