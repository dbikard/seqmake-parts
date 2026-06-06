# PphlF — PhlF-repressible promoter

A synthetic, **PhlF-repressible** σ70 promoter: strongly transcribed by
default and switched **off** when the TetR-family repressor **PhlF** binds its
operator. Repression is relieved by the small-molecule inducer
**2,4-diacetylphloroglucinol (DAPG)**.

## Origin

PphlF was built by **Stanton et al. (2014)** while mining *Pseudomonas* PhlF
repressor–operator pairs for orthogonal logic gates. A strong constitutive
scaffold — the Anderson promoter **J23119** (−35 `TTGACA`) — carries the natural
**phO** operator overlaid across its −10, so that PhlF-dimer binding occludes
σ70 recognition. The 30-bp operator (the inverted repeat
`ATGATACG…CGTATCGT`) was first characterised at the *phlA* promoter of
*Pseudomonas fluorescens* F113 by **Abbas et al. (2002)**. The exact part
sequence used here is the one pinned by the Cello design-automation toolkit
(**Nielsen et al. 2016**).

## Properties

- 51 bp, σ70-type promoter.
- **−35** `TTGACA` (J23119-derived), 17-bp spacer.
- **−10** `TATCGT` — degenerate, overlapped by the operator (the basis of repression).
- **phO operator** — 30-bp PhlF inverted repeat at the 3′ end; PhlF binds as a dimer.
- Strong when de-repressed; PhlF gives high-fold repression (~80× in the source
  work), induced by DAPG.

## Use

Inducible / repressible expression and genetic-circuit building blocks: pair
PphlF with a PhlF expression cassette to make a DAPG-responsive ON/OFF switch,
or use it as one orthogonal repressor channel within the Cello sensor/gate
library.

## References

- Abbas A, Morrissey JP, Marquez PC, Sheehan MM, Delany IR, O'Gara F.
  *Characterization of interactions between the transcriptional repressor PhlF
  and its binding site at the phlA promoter in* Pseudomonas fluorescens *F113.*
  J Bacteriol. 2002;184(11):3008–3016.
  [PMID 12003942](https://pubmed.ncbi.nlm.nih.gov/12003942/)
- Stanton BC, Nielsen AA, Tamsir A, Clancy K, Peterson T, Voigt CA. *Genomic
  mining of prokaryotic repressors for orthogonal logic gates.* Nat Chem Biol.
  2014;10(2):99–105. [PMID 24316737](https://pubmed.ncbi.nlm.nih.gov/24316737/)
- Nielsen AA, Der BS, Shin J, et al. *Genetic circuit design automation.*
  Science. 2016;352(6281):aac7341.
  [PMID 27034378](https://pubmed.ncbi.nlm.nih.gov/27034378/)
