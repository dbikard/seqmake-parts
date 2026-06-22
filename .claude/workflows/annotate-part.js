export const meta = {
  name: 'annotate-part',
  description: "Catalog-native research/verify engine for one or more RELATED DNA/protein parts. SOURCES the sequence (independent re-fetch + byte/alignment compare via tools/source_finder.py — never trusts memory), researches the literature ONCE over a related cluster, LOCATES sub-features (-35/-10/operator/RBS/domains) on the real sequence, adversarially VERIFIES coordinates (in JS) and citations, and SYNTHESIZES a part.schema.json-shaped proposal (features + references + provenance.sequence_source + nanopub-shaped functional_claims + a curated .md). PROPOSAL-ONLY: it never writes a part file — the /add-part command merges the proposal via tools/merge_part.py (which protects reviewed claims). For a cluster it also returns a collections.json-ready block.",
  whenToUse: "When adding or improving a catalog part's sourcing + annotation + claims. Pass a single part (a slug string, or { name, sequence?, feature_type?, refs? }) OR a related cluster (an array of those, or { source, parts: [...] }) — clustering shares the Research phase so a common paper is researched once. Returns verified proposals; the caller merges + runs the gates.",
  phases: [
    { title: 'Resolve', detail: 'Load each part record (parts/<status>/<slug>.json) + catalog name inventory + localized cross-part sequence overlaps (one mechanical agent)', model: 'haiku' },
    { title: 'Source', detail: 'Per part: independent re-fetch + compare via source_finder.py -> provenance.sequence_source (never from memory); verify FULL-LENGTH (candidate records may be chimeric/mis-trimmed) and EXPLAIN every cross-part homology (never dismiss)', model: 'sonnet' },
    { title: 'Research', detail: 'ONE shared literature pass over the cluster (scout, early-stop)', model: 'sonnet' },
    { title: 'Locate', detail: 'Per part: map elements onto the real sequence (verify subsequences)', model: 'sonnet' },
    { title: 'Verify', detail: 'Per part: coordinates checked in JS; one agent adversarially checks citations', model: 'sonnet' },
    { title: 'Synthesize', detail: 'Per part: a part.schema.json-shaped proposal (features + claims + provenance + .md) — Opus for parts needing judgment, Sonnet for clean+confident ones', model: 'opus' },
    { title: 'Verify recs', detail: 'Per part: one agent vets the curation recommendations; drop the refuted', model: 'sonnet' },
    { title: 'Collection', detail: 'Cluster only: curate family references + resource links for collections.json', model: 'sonnet' },
  ],
}

// Runs from the catalog repo root; `python` must resolve to the env with the
// requirements.txt deps (biopython/requests) so tools/source_finder.py works.
const REPO = '/home/dbikard/dna-parts-catalog'

// ---- args ------------------------------------------------------------------
// Accept any of:
//   "Pbla"                                     single part by slug
//   { name, sequence?, feature_type?, refs? }  single part spec
//   ["Pbla", "Pkan", ...]                      a cluster of slugs
//   [ {name, ...}, {name, ...} ]               a cluster of specs
//   { source?, parts: [ ...specs ] }           a cluster + a shared-source hint
// or a JSON-encoded string of any of the above.
let a = args
if (typeof a === 'string') {
  const s = a.trim()
  if (s.startsWith('{') || s.startsWith('[')) {
    try { a = JSON.parse(s) } catch (e) { /* keep as a plain slug string */ }
  }
}
function _spec(x) {
  if (typeof x === 'string') return { name: x.trim() }
  if (x && typeof x === 'object') {
    return {
      name: String(x.name || '').trim(),
      sequence: x.sequence || null,
      feature_type: x.feature_type || null,
      refs: Array.isArray(x.refs) ? x.refs : (x.refs ? String(x.refs).split(',').map((s) => s.trim()).filter(Boolean) : []),
    }
  }
  return { name: '' }
}
let clusterSource = ''
let rawSpecs
if (Array.isArray(a)) {
  rawSpecs = a
} else if (a && typeof a === 'object' && Array.isArray(a.parts)) {
  rawSpecs = a.parts
  clusterSource = String(a.source || a.cluster || '').trim()
} else {
  rawSpecs = [a]
}
const specs = rawSpecs.map(_spec).filter((s) => s.name)
if (!specs.length) {
  return { error: 'Pass a part slug (string), { name, sequence?, refs? }, or a cluster: an array of those, or { source, parts: [...] }.' }
}
const single = specs.length === 1

// ---- model tiering ---------------------------------------------------------
// Scoped source/search/extract/verify agents run on a cheaper model; only the
// final synthesis (judgment + record + prose) uses the top model.
const WORKER_MODEL = 'sonnet'
const SYNTH_MODEL = 'opus'
const CHEAP_MODEL = 'haiku' // mechanical agents only (Resolve = run a command + echo its JSON)

// SO terms for the common cis-elements, so the synthesizer tags db_xref
// consistently (the command also normalizes via tools/so_terms.py on write).
const SO_HINTS = [
  'promoter -> SO:0000167', '-35 box (minus_35_signal) -> SO:0000175',
  '-10 box (minus_10_signal) -> SO:0000176', '+1 / TSS -> SO:0000315',
  'operator / protein-binding site -> SO:0000057', 'RBS / Shine-Dalgarno -> SO:0000139',
  'terminator -> SO:0000141', 'CDS -> SO:0000316', 'rep_origin -> SO:0000296',
].join('; ')

// ---- schemas ---------------------------------------------------------------
const RESOLVE_SCHEMA = {
  type: 'object',
  properties: {
    parts: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          found: { type: 'boolean' },
          name: { type: 'string', description: 'the slug' },
          status: { type: 'string', description: 'validated | candidate | new (not in repo)' },
          feature_type: { type: 'string' },
          molecule_type: { type: 'string', description: 'DNA | protein' },
          sequence: { type: 'string' },
          recorded_sequence_source: { type: 'string', description: 'provenance.sequence_source if present, else empty' },
          has_md: { type: 'boolean' },
          synonyms: { type: 'array', items: { type: 'string' } },
          children: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                label: { type: 'string' }, type: { type: 'string' },
                start: { type: 'integer' }, end: { type: 'integer' }, strand: { type: 'integer' },
              },
              required: ['label', 'type', 'start', 'end'],
            },
          },
          overlaps: {
            type: 'array',
            description: 'sequence overlaps vs the rest of the catalog (tools/catalog_overlap.py), each LOCALIZED to a concrete span — a data-quality + dedup signal, NOT noise to ignore',
            items: {
              type: 'object',
              properties: {
                slug: { type: 'string' }, status: { type: 'string' }, len: { type: 'integer' },
                relation: { type: 'string' }, est_overlap_bp: { type: 'integer' },
                shared_kmers: { type: 'integer' }, q_frac: { type: 'number' }, exact: { type: 'boolean' },
                best_match: {
                  type: 'object',
                  description: 'longest EXACT contiguous match: its length (bp), strand (+1/-1), and 0-based positions in this part (q_*) and the other part (s_*)',
                  properties: {
                    bp: { type: 'integer' }, strand: { type: 'integer' },
                    q_start: { type: 'integer' }, q_end: { type: 'integer' },
                    s_start: { type: 'integer' }, s_end: { type: 'integer' }, subseq: { type: 'string' },
                  },
                },
              },
              required: ['slug', 'relation'],
            },
          },
        },
        required: ['found', 'name'],
      },
    },
    catalog_names: { type: 'array', items: { type: 'string' }, description: 'every slug + synonym in the catalog (for dedup)' },
  },
  required: ['parts'],
}

// The Source phase records an INDEPENDENT re-fetch + compare verdict. This is the
// one inviolable gate: a sequence must trace to a fetchable, byte/alignment-verified
// source, never to memory. The agent runs tools/source_finder.py and reports its
// verdict; it must not assert a source it could not fetch + compare.
const SOURCE_SCHEMA = {
  type: 'object',
  properties: {
    kind: { type: 'string', enum: ['dna', 'protein'] },
    verified: { type: 'boolean', description: 'true ONLY if an independent re-fetch matched the stored sequence (DNA: a 100%/exact source_finder hit; protein: a UniProt status of exact/canonical)' },
    sequence_source: { type: 'string', description: 'the citation string to store in provenance.sequence_source (accession + what it is + identity); empty if unverified' },
    accession: { type: 'string', description: 'the chosen source accession (e.g. "J01749", "UniProt:P62593")' },
    identity_pct: { type: 'number' },
    location: { type: 'string', description: 'divergence class vs the canonical refs: exact | edge | internal | mixed | partial | n/a' },
    boundary_question: { type: 'boolean', description: 'true if divergence sits at the part edge -> a boundary question needing experimental grounding, not a sequence call' },
    variant_suggestion: { type: 'string', description: 'if an INTERNAL diff vs the canonical ref makes this a real variant, the labelled-sibling suggestion (ColE1_AT-style); else empty' },
    blocked: { type: 'boolean', description: 'true if a needed source was access-blocked (paywall/login/403/405) and was written to sourcing/REQUESTS.md' },
    full_length_match: { type: 'boolean', description: 'true ONLY if the ENTIRE stored sequence maps to the cited deposit; false if only a sub-span aligns and the remainder is foreign (a chimera / mis-trim). A part whose sequence is only partly genuine is NOT verified.' },
    quality_flags: {
      type: 'array',
      description: 'data-quality defects found in the STORED candidate record (empty if it is a clean, correctly-delimited instance of the part): e.g. "chimera", "mis-trimmed / includes flanking sequence", "vector backbone / MCS / restriction sites embedded", "wrong strand", "mislabeled (different element)", "over-long".',
      items: { type: 'string' },
    },
    homology_findings: {
      type: 'array',
      description: 'one entry per non-trivial sequence overlap with another catalog part (from the Resolve overlaps): an explanation, never a dismissal. A >=16 bp exact match is not chance.',
      items: {
        type: 'object',
        properties: {
          other_part: { type: 'string' },
          overlap_bp: { type: 'integer' },
          strand: { type: 'integer', description: '+1 same strand, -1 reverse-complement' },
          identity_pct: { type: 'number' },
          interpretation: { type: 'string', description: 'what the shared region IS and why it recurs' },
          implicates: { type: 'string', enum: ['this_part', 'other_part', 'shared_biological_element', 'unclear'], description: 'which record (if any) the homology shows to be bad-quality; shared_biological_element = a legitimately recurring motif, neither record is wrong' },
        },
        required: ['other_part', 'interpretation', 'implicates'],
      },
    },
    unresolved: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          url_or_id: { type: 'string' }, would_unblock: { type: 'string' },
          barrier: { type: 'string', description: '403 | login | paywall | not-in-pmc | 405 | other' },
        },
        required: ['would_unblock', 'barrier'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['kind', 'verified', 'sequence_source'],
}

const RESEARCH_SCHEMA = {
  type: 'object',
  properties: {
    elements: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          part: { type: 'string', description: 'which part this element belongs to (exact slug); omit only if it applies to every part in the cluster' },
          name: { type: 'string', description: 'e.g. "-35", "-10", "operator", "RBS", "+1 TSS"' },
          feature_type: { type: 'string', description: 'GenBank type: regulatory / protein_bind / misc_feature / RBS' },
          motif: { type: 'string', description: 'the consensus or exact sequence reported in the literature' },
          evidence: { type: 'string' },
          experimental: { type: 'boolean', description: 'true if a boundary/extent is grounded in EXPERIMENT (truncation / mutational scanning / S1 or primer-extension mapping / genetics), not consensus alone' },
          location_hint: { type: 'string', description: 'where it sits relative to other elements / the TSS' },
        },
        required: ['name', 'motif', 'evidence'],
      },
    },
    references: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          pmid: { type: 'string' }, doi: { type: 'string' },
          authors: { type: 'string' }, title: { type: 'string' }, journal: { type: 'string' },
          year: { type: 'integer' },
          supports: { type: 'string', description: 'which element/claim this reference justifies' },
        },
        required: ['supports'],
      },
    },
    resources: {
      type: 'array',
      description: 'useful EXTERNAL resource LINKS for this part/family (NOT papers): a registry page (iGEM, SEVA), an Addgene kit/plasmid page, a UniProt/InterPro/SO entry, a tool, a protocol. Real, working URLs.',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' }, url: { type: 'string' },
          kind: { type: 'string', description: 'registry / kit / database / tool / protocol / other' },
          part: { type: 'string' },
        },
        required: ['title', 'url'],
      },
    },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    complete: { type: 'boolean', description: 'true ONLY if every applicable cis element of EVERY part was located with a citation (or positively confirmed not to apply)' },
    needs_curation_judgment: { type: 'boolean', description: 'true if any part likely needs a curation DECISION rather than a routine assembly: a boundary re-delimitation, a split/extract because a sub-region is used standalone OR a compose because an adjacent same-class ensemble is used as one unit (granularity, both directions), a rename, or a variant/sibling. Routes synthesis to the stronger model.' },
    notes: { type: 'string' },
  },
  required: ['elements', 'references', 'confidence', 'complete'],
}

const LOCATE_SCHEMA = {
  type: 'object',
  properties: {
    children: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          label: { type: 'string' },
          feature_type: { type: 'string' },
          start: { type: 'integer', description: '0-based start on the part sequence' },
          end: { type: 'integer', description: '0-based end, exclusive' },
          strand: { type: 'integer', enum: [1, -1] },
          subsequence: { type: 'string', description: 'sequence[start:end] — must match the motif' },
          justification: { type: 'string' },
          experimental: { type: 'boolean', description: 'is this extent grounded in experiment (not consensus alone)?' },
          citation_pmids: { type: 'array', items: { type: 'string' } },
        },
        required: ['label', 'feature_type', 'start', 'end', 'strand', 'subsequence'],
      },
    },
    notes: { type: 'string' },
  },
  required: ['children'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          label: { type: 'string' },
          coordinate_ok: { type: 'boolean' },
          subsequence_matches: { type: 'boolean' },
          citation_ok: { type: 'boolean', description: 'is the cited PMID real and does it support this element?' },
          issue: { type: 'string' },
        },
        required: ['label', 'coordinate_ok', 'subsequence_matches', 'citation_ok'],
      },
    },
    overall: { type: 'string' },
  },
  required: ['results'],
}

// part.schema.json-shaped proposal. The command merges this via merge_part.py;
// features carry catalog qualifiers (label, db_xref SO term, parent, citation,
// regulatory_class), and functional_claims carry the nanopub shape.
const FINAL_SCHEMA = {
  type: 'object',
  properties: {
    slug: { type: 'string' },
    sequence: { type: 'string' },
    feature_type: { type: 'string' },
    description: { type: 'string', description: 'one-line summary for the record' },
    provenance: {
      type: 'object',
      properties: {
        sequence_source: { type: 'string', description: 'the verified source citation from the Source phase (verbatim); empty only if the Source phase could not verify' },
      },
    },
    features: {
      type: 'array',
      description: 'the main feature FIRST (spanning the whole part), then located sub-features',
      items: {
        type: 'object',
        properties: {
          type: { type: 'string', description: 'GenBank feature type: promoter / regulatory / protein_bind / misc_feature / RBS / CDS / rep_origin' },
          start: { type: 'integer' }, end: { type: 'integer' }, strand: { type: 'integer', enum: [1, -1] },
          label: { type: 'string' },
          so_term: { type: 'string', description: `Sequence Ontology accession, e.g. "SO:0000175". Use: ${SO_HINTS}` },
          regulatory_class: { type: 'string', description: 'for type=regulatory: minus_35_signal / minus_10_signal / ribosome_binding_site / etc.; else empty' },
          parent: { type: 'string', description: 'for a sub-feature: the main feature slug; empty for the main feature' },
          note: { type: 'string' },
          citation_pmids: { type: 'array', items: { type: 'string' } },
          provisional: { type: 'boolean', description: 'true if this extent rests on consensus/alignment only (no experimental grounding) — drives a lower confidence + a provisional note' },
        },
        required: ['type', 'start', 'end', 'strand', 'label'],
      },
    },
    references: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          pmid: { type: 'string' }, doi: { type: 'string' },
          authors: { type: 'string' }, title: { type: 'string' }, journal: { type: 'string' }, year: { type: 'integer' },
        },
      },
    },
    functional_claims: {
      type: 'array',
      description: 'nanopub-shaped claims (regulation / inducer / strength / host_range / sequence_variant / ...). Each cites its evidence; review_status is ai-generated; confidence is honest.',
      items: {
        type: 'object',
        properties: {
          id: { type: 'string', description: 'stable type-derived id: inducer, regulation, repression_dynamic_range, host_range, sequence_variant, ...' },
          type: { type: 'string' },
          label: { type: 'string' },
          value: { type: 'object', additionalProperties: true },
          source: {
            type: 'object',
            properties: {
              pmid: { type: 'string' }, doi: { type: 'string' },
              quote: { type: 'string' },
              quote_source: { type: 'string', enum: ['primary', 'catalog-doc'] },
              figure: { type: 'string' }, table: { type: 'string' }, page: { type: 'string' }, section: { type: 'string' },
            },
          },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['id', 'type', 'label', 'value', 'confidence'],
      },
    },
    confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
    warnings: { type: 'array', items: { type: 'string' } },
    requested_papers: {
      type: 'array',
      description: 'papers whose PRIMARY full text was needed to support a claim but was inaccessible (paywall / not-in-PMC) AND not in the local store. The affected claims were emitted with honest (non-primary) sourcing + capped confidence; these get appended to sourcing/REQUESTS.md so a human can deposit them.',
      items: {
        type: 'object',
        properties: {
          pmid: { type: 'string' }, doi: { type: 'string' }, title: { type: 'string' },
          unblocks: { type: 'string', description: 'claim id(s) this paper would verify' },
          barrier: { type: 'string', description: 'paywall | not-in-pmc | login | 403 | other' },
        },
        required: ['unblocks'],
      },
    },
    ready_to_apply: { type: 'boolean' },
    report_markdown: { type: 'string', description: 'curated .md for a validated part: a one-line summary then ## Origin, ## Properties, ## Use, ## References (PMID/DOI links). Lab- and tool-AGNOSTIC (tools/check_content.py enforces this): never name a specific lab, kit, vendor, or software; describe the biology.' },
    recommendations: {
      type: 'array',
      description: 'curation recommendations about the PART ITSELF (not its sub-features). Empty when well-curated.',
      items: {
        type: 'object',
        properties: {
          kind: { type: 'string', enum: ['rename', 'redelimit', 'split', 'merge', 'compose', 'new_part', 'metadata', 'note'] },
          title: { type: 'string' }, rationale: { type: 'string' }, proposal: { type: 'string' },
          confidence: { type: 'string', enum: ['high', 'medium', 'low'] },
        },
        required: ['kind', 'title', 'rationale', 'confidence'],
      },
    },
  },
  required: ['slug', 'sequence', 'features', 'references', 'confidence'],
}

const COLLECTION_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    suggested_id: { type: 'string', description: 'kebab-case id for collections.json' },
    description: { type: 'string' },
    references: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' }, authors: { type: 'string' }, journal: { type: 'string' },
          year: { type: 'integer' }, pmid: { type: 'string' }, doi: { type: 'string' },
        },
        required: ['title'],
      },
    },
    resources: {
      type: 'array',
      items: { type: 'object', properties: { title: { type: 'string' }, url: { type: 'string' } }, required: ['title', 'url'] },
    },
  },
  required: ['references', 'resources'],
}

// ---- element guides (cis-element vocabulary by part type) ------------------
function _category(ft) {
  const t = (ft || '').toLowerCase()
  if (t.includes('promoter')) return 'promoter'
  if (t === 'rep_origin' || t === 'oriv' || t === 'orit' || t.includes('origin')) return 'origin'
  if (t.includes('terminator')) return 'terminator'
  if (t === 'rbs' || t.includes('ribosome')) return 'rbs'
  if (t === 'protein_bind' || t.includes('operator')) return 'operator'
  if (t === 'cds' || t.includes('domain')) return 'coding'
  return 'default'
}
const ELEMENT_GUIDES = {
  promoter: {
    scout: 'EVERY promoter ACTUALLY PRESENT IN THIS FRAGMENT and its cis elements. A fragment may carry more than one promoter (tandem, overlapping, or divergent) OR just one if it was trimmed to a single core promoter — so enumerate every promoter whose -35/-10 you can verify IN the sequence, not just the strongest, but do NOT add a promoter that falls OUTSIDE this fragment: a gene\'s promoters can be far apart (the bla P1 and P3 are ~200 bp apart, so a short P3-only fragment contains no P1). For EACH promoter present give its own -35 box, -10 box, and +1, plus any operator / activator binding site and any RBS / Shine-Dalgarno. Tag each element with its promoter (e.g. "P1 -35", "P3 -10")',
    lenses: [
      { key: 'multiplicity', prompt: (n) => `How many DISTINCT promoters lie WITHIN ${n}? It may be several (tandem/overlapping/divergent) or just one if the fragment was trimmed to a single core promoter. For each promoter you can actually place IN the fragment, give its -35, -10, +1 and literature name — but ONLY if its boxes are present in this sequence; a known upstream promoter that falls outside the fragment's span (e.g. bla P1 relative to a short P3 fragment) must NOT be added. Never collapse two real promoters into one, and never invent one that isn't there.` },
      { key: 'origin', prompt: (n) => `Pin down the ORIGIN/design of ${n}: a natural promoter fragment (which gene/operon) or an engineered design (e.g. a constitutive scaffold with an operator overlapped onto the -10)? Find the defining paper and where the -35/-10 and any operator sit, and whether an EXPERIMENT (truncation / mutational scan / TSS mapping) defines its extent.` },
      { key: 'operator', prompt: (n) => `Focus on any protein-binding site (operator/activator) in ${n}: the protein that binds it, the exact binding-site sequence (often an inverted repeat), and the paper that characterized it. If there is none, say so explicitly.` },
    ],
    locate: 'Use GenBank feature types: regulatory for -35/-10 (element in the label + a regulatory_class), protein_bind for operators, misc_feature for +1/TSS, RBS for ribosome binding sites. If the fragment carries more than one promoter, place and label EACH promoter\'s -35/-10/+1 distinctly (e.g. "P1 -35", "P3 -10") — never merge two promoters into one.',
  },
  origin: {
    scout: 'EVERY applicable functional element of this replication origin per its mechanism — RNA-primed (ColE1/p15A): RNAII pre-primer, RNAI antisense regulator, rop/rom-binding region; iteron/Rep-dependent (pSC101, RK2, R6K, F): iterons/direct repeats, DnaA box(es), the AT-rich DUE, IHF/FIS sites; rolling-circle: the dso nic site + sso. Identify the mechanism, the cognate Rep/initiator (encoded here or in trans), copy number, host range, incompatibility group',
    lenses: [
      { key: 'mechanism', prompt: (n) => `Pin down the replication MECHANISM and initiator of ${n}: RNA-primed, iteron/Rep-dependent, or rolling-circle? Name the Rep/initiator, whether it is in cis or in trans, and cite the primary paper.` },
      { key: 'elements', prompt: (n) => `Locate the specific cis elements of ${n} reported in the literature — iteron/direct-repeat consensus + count, DnaA-box positions, the RNAI/RNAII region, or the dso nic site, and the AT-rich DUE. Give motifs and positions.` },
    ],
    locate: 'Use GenBank feature types: protein_bind for iterons/DnaA boxes/Rep-binding repeats, misc_feature for RNAI/RNAII, the DUE, or a nic site, rep_origin only for a delimited minimal core origin.',
  },
  terminator: {
    scout: 'EVERY applicable element — intrinsic (Rho-independent): the GC-rich hairpin stem-loop + the poly-U/U-tract; Rho-dependent: the rut site — with the stem-loop sequence and mechanism',
    lenses: [
      { key: 'mechanism', prompt: (n) => `Is the terminator ${n} intrinsic (Rho-independent) or Rho-dependent? Give the hairpin stem-loop + U-tract, or the rut site, and cite the paper.` },
      { key: 'origin', prompt: (n) => `Pin down the ORIGIN of ${n}: natural (which gene/operon) or synthetic, plus the conventional/registry name and strength if reported.` },
    ],
    locate: 'Use GenBank feature types: terminator for the whole element, stem_loop for the hairpin, misc_feature for the U-tract or rut site.',
  },
  rbs: {
    scout: 'the Shine-Dalgarno sequence, the spacing to the start codon, and any translational-coupling or standby element',
    lenses: [
      { key: 'origin', prompt: (n) => `Pin down the origin/design of the RBS ${n}: natural (which gene) or computationally designed, the Shine-Dalgarno motif and spacing, and the defining paper/tool.` },
    ],
    locate: 'Use GenBank feature types: RBS (or regulatory) for the Shine-Dalgarno, misc_feature for the spacer to the start codon.',
  },
  operator: {
    scout: 'the operator / binding-site palindrome (usually an inverted repeat), the cognate DNA-binding protein, and the half-site consensus',
    lenses: [
      { key: 'protein', prompt: (n) => `Identify the protein that binds the operator ${n}, the exact binding-site sequence and its symmetry (inverted-repeat half-sites), and the paper that characterised it.` },
    ],
    locate: 'Use GenBank feature types: protein_bind for the operator (operator name in the label).',
  },
  coding: {
    scout: "the protein's role/function and engineering-relevant facts (cognate partners, tags, notable variants) — NOT residue-level domains/active sites (those are deferred to UniProt), plus the canonical UniProt (preferred) or NCBI protein accession",
    lenses: [
      { key: 'role', prompt: (n) => `Establish the engineering role of the protein ${n} (what it does in a construct, its cognate partners/substrates, common variants) and give its canonical UniProt accession. Do NOT hand-map residue domains — those come from UniProt.` },
    ],
    locate: 'For a coding part do NOT hand-author residue features (domains/active sites) — they are imported from UniProt downstream. Place only genuine non-residue sub-features if any.',
  },
  default: {
    scout: 'EVERY applicable functional element of this part given its type — the cis elements, binding sites, or structural motifs that define how it works',
    lenses: [
      { key: 'elements', prompt: (n) => `Identify the functional elements of ${n} and the primary literature that characterises them; fill gaps the initial scan left open.` },
    ],
    locate: 'Use the most specific appropriate GenBank feature type for each functional element (protein_bind, regulatory, misc_feature, stem_loop, etc.).',
  },
}

// ---- 1. Resolve ------------------------------------------------------------
// ONE agent loads each requested part record from parts/<status>/<slug>.json and
// the full catalog name+synonym inventory (used only in JS for dedup). A
// caller-supplied sequence wins (so a brand-new part with no file still resolves).
phase('Resolve')
const names = specs.map((s) => s.name)
const resolveResult = await agent(
  `Resolve these catalog part slugs: ${JSON.stringify(names)}. Run this EXACT command from the repo root and return the JSON it prints as your structured output (do not invent values):\n\n` +
  '```\n' +
  `cd ${REPO} && python - <<'PYEOF'\n` +
  `import json, glob, os, sys\n` +
  `NAMES = ${JSON.stringify(names)}\n` +
  `sys.path.insert(0, 'tools')\n` +
  `try:\n` +
  `    import catalog_overlap as _co\n` +
  `except Exception:\n` +
  `    _co = None\n` +
  `def load(slug):\n` +
  `    for st in ('validated','candidate'):\n` +
  `        p = f'parts/{st}/{slug}.json'\n` +
  `        if os.path.exists(p):\n` +
  `            d = json.load(open(p)); d['_status'] = st; d['_has_md'] = os.path.exists(f'parts/{st}/{slug}.md'); return d\n` +
  `    return None\n` +
  `def overlaps_for(d, nm):\n` +
  `    if _co is None or d.get('molecule_type','DNA') == 'protein' or not d.get('sequence'):\n` +
  `        return []\n` +
  `    rows = []\n` +
  `    try:\n` +
  `        for h in _co.scan(d['sequence'].upper(), exclude=d.get('slug', nm))[:6]:\n` +
  `            bm = dict(h.get('best_match') or {})\n` +
  `            if bm.get('subseq') and len(bm['subseq']) > 60: bm['subseq'] = bm['subseq'][:60] + '...'\n` +
  `            row = {k2: h[k2] for k2 in ('slug','status','len','relation','est_overlap_bp','shared_kmers','q_frac','exact') if k2 in h}\n` +
  `            if bm: row['best_match'] = bm\n` +
  `            rows.append(row)\n` +
  `    except Exception:\n` +
  `        return []\n` +
  `    return rows\n` +
  `out = []\n` +
  `for nm in NAMES:\n` +
  `    d = load(nm)\n` +
  `    if not d:\n` +
  `        out.append({'found': False, 'name': nm, 'status': 'new'}); continue\n` +
  `    f0 = (d.get('features') or [{}])[0]; q = f0.get('qualifiers', {})\n` +
  `    out.append({\n` +
  `      'found': True, 'name': d.get('slug', nm), 'status': d['_status'],\n` +
  `      'feature_type': f0.get('type',''), 'molecule_type': d.get('molecule_type','DNA'),\n` +
  `      'sequence': d.get('sequence',''),\n` +
  `      'recorded_sequence_source': (d.get('provenance') or {}).get('sequence_source',''),\n` +
  `      'has_md': d['_has_md'], 'synonyms': q.get('synonym', []),\n` +
  `      'overlaps': overlaps_for(d, nm),\n` +
  `      'children': [{'label': (c.get('qualifiers',{}).get('label',['?'])[0]), 'type': c.get('type',''),\n` +
  `                    'start': c.get('start'), 'end': c.get('end'), 'strand': c.get('strand',1)}\n` +
  `                   for c in (d.get('features') or [])[1:]],\n` +
  `    })\n` +
  `allnames = set()\n` +
  `for f in glob.glob('parts/*/*.json'):\n` +
  `    d = json.load(open(f)); allnames.add(d.get('slug',''))\n` +
  `    allnames.update((d.get('features') or [{}])[0].get('qualifiers',{}).get('synonym', []))\n` +
  `print(json.dumps({'parts': out, 'catalog_names': sorted(n for n in allnames if n)}))\n` +
  `PYEOF\n` +
  '```',
  { schema: RESOLVE_SCHEMA, label: `resolve:${single ? names[0] : names.length + ' parts'}`, phase: 'Resolve', model: CHEAP_MODEL },
)
const resolvedByName = new Map((resolveResult.parts || []).map((p) => [p.name.toLowerCase(), p]))
const existingNames = resolveResult.catalog_names || []
const existingLc = new Set(existingNames.map((n) => n.toLowerCase()))

const parts = []
for (const s of specs) {
  const r = resolvedByName.get(s.name.toLowerCase())
  const sequence = (s.sequence || (r && r.sequence) || '').toUpperCase()
  if (!sequence) {
    log(`Skipped "${s.name}": not in parts/ and no sequence supplied.`)
    continue
  }
  const feature_type = s.feature_type || (r && r.feature_type) || ''
  const isProteinPart = (r && r.molecule_type === 'protein') || /[^ACGTUN]/.test(sequence)
  const category = _category(feature_type)
  parts.push({
    name: (r && r.name) || s.name,
    status: (r && r.status) || 'new',
    feature_type, sequence,
    children: (r && r.children) || [],
    synonyms: (r && r.synonyms) || [],
    overlaps: (r && r.overlaps) || [],
    recordedSource: (r && r.recorded_sequence_source) || '',
    refs: s.refs || [],
    isProteinPart, unit: isProteinPart ? 'aa' : 'bp',
    category, guide: ELEMENT_GUIDES[category],
  })
}
if (!parts.length) {
  return { error: 'No parts resolved (none in parts/ and none had a supplied sequence).', requested: names }
}
log(`Resolved ${parts.length}/${specs.length}: ${parts.map((p) => `${p.name} (${p.status}, ${p.sequence.length}${p.unit}, ${p.category})`).join(', ')}; ${existingNames.length} catalog names for dedup`)
for (const p of parts) {
  if (!p.overlaps || !p.overlaps.length) continue
  const top = p.overlaps.slice(0, 4).map((o) => {
    const bm = o.best_match || {}
    return `${o.slug}(${o.relation}${bm.bp ? `, ${bm.bp}bp exact${bm.strand === -1 ? ' RC' : ''}` : ''})`
  }).join(', ')
  log(`[${p.name}] catalog overlaps to investigate (not noise): ${top}`)
}

// ---- 2. Source: independent re-fetch + compare (per part) ------------------
// The inviolable gate. tools/source_finder.py does the heavy lifting: protein ->
// UniProt accession from the uniprot_import block; DNA -> date-bracketed BLAST for
// the oldest reputable 100% deposit + a divergence report vs any canonical refs.
// The agent runs it, reads its JSON, and reports a verdict; if a needed source is
// access-blocked it appends to sourcing/REQUESTS.md and sets blocked=true.
phase('Source')
async function sourceOne(part) {
  const refsArg = part.refs.length ? ` --refs ${part.refs.join(',')}` : ''
  const verdict = await agent(
    `Establish and VERIFY the source of the catalog part "${part.name}" (${part.isProteinPart ? 'protein' : 'DNA'}, ${part.sequence.length} ${part.unit}). The sequence must trace to a fetchable, independently-compared source — NEVER to memory.\n\n` +
    `Run this from the repo root (the NCBI BLAST is queued, so allow time):\n\n` +
    '```\n' +
    `cd ${REPO} && python tools/source_finder.py --slug ${part.name}${refsArg} --max-wait 600\n` +
    '```\n\n' +
    `RESILIENCE: NCBI BLAST can drop the connection mid-poll. If the command fails with a connection/timeout error, the search was still SUBMITTED — it printed "submitted RID=XXXX" to stderr. Do NOT re-submit (that wastes the queue and may drop again); instead re-fetch the finished job: \`python tools/source_finder.py --slug ${part.name}${refsArg} --rid XXXX --max-wait 300\`. ${part.refs.length ? 'Because canonical reference accession(s) were supplied, the divergence-vs-refs result is the most reliable confirmation even if discovery is thin.' : 'If discovery keeps failing but you know a canonical carrier accession for this part, re-run with --refs <accession> — the divergence path (independent efetch + alignment) is more robust than blind discovery.'}\n\n` +
    `Interpret the JSON it prints:\n` +
    `- PROTEIN: the "protein" block gives the UniProt/NCBI accession + match status. verified=true if the status is exact/canonical (or identity 100). sequence_source = its "sequence_source" string. location="n/a".\n` +
    `- DNA: "dna_sources.recommended" is the oldest reputable 100% deposit (accession + date + title). verified=true ONLY if there is a full-length 100% perfect hit (n_perfect>0 and the recommended deposit covers the whole part). Build sequence_source like "pBR322 (J01749), <what region>, 100% over ${part.sequence.length} bp". If "divergence_vs_refs" is present, read each ref's "location": exact -> cite it; "edge" -> set boundary_question=true (a boundary needs experimental grounding, not a sequence call); "internal" -> set variant_suggestion (a labelled sibling, ColE1_AT-style); honor any top-level "flag" (likely-non-canonical).\n` +
    `- If source_finder finds NO 100% deposit, or a needed record is access-blocked (paywall/login/403/405): do NOT invent a source. Append the need to sourcing/REQUESTS.md (link · what it unblocks · barrier · suggested filename) per sourcing/README.md, set blocked=true and verified=false, and list it under "unresolved".\n` +
    `\nCANDIDATE RECORDS MAY BE LOW QUALITY — do NOT trust the stored sequence as a clean, correctly-delimited instance of the part. Migrated/auto-collected records are frequently CHIMERIC or VECTOR fragments (carrying backbone, a multiple-cloning site, restriction sites, or a foreign terminator/origin), MIS-TRIMMED (extra flanking sequence, wrong length), on the WRONG STRAND, or MISLABELED (a different element entirely). Confirm the ENTIRE stored sequence maps to the cited deposit, not just a sub-span: set full_length_match accordingly, and if any internal segment fails to align — or you find embedded cloning/restriction sites or a foreign element — record it in quality_flags and set verified=false (a sequence only partly genuine is NOT verified).\n` +
    `\nUNEXPECTED HOMOLOGY — INVESTIGATE, NEVER DISMISS. The Resolve step localized this part's sequence overlaps with other catalog parts (below). An EXACT match of ~16 bp or more does NOT occur by chance (4^16 ≈ 4e9), so every overlap is real homology that must be EXPLAINED — never written off as coincidental or "benign". For each, load the other part (parts/<status>/<slug>.json) and decide which it is: a legitimately RECURRING biological element (a common terminator/origin/promoter/RBS motif that appears in several parts → implicates="shared_biological_element"); evidence THIS record is mis-trimmed / chimeric / mislabeled (→ "this_part" + a quality_flag); or evidence the OTHER part is the bad record, e.g. it embeds a copy of an element it should not contain (→ "other_part" — a curation note; do NOT edit the other part here). Emit one homology_finding per overlap. Localize with EXACT matching on BOTH strands and trust the best_match span the Resolve step already computed; do NOT re-derive with difflib/fuzzy diff on DNA (its autojunk heuristic silently fails on a 4-letter alphabet).\n` +
    `\nResolve-computed overlaps for ${part.name} (each with a localized best_match: bp, strand, positions):\n${JSON.stringify(part.overlaps || [], null, 2)}\n` +
    (part.recordedSource ? `\nThe part already records sequence_source = ${JSON.stringify(part.recordedSource)}; treat this run as RE-VERIFICATION — confirm that source still resolves and still matches, and report if it has rotted.\n` : `\nThe part has no recorded sequence_source; this is DISCOVERY — find and verify one.\n`) +
    `\nReport honestly. Never set verified=true without an actual fetched + compared match.`,
    { schema: SOURCE_SCHEMA, label: `source:${part.name}`, phase: 'Source', model: WORKER_MODEL },
  )
  part.source = verdict
  const qf = (verdict.quality_flags || [])
  const otherBad = (verdict.homology_findings || []).filter((h) => h.implicates === 'other_part')
  log(`[${part.name}] source: ${verdict.verified ? 'VERIFIED' : (verdict.blocked ? 'BLOCKED -> REQUESTS.md' : 'UNVERIFIED')}` +
    `${verdict.accession ? ` (${verdict.accession}${verdict.identity_pct != null ? `, ${verdict.identity_pct}%` : ''})` : ''}` +
    `${verdict.full_length_match === false ? ' [NOT full-length: chimera/mis-trim]' : ''}` +
    `${qf.length ? ` [quality: ${qf.join('; ')}]` : ''}` +
    `${otherBad.length ? ` [flags other part(s): ${otherBad.map((h) => h.other_part).join(', ')}]` : ''}` +
    `${verdict.boundary_question ? ' [edge/boundary question]' : ''}`)
  return part
}
await parallel(parts.map((p) => () => sourceOne(p)))
const blockedParts = parts.filter((p) => p.source && p.source.blocked)
if (blockedParts.length) {
  log(`Source BLOCKED for ${blockedParts.length} part(s) -> sourcing/REQUESTS.md: ${blockedParts.map((p) => p.name).join(', ')}. They are carried forward but their proposals will flag the unverified sequence.`)
}

// ---- 3. Research: ONE shared pass over the cluster -------------------------
phase('Research')
const seqList = parts.map((p) => `>${p.name} (${p.isProteinPart ? 'protein' : 'DNA'}, ${p.sequence.length} ${p.unit}, type=${p.feature_type || '?'})\n${p.sequence}`).join('\n\n')
const perPartTargets = parts.map((p) => `- ${p.name} (${p.feature_type || 'DNA part'}): ${p.guide.scout}`).join('\n')
const sourceLine = clusterSource
  ? `These parts share a common source: ${clusterSource}. Research that source thoroughly — it likely characterises several together.\n\n`
  : ''
const sharedBlock = `\n\nSequences:\n${seqList}\n\nUse web search and fetch real sources. Only report elements and citations you can actually support; never fabricate PMIDs.`

const scout = await agent(
  `Comprehensively research the molecular architecture of ${single ? `the part "${parts[0].name}"` : `these ${parts.length} related parts`}.\n\n` +
  sourceLine +
  `For EACH part, identify its elements:\n${perPartTargets}\n\n` +
  `Give the exact or consensus motif each element has in the literature and the primary paper(s) that define them. TAG every element with "part" = the exact slug above. For any boundary/extent, set "experimental"=true ONLY if it is grounded in an EXPERIMENT (progressive truncation, mutational scanning, S1/primer-extension TSS mapping, genetics) — consensus/alignment alone is not experimental. Also gather this part's DATASHEET PARAMETERS — the operational facts a user selects/operates it by, each with a primary citation: for a promoter, its inducer/repressor + dynamic range (fold) + leakiness/basal + relative strength + host range; for a protein tag/domain, its binding partner/matrix + affinity (Kd) + antibody + removal protease/site + host range + N-/C-terminal placement; for a replicon, copy number + incompatibility group + host range; for a terminator, termination efficiency + host range; plus any key CAVEAT/failure mode. Note which are documented vs. genuinely not applicable. Also determine each part's origin (natural fragment vs engineered design), conventional/registry name(s), close variants, commonly-paired parts (cognate protein + inducer), whether the boundaries look right, and — importantly, for GRANULARITY in BOTH directions — (i) whether any functional SUB-region is used as a standalone part in its own right (its own registry/standard ID, or literature/constructs that deploy just that element independent of the larger region → a split/extract signal), and (ii) whether this part is one of an ADJACENT SAME-CLASS ensemble that is commonly deployed together as ONE unit (e.g. a tandem T1+T2 double terminator used as a single terminator → a compose signal), each ideally attested in ≥2 independent contexts — these feed curation recommendations. Return real PMIDs/DOIs (with year) and which element each reference supports.\n\n` +
  `Also collect a few useful EXTERNAL "resources" — real working LINKS (registry/kit/database/UniProt/SO/tool/protocol), NOT papers.\n\n` +
  `Self-assess: "confidence"=high ONLY if sure of every element with a solid citation each; "complete"=true ONLY if every applicable element of every part was located (or positively confirmed N/A). Set "needs_curation_judgment"=true if any part likely needs a curation decision (boundary re-delimitation, a split/extract because a sub-region is used standalone, a compose because an adjacent same-class ensemble is used as one unit, a rename, or a variant) rather than a routine annotation.` +
  sharedBlock,
  { schema: RESEARCH_SCHEMA, label: 'research:scout', phase: 'Research', model: WORKER_MODEL },
)

const research = [scout]
if (scout.confidence === 'high' && scout.complete) {
  log(`Scout confident + complete (${(scout.elements || []).length} elements, ${(scout.references || []).length} refs) — early stop`)
} else {
  const byCat = new Map()
  for (const p of parts) {
    if (!byCat.has(p.category)) byCat.set(p.category, [])
    byCat.get(p.category).push(p)
  }
  const lensThunks = []
  for (const [cat, ps] of byCat) {
    const nm = ps.map((p) => `"${p.name}"`).join(', ')
    const seqs = ps.map((p) => `>${p.name}\n${p.sequence}`).join('\n\n')
    for (const l of ELEMENT_GUIDES[cat].lenses) {
      lensThunks.push(() =>
        agent(`${l.prompt(nm)}\n\nFill the gaps the initial scan left open. TAG each element with its "part" and set "experimental" honestly.\n\nSequences:\n${seqs}\n\nUse web search and fetch real sources; never fabricate PMIDs.`,
          { schema: RESEARCH_SCHEMA, label: `research:${cat}:${l.key}`, phase: 'Research', model: WORKER_MODEL }))
    }
  }
  log(`Scout confidence=${scout.confidence}, complete=${scout.complete} — fanning out ${lensThunks.length} lens(es) across ${byCat.size} categor(y/ies)`)
  research.push(...(await parallel(lensThunks)).filter(Boolean))
}

const pool = {
  elements: research.flatMap((r) => r.elements || []),
  references: research.flatMap((r) => r.references || []),
  resources: research.flatMap((r) => r.resources || []),
}
log(`Research pool: ${pool.elements.length} element claims, ${pool.references.length} candidate refs, ${pool.resources.length} resource link(s) from ${research.length} lens(es)`)

// ---- 4-7. Per part: Locate -> Verify -> Synthesize -> Verify recs ----------
const _rc = (s) => s.toUpperCase().replace(/[ACGTN]/g, (c) => ({ A: 'T', T: 'A', G: 'C', C: 'G', N: 'N' }[c])).split('').reverse().join('')

function _elementsFor(part) {
  const target = part.name.toLowerCase()
  const syns = (part.synonyms || []).map((s) => s.toLowerCase())
  return pool.elements.filter((e) => {
    const tag = (e.part || '').trim().toLowerCase()
    if (!tag) return true
    return tag === target || syns.includes(tag) || tag.includes(target) || target.includes(tag)
  })
}

async function annotateOne(part) {
  const seq = part.sequence
  const isProteinPart = part.isProteinPart
  const guide = part.guide
  const elementsForPart = _elementsFor(part)

  // ---- Locate (skipped for coding parts: residue features come from UniProt, so there
  // is no cis-geometry to place here — saves an agent) ----
  let located = { children: [] }
  if (part.category === 'coding') {
    log(`[${part.name}] coding part — skipping Locate (residue features deferred to UniProt import)`)
  } else {
    located = await agent(
      `You are placing sub-features onto a catalog part sequence with EXACT coordinates.\n\n` +
      `Part: ${part.name} (${part.feature_type || 'unknown type'})\n` +
      `${isProteinPart ? 'Protein (amino-acid) sequence' : 'Sequence'} (0-based, length ${seq.length}${isProteinPart ? ' residues' : ''}):\n${seq}\n\n` +
      `Existing sub-features (may be empty / to be improved): ${JSON.stringify(part.children || [])}\n\n` +
      `Research findings for THIS part (element motifs + candidate references):\n${JSON.stringify({ elements: elementsForPart, references: pool.references }, null, 2)}\n\n` +
      `For each well-supported element, give 0-based [start, end) on the sequence${isProteinPart ? ' (residue positions)' : ''}, the strand ${isProteinPart ? '(+1)' : '(+1/-1)'}, and the exact subsequence sequence[start:end] (compute it — it MUST match the motif${isProteinPart ? '' : ', accounting for reverse-complement on -1'}). ${guide.locate} If an element type occurs MORE THAN ONCE (e.g. two promoters' -35/-10, multiple operators or iterons), place and label EACH occurrence distinctly — do not report only one. Set "experimental" per element (is its extent from an experiment, not consensus?). Annotate ONLY functional elements — do NOT place spacers, -35/-10 separations, discriminators, or restriction/cloning sites. Attach justifying PMIDs. Skip any element you cannot place confidently. Verify every subsequence before returning.`,
      { schema: LOCATE_SCHEMA, label: `locate:${part.name}`, phase: 'Locate', model: WORKER_MODEL },
    )
    log(`[${part.name}] located ${located.children.length} candidate sub-features`)
  }
  located.children = located.children || []

  // Note boundary-flush sub-features for the synthesizer (a boundary question that
  // wants experimental grounding — we do NOT scan lab plasmids; public KB only).
  const boundaryHits = (located.children || [])
    .filter((c) => c.start === 0 || c.end === seq.length)
    .map((c) => c.label)
  const boundaryNote = boundaryHits.length
    ? `\nBoundary-flush sub-features (${boundaryHits.join(', ')}) abut the part edge: a boundary question. Per policy, do NOT extend/trim on consensus alone — keep the boundary as recorded and, if no experimental (truncation/mapping) evidence supports a change, mark such elements provisional with a lower confidence and (if a defining paper exists but is inaccessible) note it for sourcing/REQUESTS.md.\n`
    : ''

  // ---- Verify: coordinates/subsequences in JS (deterministic); citations by agent ----
  const coordResults = (located.children || []).map((c) => {
    const inBounds = Number.isInteger(c.start) && Number.isInteger(c.end) &&
      c.start >= 0 && c.end <= seq.length && c.start < c.end
    let actual = inBounds ? seq.slice(c.start, c.end) : ''
    if (inBounds && !isProteinPart && c.strand === -1) actual = _rc(actual)
    const claimed = (c.subsequence || '').toUpperCase()
    const matches = inBounds && (claimed ? actual === claimed : true)
    return {
      label: c.label,
      coordinate_ok: inBounds,
      subsequence_matches: matches,
      issue: !inBounds ? `out-of-range [${c.start}, ${c.end}) for length ${seq.length}`
        : (claimed && actual !== claimed ? `sequence[${c.start}:${c.end}]="${actual}" != claimed "${claimed}"` : ''),
    }
  })
  const nBadCoord = coordResults.filter((r) => !r.coordinate_ok || !r.subsequence_matches).length
  log(`[${part.name}] coordinate check (JS): ${coordResults.length - nBadCoord}/${coordResults.length} children verified exact`)

  let citationVerdict = { results: [] }
  if (located.children.length) {
    citationVerdict = await agent(
      `Adversarially verify the CITATIONS on this proposed annotation. For every citation_pmid, judge whether the PMID is plausibly real and whether that paper actually supports the element it is attached to. Default citation_ok=false when uncertain or when no PMID is given.\n\n` +
      `Proposed children:\n${JSON.stringify(located.children, null, 2)}\n\n` +
      `Be skeptical. Return one result per child.`,
      { schema: VERIFY_SCHEMA, label: `verify:${part.name}`, phase: 'Verify', model: WORKER_MODEL },
    )
  } else {
    log(`[${part.name}] no located sub-features — skipping citation verification`)
  }
  const verdicts = [{ check: 'deterministic-coordinates-JS', results: coordResults }, citationVerdict]

  // ---- Synthesize the part.schema.json-shaped proposal ----
  // Adaptive tiering: Synthesis is the one Opus step. Reserve Opus for parts that actually
  // need judgment — any coordinate/citation verification failure, an unverified source, a
  // boundary question, or research that was not high-confidence + complete. A part where
  // everything verified cleanly AND research was confident is a straight assembly of
  // verified findings into the schema, which Sonnet handles well. Conservative by design:
  // ANY wrinkle -> Opus, so quality is protected on every non-trivial part.
  const src = part.source || {}
  const researchFlagsCuration = research.some((r) => r && r.needs_curation_judgment)
  const qualityConcern = src.full_length_match === false || (src.quality_flags && src.quality_flags.length > 0)
  const cleanAndConfident =
    nBadCoord === 0 && !!src.verified && !qualityConcern && boundaryHits.length === 0 && !researchFlagsCuration &&
    !!scout && scout.confidence === 'high' && scout.complete
  const synthModel = cleanAndConfident ? WORKER_MODEL : SYNTH_MODEL
  if (cleanAndConfident) {
    log(`[${part.name}] Synthesize on ${WORKER_MODEL} (clean + confident — no Opus needed)`)
  } else {
    const why = [nBadCoord ? `${nBadCoord} verify-fail` : '', !src.verified ? 'unverified-source' : '',
      qualityConcern ? 'record-quality-flag' : '',
      boundaryHits.length ? 'boundary-question' : '', researchFlagsCuration ? 'curation-judgment-flagged' : '',
      !(scout && scout.confidence === 'high' && scout.complete) ? 'research<high/incomplete' : ''].filter(Boolean).join(', ')
    log(`[${part.name}] Synthesize on ${SYNTH_MODEL} (judgment needed: ${why})`)
  }
  const proposal = await agent(
    `Synthesize a final, ready-to-review catalog proposal for the part "${part.name}" in part.schema.json shape.\n\n` +
    `Sequence (length ${seq.length}):\n${seq}\n\n` +
    `SOURCE phase verdict (authoritative — copy its sequence_source verbatim into provenance.sequence_source):\n${JSON.stringify(src, null, 2)}\n\n` +
    `Located children:\n${JSON.stringify(located.children, null, 2)}\n\n` +
    `Adversarial verdicts:\n${JSON.stringify(verdicts, null, 2)}\n\n` +
    `Candidate references:\n${JSON.stringify(pool.references, null, 2)}\n` +
    boundaryNote +
    `\nRules:\n` +
    `- features: emit the MAIN feature first (type=${part.feature_type || 'the part type'}, start 0, end ${seq.length}, the part's SO term, label "${part.name}"), then each kept sub-feature. DROP any child whose coordinate or subsequence failed verification. Keep only FUNCTIONAL sub-features (-35, -10, +1/TSS, operators, activator/repressor sites, RBS); DROP spacers, separations, discriminators, restriction/cloning sites. Each sub-feature: parent="${part.name}", a so_term (${SO_HINTS}), a regulatory_class where type=regulatory, citation_pmids, and provisional=true if its extent rests on consensus alone (no experimental grounding).\n` +
    `- provenance.sequence_source: the verified string from the SOURCE verdict. If the SOURCE verdict was unverified/blocked, leave it as the verdict gave it and add a warning — never fabricate a source.\n` +
    `- record quality + cross-part homology: the SOURCE verdict carries full_length_match, quality_flags, and homology_findings. If full_length_match is false or quality_flags is non-empty (chimera / mis-trim / embedded vector or restriction sites / wrong strand / mislabeled), add each to warnings and set confidence=low and ready_to_apply=false — this candidate sequence is not a clean instance of the part and likely needs re-sourcing or re-delimiting (a human call). For each homology_finding: implicates="this_part" → handle as above; implicates="other_part" → emit a 'note' recommendation naming that other part and the defect (a curation flag for the catalog), do NOT propose editing it here; implicates="shared_biological_element" → no action.\n` +
    `- functional_claims: emit nanopub-shaped claims (regulation / inducer / strength / host_range / sequence_variant ...) ONLY where supported, each with a stable type-derived id, a source {pmid/doi, quote, quote_source: primary|catalog-doc, figure/table/page}, an honest confidence, and value. A constitutive promoter gets at least a {id:"regulation", type:"regulation", value:{regulation:"constitutive"}} claim. Use a canonical claim TYPE from schema/claim_types.json (no new free-text types).\n` +
    `- CLAIM-EVIDENCE HONESTY GATE (symmetric with the sequence SOURCE gate — do NOT fabricate support from an abstract or memory): a claim may carry quote_source="primary" + confidence high ONLY if you actually READ the primary full text (or the specific figure/table/passage) the claim rests on. First check the local paper store: \`python tools/papers.py resolve --json --pmid <pmid> --doi <doi>\` and read it if present. If the primary full text is NOT accessible (paywall / not-in-PMC / only the abstract is reachable) and the claim's evidence needs more than the abstract (a quantitative value, a figure/table, a mechanism detail): do NOT set quote_source="primary"; cap confidence at medium (low if it rests on a figure/number you could not see); and ADD that paper to "requested_papers" {pmid/doi, title, unblocks:<claim id>, barrier}. A claim fully supported by the abstract alone is fine at its honest confidence and needs no request.\n` +
    `- DATASHEET COMPLETENESS: consult schema/claim_types.json. For this part's CLASS (promoter / terminator / operator / replicon / resistance / protein tag / fusion domain / cleavage site / recombination site), the claim_types with datasheet_slot=true and this class in applies_to are the operational parameters a user selects/operates the part by. Make sure each HIGH-VALUE slot is EITHER backed by a sourced claim OR genuinely not applicable — actively draft the MISSING ones from the research pool (e.g. a promoter's inducer/dynamic_range/leakiness/host_range; a tag's binding_affinity/antibody_recognition/tag_removal/host_range; a replicon's copy_number/incompatibility_group/host_range; a terminator's termination_efficiency/host_range), under the SAME sourcing + honesty gate as every other claim. Do NOT pad: add a slot's claim ONLY where the literature supports it — never invent a tautological or generic-to-class claim just to fill a slot.\n` +
    `- references: dedupe; full bib (pmid, doi, authors, title, journal, year) for every cited PMID.\n` +
    `- confidence: high ONLY if the sequence is source-verified AND coordinates+citations verified. ready_to_apply=true only when every kept child verified cleanly and the sequence is verified.\n` +
    `- report_markdown: a tight, factual .md — one-line summary then ## Origin, ## Properties, ## Use, ## References (PMID/DOI links). It MUST be lab- and tool-AGNOSTIC: never name a specific lab, kit, vendor, plasmid-prep brand, or software; describe the biology and cite papers. (tools/check_content.py enforces this and will reject violations.)\n` +
    `- recommendations: critically assess the PART ITSELF — rename (non-standard name); redelimit (boundaries; only on experimental grounding — else a 'note' that it is provisional); split (ATOMICITY: the part bundles >1 SO functional class, e.g. a promoter AND an RBS — divide into atomic parts); compose (kind:"compose"); new_part; metadata/note. The governing principle (AUTHORING "What a part is"): a part is functionally COHERENT ∧ USED AS A UNIT, and the catalog holds every granularity that independently passes both, ADDITIVELY and cross-linked — so granularity runs in BOTH directions:\n` +
    `    • GRANULARITY DOWN (split/extract via new_part): if a functional sub-region is COMMONLY USED ALONE (its own registry/standard ID, or literature/constructs deploying just it, or a recognized minimal/standard form — ideally ≥2 independent contexts), recommend minting it as "<slug>_<element>" while KEEPING this composite; both coexist and are cross-linked (composite lists its component, the sub-part is sub_region_of the composite). For new_part: a missing related part — a canonical variant, a cognate partner, OR such a standalone-used sub-region.\n` +
    `    • GRANULARITY UP (compose/merge): if this part plus an ADJACENT SAME-FUNCTIONAL-CLASS part are commonly deployed together AS ONE UNIT (e.g. a tandem T1+T2 double terminator used as one terminator, ≥2 independent contexts), recommend kind:"compose" to mint the composite "<wholeName>" while KEEPING the atoms, cross-linked the same way. The composite's sequence MUST be sourced FRESH from the native/canonical deposit (state the accession + the span) — NEVER assembled by concatenating member parts (that inherits member errors and drops the native junction). Only same-class ensembles compose; mixing SO classes never composes.\n` +
    `    Both directions need standalone-use EVIDENCE (cite it) and the boundary still needs experimental grounding (else provisional); default to the form already attested when usage is unproven. (A deterministic post-check drops any new_part already in the catalog.) Honest confidence; empty if well-curated.\n` +
    `- Echo slug="${part.name}", sequence, and feature_type unchanged.`,
    { schema: FINAL_SCHEMA, label: `synthesize:${part.name}`, phase: 'Synthesize', model: synthModel },
  )

  // Identity is fixed at resolve time; the synthesizer must not reclassify.
  proposal.slug = part.name
  proposal.sequence = seq
  if (part.feature_type) proposal.feature_type = part.feature_type
  // Carry the source verdict through deterministically (don't trust the model to copy it).
  proposal.provenance = proposal.provenance || {}
  if (src.sequence_source && !proposal.provenance.sequence_source) proposal.provenance.sequence_source = src.sequence_source
  proposal._source_verdict = src
  if (!src.verified) {
    proposal.warnings = [...(proposal.warnings || []), `sequence NOT source-verified (${src.blocked ? 'access-blocked -> sourcing/REQUESTS.md' : 'no 100% deposit found'}); do not promote until resolved`]
    proposal.ready_to_apply = false
  }
  log(`[${part.name}] proposal: ${(proposal.features || []).length} feature(s), ${(proposal.functional_claims || []).length} claim(s), ${(proposal.references || []).length} ref(s), confidence=${proposal.confidence}, ready=${proposal.ready_to_apply}`)

  // ---- Verify recs ----
  if (proposal.recommendations && proposal.recommendations.length) {
    const recCheck = await agent(
      `Adversarially vet these curation recommendations for "${part.name}". Be skeptical; default verified=false when unsure. One result per recommendation, keyed by 0-based "index".\n\n` +
      `Recommendations:\n${JSON.stringify(proposal.recommendations.map((r, i) => ({ index: i, ...r })), null, 2)}\n\n` +
      `Existing catalog parts (slugs + synonyms):\n${JSON.stringify(existingNames)}\n\n` +
      `Judge by kind: new_part INVALID if already in the list — and a new_part that EXTRACTS a standalone sub-region is valid ONLY if there is real evidence the sub-region is used alone (its own registry/standard ID, or independent literature/construct use, ≥2 contexts) AND the composite is kept (additive, not destructive); compose valid ONLY if the members are the SAME functional class, are commonly deployed together as ONE unit (real evidence, ≥2 contexts), the atoms are kept, and the proposal sources the composite FRESH from a named deposit (a compose that concatenates member parts is INVALID); rename valid only if the new name is the registry/literature-standard form and not taken; redelimit/split/merge must hold against the biology + research (a redelimit needs EXPERIMENTAL grounding, not consensus; a split applies to a part bundling >1 functional class); metadata/note kept only if accurate. verified=true only if correct AND worth a curator's time; one-line reason.`,
      {
        schema: { type: 'object', properties: { results: { type: 'array', items: { type: 'object', properties: { index: { type: 'integer' }, verified: { type: 'boolean' }, reason: { type: 'string' } }, required: ['index', 'verified'] } } }, required: ['results'] },
        label: `verify-recs:${part.name}`, phase: 'Verify recs', model: WORKER_MODEL,
      },
    )
    const byIndex = new Map(((recCheck && recCheck.results) || []).map((v) => [v.index, v]))
    const n0 = proposal.recommendations.length
    proposal.recommendations = proposal.recommendations
      .map((r, i) => ({ ...r, verified: byIndex.has(i) ? byIndex.get(i).verified : null, verify_reason: byIndex.has(i) ? (byIndex.get(i).reason || '') : '' }))
      .filter((r) => r.verified !== false)
    log(`[${part.name}] recommendations: ${proposal.recommendations.length}/${n0} survived verification`)
  }

  return proposal
}

phase('Locate')
const proposals = (await parallel(parts.map((p) => () => annotateOne(p)))).filter(Boolean)
log(`Done: ${proposals.length}/${parts.length} proposal(s) synthesized`)

// ---- Claim-evidence requests: surface papers whose full text was needed but blocked ----
// (the literature sibling of the sequence-SOURCE request path). Dedup by pmid/doi and
// route each through tools/papers.py request, which is store-aware + self-pruning.
const reqMap = new Map()
for (const pr of proposals) {
  for (const rp of pr.requested_papers || []) {
    const key = rp.pmid ? `pmid:${rp.pmid}` : (rp.doi ? `doi:${rp.doi}` : null)
    if (key && !reqMap.has(key)) reqMap.set(key, rp)
  }
}
const requestedPapers = [...reqMap.values()]
if (requestedPapers.length) {
  phase('Requests')
  log(`${requestedPapers.length} blocked paper(s) needed for claim evidence -> sourcing/REQUESTS.md`)
  await agent(
    `Some functional claims need a primary paper whose full text was inaccessible. For EACH entry below, run:\n` +
    `  python tools/papers.py request [--pmid <pmid>] [--doi <doi>] [--title "<title>"] --unblocks "<unblocks>" --barrier <barrier>\n` +
    `(the command is store-aware and idempotent — it skips papers already deposited and de-dups). Report how many you recorded.\n\n` +
    `Entries:\n${JSON.stringify(requestedPapers, null, 2)}`,
    { schema: { type: 'object', properties: { recorded: { type: 'integer' }, note: { type: 'string' } }, required: ['recorded'] },
      label: 'requests', phase: 'Requests' },
  )
}

// ---- 8. Collection block (cluster only) ------------------------------------
let collection = null
if (!single && proposals.length) {
  phase('Collection')
  collection = await agent(
    `These ${parts.length} parts form a related family (a catalog collection): ${parts.map((p) => p.name).join(', ')}${clusterSource ? ` — shared source: ${clusterSource}` : ''}.\n\n` +
    `Produce a collections.json-ready block:\n` +
    `- references: the KEY primary papers (not every per-element citation) — dedupe, each with title/authors/journal/year/pmid/doi.\n` +
    `- resources: useful EXTERNAL links (registry/kit/database/tool/protocol) — deduped, real working URLs with a clear title.\n` +
    `- name, a kebab-case suggested_id, and a one-paragraph description.\n` +
    `Keep ONLY papers/links the research supports; never fabricate a PMID/DOI/URL.\n\n` +
    `Candidate references:\n${JSON.stringify(pool.references, null, 2)}\n\nCandidate resources:\n${JSON.stringify(pool.resources, null, 2)}`,
    { schema: COLLECTION_SCHEMA, label: 'collection', phase: 'Collection', model: WORKER_MODEL },
  )
  log(`Collection block: ${(collection.references || []).length} reference(s), ${(collection.resources || []).length} resource(s)`)
}

// PROPOSAL-ONLY: the /add-part command merges each proposal via tools/merge_part.py
// (which protects ai-cross-checked/expert-reviewed claims and the curated .md) and
// runs the gates. This engine never writes a part file.
return single
  ? (proposals[0] || { error: `Failed to annotate "${parts[0].name}".` })
  : { source: clusterSource || null, count: proposals.length, proposals, collection,
      requested_papers: requestedPapers }
