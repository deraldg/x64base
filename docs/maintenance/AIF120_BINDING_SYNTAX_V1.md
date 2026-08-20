---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-061
  recorded_at_utc: 2026-08-19T23:30:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 2798f25e0
  authorization:
    requested_by: maintainer (member.derald), standing in-session -- R52 section 4
      named this the next unit; it is also gate 11's second-nearest fix.
  report:
    path: docs/maintenance/AIF120_BINDING_SYNTAX_V1.md
    kind: ruling
---

# AIF-120 -- R53: `BINDING` gets a syntax, and the work areas get an owner

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

Two threads meet here. Gate 11's second-nearest fix was *"Define `BINDING`'s syntax,
and require refusal when `SOURCE.Table` does not resolve"* -- R28.3 did the second
half and the first was never done. R52.4 found that the runtime's lock provider emits
`SELECT <alias>` while nothing says who opens the area. Both are answered by saying
what a document's data references mean.

This is the lane's first unit in eleven rulings that touches the **deliverable**
rather than the runtime.

## 1. Measured, not designed: 159 `ControlSource` occurrences across 170 forms

```
forms read : 170 of 170
ControlSource occurrences: 159
  alias.field                        145  91.2%   'books.desc'
  empty                                8   5.0%
  more than one dot                    4   2.5%   'This.Parent.SysTray1.Tiptext'
  bare field                           2   1.3%   'product_id'
```

VFP writes the value **quoted** in the designer record -- `"books.desc"`. `BINDING`
holds it unquoted; the quotes belong to the container, not the value. The importer
already stripped them, and the contract had never said so.

## 2. R53.1 -- the form is `alias.field`

`alias` must name an `Alias` declared in `SOURCE`. Resolution is case-insensitive,
matching `Table` resolution in section 10. Empty is legal and means unbound.

Contract section 3's field table said only *"data field this control reads and
writes"*. `manifest.py` had been enforcing `alias.field` since it was written --
**the implementation was the specification**, which is exactly the complaint gate 11
made about this document.

## 3. R53.2 -- a bare field name is refused, by a rule already in the contract

`product_id` means "the field of whatever work area happens to be current". Section
10 already refuses that reasoning for `Table`: *"never a bare name resolved against
ambient state."* One rule, applied twice. 2 occurrences in 159, and both would have
rendered against whichever table the frontend happened to have selected.

## 4. R53.3 -- an object reference is refused for a different reason, and the reason matters

`This.Parent.SysTray1.Tiptext` binds a control's property to **another control's
property**. It is not a malformed `alias.field`. It is a kind of thing UIDEF v1 does
not model.

Three ways to handle it, in increasing order of honesty:

| | what the author is told |
|---|---|
| silence | nothing -- the control renders unbound and no one knows why |
| `not alias.field` | "you made a typo" -- about a feature they used correctly |
| `object reference, not a data binding -- outside v1` | the truth |

**Until this ruling it was the first one.** `bind_check` split on the first dot, took
`This` as an alias, missed the lookup, and `continue`d past a comment reading
`# already refused above` -- which was true only for aliases that WERE declared. A
binding naming an undeclared alias was skipped in silence, and 4 of the corpus's 159
took that path.

Four refusal reasons are now distinct, and exercised rather than asserted:

```
REFUSE  BINDING This.Parent.SysTray1.Tiptext on T2   object reference, not a data binding -- outside v1
REFUSE  BINDING product_id on T3                     bare field name; not alias.field, and the current work area is ambient state
REFUSE  BINDING ghost.field on T4                    alias ghost is not declared in SOURCE
REFUSE  BINDING books.nosuchfield on T5              field not in the schema
```

## 5. R53.4 -- the work areas are open before the first handler fires

> A conforming frontend opens every `Alias` declared in `SOURCE` into its own work
> area, resolving `Table` per section 10, **before it fires any handler**. A `Table`
> that does not resolve is refused there -- not at first use, when a handler is
> already mid-flight.

R47.2 defined the acquire sequence as `SELECT <alias>` + `LOCK TABLE`. R48 gave it
granularity, R49 moved it into both runtimes. All three presumed an open area and
none of them said so. The gap surfaced only because a harness of mine opened two
tables into one work area (R52.4), silently replacing the first -- after which
`UNLOCK TABLE` released a lock the process did not hold, reported success, and left
the lock it did hold standing.

**Refusal belongs at open time, not at use time.** A handler that discovers its table
is missing is already inside a lock domain, has a scope, and may have a completion
queued; refusing there means unwinding. Refusing before the first handler fires means
refusing a document, which is what section 6's requiredness rules are for.

## 6. Evidence tier

**source-evidenced** for the corpus measurement (170 forms read, deleted records
skipped) and **runtime-proven** for the four refusal reasons, which were run against
a synthetic manifest exercising each branch. R53.4 is **planned**: no frontend opens
its areas yet, because none of them opens areas at all -- the backends render and the
runtime locks, and the `USE` has always been the harness's job.

## 7. Still open

- **Nothing implements R53.4.** It is a rule with no code behind it. The Tk and wx
  backends never issue `USE`, and until one does, the lock provider's `SELECT` works
  only because a test opened the areas for it.
- **`Order` is in section 10's example and defined nowhere.** Visible in the sample
  block, absent from the prose.
- **Gate 11's other three fixes** -- the `FONT` row's properties, the grid wrap rule
  in prose, and the menu structure keys -- remain untouched since R28. The `FONT`
  row's keys are `Name`, `Size`, `Metrics`; all four backends read `name` and `size`
  and none reads `Metrics`. That is one measurement away from being fix 1.
- **`ORIGIN_SCALE` conversions**, gate 11's fix 5, is an owner decision.

## 8. Good Neighbor note

- **What changed.** `docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md`: section 3's
  `BINDING` row now points at a new **section 10b**, which defines the syntax, the two
  refusals, and the open precondition. `gui/uidef/manifest.py`: four distinct
  refusal reasons where there were two and a silence.
- **Whose area.** AIF-120's own -- the contract and the manifest tool are both this
  lane's. No engine source was read or touched in this ruling.
- **What authorization.** Maintainer (member.derald), standing in-session; R52.4
  named this the next unit.
- **How to verify or undo.** Verify: the corpus scan is reproducible against
  `~/mnt/vfp-corpus` with the reader at `tools/vfp/read_vfp_binary.py`; the four
  refusals can be exercised by calling `manifest.bind_check` with one binding of each
  shape. Undo: section 10b is additive prose; reverting `manifest.py`'s branch
  restores the silent skip, which is the behaviour this ruling exists to end.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_DESIGN_TABLE_CONTRACT_V1.md
git add gui/uidef/manifest.py
git add docs/maintenance/AIF120_BINDING_SYNTAX_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R53 -- BINDING gets a syntax measured from the corpus, and SOURCE's work areas get an owner"
```
