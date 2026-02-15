"""
Orchestration layer.

Thin glue between:

    discovery → planning → execution

Design principles
-----------------
This layer is intentionally boring.

It:
- wires concrete implementations together
- performs zero business logic
- performs zero semantic inference
- does not reinterpret discovery internals
- delegates invariant enforcement to lower layers

If something changes, update this file explicitly.
Do not make it smart.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol, List

from dita_package_processor.discovery.models import DiscoveryInventory
from dita_package_processor.discovery.scanner import DiscoveryScanner

from dita_package_processor.planning.contracts.planning_input import (
    PlanningInput,
    PlanningArtifact,
    PlanningRelationship,
)
from dita_package_processor.planning.planner import Planner

from dita_package_processor.execution.dry_run_executor import (
    DryRunExecutor,
)
from dita_package_processor.execution.executors.filesystem import (
    FilesystemExecutor,
)

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Executor Protocol
# =============================================================================


class ExecutorProtocol(Protocol):
    """
    Minimal execution contract exposed to orchestration.
    """

    def run(self, *, execution_id: str, plan: dict) -> object:  # pragma: no cover
        ...

    def execute(self, action: dict) -> object:  # pragma: no cover
        ...


# =============================================================================
# Discovery
# =============================================================================


def run_discovery(*, package_path: Path) -> DiscoveryInventory:
    """
    Execute discovery phase.

    Parameters
    ----------
    package_path : Path
        Root directory containing DITA package.

    Returns
    -------
    DiscoveryInventory
    """
    package_path = Path(package_path).resolve()

    LOGGER.info("Running discovery package_path=%s", package_path)

    scanner = DiscoveryScanner(package_dir=package_path)
    inventory = scanner.scan()

    LOGGER.info(
        "Discovery complete artifacts=%d",
        len(inventory.artifacts),
    )

    return inventory


# =============================================================================
# Planning
# =============================================================================


def run_planning(
    *,
    discovery: DiscoveryInventory,
    package_path: Path,
    definition_map: str | None,
    definition_navtitle: str | None,
    docx_stem: str,
) -> dict:
    """
    Execute planning phase.

    Explicit conversion:

        DiscoveryInventory → PlanningInput → Plan

    This function performs no semantic reasoning.
    All invariants must already be enforced by discovery.
    """

    LOGGER.info(
        "Running planning package_path=%s docx_stem=%s",
        package_path,
        docx_stem,
    )

    # ------------------------------------------------------------------
    # MAIN MAP RESOLUTION (delegated to inventory)
    # ------------------------------------------------------------------

    main_map_path = str(discovery.resolve_main_map())

    LOGGER.debug("Resolved MAIN map path=%s", main_map_path)

    # ------------------------------------------------------------------
    # ARTIFACT CONVERSION
    # ------------------------------------------------------------------

    planning_artifacts: List[PlanningArtifact] = []

    for artifact in discovery.artifacts:
        planning_artifacts.append(
            PlanningArtifact(
                path=str(artifact.path),
                artifact_type=artifact.artifact_type,
                classification=artifact.classification_label(),
                metadata=dict(artifact.metadata),
            )
        )

    # ------------------------------------------------------------------
    # RELATIONSHIP CONVERSION
    # ------------------------------------------------------------------

    planning_relationships: List[PlanningRelationship] = []

    graph = getattr(discovery, "graph", None)

    if graph is not None:
        for edge in getattr(graph, "edges", []):
            planning_relationships.append(
                PlanningRelationship(
                    source=str(edge.source),
                    target=str(edge.target),
                    rel_type=str(
                        getattr(edge, "rel_type", None)
                        or getattr(edge, "type", None)
                    ),
                    pattern_id=str(edge.pattern_id),
                )
            )

    # ------------------------------------------------------------------
    # BUILD CONTRACT OBJECT
    # ------------------------------------------------------------------

    planning_input = PlanningInput(
        contract_version="1.0",
        main_map=main_map_path,
        artifacts=planning_artifacts,
        relationships=planning_relationships,
    )

    planner = Planner()

    plan = planner.plan(planning_input)

    LOGGER.info(
        "Planning complete actions=%d",
        len(plan.get("actions", [])),
    )

    return plan


# =============================================================================
# Executor resolution
# =============================================================================


def get_executor(
    name: str,
    *,
    apply: bool,
    source_root: Path,
    sandbox_root: Path,
) -> ExecutorProtocol:
    """
    Resolve execution backend.

    Parameters
    ----------
    name : str
        Executor name.
        Supported:
            - "filesystem"
            - "noop"
    apply : bool
        Whether filesystem mutation is allowed.
    source_root : Path
        Source artifact root.
    sandbox_root : Path
        Output root.

    Returns
    -------
    ExecutorProtocol
    """
    source_root = Path(source_root).resolve()
    sandbox_root = Path(sandbox_root).resolve()

    LOGGER.info(
        "Selecting executor name=%s apply=%s source_root=%s sandbox_root=%s",
        name,
        apply,
        source_root,
        sandbox_root,
    )

    if name == "noop":
        LOGGER.debug("Using DryRunExecutor")
        return DryRunExecutor()

    if name == "filesystem":
        LOGGER.debug("Using FilesystemExecutor")
        return FilesystemExecutor(
            source_root=source_root,
            sandbox_root=sandbox_root,
            apply=apply,
        )

    LOGGER.error("Unknown executor requested name=%s", name)
    raise ValueError(f"Unknown executor: {name}")