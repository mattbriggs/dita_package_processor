# Getting Started

This guide walks you through running the **DITA Package Processor** from source on macOS or Linux using Python 3.10+.

The processor is a **deterministic, contract-driven batch tool**.  
There is no interactive mode, no inference, and no “best guess” behavior.

What happens is exactly what the **discovery results, plan, and executor** specify.  
Nothing more. Nothing less.

---

## Prerequisites

- Python **3.10 or newer**
- macOS or Linux  
  (Windows may work but is not actively supported)
- A valid **DITA 1.3 package**, meaning:
  - One or more `.ditamap` files
  - Topics and media reachable via references
  - Well-formed XML  
    (recoverable XML may be tolerated during discovery; invalid XML is not)

There is **no requirement** that the package already be “clean” or well-structured.  
That is the point of the tool.

---

## Clone and Set Up the Project

Clone the repository and create a virtual environment:

```bash
git clone <repo-url>
cd dita_package_processor

python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

For development or local iteration:

```bash
pip install -e .
```

There is no build step.  
This is not a framework and does not generate code at install time.

---

## Mental Model (Important)

The processor runs a **fixed pipeline**:

```
discovery → planning → execution
```

Each phase:

- has a single responsibility
- produces a durable artifact
- consumes only the artifact from the previous phase
- refuses invalid input

You do **not** configure execution logic in `pyproject.toml`.  
You design behavior by:
1. Discovering what exists  
2. Planning explicit actions  
3. Executing those actions with an executor  

---

## Run the Full Pipeline (Recommended)

The easiest and safest way to start is with the **`run`** command.

### Dry-run (default, safe)

```bash
python -m dita_package_processor run \
  --package /path/to/dita/package \
  --output build
```

This performs:

- discovery
- planning
- dry-run execution

**No filesystem mutation occurs.**

You will get:
- discovery artifacts
- a validated plan
- an execution report describing what *would* happen

---

### Apply Changes Explicitly

When you are satisfied with the plan:

```bash
python -m dita_package_processor run \
  --package /path/to/dita/package \
  --output build \
  --apply
```

Key guarantees:

- Mutation is explicit
- All writes are sandboxed to `--output`
- All reads are resolved from the declared source package
- Every action is recorded in the execution report

---

## Execute a Plan Directly (Advanced)

You can also execute a plan explicitly.

This is useful for:
- CI pipelines
- reviewing or modifying plans
- replaying execution deterministically

```bash
python -m dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/original/package \
  --output build \
  --apply
```

**Important:**  
`--source-root` is required because plan paths are **relative and intentional**.  
The executor will not guess where files live.

If `--apply` is omitted, execution is dry-run only.

---

## Configuration (`pyproject.toml`)

Some optional behavior is controlled via `pyproject.toml` under:

```toml
[tool.dita_package_processor]
```

Configuration controls:
- optional planning behaviors
- naming conventions
- glossary handling
- logging

Configuration **never overrides structural validation**.  
It only enables or disables *safe, predefined behavior*.

CLI precedence is always:

```
CLI arguments > pyproject.toml > defaults
```

---

## Verify the Result

After a successful **applied** run:

- Output appears only under `--output`
- Source content is never mutated
- Files are copied, renamed, or rewritten only if explicitly planned
- Execution results are recorded per action

If the output directory is empty, that means either:
- execution was dry-run, or
- the plan contained no mutating actions

Both outcomes are intentional and observable in the execution report.

---

## Troubleshooting

- Use `--json` on `execute` to inspect execution reports directly
- Review the plan before applying it
- If files are missing, check:
  - `--source-root` correctness
  - relative paths in the plan
  - whether `--apply` was used

Failures are explicit.  
There are no silent fallbacks.

---

## Next Steps

- Read **Design** to understand architectural constraints
- Read **Planning** to learn how actions are generated
- Read **Execution** to understand executors and safety rules
- Extend the system by adding new planners or handlers, not shortcuts

---

## Summary

Getting started is intentionally boring:

1. Point at a real DITA package
2. Run discovery and planning
3. Inspect the plan
4. Apply execution deliberately

This tool exists to make large, messy DITA packages **safe to transform**.  
If you want speed or magic, this is the wrong tool.  
If you want correctness you can defend later, you’re in the right place.