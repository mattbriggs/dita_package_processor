"""
Known structural patterns for DITA discovery.

This module loads and validates declarative discovery patterns defined
in ``known_patterns.yaml``. Patterns are normalized into immutable
:class:`Pattern` objects suitable for deterministic evaluation.

This module performs:
- no classification
- no inference
- no filesystem inspection beyond loading the YAML file

Its responsibility is limited to:
    YAML → validated data → normalized Pattern objects
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List

import yaml

from dita_package_processor.discovery.patterns import Pattern

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOGGER = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_patterns() -> Dict[str, Any]:
    """
    Load declarative discovery patterns from ``known_patterns.yaml``.

    Expected YAML structure::

        version: 1
        patterns:
          - id: ...
            applies_to: ...
            signals: ...
            asserts:
              role: ...
              confidence: ...
            rationale:
              - ...

    This function only loads and validates the raw YAML structure.
    Pattern normalization is handled by :func:`load_normalized_patterns`.

    :return: Parsed YAML document.
    :raises ValueError: If structure is invalid.
    """
    path = Path(__file__).with_name("known_patterns.yaml")
    LOGGER.debug("Loading discovery patterns from %s", path)

    if not path.exists():
        raise FileNotFoundError(f"known_patterns.yaml not found: {path}")

    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        raise ValueError("known_patterns.yaml must be a mapping at top level")

    if "patterns" not in data:
        raise ValueError("known_patterns.yaml missing 'patterns' key")

    if not isinstance(data["patterns"], list):
        raise ValueError("'patterns' must be a list")

    LOGGER.info(
        "Loaded raw discovery patterns: %d entries",
        len(data["patterns"]),
    )

    return data


def load_normalized_patterns() -> List[Pattern]:
    """
    Load, validate, and normalize all discovery patterns.

    This is the canonical entry point used by discovery classifiers.

    :return: List of normalized :class:`Pattern` instances.
    :raises ValueError: If any pattern is invalid.
    """
    raw = load_patterns()
    patterns: List[Pattern] = []

    LOGGER.debug("Normalizing discovery patterns")

    for entry in raw["patterns"]:
        pattern = _load_pattern(entry)
        patterns.append(pattern)
        LOGGER.debug(
            "Loaded pattern: id=%s applies_to=%s",
            pattern.id,
            pattern.applies_to,
        )

    LOGGER.info("Successfully normalized %d patterns", len(patterns))
    return patterns


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_pattern(entry: Dict[str, Any]) -> Pattern:
    """
    Validate and normalize a single pattern entry.

    :param entry: Raw pattern mapping from YAML.
    :return: Normalized :class:`Pattern` instance.
    :raises ValueError: If required fields are missing or invalid.
    """
    if not isinstance(entry, dict):
        raise ValueError("Each pattern entry must be a mapping")

    required_fields = {
        "id",
        "applies_to",
        "signals",
        "asserts",
        "rationale",
    }

    missing = required_fields - entry.keys()
    if missing:
        raise ValueError(
            f"Pattern missing required fields: {', '.join(sorted(missing))}"
        )

    if not isinstance(entry["signals"], dict):
        raise ValueError(
            f"Pattern '{entry['id']}' signals must be a mapping"
        )

    if not isinstance(entry["asserts"], dict):
        raise ValueError(
            f"Pattern '{entry['id']}' asserts must be a mapping"
        )

    asserts = entry["asserts"]
    if "role" not in asserts or "confidence" not in asserts:
        raise ValueError(
            f"Pattern '{entry['id']}' asserts must define 'role' and 'confidence'"
        )

    if not isinstance(asserts["confidence"], (int, float)):
        raise ValueError(
            f"Pattern '{entry['id']}' confidence must be numeric"
        )

    if not isinstance(entry["rationale"], list):
        raise ValueError(
            f"Pattern '{entry['id']}' rationale must be a list of strings"
        )

    LOGGER.debug("Validating pattern '%s'", entry["id"])

    pattern = Pattern(
        id=entry["id"],
        applies_to=entry["applies_to"],
        signals=entry["signals"],
        asserts=asserts,
        rationale=entry["rationale"],
    )

    return pattern