# DITA Package Processor

The **DITA Package Processor** deterministically analyzes, plans, and transforms **DITA 1.3 packages** into a controlled, publication-ready structure.

It operates as a strict, multi-phase batch pipeline with explicit boundaries between:

- **Discovery** – observe and describe what exists  
- **Planning** – derive a validated, auditable execution plan  
- **Execution** – dispatch deterministic actions  
- **Materialization** – finalize and persist execution results  

Every run is explicit, repeatable, and explainable.

There is no inference.  
There is no runtime guessing.  
Nothing mutates unless explicitly permitted.



## What It Does

Given a bulk-generated DITA package, the processor executes a deterministic workflow.

Each phase:

- has a single responsibility  
- produces a durable, machine-readable artifact  
- is independently testable  
- refuses to proceed on invalid or ambiguous input  

The system is designed so that **structure is proven before behavior is allowed**.



# Phase 1: Discovery (Read-only)

Discovery scans the input package without mutating any files.

It:

- Locates maps, topics, and media  
- Classifies artifacts using declared patterns  
- Builds a dependency graph  
- Records structural relationships  
- Detects ambiguous or unsupported conditions  

Discovery produces a **Discovery Inventory**, describing:

- artifacts and their observable roles  
- dependency edges between artifacts  
- structural invariants  
- evidence used for classification  

Discovery answers one question:

> What is actually in this package?

If something cannot be observed safely, it is not acted upon later.

Discovery never mutates the filesystem.



# Phase 2: Planning (Deterministic, Non-destructive)

Planning converts discovery output into an explicit **Plan**.

The plan:

- contains no executable logic  
- describes what actions would be taken  
- preserves deterministic ordering  
- is schema-validated  
- is serializable and reviewable  

Planning does not touch the filesystem.

It does not infer new structure.  
It does not “fix” ambiguity.

If planning cannot prove that an action is structurally valid, it refuses to produce a plan.

Planning answers a different question:

> What would we do if execution were allowed?



# Phase 3: Execution (Explicit and Bounded)

Execution consumes a validated plan and dispatches actions using a concrete executor.

Execution properties:

- Dry-run is the default  
- Filesystem mutation requires explicit `--apply`  
- All writes are sandboxed to a declared target directory  
- Actions execute exactly once, in order  
- Results are captured as structured data  

Two executors exist:

### DryRunExecutor (`noop`)
- Simulates execution  
- Performs no mutation  
- Used when `--apply` is absent  

### FilesystemExecutor (`filesystem`)
- Performs real filesystem operations  
- Enforces sandbox boundaries  
- Requires explicit `--apply`  

Execution produces an immutable **ExecutionReport** containing:

- execution identity  
- mode (dry-run or apply)  
- ordered action results  
- success, skip, and failure states  

Logs are not the contract.  
The ExecutionReport is.



# Phase 4: Materialization

Materialization operates strictly on execution results.

It:

- performs preflight validation  
- ensures target directory safety  
- finalizes output artifacts  
- writes execution reports when requested  

Materialization never performs discovery or planning logic.

It is the final boundary before persistence.



# Quick Start

## Run the full pipeline (safe by default)

```bash
dita_package_processor run \
  --package /path/to/dita/package \
  --docx-stem OutputDoc
```

This performs:

- Discovery  
- Planning  
- Dry-run execution  

No filesystem mutation occurs.



## Apply changes explicitly

```bash
dita_package_processor run \
  --package /path/to/dita/package \
  --target build \
  --docx-stem OutputDoc \
  --apply
```

Mutation is:

- explicit  
- bounded  
- sandboxed  

`--apply` requires `--target`.



## Execute an existing plan

```bash
dita_package_processor execute \
  --plan plan.json \
  --target build \
  --apply
```

This:

- skips discovery  
- skips planning  
- executes the validated plan  



# Configuration Model

Runtime behavior may be influenced via `pyproject.toml`:

```toml
[tool.dita_package_processor]
```

Configuration may control:

- optional planning behaviors  
- naming conventions  
- feature enablement  

Precedence:

```
CLI arguments > pyproject.toml > defaults
```

Configuration never overrides structural validation.  
It only enables predefined, safe behaviors.



# Execution Model

The pipeline is linear and explicit:

```
Discovery → Planning → Execution → Materialization
```

There is:

- no implicit branching  
- no hidden retries  
- no heuristic repair  
- no runtime inference  

Each boundary is enforced by schema and contract validation.



# Why This Exists

This tool exists because real DITA corpora are inconsistent.

In practice:

- Bulk exports contain structural ambiguity  
- Scripts mutate content without proof  
- Assumptions fail silently  
- Errors surface too late  

The DITA Package Processor favors:

- Observation before action  
- Plans before mutation  
- Determinism over cleverness  
- Explicit boundaries over implicit behavior  
- Systems that survive hostile corpora  

If you want deterministic batch processing over real DITA packages, this tool exists for you.

If you want inference, auto-repair, or magic, it does not.



# Documentation Map

- Getting Started  
- CLI Reference  
- Discovery Architecture  
- Planning Contracts  
- Execution Model  
- Materialization  
- Configuration (`pyproject.toml`)  
- Design Rationale  
- Extension Guide  
- Testing Strategy  

Each document is intentionally narrow and non-overlapping.



# Summary

The DITA Package Processor is conservative by design:

- Discovery before planning  
- Planning before execution  
- Dry-run before mutation  
- Explicit permission required  
- Deterministic ordering  
- Schema-validated artifacts  
- No hidden behavior  

This system is built to survive real-world DITA packages, not ideal ones.