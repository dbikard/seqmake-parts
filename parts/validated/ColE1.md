The ColE1/pMB1-family origin of replication: the 589 bp region from the RNA II promoter -35 to the DNA replication start, carrying the convergent RNA I / RNA II promoter pair that sets plasmid copy number.

## Origin
This is the classic ColE1(pMB1) origin region used in the pUC/pBR322 plasmid families. DNA replication initiates from an RNA primer: the RNA II transcript is synthesized from a promoter several hundred bp upstream of the origin and is matured by RNase H into the DNA-replication primer ([PMID 6156450](https://pubmed.ncbi.nlm.nih.gov/6156450/)). A second, convergent promoter produces the ~108 nt antisense small RNA RNA I, which inhibits RNA II primer formation and thereby controls copy number ([PMID 6165011](https://pubmed.ncbi.nlm.nih.gov/6165011/)).

## Properties
Two sigma-70 promoters fire toward each other (convergent): the RNA II promoter on the top strand (-35 TTGAGA at 1-6, -10 CGTAAT at 22-27) and the RNA I promoter on the bottom strand (-35 TTGAAG, -10 GCTACA). RNA I is the stronger promoter and RNA II the weaker (transcribed ~5-fold less), consistent with the non-consensus RNA II -10 ([PMID 2434459](https://pubmed.ncbi.nlm.nih.gov/2434459/)). Copy number is set by the RNA I:RNA II ratio and is further lowered in trans by the Rop/Rom protein (present in pBR322, absent in high-copy pUC vectors).

## Boundaries
The part is pBR322 (GenBank J01749) bases 2534-3122 on the minus strand, the span conventionally annotated as the high-copy ori (SnapGene/Addgene "ori", 589 bp). It starts at the RNA II promoter -35 and ends at the RNA-to-DNA transition, where RNase H processes the RNA II primer ([PMID 6156450](https://pubmed.ncbi.nlm.nih.gov/6156450/)). Tomizawa et al. mapped the first DNA nucleotide to one of three consecutive nucleotides (dA, dA, dC) after a run of five A residues in which the primer RNA turns into DNA ([PMID 325558](https://pubmed.ncbi.nlm.nih.gov/325558/)); these are pBR322 2533-2531 (the ColE1 deposit J01566 marks the start at its base 1197, ±1, = pBR322 2532). The part ends one base before them, at pBR322 2534. pBR322's own record marks the origin at 2535 without a citation. The other ColE1-family origins in the catalog (`p15A`, `RSF_ori`, `CloDF13_ori`) end at the same aligned base. It leaves out the backbone on either side: 20 bp towards *bla*, and the 183 bp past the RNA-to-DNA transition (pBR322 2351-2533). Those 183 bp carry pBR322's lagging-strand priming signals, a primosome assembly site (factor Y effector site; [PMID 6279609](https://pubmed.ncbi.nlm.nih.gov/6279609/)) and a DnaA box, and are a separate part, [`pBR322_pas_DnaA`](pBR322_pas_DnaA.md), starting at the base after this part's 3' end. Many vectors carry only part of them or none.

## Use
Standard high-copy origin for E. coli cloning and expression plasmids. Drop-in replaceable with other compatibility-group origins (p15A, pSC101) when co-maintenance is needed; ColE1-type origins are incompatible with each other.

## References
- [PMID 6156450](https://pubmed.ncbi.nlm.nih.gov/6156450/) — Itoh & Tomizawa 1980, RNA primer formation by RNase H (RNA II mechanism).
- [PMID 325558](https://pubmed.ncbi.nlm.nih.gov/325558/) — Tomizawa et al. 1977, the replication start site (dA, dA or dC after a run of five A residues).
- [PMID 6165011](https://pubmed.ncbi.nlm.nih.gov/6165011/) — Tomizawa et al. 1981, RNA I antisense inhibition of primer formation.
- [PMID 6279609](https://pubmed.ncbi.nlm.nih.gov/6279609/) — Marians et al. 1982, the pBR322 factor Y (primosome assembly) sites next to the origin.
- [PMID 2434459](https://pubmed.ncbi.nlm.nih.gov/2434459/) — Lin-Chao & Bremer 1987, relative activities of the RNA I and RNA II promoters.
