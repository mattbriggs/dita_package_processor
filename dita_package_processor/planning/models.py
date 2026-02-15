"""
Planning data models.

This module defines the immutable data structures that represent a validated
execution plan.

Design Principles
-----------------
- Declarative only.
- No execution state.
- No mutation.
- No filesystem logic.
- No runtime side effects.

Planning describes intent.
Execution describes effects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Union

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Action Types
# =============================================================================


class ActionType(str, Enum):
    """
    Canonical set of allowed plan action types.

    This enum is the single source of truth for action identity.
    """

    COPY_MAP = "copy_map"
    COPY_TOPIC = "copy_topic"
    COPY_MEDIA = "copy_media"
    NOOP = "noop"
    SKIP = "skip"

    @classmethod
    def validate(cls, value: Union[str, "ActionType"]) -> str:
        """
        Validate and normalize an action type.

        Parameters
        ----------
        value:
            String or ActionType.

        Returns
        -------
        str
            Canonical action type string.

        Raises
        ------
        ValueError
            If the action type is invalid.
        """
        try:
            normalized = cls(value).value
            LOGGER.debug("Validated action type: %s", normalized)
            return normalized
        except ValueError as exc:
            LOGGER.error("Invalid action type: %s", value)
            raise ValueError(f"Invalid action type: {value}") from exc


# =============================================================================
# Plan Source Metadata
# =============================================================================


@dataclass(frozen=True)
class PlanSourceDiscovery:
    """
    Metadata describing the discovery input that produced the plan.

    Parameters
    ----------
    path:
        Root path of discovery input.
    schema_version:
        Schema version used during discovery.
    artifact_count:
        Total artifacts discovered.
    """

    path: Union[str, Path]
    schema_version: int
    artifact_count: int

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize discovery metadata.

        Returns
        -------
        Dict[str, Any]
        """
        return {
            "path": str(self.path),
            "schema_version": self.schema_version,
            "artifact_count": self.artifact_count,
        }


# =============================================================================
# Plan Intent
# =============================================================================


@dataclass(frozen=True)
class PlanIntent:
    """
    High-level intent of the plan.

    Parameters
    ----------
    target:
        Logical execution target (e.g. "analysis_only").
    description:
        Human-readable explanation of plan intent.
    """

    target: str
    description: str

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize plan intent.

        Returns
        -------
        Dict[str, Any]
        """
        return {
            "target": self.target,
            "description": self.description,
        }


# =============================================================================
# Plan Action
# =============================================================================


@dataclass(frozen=True)
class PlanAction:
    """
    Declarative execution action.

    This structure represents intent only.
    It contains no execution state.
    """

    id: str
    type: str
    target: str
    reason: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    derived_from_evidence: List[str] = field(default_factory=list)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        normalized_type = ActionType.validate(self.type)
        object.__setattr__(self, "type", normalized_type)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize PlanAction.

        Returns
        -------
        Dict[str, Any]
        """
        return {
            "id": self.id,
            "type": self.type,
            "target": self.target,
            "reason": self.reason,
            "parameters": dict(self.parameters),
            "derived_from_evidence": list(self.derived_from_evidence),
        }

    # -------------------------------------------------------------------------
    # Explicit constructors
    # -------------------------------------------------------------------------

    @classmethod
    def copy_map(
        cls,
        *,
        id: str,
        source_path: str,
        target_path: str,
        reason: str,
    ) -> "PlanAction":
        """
        Create COPY_MAP action.
        """
        return cls(
            id=id,
            type=ActionType.COPY_MAP.value,
            target=target_path,
            reason=reason,
            parameters={
                "source_path": source_path,
                "target_path": target_path,
            },
        )

    @classmethod
    def copy_topic(
        cls,
        *,
        id: str,
        source_path: str,
        target_path: str,
        reason: str,
    ) -> "PlanAction":
        """
        Create COPY_TOPIC action.
        """
        return cls(
            id=id,
            type=ActionType.COPY_TOPIC.value,
            target=target_path,
            reason=reason,
            parameters={
                "source_path": source_path,
                "target_path": target_path,
            },
        )

    @classmethod
    def copy_media(
        cls,
        *,
        id: str,
        source_path: str,
        target_path: str,
        reason: str,
    ) -> "PlanAction":
        """
        Create COPY_MEDIA action.
        """
        return cls(
            id=id,
            type=ActionType.COPY_MEDIA.value,
            target=target_path,
            reason=reason,
            parameters={
                "source_path": source_path,
                "target_path": target_path,
            },
        )


# =============================================================================
# Plan Root Model
# =============================================================================


@dataclass(frozen=True)
class Plan:
    """
    Immutable execution plan.

    A Plan is:
    - Deterministic
    - Declarative
    - Immutable
    - Execution-agnostic
    """

    plan_version: int
    generated_at: datetime
    source_discovery: PlanSourceDiscovery
    intent: PlanIntent
    actions: List[PlanAction]
    invariants: List[Dict[str, Any]] = field(default_factory=list)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.generated_at, datetime):
            raise TypeError("generated_at must be datetime")

        if not isinstance(self.actions, list):
            raise TypeError("actions must be list")

        LOGGER.debug(
            "Plan instantiated version=%s actions=%d",
            self.plan_version,
            len(self.actions),
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize plan to JSON-compatible dictionary.

        Returns
        -------
        Dict[str, Any]
        """
        return {
            "plan_version": self.plan_version,
            "generated_at": self.generated_at.isoformat(),
            "source_discovery": self.source_discovery.to_dict(),
            "intent": self.intent.to_dict(),
            "actions": [action.to_dict() for action in self.actions],
            "invariants": list(self.invariants),
        }