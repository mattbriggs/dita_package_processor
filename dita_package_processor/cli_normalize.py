"""
cli_normalize.py
================

Discovery → PlanningInput contract normalization CLI.

This command converts a raw ``discovery.json`` file into a validated
``planning_input.json`` contract.

Strict transport layer only.

Flow
----
file → normalize_discovery_report() → write

Responsibilities
----------------
- Read discovery.json
- Validate + normalize into PlanningInput
- Write planning_input.json

Non-Responsibilities
-------------------
- No planning
- No execution
- No inference
- No mutation of discovery content
- No schema edits

All semantic logic belongs to:
    planning.contracts.discovery_to_planning

This module only performs IO and delegation.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.planning.contracts.discovery_to_planning import (
    normalize_discovery_report,
)

LOGGER = logging.getLogger(__name__)

__all__ = ["register_normalize", "run_normalize"]


# =============================================================================
# CLI registration
# =============================================================================


def register_normalize(subparsers: Any) -> None:
    """
    Register the ``normalize`` subcommand.

    Parameters
    ----------
    subparsers : Any
        argparse subparser collection.

    Notes
    -----
    This command only performs contract normalization.
    It does not plan or execute.
    """
    parser = subparsers.add_parser(
        "normalize",
        help="Convert discovery.json → planning_input.json contract",
        description=(
            "Validate and normalize a discovery report into a strict "
            "PlanningInput contract. No filesystem mutation occurs beyond "
            "writing the output file."
        ),
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to discovery.json",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination planning_input.json path",
    )

    parser.set_defaults(func=run_normalize)


# =============================================================================
# Execution
# =============================================================================


def run_normalize(args: argparse.Namespace) -> int:
    """
    Execute normalization workflow.

    Strict pipeline:

        discovery.json → PlanningInput → planning_input.json

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        Exit code:

        - 0 → success
        - 2 → setup or contract failure

    Behavior
    --------
    - Fails fast on malformed JSON
    - Fails fast on contract violations
    - Never mutates discovery input
    """
    input_path: Path = args.input.resolve()
    output_path: Path = args.output.resolve()

    LOGGER.info(
        "Normalize command invoked input=%s output=%s",
        input_path,
        output_path,
    )

    # ------------------------------------------------------------------
    # Validate input path
    # ------------------------------------------------------------------

    if not input_path.exists() or not input_path.is_file():
        LOGGER.error("discovery.json not found: %s", input_path)
        print(f"ERROR: discovery.json not found: {input_path}", file=sys.stderr)
        return 2

    # ------------------------------------------------------------------
    # Read discovery JSON
    # ------------------------------------------------------------------

    try:
        LOGGER.debug("Reading discovery.json")
        raw_text: str = input_path.read_text(encoding="utf-8")
        discovery: Dict[str, Any] = json.loads(raw_text)
    except Exception:
        LOGGER.exception("Invalid JSON in discovery.json")
        print("ERROR: invalid discovery.json", file=sys.stderr)
        return 2

    # ------------------------------------------------------------------
    # Normalize contract
    # ------------------------------------------------------------------

    try:
        LOGGER.info("Normalizing discovery → PlanningInput contract")
        planning_input = normalize_discovery_report(discovery)
    except Exception:
        LOGGER.exception("Discovery normalization failed")
        print(
            "ERROR: discovery → planning contract normalization failed",
            file=sys.stderr,
        )
        return 2

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------

    try:
        LOGGER.debug("Writing planning_input.json to %s", output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(
            json.dumps(planning_input.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )
    except Exception:
        LOGGER.exception("Failed writing planning_input.json")
        print("ERROR: failed writing planning_input.json", file=sys.stderr)
        return 2

    LOGGER.info("Normalization successful")
    print(f"PlanningInput written to: {output_path}")

    return 0