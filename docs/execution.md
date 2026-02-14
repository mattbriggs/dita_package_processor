# How Execution and Run Work  
*DITA Package Processor – Execution & Orchestration Guide*

This document explains **how the `execute` and `run` commands work**, how they consume a plan, what guarantees they enforce, and how execution results are recorded.

This is not a CLI reference.  
This is a **conceptual guide** to how the system applies intent safely.

---

## The Role of Execution in the System

Execution is the **only phase that can mutate the filesystem**.

Because of that, it is deliberately constrained.

Execution does **not**:
- discover content
- infer structure
- generate actions
- fix bad plans
- guess paths

Execution answers exactly one question:

> **“Given this plan, what happened when I tried to apply it?”**

If something is not explicitly described in the plan, execution is not allowed to do it.

---

## The Execution Contract

Execution operates under a strict contract:

```
Plan → Executor → Handlers → Execution Report
```

Execution trusts **only**:
- the plan artifact
- the executor configuration
- explicit user intent (`--apply`)

Everything else is rejected.

---

## What `execute` Does

The `execute` command applies a **single, already-validated plan**.

### Conceptual Responsibilities of `execute`

`execute` is intentionally narrow. It:

1. Loads a plan artifact (`plan.json`)
2. Normalizes it into execution-safe data
3. Selects an executor
4. Dispatches actions in order
5. Records results
6. Emits an execution report

That is all.

If you are expecting `execute` to be helpful, you are using the wrong command.

---

### What `execute` Requires

At minimum:

- A valid `plan.json`
- A source root (`--source-root`)
- An output directory (`--output`)
- Explicit permission to mutate (`--apply`) if mutation is desired

If any of these are missing, execution fails fast.

This is not user hostility.  
This is safety.

---

### Dry-Run vs Apply

Execution always runs in one of two modes:

| Mode | Behavior |
|----|--------|
| Dry-run (default) | Actions are dispatched but **never mutate** |
| Apply (`--apply`) | Filesystem executor is allowed to write |

Dry-run is not a shortcut.  
It uses the *same* dispatch path, handlers, and validation.

The only difference is whether mutations are allowed.

---

## Executors: How Execution Is Performed

Execution is mediated by an **executor**, not by handlers directly.

### Why Executors Exist

Executors enforce:
- path resolution
- sandbox boundaries
- mutation policy
- dry-run semantics

Handlers do not get to decide whether they may write.

---

### Current Executors

#### NoOpExecutor (`noop`)

- Default for `execute`
- Always dry-run
- Never mutates
- Used for inspection, CI, and safety checks

#### FilesystemExecutor (`filesystem`)

- Activated only when `--apply` is present
- Enforces sandbox and mutation policy
- Dispatches real filesystem mutations
- Still records results identically to dry-run

The executor is the **last line of defense** before files are touched.

---

## How a Plan Is Used During Execution

Execution treats the plan as immutable truth.

For each action in the plan:

1. The executor selects a handler by `action.type`
2. The handler validates inputs again
3. The handler performs exactly one mutation (or skips)
4. A structured result is returned

No handler:
- creates new actions
- modifies the plan
- reorders execution
- inspects other actions

Execution is linear and ordered.

---

## Handlers During Execution

Handlers are the only code allowed to touch files.

They are:
- action-type specific
- deterministic
- defensive
- auditable

Execution never “figures out” which handler to use.  
That mapping is explicit and static.

If a handler is missing, execution fails immediately.

---

## What the Execution Report Is

The **Execution Report** is the forensic record of execution.

It answers:

> **“What happened when this plan was executed?”**

Not:
- “What does the filesystem look like now?”
- “What would I do next?”
- “What should have happened?”

---

### Execution Report Structure

An execution report records:

- Execution identity
- Timestamp
- Whether it was a dry-run
- One entry per action
- A summary of outcomes

Each action result includes:

- `action_id`
- `handler`
- `status` (`success`, `failed`, `skipped`)
- `dry_run`
- A human-readable message
- Optional error details
- Optional structured metadata

The report is schema-validated and immutable once written.

---

### Why the Report Matters

The execution report allows you to:

- Prove what happened
- Diff execution outcomes
- Debug failures mechanically
- Explain changes to auditors or stakeholders
- Rerun safely with confidence

Execution without a report is guesswork.  
This system does not allow that.

---

## What `run` Does (And Why It Exists)

The `run` command exists to solve **orchestration**, not execution.

`run` is the **only command** that composes phases together.

Conceptually:

```
run = discover + plan + execute
```

But critically:

- Each phase still produces its own artifacts
- Each phase still validates its inputs
- Execution still requires explicit permission to mutate

`run` does not weaken contracts.  
It only wires them together.

---

## Why `run` Is Separate from `execute`

Because conflating orchestration and execution is how systems rot.

`execute` must remain:
- testable in isolation
- reusable by other tools
- safe by default
- boring

`run` is allowed to be convenient.  
`execute` is not.

This separation is intentional and permanent.

---

## What Happens When You Use `run`

When you invoke:

```bash
dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc \
  --target /path/to/output \
  --apply
```

The system performs:

```
Discovery
  ↓
Planning
  ↓
Materialization preflight
  ↓
Execution
```

Key points:

- Discovery output is not reused implicitly
- Planning output is still a real plan
- Execution still consumes a plan artifact internally
- Mutation only occurs if `--apply` is present

`run` is orchestration glue, not intelligence.

---

## Common Mental Errors (And the Correct Model)

### ❌ “Why doesn’t execute figure things out?”

Because that would destroy auditability.

### ❌ “Why does execute need source-root?”

Because execution must never guess where files come from.

### ❌ “Why didn’t files appear without --apply?”

Because simulation and mutation are not the same thing.

### ✅ Correct mental model

- Planning decides *what should happen*
- Execution applies *only that*
- Reports tell you *what actually happened*

---

## Debugging Execution Correctly

When something goes wrong:

1. Inspect `plan.json`
2. Inspect the execution report
3. Identify the failing action
4. Fix:
   - planning logic **or**
   - handler logic

Never debug by re-running blindly.

This system gives you documents so you don’t have to guess.

---

## Summary

- `execute` applies a plan and records results
- It is strict by design
- It never infers, discovers, or plans
- It mutates only with explicit permission
- It always produces a forensic record

- `run` orchestrates the full pipeline
- It preserves all boundaries
- It exists for ergonomics, not shortcuts

If planning answers *what should happen*,  
and execution answers *what happened*,  
then `run` is simply the conductor keeping time.

Execution stays boring so the system stays alive.