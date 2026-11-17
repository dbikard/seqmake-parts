#!/usr/bin/env python3
"""Library quality gate: what makes a part safe to annotate a plasmid with.

The catalog is a *matching library*: a tool that annotates plasmids names every
span that matches a part. A defect in the library therefore becomes a wrong
name on many plasmids. This gate checks, over the canonical ``parts/*/*.json``:

  names       every name and synonym belongs to one part (case-insensitive);
  duplicate   no two parts are identical or >= 98% identical over the shorter
              one, unless one names the other in a link qualifier on its main
              feature (``variant_of``, ``component``, ``sub_region_of``, or
              ``cognate`` for a pair of recombination sites);
  contains    a part holding another part's whole sequence declares it: a
              link as above, or a sub-feature labelled with that part's name
              or synonym over at least 80% of the contained copy;
  near        a part that is *almost* inside a longer one -- at least 90% of
              its bases aligned at >= 95% identity, the longer part keeping
              bases of its own -- declares it the same way. This is the
              ``ts ori101`` shape: the 223 bp origin sat inside it at 97.8%
              identity, under the duplicate threshold and not an exact
              containment, and it outranked the origin on 224 plasmids;
  orf         a non-coding DNA part is not mostly one gene: no ATG open reading
              frame of >= 300 bp covers 80% of it;
  short       a DNA part is at least 20 bp;
  subfeature  every sub-feature names an existing parent and lies inside it
              (that every feature lies inside the part's own sequence is checked
              by ``validate_parts.py``, which CI runs just before this);
  manifest    ``catalog.json`` and ``index.json`` list exactly the part files,
              with the same name, synonyms, status and ``sourced`` flag;
  status      a validated part is sourced: its record names the deposit the
              sequence came from (``provenance.sequence_source``). Whether that
              deposit really contains the sequence is checked by
              ``tools/verify_sources.py``, which re-fetches it (network, so not
              part of this gate).

A part deliberately kept despite a finding goes in an allow-list below, with
the reason. Never lower a threshold to make a finding go away.

Run::

    python tools/check_library.py      # exit 1 on any finding
"""
from __future__ import annotations

import json
import sys
from itertools import combinations
from pathlib import Path

from Bio.Align import PairwiseAligner, substitution_matrices

sys.path.insert(0, str(Path(__file__).resolve().parent))
from catalog_overlap import _rc  # noqa: E402
from part_json import is_sourced  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LINK_KEYS = ("variant_of", "component", "sub_region_of", "cognate")
CODING = {"CDS", "gene", "protein_domain", "sig_peptide", "mat_peptide"}
NEAR_IDENTITY = 0.98
NEAR_IN_IDENTITY = 0.95   # a shorter part essentially inside a longer one
NEAR_IN_COVERAGE = 0.90
NEAR_IN_HOST_MAX = 0.90   # ... with bases of its own outside the alignment
ORF_FRACTION = 0.80
MIN_ORF_BP = 300  # a shorter ORF occurs by chance in non-coding DNA
MIN_DNA_BP = 20

# Real elements shorter than MIN_DNA_BP: an operator or an RBS is this short.
ALLOW_SHORT = {
    "B0034_RBS": "12 bp iGEM RBS (BBa_B0034); an RBS is this short",
    "B0030 RBS": "15 bp iGEM RBS (BBa_B0030); an RBS is this short",
    "lacO": "17 bp core of the lac operator O1 (Gilbert & Maxam 1973 publish 24 bp); an operator is this short",
    "I-SceI site": "18 bp homing-endonuclease recognition site",
    "tetO": "19 bp tet operator of the pRAB vectors (JN635500); an operator is this short",
}
# Non-coding parts that overlap a coding sequence by nature.
ALLOW_ORF = {
    "WPRE": "post-transcriptional RNA element whose sequence spans part of the "
            "woodchuck hepatitis virus X gene; used and typed as an RNA element",
}
# Validated before a sourced record was required: each cites the literature for
# its element but names no deposit for its bases. They keep their status and are
# re-sourced on the next touch (the same grandfathering `validate_parts` applies).
GRANDFATHERED_UNSOURCED = {
    "P2", "PA1/O4/O3", "PLtetO-1", "PT5/lacO", "PchnB", "Plac", "PlacUV5", "Pm",
    "PphlF", "PtetA", "Ptac", "Ptrc", "Pxyl/tet", "T7lac",
}
# Pairs found by `duplicate`/`contains` that are deliberately left undeclared,
# each until the question in its reason is settled from the literature.
ALLOW_PAIRS: dict[frozenset, str] = {
    frozenset(("PA1lacO-1", "PA1/O4/O3")):
        "PA1lacO-1 (an unsourced stub) holds all 56 bp of PA1/O4/O3; whether the "
        "Lutz & Bujard 1997 promoter is built on the Lanzer & Bujard 1988 one, or "
        "the stub is mis-sourced, needs both papers' sequence figures",
    frozenset(("PA1/O4/O3", "lacO")):
        "PA1/O4/O3 names its operators by position ('lac operator O4', 'O3'); its "
        "O4 child sits 1 bp off the exact 17 bp lacO copy: needs Lanzer & Bujard 1988",
    frozenset(("B0030 RBS", "B0034_RBS")):
        "B0034's 12 bp are the 3' end of B0030 (both iGEM RBSs). Declared as a child, "
        "the annotator replaced whole B0030 matches with B0034 on 72 plasmids and "
        "renamed 200 more (measured on a 1,390-plasmid collection), so it stays "
        "undeclared until the annotator ranks a whole parent above its child",
    frozenset(("Pxyl/tet", "PtetA")):
        "the 58 bp synthetic pRAB promoter (Helle et al. 2011) carries a one-base variant of "
        "the 29 bp PtetA at its 5' end; both are attested promoters and neither is composed "
        "of the other, so there is no true component/variant link to declare",
    frozenset(("tetR/tetA promoters", "tetO")):
        "two operator forms, neither composed of the other: tetO is the pRAB vectors' "
        "operator (JN635500 4135-4153) and the Tn10 control region's own tetO1 window "
        "(J01830) differs from it at one base",
    frozenset(("GFP", "YFP")):
        "two distinct published Aequorea GFP variants (GFP here is gfpmut2; YFP is "
        "EYFP, a variant_of EGFP): 98.3% identical, neither derived from the other",
}


def load_parts(root: Path = ROOT) -> list[dict]:
    """One dict per canonical part file: name, names (lower-cased name and
    synonyms), type, sequence, features, links, status and sourced."""
    out = []
    for status in ("validated", "candidate"):
        for jf in sorted((root / "parts" / status).glob("*.json")):
            d = json.loads(jf.read_text(encoding="utf-8"))
            feats = d["features"]
            main = next(f for f in feats if "parent" not in f["qualifiers"])
            q = main["qualifiers"]
            name = (q.get("label") or [d["slug"]])[0]
            out.append({
                "slug": d["slug"], "name": name, "status": status,
                "variant_of": {x.strip().lower() for x in q.get("variant_of", [])},
                "names": {n.strip().lower() for n in [name, *q.get("synonym", [])]},
                "names_raw": [n.strip() for n in [name, *q.get("synonym", [])]],
                "synonyms": list(q.get("synonym", [])),
                "type": main["type"], "protein": d["molecule_type"] == "protein",
                "seq": d["sequence"].upper(), "main": main, "features": feats,
                "links": {x.strip().lower() for k in LINK_KEYS for x in q.get(k, [])},
                "sourced": is_sourced(d),
            })
    return out


# ---------------------------------------------------------------- checks
def _name_key(name: str) -> str:
    """A name as a reader would match it: case, spaces and punctuation ignored,
    letters kept (so ``P cat``, ``P-cat`` and ``Pcat`` are one name, while
    ``lacZ`` and ``lacZ-alpha`` stay two)."""
    return "".join(c for c in name.lower() if c.isalnum())


def check_names(parts: list[dict]) -> list[str]:
    owners: dict[str, dict[str, list[str]]] = {}
    for p in parts:
        for n in p["names_raw"]:
            owners.setdefault(_name_key(n), {}).setdefault(p["name"], []).append(n)
    out = []
    for _key, by_part in sorted(owners.items()):
        if len(by_part) < 2:
            continue
        spellings = sorted({n for ns in by_part.values() for n in ns})
        out.append(f"[names] {' / '.join(repr(x) for x in spellings)} is a name or synonym "
                   f"of {len(by_part)} parts: {', '.join(sorted(by_part))}")
    return out


def _declared(a: dict, b: dict) -> bool:
    """Either part's main feature links the other by name, synonym or slug,
    or both are declared variants of the same part."""
    return bool(a["links"] & (b["names"] | {b["slug"].lower()})) \
        or bool(b["links"] & (a["names"] | {a["slug"].lower()})) \
        or bool(a["variant_of"] & b["variant_of"])


def _copies(outer: dict, inner: dict) -> list[int]:
    """Start of every copy of ``inner`` in ``outer`` (both strands for DNA)."""
    so, si = outer["seq"], inner["seq"]
    pats = {si} if inner["protein"] else {si, _rc(si)}
    return sorted(i for i in range(len(so) - len(si) + 1) if so[i:i + len(si)] in pats)


def _child_declares(outer: dict, inner: dict, at: int) -> bool:
    """``outer`` has a sub-feature labelled with ``inner``'s name or synonym
    over at least 80% of the copy of ``inner`` that starts at ``at``."""
    n = len(inner["seq"])
    return any("parent" in f["qualifiers"]
               and (f["qualifiers"].get("label") or [""])[0].strip().lower() in inner["names"]
               and min(f["end"], at + n) - max(f["start"], at) >= 0.8 * n
               for f in outer["features"])


def _aligner(protein: bool) -> PairwiseAligner:
    al = PairwiseAligner()
    al.mode = "local"
    if protein:
        al.substitution_matrix = substitution_matrices.load("BLOSUM62")
        al.open_gap_score, al.extend_gap_score = -11, -1
    else:
        al.match_score, al.mismatch_score = 1, -3
        al.open_gap_score, al.extend_gap_score = -5, -2
    return al


def _kmers(s: str, k: int) -> set[str]:
    return {s[i:i + k] for i in range(len(s) - k + 1)}


def identity_over_shorter(a: str, b: str, protein: bool) -> float:
    """Identities of the best local alignment (both strands for DNA) divided by
    the length of the shorter sequence."""
    short, long_ = sorted((a, b), key=len)
    al = _aligner(protein)
    best = 0
    for s in ([short] if protein else [short, _rc(short)]):
        try:
            aln = al.align(s, long_)[0]
        except (IndexError, OverflowError):
            continue
        best = max(best, aln.counts().identities)
    return best / len(short)


def _best_local(short: str, long_: str, protein: bool) -> tuple[float, float, float]:
    """Best local alignment of ``short`` against ``long_`` (both strands for DNA).

    Returns (fraction of the shorter part aligned, fraction of the longer part
    aligned, identity within the alignment)."""
    al = _aligner(protein)
    best = (0.0, 0.0, 0.0)
    for s in ([short] if protein else [short, _rc(short)]):
        try:
            x = al.align(s, long_)[0]
        except (IndexError, OverflowError):
            continue
        c = x.counts()
        n = c.identities + c.mismatches + c.gaps
        if not n:
            continue
        span_s = int(x.aligned[0][-1][1]) - int(x.aligned[0][0][0])
        span_l = int(x.aligned[1][-1][1]) - int(x.aligned[1][0][0])
        cand = (span_s / len(short), span_l / len(long_), c.identities / n)
        if cand[0] * cand[2] > best[0] * best[2]:
            best = cand
    return best


def check_overlaps(parts: list[dict]) -> list[str]:
    """`duplicate` (identical or >= 98% over the shorter) and `contains`
    (a part's whole sequence inside another) without a declaration."""
    out = []
    k = {False: 12, True: 5}
    kms = {id(p): _kmers(p["seq"], k[p["protein"]]) | (set() if p["protein"]
           else _kmers(_rc(p["seq"]), 12)) for p in parts}
    for a, b in combinations(parts, 2):
        if a["protein"] != b["protein"]:
            continue
        if frozenset((a["name"], b["name"])) in ALLOW_PAIRS:
            continue
        inner, outer = sorted((a, b), key=lambda p: len(p["seq"]))
        si, so = inner["seq"], outer["seq"]
        copies = _copies(outer, inner)
        inside = bool(copies)
        if inside and len(si) < len(so):
            if not (_declared(a, b) or all(_child_declares(outer, inner, at) for at in copies)):
                out.append(f"[contains] {outer['name']} ({len(so)}) holds the whole of "
                           f"{inner['name']} ({len(si)}) and does not declare it")
            continue
        if inside:
            ident = 1.0
        else:
            ki = _kmers(si, k[inner["protein"]])
            if not ki or len(ki & kms[id(outer)]) < 0.5 * len(ki):
                continue
            ident = identity_over_shorter(si, so, inner["protein"])
            if not _declared(a, b) and len(si) < len(so):
                # ... or nearly inside it: the shorter part aligned over nearly
                # all of itself, the longer one keeping bases of its own.
                cov, host, nid = _best_local(si, so, inner["protein"])
                if (nid >= NEAR_IN_IDENTITY and cov >= NEAR_IN_COVERAGE
                        and host <= NEAR_IN_HOST_MAX):
                    if any(_child_declares(outer, inner, at)
                           for at in range(len(so) - len(si) + 1)):
                        continue        # declared by a sub-feature, as `contains` allows
                    out.append(f"[near] {outer['name']} ({len(so)}) holds {cov:.0%} of "
                               f"{inner['name']} ({len(si)}) at {nid:.1%} identity and does "
                               f"not declare it")
                    continue
        if ident >= NEAR_IDENTITY and not _declared(a, b):
            out.append(f"[duplicate] {a['name']} ({len(a['seq'])}) ~ {b['name']} "
                       f"({len(b['seq'])}): {ident:.1%} identical over the shorter, "
                       f"and neither links the other")
    return out


def longest_orf(seq: str) -> int:
    """Length in bp of the longest ATG-initiated open reading frame on either
    strand, stop codon included (or running off the end of the sequence)."""
    stops = {"TAA", "TAG", "TGA"}
    best = 0
    for s in (seq, _rc(seq)):
        for frame in range(3):
            i = frame
            while i + 3 <= len(s):
                if s[i:i + 3] == "ATG":
                    j = i
                    while j + 3 <= len(s) and s[j:j + 3] not in stops:
                        j += 3
                    best = max(best, min(j + 3, len(s)) - i)
                    i = j
                i += 3
    return best


def check_dna_shape(parts: list[dict]) -> list[str]:
    out = []
    for p in parts:
        if p["protein"]:
            continue
        n = len(p["seq"])
        if n < MIN_DNA_BP and p["name"] not in ALLOW_SHORT:
            out.append(f"[short] {p['name']} [{p['type']}] is {n} bp (< {MIN_DNA_BP})")
        if p["type"] not in CODING and p["name"] not in ALLOW_ORF:
            orf = longest_orf(p["seq"])
            if orf >= MIN_ORF_BP and orf >= ORF_FRACTION * n:
                out.append(f"[orf] {p['name']} [{p['type']}, {n} bp] is non-coding but one "
                           f"ORF covers {orf / n:.0%} of it")
    return out


def check_subfeatures(parts: list[dict]) -> list[str]:
    out = []
    for p in parts:
        spans: dict[str, tuple[int, int]] = {}
        for f in p["features"]:
            spans.setdefault((f["qualifiers"].get("label") or [""])[0], (f["start"], f["end"]))
        for f in p["features"]:
            par = (f["qualifiers"].get("parent") or [None])[0]
            if par is None:
                continue
            label = (f["qualifiers"].get("label") or ["?"])[0]
            if par not in spans:
                out.append(f"[subfeature] {p['name']}: {label!r} names parent {par!r}, "
                           f"which is no feature of the part")
            elif not (spans[par][0] <= f["start"] < f["end"] <= spans[par][1]):
                out.append(f"[subfeature] {p['name']}: {label!r} {f['start']}..{f['end']} "
                           f"lies outside its parent {par!r} {spans[par][0]}..{spans[par][1]}")
    return out


def check_manifest(parts: list[dict], root: Path = ROOT) -> list[str]:
    out = []
    want = {p["slug"]: p for p in parts}
    for fname in ("catalog.json", "index.json"):
        listed = {e["slug"]: e for e in json.loads((root / fname).read_text(encoding="utf-8"))["parts"]}
        for slug in sorted(set(want) ^ set(listed)):
            where = "has no part file" if slug in listed else "is missing"
            out.append(f"[manifest] {fname}: {slug} {where}")
        for slug in sorted(set(want) & set(listed)):
            p, e = want[slug], listed[slug]
            for key, val in (("name", p["name"]), ("synonyms", p["synonyms"]),
                             ("status", p["status"]), ("sourced", p["sourced"])):
                if e.get(key, [] if key == "synonyms" else None) != val:
                    out.append(f"[manifest] {fname}: {slug} {key} {e.get(key)!r} != part file {val!r}")
    return out


def check_status(parts: list[dict]) -> list[str]:
    return [f"[status] {p['name']} is validated but unsourced"
            for p in parts if p["status"] == "validated" and not p["sourced"]
            and p["name"] not in GRANDFATHERED_UNSOURCED]


def findings(root: Path = ROOT) -> list[str]:
    parts = load_parts(root)
    return (check_names(parts) + check_overlaps(parts) + check_dna_shape(parts)
            + check_subfeatures(parts) + check_manifest(parts, root) + check_status(parts))


def main() -> int:
    out = findings()
    for line in out:
        print(line)
    n = sum(1 for _ in (ROOT / "parts").glob("*/*.json"))
    print(f"library quality gate: {len(out)} finding(s) over {n} parts")
    return 1 if out else 0


if __name__ == "__main__":
    sys.exit(main())
