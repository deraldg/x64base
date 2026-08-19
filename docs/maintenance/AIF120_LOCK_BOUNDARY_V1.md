---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-071
  recorded_at_utc: 2026-08-20T07:10:00Z
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
    baseline_commit: 64dedf551
  authorization:
    requested_by: maintainer (member.derald), in-session "continue"; R61 section 5
      left this as the last unproven piece of the lock work.
  report:
    path: docs/maintenance/AIF120_LOCK_BOUNDARY_V1.md
    kind: ruling
---

# AIF-120 -- R63: the lock path holds past 2^31, and the wrong accessor would have been visible on disk

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

R57 chose `a.recno64()` over `a.recno()` from a header comment. R61.5 recorded that
the choice was **well-founded and unproven**, after I built an invalid fixture trying
to test it. This is the run.

## 1. The result

```
recCount64() : 2147483649
recCount()   : -1   <-- legacy signals overflow
gotoRec64(2147483648): recno64()=2147483648  recno()=-1

try_lock_record(recno64()) : ok
is_record_locked(recno64()): yes (vm:30949:1787176256759)

  correct  : /tmp/r63_sparse.dbf.lock.2147483648
  recno()  : /tmp/r63_sparse.dbf.lock.-1   <-- what R57 would have written
```

**The proof is visible rather than inferred.** `xbase::locks` names the lock file
after the record number, so the wrong accessor does not fail quietly -- it writes
`.lock.-1` on disk, one file for every record past 2^31, all colliding. Two handlers
on two different records would have appeared to each other as the same lock.

`recno()` returning `-1` is documented in `include/xbase.hpp` as signalling overflow
rather than clamping, and that is what makes the failure loud enough to see. A
clamping accessor would have produced `.lock.2147483647` and looked plausible.

## 2. Correction 43 -- and it is correction 38 again

The first run printed the owner as empty:

```
is_record_locked(recno64()): yes ()
```

That is R57's correction 38 exactly: `is_record_locked(..., &who)` and `who.c_str()`
as two arguments of one `printf`, whose evaluation order is unspecified, so gcc read
`who` before the call filled it.

**I wrote that up as a lesson four rulings ago and then reproduced it.** Recording
the pattern in a document did not stop me repeating it, which says something about
what documentation is for: it is a record, not a guard. The guard would be a lint
rule or a habit of never calling a function in an argument list whose sibling reads
its out-parameter.

Sixth harness defect in this run, and the second identical one.

## 3. Correction 44 -- the earlier fixture, and why it was wrong

R61.5 built a fixture by patching bytes 4-7 of a VFP-flavour table. Both halves were
wrong, and `src/tests/test_recno64_sparse_e2e.cpp` shows the supported path:

| I did | the engine's way |
|---|---|
| patched the **classic** count at bytes 4-7 | the **64-bit** record_count lives at **file offset 32** |
| on a **VFP-flavour** table | `create_dbf(path, fields, Flavor::X64, err)` |
| computed offsets from a header I read myself | `dataStart64()` and `recLength64()` from the open table |

The result read back as zero records, and I briefly had a finding. This fixture is
built the engine's way and reads back `2147483649`.

**The maintainer's recollection was right and misattributed.** "2 billion + 1" is
`2^31 + 1 = 2147483649` -- the record count in *this* fixture, not pinocchio's.
Pinocchio is 1,000,000 and 5,501,358 rows, dense (R61.6).

## 4. What it cost

```
allocated on disk : 8.0K
logical size      : 19G
```

The gap between record 1 and record 2^31 is a sparse hole. On a filesystem without
sparse-file support the probe would try to allocate 19 GB, which is why the build
line says so.

## 5. Evidence tier

**runtime-proven**, against `libxbase.a` from the current tree, using
`xbase::dbf_create` rather than hand-written header bytes -- which was the
maintainer's point in *"are you building a way to read x64 dbfs or using the api
already built"*.

## 6. Still open

- **The typed provider has not been run at the boundary.** This proves
  `xbase::locks` and `recno64()` agree past 2^31; it does not run
  `uidef::xbase_lock_provider` there. The provider calls `a.recno64()` on the same
  line, so the risk is small and the run has not happened.
- **Record granularity remains unsafe for writing handlers** (R57.2), independent of
  this.
- Unchanged: R55.2, the mutation model (R61.2), R53.4's `USE` (R61.6), the section 13
  query limit (R62.2), pinocchio-scale.

## 7. Good Neighbor note

- **What changed.** New file only: `tools/uidef/lock_boundary_probe.cpp`, with its
  build line and the sparse-file warning in the header comment. No shipped code
  changed.
- **Whose area.** AIF-120's own. The engine was linked against and read; the fixture
  is created in `/tmp` by `create_dbf` and no repository table is touched.
- **What authorization.** Maintainer (member.derald), in-session "continue".
- **How to verify or undo.** Verify: the build line in the header; expect
  `recCount64() : 2147483649`, `recCount() : -1`, and the two lock-file names.
  Undo: the file is a test.

## 8. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add tools/uidef/lock_boundary_probe.cpp
git add docs/maintenance/AIF120_LOCK_BOUNDARY_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R63 -- the lock path holds past 2^31; recno() would have written .lock.-1 for every record"
```
