# Triage Execution Plan -- all 2026-07-30 findings, ordered by triage priority

**Date:** 2026-07-30
**Run:** `DECLARED-CAPABILITY-VALIDATOR-20260730` - **Author:** Claude (Cowork) - **Owner:** `member.derald`
**Baseline:** `b702b5a5d1cc629c48411af9e93ff879b198e73f` on `development`
**Status:** `review-needed`. Plan only. No source mutation authorized or performed.
**Covers:** `AIF-043` V6 (R1-R6), `AIF-079` (M0-M3), `XIDX-TXN-02` (N1-N5), index mutation seam (A-E), and the two held ledger rows.

---

## 0. Ordering principle (read this before the table)

This plan is **not** ordered by lane, and not ordered by my estimate of what is most interesting. It is ordered so that **if work stops after any sitting, the highest-value items are already banked.**

That principle matters here specifically because my own forecast for this material is that most of it will not be built. Front-loading is the hedge against my own charter enthusiasm. Sitting 1 alone retires the two silent-correctness items and the performance win; everything after it is improvement rather than repair.

Triage rank is: **silent wrongness > cheap measurable win > decisions that unblock > structure > new capability > documentation.**

## 1. One finding that changes the plan

`apply_replace_snapshot` has exactly three call paths, and **all three funnel through the same function**:

| Path | Route |
|---|---|
| `REPLACE`, `CALCWRITE` | `replaceFieldStored` -> `index_hooks::apply_replace` -> `attach.cpp:62` -> `apply_replace_snapshot` |
| `REPLACE_MULTI` | `cmd_replace_multi.cpp:905` -> `apply_replace_snapshot` |
| buffered `COMMIT` | `cmd_commit.cpp:276` -> `index_hooks::apply_replace` -> `attach.cpp:62` -> `apply_replace_snapshot` |

Two consequences:

- **Finding A is one diff that fixes all three paths.** That is what puts it in sitting 1 despite being a performance item rather than a correctness item.
- **Finding B is smaller than it looked.** The duplication is in the capture/orchestration wrapper, not in the apply. Demoted from "three copies of the seam logic" to "three copies of the wrapper." It drops to sitting 5.

`apply_delete_snapshot` and `apply_insert_snapshot` have the same shape and the same defect, with callers in `cmd_delete.cpp:245`, `cmd_recall.cpp:199`, and `append_support.cpp:275`. Fix A should consider all three siblings, not only replace.

## 2. The plan

### Sitting 1 -- stop the silent wrongness, take the cheap win (~half a day)

| # | Item | Where | Cost | Exit proof |
|---|---|---|---|---|
| 1.1 | **E** -- surface index maintenance failure | `dbarea.cpp:283` | ~5 lines | Forced-failure path prints and marks stale instead of returning `true` silently |
| 1.2 | **C1** -- `VALIDATE UNIQUE` repair bypasses the seam | `cmd_validate_unique.cpp:352-353` | ~20 lines | Repair on an indexed field, then `SEEK` the new value hits and the old misses, with no `REINDEX` |
| 1.3 | **A** -- diff the snapshots, emit only changes | `index_manager.cpp:547-576` (+ 529, 580 siblings) | ~30 lines, one function | Bench: 1-field `REPLACE` on an N-tag table drops from 2N LMDB transactions to 2. Parity: `REGRESSION ALL` green |

**Why these three first.** 1.2 is the only silent-wrong-index defect on a `status: supported` command in the mainline disk path, and its repair path rewrites precisely the kind of field most likely to be indexed. 1.1 is nearly free and makes every later failure in this subsystem diagnosable rather than invisible, so it is worth doing before rather than after. 1.3 is the largest measurable payoff per line of diff in the entire session, and section 1 shows it lands once and benefits everywhere.

**If work stops here, the session paid for itself.**

### Sitting 2 -- make the vdisk boundary refuse what it cannot serve (~half a day)

| # | Item | Where | Cost | Exit proof |
|---|---|---|---|---|
| 2.1 | **R2** -- `VDISK UNMOUNT` with an open area | `cmd_vdisk.cpp:160-164` | small | `UNMOUNT` with an area open is refused or force-closes cleanly; no post-unmount write reaches an orphan buffer |
| 2.2 | **R5** -- `BUILDLMDB` unguarded on a virtual path | `cmd_buildlmdb.cpp` | small | `BUILDLMDB` under a mounted vdisk errors clearly and creates **no** directory under the RAM root |
| 2.3 | Shared guard helper | `ramfs` | small | `refuse_if_virtual(path, layer)` exists; 2.2 uses it |

2.1 and 2.2 are the same shape and belong in one sitting. 2.3 is the item that pays forward: its value is not the two call sites it serves but that the **next** unrouted writer fails loudly instead of leaking to disk. R1-R6 are what one investigation found, not proof the set is closed.

This is `AIF-043` V6.1, minus the decisions.

### Sitting 3 -- decisions only, no code (~1-2 hours, maintainer)

These are cheap, they gate later sittings, and every one of them is a ruling only you can make.

| # | Decision | Blocks | Recommendation |
|---|---|---|---|
| 3.1 | `XIDX-TXN-02` sequencing: persistence-first, or prove the algorithm first with `save()` deferred | sitting 6 | **Prove first, on x32/CNX, session-only.** Removes `save()`, fsync, torn writes, Windows atomic-rename **and** the vdisk dependency from the first proof. Moves my M1 estimate from 0.40 to ~0.65. See the harness note in sitting 6 |
| 3.2 | **N3** duplicate-key erase: widen `InxPayload` ordering to `(key, recno)`, or scan the equal-key run | sitting 6 | Scan the run first (no format impact); widen later if measured |
| 3.3 | **R1** memo on virtual tables: route through ramfs, or refuse | sitting 4 | **Refuse** for V6. Routing `MemoStore` is larger than it looks (`create_directories`, directory scans) |
| 3.4 | **R3** `on_full`: implement enforcement, or downgrade the config surface | sitting 4 | Downgrade first. `VDISK CONFIG` currently prints a policy that does not run, which is worse than not offering it |
| 3.5 | **AIF-079** suppression granularity: file-level `status: planned` or symbol-level | sitting 7 | Symbol-level. File-level will suppress too much and hide real cases |
| 3.6 | **C2** disposition: is `cmd_sql_update`/`cmd_sql_insert` inside AIF-074's abandoned SQL group | sitting 5 | Confirm; if yes, no separate work, note it in AIF-074 |

### Sitting 4 -- finish `AIF-043` V6 (~1 day)

Implements the 3.3 and 3.4 rulings, plus the lower-severity routing gaps.

| # | Item | Cost |
|---|---|---|
| 4.1 | **R1** per the ruling (refuse or route) | small if refuse |
| 4.2 | **R3** per the ruling | small if downgrade |
| 4.3 | **R4** / **R6** -- warn or refuse on `.inx` and `.tbj` against a virtual path | small, uses 2.3 |
| 4.4 | **V6.2 proof script** -- the four assertions, registered in `cmd_regression` | ~half a day |

**4.4 assertion 4 is the one that matters and the one most likely to be quietly dropped:** after a full RAM session exercising table + index + memo, a listing of the RAM root shows zero real files. Scope it to the RAM root only, or incidental files will make it flaky and it will be deleted rather than fixed.

### Sitting 5 -- structure and disposition (~half a day)

| # | Item | Note |
|---|---|---|
| 5.1 | **B** -- consolidate the three capture/apply wrappers | Demoted per section 1. A shared helper taking the write action as a callable preserves `REPLACE_MULTI`'s single-lock/single-write property |
| 5.2 | **C2** -- record the AIF-074 disposition for the SQL pair | Documentation, not code, if 3.6 confirms |
| 5.3 | **D** -- document the buffered/immediate asymmetry | `SET INDEXTXN` HELP + table-buffer docs. Users who enable buffering for speed silently lose maintenance they had without it |

### Sitting 6 -- `XIDX-TXN-02` M1, prototype on x32/CNX (~2-3 sittings)

Conditional on ruling 3.1. Ordered so the pure-logic work is proven before any durability work starts.

> **Harness corrected by the maintainer, 2026-07-30.** This plan originally proposed proving RAM-first on `CdxNativeBackend` under a mounted vdisk. **x32/CNX is the better harness**, for a reason stronger than preference: the mutable-payload work is not per-backend at all.
>
> `include/cdx/cdx_document.hpp:20` does not mirror CNX, it **includes** it -- `#include "cnx/cnx_document.hpp"   // xindex::CnxTag, CnxHeader, InxPayload`. Both readers converge on the identical construction (`cnx_document.cpp:85`, `cdx_document.cpp:93`: `payload = InxPayload::fromEntries1Inx(tag_name, entries)`), and RUN8 is documented as "the 64-bit twin of CNX's RUN1. Identical header, 8-byte recnos" (`cdx_document.cpp:40`). CNX carries the same key logic CDX carries, minus LMDB.
>
> So **N1, N2 and N3 are authored once in `InxPayload` and serve CNX/V32, native CDX-V64, disk and RAM simultaneously.** The backend is only the harness that proves it, and x32 is the cheaper harness:
>
> | | x32 / CNX on disk | x64 / CDX-native in RAM |
> |---|---|---|
> | Dependency | none; `DO x32` is a two-line lane switch | requires a sound vdisk |
> | Existing harness | `index_x32_inx_cnx_smoke.dts` | `mem_proof.dts` |
> | Lifecycle to manage | none | mount / unmount, with the R2 hazard live |
> | Relation to the original question | it **is** the question | adjacent |
>
> The decisive point: the RAM route made sitting 6 implicitly depend on ramfs being sound, while **sitting 2 exists precisely because it is not** (memo unrouted, `UNMOUNT` orphaning a live area). Proving on x32 decouples the index lane from the vdisk lane entirely.
>
> The "no persistence" property that motivated RAM-first is preserved for free: **do not call `save()`.** Mutate the loaded payload, prove `SEEK` correct within the session before any `REBUILD`, and `CnxDocument::save` / `InxPayload::writeToStream` stay out of scope exactly as intended.
>
> This raises my `XIDX-TXN-02` M1 estimate from ~0.60 to **~0.65**, since it removes a dependency on an unproven subsystem.

| # | Item | Note |
|---|---|---|
| 6.1 | **N4** -- multi-tag capture for all `ITagBackend`, not just `CdxBackend` | **Prerequisite, not a detail.** Harmless today because the keys are discarded; the moment `upsert`/`erase` are real, single-tag maintenance silently skews every other tag |
| 6.2 | **N1** -- ordered insert/erase on `InxPayload` | Class is currently immutable by construction |
| 6.3 | **N3** -- recno-precise erase per ruling 3.2 | Correctness gate. Removing the wrong duplicate is silent corruption: counts stay right, `SEEK` still hits, the wrong record is reachable |
| 6.4 | **N2** -- `pos_by_recno_` invalidate-and-rebuild at save, not maintained | Incremental maintenance of a dense position table is O(n) per mutation, worse than the splice |
| 6.5 | Real `upsert`/`erase` on `CnxBackend`, behind `SET INDEXTXN`, **session-only (no `save()`)** | The payload work above is shared, so this is the thin part |
| 6.6 | **Proof:** `DO x32`, open a CNX-ordered table, mutate an indexed field, `SEEK` correct with no `REBUILD`, multi-tag asserted | Extends `index_x32_inx_cnx_smoke.dts`; no mount lifecycle |
| 6.7 | **Lift to `CdxNativeBackend`** -- should be near-free once 6.2-6.4 land in `InxPayload` | Confirms the shared-payload claim rather than assuming it |

Only after 6.6 is green: persistence (`CnxDocument::save`, `InxPayload::writeToStream`, atomic temp+fsync+rename, `CNX_HDRF_DIRTY` recovery, the C4 COMMIT branch). That is a separate scheduling decision, not a continuation.

6.7 is deliberately a step rather than an assumption. If lifting to native CDX-V64 turns out **not** to be near-free, the shared-payload premise is wrong and the plan needs revisiting -- which is worth finding out cheaply, right after the first proof, rather than at the end.

### Sitting 7 -- `AIF-079` validator (~1 sitting for M1, open tail after)

| # | Item | Note |
|---|---|---|
| 7.1 | M1 scanner, D1 + D4 minimum, report-only | Must find all seven seed instances. Known-answer set is the exit condition |
| 7.2 | Suppression via annotation `status` per ruling 3.5 | |
| 7.3 | M2 triage: every finding into {true defect, legitimate-and-annotated, tool error} | **This is where the lane dies if it dies.** The CLI dispatcher registers commands by name, so a large population of functions legitimately has no C++ call site. Handle that class explicitly or the tool produces noise and gets ignored |
| 7.4 | M3 ratcheted gate | Only after 7.3 shows zero tool errors |

Placed last deliberately. It is infrastructure-for-infrastructure, and by the time it runs, items 1.1-6.6 will have removed several of its own seed instances, which is fine: the lane's proof set is the *recorded* seven, not the live ones.

### Sitting 8 -- administrative debt (~15 minutes)

| # | Item |
|---|---|
| 8.1 | Land the `AIF-079` intake queue row (drafted, session README section 4) |
| 8.2 | Land the dashboard Session Log row (drafted, closeout section 6) |
| 8.3 | Confirm or correct `AIPR-20260730-004`; no allocator comparable to `claim-aif` was found |

Both rows were held because their target files already carried other sessions' uncommitted edits, and fusing lanes into one slice is what the coordination protocol forbids. They are cheap; they just need a batch that owns those files.

## 3. Dependency graph (only the edges that matter)

```
3.1 ruling ----> sitting 6 (entire)
3.2 ruling ----> 6.3
3.3 / 3.4 -----> 4.1 / 4.2
3.5 ruling ----> 7.2
2.3 helper ----> 4.3
6.1 -----------> 6.5        (multi-tag capture BEFORE real upsert/erase)
6.3 -----------> 6.5        (recno-precise erase BEFORE real erase)
6.2/6.3/6.4 ---> 6.7        (shared InxPayload work makes the CDX lift near-free)
1.3 (A) -------> 5.1 (B)    (fix the logic once, then consolidate wrappers)
```

Everything in sittings 1 and 2 is independent and can be done in any order or in parallel.

**Sitting 6 no longer depends on sitting 2.** With the x32/CNX harness there is no vdisk in the path, so the index lane and the vdisk lane can proceed in either order or concurrently. Under the original RAM-first proposal, 2.1 was an implicit prerequisite.

## 4. What I would cut if the answer is "not all of this"

In order of what I would drop first:

1. **7.4 (M3 ratcheted gate).** The report-only scanner carries most of the value; the gate is a hardening step that can wait indefinitely.
2. **5.1 (B consolidation).** Real per AIF-037, but section 1 showed the shared part is already shared. Pure hygiene now.
3. **The disk half of sitting 6.** If RAM-first proves the algorithm, the disk port is a scheduling decision that can be made on evidence rather than on plan.
4. **4.3 (R4/R6).** Lowest-severity routing gaps; a warning would do.

I would not cut sittings 1 or 2, or 4.4 assertion 4. Sitting 1 is repair. Sitting 2 is a hazard guard. Assertion 4 is the only thing in the plan that catches the *next* instance rather than the ones already found.

## 5. Honest note on this plan

Eighteen work items were generated in one day by investigations that were not asked for as lane work. My own forecast puts most of them below 50% to be built. `XIDX-TXN-02` is the cautionary case in your own tree: chartered by an AI session on 2026-07-21, marked M0 met and M1-ready, untouched nine days later.

So the ordering above is the actual deliverable, more than the item list is. If this plan is executed strictly in order and abandoned at any point, the remaining tail is by construction the part that mattered least.

The falsifiable near-term signal stands: **if 2.1 (the `VDISK UNMOUNT` guard) has not landed within about two weeks, revise every lane in this plan down sharply.** It is the cheapest guard against the worst failure mode here, and if it does not clear the queue, nothing further down will.
