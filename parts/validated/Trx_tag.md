# Trx_tag

E. coli thioredoxin-1 (trxA, UniProt P0AA25, 109 aa) used as a N-terminal fusion partner to promote solubility of recombinant proteins expressed in the bacterial cytoplasm.

## Origin

Thioredoxin-1 from *Escherichia coli* K12. The primary sequence was determined in 1968 ([PMID:4883076](https://pubmed.ncbi.nlm.nih.gov/4883076/); [doi:10.1111/j.1432-1033.1968.tb00470.x](https://doi.org/10.1111/j.1432-1033.1968.tb00470.x)) and is encoded by the chromosomal *trxA* gene. The crystal structure at 1.68 Å resolution ([PMID:2181145](https://pubmed.ncbi.nlm.nih.gov/2181145/); [doi:10.1016/0022-2836(90)90136-b](https://doi.org/10.1016/0022-2836(90)90136-b)) defines the canonical thioredoxin fold and confirms domain boundaries (residues 1–109, full protein). Its biochemistry as a cellular reductant is reviewed in [PMID:3896121](https://pubmed.ncbi.nlm.nih.gov/3896121/) ([doi:10.1146/annurev.bi.54.070185.001321](https://doi.org/10.1146/annurev.bi.54.070185.001321)). Its adoption as an expression fusion partner was reported in 1993 ([PMID:7763371](https://pubmed.ncbi.nlm.nih.gov/7763371/); [doi:10.1038/nbt0293-187](https://doi.org/10.1038/nbt0293-187)).

## Properties

- **Solubility enhancement:** N-terminal fusion of Trx_tag substantially reduces inclusion body formation for aggregation-prone passenger proteins expressed in the *E. coli* cytoplasm ([PMID:7763371](https://pubmed.ncbi.nlm.nih.gov/7763371/)).
- **Thermostability:** Tm ~85 °C, enabling a heat-treatment step (65–80 °C) after cell lysis to selectively denature most co-purifying host proteins while the Trx fusion remains soluble, providing a simple purity enhancement step ([PMID:34191368](https://pubmed.ncbi.nlm.nih.gov/34191368/); [doi:10.1002/pro.4150](https://doi.org/10.1002/pro.4150)).
- **Osmotic shock release:** Thioredoxin-1 accumulates in the osmotic-shock fraction when expressed in *E. coli*, allowing selective release of the fusion without complete cell disruption ([PMID:7763371](https://pubmed.ncbi.nlm.nih.gov/7763371/)).
- **Active site (WCGPCK, residues 32–37):** Cys33 and Cys36 form a redox-active dithiol/disulfide; the tag is catalytically active as expressed. A C33A/C36A redox-dead variant is used when the passenger protein contains cysteines that must not be perturbed ([PMID:10489448](https://pubmed.ncbi.nlm.nih.gov/10489448/); [doi:10.1107/s0907444999010392](https://doi.org/10.1107/s0907444999010392)).
- **No intrinsic affinity handle:** Trx_tag lacks an affinity handle; a co-expressed His-tag or other affinity tag is required for immobilized metal affinity purification ([PMID:24600443](https://pubmed.ncbi.nlm.nih.gov/24600443/)).
- **Size:** 109 aa (~12 kDa), adding modest molecular weight to the fusion.

## Use

Trx_tag is fused N-terminally to the passenger protein via a short linker that typically encodes a protease recognition sequence (thrombin or enterokinase site) for optional tag removal after purification. Expression in *E. coli* is performed under standard conditions; the heat-step protocol provides an additional purification advantage for thermolabile contaminants. After affinity capture (via a co-tag), the Trx portion is cleaved by the cognate protease and removed by subtractive IMAC. Detailed protocols are available in [PMID:11036651](https://pubmed.ncbi.nlm.nih.gov/11036651/) ([doi:10.1016/s0076-6879(00)26063-1](https://doi.org/10.1016/s0076-6879(00)26063-1)) and [PMID:18429194](https://pubmed.ncbi.nlm.nih.gov/18429194/) ([doi:10.1002/0471140864.ps0607s10](https://doi.org/10.1002/0471140864.ps0607s10)). Trx_tag is ranked alongside MBP as a best-in-class solubility tag in comparative reviews ([PMID:24600443](https://pubmed.ncbi.nlm.nih.gov/24600443/)).

## References

- [PMID:4883076](https://pubmed.ncbi.nlm.nih.gov/4883076/) — Holmgren A (1968) Thioredoxin. 6. The amino acid sequence of the protein from *Escherichia coli* B. *Eur J Biochem.* [doi:10.1111/j.1432-1033.1968.tb00470.x](https://doi.org/10.1111/j.1432-1033.1968.tb00470.x)
- [PMID:3896121](https://pubmed.ncbi.nlm.nih.gov/3896121/) — Holmgren A (1985) Thioredoxin. *Annu Rev Biochem.* [doi:10.1146/annurev.bi.54.070185.001321](https://doi.org/10.1146/annurev.bi.54.070185.001321)
- [PMID:2181145](https://pubmed.ncbi.nlm.nih.gov/2181145/) — Katti SK, LeMaster DM, Eklund H (1990) Crystal structure of thioredoxin from *E. coli* at 1.68-Å resolution. *J Mol Biol.* [doi:10.1016/0022-2836(90)90136-b](https://doi.org/10.1016/0022-2836(90)90136-b)
- [PMID:7763371](https://pubmed.ncbi.nlm.nih.gov/7763371/) — LaVallie ER et al. (1993) A thioredoxin gene fusion expression system that circumvents inclusion body formation in the *E. coli* cytoplasm. *Biotechnology (N Y).* [doi:10.1038/nbt0293-187](https://doi.org/10.1038/nbt0293-187)
- [PMID:10489448](https://pubmed.ncbi.nlm.nih.gov/10489448/) — Schultz LW, Chivers PT, Raines RT (1999) The CXXC motif: crystal structure of an active-site variant of *E. coli* thioredoxin. *Acta Crystallogr D.* [doi:10.1107/s0907444999010392](https://doi.org/10.1107/s0907444999010392)
- [PMID:10947986](https://pubmed.ncbi.nlm.nih.gov/10947986/) — Lennon BW, Williams CH Jr, Ludwig ML (2000) Twists in catalysis: alternating conformations of *E. coli* thioredoxin reductase. *Science.* [doi:10.1126/science.289.5482.1190](https://doi.org/10.1126/science.289.5482.1190)
- [PMID:11036651](https://pubmed.ncbi.nlm.nih.gov/11036651/) — LaVallie ER et al. (2000) Thioredoxin as a fusion partner for production of soluble recombinant proteins in *E. coli.* *Methods Enzymol.* [doi:10.1016/s0076-6879(00)26063-1](https://doi.org/10.1016/s0076-6879(00)26063-1)
- [PMID:18429194](https://pubmed.ncbi.nlm.nih.gov/18429194/) — McCoy J, LaVallie E (2001) Expression and purification of thioredoxin fusion proteins. *Curr Protoc Protein Sci.* [doi:10.1002/0471140864.ps0607s10](https://doi.org/10.1002/0471140864.ps0607s10)
- [PMID:24600443](https://pubmed.ncbi.nlm.nih.gov/24600443/) — Costa S et al. (2014) Fusion tags for protein solubility, purification and immunogenicity in *E. coli.* *Front Microbiol.* [doi:10.3389/fmicb.2014.00063](https://doi.org/10.3389/fmicb.2014.00063)
- [PMID:34191368](https://pubmed.ncbi.nlm.nih.gov/34191368/) — Schenkel M et al. (2021) Heat treatment of thioredoxin fusions increases the purity of alpha-helical transmembrane protein constructs. *Protein Sci.* [doi:10.1002/pro.4150](https://doi.org/10.1002/pro.4150)
