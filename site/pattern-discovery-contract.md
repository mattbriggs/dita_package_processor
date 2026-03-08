# Discovery Pattern Contract

This document defines the **pattern evaluation contract** used by the
DITA Package Processor during the **Discovery phase**.

Patterns are declarative descriptions of *observable structural evidence*
found in real-world DITA packages. They do **not** encode transformation
logic, intent inference, or corrective behavior.

If discovery is the act of *looking*, patterns define **what counts as
seeing something meaningful**.

---

## Design Principles

Patterns are governed by the following constraints:

1. **Evidence, not decisions**
   - Patterns emit evidence.
   - They do not classify artifacts directly.
   - Final classification is resolved elsewhere.

2. **Declarative, not procedural**
   - YAML describes *what must be observed*, not *how to observe it*.
   - No control flow, no conditionals, no embedded logic.

3. **Auditability over cleverness**
   - Every emitted result must explain *why* it fired.
   - Confidence is explicit and numeric.
   - Rationale is human-readable.

4. **Failure-safe**
   - Absence of a pattern match is not an error.
   - Fallback patterns ensure coverage without false certainty.

5. **DITA-native first**
   - XML structure and DITA semantics are preferred over filename heuristics.
   - Filenames are signals, not truth.

---

## What a Pattern Is

A **Pattern** is a declarative rule that:

- Applies to a specific artifact type (`map` or `topic`)
- Specifies one or more **signals** that must be observed
- Emits **evidence** when all signals match

Patterns are evaluated independently and may all fire for the same artifact.

---

## Pattern Structure

Each pattern definition contains the following fields:

### `id` (required)

A stable, unique identifier for the pattern.

```yaml
id: main_map_by_index
```

This ID is used for:
- Evidence attribution
- Debugging
- Report output
- Test assertions

It must never be repurposed.

---

### `applies_to` (required)

Defines the artifact type this pattern evaluates.

```yaml
applies_to: map
```

Valid values:
- `map`
- `topic`

Patterns are never evaluated against incompatible artifact types.

---

### `signals` (required)

Signals define **observable facts** that must be present for the pattern
to emit evidence.

Signals are *structural*, not interpretive.

Examples include:
- filename matches
- root element name
- presence of specific XML elements or attributes
- package-level counts

Signals must be **ANDed** together. All signals must match.

```yaml
signals:
  filename:
    equals: index.ditamap

  contains:
    - element: mapref
      attribute: href
      ends_with: .ditamap
```

Signal evaluation is deterministic and side-effect free.

---

### `asserts` (required)

Defines the evidence emitted when signals match.

```yaml
asserts:
  role: MAIN
  confidence: 0.9
```

Fields:
- `role`: the semantic role being asserted
- `confidence`: a numeric value between 0.0 and 1.0

Confidence represents **strength of evidence**, not correctness.

---

### `rationale` (required)

Human-readable explanation of *why this pattern exists* and *why it fired*.

```yaml
rationale:
  - "File is index.ditamap"
  - "Contains mapref to another map"
```

Rationale strings:
- Appear in reports
- Are included in emitted evidence
- Must be understandable without reading code

If a pattern fires and cannot explain itself, it is invalid.

---

## Evidence Model

When a pattern matches an artifact, it emits an **Evidence record**.

Evidence includes:
- `pattern_id`
- `artifact_path`
- `asserted_role`
- `confidence`
- `rationale`

Evidence is immutable once emitted.

Multiple patterns may emit evidence for the same artifact.

---

## Fallback Patterns

Fallback patterns ensure that *every artifact produces evidence* even
when no specific structural signals match.

Fallback patterns:
- Must use `signals: { fallback: true }`
- Must have the **lowest confidence**
- Must only fire when no other patterns match

Example:

```yaml
signals:
  fallback: true
```

Fallback patterns prevent silent ambiguity without overstating certainty.

---

## What Patterns Do NOT Do

Patterns explicitly do **not**:

- Modify files
- Rename artifacts
- Resolve conflicts
- Choose a final classification
- Guess author intent
- Perform transformations
- Encode control flow
- Act as a DSL

Any attempt to add these behaviors violates the contract.

---

## Relationship to the Pipeline

Patterns are evaluated during **Discovery**, before the pipeline runs.

The pipeline may:
- Refuse to execute
- Emit warnings
- Choose alternate strategies

But it must never:
- Re-run discovery logic
- Guess around missing evidence
- Override emitted evidence silently

Patterns make ambiguity **visible**, not invisible.

---

## Evolution Rules

When extending patterns:

- Add new patterns instead of mutating old ones
- Never change the meaning of an existing `id`
- Add tests for every new pattern
- Prefer DITA structure over naming conventions
- Keep confidence conservative

Discovery is about restraint, not ambition.

---

## Summary

Patterns define **how reality is observed**, not how it is corrected.

They exist to make broken, inconsistent, vendor-generated DITA packages
*legible* before we attempt to clean them up.

If discovery lies, the pipeline breaks.

This contract exists to prevent that.