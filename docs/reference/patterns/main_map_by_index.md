# Pattern: `main_map_by_index`

## Applies To
`map`

## Signals
```yaml
filename:
  equals: index.ditamap
contains:
- element: mapref
  attribute: href
  ends_with: .ditamap

```

## Asserts
```yaml
role: MAIN
confidence: 0.9

```

## Rationale
- File is index.ditamap
- Contains mapref to another map
