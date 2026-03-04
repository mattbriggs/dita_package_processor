# DITA Package Processor CLI

This document reflects the current CLI implemented in [`dita_package_processor/cli.py`](dita_package_processor/cli.py).

## Invocation

From source:

```bash
python3 -m dita_package_processor <command> [options]
```

If installed as a console script:

```bash
dita_package_processor <command> [options]
```

## Global Options

Available on the root parser:

- `--json`
- `--quiet`
- `--log-level {DEBUG,INFO,WARNING,ERROR}`
- `--version`

Some subcommands also define their own `--json` or `--quiet` flags for command-specific output behavior.

## Commands

### `discover`

Read-only package scan.

```bash
python3 -m dita_package_processor discover \
  --package /path/to/package \
  --output discovery.json \
  --fail-on-invariants
```

Arguments:

- `--package` required
- `--output` optional
- `--json` optional
- `--quiet` optional
- `--fail-on-invariants` optional

Outputs a discovery report and invariant status. No mutation occurs.

### `normalize`

Convert a discovery report into a `PlanningInput` contract.

```bash
python3 -m dita_package_processor normalize \
  --input discovery.json \
  --output planning_input.json
```

Arguments:

- `--input` required
- `--output` required

### `plan`

Generate a deterministic plan from `planning_input.json`.

```bash
python3 -m dita_package_processor plan \
  --input planning_input.json \
  --output plan.json
```

Arguments:

- `--input` required
- `--output` required
- `--schema` optional

### `execute`

Execute a validated plan against a declared source root and output root.

```bash
python3 -m dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/package \
  --output ./build
```

Apply real changes:

```bash
python3 -m dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/package \
  --output ./build \
  --apply \
  --report ./build/execution-report.json
```

Arguments:

- `--plan` required
- `--output` required
- `--source-root` required
- `--report` optional
- `--json` optional
- `--apply` optional

Dry-run is the default when `--apply` is omitted.

### `run`

Run the orchestrated pipeline from package discovery through execution.

```bash
python3 -m dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc
```

Applied run:

```bash
python3 -m dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc \
  --target ./build \
  --apply
```

Arguments:

- `--package` required
- `--docx-stem` required
- `--definition-map` optional
- `--definition-navtitle` optional
- `--target` optional, but required when `--apply` is used
- `--apply` optional
- `--report` optional

### `plugin`

Inspect and validate the plugin stack.

#### `plugin list`

```bash
python3 -m dita_package_processor plugin list
python3 -m dita_package_processor plugin list --json
```

#### `plugin info`

```bash
python3 -m dita_package_processor plugin info dita_package_processor.core
python3 -m dita_package_processor plugin info dita_package_processor.core --json
```

#### `plugin validate`

```bash
python3 -m dita_package_processor plugin validate /path/to/plugin-package
```

`plugin validate` expects a directory containing a `pyproject.toml` with a `dita_package_processor.plugins` entry-point declaration.

### `docs`

Emit CLI help text, optionally to a file.

```bash
python3 -m dita_package_processor docs
python3 -m dita_package_processor docs --output cli-help.txt
```

### `completion`

Emit shell completion code when `argcomplete` is installed.

```bash
python3 -m dita_package_processor completion --shell zsh
```

Supported shells:

- `bash`
- `zsh`
- `fish`

## Current Mental Model

- `discover` observes the package.
- `normalize` converts discovery output into the planning contract.
- `plan` emits ordered action data.
- `execute` consumes an existing plan.
- `run` orchestrates the end-to-end path.
- `plugin` inspects the extension layer behind discovery, planning, and execution.

## Notes

- `run` uses `--target` for the output root.
- `execute` uses `--output` and also requires `--source-root`.
- The CLI imports the discovery stack at startup, so source-based usage requires the runtime dependencies listed in `pyproject.toml` and `requirements.txt`.
