# thrombin_site

Engineered 6-residue thrombin (factor IIa) recognition/cleavage site (LVPRGS) used to proteolytically remove affinity or solubility tags from recombinant fusion proteins.

## Origin

The site Leu-Val-Pro-Arg-Gly-Ser (LVPRGS) was engineered from the natural human factor VIII thrombin cleavage site LVPRGF by substituting the C-terminal phenylalanine with serine; that single Phe->Ser change creates a BamHI (GGATCC) restriction site, making the cassette convenient to clone in-frame between an N-terminal tag and a target protein. It was introduced as the cleavable linker of the GST-fusion expression system described by Smith and Johnson in 1988. The sequence is source-verified at 100% identity over all 6 residues against the deposited sequence U13850.1 (misc_feature 918..935, nt CTGGTTCCGCGTGGATCC, explicitly annotated as encoding the thrombin recognition site).

## Properties

- Length: 6 amino acids (Leu-Val-Pro-Arg-Gly-Ser).
- Thrombin hydrolyses the peptide bond after the arginine (LVPR | GS), so the released downstream protein carries an N-terminal Gly-Ser scar.
- Core specificity determinants match the experimentally defined thrombin consensus: proline at P2, an obligatory arginine at P1, and a small residue at P1'; arginine at P3' is favoured but not present here.
- Caveats: cleavage leaves a non-native Gly-Ser scar, and thrombin is comparatively promiscuous, sometimes cutting cryptic internal sites within the target protein, so cleavage products should be verified. These limitations motivate alternative, more specific proteases (e.g. factor Xa, TEV) in some applications.
- A P1' Gly->Cys variant (LVPRC) exposes an N-terminal cysteine on the released protein, enabling subsequent native chemical ligation.

## Use

The site is placed in-frame between an N-terminal affinity or solubility tag and the protein of interest. After capture and washing, treatment with thrombin cleaves at LVPR | GS to release the target protein from the immobilised or fused tag. Because it is a single functionally coherent recognition/cleavage motif used as one unit, it is treated as an atomic part.

## References

- Smith DB, Johnson KS. 1988, Gene 67:31-40. [PMID 3047011](https://pubmed.ncbi.nlm.nih.gov/3047011/) | [doi:10.1016/0378-1119(88)90005-4](https://doi.org/10.1016/0378-1119(88)90005-4)
- Gallwitz M et al. 2012, PLoS One. [PMID 22384068](https://pubmed.ncbi.nlm.nih.gov/22384068/) | [doi:10.1371/journal.pone.0031756](https://doi.org/10.1371/journal.pone.0031756)
- Waugh DS. 2011, Protein Expr Purif. [PMID 21871965](https://pubmed.ncbi.nlm.nih.gov/21871965/) | [doi:10.1016/j.pep.2011.08.005](https://doi.org/10.1016/j.pep.2011.08.005)
- Jenny RJ et al. 2003, Protein Expr Purif. [PMID 12963335](https://pubmed.ncbi.nlm.nih.gov/12963335/) | [doi:10.1016/s1046-5928(03)00168-2](https://doi.org/10.1016/s1046-5928(03)00168-2)
- Liu D et al. 2008, FEBS Lett. [PMID 18331839](https://pubmed.ncbi.nlm.nih.gov/18331839/) | [doi:10.1016/j.febslet.2008.02.078](https://doi.org/10.1016/j.febslet.2008.02.078)
- Hakes DJ, Dixon JE. 1992, Anal Biochem. [PMID 1519755](https://pubmed.ncbi.nlm.nih.gov/1519755/) | [doi:10.1016/0003-2697(92)90108-j](https://doi.org/10.1016/0003-2697(92)90108-j)