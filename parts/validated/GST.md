# GST

*Schistosoma japonicum* 26 kDa glutathione S-transferase (Sj26GST) — a 218-amino-acid
affinity tag and solubility partner widely used for one-step purification of recombinant
fusion proteins on glutathione resin.

## Origin

The sequence derives from the *Schistosoma japonicum* Sj26GST antigen (UniProt P08515,
Swiss-Prot reviewed, sequence version 3). The founding expression system, described in
1988 (Smith & Johnson), established the use of this protein as an affinity handle fused to
recombinant proteins for purification from bacterial lysates, and it became the fusion
partner of the pGEX vector family. The 218 aa sequence is the canonical full-length form.

## Properties

GST forms a non-covalent homodimer in solution; each subunit folds independently but the
functional enzyme is dimeric (Kaplan 1997). Thermodynamic stability is high (ΔG ≈ 26
kcal/mol, two-state unfolding). In the context of fusion proteins, the homodimeric nature
means that two copies of the fused partner are co-presented, which can force dimerization
of the target. The protein functions both as an affinity handle (binds glutathione-agarose;
eluted with reduced glutathione) and as a chaperone-like solubility partner that promotes
soluble expression of otherwise insoluble target proteins (Harper & Speicher 2011).
Residue-level features defer to the linked UniProt entry.

## Use

GST is expressed as an N-terminal fusion to a protein of interest, typically with an
intervening protease cleavage site (thrombin, factor Xa, or TEV protease recognition
sequences — encoded as separate catalog parts). The fusion protein is captured on
glutathione resin under non-denaturing conditions and eluted with reduced glutathione; the
tag is subsequently removed by site-specific proteolysis. The cleavage site lives in the
linker between GST and the protein of interest, **not** within the GST coding sequence
itself, so a removable-tag construct composes GST + cleavage_site + target. The system
functions in *Escherichia coli* as the primary expression host, and has also been applied
in *Saccharomyces cerevisiae* and *Schizosaccharomyces pombe* (Smith 2000). Because of the
obligate dimer structure, this tag is less suitable when monomeric presentation of the
fusion partner is required.

## References

- Smith DB, Johnson KS (1988). Single-step purification of polypeptides expressed in
  *Escherichia coli* as fusions with glutathione S-transferase. *Gene*.
  PMID:[3047011](https://pubmed.ncbi.nlm.nih.gov/3047011/) |
  DOI:[10.1016/0378-1119(88)90005-4](https://doi.org/10.1016/0378-1119(88)90005-4)
- Kaplan W, Husler P, Klump H, Erhardt J, Sluis-Cremer N, Dirr H (1997). Conformational
  stability of pGEX-expressed *Schistosoma japonicum* glutathione S-transferase.
  *Protein Science*.
  PMID:[9041642](https://pubmed.ncbi.nlm.nih.gov/9041642/) |
  DOI:[10.1002/pro.5560060216](https://doi.org/10.1002/pro.5560060216)
- Smith DB (2000). Generating fusions to glutathione S-transferase for protein studies.
  *Methods in Enzymology*.
  PMID:[11036647](https://pubmed.ncbi.nlm.nih.gov/11036647/) |
  DOI:[10.1016/s0076-6879(00)26059-x](https://doi.org/10.1016/s0076-6879(00)26059-x)
- Harper S, Speicher DW (2011). Purification of proteins fused to glutathione
  S-transferase. *Methods in Molecular Biology*.
  PMID:[20978970](https://pubmed.ncbi.nlm.nih.gov/20978970/) |
  DOI:[10.1007/978-1-60761-913-0_14](https://doi.org/10.1007/978-1-60761-913-0_14)
