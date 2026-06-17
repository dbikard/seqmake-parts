# `tools/archive/` — retired tools

One-time migration scripts that have served their purpose. They are kept for
reference (and in case a future part needs the same conversion), but are **not**
part of the active pipeline — nothing in CI, the hooks, the tests, or the
`/add-part` workflow calls them.

- **`migrate_to_json.py`** — the one-time migration that generated the canonical
  `<slug>.json` for every part from its legacy `.gb`. The catalog is now
  JSON-canonical (`build_gb.py` regenerates the `.gb` *from* the JSON), so this is
  done.
- **`migrate_to_protein.py`** — converted a DNA coding part to a protein-canonical
  record (translation becomes the sequence; sub-features remapped bp→aa). New
  coding parts are authored protein-canonical directly (see `AUTHORING.md`).
