"""
Plugin management CLI subcommand.

Provides commands for inspecting and validating the plugin stack:

    dita_package_processor plugin list
        List all loaded plugins with their contributed patterns and handlers.

    dita_package_processor plugin info <name>
        Print detailed information about a specific plugin.

    dita_package_processor plugin validate <path>
        Validate a plugin from a local directory (imports directly from path).

These commands do not require a DITA package and do not mutate files.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)


# =============================================================================
# CLI registration
# =============================================================================


def register_plugin(subparsers: Any) -> None:
    """Register the ``plugin`` subcommand group."""
    plugin_parser = subparsers.add_parser(
        "plugin",
        help="Inspect and validate the plugin stack.",
    )

    plugin_subparsers = plugin_parser.add_subparsers(
        dest="plugin_command",
        required=True,
    )

    # plugin list
    list_parser = plugin_subparsers.add_parser(
        "list",
        help="List all loaded plugins.",
    )
    list_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output.",
    )
    list_parser.set_defaults(func=_run_list)

    # plugin info
    info_parser = plugin_subparsers.add_parser(
        "info",
        help="Show detailed information about a specific plugin.",
    )
    info_parser.add_argument("name", help="Plugin name (as reported by 'plugin list').")
    info_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON output.",
    )
    info_parser.set_defaults(func=_run_info)

    # plugin validate
    validate_parser = plugin_subparsers.add_parser(
        "validate",
        help="Validate a plugin from a local directory.",
    )
    validate_parser.add_argument(
        "path",
        help="Path to the plugin package directory (must contain pyproject.toml).",
    )
    validate_parser.set_defaults(func=_run_validate)

    plugin_parser.set_defaults(func=lambda args: (plugin_parser.print_help() or 0))


# =============================================================================
# plugin list
# =============================================================================


def _run_list(args: argparse.Namespace) -> int:
    from dita_package_processor.plugins.registry import get_plugin_registry

    registry = get_plugin_registry()
    plugins = registry.list_plugins()

    if getattr(args, "json", False):
        data = [_plugin_summary(p) for p in plugins]
        print(json.dumps(data, indent=2))
        return 0

    if not plugins:
        print("No plugins loaded.")
        return 0

    print(f"{'NAME':<40} {'VERSION':<12} {'PATTERNS':>8} {'HANDLERS':>9}")
    print("-" * 75)

    for plugin in plugins:
        try:
            pattern_count = len(plugin.patterns())
        except Exception:  # noqa: BLE001
            pattern_count = "?"

        try:
            handler_count = len(plugin.handlers())
        except Exception:  # noqa: BLE001
            handler_count = "?"

        print(
            f"{plugin.name:<40} {plugin.version:<12} "
            f"{str(pattern_count):>8} {str(handler_count):>9}"
        )

    print()
    print(f"Total: {len(plugins)} plugin(s)")
    return 0


# =============================================================================
# plugin info
# =============================================================================


def _run_info(args: argparse.Namespace) -> int:
    from dita_package_processor.plugins.registry import get_plugin_registry

    registry = get_plugin_registry()
    plugins = registry.list_plugins()

    match = [p for p in plugins if p.name == args.name]

    if not match:
        available = ", ".join(p.name for p in plugins)
        print(
            f"ERROR: Plugin {args.name!r} not found. "
            f"Available: {available}",
            file=sys.stderr,
        )
        return 2

    plugin = match[0]

    if getattr(args, "json", False):
        print(json.dumps(_plugin_detail(plugin), indent=2))
        return 0

    print(f"Plugin: {plugin.name}")
    print(f"Version: {plugin.version}")
    print(f"Class: {plugin.__class__.__module__}.{plugin.__class__.__name__}")
    print()

    patterns = plugin.patterns()
    print(f"Patterns ({len(patterns)}):")
    for pattern in patterns:
        print(f"  [{pattern.applies_to}] {pattern.id}")
        role = pattern.asserts.get("role", "?")
        confidence = pattern.asserts.get("confidence", "?")
        print(f"          role={role} confidence={confidence}")
    if not patterns:
        print("  (none)")

    print()

    handlers = plugin.handlers()
    print(f"Handlers ({len(handlers)}):")
    for handler_cls in handlers:
        action_type = getattr(handler_cls, "action_type", "?")
        print(f"  [{action_type}] {handler_cls.__name__}")
    if not handlers:
        print("  (none)")

    return 0


# =============================================================================
# plugin validate
# =============================================================================


def _run_validate(args: argparse.Namespace) -> int:
    """
    Validate a plugin from a local directory.

    Adds the directory to sys.path, reads pyproject.toml to find the
    entry point module, imports it, and runs validation.
    """
    plugin_dir = Path(args.path).resolve()

    if not plugin_dir.exists():
        print(f"ERROR: Path does not exist: {plugin_dir}", file=sys.stderr)
        return 2

    if not plugin_dir.is_dir():
        print(f"ERROR: Path is not a directory: {plugin_dir}", file=sys.stderr)
        return 2

    pyproject = plugin_dir / "pyproject.toml"
    if not pyproject.exists():
        print(
            f"ERROR: No pyproject.toml found in {plugin_dir}",
            file=sys.stderr,
        )
        return 2

    print(f"Validating plugin at: {plugin_dir}")

    # Read entry point from pyproject.toml
    try:
        import tomllib  # Python 3.11+
    except ImportError:
        try:
            import tomli as tomllib  # type: ignore[no-redef]
        except ImportError:
            print(
                "ERROR: tomllib/tomli required to parse pyproject.toml. "
                "Install tomli: pip install tomli",
                file=sys.stderr,
            )
            return 2

    with pyproject.open("rb") as fh:
        config = tomllib.load(fh)

    ep_group = (
        config.get("project", {})
        .get("entry-points", {})
        .get("dita_package_processor.plugins", {})
    )

    if not ep_group:
        print(
            "ERROR: No [project.entry-points.\"dita_package_processor.plugins\"] "
            "section found in pyproject.toml",
            file=sys.stderr,
        )
        return 2

    print(f"Found {len(ep_group)} entry point(s): {list(ep_group.keys())}")

    # Add directory to sys.path so local imports work
    sys.path.insert(0, str(plugin_dir))

    errors: list[str] = []
    successes: list[str] = []

    for ep_name, ep_value in ep_group.items():
        print(f"\nValidating entry point: {ep_name!r} = {ep_value!r}")

        try:
            plugin = _load_plugin_from_ep_value(ep_value)
        except Exception as exc:
            errors.append(f"[{ep_name}] Import failed: {exc}")
            print(f"  FAIL: Import error — {exc}")
            continue

        from dita_package_processor.plugins.validator import validate_plugin, PluginValidationError
        from dita_package_processor.plugins.protocol import DitaPlugin

        if not isinstance(plugin, DitaPlugin):
            errors.append(f"[{ep_name}] Not a DitaPlugin instance: {type(plugin)}")
            print(f"  FAIL: Not a DitaPlugin instance")
            continue

        try:
            validate_plugin(plugin)
        except PluginValidationError as exc:
            errors.append(f"[{ep_name}] Validation failed: {exc}")
            print(f"  FAIL: {exc}")
            continue

        pattern_count = len(plugin.patterns())
        handler_count = len(plugin.handlers())
        successes.append(ep_name)
        print(
            f"  OK: name={plugin.name!r} version={plugin.version!r} "
            f"patterns={pattern_count} handlers={handler_count}"
        )

    print()

    if errors:
        print(f"VALIDATION FAILED — {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        return 1

    print(f"Validation passed — {len(successes)} entry point(s) OK")
    return 0


def _load_plugin_from_ep_value(ep_value: str):
    """Load a plugin from a ``module:attr`` entry point string."""
    if ":" not in ep_value:
        raise ValueError(
            f"Entry point value {ep_value!r} must be in 'module:attr' format"
        )

    module_path, attr_name = ep_value.rsplit(":", 1)

    import importlib

    module = importlib.import_module(module_path)
    obj = getattr(module, attr_name)

    from dita_package_processor.plugins.protocol import DitaPlugin

    if isinstance(obj, type) and issubclass(obj, DitaPlugin):
        obj = obj()

    return obj


# =============================================================================
# Serialization helpers
# =============================================================================


def _plugin_summary(plugin: Any) -> dict:
    try:
        pattern_count = len(plugin.patterns())
    except Exception:  # noqa: BLE001
        pattern_count = -1

    try:
        handler_count = len(plugin.handlers())
    except Exception:  # noqa: BLE001
        handler_count = -1

    return {
        "name": plugin.name,
        "version": plugin.version,
        "pattern_count": pattern_count,
        "handler_count": handler_count,
    }


def _plugin_detail(plugin: Any) -> dict:
    summary = _plugin_summary(plugin)

    try:
        patterns = [
            {
                "id": p.id,
                "applies_to": p.applies_to,
                "role": p.asserts.get("role"),
                "confidence": p.asserts.get("confidence"),
            }
            for p in plugin.patterns()
        ]
    except Exception:  # noqa: BLE001
        patterns = []

    try:
        handlers = [
            {
                "action_type": getattr(h, "action_type", "?"),
                "class": h.__name__,
            }
            for h in plugin.handlers()
        ]
    except Exception:  # noqa: BLE001
        handlers = []

    return {**summary, "patterns": patterns, "handlers": handlers}
