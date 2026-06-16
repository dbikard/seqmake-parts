#!/usr/bin/env python3
"""Find a 100%-identity, deposited GenBank source for a DNA part via NCBI BLAST.

Submits a part's sequence to NCBI's BLAST URL API (megablast vs ``nt``), waits for
the queued job, and reports **full-length 100%-identity** hits with each hit's
accession, GenBank definition and deposit date — so a curator can record the oldest
reputable deposited record (a plasmid, ideally) as ``provenance.sequence_source``.

Picking the *oldest reputable* source among perfect hits is a human call; this tool
only surfaces and dates the candidates. Only meaningful for **DNA** parts — a protein
part's source is its UniProt/NCBI accession, not a nucleotide BLAST.

NCBI etiquette: one submit, then poll politely (this waits >=20 s between polls and
never resubmits). Needs ``requests`` (a catalog dependency).

Usage::

    python tools/blast.py --slug ColE1
    python tools/blast.py --seq ACGT...
    python tools/blast.py --rid <RID>          # re-fetch a finished/known job
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLAST = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
HEADERS = {"User-Agent": "dna-parts-catalog/1.0 (+https://github.com/dbikard/dna-parts-catalog)"}

# NCBI E-utilities etiquette: identify the client with tool/email and, if set,
# an API key (raises the rate limit from 3 to 10 req/s). Configure via the
# NCBI_EMAIL / NCBI_API_KEY env vars. https://www.ncbi.nlm.nih.gov/books/NBK25497/
TOOL = "dna-parts-catalog"
EMAIL = os.environ.get("NCBI_EMAIL", "")
API_KEY = os.environ.get("NCBI_API_KEY", "")
NCBI_DELAY = 0.11 if API_KEY else 0.34   # stay under the per-second limit


def _ncbi(params: dict) -> dict:
    """Add NCBI etiquette params (tool/email, optional api_key) to an E-utilities call."""
    p = {**params, "tool": TOOL}
    if EMAIL:
        p["email"] = EMAIL
    if API_KEY:
        p["api_key"] = API_KEY
    return p


def _request(method: str, url: str, *, fatal: bool = True, **kw):
    """An NCBI HTTP call with the shared User-Agent, retry/backoff on transient
    failures (429/5xx + network errors) and raise_for_status. Returns the
    response, or None when ``fatal=False`` and every attempt failed."""
    import requests
    last = None
    for attempt in range(4):
        try:
            r = requests.request(method, url, headers=HEADERS, **kw)
            if r.status_code in (429, 500, 502, 503, 504):
                last = f"HTTP {r.status_code}"
                time.sleep(2 ** attempt)
                continue
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(2 ** attempt)
    if fatal:
        sys.exit(f"NCBI request failed after retries: {url} ({last})")
    return None


def _seq_for(slug: str) -> str:
    for sub in ("validated", "candidate"):
        p = ROOT / "parts" / sub / f"{slug}.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))["sequence"].upper()
    sys.exit(f"part {slug!r} not found under parts/")


def submit(seq: str, entrez: str = "") -> tuple[str, int]:
    data = {"CMD": "Put", "PROGRAM": "blastn", "MEGABLAST": "on",
            "DATABASE": "nt", "QUERY": seq, "HITLIST_SIZE": "250"}
    if entrez:
        data["ENTREZ_QUERY"] = entrez   # e.g. '1980:2010[PDAT]' to bracket deposit age
    r = _request("POST", BLAST, data=data, timeout=60)
    rid = re.search(r"^\s*RID = (\S+)", r.text, re.M)
    rtoe = re.search(r"^\s*RTOE = (\d+)", r.text, re.M)
    if not rid:
        sys.exit("BLAST did not return an RID (submission rejected).")
    return rid.group(1), int(rtoe.group(1)) if rtoe else 30


def wait(rid: str, max_wait: int) -> None:
    waited = 0
    while waited < max_wait:
        time.sleep(20)
        waited += 20
        r = _request("GET", BLAST, timeout=60,
                     params={"CMD": "Get", "FORMAT_OBJECT": "SearchInfo", "RID": rid})
        st = re.search(r"Status=(\w+)", r.text)
        st = st.group(1) if st else "?"
        if st == "READY":
            if "ThereAreHits=yes" in r.text:
                return
            sys.exit("BLAST finished with no hits.")
        if st == "UNKNOWN":
            sys.exit(f"BLAST RID {rid} expired/unknown.")
    sys.exit(f"not ready after {max_wait}s; re-fetch later with --rid {rid}")


def results_json(rid: str) -> dict:
    r = _request("GET", BLAST, timeout=180,
                 params={"CMD": "Get", "RID": rid, "FORMAT_TYPE": "JSON2_S"})
    return json.loads(r.text)


def _meta(accs: list[str]) -> dict:
    """Deposit date / definition / length per accession (chunked esummary).
    Keyed by both the versioned and bare accession so BLAST's bare ids resolve."""
    out: dict = {}
    for i in range(0, len(accs), 80):
        chunk = accs[i:i + 80]
        if not chunk:
            break
        # Best-effort metadata enrichment: a failed chunk shouldn't abort the run.
        r = _request("GET", f"{EUTILS}/esummary.fcgi", timeout=60, fatal=False,
                     params=_ncbi({"db": "nuccore", "id": ",".join(chunk),
                                   "retmode": "json"}))
        if r is not None:
            try:
                res = r.json()["result"]
                for uid in res.get("uids", []):
                    d = res[uid]
                    av = d.get("accessionversion", uid)
                    rec = {"title": d.get("title", ""), "date": d.get("createdate", ""),
                           "len": d.get("slen", "")}
                    out[av] = rec
                    out[av.split(".")[0]] = rec
            except Exception:
                pass
        time.sleep(NCBI_DELAY)
    return out


def perfect_hits(doc: dict) -> tuple[int, list[tuple[str, str]]]:
    """From a JSON2_S result return (query_len, [(accession, title), ...]) for the
    full-length 100%-identity hits (a perfect hsp covering the whole query)."""
    search = doc["BlastOutput2"][0]["report"]["results"]["search"]
    qlen = int(search.get("query_len", 0))
    out, seen = [], set()
    for h in search.get("hits", []):
        best = max(h.get("hsps", [{}]), key=lambda x: x.get("identity", 0))
        if best.get("identity") == qlen and best.get("align_len", 0) >= qlen:
            desc = (h.get("description") or [{}])[0]
            acc = desc.get("accession", "")
            if acc and acc not in seen:
                seen.add(acc)
                out.append((acc, desc.get("title", "")))
    return qlen, out


def main() -> None:
    ap = argparse.ArgumentParser(description="BLAST a DNA part vs NCBI nt for 100%-identity sources.")
    ap.add_argument("--slug")
    ap.add_argument("--seq")
    ap.add_argument("--rid", help="re-fetch results for an existing RID")
    ap.add_argument("--entrez", default="", help="ENTREZ_QUERY filter, e.g. '1980:2010[PDAT]'")
    ap.add_argument("--max-wait", type=int, default=300)
    a = ap.parse_args()

    seq = (a.seq or "").upper() or (_seq_for(a.slug) if a.slug else "")
    if not seq and not a.rid:
        sys.exit("need --slug, --seq, or --rid")
    qlen = len(seq)

    if a.rid:
        rid = a.rid
    else:
        rid, rtoe = submit(seq, a.entrez)
        print(f"submitted RID={rid} (est {rtoe}s, qlen={qlen})", file=sys.stderr)
        wait(rid, a.max_wait)

    qlen2, hits = perfect_hits(results_json(rid))
    qlen = qlen or qlen2
    md = _meta([acc for acc, _ in hits])
    rows = [{"accession": acc, "date": md.get(acc, {}).get("date", ""),
             "subj_len": md.get(acc, {}).get("len", ""),
             "title": (md.get(acc, {}).get("title") or t)[:90]} for acc, t in hits]
    rows.sort(key=lambda r: r["date"] or "9999")   # oldest deposit first
    print(json.dumps({"slug": a.slug, "rid": rid, "qlen": qlen,
                      "n_perfect_full_length": len(hits),
                      "candidates_oldest_first": rows[:20]}, indent=2))


if __name__ == "__main__":
    main()
