---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-040
  recorded_at_utc: 2026-08-19T13:20:00Z
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
    baseline_commit: 564747371
  authorization:
    requested_by: maintainer (member.derald), in-session, "methods should inherit" --
      R31's first open item, decided by the owner.
  report:
    path: docs/maintenance/AIF120_METHOD_INHERITANCE_V1.md
    kind: ruling
---

# AIF-120 -- R32: handlers inherit, and the event vocabulary was missing nine names

Status: **ruling, review-needed.** Owner: member.derald -- **and the owner decided
this one.** Author: member.ai.claude.cowork, run `COWORK-20260818-001`. 2026-08-19.

R31 recorded its own gap: *"Methods are not inherited. R14 keeps bodies out of v1,
so a class's `METHODS` are ignored entirely. A handler reference defined only on a
class is therefore lost, and nothing counts it."* The owner ruled that they should
inherit.

## 1. R32.1 -- what inherits is the reference, never the body

R14 stands: the table carries a handler **name**, resolved by the target against a
registry it supplies. Nothing is evaluated and no body enters the table. What R32
adds is that a name defined on a class reaches the instance.

Two paths, both implemented in `gui/uidef/import_scx.py`:

- **A class member's handlers** ride with the member when R31 materialises it.
- **The class root's handlers** merge into the instance, and **an event the
  instance defines itself wins.** An override replaces; everything else inherits.
  That is what an override means, and it is checkable rather than assumed.

Measured across the corpus: **788 event handlers inherited**, and rows carrying any
`HANDLERS` rise to **1,047**.

## 2. R32.2 -- section 9's event list was missing nine standard events

Implementing this surfaced a defect in the contract, not in the code. Splitting
what a class defines into "events section 9 names" and "everything else" produced a
list where the second group was not what it claimed:

| name | occurrences | what it is |
| --- | --- | --- |
| `Unload` | **72** | a standard VFP form event |
| `MouseMove`, `MouseDown`, `MouseUp` | 9 | standard |
| `KeyPress`, `DblClick` | 6 | standard |
| `DragOver`, `DragDrop` | 4 | standard |
| `Valid` | 1 | standard |
| `addtopath`, `recordpointermoved`, ... | 136 | genuinely application-defined |

**Nine standard events, 92 handlers, silently discarded** because section 9's list
had ten names and the format has more.

`Unload` is the one that matters. Section 9 carries `Load` and not `Unload` -- it
names the setup event and drops the teardown one. **R21 spent an entire ruling on
teardown**, on destroying a container while work is in flight, and the format's own
teardown event was not in the vocabulary the whole time.

> **R32.2.** The event vocabulary gains `Unload`, `MouseMove`, `MouseDown`,
> `MouseUp`, `DoubleClick`, `DragOver`, `DragDrop`, `KeyPress` and `Validate`.
> Nineteen events, not ten. **Section 9 of the contract needs the same edit** and
> has not had it yet.

After the addition, inherited handlers rise from 696 to **788**.

## 3. R32.3 -- custom methods are named, not carried, and not invented

136 occurrences across 26 distinct names remain: `addtopath`,
`recordpointermoved`, `enabledisablebuttons`, `beforerecordpointermoved` and
others. These are real behaviour -- a class's own methods, called by its other
methods -- and v1 has **no concept** for them. `HANDLERS` maps an event to a name;
a custom method answers to no event.

They are counted and reported by name at import. They are not mapped onto an event
that happens to look similar, which would be inventing a trigger the source never
declared.

The ratio is worth keeping: a class's behaviour is roughly **as much custom method
as event handler**. A design table that carries only event handlers carries about
half of what a class library actually does.

## 4. Still open

- **Section 9 of the contract is now behind the importer.** The vocabulary is
  nineteen in code and ten in prose. That is exactly the production-versus-
  consumption drift R24 section 4 named, and it should not survive this commit by
  more than a day.
- **Depth one.** A class member that is itself an instance still does not recurse,
  so its own inherited handlers are not reached.
- **No custom-method concept.** Whether v1 should carry a named-behaviour list at
  all is a design question, not an omission to patch.
- **Nothing renders an inherited handler yet.** `dispatch_test.py` exercises
  `HANDLERS` on authored rows; no test fires one that arrived by inheritance.

## 5. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_METHOD_INHERITANCE_V1.md
git add gui/uidef/import_scx.py
git diff --cached --stat
git commit -m "AIF-120: R32 -- handlers inherit from the class; nine standard events restored to the vocabulary, Unload chief among them"
```
