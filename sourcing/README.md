# `sourcing/` — human ↔ agent source-document handoff

When `/add-part` (or the future annotate workflow) **can't access a source** it
needs — a paywalled paper, a login-gated registry/repository, a `403`/`405` to
automated fetch — it does **not** guess or recall a sequence from memory. Instead it
writes what it needs to [`REQUESTS.md`](REQUESTS.md) and **stops**. A human fetches
those documents and drops them into `incoming/`; on the next pass the agent reads
`incoming/`, byte-verifies the sequence against the provided document, and cites that
document in the part's `provenance.sequence_source`.

This turns "couldn't access" into a **first-class, resumable state** instead of a
dead end. See `proposals/unified-add-part.md` → *Unresolved sources → a human second
pass*.

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
  as. Tracked in git, so the outstanding ask is visible and auditable.
- **`incoming/`** — drop folder for the provided documents. **Gitignored** — external
  PDFs and sequences stay local and are never committed; only the resulting part
  record and its provenance citation go into the repo.

## How to use it (human)

1. Open `REQUESTS.md`, fetch the listed documents.
2. Save each into `sourcing/incoming/` using the suggested filename.
3. Tell the agent to resume (or re-run `/add-part <name>`). It will pick the files
   up from `incoming/`, verify, and continue.

A raw sequence is fine too: paste it into a `.txt`/`.fasta`/`.gb` in `incoming/` and
note which request it satisfies.
