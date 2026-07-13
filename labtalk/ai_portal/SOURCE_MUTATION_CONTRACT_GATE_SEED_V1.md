# Source Mutation Contract Gate Seed v1

Status: **Mandatory before source-code mutation**
Authority: x64base maintainer and the active contract shelf
Applies to: C++, headers, runtime command behavior, build interfaces, bindings,
GUI/runtime interfaces, and other authoritative implementation source

## Rule

An AI must not mutate source code until it has read the project's contracts.

At minimum, read:

1. `D:\code\ccode\docs\contracts\README.md`
2. `D:\code\ccode\docs\contracts\CONTRACT_REGISTRY_V1.md`
3. `D:\code\ccode\docs\contracts\CONTRACT_LIFECYCLE_V1.md`
4. every registered contract owned by or affecting the target subsystem
5. applicable source `@dottalk.contract` and `@dottalk.usage` blocks in the
   target and neighboring implementation

The central shelf indexes contracts but does not replace related database,
GUI, UI, build, safety, governance, HELP, or publication contracts. Follow the
registry links and search the owning subsystem before editing.

## Required Contract Preflight

Before applying a source patch, record:

```text
Source target:
Owning subsystem:
Contracts read:
Contract evidence states:
Constraints that apply:
Proposed behavioral effect:
Required source/test/HELP/metadata updates:
Proof plan:
Known contract drift or uncertainty:
```

If no applicable contract is found, say `no applicable registered contract
found` and inspect the contract intake queue and nearby source annotations. Do
not translate “not found” into “unconstrained.”

## Conflict Rule

If the requested code change conflicts with an active contract:

1. stop before mutating source;
2. identify the exact contract and evidence state;
3. report the conflict to the maintainer;
4. do not weaken, rewrite, or supersede the contract merely to make the patch
   convenient;
5. proceed only after the maintainer selects a contract-preserving change or
   explicitly authorizes a reviewed contract change.

## Contract Drift Rule

A source change may create drift even when the code builds. Before closeout,
check whether it changes:

- command syntax, no-argument behavior, usage access, examples, or aliases;
- runtime guarantees, storage behavior, data shape, ownership, or lifecycle;
- mutation, recovery, locking, validation, or destructive-operation safety;
- UI/binding interfaces, event names, threading, or resource ownership;
- build options, dependencies, platform behavior, or public interfaces;
- HELP, CMDHELP, metadata, SelfDoc, manual, or website claims.

When a durable rule changes, update or supersede the contract through the
contract lifecycle and keep its evidence class honest. A chat statement or
source patch alone is not a durable contract update.

## Closeout Requirement

A source-mutation task is not complete until its closeout names:

- contracts read;
- whether the patch preserved, implemented, or intentionally changed them;
- tests/runtime proof performed;
- HELP/metadata/documentation impact;
- unresolved contract drift.

This gate informs and constrains source work. It does not grant permission to
mutate source, contracts, runtime data, or publication artifacts.
