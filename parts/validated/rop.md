# rop

The ColE1/pMB1 **Rop** protein (also **Rom**, "RNA one modulator") is a small 63-amino-acid
homodimer that fine-tunes plasmid copy number. It neither starts nor blocks replication
directly; it acts as an auxiliary that strengthens the plasmid's own antisense control loop.

## Origin

Rop is encoded just downstream of the ColE1/pMB1 replication origin, and its 63-residue
sequence is completely conserved between ColE1 and pMB1 (Cesareni 1982). It is carried by
the classic medium-copy vectors of the pBR322 lineage and is absent from the high-copy pUC
lineage, which contributes to the higher copy number of pUC-based plasmids.

## Properties

- **Function:** a *trans*-acting negative regulator of replication initiation. Rop enhances
  pairing of the antisense RNA I with the RNA II primer precursor, blocking formation of the
  replication primer (Tomizawa & Som 1984).
- **Net effect:** lowers plasmid copy number; loss of rop raises it.
- **Structure:** a compact homodimeric four-helix bundle (residue-level features defer to the
  linked UniProt entry).
- **Cognate system:** the ColE1/pMB1 origin's RNA I / RNA II control region (see the `ColE1`
  part).

## Use

Include rop on a ColE1/pMB1-origin construct to hold copy number at the moderate pBR322 level;
omit it for the high-copy pUC level. Because it acts in *trans*, rop supplied from one location
can modulate a ColE1-origin replicon.

## References

1. Cesareni G, Muesing MA, Polisky B. *Control of ColE1 DNA replication: the rop gene product
   negatively affects transcription from the replication primer promoter.* Proc Natl Acad Sci
   U S A 79(20):6313–6317 (1982). doi:10.1073/pnas.79.20.6313
2. Tomizawa J, Som T. *Control of ColE1 plasmid replication: enhancement of binding of RNA I to
   the primer transcript by the Rom protein.* Cell 38(3):871–878 (1984).
   doi:10.1016/0092-8674(84)90282-4
