# DTS Authoring & Data-Environment Rules (co-developed)

Session 2026-07-21. Captured from live maintainer corrections while writing the
`INDEX_TXN` regression. These are engine facts a script author (human or AI) must
respect; documenting them alongside the test is the co-development thesis in
practice — the proof and its rules land together.

## Data-tree layout (one place per artifact kind)

- Tables live under **`data/dbf/<flavor>`**: `x64`, `x32`, `SANDBOX`, etc.
  `x64` and `x32` carry the canonical MCC student dataset. **`SANDBOX` has its own,
  independent (and often stale) copies** — e.g. a months-old `students.dbf`. It is
  scratch, not a mirror of x64.
- Indexes live under **`data/indexes/<flavor>`** (`.cdx`, `.cdx.meta`, `.cnx`, `.inx`).
- LMDB envs live under **`data/lmdb/<flavor>`** (`<stem>.cdx.d/`). Only **x64** uses LMDB.
- The path slots default to `data/dbf`, `data/indexes`, `data/lmdb` at the DATA root;
  a flavor is selected by pointing the slots at the subfolder.

The sample scripts `x64.dts`, `x32.dts`, `sandbox.dts` (run via `DO x64` etc.) do exactly
one thing: set the DBF/INDEXES/LMDB path slots to that flavor.

## Environment rules a self-bootstrapping script must obey

1. **Set the SOURCE environment before you open anything.** `USE students` resolves
   against whatever the DBF slot currently points at. Point at `SANDBOX` first and you
   silently open SANDBOX's stale `students`, not the x64 fixture — a wrong-source pass,
   not an error. Establish the flavor (`DO x64` / point the slot at `x64`) *before* `USE`.

2. **`USE` only opens-and-selects when the table isn't already open.** If it is already
   open (e.g. the startup workspace or a prior `WORKSPACE OPEN` pulled it in), a second
   `USE <table>` prints a harmless "already open in area N" warning and **does not change
   the current area**. To make an already-open table current, use **`SELECT <table>`**
   (or its area number). Reserve `USE` for genuinely-new opens.

3. **`WORKSPACE OPEN` and `WORKSPACE LOAD` each do a workspace-close first.** So a
   standalone `WORKSPACE CLOSE` is redundant when you're about to open/load — issuing
   open/load already clears the areas.

4. **Startup restores a workspace.** Boot performs a `WORKSPACE LOAD` (e.g. "restored 12
   area(s)"). A gratuitous `WORKSPACE CLOSE` in a test tears down the workspace the user's
   session just restored. Don't close the ambient workspace unless the test truly owns it.

5. **Prefer fixture-free bootstrap.** The cleanest self-contained test builds its OWN
   throwaway table from scratch (`CREATE X64 …` → `APPEND`/`REPLACE` → `CDX CREATE`/`ADDTAG`
   → `BUILDLMDB`) and `ERASE`s it at the end. This sidesteps every rule above: no dependence
   on where `students` lives, no double-`USE`, no workspace teardown, no stale-SANDBOX trap.
   Template: `pinocchio/wal_commit_rollback_regression.dts`.

## Regression-script doctrine (reinforced)

- **Set your own environment at the top:** `SET ECHO OFF`, `STOP_ON_ERROR OFF`. With
  `STOP_ON_ERROR OFF`, a leading `ERASE TABLE <t> CONFIRM` is idempotent (absent table =
  non-fatal), and a mid-script error still reaches the cleanup that restores globals.
- **Restore any global you flip.** `INDEX_TXN` flips `SET INDEXTXN`; it must
  `SET INDEXTXN OFF` at cleanup so it doesn't dirty the ambient for the next test (and
  why it stays out of the default suite).
- **Self-assert, don't narrate.** Emit machine-checkable markers via the expression path
  (`? "TAG:" + (<predicate>)` → `TAG:.T.`/`.F.`), bracketed by `FORMULA "…-BEGIN"` /
  `"…-END"`. An `ECHO EXPECT…` + eyeballed `TUP` test can never go red — it's a silent
  no-op, the exact bug that retired the legacy `commit_rollback_test.dts`.
- **Never issue a screen `CLEAR`/`CLS`.** A regression/smoke is *harvested by cut-paste*;
  a screen clear wipes the scrollback (version banner, splash, all prior markers) and
  destroys the transcript. `CLEAR VAR` (clears memvars, not the console) is fine; the bare
  `CLEAR`/`CLS` is banned in any suite script.

## How to score index freshness in a test (learned the hard way)

- **Do not score on the landed field after a SEEK.** A not-found `SEEK` leaves the
  cursor parked where it was, and `COMMIT` writes the DBF even when the index is not
  maintained. So `? "…" + (ALLTRIM(FIELD) = "sentinel")` can read the committed value
  off a parked/deleted record and *false-pass* under `SET INDEXTXN OFF`.
- **`INDEXSEEK` cannot be a freshness probe.** It is a command (prints
  `INDEXSEEK(): <recno>`, not an expression value), and `cmd_indexseek.cpp` re-confirms
  each candidate recno against the *live DBF field* before returning. That verification
  masks a stale index: it will still "find" the row by matching the committed DBF value
  even when the index key is stale. Great for a trustworthy lookup, useless for proving
  the index itself is fresh.
- **Score on ordered traversal (`TOP`/`BOTTOM`/`SKIP`).** Ordered nav materializes the
  recno vector purely from index order and does not re-verify against the DBF, so a stale
  index shows stale order. A sentinel key that sorts last (`ZZ_…`) makes `BOTTOM` a clean
  ON=green / OFF=red discriminator. Use a duplicate-key set so the surviving row outsorts
  the mutated one and the flip stays unambiguous.

## Housekeeping observed

`indexes/SANDBOX` holds orphan `.cdx.meta` files from aborted runs
(`students_txn_smoke.cdx.meta`, `students_cdx_smoke.cdx.meta`) — a `.meta` with no matching
`.dbf`/`.cdx`. Harmless, but a from-scratch test avoids creating them, and they can be
swept when convenient.
