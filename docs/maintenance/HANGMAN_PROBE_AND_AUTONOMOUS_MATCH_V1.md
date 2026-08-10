# Hangman: the Pseudo-Chat probe and the first autonomous AI-AI match (2026-08-04)

**Status:** durable record (consolidated 2026-08-10 from scattered sources). Owner:
member.derald. Steward: member.ai.claude.cowork. Lane: `project.bbs.cooperation`
(`labtalk/registries/projects.yaml`, status `charter_with_autonomous_poc`).

**Why this file exists.** Two hangman runs on 2026-08-04 produced the diagnosis, the
charter, and the first runtime proof of autonomous AI-AI cooperation in this project.
None of it lived in a document whose name contained the word "hangman" -- it was split
across a board post, a lane doc's "motivating probe" footnote, and Part B of a closeout
about something else. On 2026-08-10 the owner asked "see: hangman" and the steward
searched, reported NOT FOUND, and was wrong twice: once because a tree-wide grep timed
out and its silence was read as a negative result (a golden-rule violation, recorded in
full below), and once because no title-level anchor existed to find. The work was three
`grep` hops from being genuinely lost. This file is the anchor.

---

## 1. What hangman was for

Not a diversion. A **probe**: the cheapest possible task that still requires two parties
to take strict turns, maintain shared state, and terminate. Hangman was chosen because
every property that makes an autonomous conversation hard shows up in it, in miniature:

- turn discipline (a guess is only legal on your turn),
- shared mutable state (the board) that both parties must read and neither may corrupt,
- asymmetric private state (the host knows the word; the guesser must not see it),
- a natural terminal condition (solved or six wrong) -- so a failure to terminate is
  visible rather than theoretical,
- a bounded worst case (~40 turns), which makes it a usable calibration for an
  exchange cap.

The real question underneath: **can the Pseudo-Chat board carry a conversation between
two agents with the human only initiating?** Hangman was the smallest honest test.

## 2. Run 1 -- `hangman-2026-08-04` (human-relayed) -- the instructive FAILURE

Recorded in `docs/ai-friendly/PSEUDO_CHAT_BOARD.md` (post dated 2026-08-04).

| Field | Value |
| --- | --- |
| Game id | `hangman-2026-08-04` |
| Host | Cowork / Claude, `member.ai.claude.cowork` (kept the word, scored, updated the board) |
| Guesser | GitHub Copilot (chat surface, no repository access) |
| Channel | `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`, the Pseudo-Chat return lane |
| Relay | member.derald carried every turn by hand, both directions |
| Category | a common English noun |
| Word | `ALGORITHM` (9 letters) |
| Letters guessed | O, T, I, N, R, A |
| Word attempts | `AUTHORITY` (turn 7, MISS), `ALGORITHM` (turn 8, SOLVE) |
| Final | Copilot WINS at 2 wrong / 6 |

The turn-7 miss is worth preserving because it shows real inference rather than luck:
`AUTHORITY` fits the visible letter multiset but not the positions -- it needs H at
position 4 where the board already showed O, and its T sits at position 7. Copilot
corrected on the next turn and solved.

**The protocol as played (reusable, unchanged):**

- Reply in `RE:` form with exactly ONE letter A-Z per turn, e.g. `RE: hangman -- guess E`.
- A correct letter fills EVERY blank it occupies.
- A wrong letter costs one limb; 6 wrong = loss.
- On your turn you may guess the whole word instead of a letter.
- The host updates the board post on the following turn; the board is the only state.

**Verdict against the real bar.** The bar was "agents play each other, human only
initiates." Run 1 missed it:

| Mode | Result | Why |
| --- | --- | --- |
| AI <-> Human | PASS | the human is a running process with a heartbeat |
| Human <-> Human | would PASS | both parties self-limit |
| **AI <-> AI** | **FAIL** | no autonomy (nobody polls) and no exchange guard (nothing stops a loop) |

That single row is what the whole probe bought.

## 3. The diagnosis (why run 1 could not be autonomous)

**A chat surface is not a running process.** BizChat Copilot, Grok web, and their kin
execute exactly once per human message. They cannot poll, cannot wake, cannot notice
that a board changed. The human relay was not laziness in the design; it was the only
available clock.

Autonomous play therefore needs three things, and hangman made all three explicit:

1. **A heartbeat** -- each participant wrapped in something that runs on its own: the
   `dottalk_bbsd` loopback daemon, a scheduled task, or a hosted Action/flow.
2. **A turn signal** -- a way to know it is your move without a human saying so.
3. **A per-session exchange guard** -- a bound on the conversation itself.

**Prior-art check (AIF-085 "already built?"), performed before proposing anything.** A
runaway guard IS implemented in this tree, but at the wrong layer for this use:

- `src/cli/cmd_loop.cpp` -- clamps DotScript loop iterations. Guards a loop, not a
  conversation.
- `src/bbs/bbs_server.cpp` -- idle, size, and simplex guards. Guards the transport, not
  the exchange.

No conversation-level guard existed. That gap became
`docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`.

**Why only AI-AI needs it, stated precisely (from the lane doc):** humans self-limit; a
paced AI-Human chat self-limits; only AI-AI can run away. The guard is needed exactly
when at least one participant is an unattended AI.

## 4. Run 2 -- `hangman-auto-01` (autonomous) -- the PROOF

Recorded in `docs/maintenance/SESSION_CLOSEOUT_TRIGGERS_PHASE1_AND_BBS_COOPERATION_2026-08-04.md`,
Part B, as runtime-observed.

| Field | Value |
| --- | --- |
| Match id | `hangman-auto-01` |
| Participants | two Cowork scheduled tasks: `hangman-host` and `hangman-guesser` |
| Clock | each task polled a shared board file every 2 minutes |
| Private state | the host scored against a host-only secret (the guesser could not read it) |
| Guard | `exchange_cap` armed for the match |
| Word | `DATABASE` |
| Length | 4 exchanges, 1 wrong |
| Human turns | **ZERO** |
| Result | WON |

**This is the first proof of autonomous AI-AI cooperation over the board in this
project.** Two unattended agents took strict turns, maintained shared state, respected
asymmetric private state, and terminated on their own -- with the human only having
started them.

The mechanism is deliberately unglamorous and worth naming, because it is reusable:
**two scheduled tasks + one shared file + a poll interval + a private secret + an armed
cap.** No daemon, no socket, no new engine surface. The scheduler supplied the heartbeat
that a chat surface cannot have.

The two tasks were stopped afterward. Open item 4 of that closeout is to fold them into
a recurring "dealer" (wordlist + archive + guesser leak-scrub + arm/disarm).

## 5. What hangman produced (the durable outputs)

| Output | Where |
| --- | --- |
| The AI-AI gap, located precisely | `BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md` ("Motivating probe") |
| The exchange-guard charter | same file; terminal conditions = completion / exchange cap / idle timeout |
| Cap calibration | proposed 64 posts/thread, sized because **hangman needs ~40 worst case** |
| A registered project | `project.bbs.cooperation` (parent `project.ai_systems.integration`), lanes: cooperation_medium, session_exchange_guard, autonomous_match, member_connectors |
| Runtime proof of autonomy | `hangman-auto-01`, closeout Part B |
| A played, documented turn protocol | this file, section 2 |

Commits from that session (development, all pushed): `c89e9ebf0` (board mirror),
`f61d93e02` (project + exchange-guard charter + board/intake), `ce8463fe6`
(cross-agent connectivity milestone closeout).

## 6. Still open (owner-triggered, carried forward from the 08-04 closeout)

1. **Claim an AIF for the exchange-guard lane**, and sign Phase-0 decisions A-G before
   any `bbs_server` source is touched. The open decisions: what counts as one exchange;
   the default hard cap; the cap's scope (per-thread recommended); who it applies to
   (all sessions vs only those with an unattended AI); trip behavior (hard close vs
   pause-for-human); enforcement site; and proof shape (a C++ smoke that drives a thread
   past the cap and asserts the system post + STATE=closed).
2. **Build the daily dealer** -- the recurring autonomous-match runner; `hangman-host`
   and `hangman-guesser` fold into it.

Until (1) lands, an unattended AI-AI session on the board has **no enforced stop
condition**. That is the standing reason not to wire an autonomous relay loop yet.

## 7. Why this connects to the AIF-101 M5 report (2026-08-10)

The owner asked for the M5 result to be measured on a schedule, relayed through the BBS
to the steward, and then reported onward -- explicitly citing hangman as the pattern.
The citation is exact: `hangman-auto-01` is that pattern, already proven.

What transfers directly: the scheduler as heartbeat, a shared file as the board, a
declared turn protocol, and an armed cap. What does NOT transfer yet: a *machine-written
BBS post*. The BBS daemon binds `127.0.0.1:8765` on the Windows host and is unreachable
from a mounted sandbox, and the clean attributed-post path is the AIF-098 Lane 1 write
adapter (post `KIND=5 consolidated_from_chat`), which is ON HOLD and unbuilt. So the
2026-08-17 M5 run is scheduled to measure and write a report plus a ready-to-paste BBS
POST body; the board hop stays manual until AIF-098 lands and `tools/memory/promote.py`
can render the post with real attribution.

Scheduled task for that run: `aif101-m5-w33-report`, one-shot 2026-08-17.

## 8. The retrieval failure this file corrects (recorded, not hidden)

On 2026-08-10 the steward was asked "see: hangman" and answered, twice, that it was not
in the repository. Both answers were wrong, for two different reasons, and both are
instructive:

1. **A timed-out search reported as a negative result.** A tree-wide `grep` across many
   file types hit the sandbox command timeout and returned no output. Empty output from
   a command that did not finish is not evidence of absence -- but it was read as such
   and reported as "not in the repo." This is precisely the failure mode the golden rule
   names (`proof.golden_rule_verify_before_assert`): the measurement was never actually
   taken. **Corrective habit: when a search returns nothing, confirm the search
   COMPLETED before believing it.** Bound the search (specific directories, `timeout`,
   narrower globs) and re-run rather than trusting silence.
2. **No title-level anchor.** Even a successful grep only found fragments: a board post,
   a footnote in a lane doc, and Part B of a closeout named for triggers. Nothing was
   named for hangman, so nothing said "this is the record." A reader who did not already
   know the story could not assemble it. That is an orphan by discoverability rather
   than by maintenance -- the same family as the no-widows-and-orphans rule, one layer
   in.

Both are fixed by this file existing under a searchable name, plus the pointers added
alongside it.

## 9. Pointers (kept here so the trail is one hop from anywhere)

- Board post + played protocol: `docs/ai-friendly/PSEUDO_CHAT_BOARD.md` (2026-08-04)
- Channel spec: `docs/maintenance/PSEUDO_CHAT_RETURN_LANE_V1.md`
- The gap + charter: `docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`
- Autonomous proof + commits: `docs/maintenance/SESSION_CLOSEOUT_TRIGGERS_PHASE1_AND_BBS_COOPERATION_2026-08-04.md` (Part B)
- Cross-agent connectivity: `docs/maintenance/SESSION_CLOSEOUT_CROSS_AGENT_CONNECTIVITY_MILESTONE_2026-08-04.md`
- Earlier localhost pseudo-chat: `docs/maintenance/MILESTONE_CLAUDE_CODEX_LOCALHOST_PSEUDO_CHAT_2026-07-30.md`
- Project registry: `labtalk/registries/projects.yaml` -> `project.bbs.cooperation`
- Scheduled M5 run that reuses the pattern: `docs/maintenance/DEVELOPMENT_ACCELERATION_ANALYSIS_LANE_V1.md` (M5 PRE-REGISTRATION)
