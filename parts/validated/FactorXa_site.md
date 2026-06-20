# FactorXa_site

FactorXa_site is the IEGR (Ile-Glu-Gly-Arg) tetrapeptide that coagulation Factor Xa recognizes as its P4-P1 site and cleaves after the terminal arginine — the canonical engineered site for site-specific release of a passenger protein from its fusion tag.

## Origin
IEGR is a natural Factor Xa cleavage motif from the human coagulation cascade. The sequence stored here matches residues 311-314 of human prothrombin (UniProt P00734, THRB_HUMAN) at 100% identity over all four residues, immediately preceding a documented Factor Xa cleavage at Arg-314; the natural flanking context is DEDSDRAIEGRTATS (PMID 34265300). Prothrombin is physiologically activated by Factor Xa, and the IEGR/IDGR motifs at its activation sites are the biological template that was adapted into a general protein-engineering reagent. Its use as an engineered "restriction protease" site was introduced when sequence-specific Factor Xa proteolysis of an *E. coli*-produced hybrid protein was used to generate authentic beta-globin (PMID 6330564).

## Properties
Factor Xa (EC 3.4.21.6) recognizes the four-residue motif Ile-Glu-Gly-Arg and hydrolyzes the peptide bond on the C-terminal side of the P1 arginine (IEGR|X). Substrate-specificity profiling by phage display defined the preferred P4-P1 consensus as Ile-Glu/Asp-Gly-Arg, identifying both IEGR and IDGR as favored sequences (PMID 18296445). Because cleavage occurs after the terminal Arg, a passenger placed immediately downstream is released with a native, scar-free N-terminus. In practice the reaction is context-dependent: secondary nonspecific cleavage (for example at some Lys-containing sites) can occur, certain hydrophobic residues at the P1' position can inhibit cleavage, and the steric accessibility of the inserted site affects efficiency (PMID 12963335, PMID 8427626, PMID 2185034). Accessibility was also shown directly by inserting single or tandem IEGR sites into loops of a membrane protein (PMID 7827058).

## Use
The element is inserted into the linker between an affinity/solubility tag and the target protein so that, after capture and purification, the tag can be removed by adding Factor Xa in vitro. Because the cleaving enzyme is supplied exogenously, the site itself is host-agnostic and functions independently of the expression system. It is one of a family of in-vitro protease cleavage sites (alongside TEV, thrombin, enterokinase, and HRV3C sites) used for tag removal, each with distinct specificity and practical trade-offs (PMID 21871965). When designing a construct, the cleavage geometry (cut after P1 Arg) and the documented context-dependence of Factor Xa should be considered, and the released product checked for any retained linker residues and for nonspecific cleavage.

## References
- Nagai & Thøgersen 1984, *Nature* — [PMID 6330564](https://pubmed.ncbi.nlm.nih.gov/6330564/) · [doi:10.1038/309810a0](https://doi.org/10.1038/309810a0)
- Wearne 1990, *FEBS Lett* — [PMID 2185034](https://pubmed.ncbi.nlm.nih.gov/2185034/) · [doi:10.1016/0014-5793(90)80696-g](https://doi.org/10.1016/0014-5793(90)80696-g)
- He et al. 1993, *J Protein Chem* — [PMID 8427626](https://pubmed.ncbi.nlm.nih.gov/8427626/) · [doi:10.1007/BF01024906](https://doi.org/10.1007/BF01024906)
- Sahin-Tóth et al. 1995, *Biochemistry* — [PMID 7827058](https://pubmed.ncbi.nlm.nih.gov/7827058/) · [doi:10.1021/bi00004a001](https://doi.org/10.1021/bi00004a001)
- Jenny et al. 2003, *Protein Expr Purif* — [PMID 12963335](https://pubmed.ncbi.nlm.nih.gov/12963335/) · [doi:10.1016/s1046-5928(03)00168-2](https://doi.org/10.1016/s1046-5928(03)00168-2)
- Hsu et al. 2008, *J Biol Chem* — [PMID 18296445](https://pubmed.ncbi.nlm.nih.gov/18296445/) · [doi:10.1074/jbc.M708843200](https://doi.org/10.1074/jbc.M708843200)
- Waugh 2011, *Protein Expr Purif* — [PMID 21871965](https://pubmed.ncbi.nlm.nih.gov/21871965/) · [doi:10.1016/j.pep.2011.08.005](https://doi.org/10.1016/j.pep.2011.08.005)
- Stojanovski & Di Cera 2021, *J Biol Chem* — [PMID 34265300](https://pubmed.ncbi.nlm.nih.gov/34265300/) · [doi:10.1016/j.jbc.2021.100955](https://doi.org/10.1016/j.jbc.2021.100955)