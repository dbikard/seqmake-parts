# AGENTS.md — contributing with any coding agent

This catalog is **agent-agnostic**. It is plain files (one canonical `parts/<status>/<slug>.json`
per part), a documented SOP, and Python validation gates — so **any** coding agent (Claude Code,
Codex, Cursor, Antigravity, Aider, …) or a human can contribute. CI runs the same gates on every PR,
whoever authored it. Nothing here requires Claude.

## The contract (what makes a contribution valid)

A part's authored source of truth is `parts/<status>/<slug>.json` (validated by
`schema/part.schema.json`); the `.gb`, `catalog.json`, RDF, and the site are **generated** from it.
The full SOP — sourcing, Sequence-Ontology typing, functional claims, the claim model — is
**[`AUTHORING.md`](AUTHORING.md)** (read it before authoring). Hard rules in brief:

- **Sequence from a cited source, never memory.** Source-verify it (independent re-fetch + byte/
  alignment compare) and record `provenance.sequence_source`.
- **Every feature is SO-typed**; every claim `type` is from the controlled vocabulary
  (`schema/claim_types.json`).
- **Claims are sourced + cross-checked.** Each carries `confidence`, `usefulness`, and a verification
  `analysis_status` (`pending` / `verified` / `sources-pending` / `flagged`); a primary full text you
  can't reach → `sources-pending` + a `sourcing/REQUESTS.md` entry (see CLAIM-MODEL.md).

## The gates (agent-agnostic CLIs — run these before opening a PR)

```bash
python tools/validate_parts.py     # schema + SO coverage + claim model/vocab
python tools/build_catalog.py      # regenerate catalog.json / index.json / llms.txt / downloads
python tools/build_rdf.py          # catalog.ttl / catalog.jsonld
pyshacl -s tools/shapes.ttl -i rdfs catalog.ttl
python tools/check_content.py && python tools/check_requests.py && python tools/check_links.py
pytest tests/ -q
```

(`tools/check_all.py` runs the regenerate-and-gate sequence in one shot.) These are exactly what
`.github/workflows/validate.yml` runs in CI — pass them locally and your PR passes.

## Useful tools (plain CLIs, any agent)

- `tools/new_part.py` — scaffold a schema-valid skeleton to author by hand.
- `tools/source_finder.py` — independent re-fetch + compare to source-verify a sequence.
- `tools/papers.py` — local full-text paper store (`add`/`resolve`/`render`/`coverage`/`request`) for
  verifying claims against paywalled PDFs and figures.
- `tools/completeness.py` — datasheet-gap audit (which parts are missing claims their peers have).
- `tools/build_site.py` — regenerate the static site locally.

## Contribution loop

1. Fork + clone (`gh repo fork dbikard/seqmake-parts --clone && cd seqmake-parts`), branch.
2. Author/edit `parts/<status>/<slug>.json` per [`AUTHORING.md`](AUTHORING.md) (and the `.md` prose for
   a validated part). Use the tools above.
3. Run the gates. Commit the JSON **and** the regenerated artifacts.
4. Open a PR.

## Claude Code shortcut (optional)

If you happen to use **Claude Code**, this repo ships turnkey packaging that automates the above:
the `/add-part` command drives a verified source→research→annotate→verify→merge **workflow**
(`.claude/workflows/annotate-part.js`), plus `/cross-check`, `/incoming`, `/open-requests`. These run
on Claude Code's Workflow runtime and are **not** portable to other agents — but they produce ordinary
PRs that pass the same gates above, so they are a convenience, not a requirement. Other agents follow
the SOP directly; the bar is identical.
