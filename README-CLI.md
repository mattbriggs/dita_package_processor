# DITA Package Processor CLI  
Deterministic Pipeline Execution for DITA Packages

The **DITA Package Processor CLI** is a strict, contract-driven interface to a deterministic processing engine.

It exists for environments where:

- package structure cannot be trusted  
- assumptions must be proven before action  
- transformations must be explicit and reviewable  
- mutation must be auditable  

This CLI does not optimize for convenience.  
It optimizes for **correctness, determinism, and safety**.

Observe first. Decide explicitly. Then act.





# How to Run

From source:

```bash
python -m dita_package_processor <command> [options]
```

Editable install:

```bash
pip install -e .
dita_package_processor <command> [options]
```

Behavior is identical.





# Mental Model

The CLI exposes a **deterministic processing pipeline**:

```
Discovery → Planning → Execution → Materialization
```

For most users, this is invoked through a single command:

```
run
```

You may also execute a previously generated plan.

Each phase:

- is deterministic  
- is schema-validated  
- fails loudly on ambiguity  
- never guesses  
- never mutates implicitly  





# Primary Command: `run`

The `run` command executes the full pipeline:

```
discover → normalize → plan → execute
```

## Minimal Example (Dry-Run)

```bash
dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc
```

Behavior:

- performs read-only discovery  
- generates a deterministic plan  
- executes in **dry-run mode**  
- produces an ExecutionReport  

No filesystem mutation occurs.



## Real Execution (Mutation Enabled)

```bash
dita_package_processor run \
  --package /path/to/package \
  --target /path/to/output \
  --docx-stem OutputDoc \
  --apply
```

Behavior:

- performs discovery and planning  
- executes via filesystem executor  
- mutates only inside `--target`  
- enforces sandbox boundaries  
- produces an ExecutionReport  

Mutation requires both:

- `--apply`
- `--target`

There is no implicit mutation.





# Executing an Existing Plan

You may execute a previously generated plan.

```bash
dita_package_processor execute \
  --plan plan.json \
  --target /path/to/output
```

Dry-run is default.

To allow mutation:

```bash
dita_package_processor execute \
  --plan plan.json \
  --target /path/to/output \
  --apply
```

Behavior:

- skips discovery  
- skips planning  
- loads and validates the plan  
- executes deterministically  





# Execution Modes

| Mode | Default | Filesystem Mutation |
|------|--------|--------------------|
| Dry-run | Yes | No |
| Apply | No | Yes |

There is no `--dry-run` flag.  
Dry-run is the default behavior.

Real mutation requires `--apply`.





# Required Arguments

## run

| Argument | Required | Description |
|----------|----------|------------|
| `--package` | Yes | Path to DITA package directory |
| `--docx-stem` | Yes | Base name for generated artifacts |
| `--target` | Required with `--apply` | Output directory |
| `--apply` | Optional | Enable filesystem mutation |
| `--report FILE` | Optional | Write ExecutionReport JSON |

## execute

| Argument | Required | Description |
|----------|----------|------------|
| `--plan` | Yes | Path to plan.json |
| `--target` | Yes | Output directory |
| `--apply` | Optional | Enable filesystem mutation |
| `--report FILE` | Optional | Write ExecutionReport JSON |
| `--json` | Optional | Emit report to stdout |





# What Happens Internally During `run`

1. **Discovery**
   - Scans package
   - Extracts artifacts
   - Extracts relationships
   - Classifies maps and topics
   - Read-only

2. **Normalization**
   - Converts discovery output into PlanningInput
   - Enforces exactly one MAIN map
   - Validates relationships
   - Schema-validates contract

3. **Planning**
   - Generates deterministic plan actions
   - Sorts artifacts
   - Validates plan schema
   - No filesystem interaction

4. **Execution**
   - Dispatches actions
   - Uses noop executor (dry-run) or filesystem executor
   - Preserves order
   - Produces ExecutionReport

5. **Materialization**
   - Finalizes output artifacts
   - Writes report if requested





# Execution Report

Every execution produces an `ExecutionReport`.

The report includes:

- execution_id  
- dry_run flag  
- per-action results  
- status summary  
- handler information  

It is the authoritative record of what occurred.

Logs are not the contract.  
The report is.





# Contract Guarantees

Across all commands:

- No implicit mutation  
- No heuristic inference  
- No silent fixes  
- No cwd-relative guessing  
- No execution without explicit path contracts  
- Sandbox-only filesystem writes  
- Deterministic action ordering  
- Schema-validated boundaries  
- Fail-fast behavior  





# Common Examples

## Dry-run full pipeline

```bash
dita_package_processor run \
  --package ./package \
  --docx-stem OutputDoc
```

## Real execution

```bash
dita_package_processor run \
  --package ./package \
  --target ./out \
  --docx-stem OutputDoc \
  --apply
```

## Execute existing plan safely

```bash
dita_package_processor execute \
  --plan plan.json \
  --target ./out
```

## Execute existing plan with mutation

```bash
dita_package_processor execute \
  --plan plan.json \
  --target ./out \
  --apply
```





# What This CLI Is Not

It is not:

- interactive  
- adaptive  
- heuristic  
- self-healing  
- forgiving  

If input is invalid, it fails.

That is intentional.