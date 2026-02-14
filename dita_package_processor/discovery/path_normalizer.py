"""
Path normalization utilities for discovery.

This module normalizes relative and absolute references found in DITA
documents into deterministic, package-root–relative paths.

It ensures that the dependency graph is stable and free from duplicate
edges caused by path variation such as:

    - ./topics/a.dita
    - ../topics/a.dita
    - topics/../topics/a.dita

All of these must resolve to the same canonical path string.

Single responsibility:
    Input:
        - source file path
        - raw reference string
        - package root
    Output:
        - normalized package-root–relative POSIX path string

This module performs:
    - no filesystem mutation
    - no semantic validation
    - no file existence checks
"""

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


def normalize_reference_path(
    *,
    source_path: Path,
    reference: str,
    package_root: Path,
) -> str:
    """
    Normalize a referenced path relative to the source file and package root.

    The returned value is always:
    - relative to the package root
    - using POSIX-style separators
    - fully normalized (no ``..`` or ``.`` segments)
    - stable across platforms

    Absolute references are interpreted as package-root–anchored paths.

    :param source_path: Path of the file containing the reference.
    :param reference: Raw reference value (e.g. from ``href`` or ``data``).
    :param package_root: Root directory of the DITA package.
    :return: Normalized, package-root–relative path using POSIX separators.
    :raises ValueError: If the normalized path escapes the package root.
    """
    LOGGER.debug(
        "Normalizing reference path: source=%s, reference=%s, package_root=%s",
        source_path,
        reference,
        package_root,
    )

    # Resolve symbolically, never touching the filesystem
    source_path = source_path.resolve(strict=False)
    package_root = package_root.resolve(strict=False)

    ref_path = Path(reference)

    # Absolute paths are interpreted as package-root anchored
    if ref_path.is_absolute():
        LOGGER.debug(
            "Reference is absolute; treating as package-root anchored: %s",
            ref_path,
        )
        resolved = (package_root / ref_path.relative_to("/")).resolve(strict=False)
    else:
        LOGGER.debug(
            "Reference is relative; resolving against source directory: %s",
            source_path.parent,
        )
        resolved = (source_path.parent / ref_path).resolve(strict=False)

    LOGGER.debug("Resolved symbolic path: %s", resolved)

    try:
        normalized = resolved.relative_to(package_root)
    except ValueError as exc:
        LOGGER.error(
            "Reference escapes package root. "
            "Resolved=%s, PackageRoot=%s, Reference=%s",
            resolved,
            package_root,
            reference,
        )
        raise ValueError(
            f"Reference escapes package root: {reference}"
        ) from exc

    normalized_posix = normalized.as_posix()

    LOGGER.debug(
        "Normalized reference path (package-root relative): %s",
        normalized_posix,
    )

    return normalized_posix