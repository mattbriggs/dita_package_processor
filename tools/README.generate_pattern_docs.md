# Pattern Documentation Generator

This tool generates MkDocs-ready documentation from
`known_patterns.yaml`.

## Purpose

Patterns are *structural knowledge*, not code.

This script ensures that:

- pattern intent is visible
- confidence is explicit
- rationale is preserved
- documentation stays in sync with reality

## Usage

```bash
pip install -r tools/generate_pattern_docs.requirements.txt
python tools/generate_pattern_docs.py
```

## Output

```
docs/reference/patterns/
├── index.md
├── main_map_by_index.md
├── single_root_map.md
└── ...
```

Each file documents:
- what the pattern applies to
- the signals it observes
- the assertions it emits
- why it exists


## `tools/generate_pattern_docs.requirements.txt`

```
PyYAML>=6.0
```


## Design Principles

- YAML is authoritative
- No inference
- No re-interpretation
- No mutation
- Human-readable first

This is knowledge documentation, not a compiler pass.
```



# Why This Fits Your System

This mirrors your architecture perfectly:

```
known_patterns.yaml
        ↓
   Discovery Evidence
        ↓
   Planning Decisions
        ↓
   Actions
        ↓
   Handlers
```

And now users can **read the knowledge layer** instead of guessing at it.

If you want next steps, the natural extensions are:

- link patterns → tests that exercise them
- embed confidence heatmaps in docs
- cross-reference patterns with emitted evidence in Discovery reports

But this version already does the important thing:

It makes your system explain itself.