# Understanding the DITA Package Processor Pipeline  
*A Practical Narrative for Users*

When you use the DITA Package Processor, you are not running “a script that fixes DITA.”  
You are running a **pipeline** with clearly separated responsibilities.

Understanding those responsibilities is the key to using the tool confidently, safely, and repeatably.

This document explains **what each stage is responsible for**, what it produces, and how you should interpret its output as a user.

---

## The Big Picture

The processor is intentionally divided into stages:

```
Discovery → Normalize → Plan → Execute
```

Each stage answers a different question.  
No stage tries to answer more than one.

This separation is what makes the system predictable instead of surprising.

---

## Stage 1: Discovery  
**“What is actually in this package?”**

Discovery is **read-only**. It does not change files. Ever.

When you run discovery, the tool:

- scans maps, topics, and media
- records what files exist
- extracts relationships (map references, topic references, images)
- builds a dependency graph

What discovery does *not* do:

- guess intent
- fix problems
- rename files
- restructure content

### How to think about discovery output

Discovery produces a JSON report that answers:

- What files are present?
- How are they connected?
- Which map appears to be the main entry point?
- Are there patterns the tool recognizes?
- Are there things it *cannot* safely interpret?

As a user, you should read discovery output as **a factual inventory**, not a decision.

If discovery cannot prove something safely, it records uncertainty instead of guessing.

That restraint is deliberate.

---

## Stage 2: Normalize  
**“Is this discovery result safe to plan from?”**

Normalization is a quiet but important step.

It takes the raw discovery report and:

- validates it against a strict contract
- ensures a single, unambiguous main map exists
- confirms that artifacts and relationships are internally consistent

If normalization fails, the pipeline stops.

### What normalization means for you

Normalization is the tool saying:

> “I understand this package well enough to make decisions about it.”

If normalization succeeds, you know:

- discovery was structurally coherent
- downstream steps are operating on stable ground

You usually don’t need to read the normalized output unless something fails later.

---

## Stage 3: Planning  
**“What *would* we do to this package?”**

Planning is where intent is declared.

Based on discovery results, the planner produces a **plan**: an explicit list of actions, in order.

Examples of actions:
- copy a map
- copy a topic
- copy media
- rename an artifact
- wrap map content
- refactor glossary entries

### What a plan is (and is not)

A plan is:

- deterministic
- explicit
- reviewable
- safe to inspect
- free of execution logic

A plan is **not**:
- execution
- a script
- a guess
- a best effort

Planning answers one question:

> “If we were allowed to change things, what exactly would we do, and why?”

As a user, this is your **decision checkpoint**.

You can:
- inspect the plan
- version it
- diff it
- approve it
- reject it

Nothing has been mutated yet.

---

## Stage 4: Execute (Dry-Run)  
**“Can this plan be carried out?”**

Execution defaults to **dry-run** mode.

In dry-run:
- every action is dispatched
- handlers are resolved
- ordering is tested
- failures surface early
- no files are written

### What dry-run tells you

A successful dry-run means:

- the plan is internally coherent
- required handlers exist
- execution order is valid
- nothing obvious will fail immediately

Dry-run does *not* guarantee filesystem success.  
It guarantees **logical executability**.

Think of it as a rehearsal, not the performance.

---

## Stage 5: Execute (`--apply`)  
**“Now actually do it.”**

When you rerun execution with `--apply`, the tool switches to a filesystem executor.

At this point:

- files are copied
- directories are created
- content is materialized into the target location
- every mutation is logged and reported

Execution produces an **Execution Report**, which records:

- which actions ran
- which handler handled them
- whether each action succeeded or failed
- whether the run was dry-run or apply

### What execution means for you

Execution is intentionally boring.

It does exactly what the plan said.  
Nothing more. Nothing less.

If execution surprises you, the plan is where the explanation lives.

---

## Why This Separation Matters (For You)

Most tools blur these steps together. That makes them convenient, but fragile.

This tool does not.

Because concerns are separated, you can:

- inspect reality before decisions are made
- approve intent before files are touched
- dry-run before risking mutation
- explain *why* a change happened after the fact

If something goes wrong, you know where to look:

| Problem | Where to look |
|------|---------------|
| Missing files | Discovery |
| Wrong assumptions | Discovery / Normalize |
| Wrong intent | Plan |
| Wrong mutation | Execute |
| Unexpected change | Plan (not execution) |

That clarity is the real feature.

---

## How to Use This as a User

A safe, recommended workflow is:

1. **Run discovery**  
   Learn what the tool sees.

2. **Generate a plan**  
   Learn what the tool intends.

3. **Run execute without `--apply`**  
   Confirm it is executable.

4. **Run execute with `--apply`**  
   Materialize the result.

You are always in control of when reality changes.

---

## Final Takeaway

The DITA Package Processor is not optimized for speed or cleverness.

It is optimized for:
- predictability
- explainability
- repeatability
- safety at scale

Once you understand the pipeline as a set of **separate concerns**, the tool stops feeling strict and starts feeling reliable.

That reliability is what lets you trust it with real documentation.