"""
Target layout rules for planned artifacts.

This module defines deterministic rules that map an artifact type to
its target location within the output package.

This layer is *pure planning logic*:

- No filesystem access
- No directory creation
- No content inspection
- No mutation

It is a pure mapping layer used by the planning system to determine
where artifacts should be placed.
"""

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class LayoutRuleError(ValueError):
    """
    Raised when an unknown or unsupported artifact type is encountered.

    This indicates a planning error: either discovery classification
    failed or a new artifact type has not yet been mapped.
    """


def resolve_target_path(
    *,
    artifact_type: str,
    source_path: Path,
    target_root: Path,
) -> Path:
    """
    Resolve the target filesystem path for an artifact.

    Layout rules:

    - ``map``   → ``<target_root>/<filename>``
    - ``topic`` → ``<target_root>/topics/<filename>``
    - ``media`` → ``<target_root>/media/<filename>``

    Only the filename is preserved. All directory hierarchy from the
    source path is intentionally flattened per artifact class to ensure
    deterministic, collision-free layouts.

    This function performs **no I/O** and **no mutation**. It only
    returns a computed path.

    :param artifact_type: Artifact classification (``"map"``, ``"topic"``,
        or ``"media"``).
    :param source_path: Original artifact path.
    :param target_root: Root directory of the output package.
    :return: Target path for the artifact.
    :raises LayoutRuleError: If the artifact type is unsupported.
    """
    LOGGER.debug(
        "Resolving target path for artifact_type=%s, source_path=%s, "
        "target_root=%s",
        artifact_type,
        source_path,
        target_root,
    )

    filename = source_path.name

    if artifact_type == "map":
        target = target_root / filename
    elif artifact_type == "topic":
        target = target_root / "topics" / filename
    elif artifact_type == "media":
        target = target_root / "media" / filename
    else:
        LOGGER.error(
            "Unsupported artifact type encountered: %r", artifact_type
        )
        raise LayoutRuleError(
            f"Unsupported artifact type: {artifact_type!r}"
        )

    LOGGER.debug(
        "Resolved target path for %s (%s) → %s",
        artifact_type,
        source_path,
        target,
    )
    return target