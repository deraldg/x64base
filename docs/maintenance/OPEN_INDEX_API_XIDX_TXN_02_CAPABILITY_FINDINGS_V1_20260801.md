---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260801-001
  recorded_at_utc: 2026-08-01T17:35:00Z
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
    baseline_commit: a84ab352ac63cddcfb29708155f8fa48091e0950
  authorization:
    requested_by: maintainer
    scope: >
      Design changes toward the advertised open index API, at direct maintainer
      instruction ("make design changes, we advertise we are working towards an
      open index API, so we work towards the mission defined from the top"),
      following the guidance to model CNX features on how CDX/LMDB implements
      them and to consider prospective backends such as SIX/SNX.
  report:
    path: docs/maintenance/OPEN_INDEX_API_XIDX_TXN_02_CAPABILITY_FINDINGS_V1_20260801.md
    kind: finding
---

# Open Index API -- Capability Seam Findings (lane XIDX-TXN-02)

    lane        : XIDX-TXN-02 (index transaction / realtime maintenance)
    mission     : open index API -- backends declare capability; callers ask
                  capability, never concrete type
    owner       : member.derald
    steward     : member.ai.claude.cowork
    tier        : runtime-proven where stated; UNMEASURED items marked
    origin      : task #29 (measure SET TABLE BUFFER against realtime CNX)

Three findings. F1 is a pre-existing defect that #29 surfaced and that stands on
its own. F2 is an error I made while generalising the commit seam, caught by the
first backend that used the generalisation. F3 is the scope boundary the
corrected generalisation then exposed: removing a wasteful rebuild revealed that
the rebuild had been accidentally load-bearing.

---

## F1 -- COMMIT owes a REBIND, not a REBUILD

**Status: runtime-proven 2026-08-01, wsl-lean. Not yet fixed.**

### What was observed

Buffering a REPLACE that moves an indexed CNX value, then COMMIT, then reading
the order, gives the PRE-EDIT ordering:

    REPLACE: buffered field #2 at rec 1.
    B1_OBSERVE_order_moved_before_commit:.F.     (expected -- maintenance lags)
    COMMIT: rebuilding CNX...
    [CNX REBUILD] tag=LNAME recs=4 root=4240
    REBUILD: TABLE STALE cleared (fresh)         (declares the index fresh)
    COMMIT: complete. (1 recs)
    B2_after_commit_top_is_AAAAA:.F.             (order is still pre-edit)
    B3_after_commit_second_is_ANDERSON:.F.

### The discriminating measurement

Two faults produce that symptom and they need very different fixes:

  - the rebuild produced a WRONG FILE, or
  - the rebuild produced a CORRECT file and the ACTIVE ORDER was still bound
    to the stale in-memory permutation.

Marker `B4b` separates them. It re-issues `SET ORDER TAG LNAME` and re-reads the
top, with NO rebuild on that line:

    [CNX READ RUN1] tag=LNAME entries=4
    SET ORDER: CNX TAG 'LNAME' (ASC)
    Recno: 1
    B4b_reorder_without_rebuild_top_is_AAAAA:.T.

`.T.` The file was correct. Only the binding was stale.

### Why this matters beyond the buffered case

COMMIT's CNX branch (`src/cli/cmd_commit.cpp`, `auto_reindex_if_needed`) calls
`cmd_REBUILD` and then clears the stale flag. So on this path the engine:

  1. pays for a full rebuild it did not need,
  2. leaves the caller reading a stale ordering anyway,
  3. and reports the index fresh while doing so.

That is the "reports success without doing its job" shape (Tier 1 seed, section
6). It is NOT caused by XIDX-TXN-02 M1: before M1 this rebuild was the ONLY
maintenance mechanism for a buffered CNX edit, so the stale binding has been
there for as long as the path has existed. M1 is only how it got found.

### A hypothesis that was WRONG, recorded so it is not repeated

The first explanation offered was that COMMIT rebuilds BEFORE flushing buffered
records, so the rebuild scans pre-edit data. That was inferred from message
ordering in the transcript and is false. Source order is unambiguous:

    cmd_commit.cpp:405   apply_one_recno(...)          <- records applied
    cmd_commit.cpp:459   auto_reindex_if_needed(...)   <- rebuild
    cmd_commit.cpp:508   "COMMIT: complete. (N recs)"  <- closing summary only

Reading message order as execution order is exactly the inference-instead-of-
measurement mistake the seed warns about. The corrected hypothesis was then
tested by `B4b` rather than argued.

### Fix not attempted here

The remedy is a rebind after the rebuild (or instead of it), not a second
rebuild. It belongs to whoever takes F2's follow-up, because if CNX moves onto
the maintained path the rebuild disappears and only the rebind question remains.

---

## F2 -- One capability axis was modelled where the seam needs two

**Status: error introduced and corrected the same session. Correction
RUNTIME-PROVEN 2026-08-01 (see "The correction, measured" below).**

### The design change

The commit seam decided maintenance policy by asking what a backend IS:

    cmd_commit.cpp:383   maintain_index = im->isCdx();
    cmd_commit.cpp:310   if (orderstate::isCdx(A)) { ...skip rebuild... }
    cmd_commit.cpp:320   if (orderstate::isCnx(A)) { ...rebuild... }

That phrasing must be revisited whenever a backend is added or gains a
capability, and it was already wrong: CNX gained working `upsert`/`erase` in
XIDX-TXN-02 M1 while this line still excluded it, so a buffered CNX edit was
never maintained and always fell through to a rebuild.

Replaced with a capability report on the contract, modelled on the existing
`maxRecordNumber()` precedent in the same interface:

    IIndexBackend::maintainsIncrementally()   default FALSE   (index_backend.hpp)
      CdxBackend        -> true    (reference implementation)
      CnxBackend        -> true    (as of M1; proven by CNXLIVE)
      CdxNativeBackend  -> false   (upsert/erase still stubs)
      Bpt/BPlusTree/Lmdb/Snx -> inherit the safe default

Default false is deliberate: a backend that forgets to override gets a slow
rebuild, not a silently stale index. Cost of the safe default is wasted work;
cost of the unsafe default is wrong data.

### The error

With `SET INDEXTXN` ON, CNX now qualified for the maintained path and COMMIT
called `beginBulkWrite()`. Measured (`DOTTALK_INDEX_TXN=1`, regression CNXBUF):

    COMMIT: failed during index finalization; buffer retained for retry.
    B4b_..._top_is_AAAAA:.F.
    REBUILD: TABLE has uncommitted changes. ... REBUILD: canceled (dirty table).
    B5_rebuild_agrees_with_buffered_realtime:.F.
    ROLLBACK: discarded 2 change(s).

The seam needs TWO independent capabilities, not one:

    1. can this backend MAINTAIN across a single mutation?   CDX yes, CNX yes
    2. can this backend BATCH a set of mutations in a txn?   CDX yes, CNX no

CDX answers yes to both, which is precisely why a single flag looked sufficient
while CDX was the only participant. The generalisation was right in direction
and under-specified in content, and the second backend to use it found that
within one run.

### The asymmetry it walked into

`index_manager.cpp` implemented the bulk-write trio inconsistently:

    beginBulkWrite   -> non-CDX: ERROR  "bulk write not supported by active backend"
    commitBulkWrite  -> non-CDX: TRUE   "nothing to commit for non-CDX backends"
    abortBulkWrite   -> non-CDX: no-op

Two of three already treated absence of transactions as a non-event. Only
`begin` treated it as failure. That was invisible while the gate read `isCdx()`,
because no non-CDX backend could reach the line.

Corrected by making `begin` agree with `commit`: nothing to begin is success.
Bulk write is a batching OPTIMISATION, not a correctness requirement -- a
backend without transactions applies each mutation as it comes, which is what
`CnxBackend::upsert/erase` already do. Refusing to start a transaction that was
never needed denies maintenance to a backend that can perform it.

### The correction, measured

Same fixture, `DOTTALK_INDEX_TXN=1`, rebuilt wsl-lean, 2026-08-01:

    [INDEX TRACE] apply_replace rec=1 before=1 after=1 emitted_del=1
                  emitted_ins=1 skipped=0 ok=yes staleBefore=no leftStale=no
                  tags=[-LNAME,+LNAME]
    COMMIT: complete. (1 recs)
    B2_after_commit_top_is_AAAAA:.T.
    B3_after_commit_second_is_ANDERSON:.T.
    B4_after_commit_bottom_is_ZEBRA:.T.

Four things to read there, in order of how much they matter:

  - no "failed during index finalization" -- `beginBulkWrite` no longer refuses
    a backend that has nothing to begin;
  - no "COMMIT: rebuilding CNX..." -- the rebuild was SKIPPED, because
    maintenance happened during apply and `auto_reindex_if_needed` was told so;
  - `B2`/`B3` went `.F.` -> `.T.` This is the design change delivering the thing
    it exists for: a buffered edit that moves an indexed value is reflected in
    the committed order with no rebuild anywhere on the path;
  - `leftStale=no` -- the backend did the work and said so, rather than
    succeeding quietly while marking itself stale.

`B1` remains `.F.` and is not scored. It records that maintenance lags until
COMMIT rather than tracking the buffer eagerly, which is the intended design.

The eight default regressions were green in the same run.

### What the failure did right

Worth recording because it is the opposite of the defect shape this codebase
fears. The engine did not silently corrupt anything: it reported
"failed during index finalization", RETAINED the buffer for retry, refused a
REBUILD on a dirty table, and the later ROLLBACK discarded both changes cleanly
with `B6a`/`B6b`/`B7` all `.T.` A wrong answer would have been worse than a
loud failure, and it chose the loud failure.

---

## F3 -- SET ORDER discards realtime maintenance by reloading the container

**Status: runtime-proven 2026-08-01, INDEXTXN on. Not fixed. A scope boundary
made visible, not a regression.**

### What was observed

In the run that proved F2's correction, one marker moved the OTHER way:

    B4b_reorder_without_rebuild_top_is_AAAAA:.F.     (was .T. with INDEXTXN off)

`B2`/`B3`/`B4` are green, so the ACTIVE order is correct. `B4b` re-issues
`SET ORDER TAG LNAME` and re-reads the top, and gets the PRE-EDIT record back.
The next line rebuilds and `B5` is `.T.` again.

So the maintained ordering survives navigation but not a re-bind.

### Mechanism, from source

Four facts compose into it, and no single one of them is wrong:

    cmd_setorder.cpp:543   "always release any current backend/handles first"
                           -- close() runs UNCONDITIONALLY before openCnx
    index_manager.cpp:249  openCnx short-circuits when the container is already
                           open (setTag only, no reload) -- unreachable from
                           SET ORDER, because of the line above
    cnx_document.cpp:214   the reload re-reads RUN1 payloads from the file
                           (this is the "[CNX READ RUN1]" line in the trace)
    cnx_backend.cpp:628    persistence is DELIBERATELY absent in M1

Maintenance lives in the in-memory payload. `SET ORDER` throws that payload away
and reloads from a file nobody has written since REBUILD. The order reverts, and
nothing reports it, because from the backend's point of view a freshly loaded
container is not stale.

### Why this appeared only now

Before the capability change, COMMIT rebuilt the CNX file on every buffered
edit. That rebuild was wasteful (F1) but it had a side effect: the file on disk
matched the table, so the reload behind `SET ORDER` happened to find correct
data. That is why `B4b` read `.T.` under INDEXTXN off, which is exactly what
made it a usable discriminator for F1.

With the maintained path in force, COMMIT correctly skips the rebuild -- and the
reload now finds a file that was never updated. **The wasteful rebuild was
accidentally load-bearing.** Removing redundant work is still right; it just has
to be paired with removing the dependency on its side effect, and this is the
measurement that says which one.

### Two fixes, either sufficient for the in-session case

    A. PERSIST the maintained payload
       (XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md; task #31)
       Required for durability across a close or a process restart.
       Does not remove the reload cost.

    B. Let SET ORDER REBIND rather than reopen when the manager already holds
       this container -- delete the unconditional close(), and let the existing
       short-circuit at index_manager.cpp:249 do its job.
       Cheap. Does nothing for a restart.

B is the same remedy as F1 ("rebind, not rebuild") at a different seam, which is
worth noticing: two independent defects in this lane are both an expensive
operation standing in for a cheap one and losing correct state on the way. Both
are wanted eventually; A is the one that makes the guarantee real.

The unconditional `close()` is labelled "Critical fix" and predates this work.
Whoever removes it should find out what it was fixing first -- most likely a
handle-leak or a stale-tag bug that the short-circuit path now handles properly,
but that is an assumption until measured, and assuming otherwise is how the F1
hypothesis went wrong.

### Marker note for whoever reads B4b next

`B4b` was written to discriminate F1's two candidate faults on the UNMAINTAINED
path. On the maintained path the same line answers a different question -- it is
now the only marker in CNXBUF that crosses a container reload -- and it happens
to answer that one usefully too. That is luck, not design. When CNXBUF is
registered, `B4b` needs a comment saying which question it is answering under
which mode, or it will read as a flapping regression.

---

## Follow-up: three more type branches at the same seam

`beginBulkWrite`, `commitBulkWrite` and `abortBulkWrite` each
`dynamic_cast<CdxBackend*>` on the concrete type -- the same shape the
capability work exists to remove. They should become virtuals on
`IIndexBackend` with no-op-success defaults, so a backend DECLARES its batching
support instead of being recognised by RTTI. That is the natural second
capability axis and it would have prevented F2 outright.

Deliberately not done in the same change: one in-flight design change at a time
is enough, and the correction above needs to be proven first.

For a prospective SIX/SNX backend, the resulting contract is the deliverable:
implement `ITagBackend`, answer two capability questions honestly, and inherit
both the maintained path and the legacy fallback without editing the commit
seam at all.

---

## Evidence index

    regression CNXBUF   dottalkpp/data/scripts/cnx_realtime_buffer_proof.dts
                        (standalone; not registered until it earns it)
    F1 proof            marker B4b .T., INDEXTXN off, 2026-08-01
    F2 defect           COMMIT finalization failure, INDEXTXN on, 2026-08-01
    F2 correction       B2/B3/B4 .T. with no rebuild line, INDEXTXN on,
                        2026-08-01, plus [INDEX TRACE] leftStale=no
    F3 proof            marker B4b .F. in the same corrected run
    seam regressions    2026-08-01, wsl-lean, all green:
                        WAL_COMMIT_ROLLBACK  W0/W1/W2 .T.
                        CNXLIVE              L_T4/L_T5/L_T6 .T.
                        IDXSTALE             E_T1..E_T4 .T., leftStale=yes
                        INDEX_TXN            T3/T3/T4 .T. (DOTTALK_INDEX_TXN=1)
                        The IDXSTALE/CNXLIVE split holds in one build: the
                        native CDX-V64 stub still reports leftStale=yes and
                        earns the corrective REPLACE warning, while maintained
                        CNX reports leftStale=no. Opposite contracts, both
                        asserted, neither retuned to accommodate the other.
    unchanged suites    8/8 default green with the capability change in
    related             SESSION_CLOSEOUT_CNX_REALTIME_INDEX_MAINTENANCE_2026-07-31.md
                        (XIDX-TXN-02 M1, and the remaining-work list this feeds)
                        XIDX_TXN_02_M0_ADDENDUM_PERSISTENCE_SEAM_V1_20260731.md
                        (F3 fix A -- the deferred persistence milestone)
