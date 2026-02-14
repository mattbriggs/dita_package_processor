"""
Planning contract boundary errors.

This module defines hard-failure exceptions raised when a schema-locked
planning contract cannot be produced or validated.

These errors represent violations of architectural boundaries and are
never recoverable. They must terminate the pipeline immediately.
"""

from __future__ import annotations

import logging
from typing import Optional

LOGGER = logging.getLogger(__name__)


class PlanningContractError(ValueError):
    """
    Raised when strict contract normalization fails.

    Indicates a violation of a schema-locked contract boundary between
    discovery and planning.

    These errors mean:
        - The discovery output is invalid or incomplete
        - The normalization bridge failed
        - Planning cannot safely proceed
    """

    def __init__(self, message: str, *, context: Optional[str] = None) -> None:
        """
        Initialize a PlanningContractError.

        :param message: Human-readable error message.
        :param context: Optional contract stage or object reference.
        """
        self.context = context
        full_message = message

        if context:
            full_message = f"[{context}] {message}"

        LOGGER.error("PlanningContractError raised: %s", full_message)
        super().__init__(full_message)