"""
Tests enforcing fallback pattern semantics.

Fallback patterns must only emit evidence when no other
pattern applies to an artifact.
"""

from pathlib import Path

from dita_package_processor.discovery.patterns import (
    PatternEvaluator,
    Pattern,
)
from dita_package_processor.discovery.models import DiscoveryArtifact


def test_fallback_not_emitted_when_primary_pattern_matches() -> None:
    """
    If a non-fallback pattern emits evidence, fallback must not fire.
    """
    artifact = DiscoveryArtifact(
        path=Path("index.ditamap"),
        artifact_type="map",
        metadata={
            "contains_mapref": True,
        },
    )

    primary = Pattern(
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
        rationale=["Index map referencing another map"],
    )

    fallback = Pattern(
        id="unknown_map_fallback",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["No other map patterns matched"],
    )

    evaluator = PatternEvaluator([primary, fallback])
    evidence = evaluator.evaluate(artifact)

    assert len(evidence) == 1
    assert evidence[0].pattern_id == "main_map_by_index"
    assert evidence[0].asserted_role == "MAIN"


def test_fallback_emitted_when_no_primary_patterns_match() -> None:
    """
    If no non-fallback pattern matches, fallback must emit evidence.
    """
    artifact = DiscoveryArtifact(
        path=Path("Random.ditamap"),
        artifact_type="map",
        metadata={
            "contains_mapref": False,
        },
    )

    primary = Pattern(
        id="main_map_by_index",
        applies_to="map",
        signals={
            "filename": {"equals": "index.ditamap"},
        },
        asserts={"role": "MAIN", "confidence": 0.9},
        rationale=["Index map"],
    )

    fallback = Pattern(
        id="unknown_map_fallback",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["No other map patterns matched"],
    )

    evaluator = PatternEvaluator([primary, fallback])
    evidence = evaluator.evaluate(artifact, allow_fallback=True)

    assert len(evidence) == 1
    assert evidence[0].pattern_id == "unknown_map_fallback"
    assert evidence[0].asserted_role == "UNKNOWN"


def test_multiple_fallbacks_do_not_stack() -> None:
    """
    Evaluator must not emit more than one fallback evidence
    for a single artifact.
    """
    artifact = DiscoveryArtifact(
        path=Path("orphan.dita"),
        artifact_type="topic",
        metadata={},
    )

    fallback_a = Pattern(
        id="unknown_topic_fallback",
        applies_to="topic",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["No topic patterns matched"],
    )

    fallback_b = Pattern(
        id="another_fallback",
        applies_to="topic",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["Should never fire"],
    )

    evaluator = PatternEvaluator([fallback_a, fallback_b])
    evidence = evaluator.evaluate(artifact, allow_fallback=True)

    # Only one fallback is allowed
    assert len(evidence) == 1

    # It must be a fallback
    assert evidence[0].asserted_role == "UNKNOWN"

    # It must be one of the declared fallback patterns
    assert evidence[0].pattern_id in {
        "unknown_topic_fallback",
        "another_fallback",
    }