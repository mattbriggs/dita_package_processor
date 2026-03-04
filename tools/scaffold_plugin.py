#!/usr/bin/env python3
"""
Plugin scaffold generator for the DITA Package Processor.

Creates a complete, installable plugin package with annotated skeletons
for patterns, handlers, and action emission.

Usage::

    python tools/scaffold_plugin.py

The generator prompts for:
  - Plugin name      (e.g. ``acme_dita_bookmap``)
  - Author name
  - Version string

And produces a directory ready for ``pip install -e .`` and immediate
use with ``dita_package_processor plugin validate <dir>``.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path


# =============================================================================
# Templates
# =============================================================================

_PYPROJECT_TEMPLATE = """\
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "{plugin_name_hyphen}"
version = "{version}"
description = "DITA Package Processor plugin: {plugin_name}"
requires-python = ">=3.10"
dependencies = [
    "dita-package-processor>=0.1.0",
]

authors = [
    {{ name = "{author}" }},
]

# -----------------------------------------------------------------------
# Entry point declaration — this is what registers the plugin.
# The key (left of =) is an arbitrary label; the value is module:attr.
# -----------------------------------------------------------------------
[project.entry-points."dita_package_processor.plugins"]
{plugin_name} = "{plugin_name}:plugin"

[tool.setuptools.packages.find]
where = ["."]
include = ["{plugin_name}*"]
"""

_INIT_TEMPLATE = """\
"""
from {plugin_name}.plugin import {class_name}

# Module-level singleton — this is what the entry point resolves to.
plugin = {class_name}()

__all__ = ["plugin", "{class_name}"]
"""

_PLUGIN_TEMPLATE = """\
"""
{plugin_name} plugin implementation.

Replace the skeletons below with your real logic.
The docstrings explain the contract at each extension point.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Type

from dita_package_processor.plugins.protocol import DitaPlugin

LOGGER = logging.getLogger(__name__)


class {class_name}(DitaPlugin):
    \"\"\"
    {plugin_name} plugin.

    Contribute patterns, action emitters, and handlers to the
    DITA Package Processor pipeline.
    \"\"\"

    # =========================================================================
    # Identity (required)
    # =========================================================================

    @property
    def name(self) -> str:
        return "{plugin_name}"

    @property
    def version(self) -> str:
        return "{version}"

    # =========================================================================
    # Discovery patterns (optional)
    # =========================================================================

    def patterns(self):
        \"\"\"
        Return Pattern objects for discovery.

        Patterns are evaluated against every artifact in the DITA package.
        A matching pattern emits Evidence that you can inspect in emit_actions().

        Quick start — load from the bundled patterns.yaml:

            from dita_package_processor.knowledge.known_patterns import _load_pattern
            import yaml, pathlib

            raw = yaml.safe_load(
                (pathlib.Path(__file__).parent / "patterns.yaml").read_text()
            )
            return [_load_pattern(entry) for entry in raw["patterns"]]

        Or build Pattern objects programmatically:

            from dita_package_processor.discovery.patterns import Pattern
            return [
                Pattern(
                    id="{plugin_name}.my_map",
                    applies_to="map",
                    signals={{"filename": {{"equals": "MyMap.ditamap"}}}},
                    asserts={{"role": "my_map", "confidence": 1.0}},
                    rationale=["Matches MyMap.ditamap by filename"],
                )
            ]
        \"\"\"
        return []

    # =========================================================================
    # Planning: action emission (optional)
    # =========================================================================

    def emit_actions(
        self,
        artifact,
        evidence: List[Dict[str, Any]],
        context,
    ) -> List[Dict[str, Any]]:
        \"\"\"
        Emit action dicts for an artifact.

        Called once per artifact per plugin. Return [] to skip.

        Parameters
        ----------
        artifact
            PlanningArtifact with path, artifact_type, classification, metadata.
        evidence
            List of Evidence dicts for this artifact:
                [{{"pattern_id": ..., "asserted_role": ..., "confidence": ..., "rationale": [...]}}]
        context
            Full PlanningInput (main_map, artifacts, relationships).

        Returns
        -------
        List of action template dicts.  Each dict must include:
            type        : str   — one of the registered action types
            target      : str   — package-relative target path
            parameters  : dict  — action-specific parameters
            reason      : str   — human-readable justification
            derived_from_evidence : List[str] — pattern_ids from evidence
        Do NOT include an "id" key — the planner assigns IDs.

        Example (route artifacts with role "my_map" to a custom path)::

            roles = {{ev.get("asserted_role") for ev in evidence}}
            if "my_map" not in roles:
                return []

            from pathlib import Path
            src = artifact.path
            dest = f"target/my_maps/{{Path(src).name}}"
            return [{{
                "type": "copy_map",
                "target": dest,
                "parameters": {{"source_path": src, "target_path": dest}},
                "reason": "Custom routing for my_map role",
                "derived_from_evidence": [
                    ev["pattern_id"] for ev in evidence if ev.get("pattern_id")
                ],
            }}]
        \"\"\"
        return []

    # =========================================================================
    # Execution handlers (optional)
    # =========================================================================

    def handlers(self) -> list:
        \"\"\"
        Return handler classes for new action types.

        Each class must:
        - inherit ExecutionHandler
        - define action_type = "my_action_type"
        - implement execute(self, action, ...)

        Example::

            from {plugin_name}.handlers.my_handler import MyHandler
            return [MyHandler]
        \"\"\"
        return []
"""

_PATTERNS_YAML_TEMPLATE = """\
# Discovery patterns for {plugin_name}.
#
# Each pattern declares what to look for (signals) and what role to assert
# when the signals match (asserts.role).
#
# Pattern IDs must be globally unique across all loaded plugins.
# Use a namespace prefix: "{plugin_name}.<pattern_name>"
#
# See the built-in known_patterns.yaml for more signal examples.

version: 1
patterns:
  - id: "{plugin_name}.example_map"
    applies_to: "map"
    signals:
      filename:
        equals: "ExampleMap.ditamap"
    asserts:
      role: "example_map"
      confidence: 1.0
    rationale:
      - "Matches ExampleMap.ditamap by filename"
      - "Replace this with your real pattern"
"""

_HANDLER_TEMPLATE = """\
"""
Example handler for {plugin_name}.

Replace this skeleton with your real implementation.
\"\"\"

from __future__ import annotations

import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class ExampleHandler:
    \"\"\"
    Example execution handler.

    Change action_type to match the action type this handler processes.
    If you are reusing a built-in type (copy_map, copy_topic, copy_media,
    etc.) this handler will REPLACE the built-in handler for that type.
    Only do this if you want custom execution behaviour.
    \"\"\"

    action_type = "{plugin_name}.example_action"

    def execute(self, action: dict, **kwargs):
        \"\"\"
        Execute the action.

        Parameters
        ----------
        action
            The action dict from the plan.
        **kwargs
            May include: source_root, sandbox, policy
            (only if the executor injects them).

        Returns
        -------
        ExecutionActionResult
        \"\"\"
        from dita_package_processor.execution.models import ExecutionActionResult

        LOGGER.info(
            "ExampleHandler executing action id=%s",
            action.get("id"),
        )

        # TODO: replace with real logic
        return ExecutionActionResult(
            action_id=action["id"],
            action_type=action["type"],
            status="ok",
            message="Example handler (replace with real logic)",
        )
"""

_README_TEMPLATE = """\
# {plugin_name}

A plugin for [DITA Package Processor](https://github.com/yourorg/dita-package-processor).

## Installation

```bash
pip install -e .
```

## Verify

```bash
dita_package_processor plugin list
dita_package_processor plugin info {plugin_name}
```

## What this plugin does

TODO: describe your plugin's purpose.

## Developing

1. Edit `{plugin_name}/plugin.py` to add patterns, action emitters, and handlers.
2. Add patterns to `{plugin_name}/patterns.yaml`.
3. Add handler implementations to `{plugin_name}/handlers/`.
4. Run validation: `dita_package_processor plugin validate .`
5. Run the full test suite: `pytest tests/`
"""


# =============================================================================
# Scaffold generation
# =============================================================================


def _prompt(label: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"{label}{hint}: ").strip()
    return value or default


def _to_class_name(plugin_name: str) -> str:
    """Convert snake_case plugin name to CamelCase class name."""
    return "".join(part.capitalize() for part in plugin_name.split("_")) + "Plugin"


def _to_hyphen(plugin_name: str) -> str:
    return plugin_name.replace("_", "-")


def generate_scaffold(output_dir: Path, plugin_name: str, author: str, version: str) -> None:
    class_name = _to_class_name(plugin_name)
    plugin_name_hyphen = _to_hyphen(plugin_name)

    ctx = {
        "plugin_name": plugin_name,
        "plugin_name_hyphen": plugin_name_hyphen,
        "class_name": class_name,
        "author": author,
        "version": version,
    }

    root = output_dir / plugin_name_hyphen

    def write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
        print(f"  created  {path.relative_to(output_dir)}")

    print(f"\nGenerating plugin scaffold in: {root}")
    print()

    write(root / "pyproject.toml", _PYPROJECT_TEMPLATE.format(**ctx))
    write(root / "README.md", _README_TEMPLATE.format(**ctx))

    pkg = root / plugin_name
    write(pkg / "__init__.py", _INIT_TEMPLATE.format(**ctx))
    write(pkg / "plugin.py", _PLUGIN_TEMPLATE.format(**ctx))
    write(pkg / "patterns.yaml", _PATTERNS_YAML_TEMPLATE.format(**ctx))

    handlers_pkg = pkg / "handlers"
    write(handlers_pkg / "__init__.py", '"""Handler package."""\n')
    write(handlers_pkg / "example_handler.py", _HANDLER_TEMPLATE.format(**ctx))

    print()
    print("Done. Next steps:")
    print(f"  cd {root}")
    print("  pip install -e .")
    print("  dita_package_processor plugin validate .")
    print()
    print("Edit the generated files to add your real logic.")
    print("See plugin.py for detailed inline documentation.")


# =============================================================================
# Entry point
# =============================================================================


def main() -> None:
    print("DITA Package Processor — Plugin Scaffold Generator")
    print("=" * 50)
    print()

    plugin_name = ""
    while not plugin_name:
        plugin_name = _prompt(
            "Plugin name (snake_case, e.g. acme_dita_bookmap)"
        )
        if not plugin_name.replace("_", "").isalnum():
            print("  Error: use only letters, digits, and underscores.")
            plugin_name = ""

    author = _prompt("Author name", "Your Name")
    version = _prompt("Version", "0.1.0")

    output_dir = Path.cwd()
    generate_scaffold(output_dir, plugin_name, author, version)


if __name__ == "__main__":
    main()
