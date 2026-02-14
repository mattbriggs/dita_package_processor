"""
Tests for DITA relationship extraction.
"""

from pathlib import Path

import pytest

from dita_package_processor.discovery.relationships import RelationshipExtractor


@pytest.fixture
def dita_package(tmp_path: Path) -> Path:
    pkg = tmp_path / "dita"
    pkg.mkdir()

    # Map
    (pkg / "index.ditamap").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<map>
    <topicref href="topics/a.dita"/>
</map>
""",
        encoding="utf-8",
    )

    # Topic
    topics = pkg / "topics"
    topics.mkdir()
    (topics / "a.dita").write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<topic>
    <image href="../media/logo.png"/>
</topic>
""",
        encoding="utf-8",
    )

    # Media
    media = pkg / "media"
    media.mkdir()
    (media / "logo.png").write_bytes(b"fakepng")

    return pkg


def test_relationship_extraction(dita_package: Path) -> None:
    extractor = RelationshipExtractor(dita_package)

    # Only maps and topics participate in relationship extraction
    artifacts = [
        {"path": "index.ditamap", "artifact_type": "map"},
        {"path": "topics/a.dita", "artifact_type": "topic"},
    ]

    rels = extractor.extract(artifacts)

    assert len(rels) == 2

    # schema guard
    for edge in rels:
        assert set(edge.keys()) == {"source", "target", "type", "pattern_id"}

    assert {
        "source": "index.ditamap",
        "target": "topics/a.dita",
        "type": "topicref",
        "pattern_id": "dita_map_topicref",
    } in rels

    assert {
        "source": "topics/a.dita",
        "target": "media/logo.png",
        "type": "image",
        "pattern_id": "dita_topic_image",
    } in rels