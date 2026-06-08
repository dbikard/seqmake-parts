"""Publish an ``annotate-part`` proposal into this catalog as a validated part.

The authoring half of the catalog loop, and the write-side mirror of
``build_catalog.py``: a proposal (the JSON the ``annotate-part`` workflow
returns: part, sequence, feature_type, children, references, report_markdown)
becomes an annotated GenBank record + its ``.md`` doc page written into
``parts/validated/``, promoting the part out of ``parts/candidate/`` if it was
there, then ``tools/build_catalog.py`` rebuilds the manifest.

Self-contained (BioPython only; shares ``so_terms`` with the manifest builder),
so the catalog repo owns reading, writing and building its own data with no
dependency on seqmake. Run it directly::

    python tools/publish_part.py proposal.json [--name NAME] [--no-rebuild] [--json]

or import ``publish_part`` / ``build_part_record``. The seqmake CLI
(``seqmake library publish``) is a thin shell-out to this script.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, Reference as BioReference, SeqFeature
from Bio.SeqRecord import SeqRecord

sys.path.insert(0, str(Path(__file__).resolve().parent))
from so_terms import so_for  # noqa: E402

CATALOG_ROOT = Path(__file__).resolve().parent.parent


class PublishError(RuntimeError):
    """A proposal could not be published to the catalog."""


# --- inlined formatting helpers (were seqmake.library.io) ------------------

def _slugify(name: str) -> str:
    """Turn a part name into a safe filename stem."""
    slug = re.sub(r"[^A-Za-z0-9.\-]+", "_", name).strip("_")
    return slug or "part"


@dataclass
class Reference:
    """A literature citation. Stored natively in the GenBank ``REFERENCE``
    block (one per distinct source) and linked to a feature via ``/citation``;
    the DOI rides in the REMARK line as ``doi:<id>`` (GenBank has no DOI field)."""

    authors: str = ""
    title: str = ""
    journal: str = ""
    pmid: str | None = None
    doi: str | None = None

    def dedup_key(self) -> tuple:
        if self.pmid:
            return ("pmid", self.pmid)
        if self.doi:
            return ("doi", self.doi.lower())
        return ("ref", self.authors, self.title, self.journal)


def _reference_to_bio(ref: Reference) -> BioReference:
    """Map a ``Reference`` onto a BioPython REFERENCE block."""
    bref = BioReference()
    bref.authors = ref.authors
    bref.title = ref.title
    bref.journal = ref.journal
    if ref.pmid:
        bref.pubmed_id = ref.pmid
    if ref.doi:
        bref.comment = f"doi:{ref.doi}"
    return bref


def _build_reference_block(
    feature_refs: list[list[Reference]],
) -> tuple[list[BioReference], list[list[str]]]:
    """Deduplicate references across features and assign 1-based numbers.

    ``feature_refs`` is one reference list per feature, in write order (main
    first, then children). Returns ``(bio_refs, citations)`` where ``bio_refs``
    is the deduplicated REFERENCE-block list and ``citations[i]`` holds the
    ``/citation`` values (e.g. ``["[1]"]``) for feature ``i``.
    """
    bib: list[Reference] = []
    numbers: dict[tuple, int] = {}
    citations: list[list[str]] = []
    for refs in feature_refs:
        cites: list[str] = []
        for r in refs:
            key = r.dedup_key()
            if key not in numbers:
                bib.append(r)
                numbers[key] = len(bib)  # 1-based REFERENCE number
            cites.append(f"[{numbers[key]}]")
        citations.append(cites)
    return [_reference_to_bio(r) for r in bib], citations


# --- proposal -> GenBank record -------------------------------------------

def _reg_class(label: str) -> str:
    low = label.lower()
    # -35/-10 may sit anywhere in the label (e.g. "RNA II promoter -35" for an
    # origin's convergent promoters), so match the token, not just a prefix.
    if "-35" in low:
        return "minus_35_signal"
    if "-10" in low:
        return "minus_10_signal"
    if "rbs" in low or "shine" in low or low.strip() == "sd":
        return "ribosome_binding_site"
    if "promoter" in low:
        return "promoter"
    return "other"


def _norm_label(label: str, used: set[str]) -> str:
    """Short, unique /label: drop the parenthetical + a trailing box/site, then
    disambiguate collisions from the parenthetical."""
    base = re.sub(r"\s+(box|site)$", "", label.split(" (")[0].strip(), flags=re.I) or label
    if base not in used:
        used.add(base)
        return base
    m = re.search(r"\(([^)]*)\)", label)
    if m:
        cand = f"{base} ({m.group(1).split(',')[0].split()[0]})"
        if cand not in used:
            used.add(cand)
            return cand
    i = 2
    while f"{base} {i}" in used:
        i += 1
    used.add(f"{base} {i}")
    return f"{base} {i}"


def _first_sentence(note: str | None) -> str:
    if not note:
        return ""
    s = re.split(r"(?<=[.])\s", note.strip(), maxsplit=1)[0].strip()
    return s if len(s) <= 160 else s[:157] + "..."


def _description(proposal: dict) -> str:
    """One-line description = the report's first non-heading line (md stripped)."""
    for line in (proposal.get("report_markdown") or "").splitlines():
        line = re.sub(r"[*`]", "", line.strip())
        if line and not line.startswith("#"):
            return line if len(line) <= 200 else line[:197] + "..."
    return proposal.get("part", "")


def build_part_record(proposal: dict, *, name: str | None = None,
                      synonyms: list[str] | None = None) -> SeqRecord:
    """Convert an ``annotate-part`` proposal into an annotated ``SeqRecord``.

    A protein ``sequence`` (amino-acid alphabet) yields a protein-canonical
    record (``LOCUS ... aa``) with residue-coordinate children and the
    proposal's ``source_accession`` stamped as a ``/db_xref`` alongside the SO
    term; a DNA sequence yields a DNA record as before.

    Verifies every child's coordinates against the sequence, normalises child
    labels (unique, concise), stamps ``regulatory_class`` on regulatory
    features, and builds the shared REFERENCE block with per-feature
    ``/citation`` (references not cited by any child attach to the main feature).

    Raises:
        PublishError: No sequence, or a child's coordinates are out of bounds.
    """
    seq = (proposal.get("sequence") or "").upper()
    if not seq:
        raise PublishError("proposal has no sequence")
    # A coding part is protein-canonical: a protein sequence (aa alphabet) is
    # written as a protein record (LOCUS aa) with residue-coordinate children.
    is_protein = bool(set(seq) - set("ACGTUN"))
    name = name or proposal.get("part")
    if not name:
        raise PublishError("proposal has no part name")
    feature_type = proposal.get("feature_type") or "misc_feature"

    refmap: dict[str, Reference] = {}
    for r in proposal.get("references") or []:
        key = r.get("pmid") or r.get("doi")
        if key:
            refmap[key] = Reference(pmid=r.get("pmid", ""), doi=r.get("doi", ""),
                                    authors=r.get("authors", ""), title=r.get("title", ""),
                                    journal=r.get("journal", ""))

    used: set[str] = set()
    kids: list[tuple[str, dict]] = []
    child_reflists: list[list[Reference]] = []
    cited: set[str] = set()
    for c in proposal.get("children") or []:
        s, e = int(c["start"]), int(c["end"])
        if not (0 <= s < e <= len(seq)):
            raise PublishError(
                f"child {c.get('label')!r} coords {s}..{e} out of bounds (len {len(seq)})")
        rl = [refmap[pm] for pm in (c.get("citation_pmids") or []) if pm in refmap]
        cited.update(pm for pm in (c.get("citation_pmids") or []) if pm in refmap)
        kids.append((_norm_label(c.get("label", ""), used), c))
        child_reflists.append(rl)
    main_refs = [refmap[k] for k in refmap if k not in cited]

    bio_refs, citations = _build_reference_block([main_refs] + child_reflists)
    desc = _description(proposal)
    slug = _slugify(name)
    rec = SeqRecord(Seq(seq), id=slug[:16] or "part", name=slug[:16] or "part",
                    description=desc or name,
                    annotations={"molecule_type": "protein" if is_protein else "DNA"})
    if bio_refs:
        rec.annotations["references"] = bio_refs
    mq: dict[str, list[str]] = {"label": [name]}
    if synonyms:
        mq["synonym"] = list(synonyms)
    if desc:
        mq["note"] = [desc]
    xrefs: list[str] = []
    so = so_for(feature_type)
    if so:
        xrefs.append(so[0])
    acc = (proposal.get("source_accession") or "").strip()
    if acc:
        xrefs.append(acc)  # canonical provenance for a coding part
    if xrefs:
        mq["db_xref"] = xrefs
    rb = [str(t).strip() for t in (proposal.get("regulated_by") or []) if str(t).strip()]
    if rb:
        mq["regulated_by"] = rb  # cognate TF(s); catalog cross-links them
    if citations[0]:
        mq["citation"] = citations[0]
    rec.features.append(SeqFeature(FeatureLocation(0, len(seq), strand=1),
                                   type=feature_type, qualifiers=mq))
    for (label, c), cites in zip(kids, citations[1:]):
        q: dict[str, list[str]] = {"label": [label], "parent": [name]}
        if c["feature_type"] == "regulatory":
            q["regulatory_class"] = [_reg_class(label)]
        note = _first_sentence(c.get("note"))
        if note:
            q["note"] = [note]
        cso = so_for(c["feature_type"], (q.get("regulatory_class") or [None])[0], label)
        if cso:
            q["db_xref"] = [cso[0]]
        if cites:
            q["citation"] = cites
        rec.features.append(SeqFeature(
            FeatureLocation(int(c["start"]), int(c["end"]), strand=c.get("strand", 1)),
            type=c["feature_type"], qualifiers=q))
    return rec


# --- publish into the catalog ----------------------------------------------

def _existing_synonyms(gb_path: Path) -> list[str]:
    rec = SeqIO.read(str(gb_path), "genbank")
    main = next((f for f in rec.features if "parent" not in f.qualifiers), None)
    return list(main.qualifiers.get("synonym", [])) if main else []


def _rebuild_manifest(catalog_root: Path) -> str:
    tool = catalog_root / "tools" / "build_catalog.py"
    if not tool.exists():
        raise PublishError(f"no tools/build_catalog.py under {catalog_root}")
    proc = subprocess.run([sys.executable, str(tool)], cwd=str(catalog_root),
                          capture_output=True, text=True)
    if proc.returncode != 0:
        raise PublishError(
            f"build_catalog.py failed: {(proc.stderr or proc.stdout).strip()}")
    out = proc.stdout.strip().splitlines()
    return out[-1] if out else ""


def publish_part(proposal: dict, catalog_root: Path | str = CATALOG_ROOT, *,
                 rebuild: bool = True, name: str | None = None) -> dict:
    """Write a proposal into a catalog checkout as a validated part.

    Writes ``parts/validated/<slug>.gb`` + ``<slug>.md`` (the report), promotes
    the part out of ``parts/candidate/`` if present (preserving its synonyms),
    and rebuilds ``catalog.json`` via the catalog's own generator.

    Raises:
        PublishError: Not a catalog checkout, no ``report_markdown`` (validated
            parts require a doc page), or the record/manifest build fails.
    """
    catalog_root = Path(catalog_root)
    validated = catalog_root / "parts" / "validated"
    candidate = catalog_root / "parts" / "candidate"
    if not (catalog_root / "parts").is_dir():
        raise PublishError(f"not a catalog checkout: {catalog_root} (no parts/)")
    name = name or proposal.get("part")
    if not name:
        raise PublishError("proposal has no part name")
    report = proposal.get("report_markdown")
    if not report or not report.strip():
        raise PublishError("a validated part requires report_markdown (the .md doc page)")

    slug = _slugify(name)
    synonyms = None
    for d in (validated, candidate):
        existing = d / f"{slug}.gb"
        if existing.exists():
            synonyms = _existing_synonyms(existing)
            break

    rec = build_part_record(proposal, name=name, synonyms=synonyms)
    validated.mkdir(parents=True, exist_ok=True)
    SeqIO.write([rec], str(validated / f"{slug}.gb"), "genbank")
    (validated / f"{slug}.md").write_text(report.strip() + "\n", encoding="utf-8")

    promoted = False
    cand_gb = candidate / f"{slug}.gb"
    if cand_gb.exists():
        cand_gb.unlink()
        (candidate / f"{slug}.md").unlink(missing_ok=True)
        promoted = True

    result = {
        "slug": slug, "name": name,
        "path": str(validated / f"{slug}.gb"),
        "n_children": len(rec.features) - 1,
        "promoted_from_candidate": promoted,
    }
    if rebuild:
        result["manifest"] = _rebuild_manifest(catalog_root)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Publish an annotate-part proposal as a validated catalog part.")
    ap.add_argument("proposal_json", help="JSON the annotate-part workflow returns")
    ap.add_argument("--name", default=None, help="Override the part name from the proposal")
    ap.add_argument("--no-rebuild", action="store_true", help="Skip rebuilding catalog.json")
    ap.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    args = ap.parse_args()

    proposal = json.loads(Path(args.proposal_json).read_text(encoding="utf-8"))
    if "part" not in proposal and isinstance(proposal.get("result"), dict):
        proposal = proposal["result"]  # unwrap a raw workflow result
    try:
        res = publish_part(proposal, CATALOG_ROOT, rebuild=not args.no_rebuild, name=args.name)
    except PublishError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"ok": True, **res}))
    else:
        extra = ", promoted from candidate" if res["promoted_from_candidate"] else ""
        print(f"Published {res['name']} -> validated ({res['n_children']} sub-features{extra}).")
        print("Next: commit + push the catalog, then `seqmake library refresh`.")


if __name__ == "__main__":
    main()
