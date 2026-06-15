# Source documents needed (human → agent handoff)

The agent stops here when it can't access a source. Save each file below into
`sourcing/incoming/` with the **suggested filename**, then tell the agent to resume
— it re-reads `incoming/`, byte-verifies, and cites the provided document in the
part's `provenance.sequence_source`. `sourcing/incoming/` is gitignored, so provided
PDFs/sequences stay local. See [`README.md`](README.md).

---

## ✅ Resolved — cumate-inducible promoter (PCymRC) · opened+closed 2026-06-15

Unblocked by the human providing an Addgene Developers API token (`ADDGENE_TOKEN`)
plus `tools/addgene.py` — so no documents needed to be dropped in `incoming/`.
Fetched Addgene pAJM.712 (#108513), extracted the PCymRC promoter (bases 2835–2921),
**byte-verified** the 86-bp sequence against the deposited GenBank, and authored
`parts/candidate/PCymRC.json` (CuO_1 · −35 · −10 · CuO_2; refs Meyer 2018 + Eaton
1997). Still paywalled (a low-confidence claim flags it): a **PCymRC-specific
induction fold-change** — would be unblocked by the Meyer 2018 Supplementary
Information (`Nat Chem Biol`, PMID 30478458).
