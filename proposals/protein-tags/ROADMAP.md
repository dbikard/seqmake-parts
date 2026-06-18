# Protein-tag series — batch roadmap

Goal (agreed 2026-06-18 with the user): a **comprehensive series of protein tags**
in the catalog. Scope: **all four tag categories** (affinity/purification ·
epitope/detection · solubility + protease cleavage sites · conjugation/self-labeling),
**~30–45 parts**, AND **enrich + validate the 16 existing bare migrated stubs** (they
currently have no `sequence_source`, no references, no `functional_claims` —
`migrated_from: genbank`, `ai-generated`).

This is driven by the **`/add-part` → `annotate-part` engine** (proposal-only;
merge via `tools/merge_part.py`; gates via `tools/check_all.py`). Per
[AUTHORING.md](../../AUTHORING.md): sequence from a cited source never memory; coding
parts are protein-canonical and defer biology to UniProt (`import_uniprot_features.py`);
short **synthetic** epitope/motif peptides (His, FLAG, Strep, protease sites) have **no
UniProt entry** — their `sequence_source` is the **defining publication**, recorded in
`provenance.sequence_source`.

## Sourcing model for tags (two paths)

- **UniProt-backed** (a real protein / engineered enzyme): pass the accession as the
  engine `refs`; the Source phase verifies via UniProt and `import_uniprot_features.py`
  baked the residue features. (GST, MBP, Trx, NusA, SUMO, HaloTag, SNAP/CLIP, birA,
  SpyCatcher, SnoopCatcher.)
- **Synthetic peptide** (designed/selected motif or epitope sub-peptide): no UniProt
  accession of its own → `sequence_source` = the **defining paper**; if it is a
  sub-peptide of a real protein, name the parent protein + residues in a note. (His,
  FLAG, Strep-tag II, Twin-Strep, S-tag, AviTag, SpyTag, SnoopTag, LPETG/sortase, all
  epitope tags, all protease-site linkers.)

## Inventory (✓ = existing bare stub to ENRICH · + = NEW part to create)

### 1 — Affinity / purification
| Tag | slug | seq kind | source (authoritative) | defining ref |
|---|---|---|---|---|
| ✓ His6 (8x/10x as synonyms) | `6xHis` | synthetic | designed polyHis / IMAC | Hochuli 1987; Janknecht 1991 |
| ✓ Strep-tag II | `Strep_tag` | synthetic | selected peptide (WSHPQFEK) | Schmidt & Skerra 2007 |
| + Twin-Strep-tag | `Twin_Strep_tag` | synthetic | tandem Strep-tag II | Schmidt 2013 |
| ✓ FLAG | `FLAG` | synthetic | designed (DYKDDDDK); 3xFLAG synonym | Hopp 1988 |
| ✓ GST | `GST` | UniProt **P08515** | *S. japonicum* GST (Sj26) | Smith & Johnson 1988 |
| ✓ S-tag | `S-tag` | sub-peptide of **P61823** | RNase A residues 1–15 (S-peptide) | Kim & Raines 1993 |
| ✓ HaloTag | `HaloTag` | engineered (DhaA-based) | modified haloalkane dehalogenase | Los 2008 |
| + MBP | `MBP` | UniProt **P0AEX9** | *E. coli* maltose-binding protein (malE) | di Guan 1988; Maina 1988 |
| + CBP | `CBP_tag` | synthetic | calmodulin-binding peptide | Stofko-Hahn 1992 |
| + SBP-tag | `SBP_tag` | synthetic | streptavidin-binding peptide | Keefe 2001 |

### 2 — Epitope / detection
| Tag | slug | seq kind | parent protein | defining ref |
|---|---|---|---|---|
| ✓ HA | `HA` | sub-peptide | influenza HA (98–106) | Wilson 1984; Field 1988 |
| ✓ c-Myc | `Myc` | sub-peptide | human MYC (410–419) | Evan 1985 |
| ✓ T7-tag | `T7_tag` | sub-peptide | T7 gene-10 capsid N-term | Novagen / Lutz-Freyermuth 1990 |
| ✓ E-tag | `E-tag` | synthetic | **stored seq ends `…PLEPA`; canonical is `…PLEPR` — engine to resolve** | GE/Pharmacia |
| + V5 | `V5_tag` | sub-peptide | SV5 P/V protein | Southern 1991 |
| + VSV-G | `VSVG_tag` | sub-peptide | VSV glycoprotein | Kreis 1986 |
| + ALFA-tag | `ALFA_tag` | synthetic (de novo helix) | designed | Götzke 2019 |
| + Spot-tag | `Spot_tag` | synthetic | designed (β-strand) | Virant 2018 |

### 3 — Solubility partners + protease cleavage sites
| Tag | slug | seq kind | source | defining ref |
|---|---|---|---|---|
| ✓ SUMO | `SUMO` | UniProt | **stored seq looks like human SUMO-1 (P63165); common fusion tag is yeast Smt3 (Q12306) — engine to resolve identity** | Malakhov 2004 |
| + Thioredoxin (Trx) | `Trx_tag` | UniProt **P0AA25** | *E. coli* trxA | LaVallie 1993 |
| + NusA | `NusA` | UniProt **P0AFF6** | *E. coli* nusA | Davis 1999 |
| (MBP, GST listed under affinity — also solubility partners; cross-note) | | | | |
| ✓ TEV site | `TEV_site` | synthetic motif | ENLYFQ↓(G/S) | Carrington 1988; Kapust 2002 |
| ✓ thrombin site | `thrombin_site` | synthetic motif | LVPR↓GS | Chang 1985 |
| ✓ enterokinase site | `enterokinase_site` | synthetic motif | DDDDK↓ | Maroux 1971 / vendor maps |
| + PreScission / HRV 3C | `HRV3C_site` | synthetic motif | LEVLFQ↓GP | Cordingley 1990; Walker 1994 |
| + Factor Xa | `FactorXa_site` | synthetic motif | IEGR↓ / IDGR | Nagai & Thøgersen 1984 |

(SUMO cleavage is by Ulp1/SUMO-protease and recognizes SUMO tertiary structure, **not**
a linear motif → no separate site part; noted on `SUMO`.)

### 4 — Conjugation / self-labeling
| Tag | slug | seq kind | source | defining ref |
|---|---|---|---|---|
| ✓ AviTag | `AviTag` | synthetic | BirA acceptor peptide (GLNDIFEAQKIEWHE) | Beckett 1999 |
| ✓ BirA | `birA` | UniProt **P06709** | *E. coli* biotin ligase | Beckett 1999 |
| + SpyTag | `SpyTag` | from FbaB CnaB2 | *S. pyogenes* | Zakeri 2012 |
| + SpyCatcher | `SpyCatcher` | from FbaB CnaB2 | *S. pyogenes* | Zakeri 2012 |
| + SnoopTag | `SnoopTag` | from RrgA | *S. pneumoniae* | Veggiani 2016 |
| + SnoopCatcher | `SnoopCatcher` | from RrgA | *S. pneumoniae* | Veggiani 2016 |
| + SortaseA motif | `LPETG_tag` | synthetic motif | LPXTG sorting signal | Mazmanian 1999; Popp 2007 |
| + SNAP-tag | `SNAP_tag` | engineered (hAGT) | O6-alkylguanine-DNA AGT | Keppler 2003 |
| + CLIP-tag | `CLIP_tag` | engineered (SNAP variant) | benzylcytosine substrate | Gautier 2008 |

**Totals:** 16 enrich (✓) + ~21 new (+) ≈ **37 parts**.

## Engine clusters (shared literature → research once)

True shared-source clusters (run as one engine `cluster`):
- **C-strep**: `Strep_tag` + `Twin_Strep_tag` (Schmidt & Skerra / Schmidt 2013)
- **C-spy**: `SpyTag` + `SpyCatcher` (Zakeri 2012, one paper)
- **C-snoop**: `SnoopTag` + `SnoopCatcher` (Veggiani 2016, one paper)
- **C-snapclip**: `SNAP_tag` + `CLIP_tag` (Keppler 2003 + Gautier 2008)
- **C-avi**: `AviTag` + `birA` (Beckett 1999; cognate substrate+enzyme)
- **C-protease**: the 5 protease sites (a coherent family; shared "cleavage-site" framing
  even though each enzyme has its own ref)

Everything else runs as a **singleton** (own defining paper; the engine scales down — no
cluster sharing for a singleton).

## Collections (category sub-collections; membership lives on each part via `collection=`)
- `affinity-tags` · `epitope-tags` · `solubility-tags` · `protease-cleavage-sites` ·
  `conjugation-tags`. Each gets a `collections.json` block. (Decide vs one flat
  `protein-tags` collection at merge time — leaning sub-collections for browsability.)

## Execution waves (commit per wave; proposal-only engine writes nothing until merge)
- **W0 — validation (this session):** prove BOTH sourcing paths on existing stubs before
  scaling — one UniProt-path enrich (`GST`, P08515) + one synthetic-peptide enrich
  (`6xHis`). Confirm proposals are source-verified + `ready_to_apply`, merge, gate, promote.
- **W1 — affinity flagships (enrich):** `FLAG`, `Strep_tag`(+`Twin_Strep_tag` new), `S-tag`, `HaloTag`.
- **W2 — epitope tags:** enrich `HA`/`Myc`/`T7_tag`/`E-tag`; new `V5`/`VSVG`/`ALFA`/`Spot`.
- **W3 — solubility + protease:** enrich `SUMO`; new `MBP`/`Trx`/`NusA`; C-protease cluster.
- **W4 — conjugation:** C-avi (enrich), C-spy, C-snoop, C-snapclip; `LPETG_tag`.
- **W5 — remaining affinity:** `CBP_tag`, `SBP_tag`.

## Open curation calls (escalate, don't guess)
- `E-tag` sequence (`…PLEPA` vs canonical `…PLEPR`) — let the engine source; likely fix to `R`.
- `SUMO` identity (human SUMO-1 vs yeast Smt3) — engine to resolve which the catalog should carry.
- Collection granularity: 5 category sub-collections vs one `protein-tags` collection.
- His variants (8x/10x) — synonyms on `6xHis`, not separate parts (the existing record already lists them).
- 3xFLAG — variant/synonym note on `FLAG`, or a separate `3xFLAG` part? (default: synonym + note.)
