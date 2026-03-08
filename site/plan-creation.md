# How to Create a Plan

This document reflects the current planning model in the repository.

A plan is a deterministic artifact produced from `PlanningInput`. It is not executable logic. It is the ordered declaration of what execution should attempt.

## What a Plan Is

A plan:

- is pure data
- is ordered
- is schema-validated
- is reviewable before execution
- carries reasons and evidence references

If execution does something, it is because the plan said so.

## Current Planning Flow

```text
DiscoveryReport -> PlanningInput -> Planner -> plan actions
```

Or, in the in-process orchestration path:

```text
DiscoveryInventory -> PlanningInput model -> Planner -> plan actions
```

The critical boundary is that the planner consumes `PlanningInput`, not raw filesystem state.

## Where Planning Lives

Current planning modules are under:

```text
dita_package_processor/planning/
```

Key modules:

- `contracts/discovery_to_planning.py`
- `contracts/planning_input.py`
- `planner.py`
- `validation.py`
- `invariants.py`
- `layout_rules.py`

## How Actions Are Produced Now

The planner no longer operates as a configurable list of planning steps.

Current action production model:

1. artifacts are sorted deterministically
2. the plugin registry is loaded
3. each plugin receives each artifact and its evidence
4. plugins emit action template dictionaries
5. the planner assigns globally unique action IDs
6. the plan is validated

This means planning extensibility now happens primarily through plugin `emit_actions(...)`.

## Inputs to Planning

Planning requires:

- a valid `PlanningInput`
- a resolved main map
- normalized artifact records
- normalized relationships

Planning does not:

- rescan the package
- mutate files
- invent handlers
- guess unresolved structure

## Action Rules

Actions should remain:

- explicit
- deterministic
- reviewable
- narrow in scope
- tied to known handler types

Each action template emitted by plugins should include:

- `type`
- `target`
- `parameters`
- `reason`
- `derived_from_evidence`

The planner assigns the `id`.

## Failure Philosophy

Planning should fail when:

- the planning contract is invalid
- invariants do not hold
- plugin action emission causes invalid plan output

Planning should not compensate for ambiguity by guessing.

## Extending Planning Safely

Current extension path:

1. add or adjust discovery patterns if new evidence is needed
2. emit action templates from plugin planning logic
3. provide matching handlers for new action types
4. lock the behavior with planning and execution tests

That keeps planning declarative and keeps execution boring.

## Summary

The current planning model is:

- contract in
- plugin-assisted action emission
- deterministic ordering
- schema validation
- plan out
