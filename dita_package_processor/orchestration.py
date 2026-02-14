"""
Orchestration layer.

This module provides thin glue helpers that connect the three major phases:

    discovery  → planning → execution

Design principles
----------------
This layer is intentionally boring.

It:
- wires concrete implementations together
- performs zero business logic
- performs zero mutation
- does not guess or adapt to historical signatures

It does NOT:
- perform discovery itself
- perform planning itself
- inspect XML
- mutate filesystems
- contain dynamic reflection or compatibility hacks

If something changes, update this file explicitly.
Do not make it "smart".
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from dita_package_processor.discovery.scanner import DiscoveryScanner
from dita_package_processor.discovery.models import DiscoveryInventory

from dita_package_processor.planning.planner import Planner
from dita_package_processor.planning.models import Plan

from dita_package_processor.execution.executors.filesystem import FilesystemExecutor
from dita_package_processor.execution.dry_run_executor import DryRunExecutor
from dita_package_processor.execution.safety.policies import (
    MutationPolicy,
    OverwritePolicy,
)

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Discovery
# =============================================================================


def run_discovery(*, package_path: Path) -> DiscoveryInventory:
    """
    Execute discovery phase.

    Parameters
    ----------
    package_path : Path
        Root directory containing the source package.

    Returns
    -------
    DiscoveryInventory
        Fully populated discovery inventory.

    Notes
    -----
    This function is pure orchestration glue. It simply invokes the scanner.
    """
    LOGGER.info("Running discovery: package_path=%s", package_path)

    scanner = DiscoveryScanner(package_path=package_path)
    inventory = scanner.scan()

    LOGGER.info(
        "Discovery complete: artifacts=%d",
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
) -> Plan:
    """
    Execute planning phase.

    Parameters
    ----------
    discovery : DiscoveryInventory
        Inventory produced by discovery.
    package_path : Path
        Root source directory.
    definition_map : str | None
        Optional glossary definition map.
    definition_navtitle : str | None
        Optional glossary navigation title.
    docx_stem : str
        Base name for the output map.

    Returns
    -------
    Plan
        Deterministic execution plan.

    Raises
    ------
    ValueError
        If planning fails or required artifacts are missing.
    """
    LOGGER.info(
        "Running planning: package_path=%s docx_stem=%s",
        package_path,
        docx_stem,
    )

    planner = Planner(
        discovery=discovery,
        package_path=package_path,
        definition_map=definition_map,
        definition_navtitle=definition_navtitle,
        docx_stem=docx_stem,
    )

    plan = planner.build()

    LOGGER.info("Planning complete: actions=%d", len(plan.actions))

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
) -> Any:
    """
    Resolve execution backend.

    This function is intentionally dumb glue. It wires the requested
    executor with the provided paths and returns it.

    It must:
    - perform zero logic
    - perform zero mutation
    - not construct policy objects
    - not guess signatures

    Parameters
    ----------
    name : str
        Executor name. Supported values:
            - "filesystem"
            - "noop"
    apply : bool
        Whether filesystem mutation is allowed.
    source_root : Path
        Root directory containing source artifacts.
    sandbox_root : Path
        Output directory for generated artifacts.

    Returns
    -------
    Any
        Concrete executor instance.

    Raises
    ------
    ValueError
        If executor name is unknown.
    """

    LOGGER.info(
        "Selecting executor name=%s apply=%s source_root=%s sandbox_root=%s",
        name,
        apply,
        source_root,
        sandbox_root,
    )

    # -------------------------------------------------------------
    # Dry-run executor (no mutation)
    # -------------------------------------------------------------

    if name == "noop":
        LOGGER.debug("Using DryRunExecutor")
        return DryRunExecutor()

    # -------------------------------------------------------------
    # Filesystem executor (real mutation)
    # -------------------------------------------------------------

    if name == "filesystem":
        LOGGER.debug("Using FilesystemExecutor")
        return FilesystemExecutor(
            source_root=source_root,
            sandbox_root=sandbox_root,
            apply=apply,
        )

    # -------------------------------------------------------------
    # Unknown executor
    # -------------------------------------------------------------

    raise ValueError(f"Unknown executor: {name}")