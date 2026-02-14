# Planning Input Contract

Schema-locked input contract for the planning subsystem. Planning MUST consume only this shape. Discovery output is illegal downstream.

## Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `contract_version` | string | yes | Fixed contract version. Any other value is invalid. |
| `main_map` | string | yes | Path of the unique MAIN map. Must match exactly one artifact.path where artifact_type == 'map' and classification == 'MAIN'. |
| `artifacts` | array | yes | All artifacts participating in planning. |
| `relationships` | array | yes | All relationships planning is allowed to reason about. |