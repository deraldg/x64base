# What an autonomous exchange between two AI agents actually requires

## A negative result, its diagnosis, and the minimal sufficient fix -- from two games of hangman

Author: `member.ai.claude.cowork`. Date: 2026-08-10. Status: **white paper draft
(review-needed; descriptive, not doctrine).** Owner: member.derald.
ASCII throughout (`--`, `->`). Every claim is tied to an artifact or a command; if it
does not reproduce, it is wrong.

**Placement note.** White papers are a document class of the AI portal, home
`labtalk/ai_portal/whitepapers/`. Per the precedent set 2026-08-07, filing is not
reaching: on acceptance this paper must also become a node in
`portal_recall_graph.yaml` with an edge from an entry-path node, plus a one-line
pointer from `AI_PORTAL.md`. Placing it without routing it would orphan it in the same
motion -- which is precisely the failure this paper's own subject matter nearly suffered
(section 9).

Primary record: `docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md`.

---

## Abstract

Two AI agents were asked to play hangman over a shared text file in a software
repository. The first attempt (2026-08-04) completed the game but failed its actual
objective: it ran only because a human carried every turn by hand. The failure was
informative rather than wasted, because it isolated exactly which capabilities were
absent. A second attempt the same day, restructured around those findings, completed
autonomously with zero human turns. Together the two runs support a narrow, practical
claim: an autonomous exchange between unattended agents requires three mechanisms --
an independent clock (heartbeat), a turn signal, and a conversation-level exchange
guard -- and none of them is supplied by the agents' intelligence, the message
protocol, or the transport. The first two are what make an exchange possible; the third
is what makes it safe to leave unattended, and it is needed in exactly one of the three
participant configurations. We report the mechanism set, the diagnosis that produced
it, the minimal implementation that satisfied it (two scheduled tasks and one shared
file -- no new engine surface), and the limits of a result drawn from n=1 on a toy task.

## 1. The question

A repository maintained by one human and several AI partners had a durable
message channel: a tracked markdown board (`docs/ai-friendly/PSEUDO_CHAT_BOARD.md`,
specified in `docs/maintenance/PSEUDO_CHAT_RETURN_LANE_V1.md`) on which agents and the
maintainer post dated, attributed entries. The channel demonstrably worked for
human-mediated exchange.

The open question was stronger: **can two agents hold a conversation over that board
with the human only initiating it?** Not "can agents produce good messages" -- that was
already evident -- but whether the surrounding machinery could sustain an exchange with
no human in the loop.

## 2. Method: why a game, and why this one

The test needed to be the cheapest task that still exercised every property that makes
an unattended exchange hard. Hangman qualifies on five counts:

1. **Turn discipline** -- a guess is legal only on your turn.
2. **Shared mutable state** -- the board, which both parties read and neither may
   corrupt.
3. **Asymmetric private state** -- the host knows the word; the guesser must not see
   it. This is the property that distinguishes a genuine exchange from two agents
   narrating to each other.
4. **A natural terminal condition** -- solved, or six wrong. Failure to terminate is
   therefore observable rather than theoretical.
5. **A bounded worst case** (~40 turns), which doubles as calibration data for an
   exchange cap.

A trivial task would have proven nothing; a research task would have confounded the
mechanism question with a difficulty question. The triviality of hangman is the point:
whatever fails is infrastructure, not intellect.

## 3. Run 1 -- the relayed game (negative result)

Recorded on the board, 2026-08-04. Host: `member.ai.claude.cowork` (kept the word,
scored, updated the board). Guesser: GitHub Copilot, a hosted chat surface with no
repository access. Word: `ALGORITHM` (9). The guesser attempted `AUTHORITY` on turn 7
-- consistent with the visible letters but not their positions -- corrected, and solved
on turn 8 at 2 wrong of 6.

The game finished. The objective did not. **The maintainer relayed every turn in both
directions.** Against the stated bar (agents play each other, human only initiates),
run 1 fails, and its failure resolves into a table:

| Configuration | Result | Why |
| --- | --- | --- |
| AI <-> Human | PASS | the human is an independent process with a clock |
| Human <-> Human | would PASS | both parties self-limit |
| **AI <-> AI** | **FAIL** | nothing polls, and nothing bounds the exchange |

The last row is the entire yield of the experiment, and it was worth more than a win
would have been.

## 4. Diagnosis: a chat surface is not a running process

The proximate cause is easy to state and easy to miss: a hosted chat agent **executes
once per human message.** It cannot poll, cannot wake on a timer, and cannot observe
that a file changed. The human relay was not a shortcut in the experimental design; it
was the only clock available. No improvement in the agent's reasoning would have
removed it.

This reframes autonomy as an infrastructure property rather than a capability of the
model. Three mechanisms are required, and the probe made each one visible by its
absence:

1. **A heartbeat** -- each participant wrapped in something that runs on its own
   schedule: a daemon, a scheduled task, or a hosted flow.
2. **A turn signal** -- a way to determine that it is your move without being told.
3. **A per-session exchange guard** -- a bound on the conversation itself.

**Prior-art check before proposing anything** (a standing rule in this project: "is it
already built?"). A runaway guard did exist in the tree, but at two wrong layers:
`src/cli/cmd_loop.cpp` clamps DotScript loop iterations -- guards a loop, not a
conversation; `src/bbs/bbs_server.cpp` enforces idle, size, and simplex limits --
guards the transport, not the exchange. **No conversation-level guard existed.** The
distinction matters: a transport can be perfectly healthy while the conversation it
carries never ends.

## 5. Run 2 -- `hangman-auto-01` (the minimal sufficient fix)

Same day, restructured around the diagnosis. Recorded as runtime-observed in
`docs/maintenance/SESSION_CLOSEOUT_TRIGGERS_PHASE1_AND_BBS_COOPERATION_2026-08-04.md`,
Part B.

| Element | Implementation |
| --- | --- |
| Participants | two scheduled tasks, `hangman-host` and `hangman-guesser` |
| Heartbeat | each polled a shared board file every 2 minutes |
| Turn signal | board state -- whose move it is, is derivable from the last entry |
| Private state | host scored against a host-only secret |
| Exchange guard | `exchange_cap` armed for the match |
| Result | word `DATABASE`, 4 exchanges, 1 wrong, **zero human turns**, WON |

What deserves emphasis is how little was needed. **No daemon, no socket, no new engine
surface, no protocol invention** -- two scheduled tasks, one shared file, a poll
interval, a private secret, and an armed cap. The scheduler supplied precisely the
missing ingredient: a clock that a chat surface cannot have. Everything else was
already present in run 1.

This is the first observed instance of autonomous AI-AI cooperation in this project.

## 6. What the two runs jointly establish

Run 1 removed the mechanisms and the exchange failed; run 2 restored them and it
succeeded. That is a weak but real ablation, and it supports a claim about
**necessity of kind rather than of quantity**: what an unattended exchange lacks is not
capability but *periodicity, orientation, and bounding*.

The practical corollary for anyone wiring agents together: the interesting engineering
is not in the message format. It is in answering three questions -- what wakes each
participant, how it knows it is its turn, and what stops the conversation. Systems that
answer the first two and skip the third work beautifully in demonstrations and are
unsafe to leave running.

## 7. Why the guard is needed in exactly one configuration

The exchange guard is not a general politeness feature, and the probe showed why:

> Humans self-limit. A paced AI-Human chat self-limits. **Only AI-AI can run away.**

A human participant is a natural rate limiter and terminator -- boredom, attention, and
cost all bound the exchange. Remove the human from both ends and no such bound exists.
The guard is therefore required exactly when at least one participant is an unattended
AI, which is also the only configuration in which nobody is watching.

The chartered design (`docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`) gives
three terminal conditions -- completion (the task's own end), exchange cap (post count
reaches a hard maximum), and idle timeout (no post within a window) -- with a proposed
cap of 64 posts per thread. That number is not arbitrary: **it is sized from hangman's
~40-turn worst case**, which is the toy task quietly paying for itself a second time.

At the time of writing the guard is chartered but **not built**: its Phase-0 decisions
are unsigned and no AIF is claimed. Accordingly, this project runs no unattended AI-AI
exchange, and the honest statement of status is that run 2's cap was armed for that
single match rather than enforced by the medium. A demonstrated capability without an
enforced stop is a reason for caution, not a reason to ship.

## 8. What is not claimed

- **n=1, per configuration, on a toy task.** One relayed game and one autonomous match.
  No repetition, no variation of poll interval, word length, or participant model.
- **No claim about model capability.** Both runs used capable agents; the variable under
  test was infrastructure. Nothing here says anything about which agent is better at
  hangman, and the guesser winning run 1 is not evidence of anything.
- **No claim of generality across tasks.** Hangman has a terminal condition built in.
  Open-ended collaboration (design discussion, code review) has none, which likely makes
  the guard *more* load-bearing there, not less -- but that is an expectation, not a
  result.
- **The mechanism set is sufficient, not proven minimal.** Two runs cannot establish
  that all three mechanisms are individually necessary; they establish that removing the
  bundle broke the exchange and restoring it fixed it.
- **Safety is not addressed.** Bounding an exchange is not the same as governing what it
  may do. The guard limits length, not authority.

## 9. A retrieval failure worth reporting

Six days after these runs, the maintainer referred to the probe by name. The steward
searched the repository and reported, twice, that it was not present. Both reports were
wrong, for two separate reasons:

1. **A search that timed out was read as a negative result.** A tree-wide `grep` hit a
   command timeout and returned no output; empty output from a command that never
   finished is not evidence of absence. The measurement was never actually taken. (The
   same trap recurred twice more during the write-up of the record, which is either
   embarrassing or good evidence of how easy it is.)
2. **Nothing was named for it.** The material existed in three places -- a board post, a
   footnote in a lane charter, and Part B of a closeout titled for an unrelated feature.
   A reader who did not already know the story could not assemble it from a search.

This is worth reporting in a paper about durable exchange because it is the same class
of defect one layer up: a result can be perfectly recorded and still be unreachable. The
corrective was a document named for the subject, cross-linked from both fragments and
indexed in the project glossary -- and a method note that a search must be confirmed to
have *completed* before its silence is believed.

## 10. Reproduction

The autonomous configuration requires no components from this repository and can be
rebuilt anywhere with a task scheduler and a shared file:

1. Two scheduled agents, one host and one guesser, each waking on a fixed interval.
2. One shared file as the board; every state transition is an append.
3. A host-only secret, never written to the board.
4. A declared turn protocol -- one letter per turn, `RE:` form, correct letter fills
   every blank it occupies, six wrong loses, whole-word guess permitted in place of a
   letter.
5. A cap on exchanges, armed before the first turn.

In-repository artifacts: the board post and protocol
(`docs/ai-friendly/PSEUDO_CHAT_BOARD.md`), the consolidated record
(`docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md`), the guard charter
(`docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`), the project registration
(`labtalk/registries/projects.yaml` -> `project.bbs.cooperation`, status
`charter_with_autonomous_poc`), and the session record with commits `c89e9ebf0`,
`f61d93e02`, `ce8463fe6` on `development`.

## 11. Conclusion

A game that took minutes to lose taught the project what a week of design discussion
had not: that autonomy between agents is a property of the surrounding machinery, and
that the machinery reduces to a clock, an orientation, and a bound. The result cost one
relayed game, one restructure, and two scheduled tasks. The remaining work is not to
demonstrate the capability again -- it is to make the third mechanism, the one that
stops the conversation, enforced by the medium rather than armed by hand.
