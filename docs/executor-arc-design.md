# Executor Architecture and Design

## Purpose

Executors are the **boundary between planning and reality**.

A plan answers the question:  
> *What should be done, in what order, and why?*

An executor answers the question:  
> *What actually happened when we tried to do it?*

Executors **do not decide**, **do not infer**, and **do not mutate plans**. They simply execute validated instructions and report the outcome.

---

## Core Responsibilities

Every executor must:

1. Accept a **validated `Plan`**
2. Execute actions **in deterministic order**
3. Produce an **`ExecutionReport`**
4. Record **exactly one `ExecutedAction` per `PlanAction`**
5. Be observable **via data**, not logs
6. Never mutate the plan or its actions

If an executor violates any of these, it is broken by design.

---

## The BaseExecutor Contract

All executors inherit from `BaseExecutor`.

### What BaseExecutor does

- Implements the public `execute()` method
- Handles:
  - Execution timing
  - Ordered iteration
  - Result collection
  - Report assembly
- Enforces the invariant:
  > One plan action → one execution record

### What BaseExecutor does *not* do

- It does **not** know how actions work
- It does **not** validate parameters
- It does **not** touch the filesystem
- It does **not** dispatch handlers

Those responsibilities belong to concrete executors.

---

## Executor Identity

Each executor declares:

```python
name: str
```

This value:
- Appears in `ExecutionReport.executor`
- Is **not** the registry key
- Is intended for auditability and traceability

Example:
```python
name = "filesystem"
```

Registry keys (`"filesystem"`, `"noop"`) are **lookup concerns**, not identity.

---

## Executor Registry (`get_executor`)

The registry maps **string identifiers** to executor instances.

Responsibilities:
- Resolve executor name → implementation
- Configure execution mode (e.g. `dry_run`)
- Fail loudly on unknown executors

It does **not**:
- Execute plans
- Validate plans
- Handle execution logic

Think of it as a factory, not a controller.

---

## NoOpExecutor

### Purpose

The `NoOpExecutor` exists to:

- Prove that planning works
- Enable dry-run analysis
- Support testing and introspection
- Provide a reference executor implementation

### Behavior

- Executes zero side effects
- Records every action as `simulated`
- Preserves action order
- Produces a complete `ExecutionReport`

### Design principle

> If the NoOpExecutor breaks, the execution contract is broken.

It is intentionally boring and intentionally dumb.

---

## FilesystemExecutor

### Purpose

The `FilesystemExecutor` is the **first real executor**.

It is responsible for:
- Mutating files
- Emitting manifests
- Running action handlers

Safely.

---

### Dry-run vs Apply

| Mode | Behavior |
|----|----|
| `dry_run=True` (default) | Handlers are **not invoked** |
| `dry_run=False` | Handlers are invoked **exactly once** |

Dry-run still performs **validation**. No execution happens without validation.

---

### Dispatch Model

The executor uses an `ActionDispatchTable`:

```python
handler = self.dispatch_table.get(action.type)
```

Responsibilities:
- Resolve `action.type` → handler
- Fail fast if the action type is unknown

The dispatch table validates **type existence**, not parameters.

---

### Action Validation

Action **parameter validation** is enforced **inside the executor**, not in the dispatcher.

Example:
```python
if action.type == "copy_map":
    if missing required parameters:
        raise ActionValidationError
```

Why this lives here:
- Validation rules are execution-context specific
- Different executors may enforce different constraints
- Plans remain transportable and executor-agnostic

---

### Execution Flow (FilesystemExecutor)

For each action:

1. Resolve handler
2. Validate parameters
3. If dry-run:
   - Record `simulated`
4. If apply:
   - Invoke handler
   - Record `applied`
5. Emit an `ExecutedAction`

No branching, no retries, no hidden logic.

---

## ExecutionReport

Executors produce a single `ExecutionReport` per run.

It contains:
- Executor identity
- Plan version
- Execution timestamps
- Ordered execution results
- Optional paths and errors

This object is the **only supported audit artifact**.

Logs may exist. Logs do not count.

---

## What Executors Are *Not*

Executors are **not**:

- Workflow engines
- Retry systems
- Schedulers
- Planners
- Validators of discovery data
- Error recovery systems

Those can exist later, above or beside executors.

---

## Design Philosophy Summary

- Plans are immutable contracts
- Executors are deterministic machines
- Validation happens before mutation
- Observation happens via structured data
- Dry-run is always safe
- Apply is always explicit

If execution ever feels magical, something is wrong.
