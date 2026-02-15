"""
Planning input contract.

Defines the schema-locked boundary between discovery and planning.

Planning MUST NOT consume discovery output directly.

Contract goals
--------------
- Explicit
- Deterministic
- Schema-validatable
- No guessing
- No forgiveness
- No optional behavior

``PlanningInput`` is the hard boundary object between discovery and planning.
Anything not represented here is not permitted to influence planning.
"""

from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

LOGGER = logging.getLogger(__name__)

ArtifactType = Literal["map", "topic", "media"]

_ALLOWED_ARTIFACT_TYPES = {"map", "topic", "media"}


# =============================================================================
# Artifact Contract
# =============================================================================


@dataclass(frozen=True)
class PlanningArtifact:
    """
    Normalized planning artifact.

    This is the strict, contract-safe representation of a discovery artifact.

    Planning is intentionally restricted to this minimal view to prevent:

    - Re-discovery
    - Semantic inference
    - Filesystem logic
    """

    path: str
    artifact_type: ArtifactType
    classification: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not isinstance(self.path, str) or not self.path:
            raise ValueError("PlanningArtifact.path must be non-empty string")

        if self.artifact_type not in _ALLOWED_ARTIFACT_TYPES:
            raise ValueError(
                f"Invalid artifact_type: {self.artifact_type}"
            )

        if self.classification is not None and not isinstance(
            self.classification, str
        ):
            raise ValueError(
                "PlanningArtifact.classification must be string or None"
            )

        if not isinstance(self.metadata, dict):
            raise ValueError(
                "PlanningArtifact.metadata must be a dictionary"
            )

        LOGGER.debug(
            "PlanningArtifact validated path=%s type=%s classification=%s",
            self.path,
            self.artifact_type,
            self.classification,
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "path": self.path,
            "artifact_type": self.artifact_type,
            "classification": self.classification,
            "metadata": copy.deepcopy(self.metadata),
        }


# =============================================================================
# Relationship Contract
# =============================================================================


@dataclass(frozen=True)
class PlanningRelationship:
    """
    Stable relationship edge used by planning.
    """

    source: str
    target: str
    rel_type: str
    pattern_id: str

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("PlanningRelationship.source must be non-empty")

        if not self.target:
            raise ValueError("PlanningRelationship.target must be non-empty")

        if not self.rel_type:
            raise ValueError("PlanningRelationship.rel_type required")

        if not self.pattern_id:
            raise ValueError("PlanningRelationship.pattern_id required")

        LOGGER.debug(
            "PlanningRelationship validated %s -> %s type=%s",
            self.source,
            self.target,
            self.rel_type,
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "type": self.rel_type,
            "pattern_id": self.pattern_id,
        }


# =============================================================================
# Root Contract
# =============================================================================


@dataclass(frozen=True)
class PlanningInput:
    """
    Planning input contract root.

    This is the ONLY structure planning is allowed to consume.
    """

    contract_version: str
    main_map: str
    artifacts: List[PlanningArtifact]
    relationships: List[PlanningRelationship]

    # -------------------------------------------------------------------------
    # Validation
    # -------------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.contract_version:
            raise ValueError("PlanningInput.contract_version required")

        if not isinstance(self.main_map, str) or not self.main_map:
            raise ValueError("PlanningInput.main_map must be non-empty string")

        if not isinstance(self.artifacts, list):
            raise ValueError("PlanningInput.artifacts must be list")

        if not isinstance(self.relationships, list):
            raise ValueError("PlanningInput.relationships must be list")

        if not self.artifacts:
            raise ValueError("PlanningInput.artifacts cannot be empty")

        # NOTE:
        # We intentionally DO NOT enforce that main_map must appear in artifacts.
        # That invariant belongs to discovery.
        # Planner must remain agnostic and deterministic.

        LOGGER.debug(
            "PlanningInput validated version=%s main_map=%s artifacts=%d relationships=%d",
            self.contract_version,
            self.main_map,
            len(self.artifacts),
            len(self.relationships),
        )

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "main_map": self.main_map,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "relationships": [
                r.to_dict() for r in self.relationships
            ],
        }