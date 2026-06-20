# enterokinase_site

Enterokinase (enteropeptidase) recognition/cleavage site DDDDK — a 5-residue protease site cleaved on the C-terminal side of the Lys, leaving no residual residues on the downstream protein, widely used to remove an N-terminal fusion tag.

## Origin
DDDDK ((Asp)4-Lys) is the recognition sequence of enterokinase (enteropeptidase, EC 3.4.21.9), the intestinal serine protease that activates trypsinogen by a single cleavage in its acidic activation propeptide. The motif's canonical natural occurrence is the trypsinogen activation peptide: the part sequence is a 100%-identity match to residues 19–23 of bovine trypsinogen-1 (UniProt:P00760), within the annotated propeptide. The (Asp)4-Lys specificity was first defined biochemically for porcine enterokinase ([PMID:5570436](https://pubmed.ncbi.nlm.nih.gov/5570436/)) and confirmed as (Asp)4-Lys-Ile in comparative review ([PMID:2658218](https://doi.org/10.1016/0968-0004(89)90133-3)). The cognate enzyme is a heterodimer; its catalytic light chain alone cleaves small DDDDK peptide substrates, while the heavy chain is required for macromolecular substrate recognition ([PMID:9395456](https://doi.org/10.1074/jbc.272.50.31293), [PMID:8226855](https://doi.org/10.1073/pnas.91.16.7588)). Cryo-EM structures of the human enzyme detail the structural basis of DDDDK recognition ([PMID:36376282](https://doi.org/10.1038/s41467-022-34364-9)).

## Properties
- Five-residue site Asp-Asp-Asp-Asp-Lys; the acidic tetrad and the P1 Lys are engaged by the enterokinase light-chain S1–S5 substrate pocket.
- Cleavage occurs on the C-terminal side of the Lys (after K). Because cleavage is C-terminal to the recognition sequence, the downstream protein is released with no extra (vector-derived) residues — the defining advantage for tag removal.
- Specificity is not absolute: profiling shows the enzyme is comparatively promiscuous, prefers Arg over Lys at P1, and DDDDK is not its fastest substrate ([PMID:16672368](https://doi.org/10.1073/pnas.0511108103)). Off-target/secondary cleavage at non-canonical sites is documented ([PMID:11745150](https://doi.org/10.1002/bit.10082)).
- Downstream context modulates rate: a P1'=Ser followed by a basic P2' residue (e.g. an SRLLR-type context) enhances cleavage at a DDDDK site ([PMID:17097793](https://doi.org/10.1016/j.biochi.2006.10.005)).
- A P1 Lys→Arg variant (DDDDR) is cleaved more efficiently, needing 3–6x less enzyme for equivalent fusion-protein cleavage ([PMID:21515380](https://doi.org/10.1016/j.pep.2011.04.005)); kinetic comparison of DDDDK vs DDDDR substrates supports the engineering choice ([PMID:23436726](https://doi.org/10.1002/pro.2239)).

## Use
Placed between an N-terminal fusion tag and a target protein, DDDDK enables proteolytic excision of the tag after purification, yielding an authentic (scar-free) N-terminus on the target. Recombinant enterokinase light chain is the practical cleavage reagent ([PMID:9636275](https://doi.org/10.1038/nbt0995-982), [PMID:11745150](https://doi.org/10.1002/bit.10082)). DDDDK is also the C-terminal sub-motif of the FLAG tag (DYKDDDDK), so an N-terminal FLAG tag can be removed by the same enzyme. When higher cleavage efficiency or lower enzyme usage is needed, the DDDDR variant is the established alternative. Because of documented off-target activity, the target sequence should be checked for internal basic/acidic-flanked sites before relying on a single clean cut.

## References
- [PMID:5570436](https://pubmed.ncbi.nlm.nih.gov/5570436/) — Maroux et al., Purification and specificity of porcine enterokinase, J Biol Chem 1971.
- [PMID:2658218](https://doi.org/10.1016/0968-0004(89)90133-3) — Light & Janska, Enterokinase (enteropeptidase): comparative aspects, Trends Biochem Sci 1989.
- [PMID:8226855](https://doi.org/10.1073/pnas.91.16.7588) — Kitamoto et al., Enterokinase is a mosaic protease, PNAS 1994.
- [PMID:9395456](https://doi.org/10.1074/jbc.272.50.31293) — Lu et al., Specificity depends on the heavy chain, J Biol Chem 1997.
- [PMID:9636275](https://doi.org/10.1038/nbt0995-982) — Collins-Racie et al., Recombinant bovine enterokinase catalytic subunit in E. coli, Nat Biotechnol 1995.
- [PMID:16672368](https://doi.org/10.1073/pnas.0511108103) — Boulware & Daugherty, Protease specificity by CLiPS, PNAS 2006.
- [PMID:17097793](https://doi.org/10.1016/j.biochi.2006.10.005) — Liew et al., SRLLR motif enhances cleavage, Biochimie 2006.
- [PMID:21515380](https://doi.org/10.1016/j.pep.2011.04.005) — Gasparian et al., Improving enteropeptidase efficiency in tag removal, Protein Expr Purif 2011.
- [PMID:23436726](https://doi.org/10.1002/pro.2239) — Smith & Johnson, Human enteropeptidase light chain kinetics, Protein Sci 2013.
- [PMID:36376282](https://doi.org/10.1038/s41467-022-34364-9) — Yang et al., Cryo-EM of human enteropeptidase, Nat Commun 2022.
- [PMID:11745150](https://doi.org/10.1002/bit.10082) — Choi et al., Recombinant EK light chain in fusion protein technology, Biotechnol Bioeng 2001.