"""
Tests for loading known_patterns.yaml.

These tests validate that the known patterns knowledge base can be
loaded successfully and that its structural shape is correct.

They intentionally avoid asserting specific editorial content.
"""

from dita_package_processor.knowledge.known_patterns import load_patterns


def test_patterns_load() -> None:
    """
    Known patterns must load without error and expose a valid structure.
    """
    data = load_patterns()

    # Loader must return a mapping
    assert isinstance(data, dict)

    # Patterns key must exist
    assert "patterns" in data
    patterns = data["patterns"]

    # Patterns must be iterable
    assert isinstance(patterns, list)

    # Each pattern must be a mapping with minimal expected fields
    for pattern in patterns:
        assert isinstance(pattern, dict)

        # Optional but structurally important fields
        if "classification" in pattern:
            assert isinstance(pattern["classification"], str)

        if "category" in pattern:
            assert isinstance(pattern["category"], str)