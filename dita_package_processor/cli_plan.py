"""
cli_plan.py
===========

Planning CLI interface.

Thin controller only.

Flow
----
read → validate contract → plan → validate → write

Responsibilities
----------------
- Read planning_input.json
- Hydrate PlanningInput contract
- Invoke Planner
- Validate produced plan
- Write plan.json

Non-Responsibilities
-------------------
- No discovery parsing
- No normalization
- No schema mutation
- No inference
- No business logic

This file is strictly a transport/controller layer.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

from dita_package_processor.planning.contracts.loader import (  # ← FIXED IMPORT
    load_planning_input,
)
from dita_package_processor.planning.planner import Planner

LOGGER = logging.getLogger(__name__)

__all__ = ["register_plan", "run_plan"]


# =============================================================================
# CLI registration
# =============================================================================


def register_plan(subparsers: Any) -> None:
    """
    Register the ``plan`` subcommand.

    Parameters
    ----------
    subparsers : Any
        argparse subparser collection.
    """
    parser = subparsers.add_parser(
        "plan",
        help="Generate deterministic execution plan from planning_input.json",
    )

    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to planning_input.json contract",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Destination for generated plan.json",
    )

    parser.add_argument(
        "--schema",
        type=Path,
        help="Optional custom plan.schema.json",
    )

    parser.set_defaults(func=run_plan)


# =============================================================================
# Execution
# =============================================================================


def run_plan(args: argparse.Namespace) -> int:
    """
    Execute planning workflow.

    Strict transport pipeline:

        file → PlanningInput → planner → file

    Parameters
    ----------
    args : argparse.Namespace
        Parsed CLI arguments.

    Returns
    -------
    int
        0 success
        1 planning failure
        2 setup/contract failure
    """
    input_path: Path = args.input.resolve()
    output_path: Path = args.output.resolve()

    LOGGER.info("Plan command invoked input=%s output=%s", input_path, output_path)

    # ------------------------------------------------------------------
    # Ensure input exists
    # ------------------------------------------------------------------

    if not input_path.exists() or not input_path.is_file():
        LOGGER.error("planning_input.json not found: %s", input_path)
        print(
            f"ERROR: planning_input.json not found: {input_path}",
            file=sys.stderr,
        )
        return 2

    # ------------------------------------------------------------------
    # Load + hydrate PlanningInput contract
    # ------------------------------------------------------------------

    try:
        LOGGER.debug("Hydrating PlanningInput contract")
        planning_input = load_planning_input(input_path)
    except Exception:
        LOGGER.exception("Invalid planning_input contract")
        print(
            "ERROR: invalid planning_input.json (contract violation)",
            file=sys.stderr,
        )
        return 2

    # ------------------------------------------------------------------
    # Planner invocation
    # ------------------------------------------------------------------

    try:
        LOGGER.debug("Initializing Planner")
        planner = Planner(schema_path=args.schema) if args.schema else Planner()

        LOGGER.info("Generating plan")
        plan = planner.plan(planning_input)  # pass object, not dict

        LOGGER.info("Validating generated plan")
        planner.validate(plan)

    except Exception:
        LOGGER.exception("Plan generation failed")
        print("Plan generation failed.", file=sys.stderr)
        return 1

    # ------------------------------------------------------------------
    # Write output
    # ------------------------------------------------------------------

    try:
        LOGGER.debug("Writing plan.json to %s", output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        output_path.write_text(
            json.dumps(plan, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    except Exception:
        LOGGER.exception("Failed writing plan.json")
        print("ERROR: failed writing plan.json", file=sys.stderr)
        return 2

    LOGGER.info("Plan generation successful")
    print(f"Plan written to: {output_path}")

    return 0