TEM-1 beta-lactamase (gene *bla*, UniProt P62593) -- the 286-aa class A serine beta-lactamase precursor that confers ampicillin resistance, the canonical AmpR selection marker.

## Origin
The *bla* gene of *E. coli* plasmid pBR322 (derived from transposon Tn3/Tn2) encodes TEM-1, the prototype class A beta-lactamase. The full pBR322 sequence including this ampicillin-resistance gene was reported by Sutcliffe ([PMID 383387](https://pubmed.ncbi.nlm.nih.gov/383387/)). The stored part is the 286-residue precursor: a 23-aa Sec-dependent signal peptide (residues 1-23) followed by the mature periplasmic enzyme (residues 24-286, beginning at His24).

## Properties
TEM-1 is a serine hydrolase that inactivates penicillins (and, in its natural form, early cephalosporins) by acylating the beta-lactam carbonyl at the active-site serine. Catalysis uses the conserved class A machinery, all confirmed in the 1.8 A crystal structure ([PMID 8356032](https://pubmed.ncbi.nlm.nih.gov/8356032/)) and numbered by the Ambler scheme ([PMID 2039479](https://pubmed.ncbi.nlm.nih.gov/2039479/)):
- **Ser70** (S-x-x-K box, seq STFK) -- acylating nucleophile.
- **Lys73** -- general base partner H-bonded to Ser70.
- **Ser130** (S-D-N loop) -- proton-relay serine, H-bonded to Lys234.
- **Glu166** (omega loop) -- activates the deacylating water; the omega loop is a key regulatory element of TEM enzymes ([PMID 31835662](https://pubmed.ncbi.nlm.nih.gov/31835662/)).
- **Lys234-Ser235-Gly236** (K-S-G box) -- anchors the substrate carboxylate.

A single disulfide bond joins **Cys77** and **Cys123**, bridging the all-alpha and alpha/beta domains; its removal costs ~14 kJ/mol of stability and accelerates thermal inactivation but does not abolish catalysis ([PMID 9020874](https://pubmed.ncbi.nlm.nih.gov/9020874/)).

## Use
Standard ampicillin/carbenicillin resistance marker (AmpR) for plasmid selection in *E. coli*. The signal peptide directs the enzyme to the periplasm; for cytoplasmic or fusion applications the leader is typically removed. Note the catalog stores the precursor (leader + mature chain), so alignments against the 263-aa mature protein will be offset by 23 residues.

## References
- [PMID 383387](https://pubmed.ncbi.nlm.nih.gov/383387/) -- Sutcliffe JG. Complete nucleotide sequence of the *E. coli* plasmid pBR322. *Cold Spring Harb Symp Quant Biol* (1979). [DOI](https://doi.org/10.1101/sqb.1979.043.01.013)
- [PMID 2039479](https://pubmed.ncbi.nlm.nih.gov/2039479/) -- Ambler RP et al. A standard numbering scheme for the class A beta-lactamases. *Biochem J* (1991). [DOI](https://doi.org/10.1042/bj2760269)
- [PMID 8356032](https://pubmed.ncbi.nlm.nih.gov/8356032/) -- Jelsch C et al. Crystal structure of *E. coli* TEM1 beta-lactamase at 1.8 A resolution. *Proteins* (1993). [DOI](https://doi.org/10.1002/prot.340160406)
- [PMID 9020874](https://pubmed.ncbi.nlm.nih.gov/9020874/) -- Vanhove M et al. Consequences of removal of the Cys-77-Cys-123 disulphide bond for folding of TEM-1 beta-lactamase. *Biochem J* (1997). [DOI](https://doi.org/10.1042/bj3210413)
- [PMID 31835662](https://pubmed.ncbi.nlm.nih.gov/31835662/) -- Egorov A et al. The role of the Omega-loop in regulation of the catalytic activity of TEM-type beta-lactamases. *Biomolecules* (2019). [DOI](https://doi.org/10.3390/biom9120854)

*Reference metadata retrieved from PubMed.*
