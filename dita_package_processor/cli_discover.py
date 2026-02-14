"""
Discovery CLI subcommand.

Runs discovery-only analysis over a DITA package directory and emits:

- A human-readable summary (default)
- Optional JSON discovery report (via --output or --json)
- Optional invariant validation feedback

This command:

- Does NOT transform content
- Does NOT mutate files
- Does NOT infer intent

It is a strict observational interface over the discovery subsystem.
All results are deterministic, auditable, and schema-aligned.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List

from dita_package_processor.discovery.report import DiscoveryReport
from dita_package_processor.discovery.scanner import DiscoveryScanner
from dita_package_processor.knowledge.invariants import validate_single_main_map

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CLI registration
# ---------------------------------------------------------------------------


def register_discover(subparsers: Any) -> None:
    """
    Register the ``discover`` subcommand.

    :param subparsers: Root argparse subparser registry.
    """
    parser = subparsers.add_parser(
        "discover",
        help="Run discovery on a DITA package directory.",
    )

    parser.add_argument(
        "--package",
        type=Path,
        required=True,
        help="Path to the DITA package root directory.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help="Write discovery report JSON to this path.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON discovery report to stdout.",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress stdout output.",
    )

    parser.add_argument(
        "--fail-on-invariants",
        action="store_true",
        help="Exit non-zero if discovery invariants fail.",
    )

    parser.set_defaults(func=run_discover)


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------


def _summary_text(summary: Dict[str, int]) -> str:
    """
    Render a simple human-readable discovery summary.

    Summary is strictly derived from the discovery contract:

        {
            "map": <int>,
            "topic": <int>,
            "media": <int>
        }

    No totals. No relationship counts. No inference.

    :param summary: Summary mapping returned by DiscoveryReport.summary().
    :return: Text summary.
    """
    lines: List[str] = [
        "Discovery summary",
        "-" * 72,
    ]

    for key in ("map", "topic", "media"):
        value = summary.get(key, 0)
        label = key.capitalize()
        lines.append(f"{label:<10}: {value}")

    return "\n".join(lines)


def _format_invariant_violations(violations: List[Any]) -> List[str]:
    """
    Normalize invariant violations to human-readable strings.

    :param violations: Raw invariant violation objects.
    :return: List of formatted messages.
    """
    messages: List[str] = []

    for violation in violations:
        path = getattr(violation, "path", None)
        if path:
            messages.append(f"{violation.message} ({path})")
        else:
            messages.append(violation.message)

    return messages


# ---------------------------------------------------------------------------
# Command implementation
# ---------------------------------------------------------------------------


def run_discover(args: argparse.Namespace) -> int:
    """
    Execute discovery scanning and emit outputs.

    :param args: Parsed CLI arguments.
    :return: Exit code.
    """
    package_dir = args.package.resolve()

    if not package_dir.exists():
        print(
            f"ERROR: package directory does not exist: {package_dir}",
            file=sys.stderr,
        )
        return 2

    if not package_dir.is_dir():
        print(
            f"ERROR: package path is not a directory: {package_dir}",
            file=sys.stderr,
        )
        return 2

    LOGGER.info("Running discovery on package: %s", package_dir)

    # ------------------------------------------------------------------
    # Discovery scan
    # ------------------------------------------------------------------

    scanner = DiscoveryScanner(package_dir)
    inventory = scanner.scan()
    report = DiscoveryReport(inventory)

    discovery_data = report.to_dict()

    LOGGER.info(
        "Discovery complete: %d artifacts, %d relationships",
        len(discovery_data["artifacts"]),
        len(discovery_data["relationships"]),
    )

    # ------------------------------------------------------------------
    # Invariant validation
    # ------------------------------------------------------------------

    violations = validate_single_main_map(inventory)
    violation_messages = _format_invariant_violations(violations)

    # Merge invariants into output payload
    result: Dict[str, Any] = dict(discovery_data)
    result["invariants"] = {
        "violations": violation_messages,
        "passed": not violation_messages,
    }

    # ------------------------------------------------------------------
    # Optional file output
    # ------------------------------------------------------------------

    if args.output:
        output_path = args.output.resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(result, indent=2),
            encoding="utf-8",
        )
        LOGGER.info("Discovery report written to %s", output_path)

    # ------------------------------------------------------------------
    # Stdout output
    # ------------------------------------------------------------------

    if not args.quiet:
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(_summary_text(report.summary()))

            if violation_messages:
                print("\nInvariant violations:")
                for msg in violation_messages:
                    print(f"- {msg}")

            if args.output:
                print(f"\nDiscovery report written to: {args.output.resolve()}")

    # ------------------------------------------------------------------
    # Exit behavior on invariant failure
    # ------------------------------------------------------------------

    if violation_messages and args.fail_on_invariants:
        LOGGER.warning("Discovery invariants failed")
        return 1

    return 0