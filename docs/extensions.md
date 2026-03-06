# Extensions

The current extension mechanism is the plugin system under `dita_package_processor.plugins`.

The old step-centric extension guidance in this repo is no longer accurate as the primary public model. Internal step modules still exist, but supported external extensibility now happens through plugins.

For the full implementation playbook, see [Extension Guide](extensions-guide.md).

## Plugin Contract

A plugin can contribute three things:

- discovery patterns via `patterns()`
- planning action templates via `emit_actions(...)`
- execution handlers via `handlers()`

All plugins implement `DitaPlugin` and are loaded through the Python entry-point group. The API details are documented in [Plugin API Reference](api-ref-plugins.md).

```toml
[project.entry-points."dita_package_processor.plugins"]
my_plugin = "my_package:plugin"
```

## Load Model

Load order is deterministic:

1. `CorePlugin` always loads first.
2. Third-party plugins load in alphabetical order by entry-point name.

The registry fails loudly on conflicts:

- duplicate pattern IDs
- duplicate handler `action_type` values
- invalid plugin structure

## Built-In Plugin

Built-in behavior is wrapped by `dita_package_processor.plugins.core_plugin.CorePlugin`.

That plugin currently provides:

- normalized discovery patterns from `knowledge/known_patterns.yaml`
- built-in planning action emission for artifact copy routing
- built-in filesystem and semantic execution handlers

## Tooling

The repo includes a scaffold helper:

```bash
python3 tools/scaffold_plugin.py
```

And CLI inspection commands:

```bash
python3 -m dita_package_processor plugin list
python3 -m dita_package_processor plugin info dita_package_processor.core
python3 -m dita_package_processor plugin validate /path/to/plugin
```

## Scope Boundary

Plugins are the supported external extension surface.

Internal modules such as legacy pipeline steps, orchestration helpers, or direct CLI wiring should not be treated as stable extension APIs unless they are explicitly documented in the API reference.
