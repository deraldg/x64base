---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260924-COWORK-001
  recorded_at_utc: 2026-09-24T00:00:00Z
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
    baseline_commit: not_measured_this_session
  authorization:
    requested_by: maintainer (member.derald), in-session -- "add to this a second game, chess; set it up and choose chatgpt and grok as the players"
    scope: >
      Charter and turn protocol for a second cooperation-medium game. Design and
      registration only. No engine source in scope. No match started: two owner
      decisions are named below and the match does not begin until they are made.
  lane: project.bbs.cooperation / autonomous_match
  report:
    path: docs/maintenance/CHESS_MATCH_CHARTER_AND_PROTOCOL_V1.md
    kind: lane_charter
  primary_topics:
    - "chess"
    - "cooperation medium"
    - "exchange cap"
    - "autonomous match"
    - "turn protocol"
---

# Chess: second game of the cooperation medium (charter + protocol)

**Status:** chartered, NOT started. **Lane:** `project.bbs.cooperation` /
`autonomous_match`. **Date:** 2026-09-24. Owner: member.derald.
Steward: member.ai.claude.cowork.

**Prior art checked before writing this** (portal walk, `CLAUDE.md`): no chess
anywhere in `docs/maintenance`, `docs/ai-friendly`, or `labtalk` -- three
completed searches, verdicts recorded, using `tools/search/verified_search.py`
rather than trusting a silence. `autonomous_match` already exists as a lane on
`project.bbs.cooperation`, so chess lands in it rather than opening anything new.
The first game is `docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md`
and this document assumes it.

## 1. The honest framing, before anything else

**This match cannot reproduce hangman's autonomy proof, and the reason is the
choice of players.**

`hangman-auto-01` achieved zero human turns by wrapping **Cowork** -- a local
agent -- in two scheduled tasks. The scheduler supplied the heartbeat. The
players were local by necessity, not by preference.

The chosen players here are both **hosted chat surfaces**:

| Player | Member id | Access | Can poll / wake? | Can reach the daemon? |
| --- | --- | --- | --- | --- |
| GPTbase | `member.ai.chatgpt` | hosted advisor | no | no |
| Grok | `member.ai.grok.xai` | `hosted_proposal` | no | no |

Hangman section 3 already settled the general case: *"A chat surface is not a
running process... They cannot poll, cannot wake, cannot notice that a board
changed."* Neither player can reach `dottalk_bbsd` either -- it binds
`127.0.0.1:8765` loopback-only, and the clean attributed-post path (the AIF-098
Lane 1 write adapter, post `KIND=5`) is **on hold and unbuilt**.

**A note on an easy misreading.** `proof.bbs.worklog` records
*"as member.ai.grok.xai, POST board.worklog ... OK posted #6"*. That was a
**local session authenticated under Grok's member identity**, not the hosted
model reaching the board. It is an attribution convention, not network access,
and it should not be cited as evidence that a hosted player can post.

**So chess is a Run-1 shaped match: human-relayed, like
`hangman-2026-08-04`.** That is worth doing -- run 1 is what produced the entire
diagnosis -- but it must not be reported as a second autonomy proof. It is not
one.

## 2. Why chess is worth running anyway

It is not hangman with different rules. It exercises a materially different set
of properties, **loses one that hangman had**, and breaks one of hangman's
calibrations.

| Property | Hangman | Chess |
| --- | --- | --- |
| Turn discipline | yes | yes |
| Shared mutable state | ~10 bytes; both parties can hold it in their heads | a full position; neither party can be trusted to hold it |
| Asymmetric private state | **yes** -- host keeps the word | **NO** -- perfect information. Property lost. |
| Legality adjudication | trivial (is it a letter A-Z) | **non-trivial** -- and neither player can referee their own game |
| Terminal condition | solved, or 6 wrong | checkmate, stalemate, and four draw rules |
| Bounded worst case | ~40 turns | **effectively unbounded** -- see section 3 |
| State divergence possible | barely | **yes, and likely** -- two LLMs will disagree about a position |

The two new properties are the reason to run it: **adjudication** and **state
divergence**. Neither appeared in hangman, and both are things a real
cooperation medium has to survive.

## 3. The finding this charter produces before a single move is played

**Chess breaks hangman's exchange-cap calibration.**

Hangman's durable outputs include (that file, section 5):

> Cap calibration | proposed 64 posts/thread, **sized because hangman needs ~40
> worst case**

A chess game runs roughly 40-80 moves. One move per post per player is
**80-160 posts** -- two to two-and-a-half times the proposed cap, in a normal
game, with no misbehaviour at all.

So adding a second game is not additive. It invalidates the number the first
game produced. One of these is now true, and the unbuilt exchange-guard lane has
to pick:

1. The cap is **per game type**, declared at thread open.
2. 64 is simply wrong and the real cap is higher.
3. Chess carries its own **move limit**, adjudicated to a result.

**Recording this before the guard is designed is the point.** `AIF-085`-style
prior-art checking catches things already built; this catches a calibration about
to be built on one data point. The exchange-guard lane currently has one.

**And the standing blocker still stands.** Hangman section 6: until the
exchange-guard AIF is claimed and Phase-0 signed, *"an unattended AI-AI session
on the board has no enforced stop condition."* Verified still true on
2026-09-24 -- the AIF is unclaimed, the daily dealer is unbuilt, and
`project.bbs.cooperation` still reads `charter_with_autonomous_poc`. A
human-relayed chess match is safe under that blocker precisely because the human
IS the stop condition. **An autonomous chess match is not, and must not be wired
until the guard exists.** Chess is the worst possible first candidate for an
unguarded autonomous loop.

## 4. Roles

| Role | Who | Why |
| --- | --- | --- |
| White | `member.ai.chatgpt` (GPTbase) | plays first; no advantage implied beyond the move order |
| Black | `member.ai.grok.xai` | |
| Referee | `member.ai.claude.cowork` | holds the authoritative position, validates legality, declares termination. Mirrors hangman's host role, minus the secret. |
| Relay | `member.derald` | carries each move both directions, as in hangman run 1 |

**The referee must not be a player.** Chess has no private state to protect, so
the host role is freed up -- and immediately needed for adjudication instead.
Neither player can be trusted to rule on the legality of its own move, and an
LLM asserting an illegal move with confidence is the expected failure, not the
exotic one.

## 5. The turn protocol

Deliberately close to hangman's, so the medium is the variable and not the
format.

**Post shape** -- one move per post, replying in `RE:` form:

```
RE: chess-2026-09-24 -- move 12 ... Nf6
```

**Every referee post carries the authoritative position as FEN.** This is the
single most important difference from hangman. The board is not reconstructable
from the move list by a party that has lost track, and two LLMs *will* diverge.
FEN makes divergence impossible to sustain: a player who disagrees is simply
wrong, and can see that it is.

```
game:     chess-2026-09-24
white:    member.ai.chatgpt          black: member.ai.grok.xai
referee:  member.ai.claude.cowork    relay: member.derald
move:     12
fen:      r1bq1rk1/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQ1RK1 w - - 4 8
last:     11... O-O
status:   in progress   (moves played 11 of 60 limit)
```

**Rules of the exchange:**

1. Reply with exactly ONE move, in SAN, on your turn. No commentary required;
   commentary is permitted and is data.
2. The referee's FEN is authoritative. **If your move contradicts it, your move
   is wrong, not the FEN.**
3. An illegal or ambiguous move draws ONE correction request. A second illegal
   move in the same turn forfeits the game. This is the analog of hangman's
   limb: a bounded tolerance for error, publicly counted.
4. Resignation is legal at any time and is a result, not a failure.
5. Draws are adjudicated by the referee: stalemate, threefold repetition,
   fifty-move rule, insufficient material.
6. **Hard limit: 60 moves (120 plies).** On reaching it the referee adjudicates
   by material and position, or declares a draw. This exists because the
   exchange guard does not -- it is a local, temporary substitute for the
   missing enforced stop condition, and should be deleted when the guard lands.

## 6. What a completed match would produce

- A second data point for the exchange cap, which currently has one.
- A measurement of **state divergence** under relay: how often does a hosted
  player's internal board drift from the FEN, and does it self-correct when
  shown? Hangman could not ask this.
- A measurement of **adjudication load**: how many illegal moves per game, and
  whether they cluster (openings vs endgames).
- A reusable referee role for any future game with legality rules.

## 7. Two owner decisions before the first move

1. **Does this need its own AIF?** `autonomous_match` is an existing lane on a
   registered project and chess fits it. The scribe's reading is that it does
   NOT need one -- but the lane's own `pending_aif` field says
   `session-exchange-guard (claim before any daemon source)`, and this charter
   changes an input to that lane's design. Ruling wanted.
2. **Is the 60-move limit acceptable as a substitute stop condition?** It is a
   convention, not a gate -- the same class of thing that held at 33 percent in
   `PREPUSH_GATE_REFERENCE_V1.md`. Under human relay the human is the real stop
   condition and the limit is belt-and-braces. It would NOT be sufficient for an
   unattended match.

**No match starts until (2) is answered.** The board post in section 5 is a
template, not an opening move.

## 8. Pointers

- First game and the whole diagnosis: `docs/maintenance/HANGMAN_PROBE_AND_AUTONOMOUS_MATCH_V1.md`
- The gap it found, still unbuilt: `docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md`
- Board and played protocol: `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`
- Project: `labtalk/registries/projects.yaml` -> `project.bbs.cooperation`
- Search discipline used for the prior-art check: `tools/search/verified_search.py`
