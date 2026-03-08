# Testing and Validation

The DITA Package Processor is validated using **pytest** with a focus on
**structural correctness, observability, and deterministic behavior**.

Tests are designed to confirm not just that transformations work, but that:

- the input corpus is **correctly understood**
- assumptions are **made explicit**
- unsafe situations are **detected before mutation**
- failures are **loud, early, and explainable**

This is not a mock-heavy unit test suite.  
It is a system-level validation of how the processor behaves against real data.

---

## Running the Test Suite

From the repository root:

```bash
pytest -q
```

This runs the full test suite, including:

- discovery and classification
- knowledge invariants
- CLI contract validation
- end-to-end pipeline execution

There is no separate “unit-only” mode.  
The system is tested the way it is actually used.

---

## Testing Strategy Overview

The project follows a **layered testing strategy** aligned with the architecture:

```
Discovery  →  Knowledge  →  Transformation  →  CLI
```

Each layer has its own tests and failure semantics.

---

## Discovery Tests

Discovery tests validate **observation, not mutation**.

Located under:

```
tests/discovery/
```

### What Discovery Tests Assert

- Maps and topics are correctly scanned from disk
- Structural signatures are detected reliably
- Artifacts are classified deterministically
- Unknown or ambiguous structures are reported, not guessed
- Discovery reports are complete and internally consistent

These tests ensure that the processor understands *what is in the package*
before any transformation is attempted.

### Key Properties

- No files are modified
- No assumptions are inferred
- Classification is explainable and repeatable

Discovery is allowed to be incomplete, but never incorrect.

---

## Knowledge Layer Tests

Knowledge tests validate **encoded domain assumptions**.

Located under:

```
tests/knowledge/
```

### What Knowledge Tests Assert

- Known map patterns are loaded correctly
- Structural invariants are enforced consistently
- Unsupported patterns are rejected explicitly
- Knowledge rules remain stable over time

This layer is intentionally conservative.

If a rule exists here, it must be:
- documented
- tested
- justified by real corpus evidence

There are no “soft” rules in the knowledge layer.

---

## Transformation and Pipeline Tests

Transformation behavior is validated through **integration and end-to-end tests**.

Primary coverage lives in:

```
tests/test_end_to_end.py
```

### What the End-to-End Test Covers

The end-to-end test constructs a realistic DITA package on disk and verifies:

- `index.ditamap` is resolved and removed
- The main map is renamed to the configured DOCX stem
- Abstract content is injected into the renamed main map
- Remaining maps are numbered deterministically
- Wrapper concept topics are generated correctly
- Existing `topicref` elements are reparented
- Glossary topics are refactored into `glossentry` when configured

Assertions validate **semantic structure**, not fragile ordering or formatting details.

If the structure is wrong, the test fails.

---

## CLI Contract Tests

CLI behavior is validated separately to ensure user-facing stability.

Covered in:

```
tests/test_cli_contract.py
```

These tests assert that:

- Required arguments are enforced
- `-h` and `-v` behave correctly
- Invalid flags fail fast
- Logging overrides are respected

The CLI is treated as a public contract, not an implementation detail.

---

## Error Condition Coverage

Explicit tests exist for known failure scenarios, including:

- Missing `index.ditamap`
- Unresolvable main map references
- Missing or invalid definition maps
- Missing glossary navtitles
- Unsupported or ambiguous structures

These tests assert that:

- Structural impossibilities fail immediately
- Recoverable issues emit warnings, not crashes
- The pipeline never proceeds on invalid assumptions

Silent failure is considered a bug.

---

## Fixtures and Test Organization

Reusable fixtures live under:

```
tests/fixtures/
```

Fixtures provide:

- minimal realistic DITA packages
- controlled variations for edge cases
- shared setup logic without hiding behavior

Fixtures support clarity.  
They do not replace assertions.

---

## Logging Expectations

Logging is **always enabled**.

- Default verbosity is configured in `pyproject.toml`
- CLI flags may override logging for one-off runs
- Tests do not suppress logs unless explicitly required

For diagnostics:

```bash
pytest -q --log-cli-level=DEBUG
```

Logs are part of the behavioral contract, not incidental output.

---

## What Is *Not* Tested (By Design)

The test suite intentionally avoids:

- Mocked XML trees detached from the filesystem
- Snapshot-based output comparisons
- Performance benchmarking
- External schema validation (DTD/RNG)

The goal is **correctness, clarity, and survivability**, not theoretical coverage.

---

## Summary

The testing strategy enforces the project’s core principles:

- Observe before transforming
- Encode knowledge explicitly
- Fail loudly on invalid assumptions
- Test real behavior against real data

If a behavior matters, it is tested structurally.  
If an assumption exists, it is documented and enforced.