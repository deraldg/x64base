# Memo Sidecar Reclamation -- Lane V1

    lane        : AIF-163 (`memo-sidecar-reclamation`)
    claim       : coordination/aif/AIF-163.claim
    run         : AIFGEN-20260914-105334
    parent      : project.x64base.runtime
    owner       : member.derald
    steward     : member.ai.claude.cowork
    opened      : 2026-09-14, on the owner's reversal of his own 2026-08-31
                  no-number ruling. The reversal and what justified it are in
                  section 1; the earlier refusal was correct when it was made.
    evidence    : MIXED. Section 3a is RUNTIME-PROVEN on binary `b9289317`;
                  everything else is measured-from-files or source-evidenced.
    ships       : review-needed. The author does not self-approve.

**NOTHING IS BUILT.** This charter records a measurement and a shape, not an
implementation.

---

## 1. Why this is a lane now, when it was correctly refused before

**2026-08-31, owner:** no AIF number. *"Afterwards we concentrate on getting this
finished rather than another undone stale aif."* R133 agreed from the other side:
a lane holding one Phase-0 is a sentence in someone else's document. **That was
right.** What existed then was one measurement of one store and a parked topic.

**2026-09-14, owner: reversed.** What changed between the two rulings:

- **It is TWO separable problems, and one of them needs no ruling at all.**
- **Three stores, not one.** SRCBLOCK 85.5 percent unreachable, SYSFUNC 81.3,
  SRCUSAGE 79.3 -- the latter two first measured 2026-09-14.
- **A RUNTIME-PROVEN result that overturned BOTH of the steward's readings.** The
  prior recommendation -- "the sweep already ships, just run PACK" -- is dead.
- **A probable defect in a shipped command** (section 5), with an owner question
  attached and no home without this lane.
- **The work had no ledger presence.** Nothing in the tree said it existed. That
  is the curate-or-lose-it rule (owner, 2026-08-13) applied to this lane.

**DELIBERATELY NOT NAMED "COMPRESSION."** The measurement retired that frame:
per-object zlib is a NET LOSS (0.97x) on the store that needed help most, and the
collectable work is reclamation. Naming the lane for the disproved entry point
would mislead every future reader, which is the failure mode the naming rules in
`AI_README.md` exist to prevent.

## 2. Scope

**In:** reclaiming dead bytes from DTX memo sidecars -- unreferenced objects,
superseded and deleted-row payloads, duplicate object ids, and the atomicity any
of that requires.

**Out, named so it is not assumed:**

- **Compression itself.** Still parked; still the owner's judgement call. This
  lane MEASURES it (section 6) and does not build it.
- **Legacy `.dbt` / `.fpt`** -- 28.8 MB of the live sidecar mass, refused by PACK
  outright, a separate question.
- **The journal.** AIF-160 owns it; this lane is a consumer at most.
- **The reachability RULING.** AIF-061 M3 owns it (section 7).

## 3. What is measured

### 3a. RUNTIME-PROVEN

Binary `b9289317`, built Sep 13 2026 20:16:35 (MSVC Release). Run 2026-09-14 by
`member.derald` on grimwood, on COPIES in `dottalkpp\data\dbf\sandbox`. No live
data touched. Log: `dottalkpp\data\tmp\pack_probe_20260914-*.txt`.

- **PACK on `WORKSPACES` (`M(16)`, 148 deleted rows): PACKED, NOT REFUSED.**
  203,012 -> 97,192 B; 282 rows -> 134. Arithmetic closes:
  `1381 + 134 * 715 + 1 = 97,192`. **The DTX is byte-identical afterwards (md5).**
  110 objects (2,305,296 B, 74.0 percent) become unreachable; zero dangling.
- **PACK on `SRCBLOCK` (`M(8)`, 0 deleted rows, 7,559 orphans): NO-OP.** Both
  files md5-identical to source. **PACK is deletion-driven, not
  reachability-driven.**

Both outcomes were PREDICTED BACKWARDS by the steward, in writing, before the
run. See section 8.

### 3b. Measured from files, 2026-09-14

The device mount has been down since 2026-09-08 (Windows update); these were
measured by staging files and walking them with the in-tree reader
`tools/memo/dtxread.py`.

    store                      rows  del   objs   unreachable          share
    comments/SRCBLOCK          1279    0   8838   7559 / 226,770 B     85.5%
    metadata/SYSFUNC             79    0    425    346 / 101,235 B     81.3%
    comments/SRCUSAGE           244    0   2727   2162 / 419,193 B     79.3%
    messaging/SYS_MESSAGE_TEXT 1270    0   1270      0 /       0 B      0.0%
    workspaces/WORKSPACES       282  148    121      0 /       0 B      0.0%

    O4 projection (sidecar-only, id-preserving, policy P1):
      five stores  5,003,184 -> 3,590,352 B    reclaimed 1,412,832   28.2%

    WORKSPACES tier split (shares UNCHANGED across 14 days):
      A active/current          5 objs    212,969 B    6.8%
      B active/superseded       6 objs    595,864 B   19.1%
      C deleted/superseded    110 objs  2,305,296 B   74.0%

Fourteen days, nine new rows, two new objects -- **both landed in tier C.** The
current slice does not grow; the dead slice does.

**Duplicate object ids, two stores:** SRCBLOCK holds 8,918 object records at
8,838 distinct ids (80 duplicates, a contiguous run from 4226);
`ram/WORKSPACES` holds 5 at 3. `_live_index` is keyed by id so the later record
silently wins, and the header's `object_count_live` reports the DISTINCT count --
so nothing surfaces it.

## 4. Milestones

**M0 -- the number and the row.** This charter, the intake row, and
`coordination/aif/AIF-163.claim`, in one commit. The collision gate checks the
pair. Closes when the gate passes.

**M1 -- the orphan sweep. NO RULING REQUIRED.** An object no row references
cannot owe a reader anything, so `WORKSPACE DESTROY`'s promise is not in play.
Shape: sidecar-only and id-preserving -- build `S.new` from the reachable set at
their ORIGINAL ids, rename over `S`. **One file, one rename**, which is R136's
easy class, with no journal and no group log. Target 1,412,832 B across three
stores. Gradeable: reclaim measured, zero dangling after, and the memo zoo green.

**M1a -- the directory sync.** `xbase::durable_sync` syncs CONTENTS and
explicitly not the directory, and `include/xbase/durable.hpp` names **the
compaction case (R136's multi-file class)** as the gap that "needs its own answer
along with the journal." M1 creates a file and renames it, so it needs the
sibling primitive. Reusable by anything that creates a file. **This is the only
shipped-code work M1 cannot avoid.**

**M2 -- the catalog, and the ruling it needs.** WORKSPACES gets NOTHING from M1.
Two routes, and the first is cheaper than it looks:
  - **PACK then sweep.** Section 3a proves PACK already converts tier C into
    orphans; M1 then collects them with no tier ruling at all. **The promise
    question does not vanish -- it MOVES onto PACK**, which is what destroys the
    destroy-history. That is a pre-existing question about PACK.
  - **Rule the tiers directly.** B (595,864 B) and C (2,305,296 B) separately.

**M3 -- the PACK contract defect** (section 5).

**M4 -- duplicate ids.** Decide whether a sweep RENUMBERS (fixing them, as PACK's
copy-forward does) or PRESERVES ids (keeping them, as M1 specifies). **M1 as
written does NOT fix them.** Recorded so the choice is deliberate rather than a
side effect nobody noticed.

## 5. The defect this lane inherits

PACK's `@dottalk.usage` declares `mutates: table-file closes-table order-state
memo-sidecar index-dirty-state`. **On an `M(16)` memo table it does not mutate
the sidecar -- measured byte-identical -- it STRANDS it.** No corruption, no
dangling reference, and no shipped way to reclaim what it stranded. The table
shrank 52 percent while the sidecar held, so the ratio went from 15.4x to 32.2x:
**PACK made the imbalance worse.**

The contract is accurate for the `M(8)` case it was written for and misleading
for the `M(16)` case nobody checked.

**THIRD INSTANCE OF THE M(8)/M(16) SPLIT AS AN UNDOCUMENTED DISCRIMINATOR**,
after the blank-slot read defect (`read_u64_le` has no blank guard on the 8-byte
form while `ref_token_is_blank` guards the 16-char form) and the PACK support gap
(`has_x64_memo_fields` hardcodes `f.length == 8`). One field width, three
divergent behaviours, none stated anywhere as a property of the width. **Whether
that pattern is itself a lane is an owner call and is NOT claimed here.**

## 6. Compression, kept in scope as a MEASUREMENT only

Per-object zlib-6, which is the unit `MF_COMPRESSED` can express:

    workspaces/WORKSPACES  5.38x        comments/SRCUSAGE   1.56x
    metadata/SYSFUNC       1.42x        messaging/SYS_MSG   1.13x
    comments/SRCBLOCK      0.97x   <-- NET LOSS
    (whole-store on SRCBLOCK: 28.39x -- the gap is cross-object redundancy
     that a PER-OBJECT flag cannot reach)

And the affordances are not where the parked handoff said they were:
`MF_COMPRESSED` lives in `include/memo/memo64.hpp`, a header with **no
implementation and no caller**; persisted `content_type` lives in
`src/memo/x64_memo_store.cpp`, **excluded from the build by regex at
`src/memo/CMakeLists.txt:14`**; and the live DTX store has two size fields it
always sets equal, **no flags word at all**, one `PayloadKind` that is always
`TextUtf8` across all 13,460 measured objects, and a `payload_crc32` hardcoded
to 0.

**So compression stays parked and this lane does not open it.**

## 7. Dependencies, and what this lane does NOT own

- **AIF-061 M3** owns the reachability RULING -- *"Decide explicitly whether memo
  objects are reference-counted or garbage-collected -- this is where a half-fix
  rots."* M1 proceeds on the NARROW reading (unreferenced is unreclaimable by
  anyone) precisely because that reading needs no ruling. Anything wider waits.
- **AIF-160** owns the group log and prepare/decide/apply. **M1 deliberately does
  not need it**; M2's direct route might.
- **AIF-078** shipped `durable_sync` and declared the directory gap M1a fills.
- **AIF-070** the memo zoo is the acceptance gate. Its `random_bytes` payloads do
  not compress -- under zlib they EXPAND -- so it is adversarial in exactly the
  right direction. **No new fidelity harness should be built.**
- **AIF-108** is an open challenge over this exact surface; a sweep is a
  legitimate target for it.

## 8. The steward was wrong twice, and the mechanism caught it

Both PACK outcomes in 3a were predicted backwards, in a document written before
the run, which is why a two-minute probe on copies overturned two documents
instead of a design being built on top of them.

- **"A zero-deletion table still gets swept."** The copy-forward loop
  (`cmd_pack.cpp:607-651`) was read correctly. **What gates ENTRY to it was never
  checked.** Reading a loop is not reading the condition that reaches it.
- **"PACK refuses the `M(16)` table."** `has_x64_memo_fields` really does require
  `f.length == 8` -- that half was right. `memoKind()` was the wrong half, read
  from its call site rather than its implementation, and it evidently returns
  `NONE` for a DTX-only table so the guard never fired. **The prior document's
  own NOT CLAIMED said `memoKind()` had not been traced, and a confident heading
  was written above the caveat anyway.**

**A stated NOT CLAIMED is not a licence to assert the thing in the title.**

## 9. NOT CLAIMED

- **Nothing is built and no compaction has ever been run by this lane.** Every
  reclaim figure is a projection.
- **M1 is not designed in detail.** Id-preservation is reasoned from
  `src/memo/memostore.cpp`, not tested.
- **`memoKind()` still not traced.** Twice reasoned about, never read.
- **The PACK log was not read.** Section 3a is established from file bytes, sizes
  and md5; what PACK PRINTED for SRCBLOCK is unquoted, so "deletion-driven" is a
  strong inference rather than a quoted refusal.
- **SRCUSAGE and SYSFUNC were not PACK-tested**, only measured.
- **Index consequences untested.** PACK's contract requires containers be rebuilt
  after; the sandbox copies had none attached.
- **The mount is down**, so nothing here can be re-measured today, and no figure
  should be quoted as current without a re-run.

## 10. Evidence

    claude/MEASUREMENT_THE_GARBAGE_IS_TWO_PROBLEMS_AND_ONE_NEEDS_NO_RULING.md
    claude/MEASUREMENT_PACK_RAN_AND_BOTH_PREDICTIONS_WERE_WRONG.md
    claude/OPTIONS_HOW_COMPACTION_COULD_BE_MADE_SAFE_AND_WHAT_EACH_COSTS.md
    claude/STATUS_COMPACTIONS_BLOCKER_MOVED_IT_DID_NOT_CLEAR.md
    claude/FINDING_A_BLANK_MEMO_SLOT_READS_AS_AN_OBJECT_ID.md
    claude/FINDING_PACK_ALREADY_SWEEPS_ORPHANS_AND_REFUSES_THE_ONE_STORE_THAT_NEEDS_IT.md  (SUPERSEDED, kept as the record of the falsified prediction)
    claude/HANDOFF_COMPRESSION_LANE.md
    docs/maintenance/AI_MEMO_WAL_ATOMICITY_LANE_V1.md          (AIF-061)
    docs/maintenance/MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1.md (AIF-070)
    docs/maintenance/MEMO_OBJECT_CHALLENGE_LANE_V1.md          (AIF-108)
    include/xbase/durable.hpp                                   the named directory gap
    src/cli/cmd_pack.cpp:390-400, 607-651, 774                  the gate and the loop
