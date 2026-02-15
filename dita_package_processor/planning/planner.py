"""
planner.py
==========

Deterministic execution planner.

Responsibilities
----------------
- Accept ONLY a PlanningInput contract
- Produce a deterministic Plan dictionary
- Perform NO discovery
- Perform NO normalization
- Perform NO schema forgiveness

Planner is intentionally boring.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import jsonschema

from dita_package_processor.planning.contracts.planning_input import (
    PlanningInput,
)
from dita_package_processor.planning.invariants import validate_invariants
from dita_package_processor.planning.layout_rules import resolve_target_path

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Planner
# =============================================================================


class Planner:
    """
    Deterministic planner.

    Consumes only PlanningInput.
    Emits stable copy actions.
    """

    # =========================================================================
    # Construction
    # =========================================================================

    def __init__(self, *, schema_path: Path | None = None) -> None:
        self.schema_path = (
            schema_path
            or Path(__file__).parent / "schema" / "plan.schema.json"
        ).resolve()

        if not self.schema_path.exists():
            raise FileNotFoundError(
                f"Missing plan schema: {self.schema_path}"
            )

        with self.schema_path.open(encoding="utf-8") as fh:
            self._schema: Dict[str, Any] = json.load(fh)

        LOGGER.debug("Planner initialized with schema=%s", self.schema_path)

    # =========================================================================
    # Public API
    # =========================================================================

    def plan(self, planning_input: PlanningInput) -> Dict[str, Any]:
        """
        Generate deterministic execution plan.
        """

        LOGGER.info("Starting plan generation")

        if not isinstance(planning_input, PlanningInput):
            raise TypeError(
                "Planner.plan() requires PlanningInput instance"
            )

        artifacts = planning_input.artifacts

        LOGGER.debug("Artifacts received: %d", len(artifacts))

        # ---------------------------------------------------------------------
        # Deterministic ordering
        # ---------------------------------------------------------------------

        ordered = sorted(artifacts, key=lambda a: a.path)

        actions: List[Dict[str, Any]] = []

        logical_target_root = Path("target")

        for index, artifact in enumerate(ordered, start=1):
            source_path = Path(artifact.path)

            target_path = resolve_target_path(
                artifact_type=artifact.artifact_type,
                source_path=source_path,
                target_root=logical_target_root,
            )

            action: Dict[str, Any] = {
                "id": f"copy-{index:04d}",
                "type": f"copy_{artifact.artifact_type}",
                "target": str(target_path),
                "parameters": {
                    "source_path": str(source_path),
                    "target_path": str(target_path),
                },
                "reason": "Deterministic artifact ordering",
                "derived_from_evidence": [],
            }

            actions.append(action)

            LOGGER.debug(
                "Action emitted: %s -> %s",
                source_path,
                target_path,
            )

        # ---------------------------------------------------------------------
        # Plan object
        # ---------------------------------------------------------------------

        plan: Dict[str, Any] = {
            "plan_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "source_discovery": {
                # Schema requires 'path'
                "path": planning_input.main_map,
                "schema_version": 1,
                "artifact_count": len(artifacts),
            },
            "intent": {
                "target": "analysis_only",
                "description": "Deterministic contract-backed plan",
            },
            "actions": actions,
            "invariants": [],
        }

        LOGGER.info("Plan generation complete actions=%d", len(actions))

        self.validate(plan)

        return plan

    # =========================================================================
    # Validation
    # =========================================================================

    def validate(self, plan: Dict[str, Any]) -> None:
        """
        Validate plan against schema + invariants.
        """
        LOGGER.debug("Validating plan schema")

        jsonschema.validate(instance=plan, schema=self._schema)

        LOGGER.debug("Validating invariants")

        validate_invariants(plan)

        LOGGER.info("Plan validated successfully")