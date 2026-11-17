The Tn10 divergent tetA/tetR control region: 56 bp carrying the PtetA promoter, the divergent PtetR promoter, and the two TetR operators tetO1 and tetO2.

## Origin
This fragment is the intergenic regulatory region of the Tn10 (class B) tetracycline-resistance determinant, where the divergent promoters for *tetA* (efflux pump) and *tetR* (repressor) overlap. The architecture was defined by Bertrand et al. 1983, who mapped the overlapping divergent promoters (transcription start sites ~36 bp apart) and the two dyad-symmetry operators ([PMID 6311683](https://pubmed.ncbi.nlm.nih.gov/6311683/)). Daniels & Bertrand 1985 assigned the -35/-10 hexamers and the *tetR* start sites via promoter-down mutations ([PMID 2995683](https://pubmed.ncbi.nlm.nih.gov/2995683/)). The *tetR* gene reads from a tandem promoter, and Gülland & Hillen 1992 showed that **P_R2 is the dominant arm — more than 95% of *tetR* mRNA originates from P_R2 in vivo** (the in-vitro-active P_R1 supplies under 5% in vivo) ([PMID 1316869](https://pubmed.ncbi.nlm.nih.gov/1316869/)). P_R2's start is that run of A's, which the J01830 record places at 1544 (the tetR mRNA 5' end), one base outside this 56 bp window; no accessible source gives the -35/-10 positions of either tetR promoter, so this part declares none (see below).

## Properties
All positions are 1-based on the 56-bp part.

- **PtetA -35** (TTGACA, 2-7): canonical sigma70 -35 hexamer driving *tetA*.
- **PtetA -10** (TTATTT, 25-30): degenerate -10 hexamer, 17 bp downstream of the -35; it reads degenerate because tetO1 is superimposed on the -10/spacer.
- **PtetA +1** (37, J01830 1581): the *tetA* transcription start, 7 nt 3' of the PtetA -10, as in the record's tetA mRNA.
- **tetR promoters** (bottom strand): not declared. Daniels & Bertrand 1985 describe two (tetPR1, tetPR2); P_R2 starts at the run of five A's at J01830 1540-1544, just outside this window. The reading consistent with that start (-35 TGGTAA, -10 TAGAGT, 17 bp spacer) has 7 of 12 consensus bases, too few to predict by the catalog's criteria. Earlier sub-features put the tetR +1 at J01830 1564, inside tetO1, which the record and the five-A start contradict for P_R2. The pRAB vectors carry a modified form of this region whose tetR promoter is the candidate part `PtetR* (pRAB)`.
- **tetO1** (CACTCTATCATTGATAGAG, 6-24): 19 bp TetR operator overlapping the PtetA -10/spacer; chiefly controls PtetR; ~2x lower TetR affinity than O2.
- **tetO2** (TCCCTATCAGTGATAGAGA, 37-55): 19 bp non-palindromic, higher-affinity wild-type operator overlapping the divergent PtetR -10/-35; mainly controls PtetA.

Both operators share the TGATAGAG core and bind TetR via its HTH domain; the TetR-operator interaction was solved structurally by Hinrichs et al. 1994 ([PMID 8153629](https://pubmed.ncbi.nlm.nih.gov/8153629/)). Differential O1/O2 regulation, with little cooperativity, was shown by Meier et al. 1988 ([PMID 2835235](https://pubmed.ncbi.nlm.nih.gov/2835235/)); operator base pairs contacting TetR were mapped by Wissmann et al. 1986 ([PMID 3086838](https://pubmed.ncbi.nlm.nih.gov/3086838/)).

## Use
A tetracycline-inducible switch: bound TetR represses transcription from PtetA (and PtetR); tetracycline / anhydrotetracycline (aTc) releases TetR, de-repressing the promoters. It is the basis of Tet-OFF/Tet-inducible expression systems ([PMID 7826010](https://pubmed.ncbi.nlm.nih.gov/7826010/)). The defining feature is overlap: editing a promoter hexamer also perturbs the operator superimposed on it, so plan edits with both layers in view. The cognate repressor TetR(B) and the inducer (aTc) are required for function and are supplied separately from this fragment.

## References
- [PMID 6311683](https://pubmed.ncbi.nlm.nih.gov/6311683/) — Bertrand et al. 1983, *Gene*. Overlapping divergent promoters; two operators.
- [PMID 2995683](https://pubmed.ncbi.nlm.nih.gov/2995683/) — Daniels & Bertrand 1985, *J Mol Biol*. Promoter-down mutations; -35/-10 assignment.
- [PMID 1316869](https://pubmed.ncbi.nlm.nih.gov/1316869/) — Gülland & Hillen 1992, *Gene*. P_R2 is the dominant *tetR* promoter in vivo; start-site heterogeneity.
- [PMID 3086838](https://pubmed.ncbi.nlm.nih.gov/3086838/) — Wissmann et al. 1986, *Nucleic Acids Res*. tetO1/tetO2 sequences and TetR contacts.
- [PMID 2835235](https://pubmed.ncbi.nlm.nih.gov/2835235/) — Meier et al. 1988, *EMBO J*. Differential O1/O2 regulation.
- [PMID 7826010](https://pubmed.ncbi.nlm.nih.gov/7826010/) — Hillen & Berens 1994, *Annu Rev Microbiol*. System review.
- [PMID 8153629](https://pubmed.ncbi.nlm.nih.gov/8153629/) — Hinrichs et al. 1994, *Science*. TetR-operator co-crystal structure.
