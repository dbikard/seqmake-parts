---
description: Process files the human dropped into sourcing/incoming/ — deposit paper PDFs into the local paper store (clearing their REQUESTS.md entries) and route sequence files to the add-part Source phase. Then offer to re-verify the now-unblocked claims.
argument-hint: (none — acts on whatever is in sourcing/incoming/)
allowed-tools: Bash, Read, WebFetch, WebSearch, Workflow
---

The human has added one or more files to `sourcing/incoming/` (gitignored) — typically
**paywalled paper PDFs** they fetched to unblock a cited claim, sometimes **sequence
records** for a part. Your job: file each one correctly, clear what it satisfies, and
report what is now verifiable. See @sourcing/README.md for the handoff contract and
`tools/papers.py` for the paper store.

## Procedure

1. **List the drop folder.** `ls -la sourcing/incoming/`. Split into:
   - **Papers** — `*.pdf`. These go into the local paper store.
   - **Sequence records** — `*.gb` / `*.fasta` / `*.fa` / `*.txt` / `*.seq`. These feed the
     **add-part Source phase**, NOT the paper store.

2. **For each PDF — identify its PMID/DOI, then deposit it.**
   - First check what's wanted: `python tools/papers.py requests` lists the active requested
     papers with their PMIDs/DOIs and what each unblocks. The PDF the human fetched almost
     always matches one of these.
   - Identify the paper, in this order of effort:
     - **Filename hints** — e.g. `science.285.5428.760.pdf` → `doi:10.1126/science.285.5428.760`;
       an `author-year-title` filename → a title search.
     - **Match against the request list** above (PMID/DOI).
     - If still unsure, **Read the PDF's first page** (`Read` with `pages: "1"`) for the title /
       DOI / PMID, and confirm via PubMed (ToolSearch the PubMed tools) or by `WebFetch`-ing the DOI.
   - **Cross-check the identifier against a cited reference in the catalog** (grep `parts/*/*.json`
     for the PMID/DOI) so you attach the identifier the claims actually use — not a variant.
   - **Deposit:** `python tools/papers.py add "sourcing/incoming/<file>.pdf" --pmid <pmid> --doi <doi> --title "<title>" --move`.
     This copies + checksums + text-extracts + indexes the PDF, **auto-clears the matching
     `sourcing/REQUESTS.md` entry** (store-aware), and — with `--move` — **deletes the now-redundant
     source from `incoming/`** once it's safely stored. For a figure-bearing claim, the verifier can
     later `python tools/papers.py render --pmid <pmid> --pages <n>` to inspect the figure.
   - **Never guess** a PMID/DOI. If you cannot confidently identify a PDF, leave it, list it,
     and ask the human which paper it is.

3. **For each sequence record** (`.gb`/`.fasta`/…): it establishes/verifies a part's *sequence*,
   which the **add-part Source phase** handles (byte/alignment compare via `tools/source_finder.py`).
   Identify which part it's for if you can (filename/accession ↔ a part slug), and tell the human to
   re-run `/add-part <part>` so the engine verifies + cites it. Leave the file in `incoming/`.

4. **Report + offer to re-verify.** Summarise: which papers were deposited, which claims/parts they
   unblock (`python tools/papers.py coverage`), and which requests cleared. Then **offer** (don't
   auto-run — it spends tokens) to re-verify the now-unblocked claims now that their full text is
   local: run the **`cross-check`** workflow on the affected parts (the verifier reads the store
   first), or re-run `/add-part <part>` so the claim-evidence honesty gate re-sources them at proper
   confidence.

## Notes
- The paper store (`sourcing/papers/`) is **gitignored** — full-text PDFs stay local; only the
  citation + the part record are ever committed.
- `papers.py add --move` **removes the PDF from `incoming/`** after it's safely in the store, so the
  drop folder always reflects what's still unprocessed. (Only PDFs are moved — **never** delete a
  sequence file; the human may still need it for an add-part re-run.)
- Closes the loop with `/open-requests` (which opens requested papers in the browser to fetch).
