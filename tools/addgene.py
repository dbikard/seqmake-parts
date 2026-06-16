#!/usr/bin/env python3
"""Search and fetch plasmids from the Addgene Developers API.

A standalone sourcing helper for authoring parts (see AUTHORING.md): find a
plasmid that carries a sequence you need, fetch its annotated GenBank, and
extract the part region from it — recording the Addgene id in the part's
``provenance.sequence_source``.

The catalog API is **not keyless** — it needs a Developers API token. Set it in
the environment as ``ADDGENE_TOKEN``; without it the tool exits with a clear
message. Request a token (Catalog scope) at https://www.addgene.org/developers/.

Usage::

    python tools/addgene.py search "pET28a" [--genes Cas9] [--promoters T7] \\
        [--vector-types CRISPR] [--expression "Bacterial Expression"] \\
        [--bacterial-resistance Kanamycin] [--species "..."] [--max 10]

    python tools/addgene.py fetch 39312 [--out <file.gb>]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import urlsplit

API_BASE = "https://api.developers.addgene.org"
API_HOST = urlsplit(API_BASE).hostname
TIMEOUT = 20
# Cloudflare fronts the API and bans the default Python User-Agent (HTTP 403,
# "error code: 1010"); send an explicit one.
HEADERS = {"User-Agent": "dna-parts-catalog/1.0 (+https://github.com/dbikard/dna-parts-catalog)"}


def _token() -> str:
    tok = os.environ.get("ADDGENE_TOKEN", "").strip()
    if not tok:
        sys.exit(
            "No Addgene token. Set ADDGENE_TOKEN (Catalog scope) in your "
            "environment — request one at https://www.addgene.org/developers/."
        )
    return tok


def _get(url: str, token: str, params: dict | None = None):
    import requests  # lazy: only the Addgene tool needs it

    # Only ever send the bearer token to the Addgene API host itself. URLs taken
    # from a response body (e.g. a plasmid's genbank_url) could point off-host;
    # sending the token there would leak it to a third party.
    headers = dict(HEADERS)
    if urlsplit(url).hostname == API_HOST:
        headers["Authorization"] = f"Token {token}"
    try:
        r = requests.get(
            url, params=params,
            headers=headers,
            timeout=TIMEOUT,
        )
    except requests.exceptions.Timeout:
        sys.exit("Addgene request timed out.")
    except requests.exceptions.ConnectionError:
        sys.exit("Network error reaching Addgene.")
    if r.status_code in (401, 403):
        sys.exit(f"Addgene rejected the request (HTTP {r.status_code}); "
                 "check the token is valid and has the Catalog scope.")
    if r.status_code == 404:
        sys.exit("Addgene: not found (HTTP 404).")
    if r.status_code != 200:
        sys.exit(f"Addgene returned HTTP {r.status_code}.")
    return r


def cmd_search(a) -> None:
    token = _token()
    filters = {k: v for k, v in {
        "name": a.query, "genes": a.genes, "vector_types": a.vector_types,
        "expression": a.expression, "bacterial_resistance": a.bacterial_resistance,
        "promoters": a.promoters, "species": a.species,
    }.items() if v}
    if not filters:
        sys.exit("Give a query or at least one filter (--genes, --promoters, ...).")
    page = min(max(a.max, 1), 50)
    data = _get(f"{API_BASE}/catalog/plasmid/", token,
                params={**filters, "page_size": page, "sort_by": "newest"}).json()
    hits = []
    for x in data.get("results", []):
        pid = x.get("id")
        hits.append({
            "id": pid, "name": x.get("name", ""),
            "url": f"https://www.addgene.org/{pid}/" if pid else "",
            "genes": x.get("genes") or [], "vector_types": x.get("vector_types") or [],
            "promoters": x.get("promoters") or [], "expression": x.get("expression") or [],
            "depositor": x.get("depositor") or [], "article": x.get("article") or [],
            "purpose": x.get("purpose") or "",
        })
    json.dump({"filters": filters, "total_count": data.get("count", 0),
               "showing": len(hits), "hits": hits}, sys.stdout, indent=2)
    print()


def cmd_fetch(a) -> None:
    token = _token()
    try:
        pid = int(a.id)
    except ValueError:
        sys.exit(f"Invalid Addgene id: {a.id!r}")
    data = _get(f"{API_BASE}/catalog/plasmid-with-sequences/{pid}/", token).json()
    seqs = data.get("sequences") or {}
    entry = None
    for bucket in ("public_addgene_full_sequences", "public_user_full_sequences"):
        items = seqs.get(bucket) or []
        if items:
            entry = items[0]
            break
    if not entry or not entry.get("genbank_url"):
        sys.exit(f"Addgene {pid} has no downloadable full sequence "
                 "(only partial sequences, or none, are public).")
    gb_text = _get(entry["genbank_url"], token).text
    out = a.out or f"addgene_{pid}.gb"
    with open(out, "w", encoding="utf-8") as f:
        f.write(gb_text)
    from io import StringIO

    from Bio import SeqIO  # already a catalog dependency
    rec = SeqIO.read(StringIO(gb_text), "genbank")
    topo = (rec.annotations.get("topology") or "circular").lower()
    json.dump({
        "id": pid, "name": data.get("name") or f"addgene_{pid}",
        "url": f"https://www.addgene.org/{pid}/",
        "length": len(rec.seq), "topology": topo, "n_features": len(rec.features),
        "saved_to": out,
        "provenance_hint": f"Addgene {pid} ({entry.get('name', 'full sequence')})",
    }, sys.stdout, indent=2)
    print()


def main() -> None:
    p = argparse.ArgumentParser(
        description="Search/fetch plasmids from the Addgene catalog (needs ADDGENE_TOKEN).")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="search the Addgene catalog")
    s.add_argument("query", nargs="?", default="", help="free-text plasmid-name match")
    s.add_argument("--genes", default="")
    s.add_argument("--vector-types", dest="vector_types", default="")
    s.add_argument("--expression", default="")
    s.add_argument("--bacterial-resistance", dest="bacterial_resistance", default="")
    s.add_argument("--promoters", default="")
    s.add_argument("--species", default="")
    s.add_argument("--max", type=int, default=10)
    s.set_defaults(func=cmd_search)

    f = sub.add_parser("fetch", help="fetch a plasmid's annotated GenBank by Addgene id")
    f.add_argument("id")
    f.add_argument("--out", default="", help="output .gb path (default addgene_<id>.gb)")
    f.set_defaults(func=cmd_fetch)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
