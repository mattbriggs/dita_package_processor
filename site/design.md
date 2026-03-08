# Design: DITA Package Processor

## Overview

The current system is a deterministic, contract-driven DITA processing toolchain with a plugin-based extension model.

The public lifecycle is:

```text
discover -> normalize -> plan -> execute
```

The `run` command orchestrates that lifecycle and wraps execution with materialization preflight and finalize behavior.

## Design Goals

### 1. Deterministic Behavior

- the same input contract should produce the same plan
- the same plan and execution mode should produce the same execution behavior
- ordering is explicit and stable
- failures should be structural and loud, not heuristic

### 2. Contracts Between Phases

Each phase produces a durable artifact or model boundary:

- discovery produces inventory and report data
- normalization produces `PlanningInput`
- planning produces `plan.json`-compatible action data
- execution produces an `ExecutionReport`

This keeps reasoning localized. If something is wrong, there is a concrete boundary to inspect.

### 3. Plugin-Based Extensibility

The current extension surface is the plugin system, not runtime pipeline step injection.

Plugins can contribute:

- discovery patterns
- planning action emission
- execution handlers

Built-in behavior is exposed through `CorePlugin`, which loads before any third-party plugin.

### 4. Explicit Mutation Boundaries

- discovery does not mutate
- normalization does not mutate
- planning does not mutate
- execution is dry-run by default
- real writes require `--apply` and a bounded target root

## High-Level Architecture

```text
CLI
  -> Discovery
  -> Normalization
  -> Planning
  -> Materialization preflight
  -> Execution
  -> Execution report
```

Cross-cutting extension flow:

```text
plugins.patterns() -> discovery evidence
plugins.emit_actions() -> plan actions
plugins.handlers() -> execution registry
```

## Responsibility Map

| Concern | Current Location |
|------|--------|
| CLI routing and global flags | `cli.py` and `cli_*` modules |
| Discovery scanning and reports | `discovery/*` |
| Discovery-to-planning normalization | `planning/contracts/*` |
| Plan generation | `planning/planner.py` |
| Pipeline orchestration | `pipeline.py` |
| Materialization safety/finalize | `materialization/*` |
| Executor selection and dispatch | `orchestration.py`, `execution/*` |
| Plugin contract and loading | `plugins/*` |

## Plugin Design

### `DitaPlugin`

`DitaPlugin` is the root extension contract.

Each plugin must expose:

- `name`
- `version`

And may expose:

- `patterns()`
- `emit_actions(...)`
- `handlers()`

### Loading Model

Plugins are loaded from the Python entry-point group `dita_package_processor.plugins`.

Load order is deterministic:

1. `CorePlugin`
2. third-party plugins sorted by entry-point name

### Conflict Rules

The system fails at startup on:

- duplicate pattern IDs across plugins
- duplicate handler `action_type` values across plugins
- structurally invalid plugins

This is intentional. Silent extension conflicts are not acceptable in this tool.

## Discovery Design

Discovery observes package structure and classification evidence.

Current discovery classification is plugin-aware:

- the classifier asks the plugin registry for all patterns
- built-in and third-party patterns participate in the same evaluation path
- discovery carries evidence forward for planning

Discovery is read-only and should never encode mutation behavior.

## Planning Design

Planning consumes `PlanningInput` only.

The planner:

- sorts artifacts deterministically
- asks every loaded plugin to emit actions for each artifact
- assigns stable action IDs after aggregation
- validates the resulting plan against the schema and invariants

The planner does not discover files, mutate content, or register handlers.

## Execution Design

Execution is mediated by executors and handlers.

- executors enforce dry-run versus apply behavior
- handlers implement one action type each
- the execution handler registry is populated from plugin-contributed handlers

This means the execution layer is also plugin-aware, not manually hardcoded through import-time registration.

## Materialization Design

Materialization remains the safety boundary around execution.

It is responsible for:

- preflight validation of the target root
- finalization around execution output
- report-related artifact handling

It does not replace planning or execution and should not become a hidden behavior layer.

## Testing Strategy

Current testing emphasis:

- contract tests for discovery, planning, execution, and schemas
- execution tests around filesystem and safety behavior
- integration tests across end-to-end flows
- plugin-aware behavior verified through planning and execution surfaces

## Non-Goals

The current system is not:

- an interactive editor
- an inference engine
- a silent repair tool
- an unbounded workflow engine
- a step-injection framework for external customization

## Summary

The repo has moved from an older step-oriented architecture to a contract-and-plugin architecture:

- phases are explicit
- extension points are explicit
- mutation is explicit
- conflicts fail loudly

That is the current design center.
