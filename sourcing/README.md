# `sourcing/` — human ↔ agent source-document handoff

When `/add-part` (or the future annotate workflow) **can't access a source** it
needs — a paywalled paper, a login-gated registry/repository, a `403`/`405` to
automated fetch — it does **not** guess or recall a sequence from memory. Instead it
writes what it needs to [`REQUESTS.md`](REQUESTS.md) and **stops**. A human fetches
those documents and drops them into `incoming/`; on the next pass the agent reads
`incoming/`, byte-verifies the sequence against the provided document, and cites that
document in the part's `provenance.sequence_source`.

This turns "couldn't access" into a **first-class, resumable state** instead of a
dead end. The sourcing hard rule lives in [`AUTHORING.md`](../AUTHORING.md) (a
sequence comes from a cited source, never memory; an access-blocked source is
recorded here and the part stops).

Two kinds of request belong here:

- **Sequence sources** — a deposited record / paper that establishes a part's
  sequence (the part stops until it's byte-verifiable).
- **Boundary evidence** — a paper carrying **experimental** data that defines a
  feature's extent (mutational scanning, progressive truncation, genetics). Part
  boundaries should not be (re)delimited on sequence/consensus alone (see
  `AUTHORING.md`); when such a paper is identified but inaccessible, request it here so
  a boundary can be set on evidence rather than guessed — meanwhile keep the boundary
  provisional with a lower-confidence note.

## Layout

- **`REQUESTS.md`** — agent-written list of needed resources: each item has a link,
  what it would unblock, the access barrier, and the **exact filename** to save it
  as. Tracked in git, so the outstanding ask is visible and auditable. It lists
  **active requests only** — a fulfilled request is removed (the part's
  `provenance.sequence_source` citation + git history are the permanent record);
  `tools/check_requests.py` enforces this in CI and the `pre-push` hook.
- **`incoming/`** — drop folder for the provided documents. **Gitignored** — external
  PDFs and sequences stay local and are never committed; only the resulting part
  record and its provenance citation go into the repo.
- **`papers/`** — local **full-text paper store** for verification/cross-check, managed by
  [`tools/papers.py`](../tools/papers.py). **Gitignored** (a personal reference cache; copyrighted
  full text is never committed). Keyed by the PMID/DOI that every `functional_claims[].source`
  and `references[]` already carries, so it answers "do we hold the paper this claim cites?".

## Full-text paper store (`papers/`)

Public APIs usually expose only an **abstract**; the cross-check verifier then can't confirm
claims whose evidence is in the full text or a **figure/table**. Deposit the PDF once and the
verifier reads the real thing — including *looking at* cited figures, not just their captions.

```bash
python tools/papers.py add ~/Downloads/Bertrand1983.pdf --pmid 6311683 --doi 10.1016/0378-1119(83)90046-x
python tools/papers.py coverage          # which cited papers we have vs. still need (priority = cited by a claim)
python tools/papers.py resolve --json --pmid 6311683    # agent: locate full text
python tools/papers.py render --pmid 6311683 --pages 3  # agent: render a page to PNG to inspect a figure
```

The cross-check engine (`.claude/workflows/cross-check.js` / the `cross-check` skill) checks this
store **first**; `coverage` produces the deposit worklist — the natural place to surface a paywall
is the same `REQUESTS.md` handoff above.

## How to use it (human)

1. Open `REQUESTS.md`, fetch the listed documents.
2. Save each into `sourcing/incoming/` using the suggested filename.
3. Tell the agent to resume (or re-run `/add-part <name>`). It will pick the files
   up from `incoming/`, verify, and continue.

A raw sequence is fine too: paste it into a `.txt`/`.fasta`/`.gb` in `incoming/` and
note which request it satisfies.
