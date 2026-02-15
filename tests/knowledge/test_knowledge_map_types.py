"""
Unit tests for canonical map and artifact classification types.

These tests validate:

- Enum behavior
- Stable string values
- Deterministic membership
- Convenience set integrity
- Contract invariants for uniqueness and optionality

No behavioral logic exists in this module.
Only structural correctness is tested.
"""

from dita_package_processor.knowledge.map_types import (
    ArtifactCategory,
    MapType,
    ALL_MAP_TYPES,
    MULTIPLE_ALLOWED_MAP_TYPES,
    UNIQUE_MAP_TYPES,
    OPTIONAL_MAP_TYPES,
    EXECUTABLE_MAP_TYPES,
)


# =============================================================================
# ArtifactCategory
# =============================================================================


def test_artifact_category_is_enum() -> None:
    """ArtifactCategory must behave like a proper Enum."""
    assert hasattr(ArtifactCategory, "__members__")
    assert ArtifactCategory.MAP.value == "map"
    assert ArtifactCategory.TOPIC.value == "topic"


# =============================================================================
# MapType enum behavior
# =============================================================================


def test_map_type_is_enum() -> None:
    """MapType must behave like a proper Enum."""
    assert hasattr(MapType, "__members__")
    assert MapType.MAIN.value == "main"


def test_map_type_values_are_unique() -> None:
    """All MapType values must be unique."""
    values = [member.value for member in MapType]
    assert len(values) == len(set(values))


def test_map_type_string_roundtrip() -> None:
    """MapType must support deterministic round-trip via value."""
    for member in MapType:
        reconstructed = MapType(member.value)
        assert reconstructed is member


def test_map_type_is_case_sensitive() -> None:
    """
    MapType lookup must be case-sensitive.

    This prevents silent contract corruption.
    """
    first = next(iter(MapType))

    try:
        MapType(first.value.upper())
    except ValueError:
        pass
    else:
        raise AssertionError("MapType lookup should be case-sensitive")


# =============================================================================
# Convenience set integrity
# =============================================================================


def test_all_map_types_matches_enum() -> None:
    """ALL_MAP_TYPES must exactly match MapType members."""
    assert ALL_MAP_TYPES == set(MapType)


def test_unique_and_multiple_sets_do_not_overlap() -> None:
    """
    UNIQUE and MULTIPLE sets must not overlap.

    A map type cannot be both unique and multi-allowed.
    """
    overlap = UNIQUE_MAP_TYPES.intersection(MULTIPLE_ALLOWED_MAP_TYPES)
    assert overlap == set()


def test_unique_map_types_subset_of_all() -> None:
    """UNIQUE_MAP_TYPES must be valid MapType members."""
    assert UNIQUE_MAP_TYPES.issubset(ALL_MAP_TYPES)


def test_multiple_allowed_subset_of_all() -> None:
    """MULTIPLE_ALLOWED_MAP_TYPES must be valid MapType members."""
    assert MULTIPLE_ALLOWED_MAP_TYPES.issubset(ALL_MAP_TYPES)


def test_optional_subset_of_unique() -> None:
    """
    OPTIONAL_MAP_TYPES must be a subset of UNIQUE_MAP_TYPES.

    Optional maps are still unique when present.
    """
    assert OPTIONAL_MAP_TYPES.issubset(UNIQUE_MAP_TYPES)


def test_executable_subset_of_all() -> None:
    """EXECUTABLE_MAP_TYPES must be valid MapType members."""
    assert EXECUTABLE_MAP_TYPES.issubset(ALL_MAP_TYPES)