#!/usr/bin/env python3
"""Static-site generator — replaces ``mkdocs build`` for the index + part pages.

The site is the redesign (proposals/site-redesign/), promoted to production:
  * ``site/index.html``            — the browse/search/filter SPA; cards LINK to the
                                     static part pages (no in-page drawer).
  * ``site/parts/<slug>/index.html`` — a static part page in the same design: header +
                                     meta, the embedded ``seqmake-part-view`` widget, the
                                     full functional claims (confidence / usefulness /
                                     verification-status badges, source quote + link),
                                     references, and downloads. Server-rendered HTML at the
                                     SAME URL the live w3id IRIs + agent-layer index.json
                                     already point to (``…/parts/<slug>/``).
  * ``site/assets/site.css``       — the shared design (extracted from the prototype).
  * ``site/assets/seqmake-part-view.js`` — the vendored viewer widget.
  * ``site/parts_index.json``      — the browse index (also used by external consumers).

Reads ``catalog.json`` (the manifest build_catalog.py emits) for everything except the
widget's sequence/features, which come from each part's ``.gb`` via ``build_molecule_json``.
Run AFTER ``build_catalog.py`` (it produces catalog.json + the parts/files/ downloads).

Usage:  python tools/build_site.py  [--out site]
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from pathlib import Path

from build_catalog import build_molecule_json  # the real widget contract

ROOT = Path(__file__).resolve().parent.parent
# The production SPA template (a copy of the proposals/site-redesign prototype; production
# must not depend on a proposals/ file). Its <style> is extracted to assets/site.css at build.
TEMPLATE = ROOT / "tools" / "site_templates" / "index.html"
WIDGET = ROOT / "docs" / "assets" / "seqmake-part-view.js"
FILES_SRC = ROOT / "docs" / "parts" / "files"   # build_catalog.py emits the downloads here
TYPE_LABEL = {
    "promoter": "Promoter", "ribosome_entry_site": "RBS", "RBS": "RBS", "operator": "Operator",
    "CDS": "CDS", "polypeptide_domain": "Protein domain", "protein_domain": "Protein domain",
    "terminator": "Terminator", "origin_of_replication": "Origin", "rep_origin": "Origin",
    "oriT": "oriT", "protein_binding_site": "Binding site", "protein_bind": "Binding site",
    "ncRNA": "ncRNA", "misc_RNA": "ncRNA", "sequence_feature": "Feature", "misc_feature": "Feature",
}
E = html.escape


def tlabel(t: str) -> str:
    return TYPE_LABEL.get(t, t or "")


# ---------------------------------------------------------------- part page

def _src_link(s: dict) -> str:
    if not s:
        return ""
    url = (f"https://pubmed.ncbi.nlm.nih.gov/{s['pmid']}/" if s.get("pmid")
           else f"https://doi.org/{s['doi']}" if s.get("doi") else s.get("url", ""))
    lab = (f"PMID {s['pmid']}" if s.get("pmid")
           else f"doi:{s['doi']}" if s.get("doi") else "source")
    loc = ", ".join(x for x in (s.get("figure"), s.get("table"), s.get("page")) if x)
    a = f'<a href="{E(url)}" target="_blank" rel="noopener">{E(lab)}</a>' if url else E(lab)
    return a + (f" · {E(loc)}" if loc else "")


def _status_badge(c: dict) -> str:
    """The verification-lifecycle marker (CLAIM-MODEL.md)."""
    st = c.get("analysis_status")
    if c.get("cross_checked") or st == "verified":
        return '<span class="cbadge cc" title="independently verified against the cited source">✓ verified</span>'
    if st == "flagged":
        return '<span class="cbadge fl" title="source read; partially supported / downgraded / superseded">⚑ flagged</span>'
    if st == "sources-pending":
        return '<span class="cbadge sp" title="primary source not yet reachable — a request is filed">⏳ source pending</span>'
    return '<span class="cbadge pd" title="authored; not yet independently cross-checked">• unverified</span>'


def _claim_html(c: dict) -> str:
    conf = (f'<span class="cbadge cf-{E(c["confidence"])}">{E(c["confidence"])} confidence</span>'
            if c.get("confidence") else "")
    use = (f'<span class="cbadge us">★ {E(c["usefulness"])} usefulness</span>'
           if c.get("usefulness") else "")
    q = (f'<div class="cl-quote">“{E(c["source"]["quote"])}”</div>'
         if c.get("source", {}).get("quote") else "")
    cm = (f'<div class="cl-quote" style="font-style:normal;border-color:var(--gold)">⚠ {E(c["comment"])}</div>'
          if c.get("comment") else "")
    ctype = E((c.get("type") or "").replace("_", " "))
    return (f'<div class="claimcard">'
            f'<div class="cl-top"><span class="typechip">{ctype}</span>'
            f'{conf}{use}{_status_badge(c)}</div>'
            f'<p class="cl-label">{E(c.get("label",""))}</p>{q}{cm}'
            f'<div class="cl-src">{_src_link(c.get("source", {}))}</div></div>')


def _ref_html(r: dict) -> str:
    doi = None
    m = re.search(r"doi:(\S+)", r.get("comment", "") or "")
    if m:
        doi = m.group(1)
    pmid = r.get("pubmed_id") or r.get("pmid")
    url = (f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid
           else f"https://doi.org/{doi}" if doi else "")
    link = f' <a href="{E(url)}" target="_blank" rel="noopener">{("PMID " + E(pmid)) if pmid else "link"}</a>' if url else ""
    bits = "".join(x for x in (
        f' — {E(r["authors"])}' if r.get("authors") else "",
        f' · {E(r["journal"])}' if r.get("journal") else "") )
    return f'<div class="refitem"><span class="rt">{E(r.get("title",""))}</span>{bits}{link}</div>'


def _mol_mount(mol: dict | None) -> str:
    if not mol:
        return ""
    j = json.dumps(mol, separators=(",", ":")).replace("<", "\\u003c")
    return ('<div class="partview"><div data-part-view data-height="380">'
            f'<script type="application/json">{j}</script></div></div>')


def part_page(part: dict, mol: dict | None, css_href: str, asset_dir: str) -> str:
    slug, name = part["slug"], part["name"]
    kind = part.get("kind")
    length = part.get("length")
    length_lbl = (f"{length} {'aa' if kind == 'protein' else 'bp'}" if length is not None else "—")
    base = f"https://dbikard.github.io/seqmake-parts/parts/{slug}/"
    validated = part.get("status") == "validated"
    status = ('<span class="badge val"><span class="seal">✓</span>Validated</span>' if validated
              else '<span class="badge cand"><span class="seal"></span>Candidate</span>')
    meta = "".join(f"<span>{E(x)}</span>" for x in (
        tlabel(part.get("feature_type")), part.get("so_term") or "", length_lbl,
        "protein" if kind == "protein" else "dsDNA", part.get("source_accession") or "",
        f"{len(part.get('references', []) or [])} refs") if x)

    def _names(key):
        out = []
        for r in part.get(key, []) or []:
            out.append(r.get("name") if isinstance(r, dict) else r)
        return ", ".join(E(x) for x in out if x)

    def _row(k, v):
        return f'<div class="drow2"><div class="dk">{k}</div><div>{v}</div></div>' if v else ""

    syn = ("".join(f"<span>{E(s)}</span>" for s in part.get("synonyms", []) or []))
    syn = f'<div class="drow2"><div class="dk">Synonyms</div><div class="synlist">{syn}</div></div>' if syn else ""
    claims = part.get("functional_claims", []) or []
    claims_html = (f'<div class="dsec">Sourced claims · {len(claims)}</div>'
                   + "".join(_claim_html(c) for c in claims)) if claims else (
        '<div class="dsec">Sourced claims</div>'
        '<p style="color:var(--ink-faint);font-style:italic">No structured functional claims yet — see the references.</p>')
    refs = part.get("references", []) or []
    refs_html = (f'<div class="dsec">References</div>' + "".join(_ref_html(r) for r in refs)) if refs else ""
    uni = part.get("uniprot_import", {}).get("accession") if isinstance(part.get("uniprot_import"), dict) else None
    desc = part.get("description") or ""
    cvar = f"var(--c-{part.get('feature_type','misc_feature')})"
    return f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(name)} — SeqMake Parts</title>
<meta name="description" content="{E(desc[:180])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600&family=Hanken+Grotesk:wght@400;500;600&family=Spline+Sans+Mono:wght@400;500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{css_href}">
</head>
<body>
<header class="masthead"><div class="mhinner"><a class="brand" href="../../">SeqMake&nbsp;Parts</a>
<button class="iconbtn" id="themeToggle" aria-label="Toggle dark mode" title="Toggle theme">◑</button></div></header>
<section class="detail" id="detail">
  <div class="dwrap" style="--type:{cvar}">
    <a class="backbtn" href="../../">← Back to catalog</a>
    <div class="dtop"><span class="typechip">{E(tlabel(part.get('feature_type')))}</span>{status}</div>
    <h1 class="dt">{E(name)}</h1>
    <div class="dmeta">{meta}</div>
    {f'<p class="dlede">{E(desc)}</p>' if desc else ''}
    {_mol_mount(mol)}
    {syn}{_row("Regulated by", _names("regulated_by"))}{_row("Regulates", _names("regulates"))}
    {claims_html}{refs_html}
    <div class="dsec">Get this part</div>
    <div class="dlbtns">
      <a class="dlbtn" href="../files/{slug}.gb">⬇ GenBank</a>
      <a class="dlbtn" href="../files/{slug}.fasta">⬇ FASTA</a>
      <a class="dlbtn" href="../files/{slug}.ttl">⬇ RDF</a>
      <a class="dlbtn" href="../files/{slug}.json">↗ JSON record</a>
      {f'<a class="dlbtn" href="https://www.uniprot.org/uniprotkb/{E(uni)}" target="_blank" rel="noopener">↗ UniProt</a>' if uni else ''}
    </div>
  </div>
</section>
<script src="{asset_dir}/seqmake-part-view.js"></script>
<script>
(function(){{const KEY="seqmake-parts-theme";try{{const t=localStorage.getItem(KEY);if(t)document.documentElement.setAttribute("data-theme",t);}}catch(e){{}}
document.getElementById("themeToggle").onclick=function(){{const c=document.documentElement.getAttribute("data-theme");const n=c==="dark"?"light":"dark";document.documentElement.setAttribute("data-theme",n);try{{localStorage.setItem(KEY,n);}}catch(e){{}}}};}})();
</script>
</body>
</html>
"""


# ---------------------------------------------------------------- index page

def index_data(parts: list[dict]) -> dict:
    """Lightweight browse index — the fields the SPA grid/facets/search use (no
    per-claim prose / sequence; those live on the part pages)."""
    def tf(p):
        return [r.get("name") if isinstance(r, dict) else r for r in (p.get("regulated_by") or [])]
    out = []
    for p in parts:
        fcs = p.get("functional_claims", []) or []
        out.append({
            "name": p["name"], "slug": p["slug"], "type": p.get("feature_type"),
            "so_name": p.get("so_name"), "so_term": p.get("so_term"), "kind": p.get("kind"),
            "status": p.get("status"), "documented": bool(p.get("documented")),
            "len": p.get("length"), "aa": p.get("protein_length_aa"),
            "syn": p.get("synonyms", []) or [], "desc": p.get("description") or "",
            "cols": [c.get("name") if isinstance(c, dict) else c for c in (p.get("collections_resolved") or p.get("collections") or [])],
            "acc": p.get("source_accession") or "",
            "tf": [x for x in tf(p) if x],
            "regs": [r.get("name") if isinstance(r, dict) else r for r in (p.get("regulates") or [])],
            "nclaims": len(fcs), "claim_types": sorted({c.get("type") for c in fcs if c.get("type")}),
            "nrefs": len(p.get("references", []) or []),
            "uniprot": (p.get("uniprot_import") or {}).get("accession"),
        })
    return out


def extract_css(template_html: str) -> str:
    return re.search(r"<style>(.*?)</style>", template_html, re.S).group(1).strip() + "\n"


def build_index_html(template_html: str, manifest: dict, css_href: str) -> tuple[str, dict]:
    """Adapt the SPA template: external CSS, injected browse data, cards LINK to the
    static part pages, and the in-page detail/drawer machinery removed."""
    html_src = template_html
    data = {
        "meta": {k: manifest.get(v) for k, v in {
            "n_parts": "n_parts", "n_validated": "n_validated", "n_candidate": "n_candidate",
            "n_documented": "n_documented", "n_claims": "n_functional_claims"}.items()},
        "types": _types_list(manifest),
        "collections": manifest.get("collections", []),
        "parts": index_data(manifest["parts"]),
    }
    payload = "window.CATALOG = " + json.dumps(data, separators=(",", ":")) + ";"

    # external stylesheet
    html_src = re.sub(r"<style>.*?</style>",
                      f'<link rel="stylesheet" href="{css_href}">', html_src, flags=re.S)
    # the index doesn't need the widget bundle
    html_src = html_src.replace('<script src="../../docs/assets/seqmake-part-view.js"></script>\n', "")
    # inject the browse data in place of the data.js file
    html_src = html_src.replace('<script src="data.js"></script>', f"<script>{payload}</script>")
    # the static part pages own the detail view -> drop the in-page detail section
    html_src = re.sub(r'<section class="detail" id="detail"[^>]*></section>\s*', "", html_src)
    # cards become real links to the part pages
    html_src = html_src.replace('href="#" data-slug="${p.slug}"', 'href="parts/${p.slug}/" data-slug="${p.slug}"')
    # replace the whole detail/drawer JS block with a plain navigation
    html_src = re.sub(
        r"/\* =+ full-page part detail \*/.*?window\.addEventListener\(\"popstate\",route\);",
        'function openPart(slug){location.href="parts/"+slug+"/";}\n'
        'function route(){}\nfunction showCatalog(){}',
        html_src, flags=re.S)
    return html_src, data


def _types_list(manifest: dict) -> list[dict]:
    types: dict[str, dict] = {}
    for p in manifest["parts"]:
        t = p.get("feature_type")
        e = types.setdefault(t, {"type": t, "so_name": p.get("so_name"),
                                 "so_term": p.get("so_term"), "total": 0, "validated": 0})
        e["total"] += 1
        if p.get("status") == "validated":
            e["validated"] += 1
    return sorted(types.values(), key=lambda e: -e["total"])


# ---------------------------------------------------------------- assemble

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    args = ap.parse_args()
    out = ROOT / args.out
    if out.exists():
        shutil.rmtree(out)
    (out / "assets").mkdir(parents=True)
    (out / "parts").mkdir(parents=True)

    manifest = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
    template_html = TEMPLATE.read_text(encoding="utf-8")

    # assets — site.css is the template's <style>, extracted once (single source)
    (out / "assets" / "site.css").write_text(extract_css(template_html), encoding="utf-8")
    if WIDGET.exists():
        shutil.copyfile(WIDGET, out / "assets" / "seqmake-part-view.js")

    # index
    index_html, data = build_index_html(template_html, manifest, "assets/site.css")
    (out / "index.html").write_text(index_html, encoding="utf-8")
    (out / "parts_index.json").write_text(json.dumps(data, separators=(",", ":")) + "\n",
                                          encoding="utf-8")

    # downloads (built by build_catalog.py)
    if FILES_SRC.exists():
        shutil.copytree(FILES_SRC, out / "parts" / "files")

    # one static page per part
    n = 0
    for p in manifest["parts"]:
        slug, status = p["slug"], p.get("status")
        gb = ROOT / "parts" / ("validated" if status == "validated" else "candidate") / f"{slug}.gb"
        try:
            mol = build_molecule_json(gb)
        except Exception:
            mol = None
        page = part_page(p, mol, "../../assets/site.css", "../../assets")
        d = out / "parts" / slug
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(page, encoding="utf-8")
        n += 1

    print(f"site: index + {n} part pages -> {out.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
