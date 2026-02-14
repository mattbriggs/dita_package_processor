# DITA Package Processor CLI  
Deterministic Discovery, Normalization, Planning, and Execution for DITA Packages

The **DITA Package Processor CLI** is a strict, contract-driven execution interface.

It exists for environments where:

- package structure cannot be trusted
- assumptions must be proven before action
- transformations must be explicit and reviewable
- safety matters more than convenience

This CLI does not optimize for speed or ergonomics.  
It optimizes for **correctness, determinism, and auditability**.

Observe first. Decide explicitly. Then act.

It is not a wrapper.  
It is a transactional interface to a deterministic engine.



## How to Run

```bash
python -m dita_package_processor <command> [options]
```

Editable install:

```bash
pip install -e .
dita_package_processor <command> [options]
```

Behavior is identical.



## Mental Model

The CLI implements a **strict, linear pipeline**:

```
discover → normalize → plan → execute
```

Each phase:

- runs independently
- produces a durable artifact
- consumes only the previous artifact
- refuses invalid input
- is deterministic
- is schema-validated

Artifacts are **not interchangeable**.

If you pass the wrong artifact to a phase, it fails immediately.

This is intentional.



## Reality Check (Important)

**Current behavior:**

All four phases are implemented and meaningful:

```
discover → normalize → plan → execute
```

### Execution behavior

Execution now supports **two explicit modes**:

- **dry-run (default)** – no filesystem mutation
- **apply** – real filesystem mutation via sandboxed execution

There is **no implicit execution**.

Mutation only occurs when you explicitly opt in.



## Contract Boundaries

| Phase | Input | Output |
|------|------|--------|
| discover | package directory | discovery.json |
| normalize | discovery.json | planning_input.json |
| plan | planning_input.json | plan.json |
| execute | plan.json | execution report |

Artifacts are **not interchangeable**.

Examples:

```
plan discovery.json           → fails
execute planning_input.json  → fails
normalize plan.json          → fails
```

The CLI never guesses.



## Discovery Contract

Discovery emits:

- artifacts
- relationships
- summary metadata

Relationships use fixed, schema-locked fields:

```
source
target
type
pattern_id
```

These names are stable.



## Workflow

### 1. Discover

```bash
python -m dita_package_processor discover \
  --package /path/to/dita \
  --output discovery.json
```

Behavior:

- scans files
- builds an inventory
- extracts relationships
- **read-only**



### 2. Normalize

```bash
python -m dita_package_processor normalize \
  --input discovery.json \
  --output planning_input.json
```

Behavior:

- validates structure
- enforces exactly one MAIN map
- validates relationships
- locks schema

Output:

```
planning_input.json
```

This is the **only valid input** for planning.



### 3. Plan

```bash
python -m dita_package_processor plan \
  --input planning_input.json \
  --output plan.json
```

Behavior:

- hydrates a planning contract
- generates deterministic actions
- validates plan schema
- **read-only**



### 4. Execute

Execution consumes a validated plan and produces an **ExecutionReport**.

It requires **explicit path contracts**.

#### Required arguments

- `--plan` – path to plan.json
- `--source-root` – root directory containing source package files
- `--output` – sandbox/output directory

#### Optional arguments

- `--apply` – allow real filesystem mutation  
  (absence = dry-run)
- `--report FILE` – write ExecutionReport JSON
- `--json` – emit execution report to stdout

#### Dry-run (default)

```bash
python -m dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/package \
  --output build
```

Behavior:

- simulates action dispatch
- **does not mutate the filesystem**
- may create the output directory
- produces a deterministic execution report

#### Real execution (filesystem mutation)

```bash
python -m dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/package \
  --output build \
  --apply
```

Behavior:

- executes actions via filesystem executor
- enforces sandbox boundaries
- enforces mutation policy
- records all results in ExecutionReport

There is **no `--dry-run` flag**.

Dry-run is the default.  
Mutation requires `--apply`.



## run — Full Pipeline

Runs the full pipeline:

```
discover → normalize → plan → execute
```

Example:

```bash
python -m dita_package_processor run \
  --package /path/to/dita \
  --output build
```

Behavior:

- performs discovery, normalization, planning
- executes in **dry-run mode by default**
- requires `--apply` for real filesystem mutation
- produces the same artifacts as running each phase manually



## Command Reference

### discover
```
dita_package_processor discover --package PATH --output discovery.json
```

### normalize
```
dita_package_processor normalize --input discovery.json --output planning_input.json
```

### plan
```
dita_package_processor plan --input planning_input.json --output plan.json
```

### execute
```
dita_package_processor execute \
  --plan plan.json \
  --source-root PATH \
  --output DIR \
  [--apply] \
  [--report FILE] \
  [--json]
```

### run
```
dita_package_processor run --package PATH --output DIR [--apply]
```



## Flags

Flags are **per-command**, not global.

Common ones:

| Flag | Meaning |
|------|--------|
| --json | emit JSON output |
| --report | write ExecutionReport to file |
| --apply | allow filesystem mutation |
| --help | help text |



## Guarantees

Across all commands:

- no implicit mutation
- no guessing
- no cwd-relative paths
- no silent fixes
- explicit source root required for execution
- sandboxed filesystem writes only
- every step auditable
- failures are explicit and fatal



## TL;DR

Today:

```
discover → normalize → plan → execute
```

Execution is:

- dry-run by default
- real mutation only with `--apply`
- fully sandboxed
- path-explicit
- policy-enforced

You can now **run the full pipeline on a real DITA package** and either:

- simulate the transformation safely, or
- apply it deliberately, with receipts.