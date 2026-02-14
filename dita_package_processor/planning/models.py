"""
Planning data models.

These models describe a validated execution plan.
They contain NO execution results, NO timestamps, and NO runtime state.

Planning describes intent.
Execution describes effects.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Action Types
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Plan Source Metadata
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanSourceDiscovery:
    """
    Metadata describing the discovery input that produced the plan.
    """

    path: Union[str, Path]
    schema_version: int
    artifact_count: int


# ---------------------------------------------------------------------------
# Plan Intent
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanIntent:
    """
    High-level intent of the plan.
    """

    target: str
    description: str


# ---------------------------------------------------------------------------
# Plan Action
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanAction:
    """
    Represents a single executable action in a plan.

    This is a declarative description, not an execution record.
    """

    id: str
    type: Union[str, ActionType]
    target: str
    reason: str

    parameters: Dict[str, Any] = field(default_factory=dict)
    derived_from_evidence: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "type", ActionType(self.type).value)
        except ValueError as exc:
            LOGGER.error("Invalid action type: %s", self.type)
            raise ValueError(f"Invalid action type: {self.type}") from exc

    # --------------------------------------------------
    # Explicit constructors
    # --------------------------------------------------

    @classmethod
    def copy_map(
        cls,
        *,
        id: str,
        source_path: str,
        target_path: str,
        reason: str,
    ) -> "PlanAction":
        return cls(
            id=id,
            type=ActionType.COPY_MAP,
            target=source_path,
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
        return cls(
            id=id,
            type=ActionType.COPY_TOPIC,
            target=source_path,
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
        return cls(
            id=id,
            type=ActionType.COPY_MEDIA,
            target=source_path,
            reason=reason,
            parameters={
                "source_path": source_path,
                "target_path": target_path,
            },
        )


# ---------------------------------------------------------------------------
# Plan Root Model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Plan:
    """
    Immutable execution plan produced by the planner.

    This is a *declarative* structure.
    It does not know if it has been executed.
    It does not know if it succeeded.
    It does not know time.
    It is timeless.
    """

    plan_version: int
    generated_at: datetime
    source_discovery: PlanSourceDiscovery
    intent: PlanIntent
    actions: List[PlanAction]
    invariants: List[Dict[str, Any]] = field(default_factory=list)