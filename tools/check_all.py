#!/usr/bin/env python3
"""Run the whole consistency gate suite in one command — the checks CI runs.

`passes locally` should mean `passes CI`. Run before committing:
    python tools/check_all.py

Mirrors ``.github/workflows/validate.yml``: the content / requests / link guards,
JSON-schema validation, regeneration of every generated artifact (``.gb``,
``catalog.json``, the RDF) with a staleness check, the SHACL shapes, and the test
suite. This is the single definition of "the gates" — keep CI in step with it.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
GENERATED = ["parts", "catalog.json", "catalog.ttl", "catalog.jsonld",
             "tools/catalog_context.jsonld"]


def run(label: str, cmd: list[str]) -> bool:
    print(f"\n=== {label} ===", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode == 0


def main() -> int:
    ok = True
    for label, script in [
        ("content guard", "check_content.py"),
        ("requests guard", "check_requests.py"),
        ("link guard", "check_links.py"),
        ("schema validation", "validate_parts.py"),
    ]:
        ok &= run(label, [PY, f"tools/{script}"])

    # regenerate every generated artifact, then assert nothing drifted
    run("regenerate .gb", [PY, "tools/build_gb.py"])
    run("rebuild catalog.json + site", [PY, "tools/build_catalog.py"])
    run("rebuild RDF", [PY, "tools/build_rdf.py"])
    print("\n=== generated artifacts up to date ===", flush=True)
    if subprocess.run(["git", "diff", "--quiet", "--", *GENERATED], cwd=ROOT).returncode == 0:
        print("OK")
    else:
        print("STALE — commit the regenerated files:")
        subprocess.run(["git", "diff", "--stat", "--", *GENERATED], cwd=ROOT)
        ok = False

    ok &= run("SHACL shapes", ["pyshacl", "-s", "tools/shapes.ttl", "-i", "rdfs", "catalog.ttl"])
    ok &= run("tests", [PY, "-m", "pytest", "tests/", "-q"])

    print("\n" + ("ALL GATES PASSED" if ok else "SOME GATES FAILED"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
