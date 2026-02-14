"""
validation.py

Materialization validation rules for the DITA Package Processor.

This module enforces preconditions required for safe materialization.
It performs *pure validation* only.

Materialization validation answers:

- "Is this plan suitable for producing a target package?"
- "Is this target location safe to use?"

This module does NOT:
- create directories
- modify the filesystem
- inspect execution reports
- infer intent

It exists to fail loudly *before* irreversible work begins.
"""

from __future__ import annotations

import logging
from pathlib import Path

from dita_package_processor.planning.models import Plan

LOGGER = logging.getLogger(__name__)


class MaterializationValidationError(RuntimeError):
    """
    Raised when materialization preconditions are not satisfied.

    These are hard failures that indicate unsafe or invalid input.
    """


class MaterializationValidator:
    """
    Validates materialization preconditions.

    This class encapsulates all rules required to decide whether
    a target directory *may* be materialized safely.

    Design constraints:
    - deterministic
    - side-effect free
    - explicit failure modes
    """

    def __init__(
        self,
        *,
        plan: Plan,
        target_root: Path,
    ) -> None:
        """
        Initialize the validator.

        :param plan: Validated execution plan.
        :param target_root: Intended materialization root directory.
        """
        self.plan = plan
        self.target_root = target_root

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """
        Validate all materialization preconditions.

        :raises MaterializationValidationError:
            If any precondition fails.
        """
        LOGGER.debug("Validating materialization preconditions")

        self._validate_plan()
        self._validate_target_root()

        LOGGER.debug("Materialization validation passed")

    # ------------------------------------------------------------------
    # Validation rules
    # ------------------------------------------------------------------

    def _validate_plan(self) -> None:
        """
        Ensure the plan is actionable for materialization.
        """
        LOGGER.debug("Validating plan suitability")

        if not self.plan.actions:
            raise MaterializationValidationError(
                "Plan contains no actions; materialization is meaningless"
            )

    def _validate_target_root(self) -> None:
        """
        Ensure the target root is structurally safe.

        The directory may or may not exist.
        If it exists, it must be a directory.
        """
        LOGGER.debug("Validating target root: %s", self.target_root)

        if self.target_root.exists() and not self.target_root.is_dir():
            raise MaterializationValidationError(
                f"Target root exists but is not a directory: {self.target_root}"
            )


__all__ = [
    "MaterializationValidator",
    "MaterializationValidationError",
]