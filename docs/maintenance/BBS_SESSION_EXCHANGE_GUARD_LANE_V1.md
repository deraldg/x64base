---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260804-008
  recorded_at_utc: 2026-08-04T05:10:00Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: BBS autonomous cooperation -- session exchange-guard charter
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: f7c3b4407
  authorization:
    requested_by: maintainer
    scope: charter the missing per-session exchange guard (design only; no source)
  report:
    path: docs/maintenance/BBS_SESSION_EXCHANGE_GUARD_LANE_V1.md
    kind: lane_charter
---

# BBS Session Exchange-Guard -- lane charter (v1)

Status: **proposed / Phase-0 design**. Claim an AIF before any source. Source is
NO-GO until claimed AND reviewed: the enforcement site (`src/bbs/bbs_server.cpp`)
is core daemon code and adjoins the maintainer's protected set.

Relationships: AI Systems Integration SDLC (**AIF-086**); BBS agency legs
(**AIF-083**); `AGENCY_MODEL_V1.md`; the two-lane design
`DESIGN_bbs_pseudochat_two_lanes.md`. This is the missing primitive under the
"participant-agnostic cooperation medium" framing (AI-AI, AI-Human, Human-Human).

## Problem statement

For the BBS to carry an **autonomous** conversation -- two unattended AI members
taking turns with the human only initiating -- something must bound the exchange
so it cannot loop forever. The hangman probe (2026-08-04, Cowork vs Copilot over
the Pseudo-Chat relay) demonstrated the gap from the other side: it only ran
because a human relayed every turn, and there is no built-in stop that would end
an unattended AI-AI session at N exchanges. Humans self-limit; a paced AI-Human
chat self-limits; only AI-AI can run away. The guard is needed exactly when at
least one participant is an unattended AI.

## Prior art (checked before proposing -- AIF-085 "Already built?")

A runaway guard IS implemented in the tree, but it guards the wrong layer for
this use; and the BBS daemon guards the transport, not the conversation. Do NOT
build from scratch; reuse these idioms (AIF-037 Rule of Three).

- **DotScript loop clamp -- IMPLEMENTED, live, not deprecated**
  (`src/cli/cmd_loop.cpp`): `kDefaultMaxLoopIterations` (line 126) with a
  clamp-and-report path (lines 391-397: `ENDLOOP: iteration count N exceeds max
  M; clamping`). This is the reusable **clamp-with-message idiom**. It bounds
  *script loop execution*, not agent turns.
  - RECORDED FINDING (declared-vs-actual drift, AIF-079 flavor): the header
    comment (line 22) says "hard default max iterations: 1000" while the actual
    constant is **100,000,000**. Splittable as a one-line doc fix; noted here so
    it is not lost.
- **BBS daemon transport guards -- IMPLEMENTED** (`src/bbs/bbs_server.cpp`): a
  64 KB per-request cap (line 94), a **simplex cascade guard** (one connection at
  a time, line 96), and an **idle-connection drop timeout** (lines 350/357, "no
  client may wedge the gate"). These stop a wedged or flooding *connection*, not
  a long *conversation*. Reuse the idle-timeout as one terminal condition.
- **Scan/mine budgets -- pattern precedent**: `include/cli/scan.hpp` `max_steps`
  bounded `while`; `src/help/helpdata_source_miner.cpp` "runaway-scan guard" +
  `total_budget_exhausted(...)`.
- **VDISK CEIL -- cautionary precedent** (AIF-043/AIF-079 instance 3): a runaway
  RAM cap whose config surface exists but whose enforcement is ABSENT, so
  `on_full = fail` implies a guarantee that does not hold. Lesson: do NOT ship the
  cap as config without the enforcement path proven.
- **Two-lane split** (`DESIGN_bbs_pseudochat_two_lanes.md`, cited at
  `bbs_server.cpp:29-32`): BBS = durable attributed posts (SYSPOST/SYSTHREAD);
  CHAT = the Ollama-backed conversation lane (127.0.0.1:11434). The guard belongs
  on the CHAT/session lane, beside the existing connection guards.

Conclusion: no per-session **exchange-count** guard exists. That single primitive
is the whole of this lane.

## Proposed primitive (design)

Map the "session/match" onto the existing **`SYSTHREAD`** row rather than invent a
parallel object: a thread already groups posts, carries `STATE` (0 open, 1
answered, 2 closed) and `LASTPOST`. The guard is a **per-thread exchange counter
with a hard cap** that, when tripped, writes one attributed system post
(`SYSPOST.KIND = 4 system`) and transitions the thread to `STATE = 2 closed`, so
every subsequent reader (and every polling agent) sees the session is over.

Terminal conditions (any one ends the session):

1. **Completion** -- the task's own end (hangman solved / lost).
2. **Exchange cap** -- post count in the thread reaches the hard max (the new bit).
3. **Idle timeout** -- no new post within a window (reuse the daemon idle idiom).

Reuse: the clamp-with-message idiom from `cmd_loop.cpp` for (2); the idle timeout
from `bbs_server.cpp` for (3). New surface is minimal: a counted cap on
per-thread posts and the auto-close transition.

## Phase-0 decisions to settle (owner)

| # | Question | Options / note |
|---|---|---|
| A | What counts as one "exchange" | one post (simplest, maps to SYSPOST rows in the thread) vs one full round-trip (a post + its reply) |
| B | Default hard cap | proposed 64 posts/thread (hangman needs ~40 worst case); owner sets the number |
| C | Scope of the cap | per-thread (recommended, reuses SYSTHREAD) vs per-board vs per-member-per-day |
| D | Who the guard applies to | ALL sessions vs only sessions with >= 1 unattended-AI member (ties to SYSMEMBER.KIND + the connector model; humans self-limit) |
| E | Trip behavior | hard close (STATE=closed) vs pause-for-human (STATE=open, flagged, awaits a human resume) |
| F | Enforcement site | CHAT lane runtime (`bbs_server.cpp`) vs the match/session object vs both; must be a real enforced path, not config-only (the VDISK lesson) |
| G | Proof shape | a C++ smoke that drives a thread past the cap and asserts the system post + STATE=closed, no open-DBF required (mirror the trigger-hooks smoke) |

## Non-goals

- Not building the scheduled match yet -- that is step 2 and rides on this.
- Not touching `bbs_server.cpp` or any `bbs_schema.hpp` field until an AIF is
  claimed and the decisions are signed (core daemon; protected-adjacent).
- Not a rate-limiter or an auth control; this is a conversation-length bound only.

## Next steps

1. Claim an AIF for this lane (host-side; `session_coordinator.py claim-aif`).
2. Owner signs A-G above (Phase-0), same gate discipline as the Triggers lane.
3. THEN step 2 of the plan: the two scheduled Cowork agents (host + guesser) with
   the exchange cap enforced in the shared game-state file as the first proof of
   the primitive, before any daemon-side source lands.

## Motivating probe

`docs/ai-friendly/PSEUDO_CHAT_BOARD.md` -- the 2026-08-04 hangman run (Cowork vs
Copilot). Passed AI-Human (relay), would pass Human-Human, failed AI-AI (no
autonomy, no exchange guard). This lane is the "no exchange guard" half of that
result.
