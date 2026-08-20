---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-082
  recorded_at_utc: 2026-08-20T05:00:00Z
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
    id: project.x64base.gui
    root: D:/code/ccode/gui
  git:
    branch: development
    baseline_commit: ec8a00418
  authorization:
    requested_by: maintainer (member.derald), in-session -- pasted the MCC DTSHEMA
      workspace, then "this is the x32, we want x64 so change cnx to cdx and it
      will match", then "both" to R73 and R74.
    scope: >
      Correct contract section 4c's Order vocabulary and the two tools that
      enforce it. Reads src/ and runs the shipped binary; writes only gui/ and
      docs/. No engine change.
  report:
    path: docs/maintenance/AIF120_ORDER_VOCABULARY_V1.md
    kind: ruling
---

# AIF-120 -- R73: `Order` named an index format the document does not choose, and could name one the table does not have

**Status: review-needed.** The author does not self-approve.

## 0. The one-paragraph version

Contract 4c closed `Order` to `physical | inx | cnx`. Asked to change `cnx` to
`cdx` for x64, I went to check what the setters do and found there was nothing to
change: **`set_order_inx()` and `set_order_cnx()` are byte-identical**, and neither
attaches an index or selects a tag. The engine chooses the index format from the
table itself. Measured across four flavors of the MCC (My Community College) schema, `INX` is **not
available on x64 at all** -- so 4c permitted a document to request a format that
cannot exist for the flavor this lane targets. `Order` becomes `physical |
ordered`; which index and which tag are workspace facts.

**Evidence tier: runtime-proven**, negative half. See section 5 for what is not
proven and why.

## 1. The two setters

`src/cli/db_tuple_stream.cpp`:

```cpp
void DbTupleStream::set_order_inx() {          // 547
    mode_ = NavMode::OrderVector;
    order_pos_ = 0;
    last_emitted_recno_ = 0;
}
void DbTupleStream::set_order_cnx() {          // 553
    mode_ = NavMode::OrderVector;
    order_pos_ = 0;
    last_emitted_recno_ = 0;
}
```

Character for character the same. Neither opens a container, names a tag, or
touches `orderstate`. There are **two navigation modes** -- `Physical` and
`OrderVector` -- and the contract offered three words for them.

Confirmed at runtime against MCC `STUDENTS` (x64, 200 records):

```
RESULT  inx == cnx      : IDENTICAL
        inx == physical : IDENTICAL
```

All three, because no order was active on the area -- which is section 3.

## 2. The format is a property of the table, measured

`WORKSPACE OPEN`'s own usage text:

> Without CNX/INX/CDX, indexes are chosen by DBF flavor: true x64/v128 CDX,
> classic VFP/v32 CNX.

The maintainer's note that the MCC schema is canonical across MS-DOS, VFP and x64
makes that testable rather than quotable. One table, four flavors, engine's own
report at open:

| directory | `DBF Flavor` | `Runtime kind` | `Valid Index/Indices` |
|---|---|---|---|
| `dbf/og` (MS-DOS lineage) | `v32` | `v32` | CNX, INX |
| `dbf/vfp` | `vfp` | **`v64`** | CNX, INX |
| `dbf/x32` | `v32` | `v32` | CNX, INX |
| `dbf/x64` | `v64` | `v64` | **CDX, CNX** |

**`INX` is absent from x64 and `CDX` is absent from the other three.** A UIDEF
document saying `Order = inx` over an x64 table asks for a format the table does
not offer, and 4c called that legal. The document cannot choose the format because
the format is not the document's to choose.

Worth recording: the `vfp` table reports flavor `vfp` and runtime kind `v64`. The
trinity's "one engine API, three capacities" (R68), visible in one line of output.

## 3. The defect this shipped into R70

The shell reports an unattached index and says why:

```
Area 9: opened 'STUDENTS.dbf'  [index: STUDENTS.cdx, found (not attached)]
        (openCdx: LMDB env missing: .../lmdb/x64/STUDENTS.cdx.d)
```

**`found (not attached)`** is exactly the state a UIDEF `Order` produces when
nothing has activated an order, and the engine has a phrase for it. `set_order_*`
returns `void`. So R70's generated grid calls `set_order_cnx()`, receives nothing,
and browses **physical in silence** -- the lane's recurring defect shape, shipped
by me into generated code two rulings ago. `P2_order_ok` emits exactly that call.

The generator cannot fix this; it can only stop pretending. It now emits a comment
recording what was asked for, and R73.1 below is the report.

## 4. The ruling

- **`Order` is closed to `physical | ordered`.** Two modes, because the engine has two.
- **`inx` and `cnx` remain accepted as deprecated spellings of `ordered`**, reported with a `DEGRADE`, never silently equated. The corpus already says them and they were correct when written; a vocabulary correction should not invalidate documents whose authors did nothing wrong.
- **Which index and which tag are WORKSPACE facts.** The house already has the format: a `DTSHEMA 2` row carries `dbf=`, `index=`, `indextype=`, `tag=`, `alias=` per area. The document says *ordered*; the workspace says *by what*. Same split as R72 -- the document owns what, the environment owns which.
- **A reader that cannot confirm the order is active must not imply it did.**

`manifest.py` enforces it (`STREAM_ORDERS`, `DEPRECATED_ORDERS`); `uidef_wx.py`
emits it. `P1_order_bad` still refuses, naming the two-value set; `P2_order_ok`
still binds, with a DEGRADE note.

## 5. What is NOT proven

**That ordered differs from physical.** Every CDX attach in my container failed
with `LMDB env missing` because the copy I hold has `dbf/` and `indexes/` but no
`lmdb/` directory at all; the maintainer's tree has all twelve `.cdx.d`
environments. So the **negative** half is proven -- with no active order, all three
spellings return identical pages -- and the positive half is owed on a tree with
the LMDB sidecars. Stated here rather than implied, because a ruling that proves
only the half it could reach should say which half.

## 6. Reported, not fixed -- other areas

**R73.1 -- `set_order_*` returns void.** `WORKSPACE OPEN` can distinguish
`found (not attached)` from attached, and says so. A frontend asking the stream for
an order gets no answer, so an unattached index is indistinguishable from an
honoured request. A `bool`, or a `current_order_hint()` a caller is told to check,
would let a reader report what the shell already reports.

**R73.2 -- three words for one state, in the house's own output.** `AREA` prints
`Order: NATURAL` with no index and `Order: ASCEND` with one; `ERSATZ` prints
`ORDER: physical`; `DbTupleStream::current_order_hint()` returns `"physical"`. This
ruling adopts `physical` because 4c governs the stream and that is the stream's own
word -- but three spellings of one concept is how a vocabulary drifts.

**R73.3 -- BETA-1.2, third instance today.** The shipped `dottalkpp/data/scripts/x64.dts`
reads `SET PATH DBF DBF/x64`; on POSIX that misses `dbf/x64` and every subsequent
command fails with the tables closed. Also hit on `dbf/og/STUDENTS.DBF`, which
opens fine once the case matches. Windows hides it completely.

**R73.3a -- and that script is not tracked.** The `cited-paths` gate flagged this
ruling's citation of `x64.dts` as a WIDOW: on disk, not in the repository. Measured
rather than assumed, the directory it lives in is
**96 of 135 `.dts` files untracked** -- including `x64.dts` itself, which every x64
session runs as `do x64`, and the MCC regression canaries. A fresh clone does not
have them.

Two consequences, and the second is the one that matters. The citation above is
honest but unresolvable for any reader who cloned; and the defect in R73.3 cannot
be fixed by such a reader either, because they do not have the file to fix. This
is R42's lesson at directory scale -- *a green gate is evidence about what was
STAGED* -- and `REGRESSION_CANARY_INVENTORY_v1.md` has been carrying the same
widows against `data/scripts/canaries/*.dts` for some time.

**Deliberately not fixed here.** `data/scripts` is another lane's area and shipped
scripts are report-only unless a task names them. The recommendation is to stage
`x64.dts` at minimum -- it is referenced by name in house documentation and by
every x64 session -- at which point this ruling's citation resolves by itself and
no suppression marker is needed. A `cite-check:ignore` here would hide exactly the
signal the gate exists to raise.

**R73.4 -- `TUPLE` over a closed area prints `"" | ""`.** No error, no refusal --
a row of empty strings that reads like data. Minor, and the same shape as
everything else in this ruling.

**R73.5 -- a SIGFPE I am NOT calling an engine defect.** Calling
`orderstate::setOrder` + `setActiveTag` directly -- the pair
`SchemaWorkspace::apply_to_runtime` uses -- crashed with a floating-point exception
on the missing-LMDB condition the shell guards. My harness skipped `cmd_INIT` and
the path setup, so this is a reproduction, not a verdict. It is recorded because a
SIGFPE is a crash whoever called it, and because the call pair is the workspace
loader's own.

## 7. Good Neighbor

| | |
|---|---|
| What changed | `gui/uidef/manifest.py` (`STREAM_ORDERS`, `DEPRECATED_ORDERS`), `gui/uidef/uidef_wx.py` (emission), contract 4c, ledger rows |
| Whose area | AIF-120. `src/` read only |
| Authorization | maintainer, in-session: "change cnx to cdx"; then "both" |
| How to verify | `python gui/uidef/manifest.py` on `P1_order_bad` (refuses) and `P2_order_ok` (degrades); `DOTSCRIPT aif120/flavors.dts` for the four-flavor table |
| How to undo | `git revert`. No-`--stream` output is byte-identical before and after |
| Risk | low. One vocabulary narrowed, both old spellings still accepted |
