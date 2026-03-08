# Why `run` Exists and `execute` Stays Strict

This document explains a deliberate design choice in the DITA Package Processor CLI:

> **Why orchestration lives in `run`, and `execute` refuses to be helpful.**

This is not accidental.  
It is not unfinished.  
It is a hard boundary.

---

## The Problem We Are Avoiding

Most content-processing tools collapse these concerns into one command:

- inspect input  
- infer intent  
- mutate files  
- hope nothing goes wrong  

That approach optimizes for convenience and quietly trades away:

- debuggability  
- auditability  
- repeatability  
- trust  

The DITA Package Processor explicitly does **not** do that.

---

## The Core Contract

The system is built around a single invariant:

> **Every mutation must be justified by an explicit, inspectable artifact.**

That artifact chain is fixed:

```
package
  → discovery.json
    → planning_input.json
      → plan.json
        → execution report
```

Each artifact exists for a reason.  
Each boundary is enforced.

No phase skips ahead.  
No phase repairs the mistakes of the previous one.

---

## Why `execute` Is Strict

The `execute` command exists to do exactly one thing:

> **Apply a validated execution plan inside a bounded filesystem sandbox.**

Nothing more.

### What `execute` requires

- A concrete, schema-valid `plan.json`  
- An explicit `--source-root`  
- An explicit output directory  
- An explicit decision to mutate (`--apply`)  

If any of those are missing, `execute` fails.

That failure is intentional.

---

### What `execute` refuses to do

`execute` will not:

- Discover content  
- Normalize structure  
- Infer intent  
- Choose a “main” map  
- Invent paths  
- Guess defaults  
- Repair a broken plan  

If the plan is wrong, execution is wrong.  
That is how responsibility stays visible.

---

## Why This Matters

If `execute` were allowed to:

- accept a package directory  
- silently run discovery  
- silently generate a plan  
- silently choose paths  
- then mutate files  

you would immediately lose:

- the ability to review decisions  
- the ability to diff intent across runs  
- the ability to stop before damage  
- the ability to explain *why* something happened  

At that point, you no longer have a system.  
You have a script with ambition.

---

## Why `run` Exists

`run` exists to solve a *different* problem:

> **Orchestrating the full pipeline without weakening its contracts.**

Humans do not want to manually wire:

```text
discover → normalize → plan → execute
```

Machines do.

So `run` performs orchestration **internally**, while preserving every boundary.

---

### What `run` does

- Invokes `discover` with a package root  
- Feeds its output into `normalize`  
- Feeds normalized output into `plan`  
- Invokes `execute` with the generated plan  
- Passes `source-root` and `output` explicitly  
- Preserves all intermediate artifacts  

No shortcuts.  
No shared mutable state.

---

### What `run` does *not* do

`run` does not:

- Bypass validation  
- Skip artifacts  
- Relax schema requirements  
- Change execution semantics  
- Make `execute` more permissive  

It is orchestration glue.  
It is not intelligence.

---

## Why `run` Is a Separate Command

Because conflating orchestration with execution is how systems rot.

Keeping them separate ensures:

- `execute` is testable in isolation  
- `execute` can be safely reused by other tools  
- CI systems can inspect plans before applying them  
- Execution logic remains boring and predictable  
- Orchestration can evolve without destabilizing mutation  

This mirrors well-understood boundaries:

- plan vs apply  
- compile vs link  
- dry-run vs mutate  

---

## Implicit `run` Invocation (And Why It Exists)

The CLI supports shorthand invocation:

```bash
dita_package_processor --package ./dita
```

Internally, this is treated as:

```bash
dita_package_processor run --package ./dita
```

This exists for:

- production ergonomics  
- end-to-end testing  
- backward compatibility  

It does **not** change the underlying model.

All guarantees remain intact.

---

## A Useful Mental Shortcut

If you are deciding which command to use:

- Use **`discover`** to observe  
- Use **`normalize`** to enforce structure  
- Use **`plan`** to decide  
- Use **`execute`** to apply  
- Use **`run`** to orchestrate the whole pipeline  

If you feel tempted to make `execute` smarter, stop.  
That work belongs upstream.

---

## Design Principle (Non-Negotiable)

> **Orchestration may be convenient.  
Execution must be boring.**

Boring execution is how this tool avoids destroying real documentation at scale.

That constraint is the feature.

---

## Where This Leads

This design naturally supports future extensions:

- alternative executors  
- preview-only execution  
- policy-driven mutation  
- CI approval gates  
- plan diffs and audits  

All without ever weakening `execute`.

The discipline here compounds.

---

If you want a follow-up document, the natural next ones are:

- **Why discovery is read-only forever**  
- **Why plans are artifacts, not objects**  
- **Why no executor may mutate without `--apply`**  

They all rhyme, and they all protect the same boundary.