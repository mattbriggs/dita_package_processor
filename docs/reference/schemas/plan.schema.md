# DITA Package Processing Plan

Deterministic execution plan derived from discovery output. This document defines exactly what actions will be evaluated by the execution layer, in what form, and for what reason.

## Properties

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `plan_version` | integer | yes | Version identifier for the plan schema. This value is frozen to guarantee forward and backward compatibility. |
| `generated_at` | string | yes | ISO-8601 timestamp indicating when this plan was generated. |
| `source_discovery` | object | yes | Provenance information describing the discovery artifact from which this plan was derived. |
| `intent` | object | yes | High-level intent describing the purpose of this plan. Intent influences which actions are generated and how they are interpreted. |
| `actions` | array | yes | Ordered list of deterministic actions to be evaluated during execution. |
| `invariants` | array | no | Optional list of invariants that must remain true across execution. Used for auditing and validation. |