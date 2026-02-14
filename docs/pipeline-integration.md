# Pipeline Integration Specification

This document defines how the **Discovery subsystem** integrates with the
DITA Package Processor pipeline.

Discovery does not transform content.
The pipeline does not re-discover structure.

They communicate through **explicit artifacts**, not vibes.

---

## Design Goal

The pipeline must be able to:

- Adapt to real-world DITA package variation
- Make structural assumptions explicit
- Refuse unsafe transformations deterministically
- Avoid hardcoding corpus-specific heuristics

Discovery enables this by producing a **machine-readable structural record**
that the pipeline can consult.

---

## High-Level Flow

```
Filesystem
   ↓
Discovery Scanner
   ↓
Artifact Metadata
   ↓
Pattern Evaluation
   ↓
Evidence
   ↓
Discovery Report (JSON)
   ↓
Pipeline Planning
   ↓
Transformation Execution
```

Discovery always runs **before** the pipeline.

---

## Discovery Output Contract

Discovery emits a JSON report containing:

- Discovered artifacts
- Structural metadata
- Pattern evidence
- Summary counts
- Invariant violations (if any)

This report is:

- Read-only
- Serializable
- Stable across runs
- Suitable for version control

The pipeline treats the report as **input**, not suggestion.

---

## Pipeline Consumption Model

The pipeline consumes discovery output in three distinct phases.

---

## Phase 1: Preflight Validation

Before any transformation occurs, the pipeline evaluates:

- Structural invariants
- Required artifact presence
- Cardinality constraints

Examples:

- Exactly one MAIN map required
- At least one executable map present
- No orphaned topics (optional)

### Behavior

| Condition | Pipeline Action |
|--------|----------------|
| All invariants pass | Continue |
| Non-fatal violations | Warn |
| Fatal violations | Abort |

Discovery never aborts the pipeline.
The pipeline decides.

---

## Phase 2: Planning

The pipeline uses discovery evidence to **plan** transformations.

Planning answers questions like:

- Which map is the entry point?
- Which maps are containers vs executable?
- Which topics are glossary material?
- Which artifacts should be ignored?

Planning produces a **plan**, not side effects.

### Important Rule

> Planning is deterministic and explainable.

If the pipeline cannot explain *why* it is transforming something,
it must refuse to proceed.

---

## Phase 3: Execution

Only after planning is complete does execution begin.

Execution may:

- Normalize structures
- Reparent topicrefs
- Generate derived maps
- Rewrite content safely

Execution must never:

- Re-run discovery
- Re-evaluate patterns
- Guess intent

Discovery results are treated as authoritative for the run.

---

## Evidence Resolution Strategy

Discovery may emit **multiple conflicting evidence records** for a single artifact.

Example:

- `index.ditamap` asserted as MAIN (confidence 0.9)
- `single_root_map` asserted as MAIN (confidence 0.7)

The pipeline resolves conflicts using a resolver policy:

- Highest confidence wins
- Ties require explicit configuration
- Fallback evidence is always lowest priority

Resolvers are explicit, testable, and versioned.

---

## Configuration Hooks

The pipeline may be configured to:

- Override pattern confidence thresholds
- Disable specific pattern IDs
- Require specific roles to be present
- Treat certain roles as fatal if missing

All overrides are declarative and logged.

There is no hidden behavior.

---

## Failure Philosophy

Discovery failures are **data**.
Pipeline failures are **decisions**.

The pipeline must never silently:

- Guess a main map
- Invent a glossary
- Ignore structural anomalies

If the pipeline proceeds, it does so knowingly.

---

## Non-Goals

This integration explicitly does **not**:

- Use discovery to auto-fix packages
- Rewrite discovery output
- Call LLMs at runtime
- Introduce nondeterminism

Discovery is analysis.
The pipeline is action.

---

## Summary

Discovery answers:

> “What is actually here?”

The pipeline answers:

> “Given that reality, what can we safely do?”

They are separate on purpose.
Confusing them is how tools become untrustworthy.

This integration makes that confusion impossible.