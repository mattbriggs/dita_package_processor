"""
Unit tests for pattern evaluation.

These tests verify that the PatternEvaluator:

- Emits evidence when patterns match
- Emits nothing when patterns do not match
- Suppresses fallback when semantic evidence exists
- Emits deterministic fallback when explicitly enabled
- Fails closed on unknown signals
- Validates pattern shape strictly

This module tests observation only.
"""

from pathlib import Path

import pytest

from dita_package_processor.discovery.models import DiscoveryArtifact
from dita_package_processor.discovery.patterns import (
    Evidence,
    Pattern,
    PatternEvaluator,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def artifact() -> DiscoveryArtifact:
    """Simple test artifact with valid metadata."""
    return DiscoveryArtifact(
        path=Path("maps/index.ditamap"),
        artifact_type="map",
        metadata={
            "root_element": "map",
            "contains_topicref": True,
        },
    )


# =============================================================================
# Semantic Matching
# =============================================================================


def test_pattern_emits_evidence_when_match(
    artifact: DiscoveryArtifact,
) -> None:
    """Matching pattern must emit exactly one Evidence."""
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


def test_pattern_does_not_emit_when_not_matching(
    artifact: DiscoveryArtifact,
) -> None:
    """Non-matching pattern must emit nothing."""
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


# =============================================================================
# Fallback Behavior
# =============================================================================


def test_fallback_suppressed_when_semantic_match_exists(
    artifact: DiscoveryArtifact,
) -> None:
    """Fallback must not fire if semantic evidence exists."""
    semantic = Pattern(
        id="semantic",
        applies_to="map",
        signals={"root_element": {"equals": "map"}},
        asserts={"role": "MAIN", "confidence": 0.8},
        rationale=["Primary semantic match"],
    )

    fallback = Pattern(
        id="fallback",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.1},
        rationale=["Fallback helper"],
    )

    evaluator = PatternEvaluator([semantic, fallback])
    evidence = evaluator.evaluate(artifact)

    assert len(evidence) == 1
    assert evidence[0].pattern_id == "semantic"


def test_fallback_emits_only_when_enabled_and_no_semantic_match(
    artifact: DiscoveryArtifact,
) -> None:
    """Fallback must emit only if explicitly enabled."""
    failing = Pattern(
        id="no_match",
        applies_to="map",
        signals={"root_element": {"equals": "topic"}},
        asserts={"role": "MAIN", "confidence": 1.0},
        rationale=["Will not match"],
    )

    fallback = Pattern(
        id="zzz_fallback",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "UNKNOWN", "confidence": 0.2},
        rationale=["Fallback helper"],
    )

    evaluator = PatternEvaluator([failing, fallback])

    # Observation mode (default) → no fallback
    assert evaluator.evaluate(artifact) == []

    # Classification mode → fallback fires
    evidence = evaluator.evaluate(artifact, allow_fallback=True)

    assert len(evidence) == 1
    assert evidence[0].pattern_id == "zzz_fallback"
    assert evidence[0].asserted_role == "UNKNOWN"


def test_fallback_selection_is_deterministic(
    artifact: DiscoveryArtifact,
) -> None:
    """Lowest pattern id must be selected deterministically."""
    fallback_a = Pattern(
        id="aaa_fallback",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "A", "confidence": 0.1},
        rationale=["A"],
    )

    fallback_b = Pattern(
        id="zzz_fallback",
        applies_to="map",
        signals={"fallback": True},
        asserts={"role": "B", "confidence": 0.2},
        rationale=["B"],
    )

    evaluator = PatternEvaluator([fallback_b, fallback_a])

    evidence = evaluator.evaluate(artifact, allow_fallback=True)

    assert len(evidence) == 1
    assert evidence[0].pattern_id == "aaa_fallback"


# =============================================================================
# Fail-Closed Behavior
# =============================================================================


def test_unknown_signal_fails_closed(
    artifact: DiscoveryArtifact,
) -> None:
    """Unknown signal keys must cause match failure."""
    pattern = Pattern(
        id="bad_signal",
        applies_to="map",
        signals={"unknown_key": {"foo": "bar"}},
        asserts={"role": "MAIN", "confidence": 1.0},
        rationale=["Invalid signal"],
    )

    evaluator = PatternEvaluator([pattern])
    evidence = evaluator.evaluate(artifact)

    assert evidence == []


# =============================================================================
# Pattern Validation
# =============================================================================


def test_invalid_confidence_rejected() -> None:
    """Confidence outside 0–1 must raise ValueError."""
    with pytest.raises(ValueError):
        Pattern(
            id="bad_conf",
            applies_to="map",
            signals={},
            asserts={"role": "MAIN", "confidence": 1.5},
            rationale=["Invalid confidence"],
        )


def test_invalid_applies_to_rejected() -> None:
    """Invalid artifact type must raise ValueError."""
    with pytest.raises(ValueError):
        Pattern(
            id="bad_type",
            applies_to="invalid_type",
            signals={},
            asserts={"role": "MAIN", "confidence": 0.5},
            rationale=["Invalid applies_to"],
        )