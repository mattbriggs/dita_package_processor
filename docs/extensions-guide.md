# Extension Guide

This guide documents the current plugin-first extension architecture in the repository.

## Architecture

The extension path is vertical, not step injection into the old pipeline:

```text
plugin patterns -> discovery evidence -> plugin emit_actions -> execution handlers
```

A plugin can participate in one layer or all three.

## Minimal Plugin Shape

```python
from dita_package_processor.plugins.protocol import DitaPlugin


class MyPlugin(DitaPlugin):
    @property
    def name(self) -> str:
        return "com.example.my_plugin"

    @property
    def version(self) -> str:
        return "1.0.0"
```

## Entry Point Registration

Declare the plugin in `pyproject.toml`:

```toml
[project.entry-points."dita_package_processor.plugins"]
my_plugin = "my_package:plugin"
```

The entry point can resolve to:

- a module-level `DitaPlugin` instance
- a `DitaPlugin` subclass, which the loader will instantiate

## Discovery Contribution

Implement `patterns()` to return a list of `Pattern` objects. Pattern IDs must be globally unique across all loaded plugins.

Common approach:

- load YAML-backed patterns
- namespace every pattern ID with the plugin name
- keep asserted roles stable because they become planning evidence

## Planning Contribution

Implement `emit_actions(artifact, evidence, context)` to emit action template dictionaries.

Requirements:

- return a list
- omit the `id` field
- emit only action types that have registered handlers
- keep targets package-relative and deterministic

The planner assigns global action IDs after aggregating output from every plugin.

## Execution Contribution

Implement `handlers()` to return execution handler classes.

Each handler class must:

- expose a unique `action_type`
- implement `execute(...)`
- be structurally valid under `validate_plugin(...)`

## Validation and Introspection

Use the CLI during development:

```bash
python3 -m dita_package_processor plugin validate /path/to/plugin
python3 -m dita_package_processor plugin list
python3 -m dita_package_processor plugin info com.example.my_plugin
```

Validation checks include:

- non-empty plugin name and version
- valid pattern objects
- valid handler classes
- duplicate IDs or action types within a plugin

Cross-plugin conflicts are detected when the plugin registry aggregates all loaded plugins.

## Scaffolding

Use the included helper to create a starter package:

```bash
python3 tools/scaffold_plugin.py
```

The scaffold includes:

- `pyproject.toml`
- a module-level plugin singleton
- a `DitaPlugin` subclass skeleton
- starter pattern YAML
- starter handler skeletons

## Compatibility Notes

- `CorePlugin` is the reference implementation and loads first.
- Discovery, planning, and execution now all consume plugin registry output.
- Older docs that described extensions only as pipeline step classes should be treated as historical, not current API guidance.
