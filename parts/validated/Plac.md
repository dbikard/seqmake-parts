The wild-type *E. coli* lac core promoter (Plac): -35/-10/+1 plus a 3'-truncated LacI operator O1, in 55 bp.

## Origin
Plac is the natural *E. coli* lac control region. This 55-bp part spans the lac core promoter from the -35 hexamel through a partial O1 operator, mapped in the classic lac control-region work ([PMID 1088926](https://pubmed.ncbi.nlm.nih.gov/1088926/)). It carries the wild-type, non-consensus -10 (TATGTT) rather than the lacUV5 up-mutation (TATAAT), so it is the native (catabolite-sensitive) promoter rather than the lacUV5 derivative.

## Properties
- **-35** TTTACA (seq[0:6]), wild-type lac hexamer.
- **-35/-10 spacer** 18 bp, CTTTATGCTTCCGGCTCG (seq[6:24]) — normal lac WT spacing.
- **-10** TATGTT (seq[24:30]), weak/non-consensus Pribnow box; the WT-vs-lacUV5 diagnostic.
- **+1 TSS** A at index 36, 7 bp downstream of the -10 box (within the documented 6-8 bp window).
- **lac operator O1 (truncated)** TGGAATTGTGAGCGGATAACAA (seq[33:55]) — full O1 (TGGAATTGTGAGCGGATAACAATT) minus only the terminal TT, clipped at the part's 3' boundary ([PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/)). O1 overlaps the +1, as expected.

The upstream CAP/CRP activator site lies upstream of the -35 and is **not** included in this part.

## Use
Drives transcription from the lac promoter; repressible by LacI via the O1 operator and (in its full genomic context) activated by CAP/cAMP. Because O1 is truncated by 2 bp at the 3' end and the CAP site is absent, repression/activation strength may differ from the full native control region. The part reaches only to +1, so it contributes essentially no transcribed 5' UTR — pair with a downstream RBS/5' UTR part for expression.

## References
- [PMID 1088926](https://pubmed.ncbi.nlm.nih.gov/1088926/) — Dickson RC, Abelson J, Barnes WM, Reznikoff WS. *Genetic regulation: the Lac control region.* Science. (-35/-10/spacer/+1/operator map; natural lac origin.)
- [PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/) — Gilbert W, Maxam A. *The nucleotide sequence of the lac operator.* Proc Natl Acad Sci USA. (O1 = TGGAATTGTGAGCGGATAACAATT.)