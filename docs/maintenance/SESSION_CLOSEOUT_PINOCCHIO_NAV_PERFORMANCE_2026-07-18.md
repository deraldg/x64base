---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260718-001
  recorded_at_utc: 2026-07-18T02:20:00Z
  agent:
    provider: anthropic
    product: claude-cowork
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: pinocchio-nav-top-skip-performance
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  authorization:
    requested_by: maintainer
    scope: >-
      Close the Pinocchio Phase-1 #1 finding: ordered TOP (and, discovered in
      the same lane, BOTTOM/SKIP/GO/GOTO endpoints) on CDX/LMDB were O(n). Make
      them O(1)/O(log n), with runtime proof scripts. Source mutation in
      src/cli, src/xindex, include/cli, include/xindex.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_PINOCCHIO_NAV_PERFORMANCE_2026-07-18.md
    kind: session_closeout
---

# Session Closeout — Pinocchio Nav Performance (2026-07-18)

Status: **Phase-1 #1 finding RESOLVED (dev). Not promoted, not published.**
Owning lifecycle: DotTalk++ SDLC.
SDLC lane: implementation + proof.
Truth state: source-defined + runtime-proven.
Proof state: build + runtime transcript (per-command `SET TIMER`), dev tree only.

This work began from the external ChatGPT "slow indexing" note the maintainer
brought in; it lands the fix for the one finding
`SESSION_CLOSEOUT_PINOCCHIO_PHASE1_2026-07-15.md` named as *"the single biggest
at-scale win available"* — `TOP` walking O(n) to the first key. It was done
outside the doc lane and is reconciled here.

## One-line summary

Ordered `TOP`/`BOTTOM`/`SKIP`/`GO`/`GOTO` on a CDX (LMDB) order were routed
through a full-DBF scan + key sort; they now use the LMDB index cursor directly,
taking `TOP` on the 5,501,358-row ENROLL table from ~66 s to ~1 ms with
correctness held.

## The finding this closes

Phase 1 measured `TOP` as the entire at-scale cost (per-command timings from
that closeout):

| Table | Order | Phase-1 `TOP` |
| --- | --- | ---: |
| STUDENTS (1,000,000) | SID | 19.478 s |
| STUDENTS (1,000,000) | LNAME | 23.231 s |
| ENROLL (5,501,358) | SID | 72.169 s |

Root cause (confirmed in source): `order_first_recno`/`order_last_recno`/
`order_skip` treated `IndexFormat::CDX` with the **CNX** code path
(`build_cnx_recnos_from_db`) — read every DBF record, build N keys, sort, build
two caches, return one recno. CDX is the 64-bit/LMDB front end and should read
the already-sorted LMDB index. `GO`/`GOTO` endpoints separately materialized the
whole logical order via `logical_nav` before picking one end.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Ordered nav core | `include/cli/order_nav.hpp` | Split CDX from CNX. CDX endpoints stream the backend cursor (`order_stream_display`) and stop at the first record; CDX `SKIP` uses a recno-precise cursor step, with the position-map cache kept only as a fallback and clamped partial-to-boundary. |
| Streaming iterator | `include/cli/order_iterator.hpp`, `src/cli/order_iterator.cpp` | New `order_stream_display()` (genuinely streaming, early-stoppable, reverse-capable) and `order_step_cdx()` (single seek + N cursor advances; `Moved`/`Boundary`/`Unavailable`). `order_iterate_recnos` kept materializing on purpose (SCAN/LIST bodies may mutate the index). |
| Logical (filtered) nav | `src/cli/logical_nav.cpp` | `first/last/next/prev_recno` stream with early-stop instead of materializing + reversing the full ordered vector. |
| CDX backend | `include/xindex/cdx_backend.hpp`, `src/xindex/cdx_backend.cpp` | New `stepOrdered(baseKey, fromRec, forward, steps, outRec, out_located)`: seek exact `(key,recno)` (composite `MDB_SET` or DUPSORT `MDB_GET_BOTH`), then step N times on one cursor, partial-to-boundary. |
| SKIP command | `src/cli/cmd_skip.cpp` | Unfiltered ordered `SKIP` now calls `order_skip(A, n)` once (one cursor, N steps) instead of N re-seeking unit calls. Filtered `SKIP` still uses the per-record visibility loop. |
| Proof scripts (new) | `dottalkpp/data/scripts/pinocchio/pinocchio_nav_defect_proof.dts`, `pinocchio_nav_filter_boundary.dts`, `nav_deleted_smoke.dts` | Endpoint/skip timing proof, filtered + boundary regression, and a self-contained deleted-record smoke (throwaway table). CANDIDATE/REVIEW; the first two have passing runs. |

CNX (32-bit flavors) paths are unchanged. Every CDX path keeps the DB-scan cache
as a safe fallback when the LMDB env is unavailable.

## Verified (proof performed this session)

Built MSVC Release (`cmake --build ./build --config Release`) cleanly across
iterations; ran the proof scripts against the real 1M/5.5M pinocchio fixtures
with `SET TIMER ON` (per-command elapsed) and `SET TALK ON` (landing recnos).

Before → after, ENROLL (5,501,358), SID order:

| Op | Before | After |
| --- | ---: | ---: |
| `TOP` | 66.09 s | 0.0013 s |
| `BOTTOM` | 66.51 s | 0.0010 s |
| first `SKIP` | 65.9 s | 0.0015 s |
| `SKIP 1000000` | 87.1 s | 0.021 s |
| `SKIP -1000000000` (walk to top) | 529 s | 0.11 s |
| `GO TOP`/`GOTO FIRST`/`GO BOTTOM`/`GOTO LAST` | (materialized) | 0.001–0.002 s |

STUDENTS (1,000,000): `TOP`/`BOTTOM` by SID and by LNAME all ~0.001–0.002 s
(Phase-1 was 19.5 s / 23.2 s).

Correctness canaries (all green): ordered `TOP` by SID lands on recno 1 =
`50000000` (the Phase-1 Taylor Quinn canary); LNAME order starts at `Anderson`
(recno 655360); `DESCEND` swaps ends (`TOP`→5501358, `BOTTOM`→1); `SKIP`
sequence `1→2→3→13→113→112→102` is exact; partial-to-boundary `SKIP` stops at
the endpoint; filtered `TOP`/`SKIP`/`BOTTOM` stay inside the filter and swap
under `DESCEND`; empty-result filter fails gracefully.

Honesty notes on proof: a zero exit code was **not** treated as proof — the
timing/recno transcripts are the evidence. The first two iterations of this work
each shipped a real regression that the proof scripts caught before promotion:
(1) the initial CDX endpoint used the wrong LMDB env path (`<cdx>.d` adjacent
instead of the `SET PATH LMDB` location) and silently fell back to the 66 s
scan — fixed by routing through `IndexManager`; (2) the first cursor-step made
single `SKIP` instant but large-N `SKIP` did N re-seeks (87 s) — fixed by the
one-cursor bulk step. Both are re-verified above.

## AI-facing docs updated (AIF-006 gate)

Proposed, pending maintainer review (see "Still open"):

- Add a Session Log row to `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`
  pointing at this closeout.
- Mark the Phase-1 `TOP` O(n) performance finding **resolved (dev)** in
  `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`, referencing this
  closeout and baseline `1ce8f45d`.
- `docs/agents/CURRENT_TARGET.md` is **not** changed here: the active objective
  (public-corrections reconciliation / staging commit) is unrelated; this is a
  Pinocchio proof follow-on, not a new top-level target.

These pointer edits are drafted in this session but are AI-facing state changes
subject to review before they are considered landed.

## Published

Not promoted to `C:\x64base`. Not committed or pushed. Dev-only
(`D:\code\ccode`), working tree intentionally dirty (7 modified source files +
untracked pinocchio scripts). Release readiness is judged from staged state, not
this dirty dev tree.

## Still open — for the next session

- **Promotion gate.** The 7 source files + the two passing proof scripts are the
  reviewable unit. `nav_deleted_smoke.dts` had a script bug (`APPEND BLANK` is an
  unimplemented alias; corrected to bare `APPEND`) and has **not** had a clean
  run yet — run it before treating deleted semantics as proven.
- **Open semantic decision (deleted records).** Unfiltered `TOP`/`SKIP` under
  `SET DELETED ON` read the raw index (RawOrder) and do not consult the deleted
  flag; filtered nav does (LogicalView → `is_visible`). This matches the rest of
  the CDX system but should be an explicit decision. The deleted-smoke script is
  built to produce that readout once it runs clean.
- **Filtered-nav cost is inherent, not a regression.** Filtered `TOP`/`BOTTOM`/
  `SKIP` and no-match filters stream the visibility gate (`is_visible`), so they
  are O(distance to nearest visible row) — a no-match filter costs a full scan.
  Same gate as `LIST`/`COUNT`; unchanged from before. A filtered index would be a
  separate optimization lane.
- **HELP/CMDHELP impact.** Runtime behavior changed but command surface/usage did
  not; `TOP`/`BOTTOM`/`SKIP`/`GO`/`GOTO` grammar is unchanged. No HELP text edit
  is required by this change; confirm with `CMDHELPCHK` at promotion.
- **Source Mutation Rule** was satisfied narratively but not filed as a formal
  preflight block before editing (work started outside the lane). Recorded here
  for the promotion review.

## Provenance pointers

- `docs/maintenance/SESSION_CLOSEOUT_PINOCCHIO_PHASE1_2026-07-15.md` — the finding this closes.
- `docs/agents/CURRENT_TARGET.md` — references the manifest-approved Pinocchio plan/proof lane.
- `dottalkpp/data/scripts/pinocchio/pinocchio_nav_defect_proof.dts` — endpoint/skip timing proof.
- `dottalkpp/data/scripts/pinocchio/pinocchio_nav_filter_boundary.dts` — filtered + boundary regression.
- `dottalkpp/data/scripts/pinocchio/nav_deleted_smoke.dts` — deleted-record smoke (throwaway table).
- Baseline: branch `homegrown-cnx-20251112-branch`, commit `1ce8f45d79d4a5d80ef7d006c784e54420bd4541`.
