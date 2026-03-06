# Getting Started

This guide matches the current CLI and plugin-aware pipeline in this repository.

## Prerequisites

- Python 3.10+
- A virtual environment
- Runtime dependencies from `requirements.txt`

## Install From Source

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

If you skip dependency installation, even `python3 -m dita_package_processor --help` can fail because the root CLI imports discovery modules that depend on packages such as `lxml`.

## First Run

Dry-run the full pipeline:

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

## Stepwise Workflow

Generate each artifact explicitly when you want inspection points between phases.

Discovery:

```bash
python3 -m dita_package_processor discover \
  --package /path/to/package \
  --output discovery.json
```

Normalization:

```bash
python3 -m dita_package_processor normalize \
  --input discovery.json \
  --output planning_input.json
```

Planning:

```bash
python3 -m dita_package_processor plan \
  --input planning_input.json \
  --output plan.json
```

Execution:

```bash
python3 -m dita_package_processor execute \
  --plan plan.json \
  --source-root /path/to/package \
  --output ./build \
  --report ./build/execution-report.json
```

## Plugin Awareness

The current repo is plugin-based even for built-in behavior.

- discovery patterns come from the plugin registry
- planner actions are emitted per plugin
- execution handlers are registered per plugin

Inspect the loaded stack:

```bash
python3 -m dita_package_processor plugin list
python3 -m dita_package_processor plugin info dita_package_processor.core
```

Validate a local plugin package before installation:

```bash
python3 -m dita_package_processor plugin validate /path/to/plugin
```

## Next Reading

- [Extensions](extensions.md)
- [Extension Guide](extensions-guide.md)
- [Execution Report Guide](execution-report.md)
- [CLI API Reference](api-ref-cli.md)
- [Plugin API Reference](api-ref-plugins.md)
