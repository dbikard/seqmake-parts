Pxyl/tet: the TetR-repressible, anhydrotetracycline (aTc)-inducible promoter of the *Staphylococcus aureus* pRAB expression vectors (Helle et al. 2011) — a consensus -35/-10 promoter carrying two Tn10 *tet* operators (the O2/O1 tandem), one in the spacer and one downstream of the +1, so TetR represses transcription until aTc relieves it.

## Origin
Pxyl/tet is the inducible promoter of the *S. aureus* pRAB shuttle-vector series (Helle et al. 2011, [PMID 21921101](https://pubmed.ncbi.nlm.nih.gov/21921101/)); the sequence of record is **pRAB11** (GenBank [JN635500.1](https://www.ncbi.nlm.nih.gov/nuccore/JN635500.1)). It pairs a consensus -35 (TTGACA) / -10 (TATAAT) core with two Tn10 *tet* operators (originally sequenced by Hillen & Schollmeier 1983, [PMID 6298728](https://pubmed.ncbi.nlm.nih.gov/6298728/)). This is **not** the λ-PL Lutz & Bujard PLtetO-1: aligned end-to-end, this part is 57/58 identical to the pRAB11 Pxyl/tet core (trimmed of pRAB11's 5′ XhoI leader and 3′ KpnI/MCS), whereas it shares only the operator dyad with PLtetO-1.

> **Lab variant.** The Bikard-lab lineage (≥300 plasmids, origin construct `pDB268 pE194-tetO2-rep`) carries a single-base −10 substitution, **CATAAT** instead of the canonical **TATAAT**. seqmake annotates that copy as **`Pxyl/tet [T24C]`** — the same part, with the point mutation named. The catalog stores the canonical pRAB11 sequence.

## Properties
- **Length:** 58 bp, all features on the + strand.
- **Promoter:** -35 = TTGACA [0,6) (perfect consensus); -10 = TATAAT [23,29) (perfect consensus); 17-bp -35/-10 spacer; inferred +1 = A at [36,37), ~7 nt 3′ of the -10.
- **Operators:** two 19-bp Tn10 *tet* operators sharing the core dyad CTCTATCATTGATAGAG — tetO1 [4,23) overlapping the -35 3′ edge and filling the spacer, and tetO2 [39,58) downstream of the +1. Both are bound by the TetR homodimer; the tandem-operator arrangement and differential regulation were established by Meier et al. 1988 ([PMID 2835235](https://pubmed.ncbi.nlm.nih.gov/2835235/)) and operator base requirements by Wissmann et al. 1986 ([PMID 3086838](https://pubmed.ncbi.nlm.nih.gov/3086838/)); see also the Bertram et al. 2022 review ([PMID 34713957](https://pubmed.ncbi.nlm.nih.gov/34713957/)).

## Use
A repressible/inducible promoter for tunable expression in *S. aureus* and other bacteria: TetR keeps it OFF, anhydrotetracycline (aTc) induces it. The two-operator arrangement gives tight OFF-state repression, well suited to driving toxic or dosage-sensitive payloads. Pair it with a *tetR* cassette (as in pRAB11 / pDB268).

## References
- [PMID 21921101](https://pubmed.ncbi.nlm.nih.gov/21921101/) — Helle et al. 2011, the *S. aureus* pRAB Pxyl/tet vectors (sequence source; pRAB11 = GenBank JN635500.1).
- [PMID 6298728](https://pubmed.ncbi.nlm.nih.gov/6298728/) — Hillen & Schollmeier 1983, Tn10 *tet* gene/operator sequence.
- [PMID 2835235](https://pubmed.ncbi.nlm.nih.gov/2835235/) — Meier et al. 1988, tandem tetO1/O2 differential regulation.
- [PMID 3086838](https://pubmed.ncbi.nlm.nih.gov/3086838/) — Wissmann et al. 1986, *tet* operator mutations and TetR recognition.
- [PMID 34713957](https://pubmed.ncbi.nlm.nih.gov/34713957/) — Bertram et al. 2022, review of *tet* regulation (tetO1/O2 dyad, TetR homodimer).
