# Cross-check prototype — findings

**What this is.** A prototype of the *earned* middle tier we discussed: instead of asserting
`ai-cross-checked`, an independent verifier agent re-derives each `functional_claim` from the
**actual cited source** (blind to the claim's original `confidence`/`review_status`), and renders a
fresh, skeptical verdict. Engine: `.claude/workflows/cross-check.js` (also exposed as the `cross-check`
skill). Run it with `args = ["<slug>", ...]`.

**Sample.** 21 claims across 6 parts (`tetR_tetA_promoters`, `MBP`, `6xHis`, `FLAG`, `T7lac`, `PtetA`)
— deliberately spanning primary-quoted and self-referential (catalog-doc) claims.

## Headline: the trust signal stopped being constant

| Axis | Before (authoring pass) | After (independent cross-check) |
|---|---|---|
| **review_status** | 21 `ai-generated` (100%) | **12 `ai-cross-checked` / 9 `ai-generated`** |
| **confidence** | high 16, medium 5 | high 13, medium 7, **low 1** |

- **57% of claims *earned* `ai-cross-checked`** — confirmed verdict, primary support, source actually read.
  The other **43% could not be earned** and correctly stayed `ai-generated`. The tier now carries information.
- **The check is bidirectional — it's calibration, not just demotion.** 8 claims moved *down*
  (over-confident), **5 moved *up*** (the authoring pass was too cautious): `MBP/expression_level`,
  `MBP/dimerization_caution`, `MBP/sequence_variant`, `FLAG/minimal_epitope`, `FLAG/sulfation_caveat`
  all went medium→high once strong primary support was found.
- **6 self-referential quotes caught** — claims that cite a PMID but whose "quote" is actually our own
  catalog doc's words, not the paper's.

## Real defects it surfaced (actionable, not cosmetic)

1. **`T7lac/regulation` — DISPUTED (wrong citation attached).** The claim (LacI/IPTG-controllable T7
   promoter) is biologically correct, but its attached source **PMID 10956032** is a T7-promoter-variant
   study that doesn't support it. The genuinely supporting paper (Dubendorff & Studier 1991, PMID 1902522)
   *is in the part's reference list* but isn't the source bound to this claim. A citation-attachment bug
   that no confidence score would ever have revealed.
2. **`MBP/ligand` — primary_support: false (wrong source for the claim).** Cites a 1984 *sequencing*
   paper (PMID 6088507) that never reports ligand binding, maltodextrins, or amylose affinity. The quote
   is verbatim — but it's only the paper's *title*. → dropped high→low.
3. **`6xHis/mechanism` — over-claim vs. source.** Claim lists 4 metal ions (Ni/Co/Cu/Zn) + imidazole/low-pH
   elution; the cited primary abstract names only Ni²⁺/Cu²⁺ and says nothing about elution. → high→medium.
4. **`FLAG/antibody_recognition` — sub-claims unsupported by the cited text.** M1 "requires free N-terminus"
   and M2 "position-insensitive" are not in the cited abstract (the asserted quote is just the title). → high→medium.
5. **`MBP/solubility_partner` — over-attribution.** Bundles a mechanism sub-claim whose wording actually
   comes from a *different* paper (PMID 23166722) that the catalog correctly cites under a separate claim.
6. **`PtetA/inducer`, `tetR_tetA_promoters/regulation`** — aTc-as-inducer / de-repression mode asserted with
   a self-referential quote; abstracts support the gist but not the asserted specifics verbatim. → high→medium.

## The uncertainty notes are the product

Every verdict carries a one-sentence `uncertainty_note` — exactly the "comment about the uncertainty"
you asked for, generated at scale. Examples verbatim from the run:

> *"The primary source (1983 abstract) names 'tetracycline' as the inducer, not the 'anhydrotetracycline (aTc)'
> asserted in the claim; aTc as inducer is later/background knowledge, not in PMID 6311683."*

> *"The cited primary abstract names only Ni²⁺ and Cu²⁺ (not Co²⁺ or Zn²⁺) and says nothing about
> imidazole/low-pH elution; those parts of the claim are unverified by this source."*

## Honest caveats (tuning, not blockers)

- **Access is the main confound.** Most verifiers reached *abstract_only* (PMC full text frequently
  unavailable); a few "partially_supported" verdicts reflect a paywall, not a wrong claim. The engine is
  conservatively correct here — it won't promote what it couldn't read — but a production version should
  separate *"unverifiable (access)"* from *"refuted"* so good claims aren't punished for paywalls. One PMC
  lookup hit an ID collision (returned an unrelated paper); the verifier noticed and fell back to the abstract.
- **Slightly harsh on titles.** It sometimes dings "the quote is only the title" even when title+abstract do
  support the claim. Right *direction* (skeptical), but worth softening.
- **Cost.** 21 claims ≈ 27 agents, ~727k tokens, ~3.3 min wall-clock. The full 147-claim corpus is ~7× that.

## What this proves for the design

- `ai-cross-checked` **can be a tier that is earned** by an independent, falsifiable process — not a stamp.
- Once earned, the label **varies and de-correlates from "default high,"** so a reader can act on it.
- The same pass yields **per-claim uncertainty comments** and **a queue of real defects** (wrong citations,
  over-claims) — which is exactly what a human expert would otherwise have to find by hand.

## Suggested next steps

1. Run the full 147-claim corpus to get a real calibration picture (one `cross-check` invocation, all slugs).
2. Add a `verdict` → JSON writer that sets `recommended_confidence`/`review_status` + stores the
   `uncertainty_note` on each claim — auto-applying upgrades, but **routing disputes/demotions to a human**
   (this is where the GitHub-issue / attestation flow plugs in).
3. Decide the schema change: split the single `review_status` enum into an *evidence* axis (this engine)
   and a *human-attention* `attestations[]` axis (drop `expert-reviewed` as a stamp).
