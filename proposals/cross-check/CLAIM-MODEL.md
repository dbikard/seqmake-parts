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

`review_status` is **retired** (removed from `schema/part.schema.json`, all 273 records, the RDF
projection, SHACL, the site, and the merge ladder — `tools/migrate_claim_model.py`). A claim instead
carries `cross_checked` + `confidence` + `usefulness` + an optional `comment`, plus the verification
**lifecycle** below. There is no expert stamp.

These axes are genuinely orthogonal: a claim can be **true-but-useless** (`"MBP is a maltose-binding
protein"` — certain, zero information) or **useful-but-shaky** (a quantitative caveat from one paper).
Folding usefulness into confidence would destroy both signals.

## Verification lifecycle — `analysis_status`

`cross_checked` is a boolean, but a claim's *state* needs four values — crucially one for "a pass ran
but couldn't reach the source yet", which is distinct from "verified false" and from "not looked at".
Every claim carries `analysis_status` (with `cross_checked` = `analysis_status == "verified"`) and a
`last_checked` date:

| `analysis_status` | Meaning | Set by |
|---|---|---|
| `pending` | authored, source was reachable, **not yet independently cross-checked** | annotate-part (fresh claim) |
| `verified` | cross-checked against the **primary** source and supported (earns the trust marker) | cross-check |
| `sources-pending` | a pass needed the primary source but **couldn't access it** → a `sourcing/REQUESTS.md` entry is filed | annotate-part **or** cross-check |
| `flagged` | source was read but the claim is partially-supported, downgraded, or superseded (see `comment` / `supersedes`) | cross-check |

`sources-pending` is **shared by both engines** — a freshly authored claim whose paywalled primary
annotate-part couldn't read, and a claim cross-check couldn't reach, are the same state and unblock by
the same `/open-requests` → `/incoming` → re-run loop. The request is filed through `tools/papers.py
request` (store-aware + self-pruning), so the **only** human step in the whole pipeline is fetching a
paywalled PDF.

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
per claim. The **applier** (`tools/apply_cross_check.py`) executes them against the part JSONs:
`fix_metadata` upgrades a self-referential quote to the verbatim primary one and re-points wrong
citations; `supersede` writes the corrected `<id>__v2` (carrying its own primary quote, `supersedes` the
old) and flags the old as `superseded_by`; `downgrade_comment` lowers confidence + attaches the note; an
unreachable source routes to `sources-pending` + a filed request. A supersede whose correction can't be
parsed cleanly **falls back to `downgrade_comment`** rather than write a guess. Dry-run by default;
`--write` applies, then the caller regenerates artifacts + runs the gates (`tools/check_all.py`).

## The autonomous loop

```
/cross-check <slugs>                      # workflow → verdicts (read-only, blind to prior scores)
python tools/apply_cross_check.py --verdicts <file> --write   # verdicts → claims (verified / supersede / flagged / sources-pending)
python tools/check_all.py                 # validate · build_* · pyshacl · pytest
# any sources-pending → /open-requests → human fetches the PDF → /incoming → re-run /cross-check
```

The only human action is fetching paywalled PDFs; everything else is mechanical and gated.

## Status

- **Built:** controlled vocabulary + validator enforcement; cross-check engine scores all three axes and
  proposes corrections; local paper store (`tools/papers.py`); `review_status` fully retired and migrated
  to the `analysis_status` lifecycle; **`tools/apply_cross_check.py`** (the autonomous applier) + tests;
  the loop above wired into the cross-check workflow. First real pass applied over AviTag / birA /
  LPETG_tag / SnoopTag.
- **Next:** a full-corpus cross-check + apply pass; promote `claim_types` to a published SKOS scheme.
