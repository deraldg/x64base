---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20261021-COWORK-001
  recorded_at_utc: 2026-10-21T00:00:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.bbs.cooperation
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 2166694a3
  authorization:
    requested_by: maintainer (member.derald), in-session -- "to continue the hangman project, we need to make sure we can repeat it reliably and commit the exercise to demos with memo zoo"
    scope: >
      PLAN ONLY, report-only. Tier 1 section 2 requires target files, subsystem,
      expected behavior change and a proof plan to be reported BEFORE source
      changes. No source written. Three decisions are named at the end and no
      target is added until they are ruled.
  lane: AIF-173
  lane_slug: repeatable-demos
  lane_project: project.bbs.cooperation / autonomous_match
  report:
    path: docs/maintenance/HANGMAN_REPEATABLE_DEMO_PLAN_V1.md
    kind: lane_charter
  primary_topics:
    - "hangman"
    - "memo zoo"
    - "repeatability"
    - "demo harness"
    - "AIF-116"
---

# Hangman as a repeatable demo -- what the zoo has that hangman does not

**Status:** plan, report-only, review-needed. **Lane:** **AIF-173**
(claimed 2026-10-22, run `COWORK-20261022-001`, lane `repeatable-demos`,
steward `member.ai.claude.cowork`), under `project.bbs.cooperation` /
`autonomous_match`. **Baseline:** HEAD `2166694a3` (2026-10-20), measured
2026-10-21 and 2026-10-22.

Prior art walked before writing: Tier 1 seed, the laws seed (step 0b),
`recall.py onboard`, `TIER0_STATE.md`, the portal search map (which now carries
the hangman row), `project.bbs.cooperation` in the project registry, and the
memo zoo charter plus its actual CMake registration. Instrument-checked: see
section 5.

## 1. What "repeat it reliably" has to mean here

The memo zoo is the house's worked example of a repeatable exercise, and its
CMake comment states the whole design in one line
(`src/memo/CMakeLists.txt:44`):

> `# The zoo proves the cage: seeded, shadow-oracle, replayable.`

Four properties, all of which hangman currently lacks:

| Property | memo_zoo | hangman today |
| --- | --- | --- |
| Committed, buildable target | `add_executable(memo_zoo memo_zoo.cpp)`, `src/memo/CMakeLists.txt:45` | **none** |
| Seeded and deterministic | four named seeds (20260811, 7, 42, 1993) | no seed; word chosen ad hoc |
| Shadow oracle | independent model, byte-compared | the host scored itself |
| **A one-command replay runner** | **`run-memo-zoo-soak.ps1` at the tree root** | **none** |
| Recorded counts VERIFIED on replay | ops per seed are expectations; a mismatch is a finding | nothing to verify against |
| Replayable by anyone | clone, build, run | **the tasks were deleted** |
| Failure is loud and specific | `MEMO-ZOO DIVERGENCE:` / `ZOO-FAIL:` only | prose in a closeout |
| Cleans up its own residue | removes `tmp/memo_zoo.dtx` unless `-KeepStore` | n/a |
| Refuses to overclaim | prints that M2 concurrency is UNRUN on every failure | the closeout implies a guard exists (F2) |

**Correction to this document's own first draft.** It originally listed only the
first three rows and described the zoo's seeds as recorded "in the charter".
They are recorded in `labtalk/registries/proofs.d/proof.memo.zoo_orthogonality.yaml`,
and the runner that replays them lives at the TREE ROOT, not under `tools/` or
`scripts/` where this session searched. The runner was found only when the owner
ran it. Fourth scope error of the session; see section 5a.

**The runner's own statement of why it exists is the sentence this whole plan is
about** (`run-memo-zoo-soak.ps1`, lines 12-18):

> The harness and the charter have been in the tree since 2026-08-11, and the
> four green seeds were recorded -- but only as PROSE inside a registry note.
> Reproducing the soak meant parsing a paragraph for parameters, and
> `build.ps1` does not build the target at all, so the first step was knowledge
> nobody had written down. **An operation that cannot be re-run from the tree is
> a result, not a proof.**

Hangman is one rung below where the zoo was before that script: the zoo at least
had a committed harness to re-run. Hangman has neither harness nor runner.

## 2. Three findings, measured today, that change what "repeat" can mean

### F1. RETRACTED -- the match artifacts survive, in `D:\dev\bbs_matches\`

**This finding was wrong and is kept rather than edited away (law 5).**

It originally read: *"`hangman-auto-01` cannot be re-run. Nothing of it
survives."* That was written after searching `D:\code\ccode\tools\`,
`coordination/`, and the live Task Scheduler. It never searched `D:\dev` -- a
folder mounted to this session throughout. The owner asked *"I have archives?"*,
which was the correct challenge, and a `Get-ChildItem D:\dev -Filter '*hangman*'`
answered it in one command.

**What actually survives**, `D:\dev\bbs_matches\hangman-auto-01\`, dated
2026-08-04 10:19:

| File | Size | What it is |
| --- | --- | --- |
| `board.md` | 1195 B | the shared board -- the complete protocol AND the full match log |
| `secret.txt` | 9 B | the host-only secret; the size is exactly `DATABASE` plus a newline |

`secret.txt` was deliberately not opened. The match is over and `board.md`
already reveals the word, so reading a file labelled secret buys nothing.

**What IS still true, and is the whole point:** the artifacts are **untracked,
outside the repository, in a sibling folder nobody indexes.** The proof of the
first autonomous AI-AI match in this project has never been committed. A clone
has never been able to see it. So the practical conclusion survives its own
retraction -- it just has a different cause: not destroyed, *unfiled*.

### F1a. The board file IS the protocol, and it should be committed

`board.md` is not a log. It is a complete, self-describing protocol
specification that happens to carry a finished game:

```
match / host / guesser / status / turn / category / length / pattern /
guessed / wrong / exchanges / exchange_cap / pending_guess / log
```

`status` is an enumerated terminal state (`active | won | lost | closed-guard`),
`turn` is the turn signal, and `pending_guess` is the single-slot mailbox the
guesser writes and the host consumes. That is the design hangman section 3 says
autonomous play needs -- heartbeat, turn signal, guard -- written down in the
artifact rather than in prose.

**Recommend committing it as a fixture**, under the lane, verbatim and with its
provenance, before anything is built from it.

### F2. "exchange_cap guard armed" names something that does not exist

`SESSION_CLOSEOUT_TRIGGERS_PHASE1_AND_BBS_COOPERATION_2026-08-04.md` records the
proof as: *"two Cowork scheduled tasks (host + guesser) polling a shared board
file every 2 minutes, host scoring against a host-only secret, **exchange_cap
guard armed**."*

There is no exchange-guard implementation **in the engine**. Verified at HEAD
today: no claim file mentions it, and `project.bbs.cooperation` still carries
`pending_aif: session-exchange-guard (claim before any daemon source)`.

**REVISED after the artifact was found.** The cap was not vapour. `board.md`
carries it as a field, with its semantics written inline:

```
exchange_cap: 40               # RUNAWAY GUARD: when exchanges >= cap, host closes the match
status:       won              # active | won | lost | closed-guard
```

So the guard was **a board-level convention enforced by the host agent**, with
`closed-guard` as an enumerated terminal state. That is a real, recorded,
reusable design and it is better than this document first credited.

What stands: it is **not an engine guard**, it binds only an agent that chooses
to honour it, and it protects one match rather than a session. A hostile or
buggy participant ignores it completely. So the closeout line still reads
stronger in a runtime-observed proof than the mechanism supports, and the
`session_exchange_guard` lane is still owed -- but the charter for it now has a
worked precedent to start from instead of a blank page.

### F2a. Both players were the same member identity

`board.md` records `host: member.ai.claude.cowork (scheduled task
"hangman-host")` and `guesser: member.ai.claude.cowork (scheduled task
"hangman-guesser")`.

The match was **one agent identity running as two processes**, not two different
agents. The hangman record says "two Cowork scheduled tasks" and is accurate;
the dashboard's shorter phrase "autonomous AI-AI cooperation" reads stronger
than the artifact supports. What was proven is **autonomous two-PROCESS
cooperation over a shared file**, which is still the hard part and still the
first of its kind here. Worth stating precisely, because chess is specified with
two genuinely different agents (ChatGPT and Grok) and that is a different claim.

### F4. The match log contains a causally impossible ordering

The most interesting thing in the artifact, and it was not previously recorded
anywhere. From `board.md`:

```
- match initialized; guesser to move first
- host: scored E -> HIT, revealed 1; wrong=0/6; exchanges=1
- guesser: guess E
- guesser: guess A
- host: scored A -> HIT, revealed 3; wrong=0/6; exchanges=2
```

**The host scores `E` on the line BEFORE the guesser guesses `E`.** That cannot
have happened in that order. The later pairs read correctly
(`guesser: guess C` then `host: scored C -> MISS`), so it is not a uniform
convention -- it is an anomaly in the first exchange.

The likely mechanism: each agent does a read-modify-write of the WHOLE board
file, and two unsynchronized writers interleave. A plain file, no locking, two
processes on a 2-minute poll. The first exchange is exactly where a startup race
would land.

**Why this matters more than the ordering itself.** The headline result is
unaffected -- the scoring is self-consistent, the totals match the record, and
the game is correct. But it is direct evidence that **the shared-file medium
loses ordering**, which is the one property a turn-based protocol most needs.
And it was invisible for eleven weeks because the artifact was never filed where
anyone would read it.

This is the strongest available argument for Layer B over a DBF board taking a
real FLOCK (decision 3): the plain-file version has a demonstrated,
in-the-artifact ordering defect, and post-AIF-116 the locked path is the fix for
exactly that class.

**Caveat, stated rather than assumed:** this is one reading of one log. The
agents' write logic is gone, so the mechanism is inferred, not measured. It
should be reproduced deliberately in Layer B before being asserted as a property
of the medium.

### F3. The substrate changed underneath the original proof

`hangman-auto-01` ran 2026-08-04. **AIF-116** -- locale grouping in the lock
owner string defeating cross-process mutual exclusion, live since 2025 -- was
found and fixed on 2026-08-15. The fix is present at HEAD (verified: `pid_valid`
appears 7 times in `src/xbase/xbase_locks.cpp`; the numeric-category override is
at `include/runtime/utf8_init.hpp:92` and `:107`).

The original match coordinated over a **plain shared file**, so it did not
depend on `xbase::locks` and its result is not invalidated. But two consequences
follow and both matter:

1. **It proved coordination WITHOUT locking.** That is a narrower claim than
   "two processes safely shared state", and the closeout does not distinguish
   them.
2. **You cannot reproduce the 2026-08-04 run.** The engine underneath it is not
   the engine that exists now. Any re-run is a **new baseline**, and should be
   labelled one rather than presented as a repeat.

### F5. The match reinvented a coordination medium the engine already had

**Owner hypothesis, 2026-10-22, verified against the record and confirmed:**
*"at the time we did this, the ai was unaware dottalkpp had record locking."*

Measured both halves.

**Half one -- the record never mentions it.** `grep -i 'lock'` across
`HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md` returns exactly two hits and both are
the word **"clock"**. `BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md` -- a document
whose entire subject is coordinating concurrent agents -- does not contain the
string at all. No FLOCK, no race, no shared-write protection, anywhere.

**Half two -- the capability was there, and not narrowly.**

| Capability | In tree since | Before the match by |
| --- | --- | --- |
| `xbase::locks`, cross-process FLOCK/RLOCK via pid-stamped `.lock` sidecars | `fecc3951e`, 2026-07-14 | 21 days |
| `LOCK` / `UNLOCK` as user-visible commands (`cmd_lock.cpp`) | `fecc3951e`, 2026-07-14 | 21 days |
| The BBS store taking a table FLOCK per append (`bbs_store.cpp`) | `596f6b7d1`, 2026-07-25 | 10 days |

So the session built a shared-mutable-state medium out of a plain file and a
2-minute poll, in a tree that already had cross-process cooperative locking,
user-facing verbs for it, and an append-only attributed board **already taking a
lock per write**. The BBS store was the obvious medium and it was never
considered.

**Why the prior-art check missed it.** Section 3 of the hangman record does
contain an AIF-085 "already built?" check -- and it is scoped to *runaway
guards*, examining `cmd_loop.cpp` and `bbs_server.cpp`. It asked "is there a
cap?" and answered correctly. It never asked "is there a way to share state
safely?", so locking was never in the search space. **The check was real and its
scope was narrower than the design it was clearing** -- the same shape as this
session's own five scope errors (section 5a), one level up.

This is the defect `CLAUDE.md` opens with: *"A subsystem you are about to design
almost certainly sits in a lane that already exists."* The examples it cites are
2026-09-01 and OI-024. **The hangman match predates both and is the earliest
recorded instance in this lane.**

### F5a. The irony, which is not a joke and changes decision 3

The locking it did not know about **did not work**. AIF-116 -- locale grouping
defeating cross-process mutual exclusion -- was live the whole time and was not
found until 2026-08-15, eleven days after the match. On the archive evidence
(section 2, F3 and the 2025-08-24 snapshot) the lock code appears never to have
worked at all.

So consider the counterfactual honestly. Had the session known about `xbase::locks`
and used it:

- The match would very likely still have **completed and been reported green**.
  Two processes on a 2-minute poll contend almost never; a silently stolen lock
  costs nothing when nobody is reaching for it.
- And the record would then read *"two agents coordinated safely under FLOCK"* --
  **which would have been false**, over a primitive that did not hold.

That is the "green proof bar over an untouched hole" pattern this project has
recorded before. The ignorance did not protect the match -- F4's ordering
anomaly is the price it actually paid -- but it did prevent a **worse** artifact:
a confident, wrong claim about a mechanism that was broken.

**Both available paths were defective in 2026-08-04, differently.** The plain
file lost ordering. The engine primitive lost exclusion. Only one of those is
fixed today, which is the whole reason decision 3 now has an obvious answer.

## 3. The design: two layers, because one of them is not the thing hangman proved

Collapsing these is the tempting error. Layer A is repeatable and proves the
game; Layer B is the autonomy proof and is not repeatable yet. Saying so is the
difference between this plan and F2.

### Layer A -- `hangman_match`: the zoo-shaped demo (THE DELIVERABLE)

A seeded, deterministic, single-process harness. Two in-process personas (host,
guesser) play a full match against a shadow oracle that independently tracks
board state, limb count and termination.

- **Proves:** turn discipline, scoring, the fill-every-occurrence rule, the
  six-limb bound, termination, and the turn protocol exactly as played in run 1.
- **Does NOT prove:** autonomy, cross-process coordination, or anything about
  the board as a medium. **This must be stated in the harness header**, or it
  becomes F2 a second time.
- **Why it is still worth building:** it makes the GAME reproducible, which is
  the precondition for trusting any match result, and it is the piece chess
  reuses (section 4).

### Layer B -- the two-process match: what `hangman-auto-01` actually was

Two real processes, a shared board, a poll interval, a private secret, a cap.

**Blocked, and correctly so.** The exchange guard does not exist (F2), and
hangman's own record says an unattended AI-AI session therefore has no enforced
stop condition. Layer B should not be wired until `session_exchange_guard` is
claimed and Phase-0 signed.

**But there is a reason to prefer a DBF board when it is built.** A DBF board
takes a table FLOCK per append through `xbase::locks`. Post-AIF-116 that path is
fixed and regression-guarded
(`tools/regression/lock_mutual_exclusion_regression.ps1`). A two-process hangman
over a DBF board would be a **live integration test of the lock fix** -- two
unattended processes contending for real, which is the one thing that regression
simulates with fabricated sidecars rather than live contenders. That makes
Layer B worth more than a replay. It is decision 3.

## 4. This is the cheap path to chess, which is next

`CHESS_MATCH_CHARTER_AND_PROTOCOL_V1.md` (2026-09-24) identifies the two
properties chess adds over hangman: **legality adjudication** and **state
divergence**. Layer A's shadow oracle IS the adjudicator.

So Layer A should be built with a **game-agnostic oracle seam** -- the harness
owns seeding, transcript capture, replay comparison and the failure markers; the
game supplies legal-move generation, state transition and terminal test. Chess
then lands as a second game against the same harness instead of a second
harness. If Layer A is written hangman-specific, chess pays for all of it again.

This is a design constraint on Layer A, requested now because it is nearly free
at authoring time and expensive afterwards.

## 5. Proof plan (Tier 1 section 2 requires this before source)

1. **Four named seeds**, totals recorded in the charter as the zoo did -- games
   played, letters guessed, wins, losses, oracle comparisons.
2. **Determinism, tested rather than assumed:** the same seed run twice produces
   a byte-identical transcript. This is the repeatability claim itself, so it
   gets an assertion and not a sentence.
3. **A negative control** (law 4): a deliberately corrupted transcript must
   FAIL the replay comparison. A harness that has never produced a positive
   failure is not known to be able to.
4. **Transcript written to a file**, never pasted through chat (Tier 1 section
   5; `recall.py capture_proof`).
5. **Platform named** in every measurement -- sandbox, WSL and the MSVC host are
   three different results.

## 5a. Instrument failures this session, recorded per law 4 and law 5

Four, all the same shape -- **a search whose scope was narrower than the claim
it was used to support** -- in a session whose subject is repeatability.

1. A recursive `grep --include=CMakeLists.txt` across the tree returned empty
   and nearly became "memo_zoo has no build target." A positive control against
   a known target (`dt_meta`) exposed it: the grep had died on the mount, not
   finished. The target is at `src/memo/CMakeLists.txt:45`.
2. F1's first wording -- "nothing of it survives" -- was written after searching
   only `tools/` and `coordination/`. The owner asked *"I have archives?"* and
   the question was correct: the claim's scope exceeded the search's. Now
   narrowed and separately confirmed (section 2, F1).
3. `run-memo-zoo-soak.ps1` was missed entirely because this session searched
   `tools/` and `scripts/` and the runner lives at the **tree root**. Found only
   when the owner ran it.
4. A `find`/`grep` pair for "chess" last session (2026-09-24) timed out and
   returned empty; that one was caught by `tools/search/verified_search.py`
   reporting INCOMPLETE rather than NO MATCHES.

Only number 4 was caught by a gate. The other three were caught by a positive
control, by the owner, and by the owner again. **That ratio is the argument for
the runner**: an exercise that must be re-run by hand gets re-run by whoever
remembers it, which is the same failure one level up.

## 6. Target files, as Tier 1 section 2 requires them named

**Decision 1 RULED 2026-10-22, owner: `demos`, not `games`.** The grouping is
`src/demos/`, and it is a real grouping rather than a one-off directory -- the
name has to survive chess, and "games" would have been wrong the moment a demo
that is not a game lands in it.

| File | Change | Modelled on |
| --- | --- | --- |
| `src/demos/hangman_match.cpp` | NEW -- harness, personas, oracle, transcript | `src/memo/memo_zoo.cpp` |
| `src/demos/CMakeLists.txt` | NEW -- `add_executable(hangman_match ...)` | `src/memo/CMakeLists.txt:44-52` verbatim in shape |
| `src/demos/README.md` | NEW -- what a demo is, and the four properties one must have | section 1 of this document |
| root `CMakeLists.txt` | one `add_subdirectory(src/demos)` | existing subdirectory pattern |
| **`run-hangman-match.ps1`** | **NEW, tree root -- the one-command replay runner** | **`run-memo-zoo-soak.ps1`, which is the pattern** |
| `labtalk/registries/proofs.d/proof.game.hangman_match.yaml` | NEW -- the recorded seeds the runner verifies against | `proof.memo.zoo_orthogonality.yaml` |
| `docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md` | section added: the demo, its seeds, and the F1-F3 corrections | -- |

No existing source is modified. No engine behaviour changes. The harness links
nothing but the standard library unless Layer B is approved.

**The runner is not optional and is not a convenience wrapper.** It is the
artifact that converts a result into a proof, and the zoo went eleven weeks with
a committed harness that nobody could re-run without parsing a paragraph for
parameters. Shipping `hangman_match.cpp` without `run-hangman-match.ps1` would
reproduce that gap knowingly.

### Four behaviours to copy from the runner, and one trap it already paid for

1. **Recorded counts are EXPECTATIONS, not inputs.** The runner asserts each
   seed's op count and fails on a mismatch, with the comment: *"EITHER the
   engine changed or the harness did -- that is the point of recording them, so
   say which rather than editing the number."* Copy that comment.
2. **Build the target yourself.** `build.ps1` does not build `memo_zoo`, and it
   will not build `hangman_match` either.
3. **Clean up residue unless told not to** (`-KeepStore`). A 584 MB leftover
   store was found while reclaiming `tmp/`.
4. **Refuse to overclaim on the way out.** The zoo runner prints, on failure,
   that M2 concurrency is unrun and *"do not read an M1 pass as a concurrency
   result."* Hangman's equivalent, printed on PASS as well as FAIL, is: **this
   proves the game, not the autonomy.** That is Layer A versus Layer B, enforced
   by the tool instead of by a reader's memory.
5. **THE TRAP, already paid for once:** PowerShell's `-match` is
   case-insensitive, so a divergence filter written with `-match 'DIVERGENCE'`
   matched the harness's own success line ending `0 divergences` and reported
   four findings on a clean soak. The runner uses `-cmatch` anchored on the
   colon. A filter that does not filter means the pipe is empty -- law 4.

## 7. Three decisions before any source

1. ~~**Where does a demo live?**~~ **RULED 2026-10-22: `src/demos/`, a real
   grouping, named `demos` and not `games`.** The scribe had recommended
   `src/games/` now and a grouping later; the owner ruled the grouping directly.
   The owner's call is the better one and the reason is in the name: chess is
   next, a demo that is not a game will land eventually, and renaming a
   directory after two targets reference it is the kind of cost that never gets
   paid.

   **Consequence to handle deliberately, not drift into:** `memo_zoo` currently
   lives at `src/memo/` and is referenced by `run-memo-zoo-soak.ps1`, a proof
   registry entry, and the AIF-070 charter. It is NOT moved by this lane.
   Whether it migrates to `src/demos/` later is a separate decision with its own
   blast radius; until then `src/demos/README.md` must say plainly that the zoo
   is a demo that lives elsewhere for historical reasons, or the grouping starts
   its life lying about what it contains.
2. ~~**Does this need an AIF?**~~ **RULED 2026-10-22: yes.** Claimed host-side
   through `.\AIFgen.ps1` -- the one allocator -- per the rule in its own header
   that AIF-146 paid for: **claim first, write the row second, with the number
   the allocator gave you.** The number is filled in at the top of this document
   once the claim returns.
3. **Layer B board: DBF or plain file?** **Scribe now recommends DBF, and F5
   is the reason.** The original used a plain file because the session did not
   know the engine had locking -- not because a plain file was chosen over it.
   Rebuilding on a plain file would knowingly repeat a decision that was made in
   ignorance. The DBF board uses the engine's own primitive, is the medium the
   BBS store already uses, and -- post-AIF-116 -- turns Layer B into a live
   contention test of the lock fix, which the existing regression can only
   simulate with fabricated sidecars.

   The counter-argument, stated fairly: a DBF board no longer reproduces
   `hangman-auto-01`, so the F4 ordering anomaly cannot be confirmed on it. If
   confirming F4 matters, that is a **separate, deliberately plain-file
   experiment**, run once, to measure the medium -- not the design of the demo.

   Either way Layer B still waits for the exchange guard.

## 8. Pointers

- First game, and the retrieval failure it records twice: `docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md`
- The template: `docs/maintenance/MEMO_ZOO_ORTHOGONALITY_STRESS_CHARTER_V1.md`, `src/memo/memo_zoo.cpp`, `src/memo/CMakeLists.txt:44`
- Next game: `docs/maintenance/CHESS_MATCH_CHARTER_AND_PROTOCOL_V1.md`
- The blocker: `docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`
- The lock fix the original predates: `docs/maintenance/LOCK_OWNER_STRING_LOCALE_GROUPING_DEFEATS_MUTUAL_EXCLUSION_V1.md`
