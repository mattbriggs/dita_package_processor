# Schema Documentation Generator

This tool generates **deterministic Markdown documentation** from JSON Schema
and YAML-based schema artifacts in the DITA Package Processor repository.

It exists to prevent schema drift, stale documentation, and hand-maintained
contract descriptions.

If a schema defines behavior, this tool documents it.



## What This Tool Does

- Scans the repository for schema files (`*.schema.json`, `*.yaml`)
- Parses structural fields and requirements
- Generates Markdown documentation per schema
- Writes output to `docs/reference/schemas/`
- Produces stable, reviewable documentation artifacts

This tool does **not**:
- Modify schemas
- Infer behavior
- Execute migrations
- Depend on MkDocs plugins



## Why This Exists

Schemas are contracts.

If contracts are undocumented, they are folklore.  
If documentation is handwritten, it rots.

This tool ensures that **schemas remain the single source of truth**.



## How to Run

From the repository root:

```bash
python tools/generate_schema_docs.py
```

Generated files will appear in:

```
docs/reference/schemas/
```

These files are intended to be committed to the repository and rendered by
MkDocs like any other Markdown.



## Integration with MkDocs

Add generated files to `mkdocs.yml`:

```yaml
nav:
  - API Reference:
      - Schemas:
          - Known Patterns: reference/schemas/known_patterns.md
          - Plan: reference/schemas/plan.schema.md
```

This tool runs **before** `mkdocs build`.

## Design Guarantees

- Deterministic output
- Explicit failure modes
- No runtime guessing
- Schema-first documentation
- Compatible with CI pipelines

If documentation changes, it is because the schema changed.

That is the point.