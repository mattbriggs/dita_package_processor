# Pipeline Behavior

The DITA Package Processor executes as a **linear, ordered pipeline** with **explicit phase boundaries**.

There is no dynamic orchestration, no branching logic, and no implicit retries.

Instead of runtime “steps,” the system operates through **three deterministic phases**:

```
Discovery → Planning → Execution
```

Each phase has a single responsibility and produces a durable artifact consumed by the next phase.

---

## Pipeline Overview

The pipeline is **structural, not procedural**.

- Discovery observes the package
- Planning decides what should happen
- Execution applies (or simulates) those decisions

There is **no configuration-driven step execution at runtime**.  
All behavior is made explicit in the **plan**.

---

## Phase Responsibilities

### 1. Discovery (Read-only)

**Purpose**

Establish the structural truth of the package.

**Behavior**

- Scans maps, topics, and media
- Classifies artifacts by observable structure
- Builds a dependency graph
- Records relationships and invariants
- Identifies unsafe or ambiguous constructs

**Outputs**

- Discovery inventory
- Graph (nodes + edges)
- Structural summary

**Failure semantics**

- Fails fast on invalid XML
- Refuses to guess when structure is ambiguous

Discovery answers one question:

> *What actually exists in this package?*

---

### 2. Planning (Deterministic, Non-destructive)

**Purpose**

Translate discovery results into an **explicit execution plan**.

**Behavior**

- Applies deterministic planning rules
- Produces ordered, schema-validated actions
- Records *why* each action exists
- Produces no side effects

**Typical planned actions include**

- Selecting the true main map
- Copying maps, topics, and media into a sandbox
- Renaming the main map deterministically
- Wrapping map content under generated topicrefs
- Refactoring glossary content (if configured)

**Important**

Planning contains **no executable logic**.  
It only describes *what would happen if execution were allowed*.

**Failure semantics**

- Fails if required invariants cannot be proven
- Produces an empty plan rather than unsafe actions

Planning answers a different question:

> *What actions are safe, explicit, and justifiable?*

---

### 3. Execution (Explicit and Bounded)

**Purpose**

Apply a validated plan using a concrete executor.

**Behavior**

- Executes actions strictly in plan order
- Resolves all paths via `source_root` and sandbox
- Enforces mutation policy
- Records an immutable execution report

**Execution modes**

- **Dry-run (default)**  
  - Simulates all actions  
  - Never mutates the filesystem  

- **Filesystem execution (`--apply`)**  
  - Mutates only within the sandbox  
  - Requires explicit permission  

**Failure semantics**

- Action-level validation failures stop execution
- Recoverable conditions produce `skipped` results
- Every outcome is recorded

Execution answers the final question:

> *What actually happened when this plan was applied?*

---

## About “Steps” (Important Clarification)

Earlier versions of the system used **runtime-configured steps** such as:

- RemoveIndexMap
- RenameMainMap
- ProcessMaps
- RefactorGlossary

These are **no longer runtime pipeline steps**.

Today:

- Their logic lives in **planning rules**
- Their effects are realized via **execution handlers**
- Ordering is enforced by the **plan**, not configuration

This change is intentional and eliminates:
- hidden control flow
- partial execution
- step coupling

---

## Structural Outcomes

After a successful **applied execution**:

- Output exists only under the sandbox directory
- Main map selection is explicit
- Renames and refactors are deterministic
- Topic hierarchy is normalized
- Optional glossary refactors occur only if planned

If execution is dry-run, **no files are written**, by design.

---

## Determinism and Failure Semantics

- Discovery precedes planning
- Planning precedes execution
- Execution never invents behavior
- No implicit retries or fallbacks
- All failures are explicit and observable
- Logs are supplemental, not authoritative

There is no “silent success.”

---

## Summary

The pipeline is intentionally conservative:

- **Phases, not steps**
- **Plans, not heuristics**
- **Explicit mutation**
- **Auditable outcomes**

This design exists to make large, unreliable DITA packages **safe to transform**, not fast to process.

If the plan does not say it will happen, it will not happen.