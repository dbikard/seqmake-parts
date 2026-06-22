---
description: Process files the human dropped into sourcing/incoming/ — deposit paper PDFs into the local paper store (clearing their REQUESTS.md entries), and route sequence files by ROLE (a carrier map → byte-verify an existing part; a bare standalone sequence → /add-part). Then offer to re-verify the now-unblocked claims.
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
   - **Papers** — `*.pdf`. These go into the local paper store (step 2).
   - **Sequence records** — `*.dna` (SnapGene) / `*.gb` / `*.gbk` / `*.fasta` / `*.fa` /
     `*.txt` / `*.seq`. These are routed by **role** (step 3), not by extension.

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

3. **For each sequence record — classify by ROLE first, then route.** A dropped sequence plays one
   of two roles; do NOT guess from the extension. Run:
   ```bash
   python tools/sequences.py classify "sourcing/incoming/<file>"
   ```
   which reads `.dna`/`.gb`/`.gbk`/`.fasta`/`.txt` and reports `role: carrier | standalone`.

   - **`carrier`** — an annotated multi-feature map or a circular plasmid that *contains* a part as a
     sub-region (e.g. `pDONR221` carrying `Gateway_attP1`/`attP2`). It is dropped to **byte-verify an
     EXISTING part** — **never `/add-part` the carrier itself**.
     1. **Deposit it** so the Source phase can read it (it is gitignored, stays local):
        ```bash
        python tools/sequences.py add "sourcing/incoming/<file>" --name <carrierName> [--accession <acc>] --move
        ```
        (If the carrier IS a public NCBI accession, you don't need to store it — it is re-fetchable;
        cite the accession instead. The store is for **non-refetchable** commercial/unpublished maps.)
     2. **Locate + byte-verify** each target part within it:
        ```bash
        python tools/source_finder.py --slug <part> --carrier-name <carrierName>   # or --carrier <path>
        ```
        This prints `carrier_source` with the match span and a ready `sequence_source` string (e.g.
        `"pDONR221 positions 1-232 (+ strand)"`) and `verified: true` on a full-length exact match. If
        the part is a **truncated sub-region** of a larger annotated element in the carrier (coverage <
        the carrier feature), that is the canonical *redelimit-up* signal — flag it for a curation call,
        don't silently re-cut.
     3. Tell the human to re-run `/add-part <part>` (or do it) so the engine records that
        `provenance.sequence_source`. Do not delete a carrier the human may still need.

   - **`standalone`** — a bare sequence (typically a featureless FASTA) meant to **BE a new part**.
     Identify the intended slug (filename) and run `/add-part <slug>`; the Source phase verifies + cites
     it. Leave the file in `incoming/`.

4. **Report + offer to re-verify.** Summarise: which papers were deposited, which claims/parts they
   unblock (`python tools/papers.py coverage`), and which requests cleared. Then **offer** (don't
   auto-run — it spends tokens) to re-verify the now-unblocked claims now that their full text is
   local: run the **`cross-check`** workflow on the affected parts (the verifier reads the store
   first), or re-run `/add-part <part>` so the claim-evidence honesty gate re-sources them at proper
   confidence.

## Notes
- Both stores are **gitignored**: `sourcing/papers/` (full-text PDFs, keyed by PMID/DOI) and
  `sourcing/sequences/` (non-refetchable carrier maps, keyed by name/accession). Only the citation /
  `provenance.sequence_source` string + the part record are ever committed — never the source files.
- `--move` (on both `papers.py add` and `sequences.py add`) removes the source from `incoming/` once it's
  safely stored, so the drop folder always reflects what's still unprocessed. A carrier the human may
  still need for an add-part re-run is preserved in the store, not deleted outright.
- `papers/` = **claim evidence** (does the paper support this claim?); `sequences/` = **sequence
  provenance** (does this carrier contain this part, byte-for-byte?). Same handoff, two axes.
- Closes the loop with `/open-requests` (which opens requested papers in the browser to fetch).
