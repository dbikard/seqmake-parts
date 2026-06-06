Ptet2 is a 29-bp sigma70 promoter fragment that is, by exact sequence, the pBR322 tet (P2) constitutive promoter (-35 + 17-bp spacer + -10), with ClaI and HindIII cloning sites in the spacer and no tet operator.

## Origin
The 29-bp sequence is an exact substring of the *E. coli* plasmid pBR322 tet promoter region (pBR322 positions ~1-38; Sutcliffe 1979 [PMID 383387](https://pubmed.ncbi.nlm.nih.gov/383387/)). Its -35/-10 elements and transcription start were characterized as a sigma70 promoter by Harley et al. 1988 ([PMID 3045754](https://pubmed.ncbi.nlm.nih.gov/3045754/)). The -35 (TTGACA) is also the shared prefix of the J23119/Anderson constitutive promoter scaffold, and the overall consensus-promoter architecture follows the design discussed by Lutz & Bujard 1997 ([PMID 9092630](https://pubmed.ncbi.nlm.nih.gov/9092630/)). This is the pBR322 tetA(C) lineage, distinct from the Tn10 TetR/tetO inducible system (Hillen & Berens 1994 [PMID 7826010](https://pubmed.ncbi.nlm.nih.gov/7826010/)).

## Properties
- **-35 box** [0:6] TTGACA — perfect sigma70 -35 consensus (seqmake minus35_score = 1.0).
- **Spacer** [6:23] — 17 bp, optimal sigma70 spacing; carries the cloning sites below.
- **-10 box** [23:29] TTTAAT — strong -10 variant (5/6 to TATAAT).
- **ClaI site** [13:19] ATCGAT and **HindIII site** [19:25] AAGCTT — restriction-cloning scars in the spacer; the HindIII site overlaps the -10 at positions 23-24.
- **No tet operator (tetO).** Despite the name, the sequence is constitutive and is **not** TetR-repressible or anhydrotetracycline-inducible.

## Use
A short constitutive sigma70 promoter element. The internal ClaI and HindIII sites make it a restriction-cloning handle. As currently delimited it ends at the -10 and lacks the +1 transcription start, so the boundaries should be extended downstream before use as a functional expression promoter. If aTc-inducible behavior is intended, a genuine tetO-bearing promoter (e.g. PLtetO-1) plus a TetR repressor should be used instead.

## References
- [PMID 3045754](https://pubmed.ncbi.nlm.nih.gov/3045754/) — Harley et al. 1988, *Transcription initiation at the tet promoter and effect of mutations*, Nucleic Acids Res.
- [PMID 9092630](https://pubmed.ncbi.nlm.nih.gov/9092630/) — Lutz & Bujard 1997, *Independent and tight regulation of transcriptional units in E. coli via the LacR/O, TetR/O and AraC/I1-I2 regulatory elements*, Nucleic Acids Res.
- [PMID 383387](https://pubmed.ncbi.nlm.nih.gov/383387/) — Sutcliffe 1979, *Complete nucleotide sequence of the E. coli plasmid pBR322*, Cold Spring Harb Symp Quant Biol.
- [PMID 7826010](https://pubmed.ncbi.nlm.nih.gov/7826010/) — Hillen & Berens 1994, *Mechanisms underlying expression of Tn10 encoded tetracycline resistance*, Annu Rev Microbiol.