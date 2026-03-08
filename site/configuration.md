# Configuration (`pyproject.toml`)

The current repo can load configuration from the `[tool.dita_package_processor]` namespace in `pyproject.toml`, but the active runtime contract is narrower than some older docs implied.

Configuration should be treated as supplemental input to the CLI and pipeline, not as a dynamic workflow-definition system.

## Current Reality

What is clearly part of the current runtime surface:

- the tool namespace can be loaded through `config.py`
- CLI arguments provide the strongest runtime control
- `docx_stem`, `definition_map`, and `definition_navtitle` are current concepts in the pipeline
- plugin discovery is driven by Python entry points, not by `pyproject.toml` keys under the tool namespace

What is not the current public model:

- defining an ordered runtime pipeline of external processing steps in config
- using config as the primary extension mechanism

## Namespace

Configuration lives under:

```toml
[tool.dita_package_processor]
```

`config.py` returns only that subtree.

## Common Values In This Repo

The repository currently contains examples like:

```toml
[tool.dita_package_processor.package]
docx_stem = "OutputDoc"

[tool.dita_package_processor.definition]
map = "Definitions.ditamap"
navtitle = "Definition topic"

[tool.dita_package_processor.logging]
level = "INFO"
```

These are best understood as project-local defaults or conventions, not as a complete declarative runtime API.

## Precedence

The intended precedence remains:

```text
CLI arguments > pyproject.toml > defaults
```

In practice, the current CLI exposes the most reliable operational surface.

## Plugin Configuration

Plugins are not registered through `[tool.dita_package_processor.extensions]`.

Plugins are discovered through the Python entry-point group:

```toml
[project.entry-points."dita_package_processor.plugins"]
my_plugin = "my_package:plugin"
```

A plugin may still read its own configuration namespace if it chooses, but that is plugin-specific behavior, not core plugin registration.

## Guidance

- use CLI arguments for operational control
- use the tool namespace for stable project defaults where supported
- do not assume every key present in the sample `pyproject.toml` is an active runtime contract
- do not model extensions as configured step lists

## Summary

`pyproject.toml` is still part of the repo’s configuration story, but the current architecture is contract-and-plugin driven:

- contracts define phase boundaries
- CLI defines operational intent
- plugins define extensibility
