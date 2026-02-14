"""
Pipeline orchestration CLI command.

This module implements the ``run`` subcommand, which represents the full
DITA Package Processor pipeline:

    discover → plan → materialization → execute

Design rules:

- Dry-run is the default and safest mode
- Filesystem mutation is only allowed when ``--apply`` is provided
- This command performs real orchestration
- No planning, discovery, or execution logic lives here
- The ExecutionReport is a first-class artifact
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from dita_package_processor.pipeline import Pipeline
from dita_package_processor.execution.report_writer import ExecutionReportWriter

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI registration
# ---------------------------------------------------------------------------


def register_run(subparsers: argparse._SubParsersAction) -> None:
    """
    Register the ``run`` subcommand.

    :param subparsers: Root argparse subparser registry.
    """
    parser = subparsers.add_parser(
        "run",
        help="Run the full pipeline: discover → plan → materialize → execute.",
    )

    parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="Root directory of the source DITA package.",
    )

    parser.add_argument(
        "--docx-stem",
        required=True,
        help="Stem name for generated main DITA map (e.g. OutputDoc).",
    )

    parser.add_argument(
        "--definition-map",
        help="Optional definition map used for glossary extraction.",
    )

    parser.add_argument(
        "--definition-navtitle",
        help="Navtitle used to identify glossary topicrefs.",
    )

    parser.add_argument(
        "--target",
        type=Path,
        help="Target output directory for materialized content.",
    )

    parser.add_argument(
        "--apply",
        action="store_true",
        help="Allow filesystem mutation (dangerous).",
    )

    parser.add_argument(
        "--report",
        type=Path,
        help="Write ExecutionReport JSON to this path.",
    )

    parser.set_defaults(func=run_pipeline)


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------


def run_pipeline(args: argparse.Namespace) -> int:
    """
    Execute the full discovery → planning → materialization → execution pipeline.

    This function is a strict orchestration boundary:
    - no discovery logic
    - no planning logic
    - no materialization logic
    - no execution logic

    It validates user intent, wires the pipeline, and normalizes failures.

    :param args: Parsed CLI arguments.
    :return: Process exit code.
    """
    package_path = args.package.resolve()
    target_path = args.target.resolve() if args.target else None

    # ------------------------------------------------------------
    # CLI-level intent validation
    #
    # Mutation without an explicit target is forbidden.
    # This is a human-safety rule, not a pipeline concern.
    # ------------------------------------------------------------
    if args.apply and not target_path:
        print(
            "ERROR: --target is required when --apply is specified",
            file=sys.stderr,
        )
        LOGGER.error(
            "Invalid CLI invocation: --apply requires --target",
        )
        return 2

    LOGGER.info("Starting pipeline run")
    LOGGER.debug(
        "Pipeline parameters: package=%s target=%s apply=%s report=%s",
        package_path,
        target_path,
        args.apply,
        args.report,
    )

    try:
        pipeline = Pipeline(
            package_path=package_path,
            target_path=target_path,
            docx_stem=args.docx_stem,
            definition_map=args.definition_map,
            definition_navtitle=args.definition_navtitle,
        )

        LOGGER.info(
            "Pipeline initialized (dry-run=%s)",
            not args.apply,
        )

        # Pipeline.run returns an ExecutionReport
        report = pipeline.run(apply=args.apply)

        # ------------------------------------------------------------
        # Report emission
        # ------------------------------------------------------------
        if args.report:
            report_path = args.report.resolve()
            LOGGER.info("Writing ExecutionReport to %s", report_path)

            writer = ExecutionReportWriter()
            writer.write(report=report, path=report_path)

        LOGGER.info("Pipeline completed successfully")
        return 0

    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        LOGGER.error("Pipeline failed: %s", exc)
        return 2

    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        LOGGER.error("Pipeline failed: %s", exc)
        return 2

    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        LOGGER.exception("Pipeline crashed")
        return 1