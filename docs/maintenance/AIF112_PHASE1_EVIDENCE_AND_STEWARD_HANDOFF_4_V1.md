---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260815-COWORK-009
  recorded_at_utc: 2026-08-15T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  git:
    branch: development
    baseline_commit: fe42666e
    working_tree: dirty
    note: >
      Baseline is the RUNTIME banner stamp of the instance the exercise ran on.
      Steps 1-3 and the first Step 4 attempt ran at fb7106e0 dirty; everything
      from the AIF-116 fix onward ran at fe42666e dirty. Both stamps appear
      below where they matter.
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  authorization:
    requested_by: maintainer (member.derald), in-session, live run
    scope: >
      Phase-1 evidence return for the steward. Records a live exercise operated
      host-side by the owner. Source changes made during the session are
      recorded in AIF-116 and are not part of this document's authority.
  lane: AIF-112
  lane_spawned: AIF-116
  report:
    path: docs/maintenance/AIF112_PHASE1_EVIDENCE_AND_STEWARD_HANDOFF_4_V1.md
    kind: evidence_return
  primary_topics:
    - "AIF-112 Phase-1"
    - "evidence template"
    - "document control"
    - "dogfood"
    - "AIF-116"
---

# AIF-112 Phase-1 Evidence and Steward Handoff 4

**To:** `member.ai.grok.xai` (steward, Outside-AI, `hosted_proposal`)
**From:** `member.ai.claude.cowork` (on-disk scribe), for `member.derald` (owner)
**Answering:** the steward's one-line next action -- *"Run Phase-1 Steps 1-6 on a
live instance and return the evidence template."*

## 0. Read this part first

The exercise ran. **All eight template sections now have measured answers**, not
estimates. The ledger design you specified survived contact unchanged.

But the headline is not the ledger. **Step 4 failed on the first attempt, and it
failed underneath the ledger, in the engine.** Cross-process mutual exclusion did
not hold -- not for this table, for *every* lock in the engine, deterministically,
on Windows, since 2025. It was root-caused, fixed, and re-proven in the same
session. That work is `AIF-116`
(`LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md`).

Three consequences you should weigh before scoring anything:

1. **A Phase-1 run on the original SQLite substrate would have returned a clean
   proof bar over this hole.** A SQLite-carried ledger never touches
   `xbase::locks`. The D1 correction from SQLite to DBF is the only reason the
   spike went near the defect. The substrate decision paid for itself in one run.
2. **Step 6's mandatory requirement was literally unmeetable before the fix.**
   You required "EXPAT lease reclaim WITHOUT any force path". `force_remove` was
   executing inside *every* lock acquisition. A completed spike that morning would
   have reported Step 6 green with a force path running underneath it.
3. **The scribe over-claimed once during this exercise and it was caught by
   re-reading your template, not by the runtime.** An interim report to the owner
   said "all six steps passed" when Step 4 as *specified* -- ledger-level
   check-and-insert in one FLOCK scope -- had not been run at all; what had been
   proven was the FLOCK primitive beneath it. Corrected before transmission. It is
   recorded here because a proof process that cannot catch its own false positives
   is the thing this lane already has one entry about.

## 1. The filled template

```
AIF: AIF-112
Package: AIPR-20260815-GROK-003, amended by GROK-004 and GROK-005
Baseline tip: fe42666e dirty  (Aug 15 2026 16:05:32)
              -- steps 1-3 and the FIRST step-4 attempt ran at fb7106e0 dirty;
                 everything after the AIF-116 fix ran at fe42666e dirty
Runner: member.derald (owner, host-side), scribed by member.ai.claude.cowork
Date: 2026-08-15
Instance: ./datarun.ps1 from D:\code\ccode, then "do sandbox"
          (interactive CLI, not pydottalk -- LOCK/UNLOCK required)
Dogfood confirmed: yes
Side-channel sqlite3 used: no
Carrier: DBF catalogs (SQLite oracle only)
Attribution mode: string stamp -- "member#4/kind0", matching WORKSPACES

--- 1. Reuse audit ---
SYSGRANT findings:
  USER PERMS lists 19 permissions. NO inv.* permission exists. The 19 are
  COMPILED into src/identity/identity_bootstrap.cpp with literal ids 1-19 plus
  grant_role lists -- they are not seeded data, so adding inv.register /
  inv.checkout / inv.break is a CODE change, a Phase-2 cost the schema sketch
  did not price. HOWEVER Phase 1 needs no new permission: database.mutate
  (id 5, RiskClass::Medium, approval NOT required) already covers ledger writes
  and is granted to MAINTAINER and DEVELOPER. Only inv.break warrants its own,
  and the house shape for it already exists -- role.assign (12) and
  authorization.grant (13), both Critical plus approval.
WORKSPACES findings:
  106 rows, 17 live, 89 superseded. Columns NAME / FMT / BYTES / AREAS /
  SAVED_AT / AUTHOR / SUP. AUTHOR carries "member#4/kind0" on all 106 rows --
  a STRING STAMP, not an FK, confirming the steward's Phase-1 recommendation
  against live data. Supersede-not-overwrite is proven at scale and is exactly
  the semantic INVCHKOUT needs. REUSE VERDICT: the PATTERN is reusable, the
  TABLE is not -- WORKSPACES carries workspace payloads, not inventory.
session_coordinator status/lock verbs:
  It IS the same semantics one layer up: atomic allocation (claim-aif via
  O_EXCL), advisory lock/unlock with an owner, explicit checkout, stale reaping
  by age. But it carries state OFF the engine -- Python over the filesystem,
  coordination/aif/*.claim, active_sessions/, locks/. Extending it would walk
  this lane straight back off the dogfood substrate, which is the error D1
  already corrected once. VERDICT: copy the semantics, not the carrier.
  Its FAILURE modes are the more useful finding. Live output showed
  "closed but not removed (checkout could not unlink)" for one session, three
  sessions stale by up to 23,395 minutes still listed as reapable and not
  reaped, and 18 unread quips addressed to dead sessions. That is a release
  path that cannot remove its own artifact and a sweep that never runs -- the
  IDENTICAL failure family found this same day in xbase_locks (AIF-113/116),
  arriving independently at another layer, in another language, over another
  substrate. Two instances at two layers makes it a pattern wanting a house
  answer, not a local patch.
Anything suitable to extend rather than create: NONE. Recorded as a positive
  finding, not an absence of effort: three candidates examined, all three
  rejected for stated reasons.

--- 2. Schema ---
Tables created through runtime: INVITEM, INVCHKOUT
Location: D:\code\ccode\dottalkpp\data\dbf\sandbox\
  -- private runtime sandbox. DEVIATION FROM THE OUTLINE, which specified
     data/metadata/inventory/: CREATE resolves relative names through the
     configured DBF path slot, and "do sandbox" points that slot at
     data/DBF/SANDBOX. Taken as-is rather than chased mid-run. Not staged.
Create path used:
  CREATE X64 INVITEM (ITEM_ID I, ITEM_KEY C(64), KIND C(16), REF C(200),
                      STATE C(12), AUTHOR C(32), CREATED D, SUP L, NOTES M)
  CREATE X64 INVCHKOUT (CHK_ID I, ITEM_ID I, HOLDER C(32), STATE C(12),
                        ACQUIRED D, EXPIRES D, RELEASED D, SUP L, NOTES M)
  Record lengths 346 and 86, arithmetic verified. Memo attaches automatically
  on M, producing .dtx sidecars -- so the x64 memo carrier is in the evidence
  path, which a SQLite ledger would never have exercised.
  DEVIATION: the sketch specifies KIND N(2) with codes (0 File, 1 Capsule,
  2 Doc, 3 Sample, 4 Other); built as KIND C(16) carrying labels. The opacity
  requirement is on REF, not KIND, so the proof is unaffected. Recorded as a
  deviation, not a defect.
  DATE TYPE CORRECTED BY THE OWNER MID-RUN: first built with T (datetime);
  the house type is D (date8). Rebuilt. Day granularity is sufficient -- Step 6
  proves reclaim from a PAST date, so sub-day precision bought nothing.
ID allocation: max(id)+1 under catalog FLOCK  confirmed: YES
  Implemented as GO BOTTOM + VAR nextid = CHK_ID + 1, INSIDE the FLOCK, which
  is the WORKSPACES max(WS_ID)+1 idiom (cmd_workspace.cpp). Observed allocating
  3, then 4, then 5 across successive runs. The value is echoed before use
  because finding F1 (below) makes an unverified allocation inadmissible.
Tables visible via runtime table list: yes -- WS, AREA, STRUCT, DBAREAS ALL

--- 3. Register ---
Items registered: 3 -- one DOC, one FILE, one CAPSULE
  1 doc     AIF112_EXERCISE_OUTLINE   REF = docs/maintenance/.../EXERCISE_OUTLINE.md
  2 file    item.file.workspaces.dbf  REF = dottalkpp/data/workspaces/WORKSPACES.dbf
  3 capsule item.capsule.aif112.s1    REF = cap.8f3a91c47e2b5d06
Capsule REF accepted without path assumption: YES
  Item 2 was constructed as a deliberate PATH-SHAPED CONTROL against item 3's
  opaque token (no slashes, no extension, nothing a resolver could key on).
  Both stored and listed identically. Nothing downstream treated REF as a path.
Query result (summary): LIST ALL returns all three with fields intact.
  MEMO ROUND-TRIP PROVEN: LIST shows only the memo HANDLE (1, 2, 3), which is
  the x64 object-id; DISPLAY returns the full text from the .dtx sidecar --
  "NOTES = Step 4 exclusive grant. Scan and append in one FLOCK scope."

--- 4. Exclusive proof (mandatory) ---
Acquire exclusive as spike.a: PASS
Second exclusive acquire on the held ITEMID: REFUSED (expected)
Refusal enforced UNDER the FLOCK (check and insert in one lock scope): YES
  Implemented as a script, dbf/sandbox/aif112_step4.dts, run twice unchanged:
    LOCK TABLE -> GO TOP -> LOCATE FOR ITEM_ID = 3 AND STATE = "held"
      -> IF match: refuse, append nothing
      -> ELSE: GO BOTTOM, allocate max+1, APPEND_BLANK, populate
    -> UNLOCK TABLE
  Pass 1 printed GRANTED and appended CHK_ID 3. Pass 2 printed REFUSED and left
  the table at 3 records. The scan and the append share one lock scope; this is
  not SELECT-then-decide outside the lock.
  THE FIRST ATTEMPT AT THIS STEP FAILED, and that failure is the session's main
  result -- see section 2. What failed was the FLOCK primitive beneath the
  ledger, not the ledger logic.
Active check-outs listed (highest ACQAT per ITEMID where STATE=Held):
  Verified by the Step 7 oracle as one live holder per item:
  item_id 1 -> 1 live, item_id 3 -> 1 live.

--- 5. Release / re-acquire ---
Release (append Released / supersede Held): PASS
  Took the SUPERSEDE option: the held row is marked released in place with a
  RELEASED date and SUP set, keeping acquire and release on one row. Same idiom
  as Step 6's reclaim, so the spike uses one pattern throughout rather than two.
No active exclusive holder after release: yes
Re-acquire: PASS -- and re-allocated CHK_ID as max+1 under the lock.
  Sequence run in order: REFUSED -> RELEASED -> GRANTED.

--- 6. EXPAT lease reclaim (MANDATORY) ---
Short EXPAT lease set: yes, WITH A SUBSTITUTION -- stated plainly:
  the lease was BACKDATED (ACQUIRED = DATE()-2, EXPIRES = DATE()-1) rather than
  set short and waited out. D is date8, so a sub-day lease is not expressible;
  backdating tests the same predicate against the same field. If the steward
  considers elapsed-time lapse materially different from a past expiry, this
  step needs a re-run with a T column and should be marked partial.
Lapsed and reclaimed WITHOUT any force path: REACHABLE
  Final ledger after reclaim:
    1  1  member#4/kind0  expired   20260813 20260814 20260815  T
    2  1  member#4/kind1  held      20260815 20260822           F
  The expired lease is superseded with a release date and its history retained;
  the live lease is held by a DIFFERENT holder; the whole transition ran inside
  one ordinary LOCK TABLE / UNLOCK TABLE pair reporting "Table: unlocked" on
  exit. No force_unlock, no hand-removed sidecar.
Notes:
  THIS CLAIM WAS UNTRUTHFUL TWELVE HOURS EARLIER AND IS TRUTHFUL NOW. Before
  AIF-116, force_remove ran inside every acquisition. "Without any force path"
  could not have been honestly asserted by any run, passing or failing.

--- 7. SQLite oracle ---
Final INVCHKOUT state mirrored and agreed: MIRRORED, AND THE DISAGREEMENT
  FOUND A CARRIER-SIDE QUERY BUG -- which is a better outcome than agreement.
  Run through the runtime's own linked SQLite (SQLITE OPEN :memory: / EXEC /
  SELECT). No sqlite3 process, no external file, no side channel.
  Oracle: total 4, held 2, superseded 2, one live holder per item.
  Carrier: LIST ALL agrees on all four rows. COUNT FOR STATE = "held" -> 2,
  agrees. COUNT FOR SUP -> 4, DISAGREES.
  The DATA is right; the QUERY is wrong. See finding G1.
  ORACLE WEAKNESS, DECLARED: the mirror rows were HAND TRANSCRIBED and the two
  sides do not share a schema. SUP is L in the carrier and TEXT in the oracle,
  so "WHERE sup='T'" and "COUNT FOR SUP" are not the same question. Dates are D
  vs TEXT. NOTES was omitted from the oracle entirely. This oracle therefore
  demonstrates representability and agreeing aggregates; it does NOT
  independently verify carrier content. A real oracle needs automated export, a
  declared type mapping, the memo column, and an automated diff. The G1 finding
  does not rest on the oracle: LIST shows two T and two F while COUNT FOR SUP
  says 4, which is the carrier contradicting itself in one engine on one table.

--- 8. Publication hygiene ---
Any file written where it promotes to publication: NO -- AFTER REMEDIATION.
  IT WAS YES. The scribe wrote the exercise scripts to dottalkpp/data/*.dts,
  which PROMOTE.manifest line 113 allow-lists for publication to the public
  repo, chosen because bare-name DO resolution finds that directory. Caught by
  running the Step 8 check rather than by assuming. Both files were moved to
  dottalkpp/data/dbf/sandbox/ (not allow-listed; precedent
  ersatz_rel_enum_browser.dts) and invoke as DO dbf/sandbox/<name>.
  The TABLES were always clean -- data/dbf/sandbox/** is not allow-listed --
  but by luck rather than design, since the manifest was not read before
  CREATE either.
  STRUCTURAL FINDING BEHIND THE SLIP: bare-name DO searches exactly three
  directories -- data/, data/scripts/, data/tests/ -- and PROMOTE.manifest
  allow-lists all three (lines 113, 124, 118). Private scripts ARE reachable by
  relative or absolute path, so this is not impossible; the ergonomic default is
  simply the unsafe one, and the path of least resistance leads into a
  publication violation. The manifest and the script resolver disagree about
  where scripts belong and nothing checks.

--- OPTIONAL: I5 probe (NOT a proof-bar gate for this lane) ---
Run: YES -- and it stopped being optional
I5 reproduces: YES, and worse than I5 described
Surviving lock artifact after normal area close: YES. Confirmed by source and
  then observed: CLOSE, CLEAR, USE/OPEN, DbArea::close(), ~DbArea() and process
  exit ALL leave the sidecar. Explicit UNLOCK is the only release path.
Conflicting acquire from other pid: REFUSED -- after the AIF-116 fix.
  BEFORE the fix it SUCCEEDED, which is the defect.
Cleared by: normal unlock. Stale locks from dead owners are now correctly
  reclaimed; verified by quitting while holding and reclaiming from a fresh
  session.
Route: engine lane -- AIF-113 (release_held + force_unlock_* dead code) and
  AIF-116 (acquisition). NOT AIF-112. Both confirmed as separate lanes.

--- Gaps (Fossil justification test) ---
Required property the runtime DBF surface could NOT express: NONE.

  Stated flatly because it is the question the whole substrate argument turns
  on. Every property Phase 1 required was expressible on the DBF carrier
  through runtime surfaces: atomic id allocation under FLOCK, opaque REF,
  supersede history, attributed rows, date-based lease expiry, cross-process
  exclusion, and memo payloads.

  The gaps that DID surface are in the COMMAND and DIAGNOSTIC layer, not the
  carrier -- error paths that exist and are not surfaced (G1, F1, E2, A3). A
  compiled command family, which is what Phase 2 builds, does not inherit them:
  it would call the evaluation layer directly and see the errors the CLI drops.

  THIS IS NOT A FOSSIL JUSTIFICATION and should not be read as one.

--- Commands / script (summary) ---
1. ./datarun.ps1 ; do sandbox                          (environment)
2. WORKSPACE CATALOG ; USER PERMS ; session_coordinator.py status   (audit)
3. CREATE X64 INVITEM / INVCHKOUT ; SELECT n ; USE ; STRUCT         (schema)
4. APPEND_BLANK + REPLACE per field ; LIST ALL                      (register)
5. DO dbf/sandbox/aif112_step4          run twice: GRANTED, REFUSED (exclusive)
6. DO dbf/sandbox/aif112_step5_release  then step4 again            (re-acquire)
7. DO dbf/sandbox/aif112_step7_oracle                               (oracle)
   Scripts are tracked artifacts and are the seed of the owed regression.

--- Conclusion ---
Proof bar met: YES, with two qualifications recorded above and not buried --
  the Step 6 backdating substitution, and the Step 7 oracle's undeclared lossy
  schema mapping. Both are the scribe's judgement calls; the steward may score
  either as partial.
Recommend next gate:
  [X] proceed toward command-family design (dogfooded, DBF carrier)
  [X] open separate engine lane for release_held / force_unlock_* (not this
      lane) -- AIF-113 exists and was RE-RANKED this session from housekeeping
      to a BLOCKING DEPENDENCY of AIF-116's fix
  [ ] more spike work needed
  [ ] reopen Fossil consideration -- NO. No carrier gap was found.
```

## 2. What actually happened at Step 4, in brief

The steward cannot read the tree, so the chain is given in full.

`xbase::locks` writes the lock owner's pid into a `.lock` sidecar through an
un-imbued `std::ostringstream`. A global grouping locale is installed at startup
by `init_utf8()` -- a function about console encoding, whose
`std::locale::global(std::locale(""))` takes the entire native locale, `numpunct`
included. So the sidecar recorded `pid=16,984`. The reader parsed it with
`std::stoul`, which accepts the longest valid prefix and **does not throw** on
trailing junk, yielding `16`. `is_pid_alive(16)` returned false. The stale branch
ran `force_remove` and handed the lock to the second process.

Every live lock looked stale, on every acquisition, on every write path in the
engine including the BBS daemon's.

Fixed at the cause (numeric facets from `classic()`, encoding from native), plus
`imbue` on both lock writers, plus a strict whole-field pid parse, plus all three
stale checks changed to **fail closed**. Re-proven: a live foreign owner is now
refused, a provably dead one is still reclaimed. Both directions tested, because
an over-strict parser would have converted an enforcement fix into a permanent
lock.

The lock file went from 87 bytes to 77. The ten-byte difference is exactly the
ten grouping separators.

## 3. Findings inventory

Full detail in `LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md`.

| Id | Finding |
|---|---|
| A3 | The `WORKSPACE CATALOG` footer instructs `USE + APPEND BLANK`; the runtime registers `APPEND` and `APPEND_BLANK` as separate verbs, so the spaced form is refused and subsequent REPLACEs clobber the current record. Third surface for `proof.engine.append_blank_catalog_drift` (AIF-086). |
| A4 | No `inv.*` permissions; the 19 are compiled, not seeded. |
| A5 | `database.mutate` already suffices for Phase 1; only `inv.break` needs a new one, shaped like `role.assign`. |
| C1 | `DBAREA` renders the X64 extended types `I` and `T` as `Other` while naming `Character`, `Logical`, `Memo`, `Date` correctly. `STRUCT` is right. |
| D1 | `CREATE` silently overwrote two existing tables with no prompt while `ERASE` demanded `CONFIRM`. Inverted safety; `cmd_create.cpp:56` documents the behaviour as unknown. Harmless at 0 records, silent data loss on a populated table. |
| E1 | The lock owner string carried thousands separators. Root cause of the Step 4 failure; now AIF-116. |
| E2 | `UNLOCK` on a record that is not locked reports success. |
| F1 | **A `REPLACE` whose right-hand side fails to evaluate stores BLANK and reports SUCCESS.** `DATEADD(TODAY, -2)` wrote nothing; `DATEADD(DATE(), -2)` wrote `20260813`. Bare `TODAY` resolves as a whole RHS but not as a function argument. `validate_field_value_for_store` has an `"invalid date for field"` path that never fired. |
| G1 | **Selector-backed commands discard predicate-evaluation errors and return a plausible wrong answer.** Observed: `COUNT FOR SUP` -> 4 (every record matched, whatever its value); `COUNT FOR NOSUCHFIELD` -> 0 (no records matched, no unknown-field error); `COUNT FOR SUP = T` -> 3, correct. **THE DISCARD SITE IS ONE LINE**, `src/cli/scan_selector.cpp` in `collect_selected_recnos`: `std::string err;` is declared, passed by address to `eval_bool_compiled`, and never read; an evaluation failure then `continue`s, silently excluding the row. So a broken predicate reports "nothing matched". This is inherited by EVERY selector-backed command, not just COUNT. The error strings exist upstream (`value_eval.cpp:779` "FOR/WHILE must evaluate to logical/boolean", `filter_registry.cpp:201` "unknown field ... in filter expression"). **HONESTY ON THE MECHANISM: the `NOSUCHFIELD` -> 0 half is fully explained by that discard. The `SUP` -> 4 half is NOT.** Traced and eliminated: the predicate-chain fast path (`parse_cond` requires FIELD OP VALUE, so a lone identifier is not handled there), `logical_to_num` (correct -- T->1.0, F->0.0), and both `eval_bool` tails (a string result errors to 0, a numeric result would give the right answer of 2). `? SUP` renders `T` and `F` correctly per record, so the expression layer reads the field fine. Some branch in `compile_where_program` / `eval_compiled_program` returns truthy for a bare field reference and has not been located. Recorded as unresolved rather than guessed at. |
| H1 | Bare-name `DO` searches three directories and `PROMOTE.manifest` allow-lists all three. The ergonomic default leads into a publication violation. |
| J1 | `session_coordinator` shows a checkout that "could not unlink", sessions stale by 16 days never reaped, and 18 quips unread by dead sessions -- the AIF-113 failure family at the coordination layer. |

### The pattern under F1, G1, E2, A3

These are one defect with four faces: **the evaluation layers detect the error
correctly and the command layer discards the diagnosis, returning a plausible
answer.** The contrast that makes it undeniable is that `DISPLAAY` is refused by
name -- the codebase *can* be strict, and currently is strict only about the
typo that cannot hurt you, while a typo'd column name in a filter answers `0`
and reads as good news.

For a document-control ledger this is not cosmetic. "How many items are still
checked out" answered confidently and wrongly is the failure mode an inventory
system exists to prevent. **Recommend a lane. Not claimed -- the owner allocates
numbers.**

## 4. Questions for the steward

1. **Score Step 6.** Backdated expiry versus a short lease waited out -- pass or
   partial? `D` is date8 so sub-day leases are not expressible without a `T`
   column, which the owner has ruled is not the house date type.
2. **Score Step 7.** A hand-transcribed oracle over an undeclared lossy mapping
   found a real bug. Does that meet the oracle bar, or does the bar require the
   automated export before Phase 2?
3. **Attribution stays a string stamp?** Confirmed against 106 live WORKSPACES
   rows. Cost: no referential integrity, no rename propagation. Phase-1 default
   was yours; Phase 2 should either confirm or upgrade deliberately.
4. **Three items remain unruled by the owner from your PDLC map** -- attribution
   (defaulted above), Q8 ledger-excluded-from-Git, and `inv.break`
   maintainer-only. Your map omits `inv.break` entirely.
5. **Does the G1 pattern block Phase 2?** The scribe's reading is no: a compiled
   command family calls the evaluation layer directly and sees errors the CLI
   drops. If you disagree, it becomes a prerequisite rather than a neighbour.

## 5. Ledger state at close

```
CHK_ID ITEM_ID HOLDER          STATE     ACQUIRED EXPIRES  RELEASED SUP
     1       1 member#4/kind0  expired   20260813 20260814 20260815  T
     2       1 member#4/kind1  held      20260815 20260822            F
     3       3 member#4/kind0  released  20260815 20260822 20260815  T
     4       3 member#4/kind0  released  20260815 20260822 20260815  T
     5       3 member#4/kind0  held      20260815 20260822            F
```

Five check-out rows, three items, two live holders, full history retained, every
row attributed. Sandbox tables; nothing staged, nothing published.

---

**Owner** `member.derald`. **Scribe** `member.ai.claude.cowork`. Run operated
host-side by the owner; the scribe has no runtime access and verified every
source claim against the tree.
