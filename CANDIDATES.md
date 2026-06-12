# Candidate roadmap — standard-vector-family coverage

Parts to add so the catalog covers the atomic building blocks of the major
standard vector families. These families are **combinatorial** — each is a menu
of origins / markers / regulated promoters / terminators / regulators / tags —
so we add the *parts*, not the vectors.

**Status of this list:** candidates to gather. Add each as a `parts/candidate/`
stub first (sequence + main feature, no `.md`); annotate to `validated/` later
per the priority queue at the bottom. **A part is only added once its sequence
is sourced from the cited reference — never transcribed from memory.**

Legend — type = Sequence Ontology class · ✓ = already in catalog (not a gap).

---

## pSEVA — complete ✓
All 9 origin slots (R6K, RK2, pBBR1, pRO1600/ColE1, RSF1010, p15A, pSC101, pMB1,
CloDF13), all 6 markers (Ap/Km/Cm/Sm-Sp/Tc/Gm), T0/T1 terminators, RP4 *oriT*,
SEVA *tir*, Pm/XylS are all present. No gaps.

## pZ (Lutz & Bujard 1997, *NAR* 25:1203; Expressys)
Present: PLtetO-1✓, PA1/O4/O3✓, origins pMB1/p15A/pSC101/ts-ori101✓, tetR/lacI/araC✓.

| Part | Type | What it is | Sequence source |
|---|---|---|---|
| PLlacO-1 | promoter | λ PL + 2× lacO; LacI-repressible (IPTG) | Lutz & Bujard 1997 Fig 1 ✓ stubbed |
| Plac/ara-1 | promoter | lac/ara hybrid; AraC+LacI control (IPTG+arabinose) | Lutz & Bujard 1997 Fig 1 ✓ stubbed |
| PA1lacO-1 | promoter | phage T7 A1 core + 2× lacO; LacI-repressible (IPTG) | Lutz & Bujard 1997 Fig 1 ✓ stubbed |
| ~~PN25~~ | ~~promoter~~ | DROPPED (redundant) — not in Fig 1; pQE carries PN25/O = existing **PT5_lacO**, and native operator-free PN25 would need internal operator deletion. | — |
| ~~RBSII~~ | ~~RBS~~ | DROPPED (redundant) — not in Fig 1; the only available annotation (`AAAGAGGAGAAA`) = existing **B0034**. | — |

## pET (T7 system; Studier; Novagen pET maps)
Present: PT7✓, T7lac✓, T7 terminator✓, lacI/PlacIq✓, 6xHis/T7-tag/thrombin/TEV✓.

| Part | Type | What it is | Sequence source |
|---|---|---|---|
| T7 g10 leader | ribosome_entry_site | T7 gene-10 translational enhancer/RBS | Olins & Rangwala 1989; pET map |
| S-tag | polypeptide_domain | 15-aa S-peptide (KETAAAKFERQHMDS), RNase-S | Novagen pET; Kim & Raines |
| enterokinase site | polypeptide_domain | DDDDK↓ protease cleavage site | pET maps |
| rop / rom | CDS | ColE1 Rop, ~63 aa copy-number repressor | UniProt P03051 ✓ stubbed |

## Yeast expression (pRS / pYES / pGAL; SGD)
Present: CEN6-ARS209✓, URA3✓.

| Part | Type | What it is | Sequence source |
|---|---|---|---|
| GAL1 | promoter | galactose-inducible (442 bp) | pYES2 (Addgene 244550) ✓ stubbed |
| TDH3 | promoter | GPD/GAP, strong constitutive (668 bp) | yeast vector (Addgene 239293) ✓ stubbed |
| TEF1 | promoter | strong constitutive (414 bp) | pJF89 (Addgene 253756) ✓ stubbed |
| ADH1 | promoter | medium constitutive (705 bp) | pGADT7 (Addgene 233529) ✓ stubbed |
| CYC1 terminator | terminator | standard yeast terminator (248 bp) | pYES2 (Addgene 244550) ✓ stubbed |
| ADH1 terminator | terminator | standard yeast terminator (188 bp) | pGADT7 (Addgene 233529) ✓ stubbed |
| 2micron ori | origin_of_replication | high-copy yeast ori (878 bp; vs CEN/ARS) | pYES2 (Addgene 244550) ✓ stubbed |
| HIS3 | CDS | auxotrophic marker | UniProt P06633 ✓ stubbed |
| LEU2 | CDS | auxotrophic marker | UniProt P04173 ✓ stubbed |
| TRP1 | CDS | auxotrophic marker | UniProt P00912 ✓ stubbed |
| ~~KanMX~~ | ~~CDS~~ | DROPPED — non-atomic: KanMX is a *cassette* (Ashbya TEF promoter + kanr ORF + TEF terminator), and its ORF = existing **kanR_Tn903**. The atomic split would be the Ashbya TEF promoter/terminator as their own parts (not requested). | — |

## Mammalian core
Present: PSV40✓, CAG✓, TRE3GV✓, hU6✓, SV40 pA✓, IRES✓.

All four are now **stubbed** in `parts/candidate/`, extracted as cleanly-annotated
single features from standard reference vectors (the reference-plasmid approach
works perfectly here — no boundary inference needed).

| Part | Type | What it is | Sequence source |
|---|---|---|---|
| CMV | promoter | CMV IE enhancer/promoter (584 bp; the default) | pcDNA3.1(+) (Addgene 255272) ✓ stubbed |
| EF1a | promoter | EF-1 alpha, full intron-containing (1179 bp) | pCDH-EF1 lenti (Addgene 207805) ✓ stubbed |
| hPGK | promoter | human PGK1, medium constitutive (511 bp) | PGK lenti (Addgene 253233) ✓ stubbed |
| WPRE | misc_feature | woodchuck post-transcriptional regulatory element (589 bp) | pCDH-EF1 lenti (Addgene 207805) ✓ stubbed |

## iGEM / Anderson + BioBrick (parts.igem.org) — stubs in ✓
Present (Anderson): J23104, J23107, J23108, J23110, J23119✓.

All rows below are now **stubbed** in `parts/candidate/` (sequences pulled from
the iGEM Registry XML API, canonical `...gctagc` suffix matching the family).

| Part | Type | What it is | Sequence source |
|---|---|---|---|
| J23100, J23101, J23102, J23106, J23109, J23114, J23116, J23117 | promoter | rest of the Anderson constitutive series (known relative strengths) | iGEM Registry ✓ |
| B0034 RBS | RBS | the standard BioBrick RBS | iGEM Registry ✓ |
| B0015 terminator | terminator | the standard BioBrick double terminator (B0010+B0012) | iGEM Registry ✓ |

## Marionette inducible sensors (Meyer et al. 2019; Addgene Marionette kit)
Present: PphlF/PhlF✓, ptet/tetR✓, ParaBAD/araC✓.

Add the cognate **promoter + TF** pairs for the orthogonal inducible set:
Pcym/CymR (cumate), Pvan/VanR (vanillate), Psal/NahR (salicylate),
PttgR/TtgR (naringenin), Pcin/CinR. Source: Meyer 2019 / Addgene kit #1000000137.

---

## Validation queue — grouped by shared source (one workflow run per group)

Validate in **related clusters, not one part at a time**: every part in a group
shares the same primary literature, so a single `annotate-part` run researches
that source once and maps the sub-features onto all of them — no duplicated
research. Groups are ordered by priority. `✓ stubs in` = sequence stubs already
sit in `parts/candidate/`; the rest still need stubs gathered first.

**G1 — pZ regulated promoters** · Lutz & Bujard 1997, *NAR* 25:1203 · ✓ stubs in (PLlacO-1, Plac/ara-1, PA1lacO-1)
PLlacO-1 · Plac/ara-1 · PA1lacO-1  (PN25, RBSII dropped as redundant)
All three stubbed from L&B Fig 1 (canonical -35/-10/operator sequences). One
workflow run validates the trio; the figure pins the -35/-10/operator
architecture. PN25/RBSII dropped — see the pZ table above.

**G2 — yeast auxotrophic markers** · SGD / UniProt · ✓ stubs in (HIS3, LEU2, TRP1)
HIS3 · LEU2 · TRP1  (KanMX dropped — non-atomic cassette / ORF = kanR_Tn903)
Coding parts, protein-canonical; shared marker-gene framing.

**G3 — iGEM Anderson + BioBrick** · parts.igem.org (Anderson promoter collection) · ✓ stubs in
J23100/101/102/106/109/114/116/117 · B0034 RBS · B0015 terminator
One constitutive-promoter family (shared -35/-10 scaffold, relative-strength
table) + the two standard BioBrick parts — a single research pass covers all.

**G4 — mammalian core** · standard expression-vector literature · ✓ stubs in
CMV · EF1a · hPGK · WPRE
All four extracted from standard reference vectors (pcDNA3.1, pCDH-EF1, PGK
lenti) as cleanly-annotated single features.

**G5 — yeast promoters / terminators** · Mumberg et al. 1995; SGD · ✓ stubs in
GAL1 · TDH3(GPD) · TEF1 · ADH1 promoters · CYC1 · ADH1 terminators · 2micron ori
All extracted as cleanly-annotated single features from standard yeast vectors
(pYES2, pGADT7, pJF89, a TDH3 vector). KanMX dropped (non-atomic — see G2).

**G6 — Marionette inducible sensors** · Meyer et al. 2019; Addgene kit #1000000137
Pcym/CymR · Pvan/VanR · Psal/NahR · PttgR/TtgR · Pcin/CinR
Validate each **promoter + its cognate TF as a pair** (the TF is the promoter's
regulator) — one paper covers the whole orthogonal set.

**G7 — pET extras** · Studier; Novagen pET maps
T7 g10 leader · S-tag · enterokinase site · rop (ColE1)

Priority: **G1, G2, G3** first (workhorses; G2/G3 already stubbed) → **G4, G5**
→ **G6, G7**.
