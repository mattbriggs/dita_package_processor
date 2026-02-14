"""
Execution CLI subcommand.

Executes a validated plan and produces an ExecutionReport.

Supports:
    --plan PATH      required
    --output PATH    required (execution target root)
    --report PATH    optional
    --json           optional

Design rules
------------
CLI is dumb glue only.

It:
- loads plan
- mkdirs output
- calls executor
- writes report

It does NOT:
- use Pipeline
- perform discovery
- perform planning
- perform materialization
- invent layers
- mutate implicitly
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict

from dita_package_processor.planning.loader import load_plan
from dita_package_processor.orchestration import get_executor
from dita_package_processor.execution.report_writer import ExecutionReportWriter

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Helpers
# =============================================================================


def _normalize_plan_object(plan_obj: Any) -> Dict[str, Any]:
    """
    Normalize a hydrated Plan model into a plain JSON-compatible dictionary.

    Guarantees the returned structure contains only:
        dict / list / str / int / float / bool / None

    The execution layer must never receive:
        datetime, Path, model objects, or custom classes.

    Parameters
    ----------
    plan_obj : Any
        Hydrated Plan or dict-like structure.

    Returns
    -------
    Dict[str, Any]
        JSON-safe execution plan.
    """

    LOGGER.debug("Normalizing execution plan")

    def _normalize(value: Any) -> Any:
        # -----------------------------
        # primitives
        # -----------------------------
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        # -----------------------------
        # datetime/date → ISO string
        # -----------------------------
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        # -----------------------------
        # Path → string
        # -----------------------------
        if isinstance(value, Path):
            return str(value)

        # -----------------------------
        # dict
        # -----------------------------
        if isinstance(value, dict):
            return {k: _normalize(v) for k, v in value.items()}

        # -----------------------------
        # list/tuple
        # -----------------------------
        if isinstance(value, (list, tuple)):
            return [_normalize(v) for v in value]

        # -----------------------------
        # model serializers
        # -----------------------------
        for attr in ("to_dict", "dict", "model_dump"):
            method = getattr(value, attr, None)
            if callable(method):
                LOGGER.debug(
                    "Serializing %s via %s()",
                    type(value).__name__,
                    attr,
                )
                return _normalize(method())

        # -----------------------------
        # fallback: object → __dict__
        # -----------------------------
        if hasattr(value, "__dict__"):
            LOGGER.debug(
                "Serializing %s via __dict__",
                type(value).__name__,
            )
            return _normalize(vars(value))

        raise TypeError(
            f"Unsupported plan value type during normalization: "
            f"{type(value).__name__}"
        )

    normalized = _normalize(plan_obj)

    if not isinstance(normalized, dict):
        raise TypeError("Normalized plan must be a dictionary")

    LOGGER.debug("Plan normalization complete")

    return normalized


# =============================================================================
# CLI registration
# =============================================================================


def register_execute(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "execute",
        help="Execute a validated plan.",
    )

    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="Path to plan.json",
    )

    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Target directory for execution output",
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Write ExecutionReport JSON to this path",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit execution report to stdout as JSON",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Allow filesystem mutation (real execution).",
    )

    parser.add_argument(
        "--source-root",
        type=Path,
        required=True,
        help="Root directory containing source package files",
    )

    parser.set_defaults(func=run_execute)


# =============================================================================
# Execution
# =============================================================================


def run_execute(args: argparse.Namespace) -> int:
    """
    Execute a validated plan.

    Responsibilities
    ----------------
    CLI is glue only. It must:

    1. Validate inputs
    2. Load + normalize plan
    3. Create output directory
    4. Select executor
    5. Execute
    6. Emit report

    It must NOT:
    - mutate planning logic
    - perform discovery
    - guess paths

    Returns
    -------
    int
        0  success
        1  execution failure
        2  configuration / validation failure
    """

    plan_path: Path = args.plan.resolve()
    output_root: Path = args.output.resolve()
    source_root: Path = args.source_root.resolve()

    LOGGER.info(
        "run_execute(plan=%s, source_root=%s, output_root=%s, apply=%s)",
        plan_path,
        source_root,
        output_root,
        args.apply,
    )

    # ------------------------------------------------------------
    # Validate inputs
    # ------------------------------------------------------------

    if not plan_path.exists():
        print(f"ERROR: plan file not found: {plan_path}", file=sys.stderr)
        return 2

    if not source_root.exists():
        print(f"ERROR: source root not found: {source_root}", file=sys.stderr)
        return 2

    if not source_root.is_dir():
        print(f"ERROR: source root is not a directory: {source_root}", file=sys.stderr)
        return 2

    # ------------------------------------------------------------
    # Load + normalize plan
    # ------------------------------------------------------------

    try:
        plan_obj = load_plan(plan_path)
        plan = _normalize_plan_object(plan_obj)
        LOGGER.debug("Plan normalized successfully")
    except Exception as exc:  # noqa: BLE001
        print("ERROR: failed to load plan", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    # ------------------------------------------------------------
    # mkdir only (no logic)
    # ------------------------------------------------------------

    try:
        output_root.mkdir(parents=True, exist_ok=True)
    except Exception as exc:  # noqa: BLE001
        print("ERROR: failed to create output directory", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 2

    # ------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------

    executor_name = "filesystem" if args.apply else "noop"

    LOGGER.info("Using executor: %s", executor_name)

    executor = get_executor(
        executor_name,
        apply=args.apply,
        source_root=source_root,     # ← the important fix
        sandbox_root=output_root,
    )

    try:
        report = executor.run(
            execution_id="cli-execution",
            plan=plan,
        )
    except Exception as exc:  # noqa: BLE001
        print("ERROR: execution failed", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    # ------------------------------------------------------------
    # Write report file
    # ------------------------------------------------------------

    if args.report:
        try:
            ExecutionReportWriter().write(report=report, path=args.report)
        except Exception as exc:  # noqa: BLE001
            print("ERROR: failed to write report", file=sys.stderr)
            print(str(exc), file=sys.stderr)
            return 1

    # ------------------------------------------------------------
    # Output
    # ------------------------------------------------------------

    if args.json:
        print(json.dumps({"execution_report": report.to_dict()}, indent=2))
        return 0

    print(f"Execution ID: {report.execution_id}")
    print(f"Dry-run: {report.dry_run}")
    print(f"Total actions: {report.summary['total']}")
    print(f"Source root: {source_root}")
    print(f"Output root: {output_root}")

    if args.report:
        print(f"Report written to: {args.report.resolve()}")

    return 0