# DITA Package Processor

The DITA Package Processor is a deterministic toolchain for inspecting DITA packages, normalizing them into planning contracts, generating execution plans, and applying those plans through bounded executors.

It is organized around explicit stages:

```text
discover -> normalize -> plan -> execute
```

The `run` command orchestrates those stages for the common case. Dry-run is the default. Real filesystem mutation only happens when `--apply` is set.

## Current Capabilities

- Discovery of maps, topics, media, relationships, and classification evidence
- Contract normalization from discovery output into `PlanningInput`
- Deterministic plan generation with schema validation
- Dry-run and filesystem-backed execution modes
- Materialization preflight and execution report emission
- Plugin-based extension points for discovery patterns, planning action emission, and execution handlers

## Installation

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

The package requires Python 3.10+.

## Quick Start

Run the full pipeline safely:

```bash
python3 -m dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc
```

Apply changes explicitly:

```bash
python3 -m dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc \
  --target ./build \
  --apply \
  --report ./build/execution-report.json
```

Execute an existing plan directly:

```bash
python3 -m dita_package_processor execute \
  --plan ./plan.json \
  --source-root /path/to/package \
  --output ./build \
  --apply
```

## CLI Surface

Current top-level commands:

- `discover`
- `normalize`
- `plan`
- `execute`
- `run`
- `plugin`
- `docs`
- `completion`

The plugin command group provides:

- `plugin list`
- `plugin info <name>`
- `plugin validate <path>`

See [README-CLI.md](README-CLI.md) for command details.

## Plugin System

Plugins are now the supported extension surface.

Each plugin can contribute:

- discovery `Pattern` definitions
- planning-time `emit_actions(...)` logic
- execution handler classes

The built-in behavior is packaged as `CorePlugin`, and third-party plugins are loaded through the Python entry point group `dita_package_processor.plugins`.

## Documentation

Project docs live under [`docs/`](docs) and are wired through [`mkdocs.yml`](mkdocs.yml).

Important entry points:

- [`docs/index.md`](docs/index.md)
- [`docs/getting-started.md`](docs/getting-started.md)
- [`docs/extensions.md`](docs/extensions.md)
- [`docs/extensions-guide.md`](docs/extensions-guide.md)
- [`docs/api-ref-cli.md`](docs/api-ref-cli.md)
- [`docs/api-ref-plugins.md`](docs/api-ref-plugins.md)

## Development

Run the test suite:

```bash
pytest -q
```

Useful repo utilities:

- `tools/scaffold_plugin.py` to scaffold a plugin package
- `tools/generate_schema_docs.py` to refresh schema reference docs
- `tools/generate_pattern_docs.py` to refresh pattern reference docs

## Constraints

- Discovery is read-only.
- Planning does not mutate files.
- Execution is explicit and bounded to declared roots.
- Plans and reports are the contract, not log output.
- Ambiguity should fail loudly rather than being guessed through.
