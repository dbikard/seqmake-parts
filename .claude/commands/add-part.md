---
description: Research, annotate and add a new DNA part to the catalog (canonical JSON + optional curated prose), then validate and build.
argument-hint: <part name> [feature type]
allowed-tools: Bash, Read, Write, Edit, Grep, Glob, WebSearch, WebFetch
---

You are adding a part to this DNA parts catalog. Follow the standard operating
procedure in @AUTHORING.md exactly; it is the source of truth for the rules and
the record format (@schema/part.schema.json).

Part to add: **$ARGUMENTS**

Work through the SOP and do not skip the hard rules — most importantly:

- **The sequence must come from a cited source, never from memory.** Find it in a
  primary paper or a registry (Addgene / iGEM / SEVA / UniProt / NCBI) and record
  exactly where in `provenance.sequence_source`. If you cannot source the
  sequence, stop and report that — do not invent or recall one.
- Keep prose **lab- and tool-agnostic** (`tools/check_content.py` enforces this).
- Type the part and sub-features with **Sequence Ontology** terms.
- **Protein/CDS parts defer biology to UniProt:** stamp a required `UniProt:…`
  (or `NCBI:…`) accession and do NOT hand-author residue-level features (domains,
  active sites, binding residues, PTMs). Instead run
  `python tools/import_uniprot_features.py <slug>` to import them from UniProt
  (cached + provenance, baked into the `.gb`). Only hand-author the engineering
  layer (role, functional_claims, cognate partners).
- Every `functional_claim` cites its evidence (PMID/DOI + a verbatim quote and,
  when you have actually read it, a figure/table locator). Never fabricate a
  figure number. Mark `quote_source: primary` vs `catalog-doc` honestly, and set
  `review_status: ai-generated` and an honest `confidence`.

Concretely:

1. Check the name + synonyms aren't already in `catalog.json` / `parts/`. If they
   are, improve that record instead of duplicating.
2. Research the sequence and the key references.
3. Scaffold with `tools/new_part.py` (see AUTHORING.md for flags), then edit the
   resulting `parts/<status>/<slug>.json` to add sub-features, references,
   provenance, and functional_claims.
4. Default to a **candidate** (JSON only). Only create the validated `.md` if you
   are also writing curated prose (Origin / Properties / Use / References).
5. Run every gate and make them pass: `tools/validate_parts.py`,
   `tools/build_gb.py`, `tools/build_catalog.py`, `tools/build_rdf.py`,
   `tools/check_content.py`, `pyshacl -s tools/shapes.ttl -i rdfs catalog.ttl`,
   and `pytest tests/ -q`.
6. Show me the new `<slug>.json` (and `.md` if any) and a summary of what you
   sourced and from where, before committing. Do not open a PR unless I ask.

If anything is ambiguous (which sequence variant, which feature type, conflicting
literature), ask me rather than guessing.
