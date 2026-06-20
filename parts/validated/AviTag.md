# AviTag

A 15-aa synthetic biotin acceptor peptide (GLNDIFEAQKIEWHE) that is site-specifically biotinylated on Lys11 by the biotin ligase BirA, enabling streptavidin-based detection, affinity capture, and live-cell surface labeling.

## Origin

AviTag derives from a 13-residue BirA consensus peptide first identified by Schatz (1993; PMID:7764094) through combinatorial 'Peptides-on-Plasmids' library screening of >10^9 sequences for biotinylation by *E. coli* biotin ligase BirA. Beckett et al. (1999; PMID:10211839) defined the minimal 14-mer and optimized the sequence to the 15-mer GLNDIFEAQKIEWHE, demonstrating kcat/Km comparable to the natural biotin carboxyl carrier protein (BCCP) substrate; MALDI-TOF confirmed Lys11 (K10 in the original numbering) as the sole biotinylation site. The tag is fully synthetic with no natural protein parent. The oldest independently-fetchable sequence record is GenBank AAK73773.1 (deposited 2001-07-23), a 38-aa GTA-bio fusion deposited by Brown et al. (Nano Letters 2001).

## Properties

BirA catalyzes site-specific transfer of biotin from a biotin-AMP intermediate to the epsilon-amine of Lys11 in an ATP-dependent reaction. The resulting biotinyl-lysine binds streptavidin with femtomolar affinity (~10^-15 M Kd). In vitro biotinylation by purified BirA achieves 80-100% efficiency; in vivo co-expression of BirA yields 50-80% biotinylation depending on BirA:substrate ratio and intracellular biotin concentration (PMID:38662935). Under standard conditions BirA does not biotinylate other cellular lysines, providing site specificity. AviTag can be fused N-terminally, C-terminally, or as an internal loop insertion, provided the tag remains accessible to BirA. Slow-kinetics variants (BAP1070, BAP1108; ~45-48x slower) have been developed for proximity-based protein interaction assays (PMID:35207587).

## Use

AviTag is used for: (1) one-step streptavidin/avidin affinity purification of recombinant proteins after in vivo or in vitro biotinylation (PMID:9750126); (2) live-cell surface protein labeling using extracellularly supplied BirA followed by streptavidin or monovalent streptavidin (mSA) probes — mSA is preferred to avoid receptor crosslinking (PMID:15897449, PMID:16554831); (3) quantum dot conjugation and single-molecule tracking (PMID:15897449); (4) chromatin immunoprecipitation of biotinylated nuclear proteins with improved signal-to-noise over antibody-based ChIP (PMID:14715286); and (5) protein immobilization on streptavidin-coated surfaces. The tag is functionally validated in *E. coli*, insect cells, and at the mammalian cell surface (PMID:9750126, PMID:15897449).

## References

- PMID:7764094 — Schatz PJ (1993). [Use of peptide libraries to map the substrate specificity of a peptide-modifying enzyme](https://doi.org/10.1038/nbt1093-1138). Biotechnology.
- PMID:10211839 — Beckett D, Kovaleva E, Schatz PJ (1999). [A minimal peptide substrate in biotin holoenzyme synthetase-catalyzed biotinylation](https://doi.org/10.1110/ps.8.4.921). Protein Sci.
- PMID:9750126 — Duffy S, Tsao KL, Waugh DS (1998). [Site-specific, enzymatic biotinylation of recombinant proteins in Spodoptera frugiperda cells](https://doi.org/10.1006/abio.1998.2770). Anal Biochem.
- PMID:15897449 — Howarth M et al. (2005). [Targeting quantum dots to surface proteins in living cells with biotin ligase](https://doi.org/10.1073/pnas.0503125102). Proc Natl Acad Sci USA.
- PMID:16554831 — Howarth M et al. (2006). [A monovalent streptavidin with a single femtomolar biotin binding site](https://doi.org/10.1038/nmeth861). Nat Methods.
- PMID:18323822 — Howarth M, Ting AY (2008). [Imaging proteins in live mammalian cells with biotin ligase and monovalent streptavidin](https://doi.org/10.1038/nprot.2008.20). Nat Protoc.
- PMID:14715286 — Viens A et al. (2004). [Use of protein biotinylation in vivo for chromatin immunoprecipitation](https://doi.org/10.1016/j.ab.2003.10.015). Anal Biochem.
- PMID:25560075 — Fairhead M, Howarth M (2015). [Site-specific biotinylation of purified proteins using BirA](https://doi.org/10.1007/978-1-4939-2272-7_12). Methods Mol Biol.
- PMID:35207587 — Kulyyassov A, Ramankulov Y, Ogryzko V (2022). [Generation of Peptides for Highly Efficient Proximity Utilizing Site-Specific Biotinylation in Cells](https://doi.org/10.3390/life12020300). Life (Basel).
- PMID:38662935 — AviTrap authors (2024). [AviTrap: A novel solution to achieve complete biotinylation](https://doi.org/10.1371/journal.pone.0297122). PLoS One.