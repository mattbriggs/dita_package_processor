"""
Filesystem mutation policies.

This module defines overwrite and replacement strategies for execution.
It answers one question:

    "Given a target path and an operation, is this allowed?"

Responsibilities:
- Enforce overwrite protection
- Support replace vs deny semantics
- Centralize mutation decision logic
- Provide deterministic, auditable behavior
- Produce *classifiable* safety failures (never anonymous)
"""

from __future__ import annotations

import logging
from enum import Enum
from pathlib import Path
from typing import Literal

LOGGER = logging.getLogger(__name__)

__all__ = [
    "PolicyViolationError",
    "OverwritePolicy",
    "MutationPolicy",
]


class PolicyViolationError(RuntimeError):
    """
    Raised when a filesystem mutation violates execution policy.

    This error is intentionally semantic. It is not a generic failure.
    It represents a *policy-level safety event* and must be translated
    by the execution layer into:

        status="failed"
        failure_type="policy_violation"
    """

    failure_type: Literal["policy_violation"] = "policy_violation"

    def __init__(self, message: str, *, target: Path | None = None) -> None:
        self.target = target
        super().__init__(message)


class OverwritePolicy(str, Enum):
    """
    Canonical overwrite policies.

    These are *global invariants* for filesystem mutation.
    """

    DENY = "deny"
    REPLACE = "replace"
    SKIP = "skip"


class MutationPolicy:
    """
    Filesystem mutation policy evaluator.

    This class encapsulates overwrite behavior and makes mutation decisions
    explicit, predictable, and testable.

    It must never perform mutations.
    It only authorizes or rejects them.
    """

    def __init__(self, overwrite: OverwritePolicy) -> None:
        """
        Initialize a mutation policy.

        Parameters
        ----------
        overwrite:
            Overwrite behavior policy.
        """
        if not isinstance(overwrite, OverwritePolicy):
            raise TypeError(
                f"overwrite must be an OverwritePolicy, got {type(overwrite)!r}"
            )

        self.overwrite = overwrite

        LOGGER.debug(
            "MutationPolicy initialized with overwrite=%s",
            overwrite.value,
        )

    def validate_target(self, target: Path) -> None:
        """
        Validate whether a filesystem target can be written.

        Parameters
        ----------
        target:
            Fully resolved filesystem path.

        Raises
        ------
        PolicyViolationError
            If the policy forbids this mutation.

        Notes
        -----
        This method never mutates the filesystem.
        It only authorizes or rejects an action.

        Any raised PolicyViolationError must later be converted into:

            ExecutionActionResult(
                status="failed",
                failure_type="policy_violation",
                ...
            )
        """
        if not isinstance(target, Path):
            raise TypeError(
                f"target must be a pathlib.Path, got {type(target)!r}"
            )

        exists = target.exists()

        LOGGER.debug(
            "Validating target: %s exists=%s policy=%s",
            target,
            exists,
            self.overwrite.value,
        )

        # New files are always safe to create
        if not exists:
            return

        # Existing target → policy decides
        if self.overwrite is OverwritePolicy.DENY:
            LOGGER.error("Overwrite denied for target: %s", target)
            raise PolicyViolationError(
                f"Overwrite denied for existing path: {target}",
                target=target,
            )

        if self.overwrite is OverwritePolicy.SKIP:
            LOGGER.info("Write skipped by policy for target: %s", target)
            raise PolicyViolationError(
                f"Write skipped for existing path: {target}",
                target=target,
            )

        if self.overwrite is OverwritePolicy.REPLACE:
            LOGGER.debug("Overwrite permitted for target: %s", target)
            return

        # Enum exhaustiveness guard
        raise PolicyViolationError(
            f"Unknown overwrite policy: {self.overwrite}",
            target=target,
        )