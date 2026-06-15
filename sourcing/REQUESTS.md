# Source documents needed (human → agent handoff)

The agent stops here when it can't access a source. Save each file below into
`sourcing/incoming/` with the **suggested filename**, then tell the agent to resume
— it re-reads `incoming/`, byte-verifies, and cites the provided document in the
part's `provenance.sequence_source`. `sourcing/incoming/` is gitignored, so provided
PDFs/sequences stay local. See [`README.md`](README.md).

---

## Pending — cumate-inducible promoter (Pcym / PCymRC) · opened 2026-06-15

**Need:** a verbatim, coordinate-defined sequence for an *E. coli* cumate-inducible
promoter, with its −35, −10, and CuO operator. Any **one** of the following unblocks
it (the first is the cleanest).

- [ ] **Marionette `PCymRC` construct — Addgene pAJM.712 (#108513)**
  - https://www.addgene.org/108513/sequences/  (full GenBank / "Addgene full" map)
  - barrier: **login-gated**; the dev-API endpoint is undocumented to the agent
  - → save as **`sourcing/incoming/pAJM712_108513.gb`**
- [ ] **OR — Marionette paper Supplementary Information** (sensor promoter sequence tables)
  - Meyer et al. 2018, *Nat Chem Biol* 15(2):196–204 · PMID 30478458 · doi:10.1038/s41589-018-0168-3
  - barrier: **paywalled, no PMC copy**
  - → save as **`sourcing/incoming/Meyer2018_marionette_SI.pdf`**
- [ ] **OR — iGEM T5 + cumate-operator promoter part**
  - BBa_K875001: https://parts.igem.org/Part:BBa_K875001
  - barrier: registry returns **403** to automated fetch
  - → paste its DNA sequence (+ any −35/−10/CuO annotation) into **`sourcing/incoming/BBa_K875001.txt`**

**Also helpful (not required to source *this* part):**

- [ ] **Addgene dev-API spec** so the agent can fetch directly with `ADDGENE_TOKEN`
  next time — the exact base URL + auth header format (or a single working `curl`).
  - https://docs.developers.addgene.org  (JS-rendered; the agent can't read it)
  - → save as **`sourcing/incoming/addgene_api.md`** (a working curl example is plenty)

_Already obtained (no action needed): the CuO operator consensus
`AACAAACAGACAATCTGGTCTGTTTGTA`, the −35/−10 consensus, and the citations above._
