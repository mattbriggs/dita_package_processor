"""
planner.py
==========

Deterministic execution planner.

Responsibilities
----------------
- Accept ONLY a PlanningInput contract
- Produce a deterministic Plan
- Perform NO discovery
- Perform NO normalization
- Perform NO schema forgiveness

Design rules
------------
If discovery violates the contract, fail fast.
Planner must be boring and predictable.

Flow
----
PlanningInput → ordered artifacts → PlanActions → Plan
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Dict, List

import jsonschema

from dita_package_processor.planning.contracts.planning_input import PlanningInput
from dita_package_processor.planning.invariants import validate_invariants
from dita_package_processor.planning.layout_rules import resolve_target_path

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Planner
# =============================================================================


class Planner:
    """
    Deterministic planner.

    Consumes only :class:`PlanningInput`.

    Notes
    -----
    This class intentionally does NOT:
        - normalize relationships
        - accept discovery output
        - build DependencyGraph
        - mutate inputs

    All contract enforcement happens upstream.
    """

    # =========================================================================
    # Construction
    # =========================================================================

    def __init__(self, *, schema_path: Path | None = None) -> None:
        """
        Initialize planner.

        Parameters
        ----------
        schema_path:
            Optional custom plan schema path.
        """
        self.schema_path = (
            schema_path
            or Path(__file__).parent / "schema" / "plan.schema.json"
        )

        with self.schema_path.open(encoding="utf-8") as fh:
            self._schema: Dict[str, Any] = json.load(fh)

        LOGGER.info("Planner initialized with schema: %s", self.schema_path)

    # =========================================================================
    # Public API
    # =========================================================================

    def plan(self, planning_input: PlanningInput) -> Dict[str, Any]:
        """
        Generate deterministic execution plan.

        Parameters
        ----------
        planning_input:
            Schema-validated PlanningInput contract.

        Returns
        -------
        Dict[str, Any]
            Plan dictionary compliant with plan.schema.json.
        """
        LOGGER.info("Starting plan generation")

        if not isinstance(planning_input, PlanningInput):
            raise TypeError(
                "Planner.plan() requires PlanningInput, not raw dict"
            )

        artifacts = planning_input.artifacts

        LOGGER.debug("Artifacts received: %d", len(artifacts))

        # ---------------------------------------------------------------------
        # Deterministic ordering
        # ---------------------------------------------------------------------
        # Keep it simple and predictable.
        # Sort by path so output is stable across runs.
        # ---------------------------------------------------------------------

        ordered = sorted(artifacts, key=lambda a: a.path)

        actions: List[Dict[str, Any]] = []
        target_root = Path("target")

        for index, artifact in enumerate(ordered, start=1):
            source_path = Path(artifact.path)

            target_path = resolve_target_path(
                artifact_type=artifact.artifact_type,
                source_path=source_path,
                target_root=target_root,
            )

            action = {
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
        # Build plan
        # ---------------------------------------------------------------------

        plan: Dict[str, Any] = {
            "plan_version": 1,
            "generated_at": datetime.now(UTC).isoformat(),
            "source_discovery": {
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

        LOGGER.info("Plan generation complete: actions=%d", len(actions))

        return plan

    # =========================================================================
    # Validation
    # =========================================================================

    def validate(self, plan: Dict[str, Any]) -> None:
        """
        Validate plan against schema + invariants.

        Parameters
        ----------
        plan:
            Plan dictionary.
        """
        LOGGER.debug("Validating plan schema")

        jsonschema.validate(instance=plan, schema=self._schema)

        LOGGER.debug("Validating invariants")

        validate_invariants(plan)

        LOGGER.info("Plan validated successfully")