"""
Tests for the pattern evaluation engine.

These tests validate the *pattern evaluation contract*, not classification
policy. The evaluator is responsible only for:

- checking whether a pattern applies to an artifact
- emitting evidence when signals match
- remaining silent when signals do not match

No aggregation, precedence resolution, or mutation occurs here.
"""

from pathlib import Path

from dita_package_processor.discovery.patterns import (
    PatternEvaluator,
    Pattern,
)
from dita_package_processor.discovery.models import DiscoveryArtifact


def test_index_map_emits_main_map_evidence() -> None:
    """
    An index.ditamap that contains a mapref to another .ditamap
    should emit evidence asserting a MAIN map role.

    This test verifies:
    - filename-based signal matching
    - structural signal matching (presence of mapref)
    - correct evidence emission (not classification resolution)

    Note:
    Deeper inspection of href attributes (e.g. ends_with: .ditamap)
    is declared here but enforced only when supported by metadata.
    """
    # Artifact simulates discovery output, not raw XML.
    artifact = DiscoveryArtifact(
        path=Path("index.ditamap"),
        artifact_type="map",
        metadata={
            # Evaluator currently checks only boolean metadata flags: contains_<element>
            "contains_mapref": True,
        },
    )

    pattern = Pattern(
        id="main_map_by_index",
        applies_to="map",
        signals={
            "filename": {"equals": "index.ditamap"},
            "contains": [
                {
                    "element": "mapref",
                    "attribute": "href",
                    "ends_with": ".ditamap",
                }
            ],
        },
        asserts={"role": "MAIN", "confidence": 0.9},
        rationale=[
            "File is index.ditamap",
            "Contains mapref to another map",
        ],
    )

    evaluator = PatternEvaluator([pattern])
    evidence = evaluator.evaluate(artifact)

    assert len(evidence) == 1

    ev = evidence[0]

    assert ev.asserted_role == "MAIN"
    assert ev.confidence == 0.9
    assert ev.pattern_id == "main_map_by_index"
    assert ev.artifact_path == Path("index.ditamap")


def test_pattern_not_applied_when_signals_missing() -> None:
    """
    A pattern must not emit evidence if any required signals are missing.

    This test verifies:
    - partial matches do not produce evidence
    - filename alone is insufficient without structural confirmation
    """
    artifact = DiscoveryArtifact(
        path=Path("index.ditamap"),
        artifact_type="map",
        metadata={
            # Explicitly contradict the required structural signal
            "contains_mapref": False,
        },
    )

    pattern = Pattern(
        id="main_map_by_index",
        applies_to="map",
        signals={
            "filename": {"equals": "index.ditamap"},
            "contains": [
                {
                    "element": "mapref",
                    "attribute": "href",
                    "ends_with": ".ditamap",
                }
            ],
        },
        asserts={"role": "MAIN", "confidence": 0.9},
        rationale=["Index map with mapref"],
    )

    evaluator = PatternEvaluator([pattern])
    evidence = evaluator.evaluate(artifact)

    assert evidence == []