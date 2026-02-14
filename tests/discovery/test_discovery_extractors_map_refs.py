"""
Tests for the map reference extractor.

These tests verify that:
- <mapref> elements generate edges
- <topicref> elements generate edges
- XML namespaces are handled
- Invalid XML fails cleanly
- Returned edges match the discovery relationship schema
"""

from __future__ import annotations

from pathlib import Path

import pytest

from dita_package_processor.discovery.extractors.map_refs import extract_map_references
from dita_package_processor.discovery.graph import DependencyEdge


def _write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Core extraction behavior
# ---------------------------------------------------------------------------


def test_extracts_mapref_and_topicref(tmp_path: Path) -> None:
    map_file = tmp_path / "test.ditamap"

    _write_file(
        map_file,
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
  <mapref href="Main.ditamap"/>
  <topicref href="topics/a.dita"/>
</map>
""",
    )

    edges = extract_map_references(map_file)

    assert len(edges) == 2

    expected = [
        DependencyEdge(
            source=map_file.as_posix(),
            target="Main.ditamap",
            edge_type="mapref",
            pattern_id="dita_map_mapref",
        ),
        DependencyEdge(
            source=map_file.as_posix(),
            target="topics/a.dita",
            edge_type="topicref",
            pattern_id="dita_map_topicref",
        ),
    ]

    assert edges == expected


# ---------------------------------------------------------------------------
# Namespace handling
# ---------------------------------------------------------------------------


def test_handles_namespaced_elements(tmp_path: Path) -> None:
    map_file = tmp_path / "namespaced.ditamap"

    _write_file(
        map_file,
        """<?xml version="1.0" encoding="UTF-8"?>
<map xmlns="http://dita.oasis-open.org/architecture/2005/">
  <mapref href="Main.ditamap"/>
  <topicref href="topics/b.dita"/>
</map>
""",
    )

    edges = extract_map_references(map_file)

    assert len(edges) == 2

    assert edges[0] == DependencyEdge(
        source=map_file.as_posix(),
        target="Main.ditamap",
        edge_type="mapref",
        pattern_id="dita_map_mapref",
    )

    assert edges[1] == DependencyEdge(
        source=map_file.as_posix(),
        target="topics/b.dita",
        edge_type="topicref",
        pattern_id="dita_map_topicref",
    )


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_missing_file_raises_error(tmp_path: Path) -> None:
    missing = tmp_path / "missing.ditamap"

    with pytest.raises(FileNotFoundError):
        extract_map_references(missing)


def test_invalid_xml_raises_error(tmp_path: Path) -> None:
    map_file = tmp_path / "bad.ditamap"

    # Malformed XML: closing tags do not match
    _write_file(map_file, "<map><mapref></map>")

    with pytest.raises(ValueError):
        extract_map_references(map_file)