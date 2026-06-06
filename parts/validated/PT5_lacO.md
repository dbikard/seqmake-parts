PT5/lacO is the bacteriophage-T5 sigma-70 promoter flanked by two lac operators, giving lacI-repressible, IPTG-inducible transcription (the pQE/Bujard expression module).

## Origin
PT5/lacO derives from the T5-promoter expression system developed in the Bujard lab and used in the pDS/pQE vector lineage ([PMID 3900050](https://pubmed.ncbi.nlm.nih.gov/3900050/), [PMID 2828874](https://pubmed.ncbi.nlm.nih.gov/2828874/)). It couples a strong phage-T5 promoter recognized by E. coli RNA polymerase to two lac operators so that expression is tightly repressed by LacI and induced by IPTG.

## Properties
The 81 bp element contains a sigma-70 promoter with a -35 hexamer TTGCTT (seq[18:24]; an imperfect match to the TTGACA consensus) and a perfect -10 hexamer TATAAT (seq[41:47]), separated by a canonical 17 bp spacer. Two identical lac operator cores (TGTGAGCGGATAACAAT) flank the start of transcription: the upstream operator (seq[24:41]) fully occupies the promoter spacer and abuts the -10 box, while the downstream operator (seq[56:73]) sits 3' of the start site. The two operators together enable cooperative repression by a single LacI tetramer ([PMID 3015603](https://pubmed.ncbi.nlm.nih.gov/3015603/)). The operator core and its dyad symmetry are the classic lac operator ([PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/), [PMID 6369330](https://pubmed.ncbi.nlm.nih.gov/6369330/)).

## Use
Use PT5/lacO as a strong, LacI-repressible promoter for IPTG-inducible expression in E. coli (it requires a LacI source, e.g. lacI^q on the host or plasmid). The upstream operator within the spacer makes repression of this promoter especially tight relative to a single-operator design.

## References
- [PMID 3900050](https://pubmed.ncbi.nlm.nih.gov/3900050/) — Gentz & Bujard 1985, T5 promoters / -35,-10 architecture.
- [PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/) — Gilbert & Maxam 1973, lac operator sequence and symmetry.
- [PMID 6369330](https://pubmed.ncbi.nlm.nih.gov/6369330/) — Simons et al. 1984, ideal/symmetric lac operator.
- [PMID 3015603](https://pubmed.ncbi.nlm.nih.gov/3015603/) — Besse et al. 1986, dual upstream+downstream operator repression.
- [PMID 2828874](https://pubmed.ncbi.nlm.nih.gov/2828874/) — Bujard et al. 1987, T5-promoter expression system.