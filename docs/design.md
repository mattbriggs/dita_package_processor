# Design: DITA Package Processor

## Overview

The DITA Package Processor is a **deterministic, batch-oriented transformation engine** for bulk-generated **DITA 1.3 packages**.

It is designed to:

- Normalize inconsistent, machine-generated DITA into a predictable structure
- Execute transformations in a strictly ordered, auditable pipeline
- Support incremental extension without destabilizing existing behavior
- Operate safely on real-world XML, not idealized samples
- Be testable end-to-end using real filesystem fixtures

This system deliberately avoids:
- Implicit behavior
- Runtime inference
- Interactive workflows
- Framework-style indirection

If it runs, it runs because the configuration explicitly says so.

---

## Core Design Goals

### 1. Deterministic Execution

- All behavior is driven by explicit configuration
- Execution order is fixed and visible
- Each step runs exactly once per invocation
- No conditional branching hidden inside steps

The same input and configuration always produce the same output.

---

### 2. Extensibility Without Refactoring

- New transformations are added as new pipeline steps
- Existing steps are not modified to accommodate new behavior
- Extensions do not silently alter core semantics

Growth happens by **addition**, not mutation.

---

### 3. Strong Separation of Concerns

Each concern lives in exactly one place:

| Concern | Location |
|------|--------|
| CLI contract | `cli.py` |
| Runtime configuration | `pyproject.toml` |
| Execution orchestration | `pipeline.py` |
| Shared state | `context.py` |
| XML manipulation | `dita_xml.py` |
| Individual transformations | `steps/*` |

This separation is enforced structurally, not by convention.

---

### 4. Testability Over Cleverness

- Steps are testable in isolation
- The full pipeline is testable end-to-end
- Tests operate on real XML and real directories
- No heavy mocking of XML trees or filesystem behavior

If a transformation matters, it is validated structurally.

---

### 5. DITA-Aware, Not DITA-Fragile

The processor uses conservative heuristics that tolerate:

- Imperfect XML
- Inconsistent authoring practices
- Slight schema deviations common in bulk exports

This is intentional. Real DITA packages are messy.

---

## High-Level Architecture

```
CLI
 │
 ▼
Pipeline
 │
 ├── RemoveIndexMapStep
 ├── RenameMainMapStep
 ├── ProcessMapsStep
 └── RefactorGlossaryStep
 │
 ▼
ProcessingContext
```

Supporting layers:

- `dita_xml.py` – Safe XML parsing and transformation helpers
- `utils.py` – Filename and string utilities
- `steps/*` – Independent, single-responsibility processing units

---

## Key Design Patterns

### 1. Pipeline Pattern

**Where:** `pipeline.Pipeline`

The processor uses a classic **Pipeline pattern**:

- A pipeline is an ordered list of steps
- Each step performs a transformation
- The pipeline controls execution order, logging, and error propagation

```python
for step in self._steps:
    logger.info("Running step: %s", step.name)
    step.run(context, logger)
```

**Why this matters**

- Execution order is explicit and reviewable
- Steps can be added, removed, or reordered safely
- Behavior remains boring, predictable, and auditable

Boring is a feature.

---

### 2. Command / Strategy Hybrid (ProcessingStep)

**Where:** `steps.base.ProcessingStep`

Each step implements a shared interface:

```python
class ProcessingStep(abc.ABC):
    name: str

    @abc.abstractmethod
    def run(self, context, logger) -> None:
        ...
```

Each step acts as:

- A **Command**: “Perform this transformation”
- A **Strategy**: One interchangeable behavior in the pipeline

**Benefits**

- Steps are self-contained
- Steps do not call each other
- Steps do not manage execution flow
- Steps can be tested independently

This avoids the “giant script with flags” failure mode.

---

### 3. Context Object Pattern

**Where:** `context.ProcessingContext`

The `ProcessingContext` centralizes:

- Runtime configuration values
- Resolved filesystem paths
- Derived state shared across steps

Instead of globals or parameter sprawl, the pipeline passes a single context object:

```python
@dataclass
class ProcessingContext:
    package_dir: Path
    docx_stem: str
    main_map_path: Optional[Path]
    renamed_main_map_path: Optional[Path]
```

**Why this matters**

- Shared state is explicit and inspectable
- Steps remain loosely coupled
- New derived values can be added without breaking existing steps

---

### 4. Template Method (Implicit)

**Where:** Pipeline execution loop

The pipeline enforces a fixed execution structure:

- Setup
- Step execution
- Logging
- Failure propagation

Steps decide **what** to do.  
The pipeline decides **when** and **how** they run.

This prevents steps from:
- Calling other steps
- Managing logging inconsistently
- Reordering execution

---

### 5. Facade Pattern for XML Operations

**Where:** `dita_xml.py`

All XML manipulation is wrapped behind a small, focused API:

- `read_xml`
- `write_xml`
- `get_map_title`
- `get_top_level_topicrefs`
- `create_concept_topic_xml`
- `transform_to_glossentry`

This creates a **Facade** over `lxml`.

**Benefits**

- XPath logic is centralized
- XML handling remains consistent across steps
- DITA edge cases can be fixed in one place

If DITA conventions change, the blast radius is contained.

---

### 6. Functional Core, Imperative Shell

- **Functional core**
  - XML tree transformations
  - Slug generation
  - Structural rewrites
- **Imperative shell**
  - File I/O
  - Logging
  - CLI parsing
  - Configuration loading

This separation improves:
- Reasoning about correctness
- Unit testing
- Debugging failed runs

---

## Step Responsibilities

### RemoveIndexMapStep

- Reads `index.ditamap`
- Resolves the referenced main map
- Deletes `index.ditamap`

**Responsibility**

> Establish the true entry point and remove indirection.

---

### RenameMainMapStep

- Renames the resolved main map to `<docx_stem>.ditamap`

**Why separate**

Renaming is a structural operation and should not be entangled with content rewriting.

---

### ProcessMapsStep

This step performs the core normalization work:

- Detects the abstract map
- Injects abstract content into the main map
- Numbers remaining maps deterministically
- Creates wrapper concept topics
- Reparents existing topicrefs under the wrapper

**Cohesive responsibility**

> Normalize map structure and impose a deterministic hierarchy.

---

### RefactorGlossaryStep

- Locates the definition node in the definition map
- Iterates its child topicrefs
- Converts each referenced topic into a `glossentry` in place

This logic is isolated because glossary behavior evolves independently.

---

## Error Handling Philosophy

- **Fail fast** for structural impossibilities  
  (missing index map, unresolved main map)
- **Warn and continue** for content inconsistencies  
  (missing topics, unmatched navtitles)
- **No silent failures**

Every failure mode is logged with step context.

---

## Testing Strategy

### Integration-First Testing

- Tests use `pytest` and `tmp_path`
- Real directories and XML files are created
- Assertions validate structural outcomes, not internal state

This avoids brittle mocks and validates real-world behavior.

---

## Extensibility Scenarios

New behavior requires no refactoring:

Examples:

- Regex-based cleanup step
- Attribute normalization step
- DITA 1.2 → 1.3 migration step
- Metadata enrichment step
- Validation or linting step

To add behavior:

1. Create a new step in `steps/`
2. Register it
3. Add it to `pipeline.steps`

Nothing else changes.

---

## Design Non-Goals (Intentional)

This project does **not** attempt to be:

- A plugin framework
- An interactive assistant
- A workflow engine
- A schema repair tool
- A dynamic inference system

It is a batch processor.

---

## Summary

The DITA Package Processor applies well-understood, conservative design patterns to a messy, real-world problem:

- Pipeline for orchestration
- Command/Strategy for extensibility
- Context object for shared state
- Facade for XML safety

The result is a system that scales in capability without collapsing under cleverness.

That is the design.