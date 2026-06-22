#!/usr/bin/env python3
"""Local sequence-provenance store — the byte-source companion to ``sourcing/incoming/``.

The sequence side of the ``sourcing/`` handoff (``tools/papers.py`` is the claim-evidence
side). A part's sequence must trace to a cited source; when that source is **not publicly
re-fetchable** — a commercial or unpublished **carrier** map (e.g. pDONR221, a kit plasmid)
that contains the part as a sub-region — the carrier is deposited here so the add-part Source
phase can **byte-verify** the part against it. Public NCBI/UniProt accessions are NOT stored
(they are cited and re-fetched on demand by ``source_finder.py``); only what cannot be
re-downloaded lives here.

The store is **gitignored** — carrier maps stay local; only the resulting
``provenance.sequence_source`` string (e.g. ``"pDONR221 positions 1–232 (+ strand)"``) is ever
committed. A personal reference cache, not a redistribution channel.

Reads SnapGene ``.dna``, GenBank ``.gb``/``.gbk``, FASTA ``.fa``/``.fasta``, and raw
``.txt``/``.seq`` (the formats a human actually drops). Keyed by accession (if any) else a
slug of the carrier name.

Layout (all under ``sourcing/sequences/``, gitignored):
    acc-<accession>.<ext> / name-<slug>.<ext>   deposited carrier map
    index.json                                  manifest: key -> {name, accession, file, len, ...}

Commands:
    classify <file>                             print role (carrier | standalone) + summary
    add <file> --name pDONR221 [--accession ..] [--move]   deposit a carrier map
    resolve --name pDONR221 [--json]            print local path (source_finder reads this)
    list                                        what's in the store
    reindex                                     rebuild index.json from disk
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
STORE = ROOT / "sourcing" / "sequences"
INDEX = STORE / "index.json"

# extension -> Biopython SeqIO format (raw handled specially)
SEQIO_FORMATS = {
    ".dna": "snapgene",
    ".gb": "genbank", ".gbk": "genbank", ".genbank": "genbank",
    ".fa": "fasta", ".fasta": "fasta", ".fna": "fasta",
}
RAW_EXTS = {".txt", ".seq"}
KNOWN_EXTS = set(SEQIO_FORMATS) | RAW_EXTS


# ---------- reading ----------

def read_sequence_file(path: Path) -> dict:
    """Parse a dropped sequence file into a uniform dict:
    ``{name, sequence, topology, n_features, fmt, length}``. Raises ``ValueError`` on an
    unknown extension or unparseable content."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in RAW_EXTS or ext not in KNOWN_EXTS:
        # raw nucleotides: strip everything non-letter, uppercase
        raw = re.sub(r"[^A-Za-z]", "", path.read_text(encoding="utf-8", errors="ignore"))
        if not raw:
            raise ValueError(f"no sequence content in {path.name}")
        return {"name": path.stem, "sequence": raw.upper(), "topology": "linear",
                "n_features": 0, "fmt": "raw", "length": len(raw)}
    from Bio import SeqIO
    fmt = SEQIO_FORMATS[ext]
    rec = SeqIO.read(str(path), fmt)
    return {
        "name": rec.name or rec.id or path.stem,
        "sequence": str(rec.seq).upper(),
        "topology": (rec.annotations.get("topology") or "linear").lower(),
        "n_features": len(rec.features),
        "fmt": fmt,
        "length": len(rec.seq),
    }


def classify_role(parsed: dict) -> str:
    """Classify a dropped sequence by ROLE, not extension (the /incoming distinction):

    * **carrier** — an annotated multi-feature map or a circular plasmid that *contains* a
      part as a sub-region. It is dropped to byte-verify an EXISTING part; never /add-part it.
    * **standalone** — a bare sequence (typically a featureless FASTA) meant to BE a new part.
    """
    if parsed.get("topology") == "circular" or parsed.get("n_features", 0) >= 2:
        return "carrier"
    return "standalone"


# ---------- keys / index ----------

def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (s or "").lower()).strip("_")


def key_for(name: str | None, accession: str | None) -> str:
    if accession:
        return f"acc-{_slug(accession)}"
    if name:
        return f"name-{_slug(name)}"
    raise ValueError("need --name or --accession to key the carrier")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_index() -> dict:
    if INDEX.exists():
        return json.loads(INDEX.read_text())
    return {"sequences": []}


def save_index(idx: dict) -> None:
    STORE.mkdir(parents=True, exist_ok=True)
    idx["sequences"].sort(key=lambda s: s.get("key", ""))
    INDEX.write_text(json.dumps(idx, indent=2) + "\n")


# ---------- commands ----------

def cmd_classify(args) -> int:
    try:
        p = read_sequence_file(Path(args.file).expanduser())
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"error": str(exc)}))
        return 1
    role = classify_role(p)
    out = {"role": role, "name": p["name"], "length": p["length"],
           "topology": p["topology"], "n_features": p["n_features"], "fmt": p["fmt"],
           "hint": ("byte-verify an existing part against this carrier (do NOT /add-part it); "
                    "use source_finder --carrier" if role == "carrier"
                    else "a bare sequence meant to be a new part -> /add-part")}
    print(json.dumps(out, indent=2))
    return 0


def cmd_add(args) -> int:
    src = Path(args.file).expanduser()
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 1
    try:
        parsed = read_sequence_file(src)
    except Exception as exc:  # noqa: BLE001
        print(f"error: cannot parse {src.name}: {exc}", file=sys.stderr)
        return 1
    name = args.name or parsed["name"]
    accession = args.accession
    try:
        key = key_for(name, accession)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    STORE.mkdir(parents=True, exist_ok=True)
    dest = STORE / f"{key}{src.suffix.lower()}"
    shutil.copyfile(src, dest)

    idx = load_index()
    idx["sequences"] = [s for s in idx["sequences"] if s.get("key") != key]
    idx["sequences"].append({
        "key": key, "name": name, "accession": accession,
        "file": dest.name, "fmt": parsed["fmt"], "length": parsed["length"],
        "topology": parsed["topology"], "n_features": parsed["n_features"],
        "role": classify_role(parsed), "sha256": sha256(dest), "added_utc": _now(),
    })
    save_index(idx)

    moved = False
    if getattr(args, "move", False):
        try:
            if src.resolve() != dest.resolve():
                src.unlink()
                moved = True
        except OSError:
            pass
    print(f"added {dest.name}  ({parsed['length']} bp, {parsed['n_features']} features, "
          f"{classify_role(parsed)})" + (" — removed source from incoming/" if moved else ""))
    return 0


def _resolve(name: str | None, accession: str | None) -> dict | None:
    nslug = _slug(name) if name else None
    aslug = _slug(accession) if accession else None
    for s in load_index().get("sequences", []):
        if aslug and s.get("accession") and _slug(s["accession"]) == aslug:
            return s
        if nslug and _slug(s.get("name", "")) == nslug:
            return s
    return None


def cmd_resolve(args) -> int:
    s = _resolve(args.name, args.accession)
    if not s:
        if args.json:
            print(json.dumps({"found": False}))
        return 1
    path = STORE / s["file"]
    if args.json:
        print(json.dumps({"found": True, "path": str(path), "name": s["name"],
                          "accession": s.get("accession"), "length": s["length"],
                          "topology": s["topology"]}))
    else:
        print(path)
    return 0


def cmd_list(args) -> int:
    seqs = load_index().get("sequences", [])
    if not seqs:
        print("sequence store is empty")
        return 0
    for s in seqs:
        acc = f" [{s['accession']}]" if s.get("accession") else ""
        print(f"  {s['name']}{acc} — {s['length']} bp, {s['n_features']} feat, "
              f"{s['role']} ({s['file']})")
    return 0


def cmd_reindex(args) -> int:
    if not STORE.exists():
        print("no store directory yet")
        return 0
    existing = {s["key"]: s for s in load_index().get("sequences", [])}
    rebuilt = []
    for f in sorted(STORE.iterdir()):
        if f.suffix.lower() not in KNOWN_EXTS:
            continue
        key = f.stem
        prev = existing.get(key, {})
        try:
            parsed = read_sequence_file(f)
        except Exception:  # noqa: BLE001
            continue
        rebuilt.append({"key": key, "name": prev.get("name", parsed["name"]),
                        "accession": prev.get("accession"), "file": f.name,
                        "fmt": parsed["fmt"], "length": parsed["length"],
                        "topology": parsed["topology"], "n_features": parsed["n_features"],
                        "role": classify_role(parsed), "sha256": sha256(f),
                        "added_utc": prev.get("added_utc", _now())})
    save_index({"sequences": rebuilt})
    print(f"reindexed {len(rebuilt)} carrier(s)")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("classify", help="print role (carrier | standalone) + summary")
    c.add_argument("file")
    c.set_defaults(func=cmd_classify)

    a = sub.add_parser("add", help="deposit a non-refetchable carrier map")
    a.add_argument("file")
    a.add_argument("--name", help="carrier name (e.g. pDONR221); defaults to the record name")
    a.add_argument("--accession", help="accession if it has one (keys the entry)")
    a.add_argument("--move", action="store_true", help="remove the source from incoming/ once stored")
    a.set_defaults(func=cmd_add)

    r = sub.add_parser("resolve", help="print the local path of a stored carrier")
    r.add_argument("--name")
    r.add_argument("--accession")
    r.add_argument("--json", action="store_true")
    r.set_defaults(func=cmd_resolve)

    sub.add_parser("list", help="list stored carriers").set_defaults(func=cmd_list)
    sub.add_parser("reindex", help="rebuild index.json from disk").set_defaults(func=cmd_reindex)

    args = ap.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()
