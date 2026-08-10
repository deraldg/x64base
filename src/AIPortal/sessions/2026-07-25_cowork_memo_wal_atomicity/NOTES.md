# NOTES -- AIF-061 M1

## Why this is a package and not a commit

`member.ai.claude.cowork` holds `role.ai_partner`: `source.propose`, never `source.mutate`. This
change is in the commit durability path -- the code that decides whether data survives a crash --
which is precisely the case that boundary exists for. Delivered under the Outside-AI Delivery Rule at
maintainer instruction.

The agent did not edit `src/`, did not build, and did not run anything.

## The lane doc was wrong, and this package corrects it

`AI_MEMO_WAL_ATOMICITY_LANE_V1.md` (written earlier the same day) proposed journaling memo
**payloads** into the `.tbj` as `M <id> <len> <hex>` records under a `TBJ2` bump.

Reading the source afterwards showed two facts the design had assumed away:

1. **Memo writes are eager.** `update_text_id` fires at `REPLACE` time, not at COMMIT. The content
   already exists before the transaction commits.
2. **Nothing in the memo subsystem ever fsyncs.** `MemoStore::flush()` is a stream flush.
   `grep -c 'fsync|FlushFileBuffers' src/memo/memostore.cpp` returns 0.

So the payload does not need re-carrying in the log -- it needs to be **durable before the WAL
commit marker**. The fix is an ordering change plus a real sync, not a format change. Smaller, no
`TBJ2`, no log-size cost, and it addresses the actual defect.

The lane doc should be amended on acceptance: M1 becomes ordering+durability, and payload journaling
is re-scoped to M2 as an optional robustness upgrade (it would additionally survive corruption of the
memo file itself, which this patch does not).

**This is the second time today a design was written before the source was read closely enough.** The
first produced a "there is no WAL" claim about a crash-proven WAL. Same root cause: trusting a
document over the code. Section 6 of the standards seed now says the source is the truth.

## What this does not fix

- **ROLLBACK orphans.** Eager memo writes mean a rolled-back `REPLACE` leaves an unreferenced object.
  Space leak, not a correctness bug. Needs a refcount-or-GC decision (lane M3). Out of scope, and
  deliberately not glossed over.
- **Non-COMMIT memo writers.** Any path writing memo outside COMMIT is unchanged and unaudited.
- **Backends other than `MemoStore`.** `durable_flush` falls back to `flush()` and reports the
  weakened guarantee in `err` rather than claiming success. It does **not** fail closed -- a
  maintainer may prefer that it does.

## Confidence

**High** on the defect: three independent source facts, each verified by reading, and they compose
into a clear failure sequence.

**Moderate** on the patch: the logic is small and the ordering is plainly correct, but it has not been
compiled. The `dynamic_cast` in `memo_manager.cpp` most likely needs an added include, and the
Windows `CreateFileA` sync path is the least-exercised branch. See TEST_PLAN section 2a.

**The fault-injection test matters more than the patch.** If it does not fail on the baseline, the
defect is mischaracterised and the patch should be rejected regardless of how reasonable it looks.
A durability fix whose bug was never reproduced is a guess with a diff attached.

## Sync-by-path, and why

`std::fstream` exposes no portable fd/HANDLE. The WAL can use `_fileno` because it holds a
`std::FILE*`; the memo store cannot. Extracting a descriptor from a `basic_filebuf` differs across
libstdc++, libc++ and MSVC and relies on implementation internals.

Syncing by path -- flush the stream, then open the file separately and force its buffers down -- is
portable, uses only `_path` which the store already holds, and adds no state. The cost is one extra
open/close per commit, which is negligible against an fsync.

## Filing

Placed in `src/AIPortal/sessions/` per the precedent set by
`2026-07-21_claude_recno64_indextxn_onboarding/`.

That directory was **gitignored earlier today by this same agent**, as part of a "scratch" sweep --
hiding 46 files including prior `AI_CHANGE_PACKAGE_*.md` and 7 `.patch` deliverables. Corrected in the
same session (`!/src/AIPortal/**`; the blanket `/src/**/*.patch` and `/src/**/*.dts` rules removed,
since both are deliverable types here). Noted because it is the third instance of one pattern in a
single day -- `*.log` hiding proofs, a stale header hiding a WAL, and an ignore rule hiding change
packages. Ignore rules and comments are written once and never re-read, while what they hide keeps
accumulating value.
