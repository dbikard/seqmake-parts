# HRV3C_site

8-residue Human Rhinovirus 3C protease recognition and cleavage site (LEVLFQGP); the 3C cysteine protease (EC 3.4.22.28) cleaves between Gln (P1) and Gly (P1') — notation LEVLFQ|GP — leaving a Gly-Pro dipeptide scar on the released downstream protein.

## Origin

LEVLFQGP is derived from the natural polyprotein processing signal of Human rhinovirus 3 (HRV3). The sequence corresponds to residues 1423-1430 of the HRV3 genome polyprotein (UniProt Q82081, POLG_HRV3, Swiss-Prot reviewed), where it is annotated as a "Cleavage; by protease 3C" site between Q1428 and G1429. The HRV 3C protease is a cysteine protease that processes the viral polyprotein during replication; the substrate specificity defined by this and related natural cleavage sites was the basis for establishing the engineered recognition consensus used in recombinant protein production. Cordingley et al. (1990, PMID 2160953) defined the minimum peptide substrate (TLFQ|GP, 6 aa) and showed that P4 hydrophobicity, P1=Gln, and P1'=Gly are critical for cleavage in vitro.

## Properties

The dominant specificity determinants are P1=Gln (Glu also accepted) and P1'=Gly/Ala/Cys/Ser. P2 (Leu/Phe) and P4 (hydrophobic) also contribute. Quantitative substrate profiling (Fan et al., 2019, PMID 31613083) using yeast-display identified S1 pocket residue His160 and S1' pocket residue Thr141 as the structural determinants at the key positions, and identified LEVLFQ|GM as an improved substrate at elevated temperatures. The protease is highly specific compared to serine proteases used for tag removal, with documented low off-target cleavage frequency (Waugh 2011, PMID 21871965). A key practical advantage is robust cleavage activity at 4 °C, enabling tag removal during affinity purification under conditions that minimize target protein degradation (Abdelkader & Otting 2020, PMID 33166527). A recognized limitation is the two-residue Gly-Pro (GP) scar left on the N-terminus of the released protein; engineered 3C variants with expanded P1' specificity have been reported to address this (Mei et al., 2024, PMID 38521339).

## Use

Insert LEVLFQGP in-frame between an affinity or solubility tag and the target protein. Following affinity purification of the fusion, treat with HRV 3C protease (supplied separately or as a tagged recombinant fusion for co-purification removal) in aqueous buffer, typically at 4 °C, to release the target. The target protein retains a Gly-Pro N-terminal scar. The site is functional across bacterial and insect-cell (baculovirus) expression systems, in vitro and in vivo (Xu et al., 2022, PMID 35642592). The protease has also been demonstrated to work efficiently in cell lysate for direct on-column tag removal applications (Xu et al., 2019, PMID 30686346).

## References

- Cordingley et al. (1990) J Biol Chem — [PMID 2160953](https://pubmed.ncbi.nlm.nih.gov/2160953/) | [DOI 10.1016/S0021-9258(19)38811-8](https://doi.org/10.1016/S0021-9258(19)38811-8)
- Waugh DS (2011) Protein Expr Purif — [PMID 21871965](https://pubmed.ncbi.nlm.nih.gov/21871965/) | [DOI 10.1016/j.pep.2011.08.005](https://doi.org/10.1016/j.pep.2011.08.005)
- Fan et al. (2019) ACS Chem Biol — [PMID 31613083](https://pubmed.ncbi.nlm.nih.gov/31613083/) | [DOI 10.1021/acschembio.9b00539](https://doi.org/10.1021/acschembio.9b00539)
- Abdelkader & Otting (2020) J Biotechnol — [PMID 33166527](https://pubmed.ncbi.nlm.nih.gov/33166527/) | [DOI 10.1016/j.jbiotec.2020.11.005](https://doi.org/10.1016/j.jbiotec.2020.11.005)
- Mei et al. (2024) Int J Biol Macromol — [PMID 38521339](https://pubmed.ncbi.nlm.nih.gov/38521339/) | [DOI 10.1016/j.ijbiomac.2024.131066](https://doi.org/10.1016/j.ijbiomac.2024.131066)
- Xu et al. (2022) Biosci Rep — [PMID 35642592](https://pubmed.ncbi.nlm.nih.gov/35642592/) | [DOI 10.1042/BSR20220739](https://doi.org/10.1042/BSR20220739)
- Xu et al. (2019) Enzyme Microb Technol — [PMID 30686346](https://pubmed.ncbi.nlm.nih.gov/30686346/) | [DOI 10.1016/j.enzmictec.2019.01.004](https://doi.org/10.1016/j.enzmictec.2019.01.004)
- Davis et al. (1997) Arch Biochem Biophys — [PMID 9328292](https://pubmed.ncbi.nlm.nih.gov/9328292/) | [DOI 10.1006/abbi.1997.0291](https://doi.org/10.1006/abbi.1997.0291)
