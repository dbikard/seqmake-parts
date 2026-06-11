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
| PN25 | promoter | phage T5/N25 strong constitutive core (basis of the regulated derivatives) | Gentz & Bujard 1985; Lutz & Bujard 1997 |
| PLlacO-1 | promoter | λ PL + 2× lacO; LacI-repressible (IPTG) | Lutz & Bujard 1997 |
| Plac/ara-1 | promoter | lac/ara hybrid; AraC+LacI control (IPTG+arabinose) | Lutz & Bujard 1997 |
| RBSII | ribosome_entry_site | strong synthetic RBS of the pQE/pZ system | Bujard pDS/pQE; Lutz & Bujard 1997 |

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
| GAL1 promoter | promoter | galactose-inducible | SGD / S. cerevisiae S288C |
| TDH3 (GPD) promoter | promoter | strong constitutive | SGD |
| TEF1 promoter | promoter | strong constitutive | SGD |
| ADH1 promoter | promoter | medium constitutive | SGD |
| CYC1 terminator | terminator | standard yeast terminator | SGD |
| ADH1 terminator | terminator | standard yeast terminator | SGD |
| HIS3 | CDS | auxotrophic marker | UniProt P06633 ✓ stubbed |
| LEU2 | CDS | auxotrophic marker | UniProt P04173 ✓ stubbed |
| TRP1 | CDS | auxotrophic marker | UniProt P00912 ✓ stubbed |
| KanMX | CDS | G418 marker (kanr/Tn903 ORF; have kanR Tn903✓) | Wach et al. 1994 |
| 2µ origin | origin_of_replication | high-copy yeast ori (vs CEN/ARS low-copy) | S. cerevisiae 2-micron plasmid |

## Mammalian core
Present: PSV40✓, CAG✓, TRE3GV✓, hU6✓, SV40 pA✓, IRES✓.

| Part | Type | What it is | Sequence source |
|---|---|---|---|
| CMV promoter | promoter | CMV IE enhancer/promoter (the default) | hCMV; standard reference plasmid |
| EF1α promoter | promoter | EF-1 alpha (full, intron-containing) | human EEF1A1 |
| PGK promoter | promoter | mouse phosphoglycerate kinase | mouse Pgk1 |
| WPRE | misc_feature | woodchuck post-transcriptional regulatory element | WHV; Zufferey 1999 |

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

**G1 — pZ regulated promoters** · Lutz & Bujard 1997, *NAR* 25:1203
PN25 · PLlacO-1 · Plac/ara-1 · RBSII
One paper defines the whole regulated-promoter + RBSII architecture (-35/-10,
lac/tet operator placement, ribosome site) — research it once for all four.

**G2 — yeast auxotrophic markers** · SGD / UniProt · ✓ stubs in (HIS3, LEU2, TRP1)
HIS3 · LEU2 · TRP1 · KanMX
Coding parts, protein-canonical; shared marker-gene framing.

**G3 — iGEM Anderson + BioBrick** · parts.igem.org (Anderson promoter collection) · ✓ stubs in
J23100/101/102/106/109/114/116/117 · B0034 RBS · B0015 terminator
One constitutive-promoter family (shared -35/-10 scaffold, relative-strength
table) + the two standard BioBrick parts — a single research pass covers all.

**G4 — mammalian core** · standard expression-vector literature
CMV promoter · EF1α promoter · PGK promoter · WPRE

**G5 — yeast promoters / terminators** · Mumberg et al. 1995; SGD
GAL1 · TDH3(GPD) · TEF1 · ADH1 promoters · CYC1 · ADH1 terminators · 2µ origin

**G6 — Marionette inducible sensors** · Meyer et al. 2019; Addgene kit #1000000137
Pcym/CymR · Pvan/VanR · Psal/NahR · PttgR/TtgR · Pcin/CinR
Validate each **promoter + its cognate TF as a pair** (the TF is the promoter's
regulator) — one paper covers the whole orthogonal set.

**G7 — pET extras** · Studier; Novagen pET maps
T7 g10 leader · S-tag · enterokinase site · rop (ColE1)

Priority: **G1, G2, G3** first (workhorses; G2/G3 already stubbed) → **G4, G5**
→ **G6, G7**.
