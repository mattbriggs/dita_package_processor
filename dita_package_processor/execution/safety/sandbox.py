"""
Filesystem sandbox enforcement.

This module defines the root safety boundary for all filesystem mutation.
Every executor and handler must operate inside a sandbox root. Any attempt
to resolve paths outside this boundary is treated as a fatal error.

Responsibilities:
- Normalize and resolve filesystem paths
- Enforce root containment
- Prevent path traversal and accidental global writes
"""

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class SandboxViolationError(RuntimeError):
    """
    Raised when a path escapes the sandbox root.
    """


class Sandbox:
    """
    Filesystem sandbox.

    A sandbox defines a single root directory inside which all filesystem
    operations must remain. Any resolved path outside this root is rejected.

    This is the first and most important safety boundary in execution.
    """

    def __init__(self, root: Path) -> None:
        """
        Initialize the sandbox.

        Parameters
        ----------
        root:
            Root directory of the sandbox.
        """
        self.root = root.resolve()

        LOGGER.debug("Initializing sandbox with root: %s", self.root)

        if not self.root.exists():
            raise SandboxViolationError(
                f"Sandbox root does not exist: {self.root}"
            )

        if not self.root.is_dir():
            raise SandboxViolationError(
                f"Sandbox root is not a directory: {self.root}"
            )

    def resolve(self, path: Path) -> Path:
        """
        Resolve a path inside the sandbox.

        Parameters
        ----------
        path:
            Relative or absolute path to resolve.

        Returns
        -------
        Path
            Fully resolved path guaranteed to be inside the sandbox.

        Raises
        ------
        SandboxViolationError
            If the resolved path escapes the sandbox root.
        """
        candidate = path

        # Force relative paths to be relative to sandbox root
        if not path.is_absolute():
            candidate = self.root / path

        resolved = candidate.resolve()

        LOGGER.debug(
            "Resolving sandbox path: input=%s resolved=%s",
            path,
            resolved,
        )

        if not self._is_inside_root(resolved):
            LOGGER.error(
                "Sandbox violation: %s escapes root %s",
                resolved,
                self.root,
            )
            raise SandboxViolationError(
                f"Path escapes sandbox root: {resolved}"
            )

        return resolved

    def _is_inside_root(self, path: Path) -> bool:
        """
        Check whether a path is inside the sandbox root.

        Parameters
        ----------
        path:
            Resolved filesystem path.

        Returns
        -------
        bool
            True if path is contained within the sandbox.
        """
        try:
            path.relative_to(self.root)
            return True
        except ValueError:
            return False