# E-tag

Synthetic 13-residue epitope/affinity tag (GAPVPYPDPLEPR) derived from the M13 bacteriophage g3p protein, used as the C-terminal detection and purification tag of the pCANTAB 5E phage-display system.

## Origin

The E-tag is an engineered short peptide tag based on an epitope of the M13 bacteriophage gene III protein (g3p). The conceptual precursor is a multifunctional g3p-peptide epitope recognized by a high-affinity monoclonal antibody (mAb 10C3, dissociation constant ~6.8 x 10^-10 M), defined as a minimal ~11-residue epitope within g3p [PMID:9672201], following earlier work that mapped anti-pIII antibodies to the C-terminal half of g3p [PMID:9373333]. The 13-residue form GAPVPYPDPLEPR was adopted as the carboxyl-terminal tag of the pCANTAB 5E single-chain antibody phage-display vector. The earliest fetchable nucleotide deposit explicitly annotating the tag is a phagemid vector record carrying a misc_feature labelled "E-tag" whose 39-bp translation yields GAPVPYPDPLEPR exactly. (The identical 13-residue string also occurs by coincidence within human osteocalcin; this is unrelated to the engineered tag's origin.)

## Properties

The tag is a compact, hydrophilic 13-amino-acid peptide. It is recognized with high specificity by a cognate anti-E-tag monoclonal antibody, enabling immunodetection by western blot and ELISA and affinity capture of tagged proteins. In single-chain variable fragment (scFv) constructs it can serve a dual role, contributing favorable structural/linker behaviour in addition to detection [PMID:27113782]. A practical limitation of antibody-based affinity purification with this tag is the cost of the cognate anti-E-tag antibody [PMID:11849927].

## Use

The E-tag is most commonly fused at the carboxyl terminus of antibody fragments (scFv and Fab) in phage-display and recombinant-antibody workflows, where it is used to track and detect scFv-g3p fusion display and free antibody fragments, and to affinity-purify them via the anti-E-tag antibody [PMID:11849927][PMID:20952642]. In the pCANTAB 5E vector an amber stop codon separates the tag from g3p, so suppressor and non-suppressor hosts toggle between displayed and soluble tagged product; some derivative vectors swap the E-tag for other epitope tags [PMID:11861923]. It functions in Escherichia coli expression and on M13 phage.

## References

- Beckmann C et al. (1998) Multifunctional g3p-peptide tag for current phage display systems. *J Immunol Methods*. [PMID:9672201](https://pubmed.ncbi.nlm.nih.gov/9672201/) | [DOI:10.1016/s0022-1759(98)00008-8](https://doi.org/10.1016/s0022-1759(98)00008-8)
- Tesar M et al. (1995) Monoclonal antibody against pIII of filamentous phage. *Immunotechnology*. [PMID:9373333](https://pubmed.ncbi.nlm.nih.gov/9373333/) | [DOI:10.1016/1380-2933(95)00005-4](https://doi.org/10.1016/1380-2933(95)00005-4)
- Kramer K et al. (2002) A generic strategy for subcloning antibody variable regions from the scFv phage display vector pCANTAB 5 E into pASK85. *Biosens Bioelectron*. [PMID:11849927](https://pubmed.ncbi.nlm.nih.gov/11849927/) | [DOI:10.1016/s0956-5663(01)00292-5](https://doi.org/10.1016/s0956-5663(01)00292-5)
- Baek H et al. (2002) An improved helper phage system for efficient isolation of specific antibody molecules in phage display. *Nucleic Acids Res*. [PMID:11861923](https://pubmed.ncbi.nlm.nih.gov/11861923/) | [DOI:10.1093/nar/30.5.e18](https://doi.org/10.1093/nar/30.5.e18)
- Singh PK et al. (2010) Construction of a single-chain variable-fragment antibody against the superantigen staphylococcal enterotoxin B. *Appl Environ Microbiol*. [PMID:20952642](https://pubmed.ncbi.nlm.nih.gov/20952642/) | [DOI:10.1128/AEM.01441-10](https://doi.org/10.1128/AEM.01441-10)
- Mohammadi M et al. (2016) In silico analysis of three different tag polypeptides with dual roles in scFv antibodies. *J Theor Biol*. [PMID:27113782](https://pubmed.ncbi.nlm.nih.gov/27113782/) | [DOI:10.1016/j.jtbi.2016.04.016](https://doi.org/10.1016/j.jtbi.2016.04.016)
