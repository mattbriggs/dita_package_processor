"""
Unit tests for relationship extraction.

These tests verify that the RelationshipExtractor:

- Extracts syntactic dependencies from DITA XML
- Emits only schema-valid relationships
- Uses source/target/type/pattern_id contract
- Skips invalid or escaping references
- Normalizes hrefs safely (fragments, relative paths)
- Skips external URLs
- Never emits empty or malformed edges
"""

from pathlib import Path

import pytest

from dita_package_processor.discovery.relationships import RelationshipExtractor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def package(tmp_path: Path) -> Path:
    """Create a fake DITA package root."""
    root = tmp_path / "pkg"
    root.mkdir(parents=True, exist_ok=True)
    return root


@pytest.fixture
def extractor(package: Path) -> RelationshipExtractor:
    """RelationshipExtractor bound to the fake package root."""
    return RelationshipExtractor(package_root=package)


# ---------------------------------------------------------------------------
# Map relationship tests
# ---------------------------------------------------------------------------


def test_map_extracts_topicref_relationship(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    map_path = package / "index.ditamap"
    topic_path = package / "topics/a.dita"

    _write_file(
        map_path,
        """<map>
             <topicref href="topics/a.dita"/>
           </map>""",
    )
    _write_file(topic_path, "<topic></topic>")

    artifacts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
    ]

    relationships = extractor.extract(artifacts)

    assert len(relationships) == 1
    assert relationships[0] == {
        "source": "index.ditamap",
        "target": "topics/a.dita",
        "type": "topicref",
        "pattern_id": "dita_map_topicref",
    }


def test_map_extracts_mapref_relationship(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    root_map = package / "root.ditamap"
    sub_map = package / "submap.ditamap"

    _write_file(
        root_map,
        """<map>
             <mapref href="submap.ditamap"/>
           </map>""",
    )
    _write_file(sub_map, "<map></map>")

    artifacts = [
        {"path": "root.ditamap", "artifact_type": "map"},
        {"path": "submap.ditamap", "artifact_type": "map"},
    ]

    relationships = extractor.extract(artifacts)

    assert len(relationships) == 1
    edge = relationships[0]

    assert edge["type"] == "mapref"
    assert edge["source"] == "root.ditamap"
    assert edge["target"] == "submap.ditamap"


def test_map_strips_fragment_identifiers(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    """
    Hrefs like topics/a.dita#topicid must resolve to the file path only.
    """
    map_path = package / "index.ditamap"
    topic_path = package / "topics/a.dita"

    _write_file(
        map_path,
        """<map>
             <topicref href="topics/a.dita#Toc123"/>
           </map>""",
    )
    _write_file(topic_path, "<topic id='Toc123'></topic>")

    artifacts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
    ]

    relationships = extractor.extract(artifacts)

    assert len(relationships) == 1
    assert relationships[0]["target"] == "topics/a.dita"


# ---------------------------------------------------------------------------
# Topic relationship tests
# ---------------------------------------------------------------------------


def test_topic_extracts_image_relationship(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    topic_path = package / "topics/a.dita"
    img_path = package / "media/logo.png"

    _write_file(
        topic_path,
        """<topic>
             <image href="../media/logo.png"/>
           </topic>""",
    )
    _write_file(img_path, "binary")

    artifacts = [
        {"path": "topics/a.dita", "artifact_type": "topic"},
        {"path": "media/logo.png", "artifact_type": "media"},
    ]

    relationships = extractor.extract(artifacts)

    assert len(relationships) == 1
    edge = relationships[0]

    assert edge["source"] == "topics/a.dita"
    assert edge["target"] == "media/logo.png"
    assert edge["type"] == "image"
    assert edge["pattern_id"] == "dita_topic_image"


def test_topic_local_fragment_only_is_skipped(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    topic_path = package / "topics/a.dita"

    _write_file(
        topic_path,
        """<topic>
             <xref href="#Ref123"/>
           </topic>""",
    )

    artifacts = [{"path": "topics/a.dita", "artifact_type": "topic"}]

    relationships = extractor.extract(artifacts)

    assert relationships == []


# ---------------------------------------------------------------------------
# External link safety
# ---------------------------------------------------------------------------


def test_external_http_links_are_skipped(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    topic_path = package / "topics/a.dita"

    _write_file(
        topic_path,
        """<topic>
             <xref href="https://example.com/docs"/>
           </topic>""",
    )

    artifacts = [{"path": "topics/a.dita", "artifact_type": "topic"}]

    relationships = extractor.extract(artifacts)

    assert relationships == []


def test_mailto_links_are_skipped(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    topic_path = package / "topics/a.dita"

    _write_file(
        topic_path,
        """<topic>
             <xref href="mailto:someone@example.com"/>
           </topic>""",
    )

    artifacts = [{"path": "topics/a.dita", "artifact_type": "topic"}]

    relationships = extractor.extract(artifacts)

    assert relationships == []


# ---------------------------------------------------------------------------
# Safety tests
# ---------------------------------------------------------------------------


def test_relationship_target_outside_package_is_skipped(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    topic_path = package / "topics/a.dita"

    _write_file(
        topic_path,
        """<topic>
             <image href="../../etc/passwd"/>
           </topic>""",
    )

    artifacts = [{"path": "topics/a.dita", "artifact_type": "topic"}]

    relationships = extractor.extract(artifacts)

    assert relationships == []


def test_missing_artifact_file_is_skipped(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    artifacts = [{"path": "missing.ditamap", "artifact_type": "map"}]

    relationships = extractor.extract(artifacts)

    assert relationships == []


def test_only_schema_valid_edges_are_emitted(
    package: Path,
    extractor: RelationshipExtractor,
) -> None:
    map_path = package / "index.ditamap"
    topic_path = package / "topics/a.dita"

    _write_file(
        map_path,
        """<map>
             <topicref href="topics/a.dita"/>
           </map>""",
    )
    _write_file(topic_path, "<topic></topic>")

    artifacts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
    ]

    relationships = extractor.extract(artifacts)

    for edge in relationships:
        assert set(edge.keys()) == {"source", "target", "type", "pattern_id"}
        assert all(edge.values())
        assert edge["target"] != "."
        assert not str(edge["target"]).startswith("#")