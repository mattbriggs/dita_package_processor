# Extensions

This document defines the **supported extension mechanism** for the DITA Package Processor.

Extensions are implemented as new **pipeline steps**. There are no plugins, hooks, or dynamic loaders. If behavior is not expressed as a `ProcessingStep`, it is not a supported extension.

---

## Extension Model (At a Glance)

- Extensions are **new `ProcessingStep` classes**
- Steps participate in the pipeline in an explicit order
- Each step has **one responsibility**
- Shared state flows only through `ProcessingContext`
- Side effects are limited to the package directory

If an extension cannot be expressed this way, it does not belong in this project.

---

## Architectural Roles

| Component | Responsibility |
|--------|----------------|
| Pipeline | Owns execution order, lifecycle, and logging |
| ProcessingContext | Shared, explicit runtime state |
| ProcessingStep | One discrete transformation |
| dita_xml | Centralized XML parsing and rewriting |
| utils | Stateless helper functions |

Extensions integrate **only** at the `ProcessingStep` level.

---

## Step Contracts

Each step operates under a clear contract:  
**preconditions may be assumed; postconditions must be guaranteed**.

| Step | Preconditions | Postconditions |
|----|---------------|----------------|
| RemoveIndexMapStep | `index.ditamap` exists and references a `.ditamap` | Main map resolved; `index.ditamap` deleted |
| RenameMainMapStep | Main map path resolved | Main map renamed to `<docx_stem>.ditamap` |
| ProcessMapsStep | Renamed main map exists | Abstract topic injected; maps numbered; wrapper topics created; topicrefs normalized |
| RefactorGlossaryStep | Definition map configured and exists | Definition child topics transformed to `glossentry` |

**Failure semantics**

- Structural violations fail fast
- Content inconsistencies log warnings and continue
- Failures stop the pipeline immediately
- No rollback is performed

---

## ProcessingContext Usage

`ProcessingContext` is the **only supported shared state mechanism**.

### Stable Attributes

Always present:

- `package_dir`
- `docx_stem`
- `topics_dir` (derived)
- `media_dir` (derived)

### Derived Attributes

Populated by specific steps:

- `main_map_path`  
  Set by `RemoveIndexMapStep`

- `renamed_main_map_path`  
  Set by `RenameMainMapStep`

Steps may only read derived attributes **after** the responsible step has executed.

---

## Adding Context Attributes (Extensions)

Extensions may introduce new context attributes if they follow these rules:

- Use explicit, descriptive names
- Document the attribute in the step docstring
- Do not shadow existing attributes
- Keep attributes optional unless enforced by a prior step

Example:

```python
context.regex_cleanup_applied = True
```

Context is shared state, not a general-purpose key-value store.

---

## Creating a New Step

### Step Definition

```python
from dita_package_processor.steps.base import ProcessingStep

class MyNewStep(ProcessingStep):
    name = "my-new-step"

    def run(self, context, logger):
        # Implement exactly one responsibility
        ...
```

**Rules**

- Inherit from `ProcessingStep`
- Implement `run(context, logger)`
- Declare a stable, unique `name`
- Do not invoke other steps

---

### Step Registration

Steps are registered **explicitly** when constructing the pipeline.

Execution order is intentional and visible:

```python
Pipeline(
    steps=[
        RemoveIndexMapStep(),
        RenameMainMapStep(),
        MyNewStep(),
        ProcessMapsStep(),
        RefactorGlossaryStep(),
    ],
    logger=logger,
)
```

There is no automatic discovery.

---

## Placement Guidelines

Use these guidelines when inserting a new step:

| Step Type | Recommended Position |
|---------|----------------------|
| File discovery / deletion | Early |
| Map restructuring | Before topic-level steps |
| Topic generation | Middle |
| Content rewriting | Late |
| Validation / cleanup | Last |

If placement is ambiguous, the step is probably doing too much.

---

## XML Safety Rules

- Do **not** perform ad-hoc XML manipulation inside steps
- Reuse helpers from `dita_xml.py`
- Centralize XPath and tree logic in the facade module

Pattern to follow:

```python
doc = read_xml(path)
doc = transform_function(doc)
write_xml(doc)
```

This keeps XML behavior consistent and maintainable.

---

## Explicitly Unsupported Anti-Patterns

The following are not supported and should not be introduced:

- Steps invoking other steps
- Feature flags inside steps to simulate ordering
- Orchestration logic in the CLI
- Shared globals
- Implicit dependencies between steps

If you need conditional behavior, add a new step and make it explicit.

---

## Summary

Extensions in this project are deliberately constrained:

- Linear pipeline
- Explicit execution order
- One responsibility per step
- Controlled shared state

These constraints are what keep the system predictable, testable, and maintainable at scale.