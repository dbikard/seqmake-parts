# Stable namespace — `w3id.org/seqmake/parts`

The catalog's RDF IRIs use the permanent base **`https://w3id.org/seqmake/parts/`**
— the parts dataset under the **SeqMake** house brand — instead of the GitHub
Pages URL, so they survive a change of host or repo name.
[`seqmake/.htaccess`](seqmake/.htaccess) is the redirect that makes them resolve;
it forwards to the current site (`dbikard.github.io/dna-parts-catalog`).

## How IRIs resolve

| IRI | Redirects to |
|---|---|
| `https://w3id.org/seqmake/parts/` | the site home |
| `https://w3id.org/seqmake/parts/part/<slug>` | that part's page (`/parts/<slug>/`) |
| `https://w3id.org/seqmake/parts/collection/<id>` | that collection's page |
| `https://w3id.org/seqmake/parts/ns#<term>` | `catalog.ttl` (the graph defining `cat:` terms) |
| `https://w3id.org/seqmake/parts/catalog.ttl` (`.jsonld`/`.json`) | the published artifact |

## Registering / updating the redirect

w3id.org is a community service; the redirect lives in the
[`perma-id/w3id.org`](https://github.com/perma-id/w3id.org) repo, one directory
per namespace prefix. We register the **`seqmake/`** prefix once; the
`.htaccess` routes the `parts/…` paths (and leaves room for other SeqMake
datasets under the same prefix later).

1. Fork `perma-id/w3id.org`.
2. Copy this repo's `w3id/seqmake/` directory to `seqmake/` at the root of the
   fork (so the file lands at `seqmake/.htaccess`).
3. Open a PR. Once merged, `https://w3id.org/seqmake/parts/…` is live.

To change where the IRIs point later (new host, renamed repo), edit only
`seqmake/.htaccess` and open another PR — no IRIs change.

> Keep this directory as the source of truth and copy it into the w3id PR, rather
> than editing the fork directly, so the redirect is version-controlled alongside
> the data it serves.
