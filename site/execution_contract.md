# Execution Contract

This document defines the **execution layer contract** for the DITA Package Processor.

The execution layer is responsible for applying a generated plan to a target environment. It is the only layer permitted to perform side effects (filesystem mutation).

This document is normative. Tests, integration points, and future executors must conform to it.



## 1. Architectural Boundary

The execution layer sits between:

- Planning (pure, deterministic plan generation)
- Materialization (effects on disk)

Execution consumes a **plan dictionary** and produces an **ExecutionReport**.

It does not:

- Re-plan
- Infer missing fields
- Modify planning output
- Read discovery data directly



## 2. Executor Responsibilities

Execution is divided into three layers:

### 2.1 Dispatcher

The dispatcher:

- Iterates over `plan["actions"]`
- Preserves action order
- Invokes `executor.execute(action)`
- Collects `ExecutionActionResult`
- Produces `ExecutionReport`

The dispatcher owns:

- Plan iteration
- Plan-level validation
- Aggregation of results
- Summary calculation

The dispatcher does **not**:

- Perform filesystem operations
- Interpret action semantics



### 2.2 Executor

The executor:

- Executes exactly one action at a time
- Resolves handler from registry
- Injects dependencies (source_root, sandbox, policy)
- Catches and classifies failures
- Returns `ExecutionActionResult`

The executor owns:

- Handler resolution
- Policy enforcement
- Sandbox enforcement
- Failure translation

The executor does **not**:

- Iterate over plan
- Mutate plan
- Perform cross-action coordination



### 2.3 Handlers

Handlers:

- Perform concrete side effects
- Operate only on injected dependencies
- Must not guess paths
- Must not use CWD
- Must not access global state

Handlers may accept any subset of:

- `action`
- `source_root`
- `sandbox`
- `policy`

Handlers must return `ExecutionActionResult`.



## 3. FilesystemExecutor Contract

### 3.1 Constructor

```
FilesystemExecutor(
    *,
    source_root: Path,
    sandbox_root: Path,
    apply: bool,
)
```

Parameters:

- `source_root`
  Root directory for reading input artifacts.

- `sandbox_root`
  Root directory for all writes.

- `apply`
  If `True`, mutations are allowed.
  If `False`, execution is dry-run only.

No defaults are permitted.

Executor construction must be explicit.



### 3.2 Plan Entry Point

```
.run(
    *,
    execution_id: str,
    plan: Dict[str, Any],
) -> ExecutionReport
```

Responsibilities:

- Log execution start
- Delegate to dispatcher
- Log completion
- Return ExecutionReport

The executor must not:

- Modify `plan`
- Inject new actions
- Remove actions



### 3.3 Single Action Execution

```
.execute(action: Dict[str, Any]) -> ExecutionActionResult
```

Responsibilities:

1. Validate action has required keys
2. Resolve handler by `action["type"]`
3. Inject supported kwargs
4. Catch exceptions
5. Translate failures into structured result

The method must never raise for handler failures.
All failures must be returned as `ExecutionActionResult`.



## 4. Plan Contract

The executor consumes a plan dictionary of shape:

```
{
  "actions": [
    {
      "id": str,
      "type": str,
      ...
    }
  ]
}
```

Execution layer requires:

- `actions` key exists
- `actions` is a list
- Each action contains:
  - `id`
  - `type`

Dispatcher is responsible for rejecting malformed plans.



## 5. ExecutionReport Contract

`ExecutionReport` must contain:

- `execution_id`
- `results` (ordered list of ExecutionActionResult)
- `summary`

### 5.1 Summary Fields

At minimum:

- `total`
- `succeeded`
- `failed`
- `skipped` (if supported)

Summary must be derived only from results.



## 6. ExecutionActionResult Contract

Each action result must contain:

- `action_id`
- `status`
- `handler`
- `dry_run`
- `message`
- `error` (nullable)

### 6.1 Status Values

Allowed status values:

- `"succeeded"`
- `"failed"`
- `"skipped"`

No additional status values are permitted without schema update.



## 7. Failure Classification

Failures must be explicit and categorized.

Three categories exist:

### 7.1 Handler Error

Handler raised an exception during execution.

Returned as:

```
status="failed"
failure_type="handler_error"
```

### 7.2 Policy Violation

Mutation violated overwrite or sandbox policy.

Returned as:

```
status="failed"
failure_type="policy_violation"
```

### 7.3 Executor Error

Unexpected executor failure.

Returned as:

```
status="failed"
failure_type="executor_error"
```

No silent failures.
No implicit fallback behavior.



## 8. Safety Pipeline

Filesystem mutation flows through:

```
source_root
    ↓
sandbox boundary enforcement
    ↓
mutation policy enforcement
    ↓
handler execution
    ↓
ExecutionActionResult
```

Handlers must not bypass sandbox or policy.

All path resolution flows through the executor.



## 9. Invariants

The following invariants must hold:

- Plan is never mutated.
- Action order is preserved.
- ExecutionReport reflects exact plan order.
- All actions produce results.
- Execution is observable only through ExecutionReport.
- Logging is not a contract surface.



## 10. Test Alignment Requirements

All execution tests must assume:

- `.run()` is the plan entry point.
- `.execute()` is single-action only.
- Constructor requires explicit roots and apply flag.
- Dispatcher owns iteration.
- Failure categories are explicit.

If tests assume otherwise, tests must be updated.



## 11. Versioning

If any of the following change:

- Executor constructor signature
- ExecutionReport shape
- Failure classification taxonomy
- Plan shape requirements

The execution contract version must be incremented.