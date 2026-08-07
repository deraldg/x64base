# dottalkpp.com site -- PICK-UP HERE (AIF-095)

> **This is a claimed, chartered, pick-up-ready lane -- NOT abandoned.** Registered
> with a claim, this intake row, and this document precisely so it cannot vanish the
> way AIF-070 did (reserved, never given a queue row, then independently redesigned by
> a later session that could not see it). Closeout finished by
> `member.ai.claude.cowork` (run `COWORK-20260807-005`) at the owner's request, from a
> prior session that was erroring; the substantive findings below are that session's.

**Lane:** AIF-095 (`dottalkpp-site`) - **Owner:** member.derald -
**Steward:** member.ai.claude.cowork -
**Status:** `pick-up-ready -- SSL remediation complete; matrix scope ruling owed before content work`.

## One-line state

The SSL remediation that blocked the dottalkpp.com site work is **done** (AutoSSL
fired). Content work is now blocked only on an owner ruling: the **matrix scope**
decision (widen / separate / retire dottalkpp.com) and, upstream of it, whether
dottalkpp.com remains a site at all.

## Where things actually stand (so you don't redo done work)

- **AutoSSL fired.** The earlier "AutoSSL trigger pending" condition is resolved. Four
  documents still say it is pending and must be corrected -- and while there, **each
  mention should name its domain**, because "AutoSSL" currently denotes two lanes in
  opposite states (x64base.com done vs the dottalkpp.com names). Un-named, it is a
  quiet collision waiting to happen.
- **Waiting on machines (not on a person):** cPanel AutoSSL runs overnight; then apply
  **Force HTTPS Redirect** on the four Apache names.
- **Optional diagnostics (non-blocking):** `fsutil sparse queryflag` on an LMDB map
  file; `git-sizer` on x64base-site's ~290 MB `.git`.

## What is left, by slice

- **Slice A -- session record + index.** Land the session record into
  `docs/maintenance/` and index it in the dashboard. Cheapest moment to also land this
  pick-up doc and the intake row (the step AIF-070 skipped). Needs `claim-aif` -- DONE
  (AIF-095).
- **Slice B -- probe into `tools/`.** The measurement probe belongs under `tools/`.
- **Slice C -- BLOCKED on the matrix scope ruling** (see rulings below). No content
  work proceeds until the ruling lands.

## Rulings only the owner can make (do not settle these as steward)

1. **Matrix scope:** widen the website matrix to cover dottalkpp.com, keep it a
   separate matrix, or retire dottalkpp.com from the matrix.
2. **Prior question:** whether to keep dottalkpp.com as a site at all.

Slice C and all content work are held until #1 lands; #2 may moot the lane entirely.

## What makes this lane genuinely resumable (the AIF-070 lesson)

Three things, all now present:
1. **Claim file** -- `coordination/aif/AIF-095.claim` (reserves the number).
2. **Intake row** -- the load-bearing one; without it the lane reads ABANDONED from
   HEAD no matter what prose calls it. Added this pass to
   `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.
3. **This pick-up document** -- names where to resume and the blocker, so the next
   session knows *why* it stopped rather than guessing.

Precedent for the status: AIF-072 (`PHASE7_MANUAL_WEB_ASCENT_PICKUP_V1.md`) -- retired
as the controlling target, still claimed, explicitly not abandoned. Same shape.
