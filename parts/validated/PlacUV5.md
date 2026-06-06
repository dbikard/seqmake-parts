**PlacUV5** — the 30 bp core lacUV5 promoter (-35 through -10), a point-mutant derivative of the natural *E. coli lac* promoter carrying the catabolite-insensitive, promoter-up UV5 allele.

## Origin
lacUV5 is not a synthetic design but a mutant derivative of the wild-type *lac* promoter. It was first isolated by Silverstone, Arditti & Magasanik (1970) as a catabolite-insensitive (CAP/cAMP-independent) promoter-up revertant of a *lac* promoter mutant ([PMID 4913210](https://pubmed.ncbi.nlm.nih.gov/4913210/)). The nucleotide change responsible was later localized to the -10 box when Dickson et al. (1975) sequenced the *lac* control region ([PMID 1088926](https://pubmed.ncbi.nlm.nih.gov/1088926/)).

## Properties
This 30 bp part tiles exactly into three contiguous elements:
- **-35 box** ([0,6) `TTTACA`) — the *lac* -35 hexamer, deviating from the sigma70 consensus TTGACA at position 3; unchanged by the UV5 allele.
- **Spacer** ([6,24) `CTTTATGCTTCCGGCTCG`, 18 bp) — the -35/-10 interbox separation.
- **-10 box** ([24,30) `TATAAT`) — the perfect sigma70 consensus Pribnow box. This is the defining UV5 mutation: the WT *lac* -10 (TATGTT) is converted to consensus TATAAT (-9 G->A, -8 T->A).

The consensus -10 box makes lacUV5 a strong, constitutively active sigma70 promoter that, unlike the WT *lac* promoter, does not require CAP/cAMP activation.

## Use
lacUV5 is widely used as a strong, IPTG-inducible (when paired with *lacO* + LacI) promoter for heterologous expression in *E. coli*; it is the *lac*-derived half of hybrid promoters such as *tac*. As delimited, this part is the core promoter only and stops at the -10 box — it does not include the +1 transcription start site or the downstream *lac* operator O1 (the LacI binding site), both of which lie 3' of position 30.

## References
- [PMID 4913210](https://pubmed.ncbi.nlm.nih.gov/4913210/) — Silverstone, Arditti & Magasanik 1970, *PNAS* (UV5 isolation as catabolite-insensitive promoter-up mutant).
- [PMID 1088926](https://pubmed.ncbi.nlm.nih.gov/1088926/) — Dickson, Abelson, Barnes & Reznikoff 1975, *Science* (lac control-region sequence; -35/-10 mapping, UV5 -10 change).