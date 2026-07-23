# PROJECT LANE — Bulk / Sequential Record-I/O Scan (read the file once, not row-by-row)

**Type:** optimization lane · **Status:** **STAGED (chartered; not started; Phase-0 go/no-go owed)**
· **Filed:** 2026-07-22 · **Author:** Claude (steward) · **Authority:** Derald.
**Origin:** the completion of the scan-evaluator optimization lane (M1–M4), which drove the per-row
*evaluator + decode* cost out of the scan and, in doing so, exposed the **next** bottleneck: per-row
record fetch. **AIF:** candidate new lane; maintainer assigns the number.

## Why this lane exists (the finding)

After the scan-evaluator lane (compile-once, field-bind-once, selective/allocation-free decode,
aggregates), a full 1,000,000-row physical scan of pinocchio STUDENTS costs **~21 µs/row** whether
it is a bare aggregate (`SUM GPA`) or a one-field predicate (`COUNT FOR GPA >= 0`) — the two now sit
on top of each other. Almost none of that is expression evaluation or field decoding anymore. It is
**per-row record fetch**: the scan loop does, for every record,

```
area.gotoRec(r);        // position the cursor on record r
area.readCurrentRaw();  // io().seekg(pos); io().read(_recbuf.data(), rec_len)
```

That is ~1,000,000 individual `seekg` + `read` pairs (plus whatever `gotoRec` recomputes per call)
over a file whose data pages are almost certainly already in the OS cache (the fixtures live on a
Samsung 970 EVO NVMe and the table is ~tens of MB). So the residual is call/copy/positioning
overhead paid once per row, not disk latency. Reading the records **in blocks / streaming the file
once** should collapse it.

## Phase-0 — go/no-go (REQUIRED before any code)

The residual has two candidate owners; Phase-0 must decompose them before a single line changes,
exactly as Ticket B's Phase-0 did:

1. **`gotoRec(r)` cost.** Instrument (or micro-bench) a loop that only positions the cursor for
   `r = 1..N` with no read. If a physical-order `gotoRec` does per-call work that a sequential walk
   would not (order/index consultation, path recompute, bounds math), that is hoistable
   independently of I/O.
2. **`readCurrentRaw()` cost.** A loop that reads each record with the cursor already positioned.
   This isolates the `seekg` + `read` + copy-into-`_recbuf` overhead.

**Decision rule.** If `gotoRec` dominates → the fix is a *sequential cursor* (advance without
re-positioning), cheap and low-risk. If `readCurrentRaw`'s `seekg`+`read` dominates → the fix is a
*block reader* (read K records per `read()` into a reusable buffer, hand out slices). If the residual
is genuinely memory-bandwidth (already near `memcpy` of the table), **KILL** — there is no software
lever left and the honest answer is "the engine is at hardware speed for a full scan."

Bench = the existing `PHASE0_DECODE_COST` harness plus a positioning-only and read-only variant.
Same host, `DECx − SUM`-style normalized reads.

## Thesis: one sequential pass, block-buffered, for physical-order scans

For a **physical-order** full/rest scan (no active index order), read the DBF data region
sequentially in large blocks into a reusable buffer and iterate records as slices of that buffer,
instead of one `seekg`+`read` per record. Positioning becomes pointer arithmetic; the syscall/copy
count drops from O(rows) to O(rows·rec_len / block_size).

This is additive and **physical-order only** — an ordered scan (CDX/LMDB cursor) visits records in
key order, which is inherently non-sequential in the file, so it is out of scope for the sequential
fast path (it keeps the current per-row fetch, already fine because index scans are seek-bound by
nature). The lane targets the common `COUNT/SUM/LIST/SCAN … FOR` over physical order.

## Milestones (each Phase-0-gated; prove before proceeding)

- **M0 — decompose + baseline.** Split `gotoRec` vs `readCurrentRaw` per-row cost (above); record the
  floor. Decide sequential-cursor vs block-reader (or KILL).
- **M1 — sequential physical cursor.** For physical-order scans, advance the cursor without
  re-seeking; read forward. Expected: kills the `gotoRec` re-position cost.
- **M2 — block reader.** Read the data region in large blocks into a reusable buffer; expose records
  as spans (feeds the existing selective-decode field access, which already reads from a buffer).
- **M3 — wire the scan consumers.** `collect_selected_recnos` and `cmd_aggs` opt into the sequential
  block path when the scan is physical-order, no active filter needing per-row work beyond the
  predicate, and the table is not mid-mutation (buffered/dirty rows must still read correctly).

## Falsifiable success criteria

- **Speed:** a physical-order `COUNT FOR GPA >= 0` / `SUM GPA` over 1M rows drops from ~21 µs/row
  toward memory-bandwidth (target: well under 1 s for the full scan; a ~100 MB sequential read from
  cache is single-digit ms of pure I/O, so the ceiling is high). Bench = the Phase-0 harness.
- **Parity:** identical counts/aggregates and identical record contents vs the per-row path
  (`REGRESSION ALL` + the pinocchio proofs); deleted-flag, buffered/dirty rows, and memo fields must
  read the same.
- **Scope honesty:** ordered (index) scans are explicitly unchanged; the sequential path is
  physical-order only and gated.

## Governance / boundary (high blast radius)

This touches the **core record-read path** (`DbArea` read I/O, `readCurrentRaw`/`_recbuf`, and the
`ramfs`/stream layer) used by essentially everything. Same discipline as the scan-evaluator lane:
strictly **additive** (a new sequential/block path beside the untouched per-row `readCurrent`),
tightly **gated** (physical order, no conflicting filter, not mid-mutation), and **parity-gated** by
the full regression suite before promotion. Report-only until reviewed. Phase-0 may KILL it.

## Cross-references

- Origin / handoff: `PROJECT_LANE_SCAN_EVALUATOR_OPTIMIZATION_V1_20260722.md` (§ Lane status —
  COMPLETE; the ~21 µs/row per-row-I/O residual finding).
- Bench: `dottalkpp/data/scripts/pinocchio/ticketb_phase0_decode_cost.dts` (extend with
  positioning-only and read-only variants for M0).
- Core surfaces: `src/xbase/record_view.cpp` (`readCurrentRaw`, `readCurrent`, `checked_record_pos_`,
  `_recbuf`), `include/xbase.hpp` (DbArea read path), the `ramfs`/stream layer; consumers
  `src/cli/scan_selector.cpp` (`collect_selected_recnos`) and `src/cli/cmd_aggs.cpp`.
