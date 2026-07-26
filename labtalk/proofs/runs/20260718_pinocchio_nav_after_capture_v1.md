> **SUPERSEDED (2026-07-18):** the benchmarks ledger now binds the directly-teed
> runner transcripts `nav_defect_after_teed_20260718T142513Z.log`
> (`AD1E6A44…`) and `nav_filter_boundary_after_teed_20260718T142513Z.log`
> (`F520E661…`), status `RAW_TEED_TRANSCRIPT`. This file remains only as a
> readable `PIN-HIST → line` map and is no longer cited as evidence.

# Pinocchio Ordered-Navigation — After-Fix Proof Capture (v1)

Captured: 2026-07-18. Baseline: branch `homegrown-cnx-20251112-branch`, commit
`1ce8f45d79d4a5d80ef7d006c784e54420bd4541` (working tree dirty with the
uncommitted nav edits; version banner reads `1ce8f45d dirty` across builds).

## Provenance and honesty boundary

This is a **chat-sourced excerpt capture**: the console output was produced by
the maintainer running the scripts on the host and pasted into the working
session, then transcribed here. It is **not** a directly-teed runner log
(`DOTSCRIPT ... OUT` / `SET ALTERNATE`) and must not be relabeled as one. The
machine was **not** recorded in the run output. (Update 2026-07-18: the
maintainer has since *attested* the project machine — Alienware m16 R2 / Core
Ultra 9 185H — so the ledger now carries `machine_binding: MAINTAINER_ATTESTED`
rather than `UNRECORDED`; the "not recorded in the run output" fact still holds,
the attestation is an after-the-fact maintainer declaration.) The canonical
upgrade is a host re-run of both
scripts at the final build with `SET TIMER ON` + `SET ALTERNATE TO <log>`,
hashed and rebound. Until then the ledger status is
`AFTER_TRANSCRIPT_CHAT_SOURCED_CAPTURE`.

Elapsed values are as pasted; the benchmarks ledger rounds them (e.g. TOP
0.001293500 s → `0.0013`).

## Run A — pinocchio_nav_defect_proof.dts (endpoints + first SKIP)

The endpoint fix landed at build `Jul 17 2026 17:25:54`; the first-SKIP cursor
step landed at build `Jul 17 2026 17:40:51`. Both are on baseline `1ce8f45d`
plus progressively more of the uncommitted nav edits. `defect_proof.dts` does
not exercise large-N SKIP, so its numbers are valid for endpoints/first-SKIP.

### Build 17:25:54 — endpoints instant (ENROLL, 5,501,358, SID order)

```
. TOP
TIMER END  : 0.108401000 s
ELAPSED    : 0.001293500 s          # PIN-HIST-001 after (0.0013)
. SMARTLIST SID,CLS_ID NEXT 5
  RECNO SID      CLS_ID
      1 50000000 W26BIOL288          # canary: 50000000 (Taylor Quinn record 1)
      2 50000000 S26BUSN399
      ...
. BOTTOM
ELAPSED    : 0.000974000 s          # PIN-HIST-002 after (0.0010)
. GO TOP        -> Recno 1        ~0.001-0.002 s
. GO BOTTOM     -> Recno 5501358  ~0.001-0.002 s
. GOTO FIRST    -> Recno 1        ~0.001-0.002 s
. GOTO LAST     -> Recno 5501358  ~0.001-0.002 s
. LOOP 20 { TOP } -> 20x Recno 1, 0.009 s total   # O(1), not a warmed cache
. SKIP  (first)  ELAPSED 1.712170900 s            # pre-cursor-step: cache build once
```

### Build 17:40:51 — first SKIP instant, SET TALK ON (landing recnos visible)

```
. TOP           Recno: 1
. SKIP          Recno: 2   ELAPSED 0.001456900 s  # PIN-HIST-003 after (0.0015)
. SKIP          Recno: 3
. SKIP 10       Recno: 13
. SKIP 100      Recno: 113
. SKIP -1       Recno: 112
. SKIP -10      Recno: 102                          # exact step sequence
. SKIP 0        Recno: 102   (re-read, no move)
STUDENTS (1,000,000):
. TOP  (SID)    Recno: 1
. BOTTOM (SID)  Recno: 1000000
. TOP  (LNAME)  Recno: 655360   -> Anderson (char-key, non-physical order)
. BOTTOM (LNAME)Recno: 196351
DESCEND (ENROLL, SID):
. TOP           Recno: 5501358   (largest SID 50999999)
. BOTTOM        Recno: 1         (smallest SID 50000000)   # ends swap correctly
. ASCEND
```

## Run B — pinocchio_nav_filter_boundary.dts (build 18:15:42, all fixes)

This build has the bulk-SKIP fix (`cmd_SKIP` calls `order_skip(A, n)` once;
`stepOrdered` does one seek + N cursor advances).

### Section F — unfiltered SKIP across boundaries (ENROLL, 5,501,358, SID)

```
. BOTTOM        Recno: 5501358
. SKIP          SKIP: at end.   0.001506100 s      # F1 boundary, no cache build
. TOP           Recno: 1
. SKIP -1       SKIP: at end.   0.001581900 s      # F2 boundary
. TOP           Recno: 1
. SKIP 1000000  Recno: 1000001  ELAPSED 0.021311900 s   # PIN-HIST-004 after (0.021)
. SKIP -1000000 Recno: 1        ELAPSED 0.011625400 s
. BOTTOM        Recno: 5501358
. SKIP -5       Recno: 5501353
. SKIP 100      Recno: 5501358                      # partial-to-boundary (xBase SKIP-to-EOF)
. SKIP -1000000000  Recno: 1    ELAPSED 0.112844600 s   # PIN-HIST-005 after (0.11)
```

### Section E — filtered nav (LogicalView / streaming), LNAME = "Anderson"

```
. SET FILTER TO LNAME = "Anderson"
. COUNT         72420
. TOP           Recno: 7        -> LNAME = Anderson (Quinn)   # first visible in SID order
. SKIP          Recno: 9        -> Anderson
. SKIP          Recno: 11       -> Anderson
. BOTTOM        Recno: 999986   -> Anderson (last visible)
. SKIP          SKIP: at end.                        # past last visible
. DESCEND: TOP  Recno: 999986 ; BOTTOM Recno: 7      # endpoints swap under filter
. SET FILTER TO SID = 99999999 (no match): COUNT 0 ; TOP: failed ; BOTTOM: failed   # graceful
```

Note: filtered/no-match ops are O(distance to nearest visible row) by design
(same visibility gate as LIST/COUNT); `COUNT` on a filter (~20 s) and no-match
`TOP`/`BOTTOM` (~38 s each) are inherent, pre-existing, and not the nav change.

## PIN-HIST row → source line map

| Ledger row | Operation | Before | After | Source line above |
| --- | --- | ---: | ---: | --- |
| PIN-HIST-001 | ENROLL TOP SID | 66.09 s | 0.0013 s | Run A, 17:25:54 TOP |
| PIN-HIST-002 | ENROLL BOTTOM SID | 66.51 s | 0.0010 s | Run A, 17:25:54 BOTTOM |
| PIN-HIST-003 | ENROLL first SKIP | 65.9 s | 0.0015 s | Run A, 17:40:51 SKIP→Recno 2 |
| PIN-HIST-004 | ENROLL SKIP 1000000 | 87.1 s | 0.021 s | Run B, F3 SKIP 1000000 |
| PIN-HIST-005 | ENROLL SKIP to top boundary | 529 s | 0.11 s | Run B, F4 SKIP -1000000000 |
| PIN-HIST-006 | ENROLL TOP SID (cross-run) | 72.169 s | 0.0013 s | Run A + Phase-1 closeout |
| PIN-HIST-007 | STUDENTS TOP SID | 19.478 s | 0.001–0.002 s | Run A, STUDENTS TOP SID |
| PIN-HIST-008 | STUDENTS TOP LNAME | 23.231 s | 0.001–0.002 s | Run A, STUDENTS TOP LNAME |

The "before" values are from the earlier buggy/partial builds in the same
session (endpoint fix using the wrong LMDB env path fell back to the 66 s scan;
first cursor-step did N re-seeks for large-N SKIP = 87 s). They are narrated in
`docs/maintenance/SESSION_CLOSEOUT_PINOCCHIO_NAV_PERFORMANCE_2026-07-18.md`.

Correctness canaries green throughout: SID `TOP` → record 1 = `50000000`
(Taylor Quinn), LNAME order begins at `Anderson`, `DESCEND` swaps endpoints, the
`SKIP` step sequence and boundaries land exactly.
