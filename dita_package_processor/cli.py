"""
Unified command-line interface for dita_package_processor.

This module defines the root CLI entry point, global options, and
subcommand dispatch. Subcommands are registered in dedicated modules.

Global concerns handled here
---------------------------
- argument normalization
- logging configuration
- machine-readable output flags
- implicit pipeline execution
- docs and shell completion helpers

Design principles
----------------
- argparse owns parsing
- no manual flag handling
- subcommands contain all behavior
- this file is routing + orchestration only
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Any, Callable, Optional

from dita_package_processor import __version__
from dita_package_processor.cli_discover import register_discover
from dita_package_processor.cli_execute import register_execute
from dita_package_processor.cli_normalize import register_normalize
from dita_package_processor.cli_plan import register_plan
from dita_package_processor.cli_run import register_run

LOGGER = logging.getLogger(__name__)


# =============================================================================
# Known subcommands
# =============================================================================

KNOWN_COMMANDS = {
    "discover",
    "normalize",
    "plan",
    "execute",
    "run",
    "docs",
    "completion",
}


# =============================================================================
# Logging
# =============================================================================


def _configure_logging(level: str) -> None:
    """
    Configure root logging for the CLI process.

    Parameters
    ----------
    level : str
        Logging level name (DEBUG, INFO, WARNING, ERROR).
    """
    numeric = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    LOGGER.debug("Logging configured level=%s", level)


# =============================================================================
# Global arguments
# =============================================================================


def _add_global_args(parser: argparse.ArgumentParser) -> None:
    """
    Add global options shared by all commands.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        Root parser.
    """
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON output where applicable.",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress human-readable output (errors still print).",
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO).",
    )

    # IMPORTANT:
    # Let argparse handle this automatically.
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )


# =============================================================================
# Parser construction
# =============================================================================


def build_parser() -> argparse.ArgumentParser:
    """
    Build and return the root argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Configured CLI parser.
    """
    parser = argparse.ArgumentParser(
        prog="dita_package_processor",
        description="Deterministic discovery, planning, and execution for DITA packages.",
    )

    _add_global_args(parser)

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # Core commands
    register_discover(subparsers)
    register_normalize(subparsers)
    register_plan(subparsers)
    register_execute(subparsers)
    register_run(subparsers)

    # Auxiliary commands
    _register_docs(subparsers)
    _register_completion(subparsers)

    return parser


# =============================================================================
# Optional integrations
# =============================================================================


def _maybe_enable_argcomplete(parser: argparse.ArgumentParser) -> None:
    """
    Enable argcomplete if installed.

    Parameters
    ----------
    parser : argparse.ArgumentParser
    """
    try:
        import argcomplete  # type: ignore
    except Exception:  # noqa: BLE001
        LOGGER.debug("argcomplete not available")
        return

    argcomplete.autocomplete(parser)
    LOGGER.debug("argcomplete enabled")


# =============================================================================
# Docs + completion commands
# =============================================================================


def _register_docs(subparsers: Any) -> None:
    parser = subparsers.add_parser("docs", help="Generate CLI documentation.")
    parser.add_argument("--output", type=str)
    parser.set_defaults(func=_run_docs)


def _register_completion(subparsers: Any) -> None:
    parser = subparsers.add_parser("completion", help="Emit shell completion.")
    parser.add_argument(
        "--shell",
        choices=["bash", "zsh", "fish"],
        default="bash",
    )
    parser.set_defaults(func=_run_completion)


def _run_docs(args: argparse.Namespace) -> int:
    parser = build_parser()
    text = parser.format_help()

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(args.output)
        return 0

    print(text)
    return 0


def _run_completion(args: argparse.Namespace) -> int:
    try:
        from argcomplete.shellintegration import shellcode  # type: ignore
    except Exception:
        print(
            "ERROR: argcomplete required for shell completion.",
            file=sys.stderr,
        )
        return 2

    print(shellcode(["dita_package_processor"], shell=args.shell))
    return 0


# =============================================================================
# Entry point
# =============================================================================


def main(argv: Optional[list[str]] = None) -> int:
    """
    CLI entry point.

    Behavior
    --------
    - --help/--version handled by argparse directly
    - implicit 'run' only when no command is supplied
    """

    argv_list = list(argv or sys.argv[1:])

    parser = build_parser()
    _maybe_enable_argcomplete(parser)

    # ------------------------------------------------------------
    # First parse just to allow argparse to handle:
    #   --help
    #   --version
    # without us injecting anything.
    # ------------------------------------------------------------
    if any(flag in argv_list for flag in ("--help", "-h", "--version")):
        try:
            parser.parse_args(argv_list)
        except SystemExit as exc:
            return int(exc.code)

    # ------------------------------------------------------------
    # Implicit run logic
    #
    # Only inject run if:
    #   - no args
    #   - or first token is NOT command
    #   - and not a flag
    # ------------------------------------------------------------
    if not argv_list or argv_list[0] not in KNOWN_COMMANDS:
        LOGGER.debug("Implicit run mode triggered")
        argv_list = ["run", *argv_list]

    try:
        args = parser.parse_args(argv_list)
    except SystemExit as exc:
        return int(exc.code)

    _configure_logging(args.log_level)

    command = getattr(args, "command", None)
    LOGGER.info("CLI invoked with command=%s", command)

    if not command:
        parser.print_help()
        return 2

    func: Callable[[argparse.Namespace], int] = args.func

    try:
        return int(func(args))

    except FileNotFoundError as exc:
        LOGGER.error("File error: %s", exc)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    except Exception as exc:  # noqa: BLE001
        LOGGER.error("Unhandled failure", exc_info=True)
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1