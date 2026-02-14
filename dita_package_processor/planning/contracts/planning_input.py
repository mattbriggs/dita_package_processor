"""
Planning input contract.

This module defines the schema-locked input that the planning subsystem is
allowed to consume. Planning MUST NOT consume discovery output directly.

Contract goals
--------------
- Explicit
- Deterministic
- Schema-validatable
- No guessing
- No forgiveness
- No optional behavior

PlanningInput is the hard boundary object between discovery and planning.
Anything not represented here is not permitted to influence planning.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

LOGGER = logging.getLogger(__name__)

ArtifactType = Literal["map", "topic", "media"]


# =============================================================================
# Artifact Contract
# =============================================================================


@dataclass(frozen=True)
class PlanningArtifact:
    """
    Normalized planning artifact.

    This is the strict, contract-safe representation of a discovery artifact.

    Planning is intentionally restricted to this minimal view to prevent:
        - re-discovery
        - semantic inference
        - filesystem logic

    Parameters
    ----------
    path:
        Relative artifact path in the package.
    artifact_type:
        One of: ``map``, ``topic``, ``media``.
    classification:
        Optional classification string (e.g., ``MAIN``).
        Planning may ONLY use this for selecting ``main_map``.
    metadata:
        Opaque metadata preserved from discovery. Planning MUST NOT interpret
        unless explicitly declared by downstream rules.
    """

    path: str
    artifact_type: ArtifactType
    classification: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize artifact to contract JSON.

        No coercion or mutation occurs here. The contract layer guarantees
        type correctness upstream. This method must remain a pure projection.

        Returns
        -------
        Dict[str, Any]
            Schema-compatible artifact representation.
        """
        LOGGER.debug(
            "Serialize PlanningArtifact path=%s type=%s classification=%s",
            self.path,
            self.artifact_type,
            self.classification,
        )

        return {
            "path": self.path,
            "artifact_type": self.artifact_type,
            "classification": self.classification,
            # 🔒 DO NOT COERCE
            "metadata": self.metadata,
        }


# =============================================================================
# Relationship Contract
# =============================================================================


@dataclass(frozen=True)
class PlanningRelationship:
    """
    Planning relationship edge.

    Stable, normalized edge representation used by planning.

    This mirrors the discovery relationship contract but hides the discovery
    graph implementation details.

    Parameters
    ----------
    source:
        Source artifact path.
    target:
        Target artifact path.
    rel_type:
        Semantic relationship type (e.g., ``topicref``).
    pattern_id:
        Discovery pattern identifier for traceability.
    """

    source: str
    target: str
    rel_type: str
    pattern_id: str

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize relationship to contract JSON.

        Returns
        -------
        Dict[str, Any]
            Schema-compatible relationship representation.
        """
        LOGGER.debug(
            "Serialize PlanningRelationship %s -> %s type=%s pattern=%s",
            self.source,
            self.target,
            self.rel_type,
            self.pattern_id,
        )

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

    Parameters
    ----------
    contract_version:
        Fixed version string identifying the schema contract.
    main_map:
        Path of the unique MAIN map.
    artifacts:
        All artifacts participating in planning.
    relationships:
        All relationships planning may reason about.
    """

    contract_version: str
    main_map: str
    artifacts: List[PlanningArtifact]
    relationships: List[PlanningRelationship]

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize PlanningInput to contract JSON.

        This is the canonical wire format between discovery and planning.

        Returns
        -------
        Dict[str, Any]
            Schema-compatible planning_input.json representation.
        """
        LOGGER.debug(
            "Serialize PlanningInput version=%s main_map=%s artifacts=%d relationships=%d",
            self.contract_version,
            self.main_map,
            len(self.artifacts),
            len(self.relationships),
        )

        return {
            "contract_version": self.contract_version,
            "main_map": self.main_map,
            "artifacts": [a.to_dict() for a in self.artifacts],
            "relationships": [r.to_dict() for r in self.relationships],
        }