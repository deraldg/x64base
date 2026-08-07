---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260801-002
  recorded_at_utc: 2026-08-01T20:10:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 256cdf15c
  authorization:
    requested_by: maintainer
    scope: >
      Housekeeping and documentation before proceeding, at maintainer
      instruction, after the maintainer asked whether this effort has a PDLC
      and whether it is being maintained. The answer was no on both counts;
      this file is the correction.
  report:
    path: docs/maintenance/XIDX_TXN_02_PDLC_LANE_V1.md
    kind: lane_charter
---

# XIDX-TXN-02 -- PDLC lane record V1

    lane        : XIDX-TXN-02 (index transaction / realtime index maintenance)
    mission     : an OPEN INDEX API -- backends declare capability, callers ask
                  capability and never the concrete type
    owner       : member.derald
    steward     : member.ai.claude.cowork
    status      : M0 locked (partly by second-hand authority, see section 2)
                  M1 landed and runtime-proven
                  M2 landed and runtime-proven except crash recovery
    created     : 2026-08-01

---

## 1. Why this record exists, and what it admits

Asked directly whether this effort had a PDLC and whether it was being
maintained, the honest answer was **no to both**. Other lanes carry one
(`DDL_SCHEMA_PDLC_LANE_V1.md`, `SQLSEL_PDLC_LANE_V1.md`,
`EXPORT_SDF_PDLC_CLOSEOUT_V1.md`, `docs/maintenance/tuple_pdlc/`), so this is not
a gap in house practice. It is a gap in this lane.

What existed instead was a scatter: an M0 addendum, an M1 session closeout, an
M2 findings document, and milestone state living in an assistant task list that
is not in the repository at all. No single artifact could answer "what were M1's
exit conditions and were they met?" Two sessions of work were added to that
scatter rather than to a lane record, and this file is the correction, not a
retrospective claim that the process was followed.

**This record is now the lane's authority.** The point documents below are
EVIDENCE it points at, not competing statements of status.

---

## 2. AUTHORITY PROBLEM -- the M0 findings document does not resolve

`XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md` declares:

    amends : LANE_XIDX_TXN_02_M0_FINDINGS_V1_20260721.md
             section 1 (format-neutral directive) and section 3 (C3, atomicity)

**That file is not in the tree.** A repository-wide search finds the name only
inside documents that cite it:

    XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md
    src/AIPortal/sessions/2026-07-30_cowork_house_index_vdisk/
        LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md

So decisions C1 through C5 -- the locked M0 decisions this lane has been built
against, including the C3 that M2 amended -- are known to the current work ONLY
BY QUOTATION. They have been treated as authority without ever being read.

That is the exact failure AIF-082 exists to prevent: a pointer to a maintained
artifact, where the artifact is not there.

### What is known second-hand, and marked as such

    C1  approach A (stands, per the M0 addendum section 7)
    C2  stands (content not recovered)
    C3  persistence: temp + fsync + rename, CNX_HDRF_DIRTY backstop
        AMENDED by M2 to append-and-switch (section 4 below)
    C4  stands, includes a COMMIT branch (named in the triage plan)
    C5  stands (content not recovered)
    section 1  format-neutral directive: one mutable path serving .cnx (V32)
               and a future native .cdx (V64)

`LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md` is the fullest surviving
account and should be read as the interim substitute.

### Required before M3

Locate the M0 findings document, or declare it lost and restate C1-C5 here from
the documents that quote it. **Do not treat this section as a replacement for
that work** -- a summary of a document nobody can produce is not an authority,
and this lane has already spent two milestones pretending otherwise.

Possible location: it may have been renamed. `LANE_LMDB_INDEX_TXN_MAINTENANCE_
V1_20260721.md` in the 2026-07-21 session package shares the date and subject
and is the first place to look.

---

## 3. Milestones

### M0 -- design lock (2026-07-21, addended 2026-07-31)

    exit      : approach and persistence mechanism decided; format-neutral
                directive recorded
    status    : LOCKED, with the authority caveat in section 2
    evidence  : source-evidenced (API read, no runtime probe)
    artifacts : LANE_XIDX_TXN_02_M0_FINDINGS_V1_20260721.md  (MISSING)
                LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md
                XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md

The addendum resolved a tension M0 left open: the format-neutral directive and
the temp-plus-rename mechanism cannot both hold for a RAM-resident container,
because ramfs has no rename. Its resolution -- durability policy is a property
of RESIDENCY, not of container format -- survives into M2 and is why the seam
now carries three capability axes rather than one.

### M1 -- realtime CNX maintenance (2026-07-31)

    exit      : a REPLACE that moves an indexed value re-places that record in
                the CNX ordering immediately, with no REBUILD between the edit
                and the ordered read; the maintained ordering is IDENTICAL to
                the one a rebuild produces; staleness is reported honestly
    status    : LANDED, RUNTIME-PROVEN
    evidence  : runtime-proven, wsl-lean, 2026-07-31
    proof     : regression CNXLIVE  (cnx_realtime_index_proof.dts)
                L_T2 order moved with no rebuild
                L_T6 rebuild is a no-op over the maintained order
    closeout  : SESSION_CLOSEOUT_CNX_REALTIME_INDEX_MAINTENANCE_2026-07-31.md
    commit    : 4c5f13565 (cnx_backend.cpp), b6488ec5d (CNXLIVE)

The method is worth restating because it is not obvious: a CNX RUN1 payload
stores 4 bytes per recno and NO KEYS, so `entries_` is a PERMUTATION with
nothing to binary-search. The TABLE is the ordering authority -- the same
authority a rebuild uses -- so `upsert` compares the edited record's live field
value against the live value at each probe position. Rebuild and realtime share
`derive_sort_entry_`/`sort_entry_less_` so they cannot drift, and L_T6 asserts
exactly that.

M1 also inverted IDXSTALE, whose subject (a backend that cannot maintain) moved
off CNX. It was REPOINTED to native CDX-V64 rather than retuned, so the split
reads as deliberate.

### M2 -- persistence (2026-08-01)

    exit      : a maintained ordering survives a CLOSE and is correct on a cold
                reopen with NO rebuild; the persisted order agrees with a
                rebuild; saving twice is harmless; an interrupted save is
                detected at open and recovered
    status    : LANDED, RUNTIME-PROVEN EXCEPT CRASH RECOVERY
    evidence  : runtime-proven, wsl-lean, 2026-08-01, for everything except the
                dirty-flag recovery path, which is source-evidenced only
    proof     : regression CNXPERSIST  (cnx_persist_proof.dts), 11/11 markers
                P2 order survives the close, no rebuild
                P6/P7 rebuild agrees with the persisted permutation
                P8/P9 second close is idempotent (no second [CNX SAVE])
    commit    : PENDING at time of writing

**Mechanism, amending C3.** Append-and-switch, not temp-plus-rename: mark
`CNX_HDRF_DIRTY`, append a fresh RUN1 block per mutated tag, then write the tag
directory. The directory write is the single commit point. This is shadow
paging, it is the sequence `rebuild()` already used, and it needs no rename
primitive -- which matters because ramfs has none, and does not truncate either
(`ramfs.cpp:259-263` returns an existing RamFile unchanged, so an in-place
rewrite would leave the tail of a longer previous version).

C3's GOAL (atomicity) is met. C3's MECHANISM is superseded for both residencies.

**Scope honestly stated.** This protects against PROCESS death, not power loss.
`cnxfile` has no fsync; ordering between the appends and the directory write
holds only because both go through the same stream in sequence. Power-loss
safety needs fsync barriers around the commit point and is an addition to the
cnxfile I/O layer, deferred to M3.

**AIF-079 discharged for CNX_HDRF_DIRTY.** The flag existed since the format was
defined, was written only by PACK and ZAP, was cleared unconditionally by
`write_tagdir`, and was READ BY NOBODY. M2 makes it load-bearing, so it now has
both a writer and a reader. The recovery branch itself remains unproven.

### M3 -- hardening (NOT STARTED)

Candidate exit conditions, to be ratified against the recovered C1-C5:

    1. fsync barriers around the commit point; power-loss safety stated as a
       tested property rather than a disclaimer
    2. crash recovery proven: interrupt a save, reopen, observe the rebuild
    3. free-space reclamation -- append-and-switch grows the container on every
       save and has no compaction, which is fine for a 4-row proof and not for
       a 1M-row table under edit
    4. alternating meta pages with a checksum, replacing the single tag
       directory plus boolean flag (the LMDB precedent, already in this tree)
    5. the second capability axis: batching declared rather than recognised by
       RTTI (see F2 follow-up)

Items 3 and 4 are the difference between the mechanism being CORRECT and the
mechanism being production-grade. They were deliberately deferred, not missed.

---

## 4. Findings register

    F1  COMMIT owes a REBIND, not a REBUILD
        runtime-proven 2026-08-01 (marker B4b) -- NOT FIXED -- task #38
        Pre-existing; predates M1. COMMIT's CNX rebuild produces a CORRECT file,
        then leaves the caller on the stale in-memory binding and clears the
        stale flag. Pays for work it did not need and reports freshness it did
        not achieve.

    F2  one capability axis modelled where the seam needs two
        introduced and corrected 2026-08-01 -- CORRECTION PROVEN -- follow-up #40
        maintainsIncrementally() replaced isCdx() at the commit gate. CDX answers
        yes to both "can you maintain" and "can you batch", which is why one flag
        looked sufficient while CDX was the only participant. The bulk-write trio
        still dynamic_casts on concrete type.

    F3  SET ORDER discards maintained state by reloading the container
        runtime-proven 2026-08-01 (marker B4b inverting) -- MITIGATED by M2
        cmd_setorder.cpp:543 closes unconditionally, making the already-open
        short-circuit unreachable. Before M2 this LOST the maintained ordering;
        after M2 the reloaded file is correct, so the cost dropped from wrong
        data to a wasted read. Fix B (task #39) is now an optimisation.

    F4  REBUILD built on a DETACHED backend, so a later close-save republished
        the stale permutation over it
        introduced by M2, found and FIXED same day 2026-08-01 -- runtime-proven
        cmd_rebuild.cpp:242 constructed a local throwaway CnxBackend, leaving the
        ATTACHED backend holding a stale permutation and a non-empty dirty set.
        Harmless until M2 gave close() a save(): the next SET ORDER then wrote
        the stale ordering over the fresh rebuild. Measured as
        "[CNX REBUILD] root=4240" followed by "[CNX SAVE] root=4288".
        Fixed by rebuilding THROUGH the attached backend -- one owner of the
        state. Proven by the ABSENCE of the [CNX SAVE] line on re-run.

    F5  BOTTOM disagrees with the active CNX order on a NUMERIC tag
        runtime-observed 2026-08-01 -- NOT FIXED -- task #45
        SMARTLIST under the order prints 1,2,4,3 (SID 10,20,30,31 ascending) and
        a TOP+SKIP walk lands on record 3, but BOTTOM reports record 4. TOP is
        correct. NOT simply "BOTTOM ignores the order": CNXBUF B4 and CNXPERSIST
        P4 assert the same thing on a CHARACTER tag where ordered-last and
        physical-last differ, and both PASS. Mechanism UNMEASURED.
        Standing evidence: marker VURC_F1, which expects .F. until fixed.
        Outside this lane -- it is a navigation defect, not an index one.

    F6  CNX WALK cannot read a RUN1 block it just wrote
        runtime-observed 2026-08-01 -- NOT FIXED -- task #46
        "READ FAILED off=4192" at the offset [VERIFY WRITE] had just confirmed
        readable and CnxDocument loads without trouble. Diagnostic only, but it
        failed in the one situation where a diagnostic was the point.

Full analysis of F1-F3: `OPEN_INDEX_API_XIDX_TXN_02_CAPABILITY_FINDINGS_V1_20260801.md`.

**Note the shape F1, F3 and F4 share:** an expensive operation standing in for a
rebind, losing correct state on the way. THREE independent instances in one
lane. That is now a pattern with a name, and any new seam in this lane should be
asked "does this rebuild what it could rebind?" before it is written -- F4 was
predicted by this note one day before it was found, which is the only reason it
was recognised on sight rather than debugged from scratch.

**And a lesson about proofs, earned expensively.** F5 was mistaken for a
maintenance failure THREE times: first as a SEEK/ORDER disagreement, then as an
M2 save clobber, then as a broken rebuild sort. Each was a deduction from TOP and
BOTTOM -- two samples of a sequence. Printing the whole sequence settled it in
one run. A proof that samples an ordering at its ends is not proving the
ordering, and this lane has the scar to show it.

---

## 5. Open items

    #30  extend CNX coverage: APPEND, multi-tag, DELETE/RECALL, duplicate keys
    #32  deleted-record parity between realtime CNX and REBUILD
    #38  F1 -- COMMIT rebind
    #39  F3 fix B -- SET ORDER rebind
    #40  virtualize the bulk-write trio (F2's second axis)
    #41  surface declared-but-unbuilt CDX tags outside the trace channel
    #42  recover or declare lost the M0 findings document (section 2)
    #43  register CNXPERSIST, CNXBUF and VUREPCNX in cmd_regression.cpp
    #44  crash-recovery proof for CNX_HDRF_DIRTY
    #45  F5 -- BOTTOM vs the CNX order on a numeric tag (outside this lane)
    #46  F6 -- CNX WALK on RUN1 (outside this lane)

    CLOSED 2026-08-01:
    #31  CNX disk persistence -- M2, runtime-proven
    #33  VUREPAIR against x32/CNX -- ANSWERED YES, see below

**#33's answer, because it is the lane's best evidence that the mission works.**
VALIDATE UNIQUE REPAIR maintains a CNX order, and it needed NO SOURCE CHANGE to
do so. REPAIR routes through DbArea::replaceFieldStored, the replace snapshot is
genuinely backend-agnostic, and CNX inherited the behaviour the moment M1 gave
it working upsert/erase. That is what an open index API is supposed to buy: a
capability lands once and every caller gets it without being told about the
backend. The restriction VUREPAIR's header carried for two days was correctly
lapsed; what made it look otherwise was a marker that sampled BOTTOM.

Three regressions are written, green, and UNREGISTERED. CNXBUF additionally
needs a comment on marker B4b, which answers a different question depending on
whether INDEXTXN is on and will otherwise read as a flapping test. VUREPCNX
carries VURC_F1, which is RED BY DESIGN and must not be "fixed" by deleting it.

---

## 6. Evidence index

    regressions   CNXLIVE     cnx_realtime_index_proof.dts    (registered)
                  CNXBUF      cnx_realtime_buffer_proof.dts   (not registered)
                  CNXPERSIST  cnx_persist_proof.dts           (not registered)
                  VUREPCNX    validate_unique_repair_cnx_proof.dts
                              (not registered; 9 green + VURC_F1 red by design)
                  VUREPAIR    validate_unique_repair_index_proof.dts
                              (the x64/CDX original; header corrected 2026-08-01
                              because its x32 restriction had lapsed at M1)
                  IDXSTALE    index_maintenance_failure_proof.dts
                              (the negative counterpart; repointed at M1)

    seam suites   WAL_COMMIT_ROLLBACK, INDEX_TXN, plus 8/8 default
                  all green 2026-08-01 with M1 and M2 in

    documents     LANE_XIDX_TXN_02_M0_RECONCILIATION_V1_20260730.md
                  XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md
                  SESSION_CLOSEOUT_CNX_REALTIME_INDEX_MAINTENANCE_2026-07-31.md
                  OPEN_INDEX_API_XIDX_TXN_02_CAPABILITY_FINDINGS_V1_20260801.md

    source        include/xindex/index_backend.hpp   three capability axes
                  include/cnx/cnx_backend.hpp        CNX declarations
                  src/xindex/cnx_backend.cpp         maintenance + save
                  src/cli/cmd_commit.cpp             capability gate + save
                  include/xindex/index_manager.hpp   passthroughs

---

## 7. Maintenance rule for this file

Per AIF-082: this file carries MILESTONE STATE and POINTERS. It must not restate
what a pointed-to document says, because two documents that restate each other
diverge, and this lane already has one dangling pointer without adding
contradicting copies.

A milestone entry changes only when its evidence tier changes. "Landed" is not a
tier -- `planned`, `source-evidenced`, and `runtime-proven` are, and a milestone
that has landed without a runtime proof says `source-evidenced` and names what
is missing. M2 above is the worked example: proven for persistence, explicitly
not proven for crash recovery, in the same entry.
