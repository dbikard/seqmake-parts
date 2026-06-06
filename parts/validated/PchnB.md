Cyclohexanone-inducible promoter (PchnB) from *Acinetobacter johnsonii* NCIMB 9871, activated in *trans* by the AraC/XylS-family regulator ChnR.

## Origin
PchnB is the upstream regulatory region of the *chnB* gene (cyclohexanone monooxygenase) in the cyclohexanol catabolic gene cluster of *Acinetobacter johnsonii* NCIMB 9871 (GenBank AB006902; gene order *chnB-chnE-chnR*). Its cognate activator ChnR was identified by Iwaki et al. 1999 ([PMID 10543838](https://pubmed.ncbi.nlm.nih.gov/10543838/)). This 396-bp part is a fragment of that upstream region; the canonical registry definition spans 537 bp upstream of *chnB* to its start codon (iGEM BBa_K1946001), and the SEVA-standardized variant is the ~500 bp immediately preceding the *chnB* ATG ([PMID 26870759](https://pubmed.ncbi.nlm.nih.gov/26870759/)).

## Properties
The promoter is silent without inducer and is activated by ChnR in the presence of cyclohexanone, giving tight, dose-responsive expression in *E. coli* and *Pseudomonas* ([PMID 17950643](https://pubmed.ncbi.nlm.nih.gov/17950643/)). One *cis* element is annotated: a candidate ChnR-responsive site, the conserved 11-nt block `TTGTTTGGATC` at part position 15 (0-based [14,25), +1 strand), identical between the *chnA* and *chnB* upstream regions ~390 bp upstream of the *chnB* ATG ([PMID 10940013](https://pubmed.ncbi.nlm.nih.gov/10940013/)). Its role in ChnR binding is a hypothesis ("remains to be tested") and has not been confirmed by footprinting/EMSA. No -35/-10/+1 or RBS is mapped in the literature, so none are annotated.

## Use
Inducible expression tool for metabolic engineering: pair this promoter with the cognate activator ChnR (iGEM BBa_K1946000) and induce with cyclohexanone. The promoter alone is non-functional without ChnR supplied in *trans*. Note that this part is shorter than the canonical PchnB and does not extend to the *chnB* ATG, so verify boundaries before use.

## References
- [PMID 10940013](https://pubmed.ncbi.nlm.nih.gov/10940013/) — Cheng et al. 2000, *J Bacteriol* — conserved 11-nt ChnR-candidate block.
- [PMID 17950643](https://pubmed.ncbi.nlm.nih.gov/17950643/) — Steigedal & Valla 2008, *Metab Eng* — chnB/ChnR inducible system characterization.
- [PMID 10543838](https://pubmed.ncbi.nlm.nih.gov/10543838/) — Iwaki et al. 1999, *Appl Environ Microbiol* — ChnR identification, cluster/origin.
- [PMID 26870759](https://pubmed.ncbi.nlm.nih.gov/26870759/) — Benedetti et al. 2016, *Data in Brief* — SEVA-standardized PchnB.