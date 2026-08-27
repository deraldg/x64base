---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-004
  recorded_at_utc: 2026-08-27T20:29:02Z
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
    baseline_commit: fe198893f026f91fa1c9e007258e66a2f4c158ff
  authorization:
    requested_by: member.derald
    scope: >
      "first look at cmd_gps.cpp" then "this little program represents our
      scope doesn't it, fix it and we firm our model?" -- an explicit go for
      src/cli/cmd_gps.cpp. Then "do three first", "do both", "yes write it up
      -- we need to resolve it next because we need user identity to be
      integrated", and the owner's own correction that named the lock half:
      "record locking is user controlled too - it should be globally
      consistent."
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_GPS_AND_THE_IDENTITY_LANE_2026-08-27.md
    kind: session_closeout
primary_topics:
  - cursor_reporting
  - recno64
  - deletion_semantics
  - identity
  - rbac
  - locking
  - multi_workspace
---

# Session Closeout -- GPS at RECNO64 scope, three findings, and the identity lane opened (AIF-078)

    Date              : 2026-08-27 (fourth closeout of run COWORK-20260827-001)
    Owning lifecycle  : DotTalk++ SDLC
    SDLC lane         : implementation + finding + design
    Covers            : 03f9918ac .. 0789d102c, this session's commits only.
                        bd026fae2 and 0bbe2d294 are the CONCURRENT session's
                        and are not this report's to describe.
    Truth state       : RUNTIME-PROVEN for the GPS repair (six arms) and for
                        AIF-144 sec 2a (the lock half, prediction written
                        first). SOURCE-EVIDENCED for AIF-141, AIF-143, the
                        remainder of AIF-144, and every design document.
                        Three GPS arms NEVER FIRED and are named in sec 2.
    A NOTE ON `claude/` : paths below beginning `claude/` are claude.ai PROJECT
                        documents, NOT repo paths. `claude/` does not exist in
                        this tree and is not ignored, so a reader with a clone
                        cannot follow them and the cited-paths gate passes them
                        SILENTLY -- R75, a gate seeing the shape it was built
                        to see. The R128 closeout named this for retargeting on
                        2026-08-26 and this author repeated it three times
                        before catching it. Marked here rather than left
                        unmarked; retargeting is still owed lane-wide.

## 1. THE THROUGH-LINE

The owner pointed at one 181-line file and asked whether it represented the
scope. It did, and every rung of the ladder was broken in it:

    which AREA     addressing    R121
    which TABLE    identity      R130
    which RECORD   position      RECNO64
    which ROW      derivation    R1

Repairing it produced a finding about deletion semantics, which produced a
question about who owns a lock, which opened the identity lane. Nothing here
was planned; each step was the previous step's residue examined instead of
discarded.

## 2. GPS -- SEVEN DEFECTS, AND THE ONE THAT DEFINES THE SCOPE

`385a2572b`. All seven were in `src/cli/cmd_gps.cpp`; the repair is contained
to that file, so the help catalog -- a concurrent session's area -- is
untouched. States ride in the existing `{recno}` and `{logical_row}`
placeholders and no message id was added.

**1. IT DID NOT WORK AT OUR SCOPE.** `recno()` is the 32-bit compatibility
accessor that returns `-1` by design past INT32_MAX, so a 32-bit consumer sees
out-of-range instead of acting on a clamp. GPS read it into an `int`. On the
table class this engine exists for, the position reporter printed
`Physical Recno -1, Logical Row 0` and called it a position.
`recno64()`/`recCount64()`/`gotoRec64()` were available and documented as
authoritative.

**2. THE INSTRUMENT MOVED WHAT IT MEASURED.** The order walk repositioned the
cursor and refilled the record buffer and never restored. It stopped at the
target only when the target was VISIBLE; on a deleted current record the filter
check returned before the target check and the walk ran to the end of the
order. `workspace_session_state.dts` calls GPS and then asserts `SO_ID = 6` on
the buffer GPS left behind -- **the probe could corrupt the proof using it.**

**3. A DELETED CURRENT RECORD RETURNED THE TOTAL VISIBLE COUNT AS A ROW
NUMBER.** Not zero -- a number in the valid range that reads as "you are on the
last row". R6 in its worst form: absent represented as present, convincingly.

**4. THE ORDER WALK'S RETURN VALUE WAS DISCARDED.** `order_iterate_recnos`
returns false when an ordered backend could not be read; `err` was captured and
dropped. R3, and the AIF-118 shape -- one answer for "you are at row 3" and
"the walk died after 3".

**5. THE TRY/CATCH GUARDED NOTHING.** `recno()` is `noexcept`. The real hazard,
`workareas::current()` returning null and then `->label()`, is a null
dereference, which `catch(...)` does not catch. A guard on the impossible,
absent from the possible.

**6. IT MATERIALIZED.** `order_iterate_recnos` collects every recno into a
vector first; "where am I" on a 2^31-record table allocates ~17 GB.
`order_stream_display` was in the same header for exactly this.

**7. `GPS FOO` REPORTED THE CURSOR.** Any unrecognized argument fell through to
a position report.

**THE FIX'S SHAPE IS THE COUNT DISCIPLINE ENFORCED AT THE CALL SITE.**
`compute_logical_row` returns a KIND alongside the number -- `Derived`,
`NoRecords`, `OffTable`, `NotVisible`, `NotInOrder`, `OrderFailed` -- and the
number is read ONLY when the kind is `Derived`.

### What ran, including the run that proved nothing

**THE FIRST RUN WAS GREEN AND UNINFORMATIVE AND IS RECORDED AS SUCH.** Under
the auto-attached `SID` tag: recno 1 -> row 1, recno 200 -> row 200. Every
number matched and every number is also exactly what GPS would print if it were
echoing the physical, because SID is sequential and index order coincides with
physical order. The test could not separate derivation from no derivation.

Under tag `LNAME` the coincidence breaks: `GO TOP` gives physical **21** /
logical **1**, `GO BOTTOM` gives physical **157** / logical **200**. The
derivation is real.

**CURSOR RESTORE PROVEN:** `RECNO` 21 before and 21 after a GPS that walked the
whole order, with `? LNAME` returning `Anderson` both times.

**BOTH "no logical row" ARMS REACHED, AND THEY ARE NOT THE SAME ARM.** See
sec 3.

**NOT PROVEN, and not written down as if it were:** `NoRecords`, `OffTable` and
`OrderFailed` never fired, nor did any "none" branch of the recno cell.
`SKIP` at the last record REFUSES to move (`SKIP: at end`), so EOF was never
entered; `GO 201` remains untried. Three of six kinds are runtime-proven.

### Found while testing, recorded not fixed

- **`SET ORDER TO` bare is REJECTED** (`SetOrderMissingTargetText`) though it
  is the classic idiom for natural order in FoxPro, Clipper and dBase, and the
  error text does not name the spellings that work.
- **`SET ORDER TO 0` ALSO CLOSES THE INDEXES** (`clear_order_and_close_indexes`).
  Classic detaches only. A semantic difference behind an identical spelling,
  which is worse than a missing one.
- **`WSREPORT`'s section headed "Workspace" reports the whole PROCESS** -- two
  workspaces open, `WORKSPACE REGISTRY` correctly reports members 1 and 12,
  `WSREPORT` reports a flat `Open: 13` with no workspace column. THE COUNT
  DISCIPLINE. **R128 is what made it wrong**: before additive OPEN only one
  workspace's areas could be open, so process-wide and workspace-wide were the
  same number. That is the SECOND time additive semantics silently invalidated
  something true only because the old behaviour guaranteed a single occupant
  (AIF-140 is the first). Worth sweeping for a third.
- **`occupied_desc()` prints a `{first..last}` HULL, not the occupancy set.**
  Two areas at 0 and 7 print `{0..7}`. Multi-workspace is the feature that
  CREATES sparse occupancy and the reporting surface cannot show it. Every
  `Cursor: Area 21 of {0..42}` read this session was read as a set and never
  was one.

## 3. AIF-142 -- A DELETED ROW IS ABSENT FROM AN ORDER, NOT FILTERED FROM IT

`385a2572b`. **The arm that proved it is the one whose prediction was wrong.**

Predicted `none (record is filtered out)` under LNAME. GPS printed
`none (record not present in the active order)`, which sent the investigation
to `cmd_delete.cpp` -- which CAPTURES AND REMOVES the record's index keys
before deleting. `order_iterator.cpp` does no deleted handling of any kind. So:

    ordered path   the key is gone; nothing downstream gets to decide
    physical path  the record is yielded and the CONSUMER's filter rejects it

Same user-visible outcome, two engine facts, two different layers. **A consumer
can change its filter; it cannot change what is not there.** The old GPS printed
one number for both, and that number was the visible total.

`cmd_recall.cpp:22` states the property in the engine's own words -- *"active
indexes normally contain only live records and would otherwise hide deleted
rows"* -- and files it as RECALL's private workaround for its own target
selection, where no reader of LIST, COUNT, GPS or BROWSE would look. **A system
property discovered while fixing one command got documented as that command's
problem.**

**WHY THE NEW ARM EARNS PERMANENT PLACE:** RECALL's reindex is
`mutates_index_entries: best-effort` by declaration, so a record can be LIVE IN
THE TABLE and ABSENT FROM EVERY ORDERED TRAVERSAL. `not present in the active
order` is the detector for a failed best-effort reindex and should not be
softened back into a number.

**PREDICTED, NOT MEASURED, and the finding says so in its Basis:** `SET DELETED`
is read only by FILTERS, so with it OFF the physical path can show deleted rows
and the ordered path structurally cannot. Every runtime datum was taken with
the default ON. One test closes it, written out in the finding's sec 8.

## 4. AIF-143 -- TWO `cli::Settings`, DIFFERENT LAYOUTS

`d682cfd53`. `include/cli/settings.hpp:55` and `include/sessions.hpp:30` both
fully define `cli::Settings` in namespace `cli`, both with an inline
`static Settings& instance()`, both marked `status: supported`.

**NOT A SAFE PREFIX.** Three members exist in the live header and not the stale
one, and the FIRST -- `passive_dev_diagnostics_on` at `:60` -- comes BEFORE
`deleted_on` at `:70`. So `deleted_on` and everything after it sit at a
different byte offset.

Include the stale header anywhere and the program is ill-formed, NO DIAGNOSTIC
REQUIRED: it compiles, it links, the linker keeps one inline `instance()` and
discards the other, and the losing translation unit reads `deleted_on` at an
offset holding a different atomic. `SET DELETED OFF` silently toggling a
neighbour. Both files read correctly in isolation.

Inert only because nothing includes it -- coincidence, not structure.

**HOW IT ACQUIRED ITS SUPPORTED STAMP, and this is the reusable part:**
`3706da78c`, the AIF-050 backfill across 1034 files, applied it. The sweep asked
whether the file carried a header block and correctly answered no. It did not
ask whether the file was reachable. **A METADATA SWEEP CONVERTS
ABSENCE-OF-METADATA INTO PRESENCE-OF-A-CLAIM, AND THE CLAIM INHERITS THE
SWEEP'S BLINDNESS.**

## 5. AIF-144 -- FIVE AUTHORITIES ANSWER "WHO AM I"

`3bbce2d8d`, amended `0789d102c`. The owner named the half that matters.

| authority | answers with | consumers |
|---|---|---|
| `identity::acting_member_key()` | `member.derald` | 12 sites, 7 subsystems |
| `TeamMember::profile_home_key` | `dottalkpp/user/<key>/` | nothing |
| `user_scope_paths::current_user_name()` | the literal `"default"` | workspace roots |
| `cmd_security` legacy selector | roles + six roots | self-declared legacy |
| `locks::current_owner()` | `host:pid:ms` | every lock |

**RUNTIME-PROVEN, PREDICTION WRITTEN FIRST.** Logged in as `member.derald`
(MAINTAINER, OWNER), locked record 21, `USER AS member.ai.claude.cowork` -- an
AI member the RBAC layer itself annotates *"must ask for limited permission"* --
and `UNLOCK 21` SUCCEEDED. Both `LOCK WHO` readings byte-identical
(`GRIMWOOD:45492:1787860508740`) across the switch as predicted; the two
`WHOAMI` readings differ, which is the control. **A restricted member released
the owner's lock. Privilege flowed downhill and the concurrency layer could not
see it.**

`LOCK WHO`, whose usage says it *"reports the owner of record n"*, prints
`host:pid:ms`. **A command named WHO that cannot say who.**

**THE FINDING ARGUES AGAINST ITSELF, DELIBERATELY.** Process-scoped lock
identity is not simply wrong: classic xBase locks per workstation and
`host:pid` is the correct token for LIVENESS, which stale-lock reclamation
needs and which AIF-116/AIF-031 already hardened once. The defect is narrower --
the member is nowhere in the lock record -- so the fix is BOTH, not INSTEAD.

**THE RUN CORRECTED THE DOCUMENT'S OWN SEVERITY.** As filed it read "reachable
in two commands"; `USER AS` refuses without an authenticated owner, so the
divergence is owner-gated. The overstatement is kept beside its correction.

**THE MAIN NEGATIVE RECOMMENDATION:** do NOT wire `current_user_name()` to the
live actor, tempting though it is. It feeds `resolve_workspace_file_path()` and
therefore both `catalog_dir()` and `WORKSPACE SAVE`, so during an agent session
every posture and the whole catalog would resolve under a different root and
APPEAR TO VANISH -- with no error, because a search that finds nothing looks
exactly like a directory that is empty. **And a second, independent reason
found by running `USER LIST`:** only two of six members carry a
`profile_home_key`, and `user_profile_root()` maps empty to `"default"`, so the
wire would silently place four of six members in ONE SHARED HOME while
appearing to scope them.

**WHY IT BLOCKS GUI THREADING, and it is not the race.** All five authorities
are PROCESS-scoped. The GUI became a first-class engine consumer at AIF-078
step 2b. The day two sessions share one process they share ONE lock owner and
CANNOT CONTEND -- every lock between them succeeds and excludes nothing. Not a
race a mutex would catch; a mutex that was never there. Normalizing identity is
not a threading fix, it is the PREREQUISITE: who-am-I must become per-SESSION
before it can become per-thread.

Three rulings are stated and not taken in the finding's sec 7.

## 6. THE MULTI-WORKSPACE ALPHA CALL

The owner: *"I think we have enough pieces of the multi-workspaces to say we've
gone from concept to Alpha on that lane."* Recorded in
`claude/MULTI_WORKSPACE_LANE_ALPHA_STATUS.md` with the boundary stated, because
the word is only useful if it says what it covers: **Alpha on addressing,
identity and restore; not yet Alpha on lifecycle.**

What convinces is not any single green. R130 was proven BOTH WAYS -- the spec
written before the fix and watched to fail. And the second consumer reached the
allocator through a link rather than by widening the cherry-pick list, which
stayed at two files. Concepts do not have properties like that.

**LIFECYCLE, AND A CORRECTION.** This closeout's author reported the purge
design as unruled and unbuilt. **It was ruled "A -- flag, never pack" on
2026-08-24 and shipped the same day** as `WORKSPACE DELETE`, covered by
`workspace_purge_regression.dts`. The design document's status line is stale.

So the remaining lifecycle problem is not removal but ISOLATION: regression's
catalog writes are AD HOC, in the `.dts` corpus and not the harness -- 26 files
issue the verbs, four of them in the default suite -- at **10 rows per
`REGRESSION ALL`**. `claude/LIFECYCLE_HARDENING_SCOPED_CATALOG_ROOTS.md` records
the lever: `workspace_search_roots()` already exists and is included by exactly
one file in the tree, which is not the catalog. **The sixth AIF-079 instance
this lane has catalogued, and the one that happens to answer a live question.**

## 7. AUTHOR ERRORS -- TWENTY-FOUR, AND TWO PATTERNS

The count matters less than the patterns, and there are exactly two.

**PATTERN ONE -- I read an artifact's status line and reported it as the tree's
current state. FOUR TIMES.**

1. Told the owner the GUI had no slot handle, from
   `AIF078_FINDING_GUI_CANNOT_REACH_THE_ALLOCATOR.md`. Steps 2b and 3 had both
   landed; the owner corrected it in one sentence.
2. Reported `WORKSPACE PURGE` as designed and unbuilt. Ruled and shipped 08-24.
3. Published "+7 rows per `REGRESSION ALL`" in the Alpha status doc. It is 10
   since `WSLADDER` was promoted, and `cmd_regression.cpp` carries the
   correction in its own text.
4. Claimed `RECNO` was "not in the engine" after checking one of THREE
   surfaces. The owner: *"recno is scalar"*.

**A document's status line describes the day it was written, not today.**

**PATTERN TWO -- a statement about a pattern became an instance of it. THREE
TIMES.**

5. A good-neighbour note quoting four broken paths became a second source of
   the same advisories.
6. Its explanatory line then spelled `cite-check:ignore` and suppressed itself.
7. The `132 callers` correction spelled the two grep patterns it told the
   reader to trust, pushing 110 to 112 and 1 to 3. Reverted before shipping;
   the replacement describes the patterns without spelling them and records
   the mistake.

**ANY TOOL THAT MATCHES ON TEXT WILL FIND THE SENTENCE DESCRIBING IT.**

**And the one that is neither, and is the worst:**

8. **Reached for a classic-DBF parser on `WORKSPACES.dbf`** and got 252 records,
   216 live heads, max WS_ID 986 -- all garbage, from a `0x64` header walked as
   a classic one. Discarded before it reached a plan. **This session had already
   recorded that exact error in its own AIF-139 closeout text**, which this
   author wrote into a commit message three days earlier.

Also recorded: reading "two advisories" off a truncated paste and stating it as
the whole list; telling the owner "neither is mine" when one advisory came from
my own AIF-141 row and is permanently unstageable; predicting an off-by-one in
`WSREPORT` that turned out to be a correct CDX filter; two wrong handovers
(`WORKSPACE REGISTRY`/`WSREPORT` do not read the durable catalog; angle-bracket
placeholders pasted literally, producing a green transcript that demonstrated
nothing); saying "one member has a profile" in prose when the count is two; and
a fullwidth vertical bar that would have failed `house-style`.

**A sequence that runs to completion under failed preconditions is the most
persuasive empty result there is.**

## 8. OPEN, AND WHOSE

1. **Three rulings in AIF-144 sec 7** -- `Owner::operator==`, whether the path
   resolver may follow the live actor, the `SECURITY` legacy selector. Owner's.
2. **`SET DELETED OFF` across both traversal paths** -- one test, AIF-142 sec 8.
3. **GPS's three unfired arms** -- `GO 201` is the cheapest.
4. **`occupied_desc()` and `current_slot()`** -- shared header, unclaimed.
5. **`WSREPORT` scope** -- report the workspace, or say it reports the process.
6. **AIF-141's advisory is permanent**: `include/xbase_64_phase1_contract.txt`
   is gitignored and cited by three documents, so it fires on every commit
   touching any of them. Leave, reword, or accept.
7. **The owner seat has no password**, and owner login gates `USER AS`.
   Deployment state, owner's call.
8. **`AI_TIER1_SEED_V1.md` is at 89% of its 8192 B budget**, 866 B headroom.

## 9. GOOD NEIGHBOUR

- **What changed:** `src/cli/cmd_gps.cpp` (repaired, explicit go),
  `src/gui/core/session.cpp` (one comment), four findings, two design documents
  in the claude.ai Project, intake rows, three claim files.
- **Whose area:** `src/cli/**` had the owner's explicit "fix it".
  `src/gui/core/session.cpp` is a comment-only correction of a count.
  Everything else is documentation.
- **Authorization:** every AIF number claimed with `claim-aif` and the claim
  file verified present BEFORE the number was cited anywhere.
- **How to verify:** GPS sec 2's runs replay at the prompt; AIF-144 sec 2a is
  ten commands; each finding carries its own read-only verification block.
- **How to undo:** `tmp/cmd_gps.cpp.pre-scope` and `tmp/session.cpp.pre-countfix`
  are the pre-change files; the findings are documents and delete cleanly with
  `release-aif`.

**Author does not self-approve. Every finding ships review-needed.**
