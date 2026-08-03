# Entities and the Bridge: Build Up Solid, Build Down Empirical v0

Status: draft
Audience: developer, maintainer, architect, ai_partner, student
Registry ID: lesson.career.entities_and_the_bridge
Concepts: concept.contract.usage, concept.selfdoc.validation, concept.evidence.review
Lane: AIF-067
Lane doc: `docs/ai-friendly/ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1.md`
Proof state: source_defined
Observed: 2026-07-27 (run DOCFLUSH-20260722-001)

> This body is transcribed from the lesson record in `lessons.yaml`, which was
> authored with `member.derald` and quotes him directly. Structure and headings
> added; the argument and the quotations are unchanged.

## Career Lesson

**Declaring is the first act of building, not paperwork that precedes it.**

> "declaring something is the first step to making it real by defining it and
> then building it, testing it, proofing it and release etc."
> -- `member.derald`

The chain is:

```text
declare -> define -> build -> test -> proof -> release
```

and **declaration is generative**: naming the entity brings it into the system,
and everything after is elaboration of something that already exists.

### The thesis has two readings, and they are equally important

Declaration-is-generative is documentation **upstream** -- building up, solid
and deductive, answering *"what is this supposed to be."*

Documentation-verifies is documentation **downstream** -- building down,
empirical and inductive, answering *"does it actually do that."*

Neither subsumes the other. Upstream alone is an elegant declaration nothing
satisfies. Downstream alone is a pile of true observations about whatever
happened to get built.

A first draft of this lesson called the upstream reading "the strongest form."
That was wrong, and wrong in a way this lesson should have caught -- it makes a
hierarchy of the two directions that are supposed to meet.

**The thesis is the span.** Documentation improves and proves the code because
it both *originates* the entity and later *measures* it, and the gap between
those two acts is where every recorded defect actually lives.

Skip the declaration and later stages have nothing to be measured against. You
cannot detect drift from a specification never written.

## The Unit of Tracking Is the Entity, Not the Task

A named thing the design has decided should exist is an entity from the moment
it has a file -- **even a zero-byte one**.

> "0 byte commands, plugs, and prototypes help define the top level layer of
> our systems design"
>
> "even unfinished, they are entities and can be tracked in the SDLC as they
> are onboarded into the system, and we just track their progression through
> our documentation process."
> -- `member.derald`

A zero-byte translation unit outperforms a TODO or a backlog item on three
axes:

1. it survives refactors
2. it appears in the census
3. removing it is a deliberate act with an author

The names are not arbitrary either. `app_army`, `app_alcoa` and `app_paxon`
match `CASE_HIST_020`, `CASE_HIST_030` and `CASE_HIST_060` exactly. The empty
files and the historical case studies are one list expressed twice.

## Documentation Is the Tracker

An entity's position in the documentation chain **is** its lifecycle stage:

```text
named -> described (@dottalk.file) -> contracted (@dottalk.usage)
      -> catalogued (SYSCMD row) -> surfaced (HELP topic)
      -> proven (runtime_observed)
```

There is no second system to keep in sync, which matters in a project whose
recurring defect is two systems that never compare themselves. The
`proof_state` vocabulary is not metadata about documents; it **is** lifecycle
state.

### The one rule

```text
An entity may sit at any stage, but may not CLAIM a later stage than it occupies.
```

A zero-byte file may say "I am a reserved slot." It may **not** say "I am the
ARMY command," because SYSCMD, HELP, dotref and the census all read a usage
contract as a real command surface and count it.

## Build Up, Build Down, Build the Span

Two directions, two kinds of work.

**Building up** is solid and deductive -- structure, reserved names, contracts,
schemas. It says what the system *is*, and can precede any running code.

**Building down** is empirical and inductive -- runtime proofs, measured sizes,
actual header bytes, real command output. It says what the system *does*.

Neither reaches the far bank alone. The **span** is the reconciliation, and
every defect this project has recorded lives exactly there:

| Defect | Declared | Observed |
|---|---|---|
| AIF-065 | a documented LMDB size ladder | two observed file sizes |
| AIF-066 | a `SOURCE_HASH` written | never read |
| AIF-067 | 33 ladder arms | 30 listed options |
| AIF-067 | a 20-field table | a 10-field CSV |
| AIF-067 | a registry key | the dispatcher cannot produce it |

Nothing in those pairs is individually wrong, **which is why no test failed**.
A test checks one end of a bridge.

### Consequence for tooling

`stack_audit_v1` is span inspection. Its WARN count is not a quality score --
it is the **measured distance between what has been declared and what has been
observed**. A finding closes when the two ends meet, not when someone silences
it.

### Consequence for contributors, human or AI

- **Do not "clean up" entities.** Check `docs/cases` and the registries before
  deleting anything empty.
- **Do not let an entity claim a stage it has not reached.**
- **Say which direction you are working in.** "I read the source" and "I ran it
  and observed X" are different evidence and earn different `proof_state`
  values.
- **When the ends do not meet, record the gap.** A documented gap is span work
  scheduled; an undocumented one is a bridge that looks finished.

## Ties

- `docs/ai-friendly/ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1.md` (AIF-067) -- the lane doc.
- `lesson.career.the_tree_already_has_it` -- why deleting "empty" things is a hazard.
- `lesson.career.a_script_never_run_is_not_evidence` -- the downstream half, sharpened.

Owner: `member.derald`.
