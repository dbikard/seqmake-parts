#!/usr/bin/env python3
"""Project the catalog into RDF (SBOL3 + Sequence Ontology + SBO) -- the
semantic-web sibling of ``build_catalog.py``.

This is a *generated* artifact, never hand-authored: it reuses the exact same
parse as the manifest builder (``parse_part`` / ``_crosslink_parts`` from
``build_catalog.py``) and emits two files at the repo root:

    catalog.ttl      Turtle  (human-readable, the canonical RDF serialization)
    catalog.jsonld   JSON-LD (the same graph, for JS / JSON-LD tooling)

Every part becomes an ``sbol:Component`` with its SO role, sequence, sub-features
(as ``sbol:SequenceFeature`` + ``sbol:Range``), citations, collections and
curation status; promoter<->TF regulation becomes an ``sbol:Interaction`` (SBO
inhibition/stimulation) plus a denormalized ``cat:regulatedBy`` shortcut.

The output is fully deterministic (no blank nodes; sorted serialization) so CI
can guard that the committed files are up to date, exactly as it does for
``catalog.json``.

Usage:
    python tools/build_rdf.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS, XSD

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_catalog import (  # noqa: E402
    CANDIDATE_DIR,
    ROOT,
    VALIDATED_DIR,
    _crosslink_parts,
    parse_part,
)

# --------------------------------------------------------------------------
# Namespaces
# --------------------------------------------------------------------------
SBOL = Namespace("http://sbols.org/v3#")
PROV = Namespace("http://www.w3.org/ns/prov#")
# Stable, host-independent identity via a w3id.org redirect (see w3id/seqmake/).
# These IRIs are the catalog's permanent names; w3id.org/seqmake/parts -> the current
# GitHub Pages site, so the hosting (and repo name) can change without breaking
# any IRI that has been published or cited.
BASE = Namespace("https://w3id.org/seqmake/parts/")
PART = Namespace("https://w3id.org/seqmake/parts/part/")
COLL = Namespace("https://w3id.org/seqmake/parts/collection/")
CAT = Namespace("https://w3id.org/seqmake/parts/ns#")
PUBMED = Namespace("https://identifiers.org/pubmed:")
SO_NS = Namespace("https://identifiers.org/SO:")
SBO = Namespace("https://identifiers.org/SBO:")

# Term IRIs pinned from the official pySBOL3 constants (sbol3.SBO_DNA, ...), so
# they cannot drift from the SBOL3 / SBO / EDAM specs. Verified 2026-06.
SBO_DNA = URIRef("https://identifiers.org/SBO:0000251")
SBO_PROTEIN = URIRef("https://identifiers.org/SBO:0000252")
EDAM_DNA = URIRef("https://identifiers.org/edam:format_1207")  # IUPAC nucleotide
EDAM_PROTEIN = URIRef("https://identifiers.org/edam:format_1208")  # IUPAC protein
SBO_INHIBITION = URIRef("https://identifiers.org/SBO:0000169")
SBO_STIMULATION = URIRef("https://identifiers.org/SBO:0000170")
SBO_INHIBITOR = URIRef("https://identifiers.org/SBO:0000020")
SBO_INHIBITED = URIRef("https://identifiers.org/SBO:0000642")
SBO_STIMULATOR = URIRef("https://identifiers.org/SBO:0000459")
SBO_STIMULATED = URIRef("https://identifiers.org/SBO:0000643")

SO_OPERATOR = "SO:0000057"

# Promoters whose cognate regulator *activates* rather than represses. Phase 1
# polarity is a heuristic (default: repression); refined into a provenance-bearing
# functional claim in Phase 2. Matched case-insensitively against the TF name.
KNOWN_ACTIVATORS = {
    "arac", "chnr", "xyls", "alks", "nahr", "luxr", "rhas", "rhar", "nimr",
}


def _slug_token(s: str) -> str:
    """A URI-safe token from an arbitrary name (for deterministic child URIs)."""
    return "".join(c if c.isalnum() else "_" for c in s)


def so_uri(so_term: str | None) -> URIRef | None:
    """``"SO:0000167"`` -> the identifiers.org SO term URI."""
    if not so_term or not so_term.startswith("SO:"):
        return None
    return URIRef(str(SO_NS) + so_term.split(":", 1)[1])


def _pub_uri(ref: dict) -> URIRef | None:
    if ref.get("pmid"):
        return URIRef(str(PUBMED) + ref["pmid"])
    if ref.get("doi"):
        return URIRef("https://doi.org/" + ref["doi"])
    if ref.get("url"):
        return URIRef(ref["url"])
    return None


def _ref_uris(part: dict) -> list[URIRef]:
    out = []
    for r in part["references"]:
        u = _pub_uri(r)
        if u is not None:
            out.append(u)
    return out


def _cited_uris(indices: list[int], refs: list[dict]) -> list[URIRef]:
    out = []
    for i in indices:
        if 1 <= i <= len(refs):
            u = _pub_uri(refs[i - 1])
            if u is not None:
                out.append(u)
    return out


def add_part(g: Graph, part: dict, by_slug: dict[str, dict]) -> None:
    """Emit one part's structural triples (Component + Sequence + features +
    citations + collections + curation), minus regulation (added separately so
    the whole graph's parts exist first)."""
    p = PART[part["slug"]]
    g.add((p, RDF.type, SBOL.Component))
    g.add((p, SBOL.hasNamespace, BASE[""]))
    g.add((p, SBOL.displayId, Literal(part["slug"])))
    g.add((p, DCTERMS.title, Literal(part["name"])))
    g.add((p, RDFS.label, Literal(part["name"])))
    if part.get("description"):
        g.add((p, DCTERMS.description, Literal(part["description"])))
    g.add((p, SBOL.type, SBO_PROTEIN if part["kind"] == "protein" else SBO_DNA))
    role = so_uri(part.get("so_term"))
    if role is not None:
        g.add((p, SBOL.role, role))
    for syn in part["synonyms"]:
        g.add((p, SKOS.altLabel, Literal(syn)))
    # Curation + provenance: status is the trust signal; the WIP/AI caveat is a
    # property of the whole catalog (see README), surfaced per part here.
    g.add((p, CAT.curationStatus, Literal(part["status"])))
    g.add((p, CAT.slug, Literal(part["slug"])))
    g.add((p, CAT.documented, Literal(part["documented"], datatype=XSD.boolean)))
    if part.get("source_accession"):
        acc = part["source_accession"]
        g.add((p, CAT.sourceAccession, Literal(acc)))
        # Defer protein biology to the authoritative source: a first-class,
        # federatable link (UniProt's purl is its SPARQL entity IRI) rather than
        # re-annotating domains/active sites here.
        db, _, ident = acc.partition(":")
        if ident and db.lower() == "uniprot":
            g.add((p, RDFS.seeAlso, URIRef(f"http://purl.uniprot.org/uniprot/{ident}")))
        elif ident and db.lower() in ("genbank", "nuccore", "insdc"):
            g.add((p, RDFS.seeAlso,
                   URIRef(f"https://www.ncbi.nlm.nih.gov/nuccore/{ident}")))
        elif ident and db.lower() == "ncbi":
            g.add((p, RDFS.seeAlso,
                   URIRef(f"https://www.ncbi.nlm.nih.gov/protein/{ident}")))

    # Sequence
    seq = PART[part["slug"] + "_sequence"]
    g.add((seq, RDF.type, SBOL.Sequence))
    g.add((seq, SBOL.hasNamespace, BASE[""]))
    g.add((seq, SBOL.displayId, Literal(part["slug"] + "_sequence")))
    g.add((seq, SBOL.encoding,
           EDAM_PROTEIN if part["kind"] == "protein" else EDAM_DNA))
    g.add((seq, SBOL.elements, Literal(part["_seq"])))
    g.add((p, SBOL.hasSequence, seq))

    # Citations on the part
    for u in _ref_uris(part):
        g.add((p, DCTERMS.references, u))

    # Sub-features -> SequenceFeature + Range
    for i, c in enumerate(part["children"]):
        f = PART[f"{part['slug']}_feature_{i}"]
        g.add((p, SBOL.hasFeature, f))
        g.add((f, RDF.type, SBOL.SequenceFeature))
        g.add((f, SBOL.displayId, Literal(f"{part['slug']}_feature_{i}")))
        if c.get("label"):
            g.add((f, DCTERMS.title, Literal(c["label"])))
        crole = so_uri(c.get("so_term"))
        if crole is not None:
            g.add((f, SBOL.role, crole))
        rng = PART[f"{part['slug']}_feature_{i}_range"]
        g.add((f, SBOL.hasLocation, rng))
        g.add((rng, RDF.type, SBOL.Range))
        g.add((rng, SBOL.sequence, seq))
        g.add((rng, SBOL.start, Literal(c["start"] + 1, datatype=XSD.integer)))
        g.add((rng, SBOL.end, Literal(c["end"], datatype=XSD.integer)))
        g.add((rng, SBOL.orientation,
               SBOL.inline if c["strand"] == 1 else SBOL.reverseComplement))
        for u in _cited_uris(c.get("citations", []), part["references"]):
            g.add((f, DCTERMS.references, u))


def _operator_feature(part: dict) -> URIRef | None:
    """The promoter's operator sub-feature URI (the natural inhibited/activated
    target), if it has one."""
    for i, c in enumerate(part["children"]):
        if c.get("so_term") == SO_OPERATOR:
            return PART[f"{part['slug']}_feature_{i}"]
    return None


def add_regulation(g: Graph, part: dict, by_slug: dict[str, dict],
                   log: list[str]) -> None:
    """Emit promoter<->TF regulation: the SBOL3 Interaction model (when the TF is
    a catalog part) plus the denormalized ``cat:regulatedBy`` shortcut (always).
    ``regulated_by`` is the resolved list built by ``_crosslink_parts``."""
    p = PART[part["slug"]]
    target = None  # operator feature, resolved lazily
    for rb in part.get("regulated_by", []):
        tf_slug = rb.get("slug")
        if tf_slug:
            tf = PART[tf_slug]
            g.add((p, CAT.regulatedBy, tf))
            g.add((tf, CAT.regulates, p))
        else:
            # Unresolved name (TF not in the catalog): shortcut as a literal only.
            g.add((p, CAT.regulatedByName, Literal(rb["name"])))
            continue

        # Full SBOL3 Interaction needs a Feature of the promoter as the target.
        if target is None:
            target = _operator_feature(part)
        if target is None:
            # No operator annotated: fall back to a whole-part feature so the
            # Interaction is still structurally valid.
            target = PART[f"{part['slug']}_regulated_region"]
            g.add((p, SBOL.hasFeature, target))
            g.add((target, RDF.type, SBOL.SequenceFeature))
            g.add((target, SBOL.displayId,
                   Literal(f"{part['slug']}_regulated_region")))
            role = so_uri(part.get("so_term"))
            if role is not None:
                g.add((target, SBOL.role, role))

        activator = rb["name"].lower() in KNOWN_ACTIVATORS
        itype = SBO_STIMULATION if activator else SBO_INHIBITION
        agent_role = SBO_STIMULATOR if activator else SBO_INHIBITOR
        target_role = SBO_STIMULATED if activator else SBO_INHIBITED
        log.append(f"  {part['slug']} {'<-activated-by' if activator else '<-repressed-by'} {rb['name']}")

        tok = _slug_token(tf_slug)
        sub = PART[f"{part['slug']}_sub_{tok}"]
        g.add((p, SBOL.hasFeature, sub))
        g.add((sub, RDF.type, SBOL.SubComponent))
        g.add((sub, SBOL.displayId, Literal(f"{part['slug']}_sub_{tok}")))
        g.add((sub, SBOL.instanceOf, tf))

        inter = PART[f"{part['slug']}_interaction_{tok}"]
        g.add((p, SBOL.hasInteraction, inter))
        g.add((inter, RDF.type, SBOL.Interaction))
        g.add((inter, SBOL.displayId, Literal(f"{part['slug']}_interaction_{tok}")))
        g.add((inter, SBOL.type, itype))

        p_agent = PART[f"{part['slug']}_interaction_{tok}_p_agent"]
        p_target = PART[f"{part['slug']}_interaction_{tok}_p_target"]
        g.add((inter, SBOL.hasParticipation, p_agent))
        g.add((inter, SBOL.hasParticipation, p_target))
        g.add((p_agent, RDF.type, SBOL.Participation))
        g.add((p_agent, SBOL.role, agent_role))
        g.add((p_agent, SBOL.participant, sub))
        g.add((p_target, RDF.type, SBOL.Participation))
        g.add((p_target, SBOL.role, target_role))
        g.add((p_target, SBOL.participant, target))


def _claim_source_uri(source: dict) -> URIRef | None:
    if source.get("pmid"):
        return URIRef(str(PUBMED) + source["pmid"])
    if source.get("doi"):
        return URIRef("https://doi.org/" + source["doi"])
    if source.get("url"):
        return URIRef(source["url"])
    return None


def add_functional_claims(g: Graph, part: dict) -> int:
    """Project a part's functional_claims (from its canonical JSON) into the graph
    in the nanopublication shape: each claim is an assertion node carrying its own
    source + extraction provenance + confidence + review status, so the knowledge
    base self-describes its trust. Returns the number of claims emitted."""
    json_path = ROOT / "parts" / part["status"] / f"{part['slug']}.json"
    if not json_path.exists():
        return 0
    claims = json.loads(json_path.read_text(encoding="utf-8")).get("functional_claims", [])
    p = PART[part["slug"]]
    for c in claims:
        cu = PART[f"{part['slug']}_claim_{c['id']}"]
        g.add((p, CAT.hasFunctionalClaim, cu))
        g.add((cu, RDF.type, CAT.FunctionalClaim))
        g.add((cu, CAT.claimType, Literal(c["type"])))
        g.add((cu, RDFS.label, Literal(c["label"])))
        g.add((cu, CAT.confidence, Literal(c["confidence"])))
        g.add((cu, CAT.reviewStatus, Literal(c["review_status"])))
        val = c.get("value") or {}
        # Lossless value + typed convenience predicates for the common kinds.
        g.add((cu, CAT.claimValue, Literal(json.dumps(val, sort_keys=True))))
        if c["type"] in ("repression_dynamic_range", "induction_dynamic_range") \
                and isinstance(val.get("fold"), (int, float)):
            g.add((cu, CAT.foldChange, Literal(val["fold"], datatype=XSD.decimal)))
        if val.get("inducer"):
            g.add((cu, CAT.inducer, Literal(val["inducer"])))
        if val.get("regulation"):
            g.add((cu, CAT.regulation, Literal(val["regulation"])))
        # Assertion provenance (the nanopublication idea, as plain PROV-O), with
        # granular in-source locators (a quote and/or figure/table/page) so a
        # reviewer can find the evidence, not just the paper.
        source = c.get("source") or {}
        src = _claim_source_uri(source)
        if src is not None:
            g.add((cu, DCTERMS.references, src))
            g.add((cu, PROV.wasDerivedFrom, src))
        if source.get("quote"):
            g.add((cu, CAT.sourceQuote, Literal(source["quote"])))
        if source.get("quote_source"):
            g.add((cu, CAT.sourceQuoteFrom, Literal(source["quote_source"])))
        for key, pred in (("figure", CAT.sourceFigure), ("table", CAT.sourceTable),
                          ("page", CAT.sourcePage), ("section", CAT.sourceSection)):
            if source.get(key):
                g.add((cu, pred, Literal(source[key])))
        prov = c.get("provenance") or {}
        act = PART[f"{part['slug']}_claim_{c['id']}_provenance"]
        g.add((cu, PROV.wasGeneratedBy, act))
        g.add((act, RDF.type, PROV.Activity))
        for key, pred in (("method", CAT.method), ("agent", CAT.agent),
                          ("from", CAT.fromDoc)):
            if prov.get(key):
                g.add((act, pred, Literal(prov[key])))
        if c.get("supersedes"):
            g.add((cu, CAT.supersedes,
                   PART[f"{part['slug']}_claim_{c['supersedes']}"]))
    return len(claims)


def add_collections(g: Graph, parts: list[dict], coll_meta: dict) -> None:
    groups: dict[str, list[dict]] = {}
    for p in parts:
        for cid in p.get("collections", []):
            groups.setdefault(cid, []).append(p)
    for cid, members in sorted(groups.items()):
        c = COLL[cid]
        meta = coll_meta.get(cid) or {}
        g.add((c, RDF.type, SBOL.Collection))
        g.add((c, SBOL.hasNamespace, BASE[""]))
        g.add((c, SBOL.displayId, Literal(cid)))
        g.add((c, DCTERMS.title,
               Literal(meta.get("name") or cid.replace("-", " ").capitalize())))
        if meta.get("description"):
            g.add((c, DCTERMS.description, Literal(meta["description"])))
        for m in sorted(members, key=lambda x: x["slug"]):
            g.add((c, SBOL.member, PART[m["slug"]]))


def _bind(g: Graph) -> None:
    g.bind("sbol", SBOL)
    g.bind("so", SO_NS)
    g.bind("sbo", SBO)
    g.bind("dcterms", DCTERMS)
    g.bind("skos", SKOS)
    g.bind("prov", PROV)
    g.bind("cat", CAT)
    g.bind("part", PART)
    g.bind("collection", COLL)
    g.bind("pubmed", PUBMED)


def part_turtle(part: dict, by_slug: dict[str, dict]) -> str:
    """Turtle for a single part's subgraph (Component + sequence + features +
    regulation + functional claims) -- the per-part RDF download on its page."""
    g = Graph()
    _bind(g)
    add_part(g, part, by_slug)
    add_regulation(g, part, by_slug, [])
    add_functional_claims(g, part)
    return g.serialize(format="turtle")


def build_graph(parts: list[dict], coll_meta: dict) -> Graph:
    g = Graph()
    _bind(g)

    by_slug = {p["slug"]: p for p in parts}
    for p in parts:
        add_part(g, p, by_slug)
    log: list[str] = []
    for p in parts:
        add_regulation(g, p, by_slug, log)
    n_claims = sum(add_functional_claims(g, p) for p in parts)
    add_collections(g, parts, coll_meta)
    if n_claims:
        print(f"functional claims projected: {n_claims}")
    if log:
        print("regulation interactions (Phase 1 polarity is heuristic):")
        for line in sorted(log):
            print(line)
    return g


# JSON-LD context: maps the SBOL/SO/SBO/Dublin-Core/cat IRIs to short keys so
# catalog.jsonld is compact and readable. Written standalone to
# tools/catalog_context.jsonld too.
JSONLD_CONTEXT = {
    "sbol": str(SBOL),
    "so": str(SO_NS),
    "sbo": str(SBO),
    "dcterms": str(DCTERMS),
    "skos": str(SKOS),
    "prov": str(PROV),
    "cat": str(CAT),
    "part": str(PART),
    "collection": str(COLL),
    "pubmed": str(PUBMED),
    "rdfs": str(RDFS),
}


def _write_jsonld(g: Graph, path: Path) -> None:
    """Serialize to JSON-LD, then normalize (sort @graph by @id, sort keys) so
    the output is byte-stable across runs for the CI staleness guard."""
    data = g.serialize(format="json-ld", context=JSONLD_CONTEXT, auto_compact=True)
    obj = json.loads(data)
    if isinstance(obj, dict) and isinstance(obj.get("@graph"), list):
        obj["@graph"].sort(key=lambda n: str(n.get("@id", "")))
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def load_graph() -> tuple[Graph, list[dict]]:
    """Parse every part (validated + candidate), cross-link, and build the RDF
    graph. Shared by ``main`` and the tests."""
    parts = []
    for status_dir in (VALIDATED_DIR, CANDIDATE_DIR):
        for gb in sorted(status_dir.glob("*.gb")):
            p = parse_part(gb)
            if p is not None:
                parts.append(p)
    parts.sort(key=lambda x: x["slug"])
    _crosslink_parts(parts)

    coll_file = ROOT / "collections.json"
    coll_meta = json.loads(coll_file.read_text(encoding="utf-8")) \
        if coll_file.exists() else {}
    return build_graph(parts, coll_meta), parts


def main() -> None:
    g, parts = load_graph()

    (ROOT / "catalog.ttl").write_text(
        g.serialize(format="turtle"), encoding="utf-8")
    _write_jsonld(g, ROOT / "catalog.jsonld")
    (Path(__file__).resolve().parent / "catalog_context.jsonld").write_text(
        json.dumps({"@context": JSONLD_CONTEXT}, indent=2) + "\n", encoding="utf-8")

    print(f"rdf: {len(parts)} parts -> {len(g)} triples "
          f"(catalog.ttl + catalog.jsonld)")


if __name__ == "__main__":
    main()
