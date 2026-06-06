# Contributing a part

Thank you for helping grow the catalog! Adding a part is intentionally
low-friction: one GenBank file, optionally a documentation page.

## Add a part

1. Add `parts/<Name>.gb` — an annotated GenBank file with:
   - exactly **one main feature** spanning the whole sequence, carrying
     `/label="<Name>"` (this is the part's canonical name) and no `/parent`;
   - optional **sub-features**, each with `/parent="<Name>"` and a `/label`
     (e.g. `-35`, `-10`, an operator, an RBS), in part-relative coordinates;
   - optional `REFERENCE` blocks with `PUBMED` / `doi:` and per-feature
     `/citation=[N]` linking a feature to reference *N*.
2. Optionally add `parts/<Name>.md` — a short documentation page
   (recommended sections: **Origin**, **Properties**, **Use**, **References**).
   Parts with a `.md` are marked `documented` and get a richer website page.
3. Open a pull request. CI loads every `.gb` and rebuilds `catalog.json`; your
   PR must keep `catalog.json` up to date.

## Regenerate locally

```bash
pip install -r requirements.txt
python tools/build_catalog.py     # rebuilds catalog.json + docs/
mkdocs serve                      # preview the site at http://127.0.0.1:8000
```

Commit the updated `catalog.json` along with your part. The `docs/` tree is
generated (git-ignored) and rebuilt by CI.

## `catalog.json` schema (v1.0)

```jsonc
{
  "schema_version": "1.0",
  "n_parts": 211,
  "n_documented": 16,
  "parts": [
    {
      "name": "PphlF", "slug": "PphlF",
      "feature_type": "promoter", "synonyms": ["PhlF promoter"],
      "description": "…", "length": 51, "documented": true,
      "children": [
        {"label": "-35", "feature_type": "regulatory",
         "start": 16, "end": 22, "strand": 1, "citations": [1]}
      ],
      "references": [
        {"authors": "…", "title": "…", "journal": "…",
         "pmid": "24316737", "doi": "10.1038/…", "url": "https://pubmed…/"}
      ],
      "main_citations": [1, 2]
    }
  ]
}
```

`start`/`end` are 0-based, end-exclusive, part-relative. `citations` /
`main_citations` are 1-based indices into that part's `references`.

## Scope & licensing

Keep parts **lab-agnostic** and generally useful. By contributing you agree to
release your contribution under **CC BY 4.0** (the catalog's license). Only
contribute sequences/annotations you have the right to share.
