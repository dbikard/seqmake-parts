A 56-bp synthetic constitutive/IPTG-regulatable promoter combining the phage T7 A1 (PA1) core with two natural lac O1 operators placed at positions 4 (spacer) and 3 (downstream).

## Origin
PA1/O4/O3 is a Bujard-lab synthetic promoter built on the strong phage T7 A1 promoter (PA1). Lanzer & Bujard ([PMID 3057497](https://pubmed.ncbi.nlm.nih.gov/3057497/)) defined a set of numbered positions at which lac operators can be inserted into the A1 promoter and showed that repression efficiency depends strongly on operator position (up to ~70-fold). The part name encodes the two occupied positions: an operator in the -35/-10 spacer (position 4, "O4") and one immediately downstream of the -10 (position 3, "O3"). The same design lineage produced the widely used IPTG-controllable derivative PA1lacO-1 ([PMID 9092630](https://pubmed.ncbi.nlm.nih.gov/9092630/)), obtained by total synthesis.

## Properties
- **-35 box (0-6, TTGACT):** native T7 A1 -35 hexamer, one base from the sigma-70 consensus TTGACA.
- **lac operator O4 (6-23, TGTGAGCGGATAACAAT):** the natural lac O1 core ([PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/)) inserted into and fully occupying the 17-bp -35/-10 spacer.
- **-10 box (23-29, GATACT):** native T7 A1 -10 hexamer; the conserved TA is shifted relative to consensus TATAAT.
- **lac operator O3 (39-56, TGTGAGCGGATAACAAT):** an exact second copy of the lac O1 core downstream of the -10.
- Region 29-39 (TAGATTCAAT) spans the transcription-start region and is left unannotated.

## Use
A strong, LacI-repressible promoter for tunable expression in E. coli: in the absence of IPTG, LacI bound at the two operators represses transcription; IPTG relieves repression. The closely related PA1lacO-1 design gives roughly two-orders-of-magnitude IPTG regulation, making this promoter family a standard choice for inducible expression cassettes.

## References
- [PMID 3057497](https://pubmed.ncbi.nlm.nih.gov/3057497/) - Lanzer & Bujard (1988), defines PA1/O4/O3 and the numbered operator positions.
- [PMID 9092630](https://pubmed.ncbi.nlm.nih.gov/9092630/) - Lutz & Bujard (1997), PA1lacO-1 lineage and tight IPTG regulation.
- [PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/) - Gilbert & Maxam (1973), nucleotide sequence of the lac operator (O1).