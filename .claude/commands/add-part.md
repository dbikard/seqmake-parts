---
description: Research, annotate and add or improve a DNA part in the catalog (canonical JSON + optional curated prose), merging safely into existing records, then validate and build.
argument-hint: <part name> [feature type]
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

You are adding or improving a part in this DNA parts catalog. Follow the standard
operating procedure in @AUTHORING.md exactly; it is the source of truth for the
rules and the record format (@schema/part.schema.json).

Part to add/improve: **$ARGUMENTS**

Work through the SOP and do not skip the hard rules — most importantly:

- **The sequence must come from a cited source, never from memory.** Find it in a
  primary paper or a registry (Addgene / iGEM / SEVA / UniProt / NCBI) and record
  exactly where in `provenance.sequence_source`. If you cannot source the
  sequence, stop and report that — do not invent or recall one.
  - **If a needed source is access-blocked** (paywall / login / 403 / 405), do not
    guess: append it to `sourcing/REQUESTS.md` (link · what it unblocks · barrier ·
    the filename to save it as) and stop. On resume, read the human-provided docs
    from `sourcing/incoming/`, **byte-verify** the sequence against them, and cite
    the provided file in `provenance.sequence_source`. See `sourcing/README.md`.
- Keep prose **lab- and tool-agnostic** (`tools/check_content.py` enforces this).
- Type the part and sub-features with **Sequence Ontology** terms.
- **Protein/CDS parts defer biology to UniProt:** stamp a required `UniProt:…`
  (or `NCBI:…`) accession and do NOT hand-author residue-level features (domains,
  active sites, binding residues, PTMs). Instead run
  `python tools/import_uniprot_features.py <slug>` to import them from UniProt
  (cached + provenance, baked into the `.gb`). Only hand-author the engineering
  layer (role, functional_claims, cognate partners). If the sequence is only a
  close variant of the accession, the importer normalizes it to UniProt's
  canonical sequence — unless it's an intentional functional variant (e.g. dCas9),
  in which case set `variant_rationale` to keep it.
- Every `functional_claim` cites its evidence (PMID/DOI + a verbatim quote and,
  when you have actually read it, a figure/table locator). Never fabricate a
  figure number. Mark `quote_source: primary` vs `catalog-doc` honestly, and set
  `review_status: ai-generated` and an honest `confidence`.

Concretely:

1. **Classify first (dedup → new vs existing).** Search `catalog.json` / `parts/`
   for the name and its synonyms, and run `python tools/catalog_overlap.py --slug
   <slug>` (or `--seq`) to catch **sequence** overlap with existing parts.
   - **Not present → a new part.** Author it directly (steps 2–3a). But if a
     *different* part's sequence overlaps yours (a sub/superset or a boundary variant
     of the same element), **refine that part** instead of adding a near-duplicate.
     Re-delimiting a boundary is **not** a trivial sequence call — it should rest on
     experimental data (truncation / mutational scanning / genetics); if you only have
     consensus/alignment support, set a lower `confidence` and seek the defining paper
     (use it, or add it to `sourcing/REQUESTS.md`).
   - **In `parts/candidate/` → a candidate**, or **in `parts/validated/` (has a
     `.md`) → validated** → you are *improving* an existing record. Do **not**
     hand-edit its `functional_claims` in place; use the safe additive merge
     (step 3b). A fresh AI pass must never clobber a human-reviewed claim.

2. **Research + source.** Run `python tools/source_finder.py --slug <slug>
   [--refs <canonical accessions>]` (background it — the NCBI BLAST is queued) to find
   the **oldest reputable 100% deposited source** and a **divergence** report vs
   canonical references; a **protein** part gets its UniProt source directly. Act on
   the divergence (per AUTHORING.md): cite a 100% canonical deposit; **refine** an
   internal diff to the canonical reference, or carry a common/old variant as a
   **labelled sibling** part (`ColE1_AT`-style) with a `sequence_variant` claim; an
   **edge** diff is a boundary fix. Collect the key references (PMID/DOI).

3a. **New part — author directly.** Scaffold with `tools/new_part.py` (see
   AUTHORING.md for flags), then edit the resulting `<slug>.json` to add
   sub-features, references, `provenance.sequence_source`, and functional_claims.
   When the record clears the **completeness bar** (sourced provenance, SO-typed
   main feature, located sub-features, ≥1 reference, ≥1 functional_claim) — i.e. a
   normal researched run — make it **validated**: also write the curated
   `parts/validated/<slug>.md` (Origin / Properties / Use / References) and place the
   `.json` there. Leave it a **candidate** only when the part is genuinely bare (a
   sourced sequence + minimal info). `tools/validate_parts.py` enforces the bar.

3b. **Existing part — propose + merge (never overwrite reviewed claims).**
   - Write a *proposed overlay* JSON to a temp file (e.g. `/tmp/<slug>.proposed.json`,
     not committed) carrying **only what you're contributing** for this slug — do
     not copy the whole record. Typically `functional_claims` (reuse **stable
     type-derived ids** so a re-run lines up by id: `inducer`,
     `repression_dynamic_range`, `host_range`, …), any new `references`, and
     `provenance` updates. Include `features` only if you are deliberately
     re-annotating, and `sequence` only if you mean to assert it matches.
   - **Dry-run the merge and read the report:**
     ```bash
     python tools/merge_part.py --into parts/<status>/<slug>.json --proposed /tmp/<slug>.proposed.json
     ```
     `tools/merge_part.py` enforces the contract: an `ai-generated` claim is
     overwritten by your fresh one; an `ai-cross-checked`/`expert-reviewed` claim is
     **immutable** — a *differing* proposal is appended as a flagged `<id>__v2`
     claim that `supersedes` it (surface every `flagged_superseding` to me), an
     identical one is dropped. References are unioned; `provenance.sequence_source`
     is never silently overwritten; a **sequence mismatch is a hard error** (fix the
     sourcing, don't force it); `features` are kept unless you pass
     `--replace-features`.
   - When the report looks right, persist with `--write`. For a **validated** part,
     never touch the `.md` — improving prose stays a human act.

4. **Coding parts:** run `python tools/import_uniprot_features.py <slug>` after the
   JSON is written/merged.

5. **Run every gate and make them pass:** `tools/validate_parts.py`,
   `tools/build_gb.py`, `tools/build_catalog.py`, `tools/build_rdf.py`,
   `tools/check_content.py`, `pyshacl -s tools/shapes.ttl -i rdfs catalog.ttl`,
   and `pytest tests/ -q`.

6. **Show me** the new/changed `<slug>.json` (and `.md` if any). For an existing
   part, also show the **merge report** (added / overwritten / preserved /
   flagged_superseding) and call out anything that needs my review, plus a summary
   of what you sourced and from where, before committing. Do not open a PR unless I
   ask.

If anything is ambiguous (which sequence variant, which feature type, conflicting
literature), ask me rather than guessing.
