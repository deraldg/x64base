# Recursion markers -- tracking step-back movement in the SDLC/PDLC

**Status:** doctrine (review-needed). Owner: member.derald. Steward: member.ai.claude.cowork.
Date 2026-08-08. Coined this session. **No AIF** -- this is doctrine; it graduates to a mechanism
(markers wired into the PDLC tooling) only if the pattern proves worth automating, and that
promotion is itself governed by the **aside rule** (`AI_GLOSSARY_V1.md`).

## The idea

Development is not linear. While working a task we **step back** to fix or check a side issue,
then return. That is recursion: stepping back is a **push** (a new frame on top of the current
one), and **"recurse back"** is the **pop** (return to the frame underneath). An **aside** is one
such frame.

The problem with an un-marked recursion is the same as an un-popped stack frame: it **leaks**. You
step back, get absorbed, and never return -- the original task is left dangling and nobody notices
because the departure was never recorded. A **recursion marker** is the breadcrumb that makes the
push and the pop visible, so the movement pattern is trackable and un-returned steps surface
instead of vanishing.

## What a recursion marker is (proposed, lightweight)

A short, ASCII, greppable line dropped at each transition. Proposed forms:

- **At the origin** (the frame you leave): `RECURSED OUT -> <target> @ <point> : <reason>` and,
  when you come back, `RECURSED BACK <- <target> : <resolved|parked>`.
- **At the destination** (the frame you enter): `RECURSED IN <- <origin> @ <point>`.

Placed in the SDLC/PDLC artifacts themselves -- the lane charter, the milestone note, or the
ticket -- not in a side log, so they travel with the work and a clone sees them. The pair
(`OUT`/`IN`) makes the edge directed; the closing `BACK` marks the pop. An `OUT` with no matching
`BACK` is a leaked recursion -- a parked item that was never returned to.

## Why: movement patterns

With markers in place you can measure the shape of the work, not just its content:

- **Depth** -- how many frames deep did a task go before returning (task -> aside -> deeper aside).
- **Fan-out** -- how many side-steps a single lane spawned.
- **Leak rate** -- `OUT` markers with no `BACK`: work that was stepped away from and abandoned.
- **Return latency** -- how long a parked frame sat before it was popped.

This is the workflow/temporal complement to the **recall graph**: the recall graph holds *semantic*
edges (this memory relates to that one); recursion markers hold *temporal/movement* edges (from
here I stepped back to there, and returned -- or did not). Same graph instinct, different axis.

## Relationship to existing vocabulary

- **aside** -- a single recursion frame taken to correct/check a side issue. The aside rule (no
  PDLC unless promoted) governs whether that frame graduates to standing work. A recursion marker
  is how the aside is made visible even when it does NOT get a PDLC.
- **recurse back** -- the pop; returning to the frame underneath.
- **handoff / frontal memory** -- a leaked recursion (an `OUT` with no `BACK`) is exactly the stale
  state the consolidation thesis warns about: work stepped away from without being written back.
  Markers turn that leak into something the exit-consolidation can catch.

## Worked example -- this session's tail (documented in real time)

The recursion that prompted this doc:

```
frame 0  Grok Lane 1 coworker wrap-up (package reviewed, corrections parked, close-out)
  RECURSED OUT -> datarun check @ close-out : owner ran ./datarun to verify a suspected CNX/x64 issue
  frame 1  ./datarun regression + manual CNX-on-x64 test (SET INDEX TO test64.cnx refused)
    RECURSED OUT -> TICKET_CNX_ON_X64_WARN_NOT_REFUSE_AND_WORKSPACE_OPEN_INDEX_SOURCE_V1 @ the refusal
    frame 2  scope the stale-policy fix + WORKSPACE OPEN conveniences (ticket authored, parked)
    RECURSED BACK <- ticket : parked (AIF unclaimed, owner will recurse back)
  RECURSED BACK <- datarun check : resolved (engine green; policy bug ticketed)
  RECURSED OUT -> this doc @ close-out : owner asked to document the recursion + propose markers
frame 0 still open : Grok corrections paste-back still pending send
```

That last line is the point of the whole exercise: without the marker, "send Grok the corrections"
is easy to lose under two levels of step-back. With it, the open frame-0 obligation stays visible.

## Registration

Doctrine only. If markers earn automation (a linter that pairs `OUT`/`BACK` and reports leaks, or a
PDLC field), claim an AIF then -- promotion follows the aside rule. Homes: this doc; glossary
entries `recursion` and `recursion marker` point here. ASCII only, no em-dashes.
