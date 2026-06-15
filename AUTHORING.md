# Authoring a part

How a part is created and validated in this repo. This is the agent-facing
standard operating procedure behind the `/add-part` command; humans can follow it
directly too. It complements [`CONTRIBUTING.md`](CONTRIBUTING.md) (conventions)
and [`schema/part.schema.json`](schema/part.schema.json) (the record format).

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

A part is a **candidate** (a bare sequence + minimal info) until it becomes a
**curated record** — sourced provenance, SO-typed main feature, located sub-features,
references and functional_claims — *and* gains a curated `.md`; then it moves to
`parts/validated/` and is **validated** (`tools/validate_parts.py` enforces the bar).
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
  parts, not one. See `CONTRIBUTING.md` → *Part conventions*.
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
  functional-class level (promoter `SO:0000167`, RBS `SO:0000139`, CDS
  `SO:0000316`, …); `tools/new_part.py` stamps the main feature's `db_xref`.
- **Claims cite their evidence.** Each `functional_claim` carries a `source`
  (PMID/DOI) and, where possible, a verbatim `quote` and a `figure`/`table`/`page`
  locator — prefer a quote from the **primary** source (`quote_source: primary`);
  if you only transcribe the catalog's own prose, mark `quote_source:
  catalog-doc`. Never invent a figure number you have not read.

## Procedure

1. **Check it isn't already there.** Search `catalog.json` and `parts/` for the
   name and its synonyms, and run `python tools/catalog_overlap.py --slug <slug>`
   (or `--seq …`) to detect **sequence** overlap/containment with existing parts. If a
   part's sequence **overlaps** yours (a sub/superset, near-identical sibling, or a
   boundary variant of the same element), **refine that part** rather than adding a
   near-duplicate; only add a new part for a genuinely distinct functional unit.
   (Re-delimiting a boundary is **not** trivial — see step 4.)
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
5. **Set provenance.** Replace `provenance.sequence_source` with the real source.
6. **Add functional knowledge.** For any inducer / dynamic range / strength /
   host range claim, append a `functional_claims[]` entry with `type`, `label`,
   `value`, `source` (+ `quote`/`figure`), `confidence`, and `review_status`.
7. **Validate it (candidate).** Run the gates:
   ```bash
   python tools/validate_parts.py      # JSON vs schema
   python tools/build_gb.py            # JSON -> .gb
   python tools/build_catalog.py       # catalog.json + site
   python tools/build_rdf.py           # catalog.ttl + .jsonld
   python tools/check_content.py       # agnostic-prose guard
   pyshacl -s tools/shapes.ttl -i rdfs catalog.ttl
   python -m pytest tests/ -q
   ```
8. **Promote to validated.** When the record clears the completeness bar (sourced
   provenance, SO-typed main feature, located sub-features, ≥1 reference, ≥1
   functional_claim), move the `.json` to `parts/validated/` and write the curated
   `parts/validated/<slug>.md` (sections: Origin, Properties, Use, References) — the
   agent writes this, so a fully-researched part is validated, not left a candidate.
   Re-run step 7 (`validate_parts.py` enforces the bar). Leave a part in
   `candidate/` only when it is genuinely bare (sequence + minimal info).
9. **Commit + open a PR** with the `<slug>.json`, the generated `.gb`,
   `catalog.json`, and `catalog.ttl`/`.jsonld`. An expert review promotes claims
   to `review_status: expert-reviewed`.

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
