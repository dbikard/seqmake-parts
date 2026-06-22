# Redesign build — STATUS: full-page detail DONE (2026-06-22)

The drawer→full-page-detail conversion and the new-model verification copy are **implemented and
verified** in `index.html` + `build_index.py`. See PROPOSAL.md §3E and §6 for the current design.

## What was done
- **build_index.py** now emits per-part `claims` (full, with source + confidence/usefulness axes),
  `refs`, and `mol` (`build_molecule_json` → the widget's `MoleculeInfo`). `data.js` = 663 KB / 264 parts.
- **index.html**: drawer removed → full-page `#detail` (catalog wrapper got `id="catalog"`). `openPart()`
  renders header/meta + the **embedded `seqmake-part-view` widget** + full claims (confidence/usefulness/
  cross-checked badges, source quote+link) + references + downloads. Hash routing `#part=<slug>`
  (pushState/popstate, deep-link, Back). Widget hydration via `window.SeqmakePartView.init()` (classic
  IIFE global; bundle re-load fallback). Verification copy reworked to the new model (no `expert-reviewed`).

## Verified (no browser available here)
- Inline script `node --check` clean; source uses escaped `<\/script>` (0 raw breakouts); embedded
  `MoleculeInfo` round-trips. Fake-DOM harness: opening MBP renders the detail view, widget mount,
  claim cards + confidence badge, references, hidden catalog, `init()` called, and `#part=` routing.

## Remaining
- **Real-browser visual pass** (light/dark, mobile rail collapse, the live widget rendering) — couldn't
  run headless.
- **Production**: emit static `parts/<slug>/index.html` per part in this design to preserve the live
  w3id IRIs + agent-layer URLs (PROPOSAL §6, step 3) — the prototype's `#part=` route is in-page nav only.
