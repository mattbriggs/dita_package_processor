# DITA Package Processor

The DITA Package Processor is a deterministic pipeline for analyzing DITA packages, producing validated planning artifacts, and executing those plans through explicit executors.

The public workflow is:

```text
discover -> normalize -> plan -> execute
```

The `run` command orchestrates that workflow for the common case.

## What Is Current In This Repo

- Discovery classifies artifacts using patterns loaded through the plugin registry.
- Planning emits action templates through plugin `emit_actions(...)`.
- Execution handlers are registered through the plugin system, with the built-in stack exposed as `CorePlugin`.
- CLI support includes `plugin list`, `plugin info`, and `plugin validate`.
- Materialization remains the preflight and finalize boundary around execution.

## Read This First

- [Getting Started](getting-started.md)
- [Configuration](configuration.md)
- [Pipeline](pipeline.md)
- [Run vs Execute](run-vs-execute.md)
- [Extensions](extensions.md)
- [Extension Guide](extensions-guide.md)

## Contracts and Reference

- [CLI API Reference](api-ref-cli.md)
- [Plugin API Reference](api-ref-plugins.md)
- [Planning API Reference](api-ref-planning.md)
- [Execution API Reference](api-ref-execution.md)
- [Schema Reference](reference/schemas/plan.schema.md)

## Design Constraints

- Discovery is read-only.
- Normalization and planning are contract-producing stages, not mutation stages.
- Execution is dry-run by default.
- Real writes require explicit intent and a bounded target path.
- Duplicate plugin pattern IDs or action types are startup errors.
