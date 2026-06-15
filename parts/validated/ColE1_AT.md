# ColE1_AT

The common **cloning-vector form** of the ColE1/pMB1 origin: identical to the canonical
pMB1 replication origin except for a benign 2-bp difference (positions 412–413) in the
RNA I / RNA II control region. This is the version that a large fraction of everyday
cloning vectors actually carry, so it is documented in its own right rather than treated
as an error in the canonical sequence.

## Origin

ColE1/pMB1-family origins set plasmid copy number through a pair of convergent transcripts
— the RNA II pre-primer and the antisense RNA I (see the [`ColE1`](ColE1.md) part for the
canonical sequence and the control mechanism). The `AT` form here differs from the
canonical pBR322 (GenBank J01749, 1981) / pUC18 (L08752, 1985) origin by 2 bp at
positions 412–413. A date-bracketed search of deposited sequences finds this exact form in
**140+ vectors going back to at least 1985** — the earliest being a P-element
transformation vector (GenBank X01803, Nov 1985), and the oldest cleanly-named cloning
vector being **pEX2** (X03174, 1986).

## Properties

- **Relationship to canonical:** a 2-bp difference from the canonical pMB1 origin, within
  the RNA I/RNA II control region.
- **Benign:** its ubiquity across decades of widely-used cloning vectors shows the
  difference does not impair replication — encountering these two positions in a vector is
  expected, not a cause for concern.
- **Copy number:** high, like the canonical origin (set by the RNA I/RNA II antisense
  system); lowered by the separate [`rop`](rop.md) protein when present.

## Use

Use interchangeably with the canonical `ColE1` origin for high-copy propagation in
*E. coli*. It is kept as a distinct part so the common 2-bp difference is explained and
expected rather than flagged.

## References

1. Itoh T, Tomizawa J. *Formation of an RNA primer for initiation of replication of ColE1
   DNA by ribonuclease H.* Proc Natl Acad Sci U S A 77(5):2450–2454 (1980).
   doi:10.1073/pnas.77.5.2450
2. Lin-Chao S, Bremer H. *Activities of the RNAI and RNAII promoters of plasmid pBR322.*
   J Bacteriol 169(3):1217–1222 (1987). doi:10.1128/jb.169.3.1217-1222.1987
3. Tomizawa J, Itoh T, Selzer G, Som T. *Inhibition of ColE1 RNA primer formation by a
   plasmid-specified small RNA.* Proc Natl Acad Sci U S A 78(3):1421–1425 (1981).
   doi:10.1073/pnas.78.3.1421
