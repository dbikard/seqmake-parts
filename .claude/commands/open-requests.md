---
description: Open every requested (paywalled) paper in the browser so the human can manually download the PDFs, then drop them in sourcing/incoming/ and run /incoming.
argument-hint: [--all] (include every claim-cited paper not yet in the store, not just REQUESTS.md)
allowed-tools: Bash
---

The human wants to fetch the papers the catalog still needs — claims whose primary full text
isn't in the local store (see `tools/papers.py` and @sourcing/README.md). Open each one in their
browser so they can download the PDF.

## Procedure

1. **Get the list of fetch URLs.**
   - Default (the curated requests in `sourcing/REQUESTS.md`):
     `python tools/papers.py requests --urls`
   - If the human passed `--all`, broaden to **every paper a functional_claim cites that we don't
     yet hold**: `python tools/papers.py requests --urls --all`
   - For a human-readable view of what each unblocks, run `python tools/papers.py requests` (no `--urls`).
   - Each URL is a DOI link (`https://doi.org/…`, resolves to the publisher's article/PDF page) or,
     for a PMID-only paper, a PubMed link.

2. **Report first.** Tell the human how many papers will open (and list them with what each unblocks).
   If there are **more than ~8**, confirm before opening to avoid flooding their browser with tabs.

3. **Open each URL in the browser.** This is WSL2 — try these openers in order until one works, per URL:
   ```bash
   wslview "<url>"                                            # wslu, if installed
   cmd.exe /c start "" "<url>"                                # Windows default browser
   powershell.exe -NoProfile -Command "Start-Process '<url>'"
   xdg-open "<url>"                                           # native Linux, if a browser is set
   ```
   A reasonable loop:
   ```bash
   open_url() { wslview "$1" 2>/dev/null || cmd.exe /c start "" "$1" 2>/dev/null \
     || powershell.exe -NoProfile -Command "Start-Process '$1'" 2>/dev/null || xdg-open "$1" 2>/dev/null; }
   python tools/papers.py requests --urls | while read -r u; do open_url "$u"; done
   ```

4. **If no opener works** (headless / no Windows shell), just print the URLs as a clean clickable list
   for the human to open manually — don't fail silently.

5. **Tell the human the next step:** download each PDF, drop the files into `sourcing/incoming/`, then
   run **`/incoming`** — it deposits them into the paper store and clears their requests automatically.

## Notes
- Read-only except for opening browser tabs. Doesn't touch the catalog.
- DOI links land on the article page (where the PDF download lives); some are open-access and download
  directly, others need the human's institutional access — that's exactly why this is a manual step.
