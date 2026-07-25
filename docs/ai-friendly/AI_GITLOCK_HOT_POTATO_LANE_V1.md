# Git-Lock "Hot Potato" -- Commit-Coordination Lane (Design Note) V1

**Status:** design-intended -- not started. **Lane:** AIF-059 (continues run AIPR-20260725-001).
**Owning project:** `project.ai_friendly`. **Evidence class:** `design-intended`.

## Problem -- who has the git lock?

`development` is the dev-sync branch for `D:\code\ccode`, and more than one actor commits to it: the
maintainer plus AI agents (Grok, Cowork, Codex, and a future harnessed Ollama). Nothing coordinates
**who commits/pushes next**. Two sessions that both stage + commit + push race each other: clobbered
work, non-fast-forward push rejections, and the "just one more thing, left uncommitted" gap the
maintainer named. "Who has the git lock?" has no answer today.

## The metaphor

The commit/push right is a **hot potato**: exactly one holder at a time, passed explicitly, and never
held so long it goes cold. Whoever holds it may commit+push; everyone else waits or works read-only
until it is passed.

## Design -- advisory, mirroring the DBF lock philosophy

The engine already has cooperative record/file locking (`xbase::locks`: pid-stamped `.lock` sidecars,
stale-owner recovery). Reuse that **philosophy** for git -- do not invent a new one:

- **A single advisory holder marker** -- a `GITLOCK` record: `holder` (member.key + `host:pid:nonce`),
  `claimed_at`, `intent` (lane / what is being committed), `heartbeat`.
- **Home:** prefer a post on a dedicated **`board.gitlock`** (or `board.worklog`) over a `.gitlock`
  file -- the board is already identity-bound, durable, AUTH-gated, and the agent coordination surface
  (AIF-057). A `.gitlock` file is itself a sync object and can race; the board does not.
- **Protocol (simplex, advisory):**
  1. **CLAIM** -- before committing, an actor checks the marker. If unheld or **stale** (holder pid
     dead / heartbeat older than N minutes) it becomes the holder.
  2. **COMMIT+PUSH** -- the holder does its git work.
  3. **RELEASE** -- the holder passes the potato (posts RELEASE).
  4. **Stale recovery** -- like the FLOCK pid-liveness and the BBS cascade timeout: a holder whose
     heartbeat expired is force-released (logged), so a crashed or abandoned session cannot wedge the
     branch forever.
- **Advisory, not enforced.** git itself is not blocked (cannot be cleanly across machines); the lock
  is a cooperative convention the agents honor -- exactly like the DBF FLOCK, which protects writers
  that take it. The owner can always force-release / override.

## Access reality (why the holder differs by agent)

Agents do not have equal git access, and the lock must model that:

- **Direct-access agents (e.g. Codex)** have PC/git access -- they can `git commit`/`push` themselves,
  so they can *hold the potato* directly.
- **Script-handoff agents (e.g. Cowork/Claude today)** have no credentials on the box -- they hand the
  maintainer a reviewed commit script, so **the maintainer is the de-facto holder** for that agent's
  work. This is the current workflow until Cowork gets PC access like Codex.

The coordination need **grows** as more agents gain direct access: two direct committers on
`development` is exactly the race the lock prevents. Until then, the maintainer is the single
serializing point (which is safe but is also the "just one more thing, left uncommitted" bottleneck
the lock aims to make visible).

## Boundaries / non-goals

- Not a replacement for git's own concurrency (fetch / rebase / merge). It reduces *contention*; it
  does not do the merge.
- Coordinates cooperating agents + the maintainer, not adversaries; a rogue actor can ignore it.

## Ties (same pattern, three places)

- **DBF FLOCK** (`xbase::locks`) -- pid-stamped, stale-recovering cooperative lock.
- **BBS cascade guard** (idle timeout, AIF-057) -- do not let a stuck holder wedge a shared resource.
- **`board.worklog` / handoff** (AIF-057) -- the natural home + the same identity-bound surface.
- The maintainer's stated pain: finished-but-uncommitted work. A visible "who holds the potato / is
  anything mid-flight" makes the commit step **social and harder to drop**.

## Next

Ratify the marker home (`board.gitlock` vs `.gitlock`), the field set, the stale timeout, and whether
a thin `GIT LOCK CLAIM|RELEASE|STATUS` command wraps it. Design-intended; no code yet.
