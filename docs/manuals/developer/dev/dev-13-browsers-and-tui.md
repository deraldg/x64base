# DEV-13 Browsers and TUI

```yaml
page_id: DEV-13
title: Browsers and TUI
status: DRAFT_WITH_TEMPORARY_EVIDENCE_LANES
last_verified: 2026-05-24
```

## Temporary evidence lane / future META feeder note

Where this chapter uses temporary evidence sources, those sources are not being treated as a replacement for META. They are the current available evidence until the relevant META tables are seeded, promoted, or crosswalked.

Temporary evidence rows should later reconcile into the named future META feeder tables.


## Ownership doctrine

Browser/TUI surfaces render and navigate projected state. They do not own table storage, relation semantics, memo payloads, command truth, or metadata truth.

## Workbench front-end doctrine

This chapter now needs to be read as part of the broader workbench/front-end
architecture.

Relevant front-end families include:

- classic CLI projection surfaces
- TUI/browser surfaces
- ERSATZ and relation-aware result browsing
- wx workbench lanes
- Python preview/prototyping lanes
- campus/lab portal consumers

All of them are consumers of runtime truth.

They should consume:

- area selection and cursor state
- logical order state
- relation state
- tuple/projection state
- mutation and validation outcomes
- message and diagnostics output

from DotTalk++ and the engine.

They should not:

- invent their own database truth
- replace runtime relation semantics
- redefine index/order ownership
- become the source of command or metadata truth

## Open architecture implications

The browser/TUI/front-end family is one of the main public proofs that x64base
is an open architecture.

That means this chapter should preserve the distinction between:

- front ends as views over engine truth
- extension seams that allow new workbench surfaces to be built
- educational work that uses those surfaces to teach data navigation,
  projection, ordering, and relation traversal

## Current practical lesson

The strongest current lesson is that a front end should mirror runtime truth
rather than clone it.

That rule applies equally to:

- ERSATZ
- relation result browsers
- TUI lanes
- wx workbench
- Python preview

When those layers drift from runtime state, the runtime wins and the front end
must be repaired.

## Proven paths

- x32 MCC / ERSATZ relation browser path.
- plain ERSATZ/no-arg browser path.
- LIST as traversal proof surface.

## Canaries

- x64 workspace/ERSATZ load reporting inconsistency.
- ERSATZ GRID snapshot branch deferred.
- memo projection may show raw pointers if backend is unattached.
- TUI availability may be build-gated.

## Future/maturing META feeders

- `SYSCMD`
- `SYSSUBCMD`
- `SYSENTVAR`
- `SYSARGS`
- `SYSMSG`
- `SYSHELP`
