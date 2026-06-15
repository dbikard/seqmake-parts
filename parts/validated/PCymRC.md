# PCymRC

CymR-repressible synthetic promoter: a σ70 core (−35/−10) flanked by two cumate
operators (CuO). When no inducer is present, the CymR repressor occupies the
operators and blocks RNA polymerase; the small molecule p-cumate binds CymR and
lowers its operator affinity, de-repressing transcription.

## Origin

The cumate regulatory module comes from the *cym*/*cmt* operons of *Pseudomonas
putida* F1, where the repressor CymR controls genes for p-cymene/p-cumate catabolism
and is induced by p-cumate but not p-cymene (Eaton 1997). PCymRC is a synthetic
promoter built on that module — a σ70 core carrying two CymR operator sites, one over
the −35 and one over the transcription start — characterized as one of a panel of
small-molecule sensors optimized for *Escherichia coli* (Meyer 2018). The 90-bp
sequence here is taken from that work (Addgene pAJM.712 #108513; GenBank MH101728,
the pAJM.657 deposit), with the two operators, −35, −10 and +1 following the deposited
annotation.

## Properties

- **Regulation:** repressed by CymR; **induced (de-repressed) by p-cumate**
  (p-isopropylbenzoate).
- **Architecture:** two 32-bp cumate operators (CuO) flank a σ70 core; the upstream
  operator overlaps the −35 and the downstream operator spans the +1, so repressor
  binding occludes initiation.
- **Dynamic range:** the sensor panel it belongs to was engineered for >100-fold
  induction with low background; a PCymRC-specific value is not broken out in the
  source.
- **Host:** characterized in *E. coli*.

## Use

Pair PCymRC with its cognate repressor CymR to place a gene under p-cumate control —
an orthogonal chemical input that combines with other inducible systems for
independent, multiplexed regulation. Induce with p-cumate.

## References

1. Meyer AJ, Segall-Shapiro TH, Glassey E, Zhang J, Voigt CA. *Escherichia coli
   "Marionette" strains with 12 highly optimized small-molecule sensors.* Nat Chem
   Biol 15(2):196–204 (2018). doi:10.1038/s41589-018-0168-3
2. Eaton RW. *p-Cymene catabolic pathway in Pseudomonas putida F1: cloning and
   characterization of DNA encoding conversion of p-cymene to p-cumate.* J Bacteriol
   179(10):3171–3180 (1997). doi:10.1128/jb.179.10.3171-3180.1997
