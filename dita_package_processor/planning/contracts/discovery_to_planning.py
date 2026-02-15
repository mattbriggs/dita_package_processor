"""
Discovery → PlanningInput normalization.

This module defines the ONLY supported bridge between discovery output and
the planning subsystem. It is a strict, schema-locked contract boundary.

Rules
-----
- No optional behavior
- No guessing
- No silent defaults
- Fail fast on ambiguity
- Planning MUST NEVER read discovery directly

This file is the wall.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Set

import jsonschema

from dita_package_processor.planning.contracts.errors import (
    PlanningContractError,
)
from dita_package_processor.planning.contracts.planning_input import (
    PlanningArtifact,
    PlanningInput,
    PlanningRelationship,
)

LOGGER = logging.getLogger(__name__)

CONTRACT_VERSION = "planning.input.v1"

ALLOWED_ARTIFACT_TYPES: Set[str] = {"map", "topic", "media"}

# Planning semantics:
#   MAIN  → exactly one root map
#   None  → everything else
ALLOWED_CLASSIFICATIONS: Set[str | None] = {"MAIN", None}

# deterministic aliasing only (no guessing)
_CLASSIFICATION_ALIASES = {
    "MAIN_MAP": "MAIN",
}

_SCHEMA_PATH = Path(__file__).parent / "planning_input.schema.json"


# =============================================================================
# Public API
# =============================================================================


def normalize_discovery_report(discovery: Dict[str, Any]) -> PlanningInput:
    """
    Convert a discovery report into a validated PlanningInput contract.

    This is the ONLY legal bridge between discovery and planning.

    Parameters
    ----------
    discovery : Dict[str, Any]
        Raw discovery output.

    Returns
    -------
    PlanningInput

    Raises
    ------
    PlanningContractError
        On any structural or semantic violation.
    """
    LOGGER.info("Normalizing discovery → planning contract")

    if not isinstance(discovery, dict):
        raise PlanningContractError(
            "Discovery payload must be an object"
        )

    _require_keys(
        discovery,
        {"artifacts", "relationships", "summary"},
        context="discovery",
    )

    artifacts_raw = discovery["artifacts"]
    relationships_raw = discovery["relationships"]

    if not isinstance(artifacts_raw, list):
        raise PlanningContractError(
            "discovery.artifacts must be a list"
        )

    if not isinstance(relationships_raw, list):
        raise PlanningContractError(
            "discovery.relationships must be a list"
        )

    LOGGER.debug("Artifacts discovered: %d", len(artifacts_raw))
    LOGGER.debug("Relationships discovered: %d", len(relationships_raw))

    artifacts = _normalize_artifacts(artifacts_raw)
    artifact_paths = {a.path for a in artifacts}

    main_map = _select_main_map(artifacts)

    relationships = _normalize_relationships(relationships_raw)
    _validate_relationship_endpoints(
        relationships,
        artifact_paths,
    )

    try:
        planning_input = PlanningInput(
            contract_version=CONTRACT_VERSION,
            main_map=main_map,
            artifacts=artifacts,
            relationships=relationships,
        )
    except (ValueError, TypeError) as exc:
        raise PlanningContractError(
            f"PlanningInput construction failed: {exc}"
        ) from exc

    _validate_against_schema(planning_input)

    LOGGER.info(
        "PlanningInput validated: main_map=%s artifacts=%d relationships=%d",
        planning_input.main_map,
        len(planning_input.artifacts),
        len(planning_input.relationships),
    )

    return planning_input


# =============================================================================
# Schema enforcement
# =============================================================================


def _validate_against_schema(planning_input: PlanningInput) -> None:
    """
    Validate PlanningInput against JSON Schema.
    """
    LOGGER.debug(
        "Validating PlanningInput against schema: %s",
        _SCHEMA_PATH,
    )

    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        schema = json.load(fh)

    try:
        jsonschema.validate(
            planning_input.to_dict(),
            schema,
        )
    except jsonschema.ValidationError as exc:
        raise PlanningContractError(
            f"PlanningInput schema violation: {exc.message}"
        ) from exc


# =============================================================================
# Helpers
# =============================================================================


def _require_keys(
    data: Dict[str, Any],
    keys: Set[str],
    *,
    context: str,
) -> None:
    """
    Ensure required keys exist.
    """
    missing = sorted(k for k in keys if k not in data)
    if missing:
        raise PlanningContractError(
            f"{context} missing required keys: {missing}"
        )


# =============================================================================
# Classification normalization
# =============================================================================


def _normalize_classification(value: Any) -> str | None:
    """
    Collapse discovery classifications into planning semantics.

    Planning only understands:
        - "MAIN"
        - None

    Everything else deterministically becomes None.
    """
    if value in (None, "", "NONE"):
        return None

    if value in _CLASSIFICATION_ALIASES:
        value = _CLASSIFICATION_ALIASES[value]

    if value == "MAIN":
        return "MAIN"

    return None


# =============================================================================
# Artifact normalization
# =============================================================================


def _normalize_artifacts(
    raw: List[Dict[str, Any]],
) -> List[PlanningArtifact]:
    """
    Normalize discovery artifacts into PlanningArtifact objects.
    """
    artifacts: List[PlanningArtifact] = []

    for idx, record in enumerate(raw):
        context = f"artifact[{idx}]"

        if not isinstance(record, dict):
            raise PlanningContractError(
                f"{context} must be an object"
            )

        _require_keys(
            record,
            {"path", "artifact_type"},
            context=context,
        )

        path = record["path"]
        artifact_type = record["artifact_type"]

        if artifact_type not in ALLOWED_ARTIFACT_TYPES:
            raise PlanningContractError(
                f"{context}.artifact_type invalid: {artifact_type}"
            )

        classification = _normalize_classification(
            record.get("classification")
        )

        metadata = record.get("metadata") or {}
        if not isinstance(metadata, dict):
            raise PlanningContractError(
                f"{context}.metadata must be object"
            )

        try:
            artifact = PlanningArtifact(
                path=str(path),
                artifact_type=str(artifact_type),
                classification=classification,
                metadata=metadata,
            )
        except (ValueError, TypeError) as exc:
            raise PlanningContractError(
                f"{context} invalid: {exc}"
            ) from exc

        artifacts.append(artifact)

    return artifacts


# =============================================================================
# Main map selection
# =============================================================================


def _select_main_map(
    artifacts: List[PlanningArtifact],
) -> str:
    """
    Select exactly one MAIN map.
    """
    main_maps = [
        a.path
        for a in artifacts
        if a.artifact_type == "map"
        and a.classification == "MAIN"
    ]

    LOGGER.debug("MAIN map candidates: %s", main_maps)

    if len(main_maps) != 1:
        raise PlanningContractError(
            "Exactly one artifact must be classified as MAIN map, "
            f"found {len(main_maps)}"
        )

    return main_maps[0]


# =============================================================================
# Relationship normalization
# =============================================================================


def _normalize_relationships(
    raw: List[Dict[str, Any]],
) -> List[PlanningRelationship]:
    """
    Normalize relationships with strict field enforcement.
    """
    relationships: List[PlanningRelationship] = []

    for idx, record in enumerate(raw):
        context = f"relationship[{idx}]"

        if not isinstance(record, dict):
            raise PlanningContractError(
                f"{context} must be an object"
            )

        _require_keys(
            record,
            {"source", "target", "type", "pattern_id"},
            context=context,
        )

        try:
            relationship = PlanningRelationship(
                source=str(record["source"]),
                target=str(record["target"]),
                rel_type=str(record["type"]),
                pattern_id=str(record["pattern_id"]),
            )
        except (ValueError, TypeError) as exc:
            raise PlanningContractError(
                f"{context} invalid: {exc}"
            ) from exc

        relationships.append(relationship)

    return relationships


# =============================================================================
# Endpoint validation
# =============================================================================


def _validate_relationship_endpoints(
    relationships: List[PlanningRelationship],
    artifact_paths: Set[str],
) -> None:
    """
    Ensure relationships reference known artifacts.
    """
    unknown: List[str] = []

    for rel in relationships:
        if rel.source not in artifact_paths:
            unknown.append(rel.source)
        if rel.target not in artifact_paths:
            unknown.append(rel.target)

    if unknown:
        raise PlanningContractError(
            "Relationships reference unknown artifacts: "
            f"{sorted(set(unknown))}"
        )