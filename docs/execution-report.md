# Execution Report Guide

This guide shows how to generate `execution-report.json` and how to use it to debug runs quickly.

## Generate a report

Run the full pipeline and write a report:

```bash
python3 -m dita_package_processor run \
  --package /path/to/package \
  --docx-stem OutputDoc \
  --target ./build \
  --apply \
  --report ./build/execution-report.json
```

Execute an existing plan and write a report:

```bash
python3 -m dita_package_processor execute \
  --plan ./build/plan.json \
  --source-root /path/to/package \
  --output ./build \
  --apply \
  --report ./build/execution-report.json
```

Use dry-run (no writes) with a report:

```bash
python3 -m dita_package_processor execute \
  --plan ./build/plan.json \
  --source-root /path/to/package \
  --output ./build \
  --report ./build/execution-report.json
```

## Top-level fields

`execution-report.json` includes:

- `execution_id`
- `generated_at`
- `started_at`
- `finished_at`
- `duration_ms`
- `dry_run`
- `summary`
- `discovery`
- `results`

`summary` is aggregate action status counts.

`discovery` includes:

- `maps`
- `topics`
- `media`
- `missing_references`
- `external_references`

`results` is one entry per action with:

- `action_id`
- `status`
- `handler`
- `dry_run`
- `message`
- optional `error`
- optional `error_type`
- optional `metadata`

## Quick inspection commands

Show high-level result:

```bash
jq '{execution_id, dry_run, summary, discovery}' ./build/execution-report.json
```

Show execution timing:

```bash
jq '{started_at, finished_at, duration_ms}' ./build/execution-report.json
```

Show only failed actions:

```bash
jq '.results[] | select(.status == "failed") | {action_id, handler, error_type, error, message}' ./build/execution-report.json
```

Show media copy source and target paths:

```bash
jq '.results[] | select(.metadata.source_path? != null) | {action_id, status, source: .metadata.source_path, target: .metadata.target_path}' ./build/execution-report.json
```

## Read the report in order

1. Check `dry_run`.
2. Check `summary.failed`.
3. Check `duration_ms` and timestamps.
4. Check `discovery` counts for expected package size.
5. Inspect failed `results` entries.

## CI usage

Fail CI if any action failed:

```bash
jq -e '.summary.failed == 0' ./build/execution-report.json > /dev/null
```

Fail CI if discovery looked wrong (example: no maps):

```bash
jq -e '.discovery.maps > 0' ./build/execution-report.json > /dev/null
```
