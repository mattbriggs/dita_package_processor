# Execution Report Contract

Deterministic execution report capturing the outcome of executing a validated plan. This report is authoritative, auditable, and suitable for both human review and machine analysis.

## Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `execution_id` | string | yes | Unique identifier for this execution run. Used to correlate reports, logs, and downstream artifacts. |
| `generated_at` | string | yes | ISO-8601 timestamp indicating when the execution report was generated. |
| `dry_run` | boolean | yes | Indicates whether this execution was performed in dry-run mode, meaning no filesystem mutation occurred. |
| `results` | array | yes | Ordered list of per-action execution results, one entry for each action evaluated by the executor. |
| `summary` | object | yes | Aggregate counts summarizing the execution outcomes across all actions. |