# AI Change Package -- Memo/WAL Durability Ordering (AIF-061 M1)

## ai_report_audit envelope

```yaml
ai_report_audit:
  schema: ai-report-audit-v2
  provider: Anthropic
  product: Cowork
  model: not_exposed
  access_mode: local_repo_read_write        # file tools + sandboxed shell; NO git credentials
  session_reference: not_exposed
  agent:
    member: member.ai.claude.cowork
    role: role.ai_partner                   # source.propose; NOT source.mutate
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: null
    owner: member.derald
    committer: member.derald
  session:
    run_id: AIPR-20260725-001
    chat_handle: ""
    handle_binding: MAINTAINER_ATTESTED
    continues_run: AIPR-20260724-010
  project:
    id: project.x64base.runtime
    root: D:\code\ccode
  authorization_scope: propose-only. Delivered under the Outside-AI Delivery Rule at
    maintainer instruction. The agent did NOT edit src/ and did NOT build.
  report_path: src/AIPortal/sessions/2026-07-25_cowork_memo_wal_atomicity/
```

## Baseline

| Field | Value |
|---|---|
| Repository | `https://github.com/deraldg/x64base` |
| Branch | `development` |
| Baseline commit | `163cbefc24840492ee6828d809ef1a53573ffe6c` |
| Session date | 2026-07-25 |
| Lane | AIF-061 (`docs/maintenance/AI_MEMO_WAL_ATOMICITY_LANE_V1.md`) |

## Objective

Close the last store in the COMMIT durability chain. `COMMIT`'s own contract states it "is not an
atomic transaction across DBF, memo, and index storage." The DBF half is solved (the `.tbj` WAL,
AIF-062 `proof.wal.dbf_record`, crash-proven 2026-07-19). This package fixes the **memo half**.

## Owning lifecycle / states

| Field | Value |
|---|---|
| Owning lifecycle | SDLC -- engine durability |
| SDLC lane | AIF-061 |
| Truth state | source-defined (proposal) |
| Proof state | **none -- not compiled, not run** |
| Risk class | **HIGH.** Touches the commit durability path. |
| Next gate | maintainer build + the fault-injection test in `TEST_PLAN.md` |
| Status | proposed, awaiting review |

## The defect (verified by reading, not assumed)

Three facts, each confirmed in source at the baseline commit:

1. **`src/cli/cmd_commit.cpp:369`** calls `journal_begin_commit(area0)` -- the WAL fsync and
   **the transaction's durable commit point**.
2. **`src/cli/cmd_commit.cpp:440`** calls `mm->flush(&memo_err)` -- the memo flush, which happens
   **after** the commit point and after the DBF apply. Wrong side of the barrier.
3. **`src/memo/memostore.cpp:143` `MemoStore::flush()` is `_fp.flush()` only.** `grep -c
   'fsync|FlushFileBuffers' src/memo/memostore.cpp` returns **0** -- there is no durable sync
   anywhere in the memo subsystem. A stream flush hands bytes to the OS; it does not force stable
   storage.

Memo writes are also **eager**: `build_x64_memo_stored_value`
(`include/cli/memo_field_store.hpp:61`) calls `store->update_text_id()` at `REPLACE` time, so the
object exists in the stream buffer long before COMMIT, and the DBF field holds only its decimal
object-id.

**Failure sequence.** `REPLACE` writes memo object 42 into the stream buffer and buffers
`NOTES = "42"`. `COMMIT` fsyncs a WAL record saying *record N field NOTES = 42*. Crash before the
memo bytes reach stable storage. Recovery replays the WAL -- durable, correct, complete -- and the
record now references object 42, whose bytes were never persisted. **A dangling memo reference the
WAL cannot detect, because from its view the transaction committed cleanly.**

Severity is bounded (a crash inside a narrow window on a memo-bearing commit) but the failure is
**silent**: it surfaces later as a read error, not at recovery.

## Correction to the lane doc

`AI_MEMO_WAL_ATOMICITY_LANE_V1.md` proposed journaling the memo **payload** into the `.tbj` as
`M <id> <len> <hex>` records. That was written before the eager-write and no-fsync facts above were
established, and it is **heavier than the defect requires**.

Because the memo object is already written eagerly, the content does not need to be re-carried in the
log. What is missing is only that the memo bytes be **durable before the WAL declares the transaction
committed**. This package therefore proposes the ordering + durability fix (M1), and re-scopes payload
journaling (M2) as a later, optional robustness upgrade for the case where the memo file itself is
damaged.

Smaller, and it fixes the actual bug. The lane doc should be amended on acceptance.

## Changed files

| File | Change |
|---|---|
| `include/memo/memostore.hpp` | declare `MemoOpResult durable_flush();` |
| `src/memo/memostore.cpp` | implement `durable_flush()` -- header write, stream flush, then a real `FlushFileBuffers`/`fsync` |
| `include/memo/memo_manager.hpp` | declare `bool durable_flush(std::string* err = nullptr);` |
| `src/memo/memo_manager.cpp` | forward to the backend's `durable_flush()` |
| `src/cli/cmd_commit.cpp` | call the memo durable flush **before** `journal_begin_commit`; keep the existing post-apply `flush()` as a no-op-safe second flush |

## Added files

None.

## Deleted files

None.

## Contracts and annotations read

- `labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md` (this contract)
- `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` (sections 1-6, incl. 5c)
- `@dottalk.usage` on `cmd_commit.cpp` (`mutates: table-data table-buffer memo stale-state index journal`)
- `docs/maintenance/TABLE_BUFFER_WAL_DESIGN_2026-07-19.md` (TBJ1 format, ordering)
- `docs/maintenance/SESSION_CLOSEOUT_TABLE_BUFFER_WAL_2026-07-19.md` (Phase A/B/C proofs)
- `include/cli/table_state.hpp`, `src/cli/table_state.cpp` (WAL implementation)

## Mutation and compatibility effects

- **No format change.** `.tbj` stays `TBJ1`. No `.dtx` memo format change. Old logs replay unchanged.
- **No API break.** `flush()` keeps its signature and behavior; `durable_flush()` is additive.
- **Behavioral change:** COMMIT performs one additional fsync per commit **when a memo backend is
  attached and memo changes exist**. Cost is one fsync, alongside the WAL's existing one.
- **RamOnly mode unaffected** -- the WAL hooks already no-op there; the memo flush is gated the same way.
- **Failure path:** if the memo durable flush fails, COMMIT aborts **before** the WAL commit marker,
  leaving the buffer intact and retryable. This is strictly safer than today, where the memo failure
  is discovered after the transaction is already durable.

## Intentionally excluded

- **M2 payload journaling** (`M` records, `TBJ2`) -- re-scoped as optional; not needed for correctness.
- **The ROLLBACK orphan.** Eager memo writes mean a rolled-back memo `REPLACE` leaves an unreferenced
  object. That is a **space leak, not a correctness bug**, and fixing it needs a refcount/GC decision
  (lane M3). Deliberately out of scope here; noted so it is not mistaken for solved.
- **Index coordination (M4).** LMDB is already ACID and indexes are derivable.

## Unresolved questions

1. **Should `flush()` simply become durable**, rather than adding `durable_flush()`? Fewer call sites
   to keep straight, but it makes every existing `flush()` caller pay an fsync. I chose additive;
   the maintainer may prefer the simpler blunt version.
2. **Windows `FlushFileBuffers` on an `std::fstream`** needs the underlying `HANDLE`. `table_state.cpp`
   already solves this for the WAL (`wal_durable_sync`); the patch mirrors that approach, but the
   maintainer should confirm the memo store's stream is obtainable the same way. **This is the most
   likely compile-time failure point.**
3. **Does any non-COMMIT path** write memo and rely on `flush()` for durability? I did not audit every
   caller.
