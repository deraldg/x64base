---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-003
  recorded_at_utc: 2026-08-27T17:10:18Z
  agent:
    provider: Anthropic
    product: Cowork
    model: not_exposed
    member: member.ai.claude.cowork
    access_mode: local_write
  attribution:
    authored_by: member.ai.claude.cowork
    planned_by: null
    owner: member.derald
    committer: member.derald
  session:
    id: COWORK-20260827-001
    run_id: COWORK-20260827-001
    chat_reference: not_exposed
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: COWORK-20260826-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: f60d2d70da86e606bbd2744b0c62a29d06316a6a
  authorization:
    requested_by: member.derald
    scope: >
      "regarding LOAD, no problem, we don't save slots, we allocated them as
      they are available, do we need a slot provider??" then "yes and start
      addressing these corrections in code" -- an explicit go for src/cli,
      with the ruling drafted first and the spec written and run before the
      fix.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_R130_LOAD_IS_ADDITIVE_2026-08-27.md
    kind: session_closeout
primary_topics:
  - workspace
  - multi_workspace
  - posture_load
  - slot_allocation
  - session_state
  - regression_coverage
---

# Session Closeout -- R130: LOAD is additive, and a posture records a KEY (AIF-078)

    Date              : 2026-08-27 (third closeout of run COWORK-20260827-001)
    Owning lifecycle  : DotTalk++ SDLC
    SDLC lane         : ruling + implementation + review
    Truth state       : RUNTIME-PROVEN for the defect and the fix on the FILE
                        carrier, both directions, on two binaries from the same
                        tree. SOURCE-EVIDENCED only for the three other carriers
                        (memo, minidb, ram-memo), for the scoped KEY handler,
                        and for the unscoped CURRENT in SAVE. See sec 6 -- the
                        limit is the point, not a footnote.
    Proof state       : two interactive CLI transcripts (pre-fix and post-fix)
                        plus a full REGRESSION ALL. NOT registered: there is no
                        proof.* record.
    Mutation          : src/cli (2 files), one new .dts spec, one regression
                        registration, one ruling, one register row, one Session
                        Log row.

**SCHEMA NOTE.** `ai-report-audit-v1`, measured not chosen:
`labtalk/registries/ai_report_audit.yaml:4` pins v1 and the AIF-074 correction
records that the live validator REJECTS v2. Restated because a note nobody
repeats becomes a rediscovery.

## One-line summary

The owner asked whether LOAD needed a slot provider; it did not, one already
existed and LOAD was the only opener not using it -- and the close that looked
like the defect turned out to be the only thing holding the old design up, so
it and the key-to-slot map had to ship as one change.

## Commits

    f60d2d70d  (baseline) Rename the eleven schema_* workspace handlers
    7a3b23828  R130: LOAD is additive, and a posture records a KEY not an
                address  (src/cli x2, spec, registration, ruling, register
                row, Session Log row)   [hash back-filled by the amendment,
                sec 11.1 -- it was <pending> when this block was written]


    Date    : 2026-08-27
    Session : Claude Cowork (COWORK-20260827-001, third batch)
    Lane    : AIF-078 (multi-workspace). Completes R128.
    Ruled   : R130 by member.derald, 2026-08-27.
    Status  : review-needed. The author does not self-approve.
    Basis   : two runs on two binaries from the same tree, transcripts
              pasted by the steward. What was NOT run is in sec 6.

## 1. WHAT THE OWNER ASKED, AND WHAT THE ANSWER TURNED OUT TO BE

> "regarding LOAD, no problem, we don't save slots, we allocated them as
> they are available, do we need a slot provider??"

**No.** `cli::find_free_area_for_current_workspace(bool&)` (`workarea_util.hpp:155`,
defined `workarea_util.cpp:223`) already existed, is workspace-scoped, and was
already used by `cmd_use.cpp:765` (USE ... IN FREE) and `cmd_workspace.cpp:1223`
(R128's additive OPEN). **LOAD was the only opener in the tree still replaying
addresses.** Nothing new was built.

And on the brute close:

> "now we use workspace close as the brute solution -- everybody has database
> fun until they shutdown their app and all of the workspaces close at one time"

**That sentence is why the close was not deleted and then apologised for.** It
separated the CORRECT use of `workspace_close_all()` -- shutdown -- from the
incorrect one, LOAD borrowing it as a precondition. The function is untouched.

## 2. THE CLOSE WAS NOT THE DEFECT, AND DELETING IT ALONE WOULD HAVE BEEN WORSE

**MEASURED.** `workspace_load_from_stream()` replayed each recorded `AREA <n>`
as an ENGINE ADDRESS: `open_into_area(n, ...)` (`cmd_workspace.cpp:1310`) calls
`get_area_0based(n)` and `A.close()` on that exact slot. So the loader could
only be safe if slot `n` was free, and `workspace_close_all()` at `:2405`
guaranteed it by emptying every workspace in the session.

**Take the close away and leave the addressing, and the loader stops being
neutral and becomes actively destructive** -- it opens into whatever occupies
the recorded slots, which is precisely where another workspace's areas live.
R128 recorded this same shape for `schema_open_directory`'s slot loop and fixed
it the same way. **The close and the key-to-slot map are ONE change.** The
comment at `:2405` now says so in the tree, so nobody splits them later.

## 3. SPEC FIRST, WATCHED TO FAIL, PREDICTION WRITTEN DOWN BEFORE THE RUN

`dottalkpp/data/scripts/workspace_load_posture_keys.dts`, registered `PKEYS`,
array `58 -> 59`, `in_default_suite = false`.

**Five arms read in THREE worlds, not two** -- and the third world is the one
the arms exist for:

- **TODAY** -- `close_all` empties everything; the loaded tables take slots 0
  and 1; workspace A is gone.
- **NO MAP** -- A survives at 0 and 1; the loaded tables allocate to 2 and 3;
  but `CURSOR 0` / `CURSOR 1` / `CURRENT 0` still address 0 and 1, so **A's
  cursors are DRIVEN** and the loaded tables are left at row 1.
- **R130** -- A untouched; loaded tables at 2 and 3 with their recorded cursors
  restored through the map.

| arm | reads | predicted TODAY | measured TODAY | predicted R130 | measured R130 |
|---|---|---|---|---|---|
| `PK_G0a`..`G0d` | fixtures | `.T.` | `.T.` | `.T.` | `.T.` |
| `PK_G1a` `G1b` | posture source slots | `.T.` | `.T.` | `.T.` | `.T.` |
| `PK_G2a` `G2b` | A occupies 0 and 1 | `.T.` | `.T.` | `.T.` | `.T.` |
| `PK_T5` | engine current, no SELECT | `.T.` WRONG | `.T.` | `.T.` | `.T.` |
| `PK_T1` | slot 0 | `.F.` | `.F.` | `.T.` | `.T.` |
| `PK_T2` | slot 1 | `.F.` | `.F.` | `.T.` | `.T.` |
| `PK_T3` | `PKBT` by name | `.T.` WRONG | `.T.` | `.T.` | `.T.` |
| `PK_T4` | `PKBU` by name | `.T.` WRONG | `.T.` | `.T.` | `.T.` |

**Sixteen predictions, sixteen matches.** Recorded because a prediction that
is only written down after the run is not a prediction.

**THE PRE-FIX TRANSCRIPT SHOWS THE BRUTE CLOSE FIRING INSIDE THE LOAD**, with
PKWSA's two areas as its victims and nobody having asked:

    WORKSPACE SWITCH: current handle 4 (PKWSC), depth 0, members 0
    WORKSPACE CLOSE: Closing all work areas...
    REL: cleared all
    WORKSPACE: 2 area(s) closed.

**THE POST-FIX TRANSCRIPT SHOWS THE NEW REPORT LINE**, which is the half a
user will actually feel:

    WORKSPACE LOAD: restored 2 area(s) and 0 relation(s) (+ 2 cursor(s)).
    WORKSPACE LOAD: 2 table(s) landed at an engine slot other than the number
    recorded in the posture. The posture's AREA numbers are KEYS, not addresses
    (R130); use WORKSPACE REGISTRY to see where they are.

**THREE OF THE FIVE ARMS ARE GREEN ON THE OLD BINARY FOR THE WRONG REASON AND
THE SPEC SAYS SO IN ITS OWN TEXT.** With the slot space emptied first, the
recorded number and the allocated slot coincide by accident. `PK_T3` green on
the pre-fix build is not evidence and must not be reported as one. They
discriminate against a NEW implementation whose map is wrong -- the NO MAP
column -- and against nothing else.

**T1 AND T2 CANNOT GO BLANK, AND THAT IS ENGINEERED.** An errored marker in
this language PRINTS NOTHING rather than going red (USE_AGAIN, three cuts), so
an arm reading a CLOSED area disappears silently instead of failing. Both
fixture families therefore share the FIELD NAME `LBL` with different VALUES, so
slots 0 and 1 are readable in all three worlds and the comparison is always a
real field read.

## 4. WHAT LANDED IN THE TREE

**`src/cli/cmd_workspace.cpp`** -- six edits:

1. `workspace_close_all()` at `:2405` DELETED, replaced by the comment that
   explains why it was not a defect and why the map ships with it.
2. The AREA loop asks `cli::find_free_area_for_current_workspace()` instead of
   replaying the recorded number; reports exhaustion and broken contiguity.
3. `std::vector<int> slot_of_key` records `recorded key -> allocated slot`,
   **only on a successful open**, so a key whose table failed stays -1.
4. `CURSOR` translates through the map; an unmappable key is COUNTED, not applied.
5. `CURRENT` translates through the map; an unmappable key is IGNORED and
   REPORTED, never guessed at.
6. The `KEY` handler moved from the UNSCOPED `find_open_area_by_name_ci` to
   `find_open_area_in_workspace_ci` -- see sec 5.

Plus the usage block at `:4470`: two stale contract lines corrected.

**`src/cli/cmd_regression.cpp`** -- `PKEYS` registered, `58 -> 59`.

**`dottalkpp/data/scripts/workspace_load_posture_keys.dts`** -- new.

**`docs/maintenance/R130_POSTURE_RECORDS_A_KEY_NOT_AN_ADDRESS_V1.md`** -- the
ruling. **`docs/ai-friendly/R_RULING_REGISTER_V1.md`** -- R130 recorded BEFORE
the number was cited anywhere, on the steward's instruction ("this time record
the number").

## 5. TWO DEFECTS FOUND WHILE FIXING THIS ONE, BOTH IN THE SAME FUNCTION

**(a) THE `KEY` HANDLER WAS AN UNSCOPED WRITE.** `cmd_workspace.cpp:2555`
resolved a posture's `KEY <table> <field>` line through
`find_open_area_by_name_ci` -- lowest engine slot across EVERY workspace -- and
then WROTE through the result (`unique_reg::set_unique_field` /
`set_primary_field`). Under today's close-everything LOAD it could not reach
anywhere, because nothing else was open. **The moment LOAD became additive it
could:** a posture stamping a unique-key declaration onto another workspace's
same-named table. AIF-137's shape, third instance, inside the function being
changed. Scoped in the same commit. **NO ARM COVERS IT** -- this spec never
produces a `KEY` line.

**(b) `WORKSPACE SAVE` WRITES `CURRENT` UNSCOPED.** `workspace_save_to_string()`
filters every `AREA` and every `CURSOR` line through `sc.contains(area0)` and
then emits `CURRENT` from `eng->currentArea()` with **no scope check at all**.
So a scoped save taken while the engine sits in another workspace writes that
FOREIGN slot number into the posture. R128 found exactly this shape in the AREA
sweep and fixed it; this line is four lines further down and survived that pass.
The loader now ignores and reports an unmappable `CURRENT` rather than guessing
-- clamping it to the lowest restored area would be a guess that looks like a
restore. **NO ARM COVERS IT EITHER**: this spec never produces one, and doing so
needs a fixture that saves from a workspace the engine is not standing in.

## 6. WHAT WAS NOT RUN, AND IT IS THE LIMIT OF THIS RESULT

**ONE LOADER, FOUR CARRIERS.** `workspace_load_from_stream` is fed by
`workspace_load_from_file` (`:2599`), `ws_memo::load_from_memo` (`:3561`),
the MINIDB container (`:3665`) and `ram-memo` (`:4141`). **This change reaches
all four. Only the FILE carrier was exercised.**

`REGRESSION ALL` ran fifteen specs with no `.F.` anywhere, including
`WORKSPACE_SCOPE`, `USE_ARGS` (U_T4 still reads engine area 4, so IN FREE is
still workspace-scoped), `NAME_AMBIG`, `WSMULTI`, `WSLADDER` and `RELSCOPE2`.
`NONDESTRUCTIVE`'s `WORKSPACE LOAD` restored 12 areas into slots 0..11 with NO
remap line, which is the identity case working.

**But `WORKSPACE_MEMO`, `WORKSPACE_SESSION`, `WORKSPACE_MINIDB`,
`WORKSPACE_RAM`, `WORKSPACE_LOADSHORT` and `CASCADE_ENV` are all explicit-run
and NONE of them ran.** They are the memo, minidb and ram carriers plus the
43-area cascade posture, and `WORKSPACE_SESSION` in particular asserts
`SELECT 21` after a memo load. **The loader is proven on one carrier out of
four. That is not "the loader is proven".**

**WHY THEY SHOULD STILL PASS, AND WHY THAT IS AN ARGUMENT AND NOT A
MEASUREMENT:** every shipped posture was checked and all are contiguous
`0..n-1` except one, so loading into an emptied workspace yields identity and
`SELECT 21` still lands. The exception is **`my_cascade.dtschema`, which is
SPARSE** (7 areas, highest recorded number 7). Under R130 its tables pack
contiguously and its recorded numbers stop matching their slots. No spec was
found that loads it.

**A NEW ORDER-DEPENDENCE THIS CHANGE CREATES, NAMED SO IT IS NOT DISCOVERED:**
any spec that does `WORKSPACE LOAD` and then addresses by SLOT now depends on
the current workspace being EMPTY at load time, because the load no longer
empties it. `NONDESTRUCTIVE` is such a spec and it passed only because it runs
first and had closed everything. Run it after something that leaves areas open
and its `SELECT 8` reaches a different table. The house fix is
`WORKSPACE CLOSE ALL` before `WORKSPACE LOAD` in any spec that then addresses
by slot -- which is exactly the composition R128 ruled for replacement.

## 7. WHAT IS NOT RULED, CARRIED FORWARD FROM R130

- **Whether LOAD is RE-ENTRANT** in R128's sense. A second LOAD of the same
  posture currently allocates a fresh set. Unruled.
- **`WORKSPACE LOAD <name> AS <ws>`** -- a convenience now, not a mechanism.
- **What LOAD does with `broke_contiguity`** -- it announces; USE announces too;
  not ruled.
- **R129 sec 6.2's slot arm.** R130 sec 5 DISSOLVES it as a prerequisite for
  LOAD, because LOAD never addresses a slot it did not just allocate. It stays
  open for `SELECT` itself.
- **Relations are still cleared GLOBALLY on a scoped close** (`:180`), which
  R128 named. Additive LOAD makes that reach across workspaces routinely rather
  than rarely. The post-fix transcript still shows `REL: cleared all`.

## 8. AUTHOR ERRORS AND DRIFT, RECORDED RATHER THAN TIDIED

1. **R130 sec 8 sketched THREE arms; the spec has FIVE.** The ruling was written
   before the fixture layout existed, and its `T2` ("green today for the wrong
   reason") became `T3`/`T4`/`T5` once the fixtures were built two-plus-two
   rather than one-plus-one. **The ruling was NOT retro-edited to match.** Both
   are true of the moment they describe, and a ruling that silently retunes
   itself to its own implementation stops being a record of a decision.
2. **A first cut of the registration patch had a broken string-splice** that
   would have produced `{ { "PKEYS"` and failed to compile. Caught by reading it
   back before running it, not by the compiler.
3. **R129's NOT RULED list cites `schema_close_all()`, a name that no longer
   exists** (renamed `workspace_close_all()` in `f60d2d70d`, same session). Named
   in R130 sec 1 rather than corrected in R129, on the same principle as (1).

**GOOD NEIGHBOR**

- **What changed:** `src/cli/cmd_workspace.cpp` (loader + two usage lines),
  `src/cli/cmd_regression.cpp` (one registration), one new spec, one ruling, one
  register row.
- **Whose area:** AIF-078. `src/cli/**` is engine and had an explicit go
  ("yes and start addressing these corrections in code", 2026-08-27).
- **What authorization:** owner ruling R130, same day, after the measurement.
- **How to verify:** rebuild, then `DO workspace_load_posture_keys` -- all eight
  guards and all five arms `.T.`, and the LOAD prints the remap line. Then
  `REGRESSION ALL`.
- **How to undo:** four pre-change copies were left in the session scratch
  directory, named `cmd_workspace.cpp.pre-r130`, `cmd_workspace.cpp.pre-usagefix`,
  `cmd_regression.cpp.pre-pkeys` and `R_RULING_REGISTER_V1.md.pre-r130`. **They are
  deliberately named WITHOUT their directory prefix here:** that directory is
  git-ignored (`.gitignore:266`), so citing the full path would make the
  cited-paths gate report four IGNORED entries -- a gate signal about scratch
  files rather than about this change. Reverting the loader alone is safe;
  **reverting the map WITHOUT restoring the close is the NO MAP world of sec 3
  and must not be done.**

---

## 11. AMENDMENT, 2026-08-27, AFTER THE SIX CARRIER RUNS

**The original text above is left standing.** Everything in this section either
corrects it or completes it, and the corrections are stated rather than edited
in, because a closeout that silently retunes its own claims stops being a
record of what was known when.

### 11.1 THE COMMIT

    7a3b23828  R130: LOAD is additive, and a posture records a KEY not an
               address  (src/cli x2, spec, registration, ruling, register
               row, Session Log row)

Gates passed on the second attempt. **The first attempt was BLOCKED and the
author's gate prediction had missed it:** `ai_report_audit` requires a YAML
`ai_report_audit` envelope on every `SESSION_CLOSEOUT_*.md` and this document
shipped without one. **R75 on the author's own prediction** -- the earlier
commits in this run passed that gate, and that silence was read as "not my
concern" when it meant "those carried envelopes." Fixed with
`report_id: AIPR-20260827-COWORK-003`, and the `(AIF-078)` lane token added to
the H1 at the same time, which cleared `session-log-check`'s "names no lane in
their title" advisory.

### 11.2 THE FOUR CARRIERS ARE NOW PROVEN. SEC 6's LIMIT IS LIFTED.

All six explicit-run specs were run. **`WORKSPACE_MEMO`, `WORKSPACE_SESSION`,
`WORKSPACE_MINIDB`, `WORKSPACE_RAM`, `WORKSPACE_LOADSHORT` and `CASCADE_ENV`
all read green**, so the memo, minidb and ram-memo carriers are measured rather
than argued. `SS_T1` restored the parent at physical recno 6 and `SS_T2`
re-slaved the child to 11 through the load's own refresh, on the 43-area
posture, over the memo carrier.

**THE LOADER IS SOUND ON ALL FOUR CARRIERS.** What is not sound is what specs
may assume about where things land afterward -- see 11.4 and 11.5.

### 11.3 A CORRECTION TO SEC 6, AND IT IS THE AUTHOR'S SURVEY THAT WAS WRONG

Sec 6 states *"every shipped posture was checked and all are contiguous
`0..n-1` except one."* **That survey covered
`dottalkpp/data/workspaces/*.dtschema*` -- the FILE carrier -- and the claim was
generalised to all postures.** Memo-carried postures live inside
`WORKSPACES.dbf` and were never enumerated.

**`minidb_sidecar` IS A SPARSE MEMO POSTURE.** `workspace_minidb.dts` did
`SELECT 1` before `CREATE X64 MDMEMO`, so the posture records `AREA 1` with
nothing at 0. Under R130 the allocator answered slot 0, the load announced the
remap, and the spec's `SELECT 1` reached an empty area -- `DB_T3` and `DB_T4`
both `.F.`, followed by `REPLACE: no file open.`

**R75 AGAIN, ON THE AUTHOR'S OWN INSTRUMENT: the survey saw the shape it was
built to see, and its silence was reported as coverage.**

**FIXED AND VERIFIED.** `workspace_minidb.dts:89` now reads `SELECT MDMEMO`
instead of `SELECT 1`, with the reason written into the file. Re-run
2026-08-27: **`DB_T1` `DB_T2` `DB_T3` `DB_T4` all `.T.`**, `SELECT MDMEMO`
resolved to **area 0**, and the remap line still printed. **The slot was the
whole story; there is no memo-carriage defect.** That had been INFERRED from
`REPLACE: no file open` and is now MEASURED, which is the difference this
closeout kept insisting on elsewhere.

The `SELECT 1` at `:65` is deliberately left alone -- it is the AUTHORING
placement, it is what makes the posture sparse, and it is the only sparse memo
posture found. Keeping it keeps the case in the suite.

### 11.4 A FALSE GREEN THIS CHANGE CAUSED -- NOW AIF-140

**`WORKSPACE_LOADSHORT`'s `L_T3` reads `.T.` while reading the wrong table.**
It addresses by NAME, and the ledger fired on the line above it:

    NAME: 'TEACHERS' is open in 2 areas (ws 3 area 10, ws 3 area 22);
    resolved to area 10 [REL refresh parent].

Area 10 is the x64 TEACHERS that survived the additive load; area 22 is the
partially-restored one the arm exists to assert. First-wins took the wrong one,
and both files descend from the same bytes so the field compared equal.

**Both areas are in ONE workspace**, so workspace scoping and R129 sec 6.2 do
not reach it. `WORKSPACE LOAD` assigns a posture's `alias=` with a bare
`setLogicalNameIf()` while `USE` has a three-arm policy that refuses or renames
and announces. **Claimed as AIF-140**; finding at
`docs/maintenance/AIF140_FINDING_LOAD_DOES_NOT_RENAME_A_HELD_NAME_V1.md`.

**AND IT DEFEATS THIS DOCUMENT'S OWN ADVICE.** Sec 6 offered name addressing as
the robust alternative to slot addressing. `WORKSPACE_LOADSHORT` had ALREADY
made that move -- its header records that ordinals produced two reds that were
the spec's fault. **After an additive LOAD neither form is safe unassisted:
ordinals move and names collide.**

### 11.5 CASCADE_ENV IS GREEN OVER A DIFFERENT ARRANGEMENT

It opened two tables with `USE`, then loaded a 43-area posture, and printed
`43 table(s) landed at an engine slot other than the number recorded`. It ended
with **45 areas open instead of 43**, `CASCADE_ITEMS` and
`CASCADE_SALES_ORDERS` each open twice, and the ledger fired **five times**.
All nine arms `.T.`

**The green is real. It is not the same green.** Recorded so a later reader
comparing transcripts does not treat the two runs as equivalent.

**SEVEN LEDGER HITS ACROSS THE SESSION AND NO SPEC CAN READ ONE** -- AIF-139,
demonstrated again rather than argued.

### 11.6 A SECOND FINDING FROM THE SAME INVESTIGATION -- AIF-141

Measuring whether CDX tags resolve against descriptor tokens or logical names
(they resolve against logical names) turned up that **the X64M writer DROPS a
name that exceeds the ceiling rather than truncating it** -- three sites, and
the writer's is destructive because the long name is never written to the file
at all. Latent: the ceiling is a build vector and no fixture comes near it.
**Claimed as AIF-141**; finding at
`docs/maintenance/AIF141_FINDING_A_LONG_NAME_THAT_DOES_NOT_FIT_IS_DROPPED_V1.md`.

The design question that produced it is answered in
`docs/maintenance/AIF078_DESIGN_NAME_TIERS_AND_CORRELATION_NAMES_V1.md`, which
also records that **`_db_name`'s retirement note at `xbase.hpp:564` is now
false** -- it justified the removal on the grounds that `_ws_handle` plus
`_logical_name` covers the table-name-vs-alias split, and `_ws_handle` was
EQUAL on both colliding areas in 11.4. Sound when written on 2026-08-22;
R130 invalidated it on 2026-08-27.

### 11.7 ONE UNEXPLAINED OBSERVATION, NOT DIAGNOSED

`workspace_minidb.dts`'s header says its real-disk `MDMEMO.dtx` residue is
*"harmless; truncated by the next run."* Two consecutive runs on 2026-08-27
saved `MINIDB 1: 2 file(s), 6920 B` and then `2 file(s), 7016 B` -- **96 bytes
of growth in the carried payload, which is not truncation.** Two transcripts,
one comparison, no diagnosis offered. It may be ordinary memo-append behaviour
and the header's wording may simply be loose. **Named because a per-run growth
that a document calls truncation is the shape this house keeps finding**, and
because nobody will notice it from one run.
