"""
layout.py

Materialization layout rules for the DITA Package Processor.

This module defines deterministic rules for mapping artifact-relative paths
(from plans, handlers, or reports) into a concrete target package layout.

Materialization layout rules answer:
    "Given an artifact path, where should it live in the target package?"

Design constraints:
- deterministic: same input produces same output
- conservative: refuses ambiguous or unsafe paths
- pure mapping: no copying, no filesystem mutation
- explicit: rules are readable and testable

Default policy:
- .ditamap files are placed at target root (flattened to filename)
- .dita files are placed under target_root/topics/ (unless already under topics/)
- all other files are placed under target_root/media/
  - if already under media/, preserve relative structure
  - if under images/, nest under media/images/
  - otherwise flatten to filename under media/
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class LayoutError(ValueError):
    """Raised when an input path cannot be mapped safely into the target layout."""


# ---------------------------------------------------------------------------
# Policy protocol
# ---------------------------------------------------------------------------

class LayoutPolicy(Protocol):
    """
    Strategy interface for layout policies.

    Implementations must be deterministic and must not touch the filesystem.
    """

    def map_relative_path(self, rel_path: Path) -> Path:
        """
        Map a relative artifact path into a normalized relative target path.

        :param rel_path: Relative path for an artifact (e.g., "topics/a.dita").
        :return: Relative target path (e.g., "topics/a.dita" or "media/a.png").
        :raises LayoutError: If the path is unsafe or cannot be mapped.
        """


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_relative_path(rel_path: Path) -> None:
    """
    Validate that a path is a safe relative path.

    Rules:
    - must not be absolute
    - must not contain '..' components
    - must not be empty

    :param rel_path: Path to validate.
    :raises LayoutError: If invalid.
    """
    if not rel_path or str(rel_path).strip() == "":
        raise LayoutError("Empty path cannot be mapped")

    if rel_path.is_absolute():
        raise LayoutError(f"Absolute paths are not allowed: {rel_path}")

    if ".." in rel_path.parts:
        raise LayoutError(f"Path traversal is not allowed: {rel_path}")


# ---------------------------------------------------------------------------
# Default policy
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class DefaultDitaLayoutPolicy:
    """
    Default deterministic layout policy for DITA-like packages.

    This policy is intentionally conservative and predictable.
    """

    topics_dir: Path = Path("topics")
    media_dir: Path = Path("media")

    def map_relative_path(self, rel_path: Path) -> Path:
        """
        Map a relative artifact path into the default target layout.

        :param rel_path: Relative artifact path.
        :return: Relative target path.
        :raises LayoutError: If input is unsafe.
        """
        _validate_relative_path(rel_path)

        suffix = rel_path.suffix.lower()
        parts = rel_path.parts

        # Maps → target root, flattened
        if suffix == ".ditamap":
            mapped = Path(rel_path.name)
            LOGGER.debug("Layout map: %s -> %s", rel_path, mapped)
            return mapped

        # Topics → topics/
        if suffix == ".dita":
            if parts and parts[0] == self.topics_dir.as_posix():
                mapped = rel_path
            else:
                mapped = self.topics_dir / rel_path.name
            LOGGER.debug("Layout topic: %s -> %s", rel_path, mapped)
            return mapped

        # Media handling
        if parts and parts[0] == self.media_dir.as_posix():
            mapped = rel_path
            LOGGER.debug("Layout media (preserve): %s -> %s", rel_path, mapped)
            return mapped

        if parts and parts[0].lower() == "images":
            mapped = self.media_dir / "images" / Path(*parts[1:])
            LOGGER.debug(
                "Layout media (images->media/images): %s -> %s",
                rel_path,
                mapped,
            )
            return mapped

        mapped = self.media_dir / rel_path.name
        LOGGER.debug("Layout media (flatten): %s -> %s", rel_path, mapped)
        return mapped


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TargetLayout:
    """
    Target layout resolver.

    Converts artifact-relative paths into concrete target paths
    under a provided target root, using a policy object.

    Pattern: Strategy
    """

    target_root: Path
    policy: LayoutPolicy = DefaultDitaLayoutPolicy()

    def resolve(self, *, rel_path: Path) -> Path:
        """
        Resolve a relative artifact path to a concrete path under target_root.

        :param rel_path: Relative artifact path (must be safe).
        :return: Concrete target path.
        :raises LayoutError: If rel_path is invalid or unsafe.
        """
        _validate_relative_path(rel_path)

        mapped_rel = self.policy.map_relative_path(rel_path)
        _validate_relative_path(mapped_rel)

        resolved = self.target_root / mapped_rel
        LOGGER.debug("Resolved target path: %s -> %s", rel_path, resolved)
        return resolved


# ---------------------------------------------------------------------------
# Engine (orchestrator-facing)
# ---------------------------------------------------------------------------

class MaterializationLayoutEngine:
    """
    Orchestrates layout resolution for materialization.

    This engine provides a stable coordination surface for the
    materialization orchestrator without performing filesystem mutation.

    Responsibilities:
    - own TargetLayout
    - expose resolution as an explicit phase
    """

    def __init__(
        self,
        *,
        target_root: Path,
        policy: LayoutPolicy | None = None,
    ) -> None:
        """
        Initialize the layout engine.

        :param target_root: Root of the materialized target package.
        :param policy: Optional layout policy override.
        """
        self._layout = TargetLayout(
            target_root=target_root,
            policy=policy or DefaultDitaLayoutPolicy(),
        )

        LOGGER.info("MaterializationLayoutEngine initialized for %s", target_root)

    def resolve_path(self, *, rel_path: Path) -> Path:
        """
        Resolve an artifact-relative path into its target location.

        :param rel_path: Relative artifact path.
        :return: Concrete target path.
        :raises LayoutError: If mapping fails.
        """
        return self._layout.resolve(rel_path=rel_path)


__all__ = [
    "LayoutError",
    "LayoutPolicy",
    "DefaultDitaLayoutPolicy",
    "TargetLayout",
    "MaterializationLayoutEngine",
]