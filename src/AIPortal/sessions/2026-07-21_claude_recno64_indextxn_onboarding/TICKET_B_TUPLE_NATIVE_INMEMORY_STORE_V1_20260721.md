# TICKET — B: Tuple-Native In-Memory Store (typed vector as the table)

**Type:** backlog / optimization-phase candidate · **Status:** ❌ KILLED at Phase-0 gate
(2026-07-22) — see "Phase-0 result" below · **Filed:** 2026-07-21 · **Author:** Claude (steward)
· **Authority:** Derald.

> ## Phase-0 result — KILL (2026-07-22)
>
> Ran the go/no-go decode-cost benchmark (`data/scripts/pinocchio/ticketb_phase0_decode_cost.dts`,
> then a wall-clock `Measure-Command` harness because the engine's in-script `SECONDS()`/`SET
> TIMER` reports 0) over the 1,000,000-row pinocchio STUDENTS table:
>
> | measure | time | per-row |
> |---|---|---|
> | startup | 0.35 s | — |
> | DEC1/scan (COUNT FOR GPA>=0, 1 field) | 39.07 s | ~39 µs/row |
> | DEC3/scan (3 field predicates) | 92.52 s | ~93 µs/row |
> | per added predicate term | 26.7 s/1M | ~26.7 µs/row |
>
> **Interpretation.** A single-field predicate scan of 1M rows taking ~39 s is ~1000–10000×
> slower than it should be. The `DEC3−DEC1` delta measures the cost of extra *predicate terms*
> (field-resolve + extract + decode + compare + AND-node through a tree-walking interpreter), not
> pure field decode; byte→value decode is a small sliver inside it. The naive `decode_fraction =
> 1.368` therefore does NOT mean decode dominates — it means the **evaluator / field-access path
> dominates.**
>
> **Why B loses.** (1) Option B still routes every field reference through the same tree-walking
> evaluator; it would run this 39 µs/row loop over typed cells unchanged. (2) If the per-term cost
> is field *extraction* (per-field allocation/boxing), that is fixable **inside Option A** —
> offset-cached, allocation-free, decode-in-place field access — far cheaper and lower-risk than
> rebuilding the store as a typed vector in the maintainer-owned tuple core. Either way, swapping
> the store representation is the wrong lever. Per this ticket's own kill criterion, B is
> "complexity without payoff" because A can capture the win more cheaply.
>
> **Redirect (the real optimization target).** The leverage is the **expression/scan evaluator +
> field-access path**: compile predicates once, resolve field names to offsets once, decode in
> place without allocation/boxing. Orders of magnitude, in Option A, no tuple-core changes.
> Recommend a separate lane for that; do not reopen B unless a *columnar/vectorized execution*
> project (its own scope, not "typed vector as the store") is explicitly chartered.
>
> The Phase-0 gate did its job: zero tuple-core code spent; the store was proven not to be the
> problem.

**Original ticket (retained for context):**
**Parent lane:** AIF-043 In-Memory Tables (charter row A2 "pure arena adapter").
**Blocked-by / sequencing:** ships *after* M1 (Option A, `ramfs` byte store) is stable —
this is an optimization, not a prerequisite. **Not scheduled; review in the optimization phase.**

## Decision context (why deferred, not rejected)

M1 chose **Option A — RAM bytes**: the in-memory table is a contiguous byte buffer
byte-identical to a `.dbf`, so the whole engine (recno nav, CDX, INDEXTXN, commands, snapshot)
runs unchanged. Option A stores exactly the fixed-width rows the tuple system already builds.

**Option B** promotes the typed tuple vector to *be* the store: rows kept as
`std::vector<Row>` of already-parsed typed cells, never serialized to bytes on the hot path.
It is a genuine advanced-DB architecture (Hekaton / HANA / VoltDB-style in-memory typed /
columnar tables), but it re-implements the machinery A gets free from the byte format, and it
lands in the tuple core — which is maintainer-owned. Hence: earn it in the optimization phase,
on top of a working A, where its wins actually pay for the work.

## What B is

- Table = `std::vector<Row>`; a Row is typed cells (leveraging `TupEntry`/`TupleRow` shapes),
  not a byte slab. Record access is `rows[i]` — no offset math, no per-read field decode.
- The bytes become a *projection* (serialize on snapshot/export), not the source of truth.

## What B must build (the cost A avoids)

1. **Recno navigation over the vector** — TOP/BOTTOM/SKIP/GOTO/append/replace/delete against
   an indexable typed array (re-doing what `DbArea` does over bytes).
2. **Index feed without record bytes** — the CDX/LMDB backend composes keys from record bytes;
   B has no bytes, so the index must key off the typed cells → a new feed path (or an on-demand
   row-serializer just for the index).
3. **DBF-fidelity edge cases** — deleted flag, exact padding, memo semantics — re-expressed in
   the typed model (A inherits them from the format for free).
4. **Snapshot/export** — serialize the vector to a real `.dbf`/`.cdx` on demand.

## Why it's worth reviewing later (the payoff)

- **No re-parse:** repeated typed field access skips the decode A pays each read.
- **Columnar path:** a typed store opens column-oriented storage/ops — the real analytics win
  (aggregations, vectorized scans), the reason mainstream engines do this.
- **Richer joins / relations:** typed cells + provenance fragments compose more directly than
  byte slabs; ties into the tuple projection and REL work.

## Falsifiable success criteria (for when it's picked up)

- A RAM table on B passes the **same** `REGRESSION MEM_TABLE` proof as A (CREATE/APPEND/
  REPLACE/CDX/nav, ephemeral), i.e. B is a drop-in substrate, not a fork of behavior.
- Demonstrated win over A on a **repeated-scan / aggregation** benchmark large enough that the
  decode A pays is measurable — otherwise B is complexity without payoff (kill criterion).
- Tuple core changes are additive and reviewed (maintainer-owned surface).

## Sequencing

Optimization phase, after M1 (A) + M2 (index) are green. Revisit alongside the charter's
M4 (native CDX-in-RAM) / M5 (typed-tuple + relations polish), which share the typed-store thesis.
