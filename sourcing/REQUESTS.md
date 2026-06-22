# Source documents needed (human → agent handoff)

When the agent can't access a source it needs, it records the request here and
**stops** — see [`README.md`](README.md). A request is **removed once fulfilled**:
the permanent record is the part's `provenance.sequence_source` citation plus git
history, so this file only ever shows what is *currently* blocked.
`tools/check_requests.py` (run in CI and as a `pre-push` hook) enforces that —
resolved entries can't linger here.

Each active request gives: a link to the resource, **what it would unblock**, the
access barrier, and the **exact filename** to save it as in `sourcing/incoming/`
(gitignored). Use `- [ ]` for an open sub-task.

---

- [ ] **PMID 10882122 / doi:10.1016/s1097-2765(00)80326-3** — Ulp1-SUMO crystal structure and genetic analysis reveal conserved interactions and a regulatory element essential for cell growth in yeast — unblocks: mechanism — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 10882122 --doi 10.1016/s1097-2765(00)80326-3`
- [ ] **PMID 15263846 / doi:10.1023/b:jsfg.0000029237.70316.52** — SUMO fusions and SUMO-specific protease for efficient expression and purification of proteins — unblocks: recognition_specificity; application — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 15263846 --doi 10.1023/b:jsfg.0000029237.70316.52`
- [ ] **PMID 29976752 / doi:10.1074/jbc.ra118.004146** — Discovery and engineering of enhanced SUMO protease enzymes — unblocks: sequence_variant — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 29976752 --doi 10.1074/jbc.ra118.004146`
- [ ] **PMID 31586598 / doi:10.1016/j.pep.2019.105507** — A novel approach for production of an active N-terminally truncated Ulp1 (SUMO protease 1) catalytic domain from Escherichia coli inclusion bodies — unblocks: caveat — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 31586598 --doi 10.1016/j.pep.2019.105507`
- [ ] **PMID 29500346 / doi:10.1038/s41467-018-03191-2** — A peptide tag-specific nanobody enables high-quality labeling for dSTORM imaging — unblocks: application_dstorm, sequence_variant — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 29500346 --doi 10.1038/s41467-018-03191-2`
- [ ] **PMID 25595278 / doi:10.1074/mcp.m114.044016** — Monitoring Interactions and Dynamics of Endogenous Beta-catenin With Intracellular Nanobodies in Living Cells — unblocks: post_translational — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 25595278 --doi 10.1074/mcp.m114.044016`
- [ ] **PMID 35780707 / doi:10.1016/j.chroma.2022.463274** — An engineered peptide tag-specific nanobody for immunoaffinity chromatography application enabling efficient product recovery at mild conditions — unblocks: sequence_variant_44d — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 35780707 --doi 10.1016/j.chroma.2022.463274`
- [ ] **PMID 30988307 / doi:10.1073/pnas.1901876116** — Spy&Go purification of SpyTag-proteins using pseudo-SpyCatcher to access an oligomerization toolbox — unblocks: affinity_matrix — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 30988307 --doi 10.1073/pnas.1901876116`
- [ ] **PMID 26159704 / doi:10.1016/j.jmb.2015.06.018** — A New Versatile Immobilization Tag Based on the Ultra High Affinity and Reversibility of the Calmodulin-Calmodulin Binding Peptide Interaction — unblocks: binding_affinity — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 26159704 --doi 10.1016/j.jmb.2015.06.018`
- [ ] **PMID 10504710 / doi:10.1038/13732** — A generic protein purification method for protein complex characterization and proteome exploration — unblocks: application,host_range — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 10504710 --doi 10.1038/13732`
- [ ] **PMID 9750126 / doi:10.1006/abio.1998.2770** — unblocks: AviTag/host_range — barrier: abstract_only
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 9750126 --doi 10.1006/abio.1998.2770`
- [ ] **PMID 14995162 / doi:10.1021/ja039915e** — unblocks: LPETG_tag/application — barrier: abstract_only
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 14995162 --doi 10.1021/ja039915e`
- [ ] **PMID 30125270 / doi:10.1038/nbt.4201** — unblocks: birA/sequence_variant_turboid — barrier: abstract_only
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 30125270 --doi 10.1038/nbt.4201`
