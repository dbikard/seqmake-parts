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

- [ ] **PMID 21697512 / doi:10.1073/pnas.1101046108** — unblocks: LPETG_tag/claim:sequence_variant — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 21697512 --doi 10.1073/pnas.1101046108`
- [ ] **PMID 23989673 / doi:10.1038/nprot.2013.101** — unblocks: LPETG_tag/claim:placement — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 23989673 --doi 10.1038/nprot.2013.101`
- [ ] **PMID 26787909 / doi:10.1073/pnas.1519214113** — unblocks: SnoopTag/claim:mechanism, SnoopTag/claim:performance_yield, SnoopTag/claim:orthogonality, SnoopTag/claim:origin, SnoopTag/claim:application — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 26787909 --doi 10.1073/pnas.1519214113`
- [ ] **PMID 7764094 / doi:10.1038/nbt1093-1138** — Use of peptide libraries to map the substrate specificity of a peptide-modifying enzyme: a 13 residue consensus peptide specifies biotinylation in Escherichia coli — unblocks: mechanism, origin, sequence_variant — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 7764094 --doi 10.1038/nbt1093-1138`
- [ ] **PMID 10211839 / doi:10.1110/ps.8.4.921** — A minimal peptide substrate in biotin holoenzyme synthetase-catalyzed biotinylation — unblocks: mechanism — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 10211839 --doi 10.1110/ps.8.4.921`
- [ ] **PMID 15897449 / doi:10.1073/pnas.0503125102** — Targeting quantum dots to surface proteins in living cells with biotin ligase — unblocks: application, host_range — barrier: not-in-pmc
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 15897449 --doi 10.1073/pnas.0503125102`
- [ ] **PMID 18323822 / doi:10.1038/nprot.2008.20** — Imaging proteins in live mammalian cells with biotin ligase and monovalent streptavidin — unblocks: application — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 18323822 --doi 10.1038/nprot.2008.20`
- [ ] **PMID 25560075 / doi:10.1007/978-1-4939-2272-7_12** — Site-specific biotinylation of purified proteins using BirA — unblocks: placement, expression_yield — barrier: paywall
      full-text not machine-accessible; deposit it: `python tools/papers.py add <pdf> --pmid 25560075 --doi 10.1007/978-1-4939-2272-7_12`
