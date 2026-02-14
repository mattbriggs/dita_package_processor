"""
PlanningInput loader utilities.

Hydrates planning_input.json into a validated PlanningInput model.

Responsibilities
----------------
- Read JSON from disk
- Parse JSON
- Validate contract shape strictly
- Construct PlanningInput

No business logic.
No inference.
No silent defaults.
Fail fast on any contract violation.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List

from dita_package_processor.planning.contracts.planning_input import (
    PlanningArtifact,
    PlanningInput,
    PlanningRelationship,
)

LOGGER = logging.getLogger(__name__)


class PlanningInputLoadError(ValueError):
    """Raised when a planning_input.json cannot be loaded or validated."""


# =============================================================================
# Public API
# =============================================================================


def load_planning_input(path: Path) -> PlanningInput:
    """
    Load and hydrate a PlanningInput contract from disk.

    Parameters
    ----------
    path : Path
        Path to planning_input.json.

    Returns
    -------
    PlanningInput

    Raises
    ------
    PlanningInputLoadError
        On any IO, JSON, or contract violation.
    """
    LOGGER.info("Loading PlanningInput contract: %s", path)

    payload = _read_json(path)
    return _hydrate(payload, path)


# =============================================================================
# Internals
# =============================================================================


def _read_json(path: Path) -> Dict[str, Any]:
    """Read and parse JSON file."""
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text)
    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("Failed reading planning_input.json")
        raise PlanningInputLoadError("Invalid planning_input.json") from exc


def _hydrate(payload: Dict[str, Any], path: Path) -> PlanningInput:
    """
    Strictly validate and hydrate contract.

    This is intentionally defensive:
    anything unexpected is a hard failure.
    """
    try:
        # ---------------------------------------------------------
        # Root validation
        # ---------------------------------------------------------

        if not isinstance(payload, dict):
            raise PlanningInputLoadError("Contract must be an object")

        required = {"contract_version", "main_map", "artifacts", "relationships"}
        missing = required - payload.keys()
        if missing:
            raise PlanningInputLoadError(
                f"Missing required contract keys: {sorted(missing)}"
            )

        artifacts_raw = payload["artifacts"]
        relationships_raw = payload["relationships"]

        # ---------------------------------------------------------
        # Type guards (this fixes your failing tests)
        # ---------------------------------------------------------

        if not isinstance(artifacts_raw, list):
            raise PlanningInputLoadError("artifacts must be a list")

        if not isinstance(relationships_raw, list):
            raise PlanningInputLoadError("relationships must be a list")

        # ---------------------------------------------------------
        # Hydration
        # ---------------------------------------------------------

        artifacts: List[PlanningArtifact] = []
        for idx, record in enumerate(artifacts_raw):
            if not isinstance(record, dict):
                raise PlanningInputLoadError(
                    f"artifact[{idx}] must be an object"
                )
            artifacts.append(PlanningArtifact(**record))

        relationships: List[PlanningRelationship] = []
        for idx, record in enumerate(relationships_raw):
            if not isinstance(record, dict):
                raise PlanningInputLoadError(
                    f"relationship[{idx}] must be an object"
                )

            relationships.append(
                PlanningRelationship(
                    source=record["source"],
                    target=record["target"],
                    rel_type=record["type"],
                    pattern_id=record["pattern_id"],
                )
            )

        model = PlanningInput(
            contract_version=payload["contract_version"],
            main_map=payload["main_map"],
            artifacts=artifacts,
            relationships=relationships,
        )

        LOGGER.debug(
            "Hydrated PlanningInput successfully: artifacts=%d relationships=%d",
            len(artifacts),
            len(relationships),
        )

        return model

    except PlanningInputLoadError:
        raise

    except Exception as exc:  # noqa: BLE001
        LOGGER.exception("PlanningInput hydration failed")
        raise PlanningInputLoadError("Contract hydration failed") from exc