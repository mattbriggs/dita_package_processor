"""
Topic type definitions for DITA knowledge layer.

This module defines canonical topic classifications used during
discovery and downstream semantic interpretation.

Design Principles
-----------------
- Deterministic
- Explicit
- No inference
- No fallback logic
- No mutation

These types represent semantic classification labels only.
They do not contain behavioral logic.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Topic Kind Enumeration
# =============================================================================


class TopicKind(str, Enum):
    """
    Canonical topic classification kinds.

    Values represent normalized semantic categories.
    """

    CONCEPT = "concept"
    TASK = "task"
    REFERENCE = "reference"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        """Return string value."""
        return self.value


# =============================================================================
# TopicType Model
# =============================================================================


@dataclass(frozen=True)
class TopicType:
    """
    Immutable semantic topic classification.

    Parameters
    ----------
    kind : TopicKind
        Canonical topic kind.
    confidence : float
        Classification confidence (0.0–1.0).

    Notes
    -----
    This object contains no logic beyond validation.
    It is a value object.
    """

    kind: TopicKind
    confidence: float

    def __post_init__(self) -> None:
        if not isinstance(self.kind, TopicKind):
            raise TypeError("TopicType.kind must be TopicKind")

        if not isinstance(self.confidence, (float, int)):
            raise TypeError("TopicType.confidence must be numeric")

        confidence = float(self.confidence)

        if not (0.0 <= confidence <= 1.0):
            raise ValueError("TopicType.confidence must be between 0 and 1")

        object.__setattr__(self, "confidence", confidence)

        LOGGER.debug(
            "TopicType created: kind=%s confidence=%.2f",
            self.kind.value,
            confidence,
        )

    # ---------------------------------------------------------------------
    # Convenience
    # ---------------------------------------------------------------------

    @property
    def label(self) -> str:
        """
        Human-readable label.

        Returns
        -------
        str
        """
        return self.kind.value

    def is_unknown(self) -> bool:
        """
        Return True if classification is UNKNOWN.
        """
        return self.kind == TopicKind.UNKNOWN