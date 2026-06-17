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

_No active requests._
