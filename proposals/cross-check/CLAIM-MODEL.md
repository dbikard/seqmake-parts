# Claim model — confidence, usefulness, type, and autonomous correction

Decided direction for how `functional_claims` are scored, typed, and self-corrected. Supersedes the
three-tier `review_status` ladder. Companion to [`FINDINGS.md`](FINDINGS.md) (the prototype evidence).

## Why the old model was wrong

The single `review_status` enum (`ai-generated → ai-cross-checked → expert-reviewed`) conflated two
orthogonal things and depended on a human tier nobody would fill. We're dropping the human tier entirely
(no human in the loop) and splitting the rest into **independent axes the cross-check agent scores**:

| Axis | Question | Values |
|---|---|---|
| **confidence** | How well-supported by the cited primary source? | low / medium / high |
| **usefulness** | How much does it help a designer choose/operate this part? | low / medium / high |
| **claim_type** | What *kind* of assertion is it? | controlled vocabulary (`schema/claim_types.json`) |

`review_status` is **retired**. A claim instead carries `cross_checked` (verified against a read source,
with a timestamp) + `confidence` + `usefulness` + an optional `comment`. There is no expert stamp.

These axes are genuinely orthogonal: a claim can be **true-but-useless** (`"MBP is a maltose-binding
protein"` — certain, zero information) or **useful-but-shaky** (a quantitative caveat from one paper).
Folding usefulness into confidence would destroy both signals.

## Usefulness — anchored in the part datasheet

A claim is **useful to the degree it fills a datasheet slot a designer consults to choose or operate the
part** (the "datasheet" framing: Canton, Labno & Endy 2008, *Refinement and standardization of synthetic
biological parts and devices*, Nat Biotechnol 26:787). Criteria:

- **Selection-relevant** — would someone pick this part over an alternative *because of* it? (comparative/discriminating)
- **Operationally actionable** — a parameter you set or use (inducer + concentration, Kd, dynamic-range fold, copy number, protease/site, host, conditions)
- **Specific / quantitative** over vague
- **Non-redundant** with the part's own description and structured `features`/`uniprot_features`
- **Risk-reducing** — caveats and failure modes are **high** usefulness

**Low-usefulness anti-patterns** (the checker flags/deprecates these): **tautological** (restates the
part's identity), **generic-to-class** ("is a fusion tag", "used in E. coli"), **historical/bibliographic**
("sequenced in 1984"), **unfalsifiable/vague** ("is robust").

Scored `{high, medium, low}` + a one-line `usefulness_rationale`, mirroring `confidence` + comment.
Routing: low-usefulness **and** low-confidence → deprecate-with-comment; high-usefulness **but** unverified
→ prioritise for the paper-store fetch (`tools/papers.py coverage`).

## Claim ontology — a controlled, decision-oriented vocabulary

The old `type` field was uncontrolled free text and had already drifted: `affinity` / `binding_affinity` /
`affinity_binding`; `strength` / `strength_class`; one-off `induction_dynamic_range` + `repression_dynamic_range`;
plus mis-types (`S-tag/detection_sensitivity` was typed `strength`). 27 strings, much redundancy.

`schema/claim_types.json` replaces it with a **flat controlled vocabulary**, organized by the **datasheet
section** a designer consults and tagged with the **part classes** each type applies to. Sections:
Regulation & control · Performance · Interaction & affinity · Processing & modification · Composition &
structure · Context & deployment · Selection & replication · Caveats & limitations · Identity & origin.
`datasheet_slot: true` marks types that fill an operational parameter — a structural prior for usefulness.

- **Enforced now:** `validate_parts.py` rejects any claim `type` not in the vocabulary. Every historical
  string is registered as a canonical type or an `alias`, so existing data passes (261 files clean) while
  **new drift is impossible**.
- **Re-typing:** the cross-check agent assigns the correct canonical `claim_type` per claim (fixing
  mis-types); aliases are the bulk grandfather, the agent does the intelligent per-claim correction.
- **Later:** promote to a published SKOS scheme at `w3id.org/seqmake/claim-types` once stable — consistent
  with how SO/ChEBI are already used and with the existing RDF projections.

## Autonomous correction (no human in the loop)

The cross-check agent **corrects what it confidently can and annotates the rest** — git is the only undo, so
the guardrail is *never destroy, always supersede*, and *converge across passes* rather than be right once.

Three properties keep it safe:
1. **Corrections supersede, never overwrite.** A content correction writes a *new* claim that `supersedes`
   the old (old retained, flagged). Nothing is lost; the change is auditable in the data, not just in git.
2. **Every correction carries its own primary quote** (gated by `shapes.ttl`), so it is itself a checkable
   claim — the *next* pass re-verifies it. The system self-heals over passes.
3. **Autonomy bounded by change kind**, via `correction_action`:

| `correction_action` | When | Effect |
|---|---|---|
| `none` | confirmed & clean | — |
| `fix_metadata` | replace a self-referential quote with the real primary one; re-point a wrong citation to the correct paper **already in the part's refs** | in-place metadata fix (reversible) |
| `supersede` | confident the content is over-stated/wrong and the correct form is known | new claim supersedes old; old retained |
| `downgrade_comment` | suspected problem, can't confidently rewrite | keep claim, lower `confidence`, attach the `uncertainty_note` as a comment |

The cross-check engine (`.claude/workflows/cross-check.js`) emits `correction_action` + `proposed_change`
per claim. The **applier** (`tools/apply_cross_check.py`, next build) executes them against the part JSONs,
then runs the standard gates (`validate_parts` · `build_*` · `pyshacl` · `pytest`).

## Status

- **Built:** controlled vocabulary + validator enforcement; cross-check engine scores all three axes and
  proposes corrections; local paper store (`tools/papers.py`) so paywalled full text + figures are verifiable.
- **Next:** `tools/apply_cross_check.py` (the autonomous applier), then a full-corpus pass.
