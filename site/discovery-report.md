# Sample Discovery Report

This is a **representative Discovery Report** rendered in Markdown.  
It shows what a *real run* against a messy corpus should produce.

You can treat this as both:
- documentation
- a golden example for tests

---

## Discovery Report  
**DITA Package Processor**

**Package Root:**  
`/data/unison/CL-FC0036-Centralines-Board-Charter/dita`

**Discovery Version:** `0.1.0`  
**Timestamp:** `2025-01-14T09:42:11Z`

---

## Summary

| Metric | Count |
|------|------|
| Maps discovered | 7 |
| Topics discovered | 214 |
| Classified maps | 6 |
| Unknown maps | 1 |
| Invariant violations | 1 |

**Transformation eligibility:** ❌ **Blocked**

---

## Map Inventory

| File | MapType | Confidence | Notes |
|----|--------|------------|------|
| `index.ditamap` | CONTAINER | High | Entry-point wrapper |
| `Main.ditamap` | MAIN | High | Referenced by index |
| `Abstract.ditamap` | ABSTRACT | Medium | Title + structure match |
| `Definitions.ditamap` | GLOSSARY | High | Glossary signature detected |
| `Map1.ditamap` | CONTENT | High | Standard content map |
| `Map2.ditamap` | CONTENT | High | Standard content map |
| `LegacyOverview.ditamap` | UNKNOWN | Low | No matching signature |

---

## Topic Inventory (Summary)

| TopicType | Count |
|---------|------|
| CONTENT | 203 |
| GLOSSARY | 8 |
| UNKNOWN | 3 |

---

## Invariant Validation

### ❌ Violations

#### INV-001: Single MAIN Map Required

- **Expected:** exactly 1 MAIN map
- **Found:** 1  
- **Status:** ✅ Pass

#### INV-002: At Most One ABSTRACT Map

- **Expected:** ≤ 1
- **Found:** 1  
- **Status:** ✅ Pass

#### INV-003: GLOSSARY Map Must Be Unique

- **Expected:** ≤ 1
- **Found:** 1  
- **Status:** ✅ Pass

#### INV-004: No UNKNOWN Maps When Transforming

- **Expected:** 0 UNKNOWN maps
- **Found:** 1  
- **Status:** ❌ Fail

---

## Blocking Issues

### UNKNOWN Map Detected

- **File:** `LegacyOverview.ditamap`
- **Reason:**  
  - No known filename pattern  
  - No structural signature match  
  - Contains both `mapref` and `topicref` elements  

**Action Required:**  
Document a new pattern **or** explicitly exclude this map from transformation.

---

## Recommendation

Transformation is **blocked** until:
- `LegacyOverview.ditamap` is classified, or
- the transformation pipeline is configured to ignore UNKNOWN maps

---

## Discovery Notes

- All XML files parsed successfully
- No fatal parse errors detected
- Recoverable XML issues were logged but tolerated

