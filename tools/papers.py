#!/usr/bin/env python3
"""Local full-text paper store — the paywall companion to ``sourcing/incoming/``.

A human drops a (often paywalled) paper PDF into the store, keyed by its PMID/DOI;
the cross-check agent (and any verifier) reads the *full text* from here instead of
being stuck on a public abstract. The store is **gitignored** — copyrighted PDFs and
their extracted text stay local and are never committed; only the part record and its
citations go into the repo. This is a personal reference cache (think Zotero storage),
not a redistribution channel.

The link to claims is implicit and already in the data: every ``functional_claims[].source``
and every ``references[]`` carries a ``pmid``/``doi``. This tool keys files by those, so
``resolve`` answers "do we have the paper this claim cites?" and ``coverage`` reports, across
the whole catalog, which cited papers we hold vs. still need.

Text is not enough: many claims cite a **figure/table** ("Fig 2", "Fig 3B"), where the
data actually lives. So the store keeps the original PDF and can **render any page to a PNG**
(``render``) for a vision-capable agent to *inspect the figure* — not just read its caption.
``resolve`` hands back both the extracted-text path (cheap prose) and the PDF path (figures).

Layout (all under ``sourcing/papers/``, gitignored):
    pmid-<pmid>.pdf / .txt      deposited file + cached extracted text
    doi-<slug>.pdf  / .txt      (when there is no PMID)
    <stem>.fig/p<NN>.png        on-demand page renders for figure inspection (`render`)
    index.json                  manifest: key -> {files, title, sha256, pages, added}
    coverage.json               last `coverage` report (cited papers: have vs. missing)

Commands:
    add <file> --pmid 12345 [--doi 10.x/y] [--title "..."]   ingest a paper
    resolve [--pmid 12345] [--doi 10.x/y] [--json] [--pdf]   print local path (agent uses this)
    render  [--pmid 12345] [--doi 10.x/y] --pages 3-5        render PDF pages to PNGs for figure inspection
    reindex                                                  rebuild index.json from disk
    coverage [--candidate]                                   cited-paper have/missing report
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "sourcing" / "papers"
INDEX = STORE / "index.json"
COVERAGE = STORE / "coverage.json"
REQUESTS = ROOT / "sourcing" / "REQUESTS.md"
SENTINEL = "_No active requests._"
PARTS_DIRS = {"validated": ROOT / "parts" / "validated",
              "candidate": ROOT / "parts" / "candidate"}


# ---------- key / filename helpers ----------

def norm_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    doi = doi.strip().lower()
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", doi)
    return doi or None


def doi_slug(doi: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm_doi(doi)).strip("_")


def basename_for(pmid: str | None, doi: str | None) -> str:
    """Filename stem: PMID wins (stable, short); else a slugified DOI."""
    if pmid:
        return f"pmid-{str(pmid).strip()}"
    if doi:
        return f"doi-{doi_slug(doi)}"
    raise ValueError("need a --pmid or --doi to key the paper")


# ---------- text extraction ----------

def extract_text(pdf: Path) -> tuple[str | None, int]:
    """Return (text, n_pages). Tries PyMuPDF then pypdf; (None, 0) if neither works."""
    try:
        import fitz  # PyMuPDF
        with fitz.open(pdf) as doc:
            return "\n".join(page.get_text() for page in doc), doc.page_count
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        r = PdfReader(str(pdf))
        return "\n".join((p.extract_text() or "") for p in r.pages), len(r.pages)
    except Exception:
        return None, 0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------- index ----------

def load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {"papers": []}


def save_index(idx: dict) -> None:
    STORE.mkdir(parents=True, exist_ok=True)
    idx["papers"].sort(key=lambda p: (p.get("pmid") or "", p.get("doi") or ""))
    INDEX.write_text(json.dumps(idx, indent=2) + "\n")


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- commands ----------

def cmd_add(args) -> int:
    src = Path(args.file).expanduser()
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 1
    pmid = str(args.pmid).strip() if args.pmid else None
    doi = norm_doi(args.doi)
    if not (pmid or doi):
        print("error: provide --pmid and/or --doi", file=sys.stderr)
        return 1
    STORE.mkdir(parents=True, exist_ok=True)
    stem = basename_for(pmid, doi)
    ext = src.suffix.lower() or ".pdf"
    dest = STORE / f"{stem}{ext}"
    shutil.copyfile(src, dest)

    txt_name = None
    pages = 0
    if ext == ".pdf":
        text, pages = extract_text(dest)
        if text and text.strip():
            txt = STORE / f"{stem}.txt"
            txt.write_text(text)
            txt_name = txt.name
        else:
            print("  note: no text extracted (scanned PDF?); the agent can still Read the PDF directly.",
                  file=sys.stderr)

    idx = load_index()
    # replace any existing entry with the same stem
    idx["papers"] = [p for p in idx["papers"] if p.get("stem") != stem]
    idx["papers"].append({
        "stem": stem, "pmid": pmid, "doi": doi,
        "title": args.title, "pdf": dest.name, "txt": txt_name,
        "pages": pages, "sha256": sha256(dest), "added_utc": _now(),
    })
    save_index(idx)
    print(f"added {dest.name}" + (f" (+{txt_name}, {pages} pp)" if txt_name else ""))
    return 0


def _resolve(pmid: str | None, doi: str | None) -> dict | None:
    pmid = str(pmid).strip() if pmid else None
    doi = norm_doi(doi)
    for p in load_index().get("papers", []):
        if pmid and p.get("pmid") == pmid:
            return p
        if doi and p.get("doi") == doi:
            return p
    return None


def cmd_resolve(args) -> int:
    p = _resolve(args.pmid, args.doi)
    if not p:
        if args.json:
            print(json.dumps({"found": False}))
        return 1
    pdf_path = STORE / p["pdf"]
    txt_path = STORE / p["txt"] if p.get("txt") else None
    if args.pdf:                      # caller wants the PDF (to inspect figures)
        print(pdf_path)
        return 0
    if args.json:
        print(json.dumps({"found": True,
                          "txt": str(txt_path) if txt_path else None,
                          "pdf": str(pdf_path), "pages": p.get("pages"),
                          "title": p.get("title"),
                          "hint": "read txt for prose; render/Read the pdf at the cited page to inspect figures"}))
    else:                            # default: cheapest readable form
        print(txt_path or pdf_path)
    return 0


def _parse_pages(spec: str) -> list[int]:
    """'3', '3-5', '2,4,7-9' -> sorted 1-indexed page list."""
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b) + 1))
        elif part:
            out.add(int(part))
    return sorted(out)


def cmd_render(args) -> int:
    """Render PDF pages to PNGs so an agent can visually inspect figures/tables."""
    p = _resolve(args.pmid, args.doi)
    if not p:
        print("error: paper not in store (add it first)", file=sys.stderr)
        return 1
    pdf = STORE / p["pdf"]
    try:
        import fitz
    except Exception:
        print("error: PyMuPDF (fitz) not installed — cannot render. The agent can still Read the PDF directly:\n"
              f"  {pdf}", file=sys.stderr)
        return 1
    outdir = STORE / f"{p['stem']}.fig"
    outdir.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf) as doc:
        n = doc.page_count
        pages = _parse_pages(args.pages) if args.pages else list(range(1, n + 1))
        written = []
        for pg in pages:
            if pg < 1 or pg > n:
                continue
            pix = doc[pg - 1].get_pixmap(dpi=args.dpi)
            out = outdir / f"p{pg:03d}.png"
            pix.save(out)
            written.append(out)
    for w in written:
        print(w)
    if not written:
        print("no pages rendered (check --pages range)", file=sys.stderr)
        return 1
    return 0


def cmd_reindex(args) -> int:
    if not STORE.exists():
        print("error: no store yet", file=sys.stderr)
        return 1
    idx = {"papers": []}
    for pdf in sorted(STORE.glob("*.pdf")):
        stem = pdf.stem
        m_pmid = re.match(r"pmid-(.+)$", stem)
        m_doi = re.match(r"doi-(.+)$", stem)
        txt = STORE / f"{stem}.txt"
        idx["papers"].append({
            "stem": stem,
            "pmid": m_pmid.group(1) if m_pmid else None,
            "doi": None,  # cannot losslessly recover DOI from slug; re-add to restore it
            "title": None,
            "pdf": pdf.name, "txt": txt.name if txt.exists() else None,
            "pages": extract_text(pdf)[1] if not txt.exists() else 0,
            "sha256": sha256(pdf), "added_utc": _now(),
        })
        _ = m_doi
    save_index(idx)
    print(f"reindexed {len(idx['papers'])} paper(s)")
    return 0


def _iter_part_files(include_candidate: bool):
    dirs = [PARTS_DIRS["validated"]]
    if include_candidate:
        dirs.append(PARTS_DIRS["candidate"])
    for d in dirs:
        if d.exists():
            yield from sorted(d.glob("*.json"))


def cmd_coverage(args) -> int:
    """Join every cited (pmid/doi) in the catalog against the store."""
    cited: dict[str, dict] = {}  # key -> {pmid, doi, citing: set("slug/claim_id" | "slug/ref")}

    def note(pmid, doi, where):
        pmid = str(pmid).strip() if pmid else None
        doi = norm_doi(doi)
        if not (pmid or doi):
            return
        key = f"pmid:{pmid}" if pmid else f"doi:{doi}"
        e = cited.setdefault(key, {"pmid": pmid, "doi": doi, "citing": set()})
        e["citing"].add(where)
        if pmid and not e["pmid"]:
            e["pmid"] = pmid
        if doi and not e["doi"]:
            e["doi"] = doi

    for pf in _iter_part_files(args.candidate):
        d = json.loads(pf.read_text())
        slug = d.get("slug", pf.stem)
        for ref in d.get("references", []):
            doi = None
            c = ref.get("comment", "")
            m = re.search(r"doi:(\S+)", c or "")
            if m:
                doi = m.group(1)
            note(ref.get("pubmed_id"), doi, f"{slug}/ref")
        for cl in d.get("functional_claims", []):
            s = cl.get("source", {})
            note(s.get("pmid"), s.get("doi"), f"{slug}/claim:{cl.get('id')}")

    have, missing = [], []
    for key, e in sorted(cited.items()):
        hit = _resolve(e["pmid"], e["doi"])
        rec = {"pmid": e["pmid"], "doi": e["doi"],
               "citing": sorted(e["citing"]),
               "claims": sorted(w for w in e["citing"] if "claim:" in w)}
        (have if hit else missing).append(rec)

    # a paper "needed" by a claim (not just a reference) is the priority fetch list
    missing_for_claims = [m for m in missing if m["claims"]]
    report = {"generated_utc": _now(),
              "cited_total": len(cited), "have": len(have), "missing": len(missing),
              "missing_blocking_claims": len(missing_for_claims),
              "have_papers": have, "missing_papers": missing}
    STORE.mkdir(parents=True, exist_ok=True)
    COVERAGE.write_text(json.dumps(report, indent=2) + "\n")

    print(f"cited papers: {len(cited)}  |  in store: {len(have)}  |  missing: {len(missing)}"
          f"  ({len(missing_for_claims)} are cited by a functional_claim)")
    if missing_for_claims:
        print("\nmissing & cited by a claim (priority to deposit):")
        for m in missing_for_claims[: args.limit]:
            ident = (f"PMID {m['pmid']}" if m["pmid"] else "") + (f" doi:{m['doi']}" if m["doi"] else "")
            print(f"  - {ident.strip()}  <- {', '.join(m['claims'])}")
        if len(missing_for_claims) > args.limit:
            print(f"  ... and {len(missing_for_claims) - args.limit} more (see {COVERAGE.relative_to(ROOT)})")
    return 0


def _split_requests(text: str) -> tuple[str, list[str]]:
    """(header-through-last-rule, managed-tail-lines)."""
    lines = text.splitlines()
    rules = [i for i, l in enumerate(lines) if l.strip() == "---"]
    if not rules:
        return text.rstrip() + "\n\n---\n", []
    idx = rules[-1]
    return "\n".join(lines[: idx + 1]), lines[idx + 1:]


def _parse_request_entries(tail: list[str]) -> list[dict]:
    """Each ``- [ ]`` block, kept VERBATIM, tagged with any pmid/doi it names."""
    entries: list[dict] = []
    cur: dict | None = None
    for l in tail:
        s = l.strip()
        if s.startswith("- [ ]"):
            if cur:
                entries.append(cur)
            mp = re.search(r"PMID\s+(\d+)", l)
            md = re.search(r"doi:([^\s)]+)", l)
            cur = {"pmid": mp.group(1) if mp else None,
                   "doi": norm_doi(md.group(1)) if md else None, "lines": [l]}
        elif cur is not None and s and s != SENTINEL:
            cur["lines"].append(l)
    if cur:
        entries.append(cur)
    return entries


def cmd_request(args) -> int:
    """Record a needed (paywalled) paper in REQUESTS.md — store-aware & self-pruning.

    Skips if we already hold the paper; drops any existing request now satisfied by
    the store; idempotent on (pmid/doi). This is the claim-evidence sibling of the
    sequence-source request path: it's how a blocked *paper* (not sequence) surfaces."""
    pmid = str(args.pmid).strip() if args.pmid else None
    doi = norm_doi(args.doi)
    if not (pmid or doi):
        print("error: provide --pmid and/or --doi", file=sys.stderr)
        return 1
    if _resolve(pmid, doi):
        print("already in store — not requesting")
        return 0
    text = REQUESTS.read_text(encoding="utf-8") if REQUESTS.exists() else f"# Source documents needed\n\n---\n\n{SENTINEL}\n"
    head, tail = _split_requests(text)
    kept = [e for e in _parse_request_entries(tail) if not _resolve(e["pmid"], e["doi"])]
    dup = any((pmid and e["pmid"] == pmid) or (doi and e["doi"] == doi) for e in kept)

    body_lines: list[str] = []
    for e in kept:
        body_lines += e["lines"]
    added = False
    if not dup:
        ident = " / ".join([x for x in (f"PMID {pmid}" if pmid else None,
                                        f"doi:{doi}" if doi else None) if x])
        title = f" — {args.title}" if args.title else ""
        deposit = "`python tools/papers.py add <pdf>" + (f" --pmid {pmid}" if pmid else "") \
                  + (f" --doi {doi}" if doi else "") + "`"
        body_lines += [
            f"- [ ] **{ident}**{title} — unblocks: {args.unblocks or 'a functional_claim'} "
            f"— barrier: {args.barrier or 'paywall'}",
            f"      full-text not machine-accessible; deposit it: {deposit}",
        ]
        added = True

    body = "\n".join(body_lines) if body_lines else SENTINEL
    REQUESTS.write_text(head + "\n\n" + body + "\n", encoding="utf-8")
    print("requested" if added else "already requested")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Local full-text paper store for cross-check / verification.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="ingest a paper PDF, keyed by PMID/DOI")
    a.add_argument("file")
    a.add_argument("--pmid")
    a.add_argument("--doi")
    a.add_argument("--title")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("resolve", help="print local path for a cited PMID/DOI (exit 1 if absent)")
    r.add_argument("--pmid")
    r.add_argument("--doi")
    r.add_argument("--json", action="store_true")
    r.add_argument("--pdf", action="store_true", help="print the PDF path (to inspect figures)")
    r.set_defaults(func=cmd_resolve)

    rn = sub.add_parser("render", help="render PDF pages to PNGs for figure/table inspection")
    rn.add_argument("--pmid")
    rn.add_argument("--doi")
    rn.add_argument("--pages", help="e.g. '4' or '3-5' or '2,4,7-9' (default: all pages)")
    rn.add_argument("--dpi", type=int, default=150)
    rn.set_defaults(func=cmd_render)

    ri = sub.add_parser("reindex", help="rebuild index.json from files on disk")
    ri.set_defaults(func=cmd_reindex)

    c = sub.add_parser("coverage", help="report cited papers we have vs. still need")
    c.add_argument("--candidate", action="store_true", help="also scan parts/candidate/")
    c.add_argument("--limit", type=int, default=40)
    c.set_defaults(func=cmd_coverage)

    q = sub.add_parser("request", help="record a blocked (paywalled) paper in sourcing/REQUESTS.md")
    q.add_argument("--pmid")
    q.add_argument("--doi")
    q.add_argument("--title")
    q.add_argument("--unblocks", help="what this paper would unblock, e.g. 'MBP/claim:ligand'")
    q.add_argument("--barrier", help="paywall | not-in-pmc | login | 403 | other")
    q.set_defaults(func=cmd_request)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
