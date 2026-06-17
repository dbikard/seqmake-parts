"""The Markdown relative-link guard (tools/check_links.py)."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

from check_links import broken_links, tracked_md  # noqa: E402


def test_valid_relative_link_passes(tmp_path):
    (tmp_path / "target.md").write_text("hi", encoding="utf-8")
    md = tmp_path / "doc.md"
    md.write_text("see [the target](target.md) and [anchor](#x) and [web](https://x.io)",
                  encoding="utf-8")
    assert broken_links(md) == []


def test_broken_relative_link_is_flagged(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("see [gone](does_not_exist.md)", encoding="utf-8")
    assert broken_links(md)


def test_anchor_on_existing_file_ok(tmp_path):
    (tmp_path / "RDF.md").write_text("x", encoding="utf-8")
    md = tmp_path / "doc.md"
    md.write_text("[model](RDF.md#the-model)", encoding="utf-8")
    assert broken_links(md) == []


def test_link_inside_code_fence_is_ignored(tmp_path):
    md = tmp_path / "doc.md"
    md.write_text("```\n[example](nonexistent.md)\n```\n", encoding="utf-8")
    assert broken_links(md) == []


def test_repo_markdown_links_all_resolve():
    """Every tracked Markdown file's relative links point at a real path."""
    bad = {md.relative_to(ROOT).as_posix(): broken_links(md)
           for md in tracked_md() if broken_links(md)}
    assert not bad, f"broken links: {bad}"
