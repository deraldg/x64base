# Session Closeout — Pinocchio Phase 1 (2026-07-15)

Status: **MILESTONE — Phase 1 (performance at scale) PASSED.**
"Can the educational database be a real boy?" At 1,000,000 students and
5,501,358 enrollments, correctness held across the board. Yes.

## What was proven

A fresh `-Reset` build (`CREATE X64` → `IMPORT` → `CDX` → `BUILDLMDB`) over
generated MCC-shaped data, then the read-only battery. All correctness gates
green at real-world scale:

- **Load:** `IMPORT` brought in 1,000,000 STUDENTS and 5,501,358 ENROLL rows;
  `COUNT` matched both exactly.
- **Ordered by key:** `SET ORDER TO TAG SID` + `TOP` → record 1 =
  `50000000 Taylor Quinn` (the canary), then `50000001`, `50000002` … full
  8-digit keys, correctly ordered.
- **Point lookups land, both sides:** `SEEK 50000500` → **Found at 501**
  (STUDENTS) and **Found at 2749** (the 5.5M-row ENROLL child).
- **Secondary order + predicate:** `SET ORDER TO TAG LNAME` → `Anderson` first;
  `LIST FOR MAJOR = CSCI` ran in `MODE LMDB`.
- **Fresh indexes:** every `CDX CREATE` reported `created:` (not
  `already exists`) — the `-Reset` cleared the stale empty leftovers.
- **LMDB sizing:** `HUGE` (1 GiB) indexed 1M × 3 tags; explicit `MAPSIZE 2G`
  indexed 5.5M × 2 tags; **no `MDB_MAP_FULL`**. Real-boy scale fit inside the
  named ceiling for STUDENTS and just above it for ENROLL — the 4G/8G first
  guess was overkill.
- **Speed (wall clock only):** the full generate→build→measure run took
  **~20–30 minutes** end to end (IMPORT of 6.5M rows across two tables, five CDX
  tags, two `BUILDLMDB`, then the read-only battery). That is the *only* timing
  we have — see "Timing status" below.

## The fix that got here

The first runs used `SID I` (bare integer). The engine reported it as `I 4` and
truncated the 8-digit SID to 4 significant digits (`50000000 → 5000`), which
corrupted the stored value, the index key (broken order, failed SEEK) and the
display — while `LNAME` (`C(20)`) indexed perfectly. Switching the key to
`N(8)` (the same type MCC's SID uses, which renders `50000000` correctly)
fixed store, index, order, SEEK, and display. The generated CSV always held the
full 8-digit SID, so this was purely the `I` field on import.

## Findings (logged to the intake queue)

1. **`I` wide-key truncation.** Bare `I` → `I(4)` cannot hold an 8-digit key; it
   keeps ~4 high-order digits. Either bare `I` needs an explicit wider width, or
   `I` should hold `50000000` and the truncation is a store/index/display bug.
   Clean A/B repro in this lane.
2. **`SMARTLIST NEXT` restarts from the top after `SEEK`.** `SEEK 50000500`
   reports "Found at 501/2749" correctly, but a following `SMARTLIST NEXT` lists
   from record 1, not the sought record — consistent on both tables. Implicit
   `TOP`, or a bug.
3. **`SET TIMER` is not exercised per-command when nested under `DOTSCRIPT`.**
   The CLI treats `DOTSCRIPT` (and `DOTSCRIPT TRACE`) as a single command, so the
   timer wraps the whole script (one aggregate) and never descends to the nested
   lines. Per-command timing requires running the battery as top-level REPL
   commands, not nested. (Maintainer-diagnosed.)

## Timing status — Phase 1.1 CAPTURED

The `DOTSCRIPT`-nested runs produced **no** timer lines (finding 3, confirmed:
not one `ELAPSED` in either trace). Re-running the battery as **top-level REPL
commands** — `pinocchio_measure_repl.dts` pasted at the `.` prompt, wrapped in
`SET ALTERNATE TO tmp\pinocchio\measure_timed` / `SET ALTERNATE ON` — timed every
command. Full capture: `tmp/pinocchio/measure_timed`. Earlier "133s" figures were
unsupported and have been removed; these are the real numbers.

### Per-command elapsed (fresh N(8) build)

**STUDENTS (1,000,000)**

| Command | ELAPSED |
| --- | ---: |
| USE STUDENTS | 0.027 s |
| COUNT → 1000000 | 0.0015 s |
| SET ORDER TO TAG SID | 0.010 s |
| **TOP (SID)** | **19.478 s** |
| SMARTLIST NEXT 5 (canary ✓) | 0.074 s |
| SET ORDER TO TAG LNAME | 0.031 s |
| **TOP (LNAME)** | **23.231 s** |
| SMARTLIST NEXT 20 (Anderson ✓) | 0.135 s |
| LIST FOR MAJOR = CSCI (first 20) | 0.244 s |
| SEEK 50000500 → Found at 501 | 0.018 s |

**ENROLL (5,501,358)**

| Command | ELAPSED |
| --- | ---: |
| USE ENROLL | 0.017 s |
| COUNT → 5501358 | 0.0019 s |
| SET ORDER TO TAG SID | 0.008 s |
| **TOP (SID)** | **72.169 s** |
| SMARTLIST NEXT 10 | 0.348 s |
| SEEK 50000500 → Found at 2749 | 0.003 s |
| SMARTLIST NEXT 8 | 0.238 s |

### What the numbers say

- **`TOP` is the entire cost.** The three `TOP` calls sum to 114.9 s of a ~116 s
  battery; every other operation combined is under 1.5 s. `TOP` scales with table
  size (1M ≈ 20 s, 5.5M ≈ 72 s) — an **O(n) walk to reach the first key** rather
  than a jump to it. Logged as a performance finding (see intake queue). This is
  almost certainly the single biggest at-scale win available.
- **Point and lookup ops are excellent at scale.** `SEEK` is 3–18 ms even on the
  5.5M child; `SMARTLIST NEXT` is 50–350 ms; `LIST FOR` (first 20) is 0.24 s.
- **`COUNT` does not measure scan throughput.** It returns in ~1.5 ms because it
  reads the stored record count, not a physical scan — battery item #1 should be
  relabeled or replaced with a real full-scan op if scan throughput is wanted.
- **Wall clock reconciled.** The ~20–30 min the maintainer observed was the *full*
  generate→build→measure run; the read-only battery itself is ~2 min, and of that
  ~115 s is the three `TOP` calls. The build (IMPORT of 6.5M rows + CDX + two
  BUILDLMDB) is the bulk of the wall time — a Phase 1.1 follow-up can time those
  stages the same way (paste the build body at the REPL).

## Next

- **Phase 1.1 — DONE** (per-command timings captured above). Follow-on: time the
  build stages (IMPORT / CDX / BUILDLMDB) the same way, and add a real full-scan
  op since `COUNT` doesn't measure scan throughput.
- **`TOP` performance** — the one finding worth chasing before Phase 2: profile
  why `TOP` walks O(n) to the first key when `SEEK` reaches any key in ms. Biggest
  at-scale win in hand.
- **Phase 2** — fault injection (concurrency, crash/reopen, durability), the
  areas the engine rates Unverified. Defined in the plan, deferred.

## Report by stage

Dev changed: `pinocchio_build.dts` (SID `N(8)`, LMDB right-sizing), the charter,
this closeout, the intake queue. Built + measured: a full 1M/5.5M cold build and
read-only battery, correctness-green. Promoted / pushed: not applicable (lane is
dev-only; data is derived and gitignored). The `.dts` remain
CANDIDATE/REVIEW — now with one passing run behind them.
