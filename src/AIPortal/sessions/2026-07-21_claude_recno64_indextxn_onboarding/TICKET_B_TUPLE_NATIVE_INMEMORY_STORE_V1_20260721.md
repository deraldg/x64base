# TICKET — B: Tuple-Native In-Memory Store (typed vector as the table)

**Type:** backlog / optimization-phase candidate · **Status:** deferred (review later) ·
**Filed:** 2026-07-21 · **Author:** Claude (steward) · **Authority:** Derald.
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
