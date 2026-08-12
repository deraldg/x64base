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

---

## Proof P4 (Strong) -- 2026-08-12 -- A FIXTURE chore surfaced silent data destruction in FIELDMGR APPEND

**Building:** AIF-070 Part B (task #168) -- a *data* task, not an engine task: add `NOTES M`
to the canonical MCC `STUDENTS`/`TEACHERS` fixtures so MINIDB containers would have real
memo sidecars to carry. The owner ruled the mechanism must be in-engine ("build the verb,
not a host-side one-off"), which required engaging `FIELDMGR APPEND` and its rewrite
(`src/core/fields_mgr.cpp::append_rewrite_table`).

**Surfaced:** the rewrite loop **never called `writeCurrent()`**. `set()` only stores into
the in-memory `_fd` vector; `appendBlank()` writes a space-padded row to disk immediately
and the *next* `appendBlank()` discards the pending values (`dbf_file.cpp` appendBlank ->
gotoRec64 -> readCurrent). Every `set()` returned true into a buffer nobody flushed, so the
verb silently replaced 200 rows of real data with 0x20 -- **while record count, schema,
field descriptors, and deleted flags all read correct.**

**Why the whole existing suite missed it:** `FIELDMGR APPEND` had no regression at all, and
-- the sharper half -- its failure mode defeats *shape-based* checking. A test that opened
the table and asserted "200 records, 10 fields, NOTES present" would have **passed green on
a blanked table**. Same family as P1: the defect lives below the frontier of what the
existing proofs can see, not merely outside their coverage.

**Co-development in action:**
- **Code:** the missing `writeCurrent()` inside the loop, before `deleteCurrent()`; plus two
  more defects the same read exposed -- the X64M identity stamped from the TEMP path stem
  (identity-explicit `create_dbf` overload), and long x64 field names *refused* rather than
  merely untested (ceiling raised to the X64M authority, legacy re-tightened, descriptors
  routed through `field_name_policy`'s `~n` mangler).
- **Test:** proven on throwaway copies (short-name memo append + 19-char long-name append,
  values read back BY LONG NAME, hex-verified record bytes) then on canonical fixtures
  (PB_T1..T4). Test-design debt recorded explicitly, not silently: the FIELDMGR_APPEND
  regression spec (short-name / long-name / **deleted-row** arms) is owed -- the deleted-row
  arm matters because `deleteCurrent()` ends in its own `writeCurrent()`, so deleted rows
  would have survived correct; MCC has none, which is why the corruption was 200/200.
- **Docs:** AIF-110 claimed and its intake row written the same session, then **amended when
  measurement contradicted the first diagnosis**; usage contract updated; migration script
  header carries all five runs' lessons; guard raised *and* lifted in-session; neighbor
  notice posted to `board.notice` #9 with the risk shape in plain words ("check values, not
  counts").

**Grading note (honest):** P4 is Strong, but by a partly different mechanism than P1-P3.
Those were invisible because no *fixture* could reach them (recnos above the 32-bit clamp).
P4 was invisible because the verb was untested **and** because its failure shape passes
every structural assertion. Both are "below the test frontier"; the second variety is
arguably more dangerous because it survives naive testing.

---

## Proof P5 (Moderate) -- 2026-08-12 -- Probe-before-number surfaced the ramfs bypass ledger

**Building:** a runtime probe for an unattributed four-day-old BBS defect report ("descending
path looks off"), under the house probe-before-number rule. Building it required exercising
index creation inside the RAM VFS.

**Surfaced:** two more members of the ramfs-bypass family -- `INDEX ON` writes its INX via
`std::ofstream` (bypasses the VFS entirely), and `CNX ADDTAG`/`REBUILD` existence-check the
**real filesystem** for a container `CNX CREATE` had just placed in the VFS. Member 1 (the
DTX memo sidecar) was found 2026-08-11 by the same kind of pass.

**Yield:** the probe's own v1 was an invalid run (six false reds from a dead scaffold), which
produced a durable guard pattern: `DS_G0`, a liveness marker that makes "the scaffold failed"
self-announcing rather than masquerading as a finding. The original report closed **green**
with evidence and no AIF claimed -- a negative result, recorded as such and answered on the
board.

**Grading:** Moderate. The bypasses are measured findings and a documented ledger, not fixed
defects; a dedicated ramfs-coverage pass would plausibly have found them too.

---

## Proof P6 (Strong) -- 2026-08-12 -- Rebuilding an index surfaced that the documented reset rule was incomplete

**Building:** Part B's index rebuild after the schema change (the MCC README's reset rule:
"`CDX CREATE` refuses an existing container, so delete it first").

**Surfaced:** deleting only the `.cdx` is **not** a reset. CDX identity lives in a separate
`<container>.cdx.meta` sidecar (`src/xindex/cdx_meta.cpp`), so a freshly created container is
still judged by the stale identity and refuses to attach -- with a `metadata mismatch`
message that names the *table* and looks like a table problem.

**Yield:** doctrine corrected in place; the reset rule gains its corollary (delete BOTH, and
the `.gitignore` policy that keeps `.cdx.meta` untracked-because-regenerable is exactly why
it survives a naive cleanup). Cost of not knowing it: two full investigation cycles this
session chased a "table" defect that was an index-identity artifact.

**Co-development:** migration script header, intake row, and the `board.notice` neighbor
warning all carry it; it is stated as a rule, not as an anecdote.

---

## Scoreboard

**6 proofs: 5 Strong, 1 Moderate** (P1 in-memory -> readCurrent, P2 INDEXTXN -> INDEXSEEK,
P3 INDEXTXN -> O11, P4 fixture-chore -> FIELDMGR blank-corruption, P5 probe -> ramfs bypass
ledger, P6 index-rebuild -> `.cdx.meta` reset corollary).

Common thread, now across two eras of the project: every Strong yield was a defect **below
the test frontier** -- either unreachable by any fixture (recnos above the 32-bit clamp,
DBF-masking probes) or **invisible to shape-based assertions** (blank records wearing a
correct header). The 2026-08-12 entries also extend the thesis in a direction P1-P3 did not
test: the *building* work was a data/fixture chore and a documentation-driven probe, not a
feature lane -- the mechanism fired anyway.

**Falsification watch (kept honest):** the criteria say the thesis decays if lanes yield
nothing or yield only Weak entries. Counter-evidence to log fairly -- the 2026-08-11
workspace sessions (catalog v2, DTSHEMA 3, MINIDB) produced *corrections to my own claims*
(the DTX "zero disk writes" error, the 13-vs-24 CDX variance) rather than latent engine
defects; those are honest-record wins, not thesis proofs, and are deliberately **not**
counted here. One lane in three yielding a Strong engine defect is the current,
unembellished rate.

**Process note, logged against myself (2026-08-12):** this ledger entry was itself written
with em-dashes, arrows, and superscripts, and the author asserted "house standards applied"
before the house-style gate proved otherwise. The gate caught it; the AIF-090 fixer then
REFUSED the file because the historical P1-P3 text contains codepoints it has no mapping for
(superscript one, a red-circle emoji) -- so the repair was hand-done on the added lines only,
leaving the 2026-07-21 record verbatim. Two lessons worth more than the typos: an assertion
of compliance is not compliance (the golden rule applies to process claims, not just
technical ones), and a normalizer that refuses unknown input is behaving correctly even when
that blocks the convenient path.

---

## The operating rule this implies

1. **Every feature lane includes a "read the surfaces you touch" pass** — and treats it as
   an audit, not just orientation.
2. **Findings become steward items immediately** (right AIF, right severity), in the same
   session, before momentum moves on.
3. **The proof co-develops:** a fix without a test that would have caught it is only half
   the thesis. Where a direct test is impractical (e.g. >2³¹ rows), record the test-design
   debt explicitly rather than silently.
