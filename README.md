# DITA Package Processor

The **DITA Package Processor** is a deterministic execution platform for  
analyzing, planning, and applying transformations to **DITA 1.3** packages.

It is designed for unpredictable, vendor-generated, or legacy corpora where  
ambiguity, implicit behavior, and hidden side effects are unacceptable.

This is **not** an interactive tool.  
This is **not** an inference engine.  
This is **not** a self-healing pipeline.

It does exactly what you tell it to do, in the order you tell it to do it,  
and it records everything it does as structured, auditable data.

If something is ambiguous, invalid, or underspecified, it fails rather than guessing.





## When to Use This Tool

Use this processor when:

- You need deterministic restructuring of DITA packages  
- You require auditable filesystem mutation  
- You operate in regulated or high-risk environments  
- You cannot tolerate heuristic classification or implicit inference  

Do not use this processor when:

- You want adaptive or “best guess” behavior  
- You expect automatic repair of malformed content  
- You need interactive editing workflows  





## System Guarantee

Given the same DITA package and the same execution parameters, the processor guarantees:

- Identical planning output  
- Identical execution artifacts  
- Identical execution reports  

No hidden state.  
No implicit mutation.  
No heuristic branching.  





## Quick Start (Minimal Example)

```bash
dita_package_processor run \
  --package ./package \
  --target ./out \
  --docx-stem OutputDoc
```

This performs:

1. **Discovery** (read-only analysis)  
2. **Planning** (explicit plan generation)  
3. **Execution** (deterministic action dispatch)  
4. **Materialization** (artifact finalization)  

Mutation requires `--apply`.  
Dry-run is the default.





## Accessing the CLI

After setup:

```bash
source .venv/bin/activate
python -m dita_package_processor -h
```

Or if installed editable:

```bash
dita_package_processor -h
```

Full CLI documentation lives in:

**[README-CLI.md](README-CLI.md)**





## Setup

Create a virtual environment, install the package in editable mode, and verify the installation.

### Installation (From Source)

#### 1. Create and activate a virtual environment

From the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Ensure Python 3.10+.

#### 2. Install in editable mode

```bash
pip install -r requirements.txt
pip install -e .
```

Editable mode (`-e`) means:

- The CLI is available immediately  
- Code changes reflect without reinstalling  
- You are working directly against the source tree  

#### 3. Verify installation

```bash
dita_package_processor --help
```

If usage information prints without error, installation is successful.





## Run the Test Suite

Before trusting the system with real content:

```bash
pytest -q
```

The test suite covers:

- Discovery contracts  
- Planning invariants  
- Plan validation  
- Execution behavior  
- End-to-end integration  

A clean pass indicates structural integrity.





## Design Philosophy

The processor is built on strict constraints:

- **Determinism over cleverness**  
  The same input always produces the same output.

- **Explicit structure over heuristics**  
  Behavior is encoded in rules, schemas, and plans.

- **Read-only analysis before mutation**  
  Discovery and planning never touch the filesystem.

- **Auditable plans before execution**  
  All mutation originates from an explicit, serialized plan.

- **Execution is observable through data, not logs**  
  Results are captured in immutable execution reports.

- **Idempotence everywhere**  
  Re-running the same plan does not cause duplication or damage.

If you want adaptive behavior or inference-driven processing, this is the wrong tool.





## Architecture Overview

The system is explicitly layered:

```
Discovery → Planning → Execution → Materialization
```

Each layer is independently invocable and independently testable.

No layer performs work outside its responsibility.  
No layer implicitly mutates upstream state.





## System Status

Planning, execution, and materialization are contract-validated and test-enforced.

The following guarantees are stable:

- Discovery, planning, execution, and materialization are fully separated  
- Plans are JSON Schema validated  
- Plans are side-effect free  
- Executors preserve action ordering  
- Execution produces structured `ExecutionReport` objects  
- Dry-run is default; mutation requires explicit consent  
- All handlers are:
  - deterministic  
  - idempotent  
  - dry-run safe  
  - auditable  

Execution is a transaction boundary, not a script.





## Documentation

Documentation is treated as a build artifact.

The documentation site is generated from:

- Python docstrings (via `mkdocstrings`)  
- JSON Schemas (auto-generated)  
- Declarative YAML knowledge files (auto-generated)  
- Markdown architecture guides  

### Documentation Toolchain

- **MkDocs** for site generation  
- **mkdocstrings** for API reference  
- Custom generators for schema and knowledge documentation  



### 1. Generate JSON Schema Documentation

```bash
python tools/generate_schema_docs.py
```

This scans for `*.schema.json` files and generates documentation into:

```
docs/reference/schemas/
```

These files are generated artifacts and must not be manually edited.



### 2. Generate Known Patterns Documentation

Declarative discovery knowledge lives in:

```
dita_package_processor/knowledge/known_patterns.yaml
```

Generate documentation:

```bash
python tools/generate_known_patterns_docs.py
```

Output is written to:

```
docs/reference/knowledge/known-patterns.md
```



### 3. Serve Documentation Locally

```bash
mkdocs serve
```

Open:

```
http://127.0.0.1:8000/
```



### Documentation Update Workflow

When making behavioral changes:

```bash
# 1. Update code / schemas / patterns
# 2. Regenerate documentation
python tools/generate_schema_docs.py
python tools/generate_known_patterns_docs.py

# 3. Validate site build
mkdocs serve
```

Out-of-date generated documentation is considered a build failure.





## Tests

Run all tests:

```bash
pytest
```

By subsystem:

```bash
pytest tests/discovery
pytest tests/planning
pytest tests/execution
pytest tests/materialization
pytest tests/cli
pytest tests/pipeline
pytest tests/integration
```

Tests assert behavioral contracts:

- Deterministic planning  
- Schema validity  
- Execution observability  
- Order preservation  
- Dry-run guarantees  
- Idempotence  
- Mutation safety  
- Forensic reporting  
- Media exclusion guarantees  





## What This README Defines

This document establishes the architectural contract:

- What the system guarantees  
- How mutation is controlled  
- How execution is observed  
- How documentation is generated and validated  



## What This README Does Not Define

- CLI flag details  
- Individual JSON schema fields  
- Execution plan structure  
- Discovery rule specifics  

Those are documented in:

**[README-CLI.md](README-CLI.md)**



This version keeps your spine. It just breathes a little easier and onboards faster.