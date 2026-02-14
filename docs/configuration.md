# Configuration (`pyproject.toml`)

The DITA Package Processor is configured via **`pyproject.toml`** under the
`[tool.dita_package_processor]` namespace.

Configuration controls **what the processor does at runtime**.
If a step is not listed, it does not run.

There is no implicit behavior.

---

## Configuration Location

Place `pyproject.toml` at the project root:

```
dita_package_processor/
├── pyproject.toml
├── dita_package_processor/
│   └── cli.py
```

The processor reads configuration automatically from this file unless
overridden by CLI arguments.

---

## Configuration Namespace

All processor configuration lives under:

```toml
[tool.dita_package_processor]
```

Nothing outside this namespace is read or interpreted by the processor.

---

## Configuration Sections

### `[tool.dita_package_processor.package]`

Defines the input package and output naming.

```toml
[tool.dita_package_processor.package]
root_dir = "/absolute/or/relative/path/to/dita/package"
docx_stem = "OutputDoc"
```

**Keys**

- `root_dir` (str, required)  
  Path to the root of the DITA package.  
  Must contain `index.ditamap`.

- `docx_stem` (str, required)  
  Filename stem used when renaming the main DITA map.  
  Example: `OutputDoc` → `OutputDoc.ditamap`

---

### `[tool.dita_package_processor.pipeline]`

Defines the ordered execution pipeline.

```toml
[tool.dita_package_processor.pipeline]
steps = [
  "remove-index-map",
  "rename-main-map",
  "process-maps",
  "refactor-glossary",
]
```

**Keys**

- `steps` (list[str], required)  
  Ordered list of processing steps.

**Rules**

- Execution order is **explicit**
- Steps not listed do not run
- Steps are executed exactly once, in order
- Steps do not call each other

This is a pipeline, not a workflow engine.

---

### `[tool.dita_package_processor.definition]` (optional)

Configures glossary refactoring.

```toml
[tool.dita_package_processor.definition]
map = "Definitions.ditamap"
navtitle = "Definition topic"
```

**Keys**

- `map` (str, required if section present)  
  Definition map filename, relative to the package root.

- `navtitle` (str, optional)  
  Navtitle used to locate the definition node.  
  Defaults to `"Definition topic"`.

**Behavior**

- If this section is omitted, glossary refactoring is skipped.
- If the map is missing, the step logs a warning and continues.
- If the navtitle is not found, the step logs a warning and continues.

Glossary refactoring is **optional by design**.

---

### `[tool.dita_package_processor.logging]`

Controls logging verbosity.

```toml
[tool.dita_package_processor.logging]
level = "INFO"
```

**Keys**

- `level` (str)  
  One of: `DEBUG`, `INFO`, `WARNING`, `ERROR`

There is no silent mode.

---

### `[tool.dita_package_processor.extensions]` (namespaced)

Extensions must explicitly opt in under their own namespace.

```toml
[tool.dita_package_processor.extensions.regex_cleanup]
enabled = false
patterns = [
  { find = "\\s+", replace = " " },
  { find = "TODO:", replace = "" },
]
```

**Rules**

- Core steps must not depend on extension configuration
- Extensions must not mutate core behavior implicitly
- Each extension owns its namespace

Extensions are additive, not magical.

---

## CLI Overrides

Configuration values may be overridden via the CLI for one-off runs.

Example:

```bash
dita_package_processor \
  -i /path/to/package \
  -o /path/to/output \
  -l DEBUG
```

**Precedence Order**

```
CLI arguments > pyproject.toml > defaults
```

CLI overrides do **not** modify `pyproject.toml`.

---

## Rules of Thumb

- Configuration is explicit or it does not exist
- Pipelines do exactly what they say
- Optional steps fail soft, required steps fail hard
- New behavior should be added as a new step, not a flag
- If you want inference, this is the wrong tool

---

## Summary

`pyproject.toml` defines the processor’s behavior.
The CLI may override it.
Nothing else is consulted.

This is intentional.