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

        # Collect action templates from all plugins (no "id" fields yet).
        from dita_package_processor.plugins.registry import get_plugin_registry

        plugin_registry = get_plugin_registry()

        raw_actions: List[Dict[str, Any]] = []

        for artifact in ordered:
            emitted = plugin_registry.emit_actions_for(artifact, planning_input)
            raw_actions.extend(emitted)

            LOGGER.debug(
                "Artifact %s → %d action(s) emitted",
                artifact.path,
                len(emitted),
            )

        # Assign globally unique, deterministic IDs.
        actions: List[Dict[str, Any]] = []
        for index, action_template in enumerate(raw_actions, start=1):
            action: Dict[str, Any] = {"id": f"action-{index:04d}", **action_template}
            actions.append(action)

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