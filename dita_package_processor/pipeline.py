"""
pipeline.py
===========

Pipeline orchestration for the DITA Package Processor.

Coordinates:

    Discovery → Planning → Materialization → Execution

The pipeline is the ONLY execution boundary.

CLI layers must never directly instantiate executors.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Optional

from dita_package_processor.discovery.models import DiscoveryInventory
from dita_package_processor.materialization.orchestrator import (
    MaterializationOrchestrator,
)
from dita_package_processor.orchestration import (
    get_executor,
    run_discovery,
    run_planning,
)
from dita_package_processor.planning.loader import load_plan

LOGGER = logging.getLogger(__name__)


# ============================================================================
# Pipeline
# ============================================================================


class Pipeline:
    """
    Orchestrates the full DITA processing lifecycle.

    The pipeline owns:
        - filesystem paths
        - materialization
        - executor wiring

    CLI must remain thin and only call this boundary.
    """

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        *,
        package_path: Optional[Path],
        docx_stem: Optional[str],
        target_path: Optional[Path] = None,
        definition_map: Optional[str] = None,
        definition_navtitle: Optional[str] = None,
        apply: bool = False,
    ) -> None:
        self.package_path = package_path.resolve() if package_path else None
        self.docx_stem = docx_stem
        self.target_path = target_path.resolve() if target_path else None
        self.definition_map = definition_map
        self.definition_navtitle = definition_navtitle
        self.apply = apply

        LOGGER.debug(
            "Pipeline init package=%s target=%s apply=%s",
            self.package_path,
            self.target_path,
            self.apply,
        )

    # =========================================================================
    # FULL RUN (discover → plan → execute)
    # =========================================================================

    def run(self, *, apply: Optional[bool] = None):
        """
        Execute full pipeline.

        Returns ExecutionReport.
        """
        if apply is not None:
            self.apply = apply

        self._validate_package_required()

        LOGGER.info("DISCOVERY START")

        inventory: DiscoveryInventory = run_discovery(
            package_path=self.package_path
        )

        LOGGER.info("PLANNING START")

        # Planner now returns a dict plan, not a Plan model
        plan: Dict[str, Any] = run_planning(
            discovery=inventory,
            package_path=self.package_path,
            definition_map=self.definition_map,
            definition_navtitle=self.definition_navtitle,
            docx_stem=self.docx_stem,
        )

        return self._execute_plan_object(plan)

    # =========================================================================
    # EXECUTE ONLY (plan already exists)
    # =========================================================================

    def execute_plan(self, *, plan_path: Path, apply: Optional[bool] = None):
        """
        Execute an already-generated plan.

        Skips discovery + planning.

        Returns ExecutionReport.
        """
        if apply is not None:
            self.apply = apply

        if not self.target_path:
            raise ValueError("target_path required for execution")

        LOGGER.info("Loading plan for execution: %s", plan_path)

        plan: Dict[str, Any] = load_plan(plan_path)

        return self._execute_plan_object(plan)

    # =========================================================================
    # INTERNAL EXECUTION (shared by both paths)
    # =========================================================================

    def _execute_plan_object(self, plan: Dict[str, Any]):
        """
        Shared execution logic.

        Handles:
            - materialization
            - executor dispatch
            - finalize
        """
        if not self.target_path:
            raise ValueError("target_path must be provided")

        # --------------------------------------------------------------
        # MATERIALIZATION PREFLIGHT
        # --------------------------------------------------------------

        LOGGER.info("MATERIALIZATION PREFLIGHT")

        materializer = MaterializationOrchestrator(
            plan=plan,
            target_root=self.target_path,
        )

        materializer.preflight()

        # --------------------------------------------------------------
        # EXECUTION
        # --------------------------------------------------------------

        executor_name = "filesystem" if self.apply else "noop"

        LOGGER.info("EXECUTION mode=%s", executor_name)

        executor = get_executor(
            executor_name,
            apply=self.apply,
            source_root=self.package_path or self.target_path,
            sandbox_root=self.target_path,
        )

        execution_plan: Dict[str, Any] = {
            "actions": plan.get("actions", [])
        }

        report = executor.run(
            execution_id="pipeline-execution",
            plan=execution_plan,
        )

        materializer.finalize(execution_report=report)

        LOGGER.info("EXECUTION COMPLETE")

        return report

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_package_required(self) -> None:
        if not self.package_path:
            raise ValueError("package_path required")

        if not self.package_path.exists():
            raise FileNotFoundError(self.package_path)

        if not self.package_path.is_dir():
            raise ValueError(f"Not a directory: {self.package_path}")