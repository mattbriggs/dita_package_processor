# Pattern Evaluator

This document describes the **PatternEvaluator**, the component responsible
for executing discovery patterns against discovered artifacts and emitting
structured evidence.

The evaluator is intentionally simple. Its job is not to be clever. Its job
is to be *predictable*.

---

## Purpose

The PatternEvaluator:

- Applies declarative patterns to discovered artifacts
- Evaluates whether required signals are present
- Emits **evidence records** when patterns match
- Never assigns final classifications
- Never mutates artifacts
- Never resolves conflicts

The evaluator is the bridge between **observation** and **decision-making**.

---

## Inputs

The evaluator operates on two inputs:

### 1. Discovered Artifacts

A `DiscoveryArtifact` represents a file already identified during scanning.

Artifacts provide:

- `path`
- `artifact_type` (`map` or `topic`)
- `metadata` (precomputed structural facts)

The evaluator does **not** parse XML itself. All structural facts must already
exist in artifact metadata.

---

### 2. Patterns

Patterns are loaded from `known_patterns.yaml` and normalized into `Pattern`
objects.

Each pattern defines:

- What artifact type it applies to
- Which signals must be present
- What evidence it emits when matched

---

## Evaluation Contract

Evaluation follows these rules, in this order:

1. **Artifact type filtering**
   - Patterns whose `applies_to` does not match the artifact are skipped.

2. **Signal matching**
   - All declared signals must match the artifact’s metadata.
   - Signals are logically ANDed.
   - Missing signals cause a non-match, not an error.

3. **Evidence emission**
   - If all signals match, the pattern emits one Evidence record.
   - Evidence is immutable once created.

4. **Fallback handling**
   - Fallback patterns only fire if *no other patterns matched*.
   - Fallback patterns always have the lowest confidence.

---

## Signal Evaluation

Signals describe *observable facts*, not interpretations.

Examples of signals include:

- Filename equality or substring checks
- Root XML element names
- Presence of specific XML elements or attributes
- Package-level counts (e.g. number of maps)

Signals are matched against artifact metadata only.
The evaluator never inspects files directly.

---

## Evidence Emission

Each matching pattern emits exactly one Evidence object containing:

- `pattern_id`
- `artifact_path`
- `asserted_role`
- `confidence`
- `rationale`

Multiple patterns may emit evidence for the same artifact.

Conflicting evidence is expected and allowed.

---

## What the Evaluator Does NOT Do

The PatternEvaluator explicitly does **not**:

- Choose a final classification
- Merge or rank evidence
- Resolve conflicts
- Apply heuristics
- Modify artifacts
- Call external systems
- Interpret intent

Those responsibilities belong to later stages.

---

## Determinism Guarantees

Given:

- The same artifact metadata
- The same pattern set

The evaluator will:

- Emit the same evidence
- In the same order
- Every time

There is no randomness and no hidden state.

---

## Failure Modes

The evaluator must fail *softly*:

- Invalid patterns are rejected at load time
- Missing metadata causes patterns to not match
- No matches results in fallback evidence, not an error

Discovery must never crash the pipeline.

---

## Summary

The PatternEvaluator is a pure function:

```
(artifact, patterns) → evidence[]
```

It exists to make structural reality explicit, testable, and reviewable.

Nothing more.
Nothing less.