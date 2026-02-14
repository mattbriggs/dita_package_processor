"""
collision.py

Target collision detection for materialization.

This module detects filesystem conflicts before execution occurs.

It ensures:
- No two planned outputs resolve to the same target location.
- Collision detection is deterministic and explicit.
- No filesystem mutation occurs here.

This module supports two APIs:

1) Legacy style (stateful):
   detector = CollisionDetector(artifacts=[...])
   detector.detect()

2) Injectable orchestrator style (stateless):
   detector = MaterializationCollisionDetector()
   detector.detect(artifacts=[...])
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set

LOGGER = logging.getLogger(__name__)


class MaterializationCollisionError(RuntimeError):
    """Raised when target path collisions are detected."""


@dataclass(frozen=True)
class TargetArtifact:
    """
    Represents a single materialized output artifact.

    Attributes:
        path:
            Absolute or resolved target path.
        source_action_id:
            ID of the plan action producing this artifact.
    """

    path: Path
    source_action_id: str


def _detect_collisions(*, artifacts: Iterable[TargetArtifact]) -> None:
    """
    Core collision detection logic.

    This is intentionally shared by both detector styles so behavior remains
    consistent across the system.

    :param artifacts: Iterable of TargetArtifact objects.
    :raises MaterializationCollisionError: If duplicates are detected.
    """
    LOGGER.info("Detecting materialization collisions")

    seen: Set[Path] = set()
    collisions: List[str] = []

    for artifact in artifacts:
        # Normalize deterministically:
        # - keep it absolute if already absolute
        # - resolve symlinks and ".." consistently
        try:
            normalized = artifact.path.resolve()
        except Exception:  # noqa: BLE001
            # If resolve fails (rare), fall back to the raw path.
            normalized = artifact.path

        if normalized in seen:
            collisions.append(
                f"Duplicate target path: {normalized} "
                f"(from action {artifact.source_action_id})"
            )
        else:
            seen.add(normalized)

    if collisions:
        LOGGER.error("Materialization collisions detected")
        for c in collisions:
            LOGGER.error(c)

        raise MaterializationCollisionError(
            "Materialization collision(s) detected:\n" + "\n".join(collisions)
        )

    LOGGER.info("No materialization collisions detected")


class CollisionDetector:
    """
    Legacy collision detector API (stateful).

    This class remains for backward compatibility with tests and older code.

    Usage:
        detector = CollisionDetector(artifacts=[...])
        detector.detect()
    """

    def __init__(self, *, artifacts: Iterable[TargetArtifact]) -> None:
        """
        Initialize the detector.

        :param artifacts: Iterable of TargetArtifact objects.
        """
        self._artifacts = list(artifacts)

    def detect(self) -> None:
        """
        Detect collisions among target artifacts.

        :raises MaterializationCollisionError: If collisions are detected.
        """
        _detect_collisions(artifacts=self._artifacts)


class MaterializationCollisionDetector:
    """
    Injectable collision detector API (stateless).

    This is the preferred interface for orchestration wiring.

    Usage:
        detector = MaterializationCollisionDetector()
        detector.detect(artifacts=[...])
    """

    def detect(self, *, artifacts: Iterable[TargetArtifact]) -> None:
        """
        Detect collisions among target artifacts.

        :param artifacts: Iterable of TargetArtifact objects.
        :raises MaterializationCollisionError: If collisions are detected.
        """
        _detect_collisions(artifacts=artifacts)


__all__ = [
    "MaterializationCollisionError",
    "TargetArtifact",
    "CollisionDetector",
    "MaterializationCollisionDetector",
]