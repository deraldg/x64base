---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260827-COWORK-005
  recorded_at_utc: 2026-08-27T23:26:27Z
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
    baseline_commit: 8776dd4cac4fda98b4cdd943943c5d0acd5b1910
  authorization:
    requested_by: member.derald
    scope: >
      "it is time to take the time to normalize it" (identity), then "do it"
      for stage 1, "fix them now as part of the job" for the FOR predicates,
      "keep going on the workspace cycle", "go" for L0 and L2, and a SECOND
      explicit "go" for L1 after the 216 -> 106 blast radius was shown.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_IDENTITY_STAGE1_AND_LIFECYCLE_L1_2026-08-27.md
    kind: session_closeout
primary_topics:
  - identity
  - locking
  - predicate_evaluation
  - multi_workspace
  - catalog_lifecycle
  - schema_design
---

# Session Closeout -- identity stage 1, the FOR-predicate defect, and lifecycle L1 (AIF-078 / AIF-144)

    Date              : 2026-08-27 (fifth closeout of run COWORK-20260827-001)
    Owning lifecycle  : DotTalk++ SDLC
    SDLC lane         : implementation + finding + design
    Covers            : 790947103 .. b7b888fc3, this session's commits, PLUS one
                        act that is not a commit: L1 ran against the PRODUCTION
                        catalog (sec 4). The catalog is not tracked by git.
    Truth state       : RUNTIME-PROVEN for AIF-144 stages 1 and 1b, for the
                        FOR-predicate fixes (two binaries, same tree), for L0
                        and for L1 (fourteen predictions, fourteen matches).
                        SOURCE-EVIDENCED for the catalog-split design.
                        L2 is BLOCKED and the blocker was MEASURED, not guessed.
    Note on `claude/` : paths beginning `claude/` are claude.ai PROJECT documents,
                        not repo paths. The cited-paths gate passes them
                        silently. Named per the R128 closeout's standing request.

## 1. IDENTITY, STAGE 1 -- A LOCK NOW RECORDS WHO TOOK IT

`e3a99df8a`. AIF-144 measured that five authorities answer "who am I" and the
lock system asks none of them. Stage 1 gives `Owner` a `member` field that is
**never part of `operator==`**.

**RUNTIME-PROVEN, prediction written first.** Logged in as `member.derald`
(MAINTAINER, OWNER), locked record 21, then `USER AS member.ai.claude.cowork`:

    LOCK WHO 21 -> member.derald (GRIMWOOD:51772:1787863836752)
    USER AS member.ai.claude.cowork
    LOCK WHO 21 -> member.derald (GRIMWOOD:51772:1787863836752)

**The second reading is the discriminator and it still says derald** -- the lock
records who TOOK it, not who is asking. `UNLOCK` still succeeds, deliberately:
exclusion is unchanged. What changed is that the release is now VISIBLY
attributed to a different member than the holder. The defect AIF-144 proved
silent is now legible.

**WHY THE MEMBER IS OUTSIDE EQUALITY, and it is not the obvious choice.** Folding
it in sounds stricter and sets a trap: sudo to another member, take a lock, sudo
back, and the principal can no longer release it -- deadlock by design.
`host:pid:ms` stays the LIVENESS token, which stale-lock reclamation is built on
and which AIF-116/AIF-031 already hardened.

**SIX WRITERS BECAME ONE.** `g_acting` had six direct assignments; they now route
through `assign_acting()`, which is also where the push to the lock layer
happens. The engine gains no identity include -- `xbase` stores the string and
never resolves it -- and that this LINKS was verified before the edit, not after:
`dottalk_bbsd` compiles `src/identity/*.cpp` and links `xbase`.

**TWO GAPS NAMED IN THE HEADER RATHER THAN DISCOVERED LATER:** the setter mutates
a process global (same shape as `g_acting`; stage 2 removes both), and the acting
member is initialised STATICALLY, so a lock taken before any login records no
member and `LOCK WHO` says `(no member recorded)`. That is true of the file. The
better fix is a provider the engine CALLS at lock time, deliberately not taken
because it needs somewhere to be installed and that somewhere is stage 2's
session object.

## 2. STAGE 1b -- AND THE OWNER'S QUESTION THAT EXPOSED IT

`9abb61109`. Asked "is `Owner::operator==` functional now", the measured answer
was: it compiles, it would do the right thing, and **it had ZERO CALLERS in the
entire tree.**

Every ownership decision compared strings by hand -- `remove_if_owned`,
`create_or_validate_owned`, and twice inside `try_lock_record`. Four hand-written
implementations of one rule with nothing forcing them to agree.

**THAT CORRECTED STAGE 1's OWN COMMIT MESSAGE.** It said "member is NEVER part of
`operator==`" -- true, and nearly vacuous, because the operator was never
invoked. The property was real; it was enforced by four string comparisons
rather than by the operator claiming to express it. All four now route through
`lock_is_mine()`, which invokes it. Byte-for-byte the same decision; what it buys
is ONE site for AIF-144 sec 7's member-aware refusal rule to land in.

Seventh AIF-079 instance this lane has catalogued, and the first closed by giving
the dead thing a caller rather than deleting it.

**AIF-144 sec 7 R-a is now marked TAKEN**, with the original reasoning kept
beside it, because the deadlock trap is why the answer is not the obvious one.

## 3. THE FOR-PREDICATE DEFECT -- FOUND BY A CENSUS THAT WOULD NOT RECONCILE

`7d7b81581`. Writing a catalog census produced three numbers that did not add up,
and that is the only reason anyone noticed.

                                    build 13:49:57   build 15:59:20
    COUNT                                      216              216
    COUNT FOR SUPERSEDED =  "1"                195              195
    COUNT FOR SUPERSEDED <> "1"                  0               21
    195 + live = 216 ?                        NO               YES

**THREE COMMANDS, ONE MALFORMED PREDICATE, THREE DIFFERENT WRONG ANSWERS, TWO
SILENT.**

- **The lexer did not know its own dialect.** `src/cli/expr/lexer.cpp` accepted
  `!=` (the C spelling) and not `<>` or `#`, the canonical dBase/FoxPro/Clipper
  not-equals. NOTHING ELSE NEEDED CHANGING: `TokKind::Ne` existed and
  `parser.cpp:84` already mapped it to `CmpOp::NE`. The operator was fully
  implemented and simply unspellable. Meanwhile `predicate_chain.cpp`,
  `cmd_locate.cpp:260`, `normalize_where.cpp` and `rhs_eval.cpp:317` ALL accept
  `<>` -- five spellings of one operator set, disagreeing.
- **LIST received the refusal and listed everything.** `cmd_list.cpp:524` caught
  `compile_where`'s error, PRINTED it, and returned every row -- announcing it
  could not answer the question asked and then answering a different one. Now it
  REFUSES.
- **COUNT never asked and printed a confident zero.** "No rows match" and "I
  could not evaluate your question" had the same output, and zero is a PLAUSIBLE
  ANSWER -- R6 in the most-used counting verb in the shell. Now the predicate is
  compiled first and a failure refuses with NO NUMBER, because a number is a
  claim.

**`compile_where` ITSELF WAS ALWAYS RIGHT.** AIF-074 ED-01b built it as "the ONE
funnel both evaluator families reach" precisely so a partly-parsed predicate
could not be evaluated as though whole. That lane closed this silent
wrong-answer class four times AT THE EVALUATOR. It was still open one level up,
at the CONSUMERS -- one discarded the verdict, the other never requested it.

**NAMED HOLE, NOT PAPERED OVER:** predicates containing function calls are exempt
from the new COUNT guard, because the selector routes those to
`predx::eval_expr()` and `compile_where` does not model that grammar. So
`COUNT FOR SOUNDEX(X)=SOUNDEX("Y")` still has no guard. Written at the guard.

## 4. LIFECYCLE -- L0 MEASURED, L1 DONE, L2 BLOCKED

**L0 (`l0probe.dts`, commit `3e82091f1`).** `SETPATH WORKSPACES <path>` already
redirects the catalog with NO code change: production 252/216 before, scratch
mints WS_ID 1, production 252/216 after. The scratch catalog gets its OWN
high-water sequence, so isolation is total. The fork -- do shipped postures
follow? -- answered NO, and the error named where it looked: the DATA root,
never the original workspaces root.

**L1 -- DONE, and it ran against PRODUCTION.** Owner-authorized twice, the second
time after being shown the blast radius. Backup first (`tmp/catalog_backup/`;
`tmp/` is scratch by convention and the catalog is not tracked by git, so that
backup is the only rollback).

Fourteen names deleted. **Fourteen predictions written before the run, fourteen
matches**, totalling 110 rows. Four reconciliation checks all passed:

    sum of reported deletions      110
    visible COUNT 216 -> 106        drop = 110, equal to the sum
    live heads     21 -> 7
    SET DELETED OFF -> 252          nothing packed
    GO BOTTOM / ? WS_ID -> 252      high-water intact, next WS_ID 253

**THE CENSUS CORRECTED THE PLAN TWICE.** The "thirteen live heads" figure was
three days stale -- it was 21 -- and the direct count was itself lying until sec
3's fix landed. And **not every live head is residue**: `x64` and `x32` are
DIRECTORY IDENTITIES whose adoption by `workspace open dbf` is D10.1 working as
designed. Seven were deliberately left. The plan's condition 3 was reworded from
"no catalog-only live head survives" to "no SPEC-MINTED live head survives."

**EIGHT OF THE TWENTY-ONE WERE MINTED THAT MORNING** by this session's own
carrier proving (WS_IDs 243-252). The census measuring the problem contained the
author's own residue.

**L2 -- BLOCKED, AND CHECKING BEFORE WRITING IS WHAT FOUND IT.**
`workspace_identity_ladder.dts` and `workspace_purge_regression.dts` WRITE
through the WORKSPACES slot and READ through the DBF slot (`SET PATH DBF
workspaces`, DATA-relative and pinned to production). Bracket the WORKSPACES
slot and the mint lands in scratch while the `LOCATE` searches production, and
every `WSL_*` / `PG_*` arm reds for a reason unrelated to what it tests -- the
two specs whose entire subject is catalog lifecycle, minting most of the 10 rows
per run. **The missing affordance: a script cannot say "the catalog, wherever it
currently is."** Three options recorded in the plan; the recommended one needs
new `SET PATH` grammar, which is a ruling and was not taken.

## 5. THE CATALOG SPLIT DESIGN

`b7b888fc3`. Three owner questions -- "the catalog of what", "can we split the
table", "make a key to link them" -- and the measurement makes it near-obvious:
**`scan_catalog()` reads FOUR fields** and every catalog operation funnels
through it across six call sites. The table already has two halves and only one
is ever scanned.

Four grounded arguments: R6 (a birth is a payload-shaped row meaning "no
payload"); the count discipline (one COUNT over four kinds); weight (a 3.1 MB
memo sidecar against a 178 KB table, opened on every mint); and a cheaper answer
to L1's gap, where supersede and flag-the-history are welded together.

**THE KEY ALREADY EXISTS AND THE RULING ALREADY EXISTS.** `WS_ID` is declared
unique and primary; D10.2 already ruled it IS the durable identity. **The schema
does not reflect its own ruling.**

Costs stated: migration of 252 rows, and THREE SPEC ARMS BREAK by line number --
`WSL_T1`/`WSL_T2` assert `FMT` and `SIZE_B` on a row that will not exist, and
their replacement needs a contrast fixture because absence cannot be asserted in
this language. **That is the hardest part and the design does not solve it.** It
also does NOT fix L2, and says so.

## 5a. WHAT THE DATA TREE SHOWED, AND IT CORRECTED THREE THINGS

The owner displayed the full `dottalkpp` directory listing. It settled more than
any source reading this session.

**THE PER-PROFILE WORKSPACE SECTIONS ARE NOT A PROPOSAL -- THEY ARE A
HALF-FINISHED FEATURE, AND THE EVIDENCE IS PHYSICAL.**

    user/default/workspaces   12 files   newest Jun 26
    user/derald/workspaces    10 files   newest May  4
    user/public/workspaces    10 files   newest May  4  (identical to derald)
    user/user/workspaces       0 files

Real `.dtschema` postures and `.erz` files. NOTHING has written there since
June; every workspace this session touched went to `data/workspaces`. So
`user_workspaces_root()` is not merely unwired code (AIF-144 sec 1) -- the
directories were built, populated, and stranded when `current_user_name()` was
pinned to "default". `public` being a byte-for-byte copy of `derald` says the
profiles were seeded once by hand and never diverged, because nothing wrote to
them. This is the AIF-079 shape with content on disk rather than a symbol with
no callers.

**THE HOUSE ALREADY SPLITS ITS CATALOGS, TWICE**, which is a better argument for
the catalog-split design than any of the four that design shipped with:

    data/metadata/          SYSCMD SYSFUNC SYSARGS SYSSUBCMD SYSHELP
                            SYSMSG SYSENTVAR SYSFLDDIC
    data/metadata/portal/   SYSLANE SYSPROOF SYSRUN SYSTASK SYSRUNLANE

`SYSRUNLANE` is an explicit LINK TABLE -- runs joined to lanes, with its own CDX
and LMDB. That is the owner's "make a key to link them", already shipped.
`WORKSPACES.dbf` is the OUTLIER. The design was amended in the same commit as
this closeout to lead with that.

**AND IT CORRECTED A CLAIM THIS RUN COMMITTED AN HOUR EARLIER.** The design doc
cited `PROOF_CURATION_LANE_V1.md` sec 4 as PROPOSING `SYSPROOF.dbf`.
**`SYSPROOF.dbf` is on disk** with a CDX and an LMDB directory. The proposal
landed. That is pattern one -- reading a document's proposal section as current
state -- for the EIGHTH time this run, and the first caught by looking at the
tree rather than by a gate or the owner.

**TWO SMALLER THINGS FROM THE SAME EXCHANGE.**

`SETPATH WORKSPACES <path>` is the INTENDED way to work with a different posture
set -- the owner's words: "if you are working with dtschema, do setpath
workspaces d:\dev\new". So L0's "fork" was never a defect: a workspace SECTION
is a catalog and its postures as a unit, and moving it moves the unit
coherently. A `SET CATALOG` narrow slot was proposed earlier in the session and
is WITHDRAWN -- it solved a problem that does not exist.

`DOTSCRIPT` resolves scripts through an ORDERED CANDIDATE LIST and prints EVERY
candidate it tried on failure (`cmd_dotscript.cpp:287-338`). The workspace
resolver reports ONE path, and not the expected one -- L0's failure named the
DATA root rather than the section. Two resolvers, same engine, one honest. The
attempts-trail is small, additive, and would have answered by printing what this
session answered by inference.

**AND ONE DOGFOOD LOOP CLOSED WITHOUT ANYONE PLANNING IT.** `WsLock` -- the
catalog's own cross-process lock -- calls `xbase::locks::try_lock_table`, the
shim this session modified in stages 1 and 1b. Every `WORKSPACE NEW`, `SAVE`,
`DESTROY` and `DELETE` now takes a table lock that records the acting member.
It also answers the safety question properly: `xbase::locks` uses a SIDECAR lock
file, not an OS handle on the DBF, so holding the catalog open in a work area is
orthogonal to `WsLock`. `l1verify` showed that empirically; this explains it.

Separately: `author_stamp()` writes `member#4/kind0` into every catalog row's
AUTHOR field -- a numeric surrogate, not the member key. **A SIXTH answer to
"who am I"**, inside the catalog itself. AIF-144's table needs a row.

## 6. AUTHOR ERRORS -- AND THE PATTERN NAMED IN THE LAST CLOSEOUT REPEATED FOUR MORE TIMES

**PATTERN TWO ("a statement about a pattern becomes an instance of it") reached
seven.** Instances 4 and 5 were committed INSIDE the closeout section naming the
pattern -- the gate caught them (`2 suppression(s) hiding nothing`), one blinding
a real tracked citation. Instance 6 was avoided: a `lock_is_mine` comment quoting
the old comparison would have matched a future grep for "does none survive".
Instance 7 was caught pre-commit: this session's catalog-split design cited the
untracked catalog by repo path in a document partly about that defect.

**THREE HANDOVERS IN A ROW FAILED THE SAME WAY** -- angle-bracket placeholders
taken literally, a missing `do x64`, and an abbreviated `D:\...` path re-printed
in chat after the file on disk was correct. **The file being right does not help
when what gets pasted is the chat.** Fixed by handing over `.dts` scripts the
engine reads instead of text to paste; every probe since has run first time.

**AN INSTRUMENT WAS WRONG AND EVERYTHING IT MEASURED WAS RE-RUN.** The
brace-balance checker used on every engine edit was a regex handling neither char
literals nor block comments; it reported `lexer.cpp` as 23/25 BEFORE any change.
Replaced with a state-machine counter and all nine edited files re-verified.
**An instrument that agrees with you is not thereby correct.**

**TWO DUPLICATE EMPTY COMMITS** carry the stage-1b message
(`c7a57c9c1`, `a12b157fe`), each holding only a regenerated `TIER0_STATE.md`.
The mechanism is worth knowing: **`tier0-refresh` guarantees a commit is never
empty**, so a repeated `git commit -F <same file>` always succeeds and always
produces a duplicate. `prepush-gate`'s "no changes in staged index" guard fired
once and was defeated on the next attempt by the regeneration. Not unwound --
shared worktree, live co-session -- but named so a reader does not conclude
stage 1b landed three times.

**A METHOD NOTE, because the owner raised it directly.** Told to rest before
continuing, the honest answer was that there is nothing to rest. What degrades
across a long session is not stamina but **self-citation**: my own earlier
summaries start functioning as evidence in place of the tree. That is precisely
the shape of pattern one from the last closeout -- four documents read as current
state. The mitigation is not focus, it is re-measurement plus writing state to a
durable place, which is what the lifecycle plan and this closeout are for.

## 7. OPEN, AND WHOSE

1. **AIF-144 sec 7 R-b and R-c** -- the path resolver, the SECURITY legacy
   selector. R-a is taken. Owner's.
2. **L2's affordance** -- new `SET PATH` grammar, or an alternative. Owner's.
3. **The catalog split** -- ruling requested by the design. Owner's.
4. **GPS's three unfired arms**; `GO 201` is the cheapest.
5. **`SET DELETED OFF` across both traversal paths** (AIF-142 sec 8).
6. **`LOCK <n>` does not validate `n` against `recCount64()`** -- found while
   testing stage 1, unclaimed.
7. **`occupied_desc()`, `current_slot()`, `WSREPORT` scope** -- reporting.
8. **`AI_TIER1_SEED_V1.md` at 89% of its 8192 B budget.**

## 8. GOOD NEIGHBOUR

- **What changed:** `include/xbase_locks.hpp`, `src/xbase/xbase_locks.cpp`,
  `src/identity/identity_admin.cpp`, `src/cli/cmd_lock.cpp`,
  `src/cli/expr/lexer.cpp`, `src/cli/cmd_list.cpp`, `src/cli/cmd_count.cpp`; four
  new `.dts` probes; one design; one finding amended. **AND THE PRODUCTION
  CATALOG: 110 rows flagged and superseded.**
- **Whose area:** `src/xbase/**` and `src/cli/**` are engine; every change had an
  explicit go. The catalog write was authorized twice.
- **How to verify:** `do l0probe`, `do l1census`, `do l1verify` reproduce secs 4.
  Stage 1's proof is ten commands at the prompt.
- **How to undo:** `tmp/*.pre-*` hold every pre-change source file.
  `tmp/catalog_backup/WORKSPACES.{dbf,dtx}.20260827T230621Z` is the ONLY rollback
  for L1; there is no in-engine undo.

**Author does not self-approve. Every finding and design ships review-needed.**
