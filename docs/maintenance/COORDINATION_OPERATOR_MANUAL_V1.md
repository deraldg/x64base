# Session Coordination -- Operator Manual V1

Status: proposal (review-needed), authored 2026-08-07, lane AIF-096.
Owner `member.derald`; steward `member.ai.claude.cowork`. ASCII (`--`, `->`).

This is the "how do I use it" manual for concurrent-session coordination. For internals,
the design model, and how to extend it, see `COORDINATION_DEVELOPER_MANUAL_V1.md`.

Tool: `python tools/coordination/session_coordinator.py <command>` (run from
`D:\code\ccode`; stdlib only, no build needed). Add `--root <path>` to point at another
tree; it defaults to the current directory.

## The one thing to understand first

A chat cannot remember itself; the project does. Every identity fact you rely on -- who
you are, what you claimed, who messaged you -- lives in files under `coordination/`, and
your first job each session is to read them. That is what `wake` does.

## Session lifecycle (the happy path)

1. **Wake** -- your first move, before any work:

       python tools/coordination/session_coordinator.py wake \
         --member member.you --run COWORK-20260807-007 --parent COWORK-20260807-005

   It prints who you are from the record:

       you are COWORK-20260807-007  (member member.you)
         born:   2026-08-07T22:40:00Z
         parent: COWORK-20260807-005
         holds:  (no claims)
         inbox:  0 unread quip(s)

   `--parent` is the run you were continued from; omit it if you are a fresh start.

2. **Claim a lane** before you touch its work (grep is not an allocator):

       python ... claim-aif --member member.you --run COWORK-20260807-007 --lane my-lane

   It allocates the next free AIF number atomically and writes a durable claim file. Then
   add an intake row so the lane is visible from HEAD -- a claim without a row reads as
   abandoned.

3. **Work.** Each lane you claim becomes one "aside" in your session's chain.

4. **Check out** when done, so you are not left showing as live:

       python ... checkout --run COWORK-20260807-007

   If it cannot delete your presence file (some mounts refuse), it TELLS you and marks the
   record closed rather than lying that it removed it.

## Talking to other sessions -- the channel ladder

Pick the rung by how far the message must reach and how long it must survive.

| Want to | Use | Reaches | Survives |
| --- | --- | --- | --- |
| nudge a session that is live right now | `quip send` | checked-in runs | no (ephemeral) |
| leave a note for a session that is NOT here | pseudo-chat board | any tree-reader, later | yes (tracked) |
| own a lane number | `claim-aif` | everyone | yes (tracked) |
| hand off unfinished work | claim + intake row + pickup doc | everyone, later | yes (tracked) |

Quip examples:

    # direct, to one run
    python ... quip send --from COWORK-...-007 --to COWORK-...-001 --msg "manifest held"
    # broadcast to every other live run (refuses if none are live)
    python ... quip send --from COWORK-...-007 --to all --msg "checked in on VFP"
    # read yours; --ack deletes what it prints
    python ... quip read --run COWORK-...-007 --ack

If you quip a run that is not checked in, it still delivers but WARNS you: the note sits
in a local, gitignored inbox and will not reach a fresh clone. For an absent partner, use
the pseudo-chat board instead (`docs/ai-friendly/PSEUDO_CHAT_BOARD.md`).

## Seeing the state

- `python ... status` -- live sessions (stale ones flagged), held locks, claimed numbers,
  unread quips.
- `labtalk/ai_portal/TIER0_STATE.md` -- the generated, can't-drift snapshot. Its
  "Sessions, lineage, asides" section shows each run's parentage and its ordered claim
  chain. Read it; do not restate it.

## Contested shared file

    python ... lock docs/some/shared.md --run COWORK-...-007      # advisory; check first
    python ... unlock docs/some/shared.md --run COWORK-...-007

Locks are cooperative -- they warn, they do not enforce. Check before you edit a hot file.

## Rules that keep you a good neighbor

- Never `git add -A` / `git add .` -- name exact paths; the tree holds other sessions' work.
- ASCII only in what you write here (`--`, `->`); `&&` is the DotTalk++ comment marker.
- In a mounted sandbox: read-only git only (`git --no-optional-locks status`); hand every
  mutating git to the maintainer.
- A claim with no intake row is invisible from HEAD. Register as you claim, not later.

## Troubleshooting

- **"no other checked-in sessions to quip"** -- you broadcast with `--to all` but nobody
  else is live. Use the pseudo-chat board.
- **`status` shows stale sessions** -- old runs that never checked out. Expected; they are
  flagged `[stale, reapable]` and can be reaped by the maintainer.
- **`quip read --ack` says "acked 0 of N"** -- the mount refused to delete; the notes are
  still there. Not a lie, a real condition; retry on a tree where unlink works.
- **You do not know your own run/parent after a break** -- read `TIER0_STATE.md` (survives
  checkout) or your `coordination/lineage/<run>.yaml`; that is exactly what they are for.
