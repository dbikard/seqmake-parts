Natural 29 bp Tn10 PtetA promoter: a sigma-70 -35/-10 promoter whose spacer holds the central 17 bp of the tetO1 operator, making transcription TetR/anhydrotetracycline-controllable.

## Origin
Derived from the Tn10 tetracycline-resistance determinant, where two overlapping divergent promoters (PtetA and PtetR) share an intergenic region and are controlled by tandem tet operators. This part is the PtetA arm, which drives the tetA efflux gene. Promoter start points and operator architecture were mapped by Bertrand et al. 1983 ([PMID 6311683](https://pubmed.ncbi.nlm.nih.gov/6311683/)); the broader TetR/tetO/tetracycline regulatory mechanism is reviewed by Bertram & Hillen 2008 ([PMID 21261817](https://pubmed.ncbi.nlm.nih.gov/21261817/)).

## Properties
- **-35 box** [0,6): `TTGACA` — perfect sigma-70 consensus.
- **tetO1 operator** [6,23): `CTCTATCATTGATAGAG` — the central 17 bp of the dyad-symmetric ~19 bp tet operator, sitting in the -35/-10 spacer and abutting the -10. Bound by TetR; binding is relieved by tetracycline/anhydrotetracycline. O1/O2 differentially regulate tetA vs tetR (Meier et al. 1988, [PMID 2835235](https://pubmed.ncbi.nlm.nih.gov/2835235/)); canonical tetO palindrome from Lutz & Bujard 1997 ([PMID 9092630](https://pubmed.ncbi.nlm.nih.gov/9092630/)).
- **-10 box** [23,29): `CATAAT` — matches the sigma-70 -10 consensus TATAAT at 5/6 positions (C at position 1).
- All three sub-features tile the 29 bp contiguously with no gaps or overlaps, all on the + strand.

## Use
TetR/tetracycline-inducible expression in E. coli: TetR represses by binding tetO1; adding tetracycline or anhydrotetracycline (aTc) derepresses transcription. Pair with a TetR source for switchable control. Note the part omits the +1 transcription start site (which lies just downstream of the -10) and a downstream RBS, so a 5' UTR/RBS must be supplied for translation.

## References
- [PMID 6311683](https://pubmed.ncbi.nlm.nih.gov/6311683/) — Bertrand et al. 1983, Gene. Overlapping divergent Tn10 promoters; -35/-10/operator mapping.
- [PMID 2835235](https://pubmed.ncbi.nlm.nih.gov/2835235/) — Meier et al. 1988, EMBO J. Differential tetA/tetR regulation by tandem operators O1/O2.
- [PMID 9092630](https://pubmed.ncbi.nlm.nih.gov/9092630/) — Lutz & Bujard 1997, NAR. TetR/O regulatory element; canonical tetO palindrome.
- [PMID 21261817](https://pubmed.ncbi.nlm.nih.gov/21261817/) — Bertram & Hillen 2008, Microb Biotechnol. Review of TetR-based prokaryotic regulation.