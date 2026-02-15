"""
Unit tests for TopicKind and TopicType.

These tests validate:

- TopicKind behaves as a stable Enum
- TopicType enforces validation rules
- Confidence bounds are enforced
- Type constraints are enforced
- Convenience methods behave correctly
- Value semantics are deterministic
"""

from __future__ import annotations

import pytest

from dita_package_processor.knowledge.topic_types import (
    TopicKind,
    TopicType,
)


# =============================================================================
# TopicKind Tests
# =============================================================================


def test_topic_kind_is_enum() -> None:
    """TopicKind must behave as an Enum."""
    assert hasattr(TopicKind, "__members__")


def test_topic_kind_members_are_unique() -> None:
    """Enum values must be unique."""
    values = [member.value for member in TopicKind]
    assert len(values) == len(set(values))


def test_topic_kind_string_roundtrip() -> None:
    """Enum must support deterministic value round-trip."""
    for member in TopicKind:
        assert TopicKind(member.value) == member


def test_topic_kind_is_case_sensitive() -> None:
    """Enum lookup must be case-sensitive."""
    first = next(iter(TopicKind))

    with pytest.raises(ValueError):
        TopicKind(first.value.upper())


# =============================================================================
# TopicType Construction
# =============================================================================


def test_topic_type_valid_construction() -> None:
    """Valid TopicType must construct successfully."""
    topic = TopicType(kind=TopicKind.CONCEPT, confidence=0.8)

    assert topic.kind == TopicKind.CONCEPT
    assert topic.confidence == 0.8
    assert topic.label == "concept"


def test_topic_type_confidence_casts_to_float() -> None:
    """Confidence int must normalize to float."""
    topic = TopicType(kind=TopicKind.TASK, confidence=1)

    assert isinstance(topic.confidence, float)
    assert topic.confidence == 1.0


def test_topic_type_confidence_bounds_enforced() -> None:
    """Confidence outside 0–1 must raise ValueError."""
    with pytest.raises(ValueError):
        TopicType(kind=TopicKind.REFERENCE, confidence=1.5)

    with pytest.raises(ValueError):
        TopicType(kind=TopicKind.REFERENCE, confidence=-0.1)


def test_topic_type_confidence_type_enforced() -> None:
    """Non-numeric confidence must raise TypeError."""
    with pytest.raises(TypeError):
        TopicType(kind=TopicKind.CONCEPT, confidence="high")  # type: ignore[arg-type]


def test_topic_type_kind_type_enforced() -> None:
    """Kind must be TopicKind."""
    with pytest.raises(TypeError):
        TopicType(kind="concept", confidence=0.5)  # type: ignore[arg-type]


# =============================================================================
# Convenience Methods
# =============================================================================


def test_topic_type_is_unknown() -> None:
    """is_unknown must reflect UNKNOWN kind."""
    unknown = TopicType(kind=TopicKind.UNKNOWN, confidence=0.5)
    concept = TopicType(kind=TopicKind.CONCEPT, confidence=0.5)

    assert unknown.is_unknown() is True
    assert concept.is_unknown() is False


# =============================================================================
# Value Semantics
# =============================================================================


def test_topic_type_equality() -> None:
    """Identical TopicType instances must compare equal."""
    a = TopicType(kind=TopicKind.CONCEPT, confidence=0.9)
    b = TopicType(kind=TopicKind.CONCEPT, confidence=0.9)

    assert a == b


def test_topic_type_inequality() -> None:
    """Different values must not compare equal."""
    a = TopicType(kind=TopicKind.CONCEPT, confidence=0.9)
    b = TopicType(kind=TopicKind.TASK, confidence=0.9)

    assert a != b