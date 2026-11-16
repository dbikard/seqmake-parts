The pBR322 region just past the ColE1-family DNA replication start (pBR322 2351-2533), carrying the lagging-strand primosome assembly site (pas) and a DnaA box; it lies directly 3' of the ColE1 origin in pBR322 and pUC vectors.

## Origin
ColE1-family replication runs one way: the RNA II primer is extended into the leading strand, and the displaced parental strand (the L strand of pBR322) becomes the lagging-strand template. Synthesis on that single strand starts at signals just past the origin. Zipursky & Marians found two sites near the pBR322 and ColE1 origins, on opposite strands, that activate the ATPase of replication factor Y (PriA) when single-stranded ([PMID 6109282](https://pubmed.ncbi.nlm.nih.gov/6109282/)). The one on the L strand lies in this part, and cloned into an f1 phage vector it directs dnaB-, dnaC- and dnaG-dependent complementary-strand synthesis: a primosome assembly site ([PMID 6279609](https://pubmed.ncbi.nlm.nih.gov/6279609/); deletions abolish both activities, [PMID 6130524](https://pubmed.ncbi.nlm.nih.gov/6130524/)). DnaA also binds the pBR322 origin region ([PMID 6091903](https://pubmed.ncbi.nlm.nih.gov/6091903/)), at a DnaA box in this part.

## Properties
- **pas (L strand), part 119-182:** the factor Y effector site, active as single-stranded DNA on the lagging-strand template, read on the part's top strand.
- **DnaA box, part 87-95 (bottom strand):** TTATCCACA, a perfect match to the 9 bp DnaA-box consensus TTAT(C/A)CA(C/A)A and the only match in the region.
- **Required in vitro.** In cell-free replication, pBR322 needs a primosome assembly site on the lagging strand but not on the leading strand; without it, intermediates with only the leading strand made accumulate ([PMID 2844795](https://pubmed.ncbi.nlm.nih.gov/2844795/)). Deleting the lagging-strand site together with the DnaA site cuts synthesis to under 10% ([PMID 2844794](https://pubmed.ncbi.nlm.nih.gov/2844794/)). DnaA bound at its box can stand in for the pas: pBR322 lacking the pas sites replicates efficiently in vitro when DnaA and its binding site are present ([PMID 3791416](https://pubmed.ncbi.nlm.nih.gov/3791416/)).
- **Dispensable for copy number in vivo.** Deleting the DnaA site and the primosome assembly sites next to the pBR322 origin did not change plasmid copy number in *E. coli*, in exponential growth, after DnaA inactivation or with DnaA in excess ([PMID 1708087](https://pubmed.ncbi.nlm.nih.gov/1708087/)).

## Boundaries
The part is pBR322 (GenBank J01749) bases 2351-2533 on the minus strand, read in the same direction as the [`ColE1`](ColE1.md) part. It starts at the base after ColE1's 3' end (pBR322 2534, at the RNA-to-DNA transition), so `ColE1` followed by this part is pBR322 2351-3122 without a gap or overlap; pUC19 (L09137) carries the same 183 bp. Marians et al. placed the L-strand site within nucleotides 2353-2416 ([PMID 6279609](https://pubmed.ncbi.nlm.nih.gov/6279609/)), numbered on the original 4362 bp sequence. Two later revisions, +1 bp at 526 ([PMID 6307828](https://pubmed.ncbi.nlm.nih.gov/6307828/)) and -2 bp at 1893 and 1915 ([PMID 3063608](https://pubmed.ncbi.nlm.nih.gov/3063608/)), shift every position past 1915 by -1, giving 2352-2415 on J01749: exactly the HaeII-AluI fragment. These are maximal limits, not a minimal site. The J01749 record annotates the site at 2351-2414, one base off, as if from the 4363 bp numbering. The DnaA box at 2439-2447 is located by its sequence.

## Use
Carried next to the ColE1 origin in pBR322- and pUC-derived vectors, and in variable amounts in other vectors with a ColE1-type origin, from all of it to none. It is not needed for plasmid maintenance in *E. coli* at normal copy number; it matters for in vitro replication systems and when interpreting how a vector's lagging strand is primed.

## References
- [PMID 6109282](https://pubmed.ncbi.nlm.nih.gov/6109282/) — Zipursky & Marians 1980, two factor Y effector sites near the ColE1 and pBR322 origins.
- [PMID 6279609](https://pubmed.ncbi.nlm.nih.gov/6279609/) — Marians et al. 1982, the maximal limits of the pBR322 factor Y effector sites.
- [PMID 6130524](https://pubmed.ncbi.nlm.nih.gov/6130524/) — Soeller & Marians 1982, deletion mutants of the pBR322 factor Y effector sites.
- [PMID 6091903](https://pubmed.ncbi.nlm.nih.gov/6091903/) — Fuller et al. 1984, DnaA binding at oriC and other sites, including near the pBR322 origin.
- [PMID 3791416](https://pubmed.ncbi.nlm.nih.gov/3791416/) — Seufert & Messer 1987, DnaA binding substitutes for primosome assembly in vitro.
- [PMID 2844795](https://pubmed.ncbi.nlm.nih.gov/2844795/) — Masai & Arai 1988, a lagging-strand n' site is required for efficient pBR322 replication in vitro.
- [PMID 2844794](https://pubmed.ncbi.nlm.nih.gov/2844794/) — Ma & Campbell 1988, DnaA and n' sites in ColE1-type replication in vitro.
- [PMID 1708087](https://pubmed.ncbi.nlm.nih.gov/1708087/) — Chiang et al. 1991, deleting the DnaA site and pas does not change pBR322 copy number in vivo.
- [PMID 6307828](https://pubmed.ncbi.nlm.nih.gov/6307828/), [PMID 3063608](https://pubmed.ncbi.nlm.nih.gov/3063608/) — Peden 1983 and Watson 1988, the pBR322 sequence revisions behind the J01749 numbering.
