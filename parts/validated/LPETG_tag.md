# LPETG_tag

LPETG is the canonical sortase A recognition motif — a single instance of the Gram-positive LPXTG cell-wall sorting signal — and the standard C-terminal handle for sortase-mediated protein ligation (sortagging).

## Origin
LPETG (Leu-Pro-Glu-Thr-Gly) is the native C-terminal cell-wall sorting signal of *Staphylococcus aureus* Immunoglobulin G-binding protein A (Protein A / SpA), where it is annotated as the "LPXTG sorting signal" motif (UniProt P02976, residues 482-486). The same LPXTG-class signal occurs in many Gram-positive surface proteins (e.g. fibronectin-binding protein FnbA, UniProt P14738, residues 982-986). Mass-spectrometry analysis of native SpA confirms the exact LPETG sequence in the precursor protein (PMID 25644005). The sequence is source-verified at 100% identity (5/5 residues) to the UniProt P02976 motif annotation.

## Properties
LPETG belongs to the LPXTG consensus, with Glu (E) at the variable X position — a residue commonly found in efficient sortase substrates. Sortase A (SrtA), a cysteine transpeptidase, recognizes LPXTG and cleaves the Thr-Gly bond (LPET|G), forming a covalent acyl-enzyme thioester intermediate at its active-site cysteine. This intermediate is then resolved by nucleophilic attack of an N-terminal oligoglycine (Gly-n) amine, transferring the LPET-acyl group onto the acceptor and reconstituting an LPETGG... junction (PMID 10427003, PMID 10535938). In its natural role this transpeptidation anchors surface proteins to the peptidoglycan via the pentaglycine cross-bridge. Synthetic LPETG-containing peptides are incorporated into the *S. aureus* cell wall in a SrtA- and growth-phase-dependent manner (PMID 24586638). The motif itself is host-agnostic: ligation depends only on the supplied sortase, often the evolved pentamutant eSrtA, which has markedly improved activity toward LPETG (PMID 21697512).

## Use
A protein bearing a C-terminal LPETG can be site-specifically conjugated to any partner that presents an N-terminal (oligo)glycine — peptides, proteins, small molecules, surfaces, and even D- or branched peptides (PMID 14995162). For efficient cleavage the LPXTG motif should lie in an accessible, unstructured region; a common engineering layout places an affinity tag downstream (e.g. POI-LPETG-His6) so the tag is removed upon ligation (PMID 23989673). Typical applications include site-specific bioconjugation and labeling, protein-protein and protein-peptide ligation, protein immobilization, and C-terminal or internal-loop labeling. Orthogonal engineered sortases that instead read LAXTG or LPXSG enable dual, independent labeling alongside canonical LPETG chemistry (Dorr et al. 2014, DOI 10.1073/pnas.1411179111).

## References
- Mazmanian et al. 1999, Science — [PMID 10427003](https://pubmed.ncbi.nlm.nih.gov/10427003/) · [doi:10.1126/science.285.5428.760](https://doi.org/10.1126/science.285.5428.760)
- Ton-That et al. 1999, PNAS — [PMID 10535938](https://pubmed.ncbi.nlm.nih.gov/10535938/) · [doi:10.1073/pnas.96.22.12424](https://doi.org/10.1073/pnas.96.22.12424)
- Mao et al. 2004, JACS — [PMID 14995162](https://pubmed.ncbi.nlm.nih.gov/14995162/) · [doi:10.1021/ja039915e](https://doi.org/10.1021/ja039915e)
- Guimaraes et al. 2013, Nat Protoc — [PMID 23989673](https://pubmed.ncbi.nlm.nih.gov/23989673/) · [doi:10.1038/nprot.2013.101](https://doi.org/10.1038/nprot.2013.101)
- Chen et al. 2011, PNAS — [PMID 21697512](https://pubmed.ncbi.nlm.nih.gov/21697512/) · [doi:10.1073/pnas.1101046108](https://doi.org/10.1073/pnas.1101046108)
- Dorr et al. 2014, PNAS — [doi:10.1073/pnas.1411179111](https://doi.org/10.1073/pnas.1411179111)
- Hansenova Manaskova et al. 2014, PLoS One — [PMID 24586638](https://pubmed.ncbi.nlm.nih.gov/24586638/) · [doi:10.1371/journal.pone.0089260](https://doi.org/10.1371/journal.pone.0089260)
- O'Halloran et al. 2015, Infect Immun — [PMID 25644005](https://pubmed.ncbi.nlm.nih.gov/25644005/) · [doi:10.1128/IAI.03122-14](https://doi.org/10.1128/IAI.03122-14)