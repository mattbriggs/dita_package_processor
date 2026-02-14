"""
Unit tests for pattern evaluation.

These tests verify that the PatternEvaluator:

- Emits evidence when patterns match
- Emits nothing when patterns do not match
- Ignores fallback patterns during semantic evaluation
- Fails closed on unknown signals

This module tests *observation only*. No classification or resolution logic
exists here. If no evidence is observed, discovery remains silent.
"""

from pathlib import Path

import pytest

from dita_package_processor.discovery.patterns import (
    Evidence,
    Pattern,
    PatternEvaluator,
)
from dita_package_processor.discovery.models import DiscoveryArtifact


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def artifact() -> DiscoveryArtifact:
    """Simple test artifact with metadata."""
    return DiscoveryArtifact(
        path=Path("/package/maps/index.ditamap"),
        artifact_type="map",
        metadata={
            "root_element": "map",
            "contains_topicref": True,
        },
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pattern_emits_evidence_when_match(artifact: DiscoveryArtifact) -> None:
    """Matching pattern must emit evidence."""
    pattern = Pattern(
        id="test_map_main",
        applies_to="map",
        signals={"root_element": {"equals": "map"}},
        asserts={"role": "MAIN", "confidence": 0.9},
        rationale=["Root element is <map>"],
    )

    evaluator = PatternEvaluator([pattern])
    evidence = evaluator.evaluate(artifact)

    assert len(evidence) == 1
    ev = evidence[0]
    assert isinstance(ev, Evidence)
    assert ev.pattern_id == "test_map_main"
    assert ev.asserted_role == "MAIN"
    assert ev.confidence == 0.9
    assert ev.artifact_path == artifact.path


def test_pattern_does_not_emit_when_not_matching(artifact: DiscoveryArtifact) -> None:
    """Non-matching patterns must emit nothing."""
    pattern = Pattern(
        id="wrong_root",
        applies_to="map",
        signals={"root_element": {"equals": "topic"}},
        asserts={"role": "MAIN", "confidence": 1.0},
        rationale=["Should not match"],
    )

    evaluator = PatternEvaluator([pattern])
    evidence = evaluator.evaluate(artifact)

    assert evidence == []


def test_fallback_patterns_are_ignored_when_other_patterns_match(
    artifact: DiscoveryArtifact,
) -> None:
    """
    Fallback patterns must not interfere with normal semantic matching.

    They are not semantic assertions and should be ignored entirely by the
    evaluator.
    """
    main_pattern = Pattern(
        id="main_pattern",
        applies_to="map",
        signals={"root_element": {"equals": "map"}},
        asserts={"role": "MAIN", "confidence": 0.9},
        rationale=["Primary match"],
    )

    fallback_pattern = Pattern(
        id="fallback_pattern",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["Fallback pattern is non-semantic"],
    )

    evaluator = PatternEvaluator([main_pattern, fallback_pattern])
    evidence = evaluator.evaluate(artifact)

    assert len(evidence) == 1
    assert evidence[0].pattern_id == "main_pattern"


def test_fallback_patterns_do_not_emit_evidence_when_no_match(
    artifact: DiscoveryArtifact,
) -> None:
    """
    Fallback patterns must not emit semantic evidence.

    If no non-fallback patterns match, discovery remains silent.
    """
    failing_pattern = Pattern(
        id="failing_pattern",
        applies_to="map",
        signals={"root_element": {"equals": "topic"}},
        asserts={"role": "MAIN", "confidence": 1.0},
        rationale=["Will not match"],
    )

    fallback_pattern = Pattern(
        id="fallback_pattern",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["Fallback patterns do not assert semantics"],
    )

    evaluator = PatternEvaluator([failing_pattern, fallback_pattern])
    evidence = evaluator.evaluate(artifact)

    assert evidence == []


def test_unknown_signal_fails_closed(artifact: DiscoveryArtifact) -> None:
    """Unknown signal types must cause the pattern to fail."""
    pattern = Pattern(
        id="bad_signal",
        applies_to="map",
        signals={"some_unknown_key": {"foo": "bar"}},
        asserts={"role": "MAIN", "confidence": 1.0},
        rationale=["Should fail closed"],
    )

    evaluator = PatternEvaluator([pattern])
    evidence = evaluator.evaluate(artifact)

    assert evidence == []