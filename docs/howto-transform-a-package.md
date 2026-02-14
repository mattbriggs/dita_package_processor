# Transform a DITA Package

The **DITA Package Processor** transforms a source DITA package into a **materialized target package** using a strict, deterministic pipeline.

The pipeline consists of:

- **Discovery** – observe and classify the source package  
- **Normalize** – enforce structural invariants  
- **Planning** – generate an explicit execution plan  
- **Execution** – materialize content into a target directory  

Filesystem mutation only occurs when explicitly enabled with `--apply`.

There is no in-place mutation.  
There is no guessing.  
There is no implicit execution.

---

## The one command that matters

To transform a source DITA package into a **materialized target package**, run:

```bash
dita_package_processor run \
  --package /path/to/source-dita-package \
  --source-root /path/to/source-dita-package \
  --output /path/to/target-package \
  --apply
```

That’s the canonical invocation.

No extra flags.  
No hidden defaults.  
No accidental overwrites.

---

## What each part actually does (no lies)

### `--package`

This identifies the **logical package root** for discovery and planning.

It must contain:

- `index.ditamap`
- a resolvable main map
- well-formed XML

Nothing in this directory is mutated.

Ever.

---

### `--source-root`

This is the **filesystem truth** used during execution.

Key rule (the one that bit you):

> All paths in the execution plan are resolved **relative to `--source-root`**.

If this is wrong, execution will “work” but find nothing.

This flag is mandatory for `execute` and required for `run` once execution is involved.

---

### `--output`

This is the **target directory** where the processed package is written.

Rules enforced by the CLI:

- Required when `--apply` is present  
- Must be writable  
- Is created if missing  
- Is never deleted implicitly  
- Is never allowed to overlap the source tree  

There is **no in-place mutation**.

This is intentional and non-negotiable.

---

### `--apply`

This flag explicitly authorizes filesystem mutation.

Without it:

- discovery runs  
- normalization runs  
- planning runs  
- execution runs in **dry-run mode only**  
- no files are written  

With it:

- execution switches to the filesystem executor  
- actions are applied deterministically  
- files are written into `--output`  
- results are recorded in an execution report  

No `--apply` means no writes. Always.

---

## What actually happens internally (the real pipeline)

When you run the command above, the pipeline is:

```
Discovery
  ↓
Normalize
  ↓
Planning
  ↓
Execution
    • sandboxed filesystem access
    • explicit source-root resolution
    • deterministic action dispatch
```

Important clarifications:

- There is **no separate materialization phase** anymore
- Layout resolution is encoded directly in the plan
- Collision prevention is enforced by:
  - explicit target paths
  - sandbox validation
  - executor policy checks

Execution **never invents paths**.  
It only executes what the plan describes.

---

## What you get at the end

After a successful run with `--apply`, you have:

- A fully materialized DITA package in `--output`
- Deterministic directory layout
- Explicitly copied maps, topics, and media
- Normalized map hierarchy
- Optional semantic refactors applied
- A package that opens cleanly in Oxygen

Example:

```bash
oxygen /path/to/target-package/<main-map>.ditamap
```

No cleanup required.  
No manual repair.

---

## Dry run (strongly recommended first)

```bash
dita_package_processor run \
  --package ./source \
  --source-root ./source \
  --output ./out
```

This:

- executes the full pipeline
- simulates execution
- validates every action
- proves path resolution
- writes **no files**

If this fails, applying would have failed too.

---

## Writing an execution report

```bash
dita_package_processor run \
  --package ./source \
  --source-root ./source \
  --output ./out \
  --apply \
  --report execution_report.json
```

The report records:

- every action
- execution status
- handler identity
- dry-run vs applied state
- failures and skips

It is a forensic artifact.  
You can diff it, archive it, or feed it into CI.

---

## The important meta-point

You did **not** build:

- a script
- a copier
- a batch hack

You built:

- a **compiler-style pipeline**
- with explicit contracts
- a validated plan
- a sandboxed executor
- and a boring execution phase

The CLI feels strict because it is.

Strict is what makes this safe at scale.
