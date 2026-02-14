# DITA Package Processor

The **DITA Package Processor** is a deterministic execution platform for  
analyzing, planning, and applying transformations to **DITA 1.3** packages.

It is designed for hostile, vendor-generated, and legacy corpora where  
ambiguity, implicit behavior, and hidden side effects are unacceptable.

This is **not** an interactive tool.  
This is **not** an inference engine.  
This is **not** a self-healing pipeline.

It does exactly what you tell it to do, in the order you tell it to do it,  
and it records everything it does as structured, auditable data.

If something is ambiguous, invalid, or underspecified, it fails loudly  
rather than guessing.



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

Full CLI documentation lives in  
**[README-CLI.md](README-CLI.md)**.



## Design Philosophy

The processor is built on non-negotiable constraints:

- **Determinism over cleverness**  
  The same input always produces the same output.

- **Explicit structure over heuristics**  
  All behavior is encoded in rules, schemas, and plans.

- **Read-only analysis before mutation**  
  Discovery and planning never touch the filesystem.

- **Auditable plans before execution**  
  All filesystem mutation must originate from an explicit, serialized plan.

- **Execution is observable through data, not logs**  
  Results are captured in immutable execution reports.

- **Idempotence everywhere**  
  Re-running the same plan never causes accidental duplication or damage.

If you want inference, adaptive behavior, or “best guess” fixes, this is the  
wrong tool.



## System Status

The planning, execution, and materialization subsystems are now **infrastructure-grade**.

The following contracts are stable and enforced by tests:

- Planning, execution, and materialization are fully separated
- Plans are JSON-schema validated artifacts
- Plans are side-effect free
- Executors preserve action ordering
- Execution produces structured **ExecutionReport** objects
- Materialization operates only on execution artifacts
- Reports are complete forensic records, not log output
- Dry-run is the default; mutation requires explicit consent
- All handlers are:
  - deterministic  
  - idempotent  
  - dry-run safe  
  - auditable  

Execution is no longer “script-like.”  
It is a transaction layer.



## Architecture Overview

The system is explicitly layered:

```
Discovery → Planning → Execution → Materialization
```

Each layer is independently invocable and independently testable.

No layer leaks into the next.  
No layer performs work outside its responsibility.



## Documentation

Documentation is treated as a **first-class build artifact**, not prose.

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

All JSON Schemas in the repository are documented automatically.

Run:

```bash
python tools/generate_schema_docs.py
```

This will:

- scan the repository for `*.schema.json`
- generate Markdown documentation per schema
- write output to:

```
docs/reference/schemas/
```

These files are **inputs** to MkDocs.  
They are not hand-edited.



### 2. Generate Known Patterns Documentation

Declarative discovery knowledge lives in:

```
dita_package_processor/knowledge/known_patterns.yaml
```

To generate documentation for this file, run:

```bash
python tools/generate_known_patterns_docs.py
```

This will:

- parse `known_patterns.yaml`
- produce human-readable, auditable documentation
- write output to:

```
docs/reference/knowledge/known-patterns.md
```

This ensures that **pattern logic is reviewable without reading code**.



### 3. Serve the Documentation Locally

Once generated artifacts are up to date:

```bash
mkdocs serve
```

Then open:

```
http://127.0.0.1:8000/
```



### Documentation Update Workflow (Canonical)

When making architectural or behavioral changes, the expected workflow is:

```bash
# 1. Update code / schemas / patterns
# 2. Regenerate derived documentation
python tools/generate_schema_docs.py
python tools/generate_known_patterns_docs.py

# 3. Validate documentation build
mkdocs serve
```

If generated documentation is out of date, that is considered a **build failure**, not a cosmetic issue.



## Tests

Tests use **pytest** and operate on real filesystem fixtures.

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

Tests assert **behavioral contracts**, not implementation details:

- Deterministic planning
- Schema validity
- Execution observability
- Order preservation
- Dry-run guarantees
- Idempotence
- Mutation safety
- Forensic reporting
- Media discovery correctness
- Media planning exclusion guarantees



## What This README Explains

This README defines the **architecture contract**:

- what the system guarantees
- what each layer is allowed to do
- how mutation is controlled
- how execution and materialization are observed
- how documentation is generated and kept in sync



## What This README Does Not Explain

- CLI workflows  
- Subcommands and flags  
- Individual JSON schema fields  
- Execution plan contents  
- Discovery invariants  

Those live in the **[CLI Usage README](README-CLI.md)**.
