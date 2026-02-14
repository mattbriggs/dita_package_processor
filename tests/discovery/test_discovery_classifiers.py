"""
Tests for map classification logic.

These tests validate deterministic discovery-time classification behavior
based solely on declarative pattern evaluation.

Important design constraint:
Filenames MUST NOT imply semantic intent unless explicitly encoded
as discovery patterns.
"""

from pathlib import Path

from dita_package_processor.discovery.classifiers import classify_map


def test_main_ditamap_without_signals_is_unclassified() -> None:
    """
    A map named ``Main.ditamap`` MUST NOT be assumed to be the main map
    in the absence of supporting structural or contextual signals.

    Classification must remain null unless a pattern explicitly asserts it.
    """
    artifact = classify_map(
        path=Path("Main.ditamap"),
        metadata={},
    )

    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []


def test_unknown_map_when_no_signals() -> None:
    """
    A map with no recognizable signals must remain unclassified.

    Discovery does not invent intent. It only reports evidence.
    """
    artifact = classify_map(
        path=Path("Random.ditamap"),
        metadata={},
    )

    assert artifact.classification is None
    assert artifact.confidence is None
    assert artifact.evidence == []