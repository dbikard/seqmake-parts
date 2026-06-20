# SUMO

SUMO (yeast Smt3) is the 98-aa *Saccharomyces cerevisiae* small ubiquitin-related modifier, a ubiquitin-like beta-grasp protein ending in a conserved C-terminal Gly-Gly. It is the canonical N-terminal SUMO-fusion tag: it boosts soluble expression of difficult passengers and is cleaved at the Gly-Gly by the SUMO-specific protease Ulp1 to release the passenger with a native N-terminus.

## Origin

SUMO is the product of the *S. cerevisiae* SMT3 gene (UniProt Q12306, Swiss-Prot reviewed), an essential ubiquitin-like modifier involved in the sumoylation pathway (E1 Aos1/Uba2, E2 Ubc9) and processes such as chromosome segregation. The full gene product is a 101-aa precursor; the mature chain (residues 2–98) is exposed after removal of the C-terminal propeptide (residues 99–101, ATY) by the SUMO protease Ulp1, leaving the conserved C-terminal Gly-Gly. The sequence stored here is residues 1–98: it retains the initiator Met (M1) for use as a recombinant N-terminal fusion tag and ends precisely at the Gly-Gly Ulp1 cleavage site. It is 100% identical to UniProt Q12306 over residues 1–98.

## Properties

SUMO adopts a compact ubiquitin-like beta-grasp fold; the Ulp1–SUMO co-crystal structure (PDB 1EUV, 1.60 Å) defines how the protease engages the folded domain and its C-terminal diglycine (PMID 10882122). Cleavage specificity is determined by the conserved C-terminal Gly-Gly: single substitutions in the diglycine are tolerated, but dual mutation abolishes cleavage, consistent with a tapered protease active-site pocket (PMID 36293045). Crucially, Ulp1 recognizes the three-dimensional fold of SUMO rather than a linear recognition sequence, which gives it broad tolerance at the cleavage site — any residue except proline is accepted immediately downstream, so the released passenger carries a native (scarless) N-terminus (PMID 16084395, PMID 16322573). In a head-to-head comparison of common fusion partners, SUMO ranked in the top tier (alongside NusA, ahead of MBP, GST, thioredoxin and ubiquitin) for enhancing expression and solubility, and Ulp1 cleaved its substrate with a kcat roughly 25-fold higher than a commonly used TEV protease (PMID 16322573).

## Use

SUMO is deployed as an N-terminal fusion partner to enhance the soluble expression and overall yield of difficult-to-express recombinant proteins, most commonly in *E. coli* (PMID 15263846, PMID 16084395). After expression and capture, the SUMO tag is removed by the SUMO-specific protease Ulp1, which cleaves immediately after the C-terminal Gly-Gly to release the passenger with a native N-terminus — an advantage over proteases that leave residual linker residues (PMID 15263846, PMID 16322573). Because Ulp1 reads the SUMO fold rather than a linear site, essentially any N-terminal residue can be generated on the passenger (except proline). Improved single-column SUMO-fusion workflows using the Ulp1 catalytic domain have been described for proteins that are otherwise hard to produce (PMID 18467498). The tag functions as a unit and is typically paired with its cognate Ulp1 protease, which is best treated as a separate, cross-linked part.

## References

- Mossessova & Lima 2000, *Mol Cell* — [PMID 10882122](https://pubmed.ncbi.nlm.nih.gov/10882122/) · [doi:10.1016/s1097-2765(00)80326-3](https://doi.org/10.1016/s1097-2765(00)80326-3)
- Malakhov et al. 2004, *J Struct Funct Genomics* — [PMID 15263846](https://pubmed.ncbi.nlm.nih.gov/15263846/) · [doi:10.1023/B:JSFG.0000029237.70316.52](https://doi.org/10.1023/B:JSFG.0000029237.70316.52)
- Butt et al. 2005, *Protein Expr Purif* — [PMID 16084395](https://pubmed.ncbi.nlm.nih.gov/16084395/) · [doi:10.1016/j.pep.2005.03.016](https://doi.org/10.1016/j.pep.2005.03.016)
- Marblestone et al. 2006, *Protein Sci* — [PMID 16322573](https://pubmed.ncbi.nlm.nih.gov/16322573/) · [doi:10.1110/ps.051812706](https://doi.org/10.1110/ps.051812706)
- Lee et al. 2008, *Protein Sci* — [PMID 18467498](https://pubmed.ncbi.nlm.nih.gov/18467498/) · [doi:10.1110/ps.035188.108](https://doi.org/10.1110/ps.035188.108)
- Zhang et al. 2022, *Int J Mol Sci* — [PMID 36293045](https://pubmed.ncbi.nlm.nih.gov/36293045/) · [doi:10.3390/ijms232012188](https://doi.org/10.3390/ijms232012188)