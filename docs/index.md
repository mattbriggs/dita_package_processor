# DITA Package Processor

The **DITA Package Processor** deterministically analyzes, plans, and transforms **DITA 1.3 packages** into a controlled, publication-ready structure.

It operates as a **strict, multi-phase batch pipeline** with explicit boundaries between:

- **Discovery** – observe and describe what exists  
- **Planning** – derive a validated, auditable execution plan  
- **Execution** – apply or simulate changes using a bounded executor  

Every run is explicit, repeatable, and explainable.

There is no inference.  
There is no runtime guessing.  
Nothing mutates unless an explicit executor is invoked with permission.

---

## What It Does

Given a bulk-generated DITA package, the processor performs a **three-stage workflow**.

Each stage:

- has a single responsibility  
- produces a durable, machine-readable artifact  
- is independently testable  
- refuses to proceed on invalid or ambiguous input  

The system is designed so that **structure is proven before behavior is allowed**.

---

## Phase 1: Discovery (Read-only)

Discovery scans the input package without mutating any files.

It:

- Locates maps, topics, and media  
- Classifies artifacts by observable structure  
- Builds a dependency graph  
- Records structural relationships  
- Identifies known patterns and unsafe conditions  

Discovery produces a **Discovery Contract** that describes:

- artifacts and their roles  
- dependency edges between artifacts  
- structural invariants  
- ambiguous or unsupported constructs  

Discovery exists to answer exactly one question:

> *What is actually in this package?*

If something cannot be observed safely, it is not acted upon later.

---

## Phase 2: Planning (Deterministic, Non-destructive)

Planning converts discovery output into an **explicit execution plan**.

The plan:

- Contains **no executable logic**  
- Describes **what actions would be taken and why**  
- Is schema-validated and serializable  
- Is deterministic and repeatable  
- Can be inspected, reviewed, versioned, and tested  

A plan may include actions such as:

- Selecting the true main map  
- Copying maps, topics, and media into a new structure  
- Renaming the main map based on a DOCX stem  
- Reparenting `topicref` elements deterministically  
- Wrapping or restructuring maps  
- Injecting or refactoring glossary content when configured  

Planning is considered *green* when:

- Actions are non-empty (unless analysis-only)  
- Ordering is deterministic  
- Output conforms to the plan schema  

If planning cannot prove an action is safe, **the action is not planned**.

Planning answers a different question:

> *What would we do if execution were allowed?*

---

## Phase 3: Execution (Explicit and Bounded)

Execution consumes a validated plan and applies it using a concrete **executor**.

Key properties:

- Executors are **named, explicit implementations**  
- Execution is **dry-run by default**  
- Filesystem mutation requires explicit opt-in (`--apply`)  
- All paths are resolved via a declared `source-root` and sandbox  
- Each action is executed exactly once, in order  
- Results are captured as structured data  

Two executors exist today:

- **DryRunExecutor (`noop`)**  
  - Always simulates  
  - Never mutates  
  - Used when `--apply` is not provided  

- **FilesystemExecutor (`filesystem`)**  
  - Performs real filesystem operations  
  - Enforces sandbox and mutation policies  
  - Requires explicit `--apply`  

Execution produces an **Execution Report** that:

- records execution identity and mode  
- records every action result  
- records failures, skips, and successes  
- is schema-defined and immutable  

Execution may also emit an **Execution Manifest**, recording *what actions occurred*, not an inferred filesystem state.

---

## Quick Start

### Run the full pipeline (safe by default)

```bash
dita_package_processor run \
  --package /path/to/dita/package \
  --output build
```

This performs discovery, planning, and **dry-run execution**.  
No filesystem mutation occurs.

---

### Apply changes explicitly

```bash
dita_package_processor run \
  --package /path/to/dita/package \
  --output build \
  --apply
```

Mutation is **explicit, intentional, and bounded**.

---

### Execute a plan directly

```bash
dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/original/package \
  --output build \
  --apply
```

Execution requires an explicit `source-root` so that relative paths in the plan can be resolved safely.

---

## Configuration Model

Runtime behavior can be influenced via **`pyproject.toml`** under:

```toml
[tool.dita_package_processor]
```

Configuration controls:

- which planning steps are enabled  
- optional behaviors (e.g., glossary handling)  
- naming conventions  

Precedence order:

```
CLI arguments > pyproject.toml > defaults
```

Configuration never overrides structural validation.  
It only enables or disables *safe, predefined behaviors*.

---

## Execution Model

- Linear, ordered pipeline  
- Discovery → Planning → Execution  
- One responsibility per phase  
- No implicit branching or retries  
- Shared state via explicit models  
- Fail fast on structural violations  

There is no hidden control flow.  
There is no “smart” behavior at runtime.

---

## Why This Exists

This tool exists to address a recurring failure mode in real systems:

- Bulk DITA exports are inconsistent  
- Assumptions fail silently  
- Scripts mutate content without proof  
- Errors surface too late  

The DITA Package Processor favors:

- Observation before action  
- Plans before mutation  
- Explicit structure over cleverness  
- Boring logic you can audit  
- Systems that survive real corpora  

If you want deterministic batch processing over real DITA packages, this tool exists for you.

If you want inference, auto-repair, or magic, it does not.

---

## Documentation Map

- **Getting Started** – Installation and first run  
- **CLI** – Commands, flags, and contracts  
- **Discovery** – Scanning, classification, and graph construction  
- **Planning** – Steps, actions, and invariants  
- **Execution** – Executors, safety, reports, and manifests  
- **Configuration** – `pyproject.toml` reference  
- **Design** – Architectural constraints and rationale  
- **Extensions** – Adding steps and handlers safely  
- **Testing** – Validation at unit, integration, and system levels  

Each document is intentionally narrow and non-overlapping.

---

## Summary

The DITA Package Processor is conservative by design:

- Discovery before planning  
- Planning before execution  
- Dry-run before mutation  
- Explicit permissions  
- Deterministic ordering  
- Schema-validated artifacts  
- No hidden behavior  

This is a system designed to **survive reality**, not pretend it does not exist.

If you want, the next logical step is:
- a **“User vs Developer mental model” page**, or  
- a **“How to add a new transformation safely” guide**, or  
- a **worked end-to-end example with real artifacts**.