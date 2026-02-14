"""
Tests for the topic reference extractor.

These tests verify that:
- <xref> elements generate edges
- <image> elements generate edges
- <object> elements generate edges using the data attribute
- XML namespaces are handled correctly
- Invalid XML fails cleanly
- Returned edges conform to the discovery relationship schema
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.discovery.extractors.topic_refs import (
    extract_topic_references,
)
from dita_package_processor.discovery.graph import DependencyEdge


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Core extraction behavior
# ---------------------------------------------------------------------------


def test_extracts_xref_image_and_object(tmp_path: Path) -> None:
    topic_file = tmp_path / "test.dita"

    _write_file(
        topic_file,
        """<?xml version="1.0" encoding="UTF-8"?>
<concept id="c1">
  <conbody>
    <p>
      <xref href="topics/other.dita"/>
      <image href="media/image.png"/>
      <object data="media/video.mp4"/>
    </p>
  </conbody>
</concept>
""",
    )

    edges = extract_topic_references(topic_file)

    assert len(edges) == 3

    assert edges[0] == DependencyEdge(
        source=topic_file.as_posix(),
        target="topics/other.dita",
        edge_type="xref",
        pattern_id="dita_topic_xref",
    )

    assert edges[1] == DependencyEdge(
        source=topic_file.as_posix(),
        target="media/image.png",
        edge_type="image",
        pattern_id="dita_topic_image",
    )

    assert edges[2] == DependencyEdge(
        source=topic_file.as_posix(),
        target="media/video.mp4",
        edge_type="object",
        pattern_id="dita_topic_object",
    )


# ---------------------------------------------------------------------------
# Namespace handling
# ---------------------------------------------------------------------------


def test_handles_namespaced_elements(tmp_path: Path) -> None:
    topic_file = tmp_path / "namespaced.dita"

    _write_file(
        topic_file,
        """<?xml version="1.0" encoding="UTF-8"?>
<concept xmlns="http://dita.oasis-open.org/architecture/2005/" id="c1">
  <conbody>
    <xref href="x.dita"/>
    <image href="i.png"/>
    <object data="o.bin"/>
  </conbody>
</concept>
""",
    )

    edges = extract_topic_references(topic_file)

    assert len(edges) == 3

    assert edges[0].source == topic_file.as_posix()
    assert edges[0].target == "x.dita"
    assert edges[0].edge_type == "xref"

    assert edges[1].source == topic_file.as_posix()
    assert edges[1].target == "i.png"
    assert edges[1].edge_type == "image"

    assert edges[2].source == topic_file.as_posix()
    assert edges[2].target == "o.bin"
    assert edges[2].edge_type == "object"


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_missing_file_raises_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.dita"

    with pytest.raises(FileNotFoundError):
        extract_topic_references(missing)


def test_invalid_xml_raises_error(tmp_path: Path) -> None:
    topic_file = tmp_path / "bad.dita"

    # Malformed XML: mismatched tags
    _write_file(topic_file, "<concept><xref></concept>")

    with pytest.raises(ValueError):
        extract_topic_references(topic_file)