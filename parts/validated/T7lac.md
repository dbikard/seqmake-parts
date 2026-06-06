Engineered **T7lac** regulatory region: the bacteriophage T7 phi10 (class III) promoter immediately followed by a lac operator O1, giving LacI-controllable, low-basal expression from T7 RNA polymerase.

## Origin
This is the canonical **T7lac** promoter described by Dubendorff & Studier ([PMID 1902522](https://pubmed.ncbi.nlm.nih.gov/1902522/)), the configuration used throughout the pET expression system. It joins the standard T7 phi10 promoter consensus (TAATACGACTCACTATAG) to the natural 21 bp lac operator O1 (AATTGTGAGCGGATAACAATT) positioned so the operator center lies ~15 bp downstream of the T7 +1 start. The 67 bp part as supplied also carries ~23 bp of upstream cloning/vector sequence before the promoter.

## Properties
- **T7 promoter (idx 24-42, +):** 18 bp phi10 class III consensus, recognized by single-subunit T7 RNA polymerase, not by host sigma-70 holoenzyme. The upstream ~13 bp (TAATACGACTCAC, idx 24-37) form the polymerase recognition/binding domain.
- **+1 start (idx 41-44, +):** transcription initiates at the 3' G of the consensus; class III promoters favor a G/poly(G) run with a purine/GTP preference (here the GGGG run at idx 41-44). See [PMID 10956032](https://pubmed.ncbi.nlm.nih.gov/10956032/).
- **lac operator O1 (idx 45-66, +):** natural 21 bp operator; its central GCGG is contacted by the LacI hinge helices in the minor groove ([PMID 8638105](https://pubmed.ncbi.nlm.nih.gov/8638105/)). Bound LacI blocks the adjacent T7 promoter, suppressing basal transcription.

## Use
Drives tightly regulated T7-polymerase transcription in expression hosts that supply T7 RNAP in trans (e.g. lambdaDE3 lysogens). LacI bound at the operator lowers leaky basal expression; adding IPTG relieves repression and allows full T7-driven transcription. Requires a LacI source (host or lacIq on the plasmid) to function as a regulated promoter.

## References
- [PMID 1902522](https://pubmed.ncbi.nlm.nih.gov/1902522/) — Dubendorff & Studier 1991, defining T7lac paper (operator placement, LacI repression, IPTG derepression).
- [PMID 10956032](https://pubmed.ncbi.nlm.nih.gov/10956032/) — Imburgio et al. 2000, T7 promoter recognition, binding vs. initiation domains, +1 start-site selection.
- [PMID 4587255](https://pubmed.ncbi.nlm.nih.gov/4587255/) — Gilbert & Maxam 1973, original lac operator sequence.
- [PMID 8638105](https://pubmed.ncbi.nlm.nih.gov/8638105/) — Lewis et al. 1996, LacI/operator crystal structure (central GCGG, hinge-helix contacts).