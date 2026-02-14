# Worked Example: From Raw DITA to Discovery Evidence

This document walks through a concrete example of how discovery works,
from raw DITA files to emitted evidence and final report output.

This is not a tutorial. It is an execution trace.

---

## Example Input: Raw DITA Package

Assume the following package structure:

```
dita/
├── index.ditamap
├── Main.ditamap
└── topics/
    └── definition.dita
```

### `index.ditamap`

```xml
<map>
  <title>Index</title>
  <mapref href="Main.ditamap"/>
</map>
```

### `Main.ditamap`

```xml
<map>
  <title>Main Content</title>
  <topicref href="topics/definition.dita"/>
</map>
```

### `topics/definition.dita`

```xml
<glossentry>
  <glossterm>Widget</glossterm>
  <glossdef>Example definition</glossdef>
</glossentry>
```

---

## Step 1: Discovery Scanner

The scanner walks the filesystem and identifies artifacts.

### Discovered Artifacts

| Path                    | Type   |
|-------------------------|--------|
| index.ditamap           | map    |
| Main.ditamap            | map    |
| topics/definition.dita  | topic  |

No classification occurs at this stage.

---

## Step 2: Metadata Extraction

Structural facts are extracted and stored as metadata.

### Artifact: `index.ditamap`

```json
{
  "path": "index.ditamap",
  "artifact_type": "map",
  "metadata": {
    "filename": "index.ditamap",
    "contains_mapref": true,
    "referenced_extensions": [".ditamap"]
  }
}
```

### Artifact: `Main.ditamap`

```json
{
  "path": "Main.ditamap",
  "artifact_type": "map",
  "metadata": {
    "filename": "Main.ditamap",
    "contains_topicref": true,
    "referenced_extensions": [".dita"]
  }
}
```

### Artifact: `topics/definition.dita`

```json
{
  "path": "topics/definition.dita",
  "artifact_type": "topic",
  "metadata": {
    "root_element": "glossentry"
  }
}
```

---

## Step 3: Pattern Evaluation

Patterns are evaluated independently for each artifact.

---

### Evaluating `index.ditamap`

#### Pattern: `main_map_by_index`

**Signals checked:**

- filename equals `index.ditamap` → ✅
- contains `<mapref>` with `.ditamap` href → ✅

**Result:** Pattern matches.

**Evidence emitted:**

```json
{
  "pattern_id": "main_map_by_index",
  "artifact_path": "index.ditamap",
  "asserted_role": "MAIN",
  "confidence": 0.9,
  "rationale": [
    "File is index.ditamap",
    "Contains mapref to another map"
  ]
}
```

---

### Evaluating `Main.ditamap`

No MAIN patterns match.

Fallback or content patterns may emit lower-confidence evidence later.

---

### Evaluating `topics/definition.dita`

#### Pattern: `glossary_topic_by_root`

**Signals checked:**

- root_element equals `glossentry` → ✅

**Evidence emitted:**

```json
{
  "pattern_id": "glossary_topic_by_root",
  "artifact_path": "topics/definition.dita",
  "asserted_role": "GLOSSARY",
  "confidence": 1.0,
  "rationale": [
    "Topic root element is <glossentry>"
  ]
}
```

---

## Step 4: Evidence Collection

At the end of evaluation, evidence looks like this:

```json
[
  {
    "artifact": "index.ditamap",
    "role": "MAIN",
    "confidence": 0.9
  },
  {
    "artifact": "topics/definition.dita",
    "role": "GLOSSARY",
    "confidence": 1.0
  }
]
```

No conflicts were resolved yet.

---

## Step 5: Report Generation

The DiscoveryReport summarizes observed facts and evidence.

### Example Summary Output

```json
{
  "maps": 2,
  "topics": 1,
  "main_maps": 1,
  "glossary_topics": 1,
  "unknown_artifacts": 0
}
```

This report is:

- Machine-readable
- Auditable
- Safe to archive
- Safe to feed into later pipeline stages

---

## Key Takeaways

- Discovery does not *decide*, it *records*
- Patterns emit evidence, not truth
- Conflicts are expected and visible
- Transformation logic comes later

Discovery exists to replace guesswork with facts.