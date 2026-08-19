---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-029
  recorded_at_utc: 2026-08-19T09:45:00Z
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
    baseline_commit: bf2da2852
  authorization:
    requested_by: maintainer (member.derald), in-session, "I just woke up an hour ago ---
      go go go!" -- taking the third item in the queue: R20.1's own gap, where the
      importer still produced host items with an empty handler.
  report:
    path: docs/maintenance/AIF120_CAPABILITY_MAPPING_V1.md
    kind: ruling
---

# AIF-120 -- R22: a capability mapping is a translation, and refusal is an outcome

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R20 decoded `OBJCODE = 78` and gave `DISPATCH` a third value, `host`. R20.1 then
recorded the gap R20 left open in my own importer:

> this is 21 of 67 items (31%) -- an importer treating them as ordinary items
> produces a menu whose Edit family silently does nothing.

That gap is now closed at both ends: the importer maps them, and a real target
consumes them. Closing it produced four clauses.

## 1. The accounting, both fixtures

`tools/uidef/import_mnx.py` now reports every item's disposition, because an item
that leaves the importer with neither a handler nor a named reason is the silent
failure itself.

| fixture | mapped | unmapped | nameless | named separators |
| --- | --- | --- | --- | --- |
| `test_main.mnx` | **18** | 0 | 0 | **3** |
| `test_go.mnx` | 0 | 0 | 0 | 0 |

18 + 3 = 21, which is the `OBJCODE = 78` count R20 measured. Nothing is
unaccounted for, and the nine `OBJCODE = 77` openers are excluded by name rather
than by silence -- R18 already says an opener's behaviour *is* opening its
submenu.

## 2. R22.1 -- a translation table needs an independent witness

R20.2 required the vocabulary to be the DSL's rather than VFP's: `_med_slcta` is
not a portable identifier, `edit.select_all` is. That is right, and it also means
every row of the table is a translation I made up, in a file no measurement
checks.

So the table is checked against the one independent witness in the record: **the
item's own caption.** Every word of the caption must appear in the capability
identifier, or the rename must be declared on purpose in a `RENAMED` table with a
reason.

It caught a real error on its first run. I had mapped `_mtl_browser` to
`tools.data_browser`; the caption is **"Class Browser"**, and VFP's `_mtl_browser`
is the Class Browser, not `BROWSE`. The check named the missing word:

```
CAPTION MISMATCH -- capability may name the wrong thing:
  I055 'Class Browser' -> tools.data_browser (missing class)
```

The negative test in the evidence transcript re-introduces the wrong mapping on
purpose, so the guard is proven to fire rather than merely present. Four renames
are declared deliberately: `program.run` (VFP spells it `DO`), `window.rotate`
(VFP spells it `Cycle`), and the two joined identifiers `edit.find_again` and
`edit.select_all`.

This is R13's `RESERVED2` principle turned on a file I wrote myself: a claim that
can be checked should be checked.

## 3. R22.2 -- a named host resource is not necessarily a command

Three of the 21 are `_med_sp100`, `_med_sp200`, `_med_sp300`: named host resources
whose `PROMPT` is `\-`. They are separators. **Being a named host resource is an
identity, not a promise of behaviour**, and a separator takes no capability.

Getting this wrong is not harmless in either direction. Assigning them a
capability puts three items into the refusal report that belong nowhere, which is
what the first version of this importer did -- it reported "3 unmapped" and they
were not unmapped, they were separators.

## 4. R22.3 -- an unmapped host resource enters a reserved namespace

A host resource with no DSL name imports as `unmapped.<vfp name>` rather than as a
plain item. No target can claim to provide anything in that namespace, so R20's
refuse-and-name rule fires with **no special case in the consumer**.

Stated honestly: this is a design decision, not a measured finding. The corpus
produced **zero** unmapped resources, so the path is implemented and unexercised
by real data. It is here because the alternative -- import it as an ordinary item
-- is the exact failure R20.1 named.

## 5. R22.4 -- refusal is a first-class outcome, and it must be visible

`tools/uidef/uidef_tk_host.py` is the consumer half: a real capability table for
Tk, and a real refusal for everything Tk does not have. Tk is a fair test because
the split is the backend's, not mine -- it genuinely provides clipboard editing on
a `Text` widget through virtual events, and genuinely has nothing resembling
`program.run` or `window.arrange`.

| | n | capabilities |
| --- | --- | --- |
| provided, wired to real behaviour | **7** | `edit.undo`, `edit.redo`, `edit.cut`, `edit.copy`, `edit.paste`, `edit.clear`, `edit.select_all` |
| **refused and named**, item disabled | **11** | `edit.find`, `edit.find_again`, `edit.replace`, `program.run`, `program.cancel`, `program.resume`, `program.suspend`, `program.compile`, `tools.class_browser`, `window.arrange`, `window.rotate` |

And they do the work. Exercised on the live widget:

```
edit.cut   -> 'WORLD'          (from "HELLO WORLD", "HELLO " selected)
edit.paste -> 'WORLDHELLO '
edit.undo  -> 'WORLD'
```

Three of the seven are exercised, not all seven -- `copy`, `clear` and
`select_all` are wired and unclicked.

`docs/maintenance/evidence/AIF120_host_caps.png` is the Edit menu posted: seven
live items with their accelerators, three greyed and labelled
`[no host capability: edit.find]`, and the separators in their measured positions.

**The headline is the ratio.** A real target refused **11 of 18** -- 61% -- and the
menu is still correct. That is what makes `host` the most portable dispatch value,
and it is not because support is universal. It is because refusal is an outcome
the format anticipates. A target that provides nothing but clipboard editing still
produces an honest menu; the user sees which commands this host does not have
instead of clicking seven dead items.

R7 said a control that binds to nothing must not render as an ordinary empty box.
R22.4 is the same rule for behaviour: **an item whose capability is absent must not
render as an ordinary live item.**

## 6. What this changes

- No new column, again. `DISPATCH = host` plus a capability identifier in
  `HANDLERS` carried all of this. Two rulings running, no schema change.
- The importer gains an accounting line and a caption guard.
- `tools/uidef/uidef_tk_host.py` is new: the reference consumer for `host`.

## 7. A defect in my own render, caught by looking at it

The first render of `uidef_tk_host.py` drew every label with literal double
quotes -- `"Undo"`, `"CTRL+Z"`. I had reimplemented `parse_props` in the new file
and left out the quote strip that `uidef_tk.py` has had all along. The committed
renderer was never wrong; the new one was, for one run.

Worth recording because of how it was found: not by a test, by opening the
screenshot. Five earlier renders in this lane were checked the same way and were
clean, which is the only reason I noticed this one was not.

## 8. Still open

- **The refusal report is per-render, not per-document.** A target cannot ask "will
  this menu work here?" without building it. A capability manifest -- the set of
  capabilities a document requires -- would answer that before a window exists.
  Not built.
- **Capability arguments.** `edit.find` plainly needs a search term and
  `program.run` needs something to run. Every capability here is nullary. The
  corpus does not settle it, because VFP's host items carry no arguments either.
- **One backend.** Tk's 7-of-18 is one data point. The wx side of the tree would
  give a second, and the ratio is the interesting number.

## 9. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Explicit paths only; no `git add -A`. Review before staging -- the author does not
self-approve. `AIF120_host_caps.png` is a render, and PNG evidence has passed the
data-fixtures gate in this lane before.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_CAPABILITY_MAPPING_V1.md
git add docs/maintenance/evidence/AIF120_hostcaps.txt
git add docs/maintenance/evidence/AIF120_host_caps.png
git add tools/uidef/import_mnx.py
git add tools/uidef/uidef_tk_host.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git add coordination/active_sessions/COWORK-20260818-001.yaml
git diff --cached --stat
git commit -m "AIF-120: R22 -- host capability mapping closed; a translation table gets a caption guard, refusal is a visible outcome"
```
