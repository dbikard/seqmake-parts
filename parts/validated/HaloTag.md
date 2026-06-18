# HaloTag

HaloTag7 — a 297-amino-acid self-labeling protein tag engineered from a bacterial haloalkane dehalogenase that forms a rapid, essentially irreversible covalent bond with synthetic chloroalkane ligands, enabling labeling, imaging, immobilization, and purification of fusion proteins.

## Origin

HaloTag is a re-engineered monomeric haloalkane dehalogenase derived from the DhaA enzyme of *Rhodococcus rhodochrous*. In the native enzyme, catalysis proceeds in two steps: a nucleophilic aspartate at the alpha/beta-hydrolase nucleophile elbow attacks the terminal carbon of a haloalkane to form a covalent ester intermediate and release halide, after which a base histidine activates water to hydrolyze the intermediate and regenerate the free enzyme. HaloTag carries an engineered substitution of that base histidine to phenylalanine, which abolishes the hydrolytic second step and traps the covalent enzyme-ligand ester, converting a transient catalytic intermediate into a stable, specific covalent link ([PMID 18533659](https://pubmed.ncbi.nlm.nih.gov/18533659/)).

The sequence in this record is the HaloTag7 variant, which carries 21 additional substitutions relative to the parent dehalogenase that improve folding, soluble expression, and ligand-binding kinetics ([PMID 19464373](https://pubmed.ncbi.nlm.nih.gov/19464373/)). It is the standard HaloTag scaffold and is the basis for later engineered variants. The stored sequence corresponds exactly (100% identity, full length) to the deposited canonical HaloTag protein record.

## Properties

- **Covalent, irreversible capture:** HaloTag binds its chloroalkane ligand through a covalent ester bond that forms rapidly under physiological conditions and is essentially irreversible, overcoming the equilibrium limitations of reversible affinity tags ([PMID 18533659](https://pubmed.ncbi.nlm.nih.gov/18533659/)).
- **Fast, tunable labeling kinetics:** apparent second-order labeling rate constants span more than six orders of magnitude (~10^3 to 10^8 M^-1 s^-1) depending on the attached fluorophore, with rhodamine-chloroalkane substrates reacting near the diffusion limit; for matched substrates HaloTag7 labels more than 100-fold faster than the SNAP-tag ([doi:10.1021/acs.biochem.1c00258](https://doi.org/10.1021/acs.biochem.1c00258)).
- **Solubility enhancement:** as an N-terminal fusion partner in *E. coli*, HaloTag7 yielded soluble protein for 74% of 23 test human proteins, compared with 52% (MBP), 39% (GST), and 22% (His6) for the same panel ([PMID 19464373](https://pubmed.ncbi.nlm.nih.gov/19464373/)).
- **Modularity:** a single genetic fusion can be derivatized with many distinct functional groups (fluorescent dyes, affinity handles, solid supports) simply by changing the molecule appended to the common chloroalkane linker ([PMID 18533659](https://pubmed.ncbi.nlm.nih.gov/18533659/)).
- **Engineerability:** point mutants of HaloTag7 alter dye brightness and fluorescence lifetime, enabling fluorescence-lifetime multiplexing of multiple targets in one spectral channel ([PMID 34916672](https://pubmed.ncbi.nlm.nih.gov/34916672/)).

## Use

- **Cellular imaging and detection:** covalent labeling of HaloTag fusions with chloroalkane-fluorophore conjugates for live-cell, fixed-cell, and super-resolution microscopy ([PMID 18533659](https://pubmed.ncbi.nlm.nih.gov/18533659/), [PMID 34916672](https://pubmed.ncbi.nlm.nih.gov/34916672/)).
- **Affinity purification:** covalent capture of HaloTag fusions on a chloroalkane-functionalized solid support, followed by site-specific protease cleavage to release tag-free product; effective for proteins from both bacterial and mammalian hosts, including functional human kinases ([PMID 19464373](https://pubmed.ncbi.nlm.nih.gov/19464373/), [PMID 21129486](https://pubmed.ncbi.nlm.nih.gov/21129486/)).
- **Solubility tagging:** improving soluble expression of recombinant proteins, with performance comparable to MBP and the advantage that cleavage does not precipitate the released partner ([PMID 23115610](https://pubmed.ncbi.nlm.nih.gov/23115610/)).
- **Chemogenetic degradation:** bifunctional chloroalkane-E3-ligase-ligand molecules recruit the ubiquitin-proteasome system to HaloTag7 fusions to trigger their targeted degradation ([PMID 26070106](https://pubmed.ncbi.nlm.nih.gov/26070106/)).
- **Protein-protein interaction imaging:** a split-HaloTag complementation assay reconstitutes a functional tag upon interaction of two fused partners, then binds a fluorescent ligand for advanced microscopy ([PMID 34746759](https://pubmed.ncbi.nlm.nih.gov/34746759/)).

## References

- [PMID 18533659](https://pubmed.ncbi.nlm.nih.gov/18533659/) | [doi:10.1021/cb800025k](https://doi.org/10.1021/cb800025k) — Los GV et al., *ACS Chem Biol* 2008. Founding description of HaloTag; covalent chloroalkane mechanism and modular labeling.
- [PMID 19464373](https://pubmed.ncbi.nlm.nih.gov/19464373/) | [doi:10.1016/j.pep.2009.05.010](https://doi.org/10.1016/j.pep.2009.05.010) — Ohana RF et al., *Protein Expr Purif* 2009. HaloTag7 variant; solubility enhancement and protease-coupled purification.
- [PMID 34916672](https://pubmed.ncbi.nlm.nih.gov/34916672/) | [doi:10.1038/s41592-021-01341-x](https://doi.org/10.1038/s41592-021-01341-x) — Frei MS et al., *Nat Methods* 2021. Engineered HaloTag variants for fluorescence-lifetime multiplexing.
- [doi:10.1021/acs.biochem.1c00258](https://doi.org/10.1021/acs.biochem.1c00258) — Frei MS et al., *Biochemistry* 2021. Labeling kinetics of HaloTag7 versus SNAP-tag and CLIP-tag.
- [PMID 26070106](https://pubmed.ncbi.nlm.nih.gov/26070106/) | [doi:10.1021/acschembio.5b00442](https://doi.org/10.1021/acschembio.5b00442) — Buckley DL et al., *ACS Chem Biol* 2015. HaloPROTAC-induced degradation of HaloTag fusions.
- [PMID 34746759](https://pubmed.ncbi.nlm.nih.gov/34746759/) | [doi:10.1016/j.xplc.2021.100212](https://doi.org/10.1016/j.xplc.2021.100212) — Minner-Meinen R et al., *Plant Commun* 2021. Split-HaloTag protein-protein interaction imaging.
- [PMID 21129486](https://pubmed.ncbi.nlm.nih.gov/21129486/) | [doi:10.1016/j.pep.2010.11.014](https://doi.org/10.1016/j.pep.2010.11.014) — Ohana RF et al., *Protein Expr Purif* 2010. HaloTag purification of functional human kinases.
- [PMID 23115610](https://pubmed.ncbi.nlm.nih.gov/23115610/) | [doi:10.2174/1875397301206010008](https://doi.org/10.2174/1875397301206010008) — Peterson SN, Kwon K, *Curr Chem Genomics* 2012. HaloTag as a solubility tag; functional-analysis applications.