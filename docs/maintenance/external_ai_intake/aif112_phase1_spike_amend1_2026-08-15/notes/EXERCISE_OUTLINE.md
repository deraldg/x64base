# Exercise outline (run against live x64base) -- amended

**Rule:** every step goes through the product. No side-channel sqlite3.
CLI is required for LOCK/UNLOCK. pydottalk may be used for record-level
assertions only.

## Setup

1. Start a live x64base / DotTalk++ instance (local development tree).
2. Confirm LOCK, UNLOCK, SET EXCLUSIVE, SET MULTILOCKS are reachable
   (HELP / CMDHELP).
3. Choose a private data location that will never be staged to GitHub.
4. Record instance identity / version / tip in the evidence note.

## Steps

### 0. Discover

HELP / CMDHELP on LOCK, UNLOCK, SET EXCLUSIVE, SET MULTILOCKS.
Record the supported surface.

### 1. Reuse audit

Inspect SYSGRANT, WORKSPACES, and session_coordinator status/lock verbs.
Record what already exists that can carry or mirror check-out semantics.

### 2. THE PROBE (before building anything) -- I5

This step outranks the rest if it fails.

1. In CLI session A: acquire a lock (engine LOCK or equivalent).
2. Close the area normally WITHOUT exiting the process.
3. Look for a surviving lock artifact.
4. From dottalk_bbsd (different pid, same data root) attempt a conflicting
   acquire.
5. Confirm whether FORCE UNLOCK is the only recovery.

Record: I5 reproduces / does not reproduce.
If it reproduces, that is the Phase-1 headline.

### 3. Schema

If nothing suitable exists to extend, create INVITEM + INVCHKOUT through
the runtime (DBF under data/metadata/inventory/ or the local convention).
Confirm tables are visible via the runtime.

### 4. Register inventory

Insert at least three INVITEM rows:
  - one FILE
  - one SAMPLE or DOC
  - one CAPSULE-shaped REF (synthetic id is fine)
Query and show them.

### 5. Exclusive check-out proof

1. ACQUIRE exclusive on item 1 as member spike.a.
2. Confirm STATE=Held, MODE=Exclusive.
3. Second exclusive acquire as spike.b (or second session) must FAIL.
4. Record HOW it fails -- engine-enforced refusal is stronger than
   SELECT-then-decide.
5. List active check-outs.

### 6. Release and re-acquire

1. RELEASE the lock held by spike.a.
2. Confirm no active exclusive holder.
3. Re-acquire must succeed.

### 7. Stale recovery (EXPAT lease)

1. Acquire with a short EXPAT lease.
2. Let it lapse.
3. Reclaim without FORCE UNLOCK.
4. Record reachable / not reachable.

### 8. Advisory (light touch)

On a MERGEABLE item, acquire advisory; note concurrent behavior.

### 9. Capsule reference

Confirm CAPSULE item locks and lists without treating REF as a path.

### 10. Oracle

Mirror final INVCHKOUT state in SQLite and confirm agreement
(SQLite remains verification instrument only).

### 11. Hygiene

Confirm nothing was written where it promotes to publication.

## Deliverable

Fill the evidence template. I5 probe result and EXPAT reclaim result are
mandatory fields.
