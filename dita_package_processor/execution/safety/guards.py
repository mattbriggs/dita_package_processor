"""
Filesystem write permission guards.

This module enforces *write permission* semantics before any mutation
occurs. It answers one question:

    "Is the current process actually allowed to write to this path?"

Sandbox decides *where*.
Policies decide *whether*.
Guards decide *if the OS allows it*.

If this fails, it is not a logic problem. It is an environment problem.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class WritePermissionError(PermissionError):
    """
    Raised when a path is not writable by the current process.
    """


def ensure_parent_writable(path: Path) -> None:
    """
    Ensure the parent directory of a path is writable.

    This is the most common check before file creation or replacement.

    Parameters
    ----------
    path:
        Target filesystem path.

    Raises
    ------
    WritePermissionError
        If the parent directory does not exist or is not writable.
    """
    parent = path.parent

    LOGGER.debug("Checking parent directory write permission: %s", parent)

    if not parent.exists():
        LOGGER.error("Parent directory does not exist: %s", parent)
        raise WritePermissionError(
            f"Parent directory does not exist: {parent}"
        )

    if not parent.is_dir():
        LOGGER.error("Parent path is not a directory: %s", parent)
        raise WritePermissionError(
            f"Parent path is not a directory: {parent}"
        )

    if not os.access(parent, os.W_OK):
        LOGGER.error("No write permission in directory: %s", parent)
        raise WritePermissionError(
            f"No write permission in directory: {parent}"
        )

    LOGGER.debug("Parent directory writable: %s", parent)


def ensure_target_writable(path: Path) -> None:
    """
    Ensure a target path is writable.

    This is used when modifying an *existing* file.

    Parameters
    ----------
    path:
        Existing filesystem path.

    Raises
    ------
    WritePermissionError
        If the file does not exist or is not writable.
    """
    LOGGER.debug("Checking target file write permission: %s", path)

    if not path.exists():
        LOGGER.error("Target file does not exist: %s", path)
        raise WritePermissionError(
            f"Target file does not exist: {path}"
        )

    if not path.is_file():
        LOGGER.error("Target path is not a file: %s", path)
        raise WritePermissionError(
            f"Target path is not a file: {path}"
        )

    if not os.access(path, os.W_OK):
        LOGGER.error("No write permission on file: %s", path)
        raise WritePermissionError(
            f"No write permission on file: {path}"
        )

    LOGGER.debug("Target file writable: %s", path)