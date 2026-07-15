# DotTalk++ Contract Lifecycle v1

Status: active process contract.

## Purpose

DotTalk++ work often begins in chat, experiments, or guarded implementation
passes. Good ideas can disappear when a chat is compacted, when memory is freed,
or when an implementation partially succeeds and the rationale is lost.

This lifecycle defines how a contract becomes durable.

## Contract States

| State | Meaning |
| --- | --- |
| Chat-intended | Discussed in chat only; not durable |
| Draft | Written in repo but not reviewed or linked |
| Design-intended | Accepted as a design constraint, not yet runtime-proven |
| Source-defined | Public code/API/source comments implement it |
| Runtime-proven | Tests or commands prove it |
| HELP-documented | HELP/CMDHELP explains it |
| Metadata-staged | Metadata/catalog rows carry it |
| Publication-ready | SelfDoc/manualgen can publish it with evidence |
| Superseded | Replaced by a newer contract |
| Rejected | Explicitly not part of the system |

## Chat To Contract Rule

A chat decision is not durable until it lands in the repo.

Minimum durable form:

- a contract document,
- a registry row,
- an honest evidence class,
- links to proof or planned proof.

If the decision affects source behavior, add source comments or tests as soon as
practical.

## Contract Document Requirements

Every durable contract should answer:

- What behavior or boundary does this constrain?
- Which subsystem owns it?
- Which files/code/tests currently prove it?
- What evidence class does it have?
- What must not be done because of it?
- What are the migration or review triggers?
- What is deferred?

## Evidence Upgrade Path

```text
contract doc
  -> source/API shape
  -> smoke or regression test
  -> HELP/metadata alignment where user-facing
  -> manual/selfdoc publication
```

Skipping steps is allowed only if the contract clearly says so and remains
honest about evidence class.

## Contract Drift

Contract drift happens when:

- source behavior changes but the contract does not,
- HELP says something different from runtime,
- metadata rows preserve old behavior,
- manualgen publishes stale claims,
- chat creates new rules without repo artifacts,
- tests prove only the old behavior.

When drift is found:

1. Identify the stronger authority.
2. Update weaker artifacts or mark the contract superseded.
3. Add a report or test if the drift can recur.
4. Update `CONTRACT_REGISTRY_V1.md`.

## Transitory Notes

Not every note is a contract.

Transitory notes are allowed for:

- implementation scratch,
- temporary plans,
- one-time reports,
- exploratory options,
- rejected branches,
- local workarounds.

But if a note says future work "must", "should always", "must not", "guarantees",
or "defines", it should usually become a contract or be softened.

## Naming

Use stable names:

```text
<SUBSYSTEM>_<SUBJECT>_CONTRACT_V<n>.md
```

Examples:

- `VALUE_LOCALE_COLLATION_CONTRACT_V1.md`
- `DATABASE_SAFETY_CONTRACT_V1.md`
- `WINDOWED_APP_CONTRACT_V1.md`

Usage contracts embedded in source may keep their command-specific form, but
should still be harvestable and registry-visible.

## Agent Rule

When an AI agent creates or relies on a contract:

- do not leave it only in the final answer,
- do not rely on chat memory,
- write the contract or update the registry,
- keep the evidence class honest,
- prefer small source/test hooks that make the contract checkable.

