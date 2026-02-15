"""
Tests for discovery-time map classification.

These tests validate deterministic classification behavior driven solely
by declarative pattern evaluation.

Design constraint
-----------------
Filenames MUST NOT imply semantic intent unless explicitly encoded
as discovery patterns.

Discovery does not guess.
Discovery does not infer.
Discovery only reports evidence.
"""

from pathlib import Path

from dita_package_processor.discovery.classifiers import classify_map
from dita_package_processor.knowledge.map_types import MapType


# =============================================================================
# Unclassified Maps
# =============================================================================


def test_main_ditamap_without_signals_is_unclassified() -> None:
    """
    A map named ``Main.ditamap`` MUST NOT be assumed to be the main map
    in the absence of supporting structural signals.
    """
    artifact = classify_map(
        path=Path("Main.ditamap"),
        metadata={},
    )

    assert artifact.artifact_type == "map"

    # No structural evidence → no classification
    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


def test_unknown_map_when_no_signals() -> None:
    """
    A map with no recognizable signals must remain unclassified.

    Discovery does not invent intent.
    """
    artifact = classify_map(
        path=Path("Random.ditamap"),
        metadata={},
    )

    assert artifact.artifact_type == "map"

    # Must remain unclassified
    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


# =============================================================================
# Type Safety
# =============================================================================


def test_map_classification_type_is_enum_when_present() -> None:
    """
    If classification occurs, it must be a MapType enum,
    not a raw string.
    """
    # Simulate structural signal manually
    artifact = classify_map(
        path=Path("index.ditamap"),
        metadata={
            "root_element": "map",
            "contains_mapref": True,
        },
    )

    if artifact.classification is not None:
        assert isinstance(artifact.classification, MapType)