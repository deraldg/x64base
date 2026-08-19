---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-077
  recorded_at_utc: 2026-08-20T22:15:00Z
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
    baseline_commit: 8145e0880
  authorization:
    requested_by: maintainer (member.derald), in-session "yahoo, go for it cowboy",
      answering R68 section 4's costed plan. This ruling edits src/cli/, which is
      outside AIF-120 -- see the Good Neighbor note.
  report:
    path: docs/maintenance/AIF120_TUPLE_STREAM_RECNO64_V1.md
    kind: ruling
---

# AIF-120 -- R69: the tuple stream goes pure 64, and the widening found three defects the width was hiding

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R68 costed the work at four files and twenty declarations. That was right about the
size and wrong about the nature: **this was not a widening exercise. Three of the
narrow types were load-bearing, and two of them were broken already.**

## 1. R69.1 -- the stream could not position on an x64 table at all

`src/cli/db_tuple_stream.cpp`, the helper every navigation path goes through:

```cpp
long safe_rec_count(xbase::DbArea* A) {
    try { return static_cast<long>(A->recCount()); }        // <-- the 32-bit adapter
    ...
bool goto_rec_safe(xbase::DbArea* A, long r) {
        if (r < 1 || r > static_cast<long>(A->recCount())) return false;
```

`recCount()` is the **signalling** narrow accessor. Past `INT32_MAX` it returns
**-1** on purpose -- xbase.hpp's rule, and R63 proved its value. So on any table
past 2^31 the bound check reads `r > -1`, which is true for every record, and
`goto_rec_safe` returns **false for everything**. `max_recno_` becomes -1 as well,
so `refresh_bounds_only` clamps the cursor to -1.

**The Smart Browser and every tuple cursor were inert on exactly the tables the
RECNO64 lane exists to serve** -- not wrong, not truncated, simply unable to move.
Now `recCount64()` and `gotoRec64()`.

This is the R3 rule violated from the consumer side: the accessor did its job and
signalled, and the caller treated the signal as a count. **A signal only works if
someone reads it as one.**

## 2. R69.2 -- the index held the right number and the stream threw the top bits away

```cpp
if (rn64 > 0 && rn64 <= static_cast<uint64_t>(recCount)) {
    out.push_back(static_cast<uint32_t>(rn64));      // <-- 64-bit read, 32-bit store
}
```

`collect_lmdb_cdx_recnos` reads a full 64-bit record number out of the x64 CDX/LMDB
index -- which stores them at full width, RECNO64 M3c -- and narrowed it into a
`uint32_t` order vector. Silently, and on **both** platforms, so no build was safe.

The proof run makes the consequence concrete:

```
narrow ceiling 4294967295; refused 4294967296 (the old path would have stored 0)
```

**2^32 truncates to 0, and 0 is the engine's own "no current record"** (`bof()` is
`_crn64 == 0`). The truncation did not merely name the wrong row; it produced the
value that means *no row*.

## 3. R69.3 -- the browser's cursor restore (R67.3, now fixed)

`app_smart_browser.cpp` snapshotted every open work area's cursor as `int32_t` via
`recno()` and restored it under `if (recno <= 0) continue;`. Past 2^31 `recno()` is
-1, the guard fires, and the browser **silently does not restore the cursor it
promises to preserve** -- after which the relations refresh re-syncs every child to
wherever the browse left the parent. Now `recno64()` / `gotoRec64()`, with the guard
narrowed to `== 0`, which is the engine's real "no current record" and no longer
doubles as the overflow signal.

## 4. What was built

| file | change |
|---|---|
| `src/cli/tuple_types.hpp` | `RecordNo` = `uint64_t`, `RecordDelta` = `int64_t` (RECNO64 plan item 1); `TupleFragment::recno` widened from `int` |
| `src/cli/tuple_stream.hpp` | `skip(RecordDelta)`; **`goto_record(RecordNo)` added** -- BETA-6.1 freezes GOTO for tuple iteration and the interface had none, so a second implementation was not required to provide it; `max_record_number()` / `record_number_fits()` |
| `src/cli/db_tuple_stream.hpp` | 13 `long` -> `RecordNo`/`RecordDelta`; new `OrderVec` |
| `src/cli/db_tuple_stream.cpp` | R69.1, R69.2; signed-then-range-check arithmetic in `step()` |
| `src/cli/app_smart_browser.cpp` | R69.3; `stoll` not `stol` in the pager's own SKIP/GOTO |
| `src/cli/tuple_builder.cpp` | R69.4 -- `safe_recno` and the buffer-override key |
| `src/cli/cmd_ersatz.cpp` | R69.4 -- three recno helpers and R69.3's third instance |
| `src/tuple/tuple_cell_adapter.cpp` | R69.4 -- the one explicit, signalling narrow into `dt::data::Cell` |
| `src/tests/test_tuple_stream_order_capacity.cpp` | new; registered in `src/tests/CMakeLists.txt` |

**The trinity is untouched.** `gotoRec64`, `recno64`, `recCount64` already existed;
`include/` has no diff.

### Pure 64 -- the owner's ruling, and what it replaced

The first version of this made the order vector a **two-width variant**: narrow
`uint32_t` backing chosen once from the resolved count, wide above `UINT32_MAX`,
with `push()` refusing rather than truncating. That was R68 section 4's design and
it was M4-4's shape one layer up.

**The owner ruled pure 64.** The vector is `std::vector<RecordNo>`, with no width to
select, mis-select, or forget to widen. It costs 22 MB extra on a pinocchio-scale
ordered browse and removes a second code path in exchange. What the variant was
protecting against -- silent truncation -- is now **impossible rather than refused**,
which is the better kind of guarantee.

**32-bit tables are still fully supported, and nothing about them changed.** A
classic CNX or `.inx` still stores four-byte record numbers and still loads through
a `std::vector<uint32_t>`, because that is what the *format* holds; it widens on the
way in. What is gone is a 32-bit representation of a record number anywhere *inside*
the stream.

`order_pos_` moved from 0-based-with--1-sentinel to **1-based-with-0**. An unsigned
identity has no room for -1, and 0 was already free -- which removed the position
adjustment that four separate call sites were each doing by hand.

### The bottlenecks, named

Widening moves cost around rather than removing it. Three places to watch:

1. **The order vector itself** -- 2x memory for an ordered browse: ~44 MB at
   pinocchio's 5,501,358 rows. This is the cost the owner accepted.
2. **The reserve hint in `collect_lmdb_cdx_recnos`** -- the first place a wide count
   becomes an allocation. The old line clamped the *lower* bound
   (`std::max(0, recCount)`) against a signed int; with an unsigned count the bound
   that matters is the upper one, so it is now capped at 4 Mi entries (32 MB) and
   grows from there if the data warrants.
3. **`order_find_pos` is a linear scan**, so an ordered `GOTO <recno>` is O(n) --
   5.5M comparisons at pinocchio scale. This is **pre-existing** (it was
   `std::find` over the same vector) and unchanged here, but it is the one that
   will show up first under load, and it is worth a sorted side index or a hash if
   ordered GOTO ever becomes hot.

## 5. Correction 48 -- I verified a build that excluded the bug I was fixing

**The maintainer's MSVC build failed, and it was right to.** Three errors and three
warnings, none of which my container had seen:

```
db_tuple_stream.cpp(165,9):  error C2039: 'reserve': is not a member of 'OrderVec'
db_tuple_stream.cpp(165,47): error C2672: 'std::max': no matching overloaded function
db_tuple_stream.cpp(562,18): warning C4245: conversion from 'int' to 'RecordNo',
                             signed/unsigned mismatch          [and 569, 575]
```

Two causes, and both are mine.

**(a) The LMDB block is behind `#if DOTTALK_WITH_INDEX` and my container has no
`lmdb.h`, so I compiled the `#else` stub and called it clean.** The failing line 165
is inside that block -- which is *the same block containing R69.2, the truncation
this whole ruling exists to fix*. I verified eleven translation units against a
configuration that excluded the defect. That is correction 39's shape returning:
code that builds on exactly one machine, reported as if it built. Fixed by
installing `liblmdb-dev` and compiling with `-DDOTTALK_WITH_INDEX=1`; **an `#if` I
did not check the state of is not a translation unit I compiled.**

**(b) `-Wall -Wextra` does not warn on signed-to-unsigned assignment; MSVC's C4245
does.** Three `order_pos_ = -1;` assignments in `set_order_physical/inx/cnx` --
setters I never read, because I had followed the *navigation* path and stopped.
gcc took them silently. `-Wsign-conversion` catches them, and both changed files are
now clean under it.

## 6. What I verified this time

- `-Wall -Wextra` **and** `-Wsign-conversion` clean on both changed translation
  units, **with `-DDOTTALK_WITH_INDEX=1`** so the LMDB block actually compiles.
- All 11 `.cpp` files including the tuple headers still compile; the only warnings
  are pre-existing ones in other people's code (`cmd_ersatz` range-loop copy,
  `app_smart_browser` misleading-indentation at lines 189/253/303, all at HEAD).
- The test builds and passes:

```
recno 4294967296 survives; narrowed it would have been 0 (bof)
order vector is pure 64: 4294967296 and 4294967303 distinct,
classic range intact, 1-based find. PASS
```

**`REGRESSION ALL` is green** on build `5246809f`, 2026-08-19. The suites that
matter, and what each one actually exercised:

| suite | what it proves about this change |
|---|---|
| **INDEX_X64** | the rewritten `collect_lmdb_cdx_recnos` end to end -- CDX attach, `SET ORDER TAG LNAME`, ordered SMARTLIST, SEEK/FIND/LOCATE, tag switch to SID, `BUILDLMDB` on a fresh 2-tag container, mutate an indexed field then `SEEK` -> `Found at 205`, restore -> `Found at 1`, clear to physical |
| **INDEX_X32** | the CNX and legacy `.inx` paths, which now load through a `uint32_t` temporary and widen on the way in -- ordered traversal, SMARTLIST under two tags, `SEEK` -> `Found at 12` / `Found at 2`, INDEX/REINDEX, ASC/DESC, clear |
| **NONDESTRUCTIVE** | the full shell surface over a 12-area x64 workspace, including `LOCK`/`UNLOCK`, cursor movement, and CDX order attach/switch/clear |
| **X64_METRICS** | both structural barrier cases, unchanged |
| **LANGUAGE, DOTSCRIPT_EXPR, DOTSCRIPT_PARITY, LEXING** | every marker `.T.` / `PASS` |

**The strongest single result is a comparison, not a pass.** `INDEX_X64`'s ordered
listing is byte-identical to the pre-change baseline in the maintainer's own
`REGRESSION ALL` transcript -- the same seven blank-`LNAME` rows at recno
205/206/211-215 sorting first, then Anderson at 78/83/85. The order vector returns
the same rows in the same order after going pure 64, which is what a widening is
supposed to do and what a truncation would not.

## 6b. R69.4 -- the widening's own regression, found by the C4244 warnings

**The maintainer's build succeeded, and its three remaining warnings were the
important part.** `C4244: conversion from 'const dottalk::RecordNo' to 'int'` at
`tuple_cell_adapter.cpp` (twice) and `cmd_ersatz.cpp:1540`. Following them up the
vertical found the defect I had created:

```cpp
// src/cli/tuple_builder.cpp -- the SOURCE of every TupleFragment::recno
int safe_recno(const xbase::DbArea* A) {
    try { return static_cast<int>(A->recno()); } catch (...) { return 0; }
}
```

It reads `recno()`, so past `INT32_MAX` it produced **-1** -- correct, visible, and
exactly what xbase.hpp's rule intends. **I widened `TupleFragment::recno` to an
unsigned `RecordNo` without widening its producer, so that -1 became
18446744073709551615.** A signal turned into a plausible-looking record number,
which is the precise failure mode `-1` was chosen to prevent.

**Widen the producer or do not widen the field.** Nothing in between is safe, and
the compiler only pointed at it because the *consumers* narrowed back down.

Fixed at the source (`recno64()`), and four more of the same family with it:

| site | was | now |
|---|---|---|
| `tuple_builder.cpp` `safe_recno` | `int` from `recno()` | `RecordNo` from `recno64()` |
| `tuple_builder.cpp` `get_buffer_override(int recno, ...)` | `int` key into a `uint64_t` change map | `RecordNo` |
| `cmd_ersatz.cpp` `safe_area_recno` / `ersatz_recno_safe` | `int` / `long` from `recno()` | `RecordNo` from `recno64()` |
| `cmd_ersatz.cpp` `tuple_row_recno` | `int` | `RecordNo` |
| `cmd_ersatz.cpp` cursor restore | `gotoRec(size_t)` under `> 0` | `gotoRec64` -- **R69.3's defect, third instance** |

`dt::data::Cell::recno` stays `int`, deliberately: widening it reaches the row
codecs, cell validation and browse edit, which is a different vertical. So the
narrowing happens **once, explicitly, in `cell_recno_narrow()`, and it signals** --
returning `-1` past `INT32_MAX`, the same value and the same reason as the engine's
own 32-bit adapters, into a field documented as "1-based recno, if known" where 0
means unknown and -1 was free.

Everything above is clean under `-Wall -Wextra -Wconversion -Wsign-conversion` with
`-DDOTTALK_WITH_INDEX=1`. The only warnings left in these files are pre-existing at
HEAD and unrelated to record numbers (`-Wmisleading-indentation`,
`-Wrange-loop-construct`, and a `directory_entry` index in `cmd_workspace`).

## 7. Correction 47

`-Wall -Wextra` caught one of mine: `if (order_pos_ < 0)` left on a value I had just
made unsigned -- *"comparison of unsigned expression in '< 0' is always false"*. A
dead guard, and it sat directly in front of `next_page`'s positioning.

That is the shape of every defect in sections 1 to 3 as well. **A width change turns
live guards into dead ones silently, and the compiler only tells you when the sign
changes** -- it said nothing about `r > -1`, because that comparison is perfectly
well-formed and merely wrong.

## 8. Deliberately not done

- **`browse_order.hpp`'s `std::vector<uint32_t>` and `goto_recno(DbArea&, uint32_t)`
  are unchanged.** They serve CNX and legacy `.inx`, which M4-4 decided stay 32-bit.
  Widening them would state a capacity those formats do not have.
- **`include/tuple/tuple_graph_cursor.hpp` still has `int` recnos**
  (`first_root_recno`, `last_root_recno`, `root_skipped_*`). They are diagnostics
  counters, not the positioning path. Reported, left alone: the house's own word for
  the right approach is a *vertical*, not a sweep.
- `app_smart_browser.cpp` carries one pre-existing non-ASCII character (an em dash,
  line 266). It is at HEAD, it is not mine, and fixing it would be an unrelated edit
  inside someone else's file.

## 9. Evidence tier

**runtime-proven.** The order vector's 64-bit behaviour by the new unit test; the
whole change by `REGRESSION ALL` green on the maintainer's MSVC build, with
`INDEX_X64`'s ordered output byte-identical to the pre-change baseline.
**source-evidenced** for R69.1, R69.2 and R69.3 -- each is a quoted line with the
mechanism spelled out, and R69.3 was measured in R67.3.
**planned** for the change as a whole **until the maintainer links and runs
`REGRESSION ALL`**. Compiling eleven translation units is a syntax check.

## 10. Still open

- **Nothing in the suite has a table past 2^31.** So R69.1 and R69.2 are proven
  *correct* by the regression -- ordered traversal, seek and index maintenance all
  behave exactly as before -- and proven *at the boundary* only by construction plus
  the unit test. The end-to-end boundary proof still wants an ordered browse over a
  sparse >2^31 table, which needs an index over one; that is more than
  `test_recno64_sparse_e2e.cpp`'s sparse hole and is the honest remaining gap.
- **`include/xbase.hpp`, `include/xbase_vfp.hpp` and `include/xbase_64.hpp` are
  byte-identical to HEAD** -- verified by md5 against `git cat-file`, not asserted.
  The trinity was not touched and did not need to be.
- **A boundary test with a real table.** `test_recno64_sparse_e2e.cpp` builds a
  sparse x64 table past 2^31 with `create_dbf`; the equivalent for an ordered browse
  over one would prove R69.1 and R69.2 end to end rather than by construction. It
  needs an index over that table, which is more than a sparse hole.
- Unchanged: R67's open items (nothing constructs a stream from a UIDEF document
  yet), R64.1, R64.2, R65.3, R65.4, R55.2, R62.2.

## 11. Good Neighbor note

- **What changed.** Five files in `src/cli/`, one new file in `src/tests/`, and its
  registration in `src/tests/CMakeLists.txt`. **`include/` is untouched** -- the
  trinity already exposed everything needed.
- **Whose area.** `src/cli/` is **not** AIF-120's, and this is the first time this
  lane has edited it. Every change is confined to the tuple-stream vertical named in
  RECNO64's own plan item 3 (*"SmartList/browsers, tuple + relation cursors"*), and
  no lock, buffer, index or command surface was touched.
- **What authorization.** Maintainer (member.derald), in-session *"yahoo, go for it
  cowboy"*, directly answering R68 section 4's costed plan. Recorded explicitly
  because the authorization is what makes a cross-area edit legitimate, and a
  cheerful one is still one.
- **How to verify or undo.** Verify: build, then
  `ctest -R dottalkpp_tuple_order_capacity_test`, then `REGRESSION ALL`, then a
  Smart Browser session over an ordered x64 table. Undo: the six files revert
  together; `include/` needs nothing reverted.

## 12. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

R65 through R68 are still uncommitted; their blocks are in their own documents.
**Build and run the regression before committing this one** -- section 5 says why.

```powershell
cd D:\code\ccode
git add src/cli/tuple_types.hpp
git add src/cli/tuple_stream.hpp
git add src/cli/db_tuple_stream.hpp
git add src/cli/db_tuple_stream.cpp
git add src/cli/app_smart_browser.cpp
git add src/cli/cmd_ersatz.cpp
git add src/cli/tuple_builder.cpp
git add src/tuple/tuple_cell_adapter.cpp
git add src/tests/test_tuple_stream_order_capacity.cpp
git add src/tests/CMakeLists.txt
git add docs/maintenance/AIF120_TUPLE_STREAM_RECNO64_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R69 -- tuple stream goes pure 64; it could not position past 2^31, the CDX order vector truncated recnos to 0, and widening a field without its producer turned a -1 signal into 1.8e19"
```
