export const meta = {
  name: 'cross-check',
  description: 'Independently re-verify each functional_claim against its cited source; emit a fresh, skeptical verdict (confidence + status + uncertainty note). Earns the "verified" analysis_status (cross_checked) instead of asserting it.',
  whenToUse: 'To turn "verified" into a status that is earned: run over a part\'s (or several parts\') functional_claims to test whether each is actually supported by the primary source it cites. args = array of part slugs (defaults to a built-in sample). COMPLETE LOOP: after this returns, save the verdicts to a file and apply them autonomously — `python tools/apply_cross_check.py --verdicts <file> --write` — then regenerate + gate (`python tools/check_all.py`). Any unreachable source becomes analysis_status=sources-pending with a sourcing/REQUESTS.md entry; fetch those via /open-requests -> /incoming, then re-run. No human input is needed except fetching paywalled PDFs.',
  phases: [
    { title: 'Extract', detail: 'read each part, emit its claims blind to original confidence/status' },
    { title: 'Cross-check', detail: 'one independent verifier per claim' },
  ],
}

// args = array of validated-part slugs to cross-check. Defaults to a diverse sample.
const DEFAULT_SLUGS = ['tetR_tetA_promoters', 'MBP', '6xHis', 'FLAG', 'T7lac', 'PtetA']
let raw = args
if (typeof raw === 'string') { try { raw = JSON.parse(raw) } catch (e) { raw = null } }
const slugs = (Array.isArray(raw) && raw.length && raw.every((s) => typeof s === 'string'))
  ? raw
  : DEFAULT_SLUGS

// ---- Stage 1 schema: the stripped, agent-facing claim payload (NO confidence/usefulness/analysis_status/cross_checked) ----
const CLAIMS_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['part', 'claims'],
  properties: {
    part: { type: 'string' },
    claims: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['claim_id', 'claim_type', 'claim_label', 'asserted_source'],
        properties: {
          claim_id: { type: 'string' },
          claim_type: { type: 'string' },
          claim_label: { type: 'string' },
          claim_value: { type: 'object', additionalProperties: true },
          asserted_source: { type: 'object', additionalProperties: true },
        },
      },
    },
  },
}

// ---- Stage 2 schema: the independent verdict (three axes: evidence, usefulness, type) + correction ----
const VERDICT_SCHEMA = {
  type: 'object',
  additionalProperties: false,
  required: ['part', 'claim_id', 'claim_type', 'usefulness', 'usefulness_rationale',
             'source_accessed', 'quote_check', 'verdict', 'evidence_strength', 'primary_support',
             'recommended_confidence', 'cross_checked', 'correction_action',
             'uncertainty_note', 'evidence_quote', 'reasoning'],
  properties: {
    part: { type: 'string' },
    claim_id: { type: 'string' },
    // --- TYPE axis: assign the correct canonical claim_type from schema/claim_types.json ---
    claim_type: { type: 'string',
      description: 'the canonical claim_type this claim SHOULD have (re-type if the asserted type is generic/wrong, e.g. a "function"/"strength" mis-type)' },
    claim_type_changed: { type: 'boolean', description: 'true if claim_type differs from the asserted type' },
    // --- USEFULNESS axis (orthogonal to confidence): how decision-relevant is the claim? ---
    usefulness: { type: 'string', enum: ['high', 'medium', 'low'],
      description: 'how much the claim helps a designer choose or operate this part — independent of whether it is true' },
    usefulness_rationale: { type: 'string', description: 'one line: which datasheet slot it fills / or which anti-pattern makes it low (tautology, generic-to-class, historical, vague)' },
    // --- EVIDENCE axis ---
    source_accessed: { type: 'string',
      enum: ['full_text', 'abstract_only', 'metadata_only', 'inaccessible'],
      description: 'the most authoritative form of the cited source you actually read' },
    quote_check: { type: 'string',
      enum: ['verbatim_in_primary', 'paraphrase_supported', 'not_found_in_source',
             'self_referential', 'unverifiable'],
      description: 'self_referential = the asserted quote is the catalog\'s own words, not the paper\'s' },
    verdict: { type: 'string',
      enum: ['confirmed', 'partially_supported', 'disputed', 'unverifiable'] },
    evidence_strength: { type: 'string', enum: ['strong', 'moderate', 'weak', 'none'] },
    primary_support: { type: 'boolean',
      description: 'true ONLY if the primary cited source itself supports the claim (not a review, not the catalog doc, not your prior knowledge)' },
    recommended_confidence: { type: 'string', enum: ['low', 'medium', 'high'] },
    cross_checked: { type: 'boolean',
      description: 'true ONLY if verdict=confirmed AND primary_support=true AND you actually read the source — the claim is now independently verified' },
    // --- CORRECTION (autonomous; no human in the loop) ---
    correction_action: { type: 'string',
      enum: ['none', 'fix_metadata', 'supersede', 'downgrade_comment'],
      description: 'none=confirmed & clean; fix_metadata=safe metadata fix (replace self-referential quote with the real primary one, or re-point a wrong citation to the correct paper ALREADY in the part refs); supersede=you are confident the claim content should be narrowed/corrected (new claim supersedes old, old retained); downgrade_comment=cannot confidently rewrite, so keep claim, lower confidence, attach comment' },
    proposed_change: { type: 'object', additionalProperties: true,
      description: 'concrete edit for fix_metadata/supersede: e.g. {field:"source.pmid", from:"10956032", to:"1902522"} or {new_label, new_value, drop:["Co2+","Zn2+"]}. {} for none/downgrade_comment.' },
    uncertainty_note: { type: 'string', description: 'one sentence on what is shaky/unverifiable; "" if genuinely none' },
    evidence_quote: { type: 'string', description: 'verbatim sentence from the source you actually read; "" if none found' },
    reasoning: { type: 'string', description: '2-4 sentences: what you read and how you judged' },
  },
}

const LISTER_PROMPT = (slug) => `Read the file parts/validated/${slug}.json. Return its "functional_claims"
as a payload for downstream verification. For each claim emit ONLY: claim_id, claim_type (its "type"),
claim_label (its "label"), claim_value (its "value"), and asserted_source (its "source" object verbatim —
keep pmid/doi/url/quote/quote_source/figure/table/page/section).
CRITICAL: DO NOT include the claim's "confidence", "usefulness", "analysis_status", or "cross_checked" —
downstream verifiers must judge blind to what any prior pass already decided. Also set part="${slug}".
Do not read the .md file.`

const VERIFY_PROMPT = (c, slug) => `You are an INDEPENDENT verifier for a DNA/protein parts catalog. A prior AI pass
asserted the functional claim below and attached a source. Decide, from scratch, whether the cited PRIMARY
source actually supports it. You are NOT told what confidence the prior pass assigned — do not guess it.
Default to skepticism: an unverified claim is NOT confirmed.

PART: ${slug}
CLAIM (as asserted — treat every field as a hypothesis, including the quote):
${JSON.stringify(c, null, 2)}

PROCEDURE:
1. Load the source. FIRST check the LOCAL full-text paper store (it holds paywalled PDFs a human deposited):
     python tools/papers.py resolve --json --pmid <pmid> --doi <doi>
   If found, Read the returned txt path for full text (source_accessed=full_text). If NOT found, use ToolSearch
   to pull PubMed + web tools, e.g.
   ToolSearch "select:mcp__plugin_pubmed_PubMed__get_article_metadata,mcp__plugin_pubmed_PubMed__get_full_text_article,mcp__plugin_pubmed_PubMed__search_articles"
   and ToolSearch "select:WebFetch,WebSearch". Fetch by pmid, then doi/url, then a title search.
   Prefer full text; fall back to abstract; record what you actually reached in source_accessed.
2. Check the asserted quote. Is it verbatim in the PRIMARY paper? If asserted quote_source is "catalog-doc",
   that quote is the catalog's OWN words — NOT primary support; you must find support in the paper itself
   or mark quote_check=self_referential.
3. Judge the claim on the source you read — not on background knowledge. If the asserted_source names a
   FIGURE or TABLE (or the claim is quantitative/structural), do not trust the caption text alone — when the
   paper is in the local store, INSPECT the figure: find its page in the .txt, then
     python tools/papers.py render --pmid <pmid> --doi <doi> --pages <page>
   and Read the resulting PNG (or Read the PDF path from \`resolve --pdf\` at that page range). For a
   structural/sequence claim you may also re-derive from the part's sequence (read parts/validated/${slug}.json
   for the sequence only).
4. TYPE the claim. Read schema/claim_types.json (the controlled vocabulary). Set claim_type to the canonical
   type this claim SHOULD have. Re-type generic/wrong types — a bare "function" or a "strength" that is really a
   detection-sensitivity claim must be corrected to the right canonical type. Set claim_type_changed accordingly.

5. SCORE usefulness (high/medium/low) — INDEPENDENT of whether the claim is true. A claim is useful to the degree
   it fills a datasheet slot a designer consults to CHOOSE or OPERATE this part:
     + selection-relevant (would someone pick this part over an alternative because of it? comparative/discriminating)
     + operationally actionable (a parameter you set/use: inducer+conc, Kd, dynamic-range fold, copy number, protease/site, host, conditions)
     + specific/quantitative over vague; non-redundant with the part description & structured features; risk-reducing (caveats/failure modes are HIGH)
   LOW-usefulness anti-patterns: tautological (restates the part's identity), generic-to-class ("is a fusion tag",
   "used in E. coli"), historical/bibliographic ("the gene was sequenced in 1984"), unfalsifiable/vague ("is robust").
   Put the deciding reason in usefulness_rationale.

6. DECIDE evidence + AUTONOMOUS correction (no human will review — correct what you confidently can, annotate the rest):
   - cross_checked=true ONLY if verdict=confirmed AND primary_support=true AND you read the source; else false.
   - recommended_confidence: high only with strong primary support; medium if partial/indirect; low if weak or
     access-limited. If you could not access the source, keep low/medium and say so in uncertainty_note — never invent support.
   - correction_action + proposed_change:
       * none           — confirmed and clean.
       * fix_metadata   — a SAFE, reversible metadata fix: replace a self-referential quote with the real primary
                          sentence you found, OR re-point a wrong citation to the correct paper that is ALREADY in
                          the part's references. Give the exact change in proposed_change.
       * supersede      — you are CONFIDENT the claim's content is over-stated/wrong and you know the correct form
                          (e.g. narrow metals to those the source supports). The corrector will write a NEW claim that
                          supersedes the old (old retained). Put the corrected label/value in proposed_change.
       * downgrade_comment — you suspect a problem but cannot confidently rewrite it: keep the claim, lower confidence,
                          and the uncertainty_note becomes the attached comment.
   - evidence_quote must be copied from the source YOU read ("" if none).
Be terse and honest. A "disputed"/"unverifiable" verdict and a "low usefulness" score are successful, valuable results.`

log(`cross-checking ${slugs.length} part(s): ${slugs.join(', ')}`)

const results = await pipeline(
  slugs,
  // Stage 1 — extract claims (blind payload). Read-only agent: a checker must never mutate the catalog.
  (slug) => agent(LISTER_PROMPT(slug), { label: `extract:${slug}`, phase: 'Extract', schema: CLAIMS_SCHEMA, agentType: 'Explore' }),
  // Stage 2 — fan out one independent verifier per claim of that part (read-only: can Read/Bash/WebFetch, cannot Write/Edit)
  (listed, slug) => parallel(
    ((listed && listed.claims) || []).map((c) => () =>
      agent(VERIFY_PROMPT(c, slug), { label: `verify:${slug}/${c.claim_id}`, phase: 'Cross-check', schema: VERDICT_SCHEMA, agentType: 'Explore' })
    )
  )
)

const verdicts = results.flat().filter(Boolean)
const tally = (key) => verdicts.reduce((m, v) => ((m[v[key]] = (m[v[key]] || 0) + 1), m), {})
log(`Next: save these verdicts to a file and apply them autonomously — ` +
    `python tools/apply_cross_check.py --verdicts <file> --write — then python tools/check_all.py. ` +
    `Unreachable sources become sources-pending + a REQUESTS.md entry (fetch via /open-requests).`)
return {
  parts: slugs,
  n_verdicts: verdicts.length,
  by_verdict: tally('verdict'),
  by_usefulness: tally('usefulness'),
  by_recommended_confidence: tally('recommended_confidence'),
  by_correction_action: tally('correction_action'),
  by_quote_check: tally('quote_check'),
  cross_checked: verdicts.filter((v) => v.cross_checked).length,
  retyped: verdicts.filter((v) => v.claim_type_changed).length,
  low_usefulness: verdicts.filter((v) => v.usefulness === 'low').length,
  corrections_proposed: verdicts.filter((v) => v.correction_action !== 'none').length,
  next_step: 'python tools/apply_cross_check.py --verdicts <verdicts.json> --write ; python tools/check_all.py',
  verdicts,
}
