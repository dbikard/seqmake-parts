# Stable namespace — `w3id.org/bioparts`

The catalog's RDF IRIs use the permanent base **`https://w3id.org/bioparts/`**
instead of the GitHub Pages URL, so they survive a change of host or repo name.
[`bioparts/.htaccess`](bioparts/.htaccess) is the redirect that makes them
resolve; it forwards to the current site (`dbikard.github.io/dna-parts-catalog`).

## How IRIs resolve

| IRI | Redirects to |
|---|---|
| `https://w3id.org/bioparts/` | the site home |
| `https://w3id.org/bioparts/part/<slug>` | that part's page (`/parts/<slug>/`) |
| `https://w3id.org/bioparts/collection/<id>` | that collection's page |
| `https://w3id.org/bioparts/ns#<term>` | `catalog.ttl` (the graph defining `cat:` terms) |
| `https://w3id.org/bioparts/catalog.ttl` (`.jsonld`/`.json`) | the published artifact |

## Registering / updating the redirect

w3id.org is a community service; the redirect lives in the
[`perma-id/w3id.org`](https://github.com/perma-id/w3id.org) repo, one directory
per namespace.

1. Fork `perma-id/w3id.org`.
2. Copy this repo's `w3id/bioparts/` directory to `bioparts/` at the root of the
   fork (so the file lands at `bioparts/.htaccess`).
3. Open a PR. Once merged, `https://w3id.org/bioparts/…` is live.

To change where the IRIs point later (new host, renamed repo), edit only
`bioparts/.htaccess` and open another PR — no IRIs change.

> Keep this directory as the source of truth and copy it into the w3id PR, rather
> than editing the fork directly, so the redirect is version-controlled alongside
> the data it serves.
