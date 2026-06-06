## Part(s) added / changed

<!-- name(s) and a one-line description -->

## Checklist

- [ ] `<Name>.gb` has one main feature (`/label`, no `/parent`) + optional
      `/parent`-tagged sub-features, in part-relative coordinates.
- [ ] References use `PUBMED` / `doi:` with per-feature `/citation=[N]` where applicable.
- [ ] Candidate part in `parts/candidate/<Name>.gb` (no `.md`), **or** validated
      part in `parts/validated/<Name>.gb` **with** a `parts/validated/<Name>.md`
      page (Origin / Properties / Use / References).
- [ ] Ran `python tools/build_catalog.py` and committed the updated `catalog.json`.
- [ ] Content is lab-agnostic and I have the right to release it under **CC BY 4.0**.
