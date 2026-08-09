# Co-Development Thesis — Ledger

> **Thesis (house doctrine, Derald):** New work *proves* the engine. Testing and
> documentation **co-develop** with the code — not after it. A feature build is also an
> audit of every surface it touches; latent defects that hide below the test frontier are
> flushed out by the act of reading and exercising those surfaces to build something new.

A thesis is an empirical, falsifiable claim — so it stands or falls on **proofs**, not
assertion. This ledger IS the proof-set. Each entry must actually demonstrate the mechanism
firing, and each is graded by strength.

### What counts as a proof (all three, or it's just a coincidence)
1. **Coupling:** building work A *required* engaging surface B (reading/exercising it).
2. **Yield:** a real defect fixed or invariant hardened in B resulted — not cosmetic.
3. **Co-development:** the test and the documentation moved *with* the fix, same session.

### Strength grading
- **Strong** — the defect was **structurally invisible to the existing suite**; only
  building A could have surfaced it. (These carry the thesis.)
- **Moderate** — building A found it faster/earlier than routine work would have.
- **Weak** — plausibly found anyway; logged for completeness, doesn't do much work.

### What would falsify / weaken the thesis (kept honest on purpose)
A run of feature lanes whose "read the surfaces you touch" pass yields **nothing**; defects
that only ever come from dedicated QA and never from adjacent building; or proofs that are
all Weak. If the ledger stops earning Strong entries, the thesis is decoration.

---

## Proof P1 (Strong) — 2026-07-21 · In-memory tables lane surfaced a RECNO64 read/write bug

**Building:** In-Memory Tables lane (AIF-043), M1 drop-1a — the behavior-preserving `io()`
byte-store seam. To place the seam I had to read the record read/write path
(`record_view.cpp::readCurrent`/`writeCurrent`).

**Surfaced:** those functions compute the record offset from **`_crn`** — the *clamped
int32 mirror* — not `_crn64` (`record_view.cpp:69–70`). `gotoRec64` clamps `_crn` to
`INT32_MAX` past 2³¹, so a read/write of any record beyond 2³¹ lands at the clamped
offset = **the wrong record**. A latent 🔴 truncation on the most fundamental op (read a
row), independent of the in-memory work.

**Why the whole existing suite missed it:** every fixture (`students`, x64/x32, the
throwaway tables) is far below 2³¹ records, so `_crn == _crn64` always — the clamp never
engages. The bug lives *below the test frontier*. Only reading the surface to build an
unrelated feature exposed it.

**Co-development in action:**
- **Code:** fix folds under AIF-027 as its own one-line drop — `checked_record_pos_(*this,
  _crn64)` in both functions.
- **Test:** wants a >2³¹ read/write proof (design note: a genuine 2³¹-row table is huge;
  the in-memory lane may enable a cheaper sparse/oracle probe — TBD in AIF-027).
- **Docs:** logged in `RECNO64_CARRIER_AUDIT_V1` + `M1_ASSEMBLY_IN_MEMORY_TABLES_V1` +
  this ledger, same session it was found.

---

## Further proofs this session

- **Proof P2 (Strong) — 2026-07-21 · SET INDEXTXN test build → `INDEXSEEK` freshness-mask.**
  Choosing how to *score* the INDEX_TXN flip forced a read of `cmd_indexseek.cpp`; found
  that `INDEXSEEK` re-verifies each candidate recno against the live DBF field, so it
  **cannot** be a freshness probe (it "finds" a row by the committed value even when the
  index key is stale). Yield: a would-be test that **false-passes under OFF** was averted;
  the test now scores on ordered position. Strong — the broken test would have shipped
  green. (Coupling ✓ yield ✓ co-dev ✓.)

- **Proof P3 (Strong) — 2026-07-21 · Same read confirmed O11 live in dev.** Reading
  `cdx_backend.cpp` for that work confirmed the LMDB cursor `uint32` recno truncation (O11)
  — invisible to the suite (all fixtures <2³¹) — was live in dev, seeding the whole RECNO64
  carrier audit + the L1/M4/M5 sweep. One feature's grounding became a correctness lane of
  its own. Strong. (Coupling ✓ yield ✓ co-dev ✓.)

## Scoreboard

3 proofs, all Strong (P1 in-memory→readCurrent, P2 INDEXTXN→INDEXSEEK, P3 INDEXTXN→O11).
Common thread: every yield was a defect **below the test frontier** (>2³¹ recnos, or a
DBF-masking probe) that routine testing could not have reached. That is the thesis earning
its keep — not decoration (yet; keep grading honestly).

---

## The operating rule this implies

1. **Every feature lane includes a "read the surfaces you touch" pass** — and treats it as
   an audit, not just orientation.
2. **Findings become steward items immediately** (right AIF, right severity), in the same
   session, before momentum moves on.
3. **The proof co-develops:** a fix without a test that would have caught it is only half
   the thesis. Where a direct test is impractical (e.g. >2³¹ rows), record the test-design
   debt explicitly rather than silently.
