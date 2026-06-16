"""The vendored part-view widget bundle must carry provenance and match its hash.

``docs/assets/seqmake-part-view.js`` is an opaque, minified bundle auto-copied
from its source repo — we don't review it by hand. Instead the copy step records
a provenance sidecar (source / version / commit / built / sha256) so each update
is auditable from the diff, and CI verifies the committed bundle is exactly what
the sidecar claims (catching a partial/corrupted copy, or a forgotten sidecar
update). See CONTRIBUTING.md (interactive viewer)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUNDLE = ROOT / "docs" / "assets" / "seqmake-part-view.js"
SIDECAR = ROOT / "docs" / "assets" / "seqmake-part-view.version.json"


def test_sidecar_present_with_required_fields():
    assert SIDECAR.exists(), "missing provenance sidecar for the vendored bundle"
    meta = json.loads(SIDECAR.read_text(encoding="utf-8"))
    for k in ("source", "version", "commit", "built", "sha256"):
        assert k in meta, f"sidecar is missing '{k}'"


def test_bundle_matches_recorded_hash():
    meta = json.loads(SIDECAR.read_text(encoding="utf-8"))
    actual = hashlib.sha256(BUNDLE.read_bytes()).hexdigest()
    assert actual == meta["sha256"], (
        "vendored bundle sha256 does not match its sidecar — re-run the copy step "
        "so the sidecar records this build (or the copy was partial/corrupted)")
