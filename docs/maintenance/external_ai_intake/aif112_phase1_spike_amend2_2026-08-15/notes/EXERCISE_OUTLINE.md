# Exercise outline (run against live x64base) -- Handoff 2 order

**Rule:** every step through the product. No side-channel sqlite3.
CLI for LOCK/UNLOCK if touched. pydottalk for record-level assertions only.
Carrier: DBF catalogs (D1 steward-accepted). SQLite = oracle only.

## Setup

1. Start live x64base / DotTalk++ (local development tree).
2. Confirm data root is the private runtime location (never staged to GitHub).
3. Record instance identity / version / tip in the evidence note.

## Steps

### 1. Reuse audit

Inspect SYSGRANT, WORKSPACES, session_coordinator status/lock verbs.
Record what already carries or mirrors check-out semantics, including
"nothing suitable to extend."

### 2. Create INVITEM + INVCHKOUT through the runtime

DBF under data/metadata/inventory/ (or local convention).
House names: INVITEM (7), INVCHKOUT (9).
ID allocation: max(id)+1 under catalog FLOCK.
Attribution: string stamp via current_member() (match WORKSPACES), unless
owner has already ruled for N(20) FK.
Confirm tables visible via the runtime.

### 3. Register inventory

At least three INVITEM rows:
  - one FILE
  - one SAMPLE or DOC
  - one CAPSULE-shaped REF (opaque, not assumed a path)
Query and show them.

### 4. Exclusive proof

Under the FLOCK: scan for any Held row on this ITEMID; refuse if exclusive
requested and one exists; otherwise append.
Second exclusive acquire on a held ITEMID must be REFUSED because
check-and-insert share one lock scope.
Record that the refusal is under-FLOCK, not SELECT-then-decide outside it.
List active check-outs (highest ACQAT per ITEMID where STATE=Held).

### 5. Release / re-acquire

Release (append Released / supersede Held).
Confirm no active exclusive holder.
Re-acquire must succeed.

### 6. EXPAT lease reclaim

Acquire with short EXPAT.
Let it lapse.
Reclaim without any force path (force_unlock_* is confirmed unreachable;
the ledger must not need one).
Record reachable / not reachable.

### 7. SQLite oracle

Mirror final INVCHKOUT state in SQLite; confirm agreement.
SQLite remains verification instrument only.

### 8. Publication hygiene

Nothing written where it promotes to publication.

### Optional -- I5 probe (not a gate)

If convenient: acquire via LOCK command, close area without exiting process,
inspect surviving artifact, attempt conflicting acquire from other pid.
Route result to the engine lane. Do not block AIF-112 on it.

## Deliverable

Fill the evidence template. EXPAT reclaim result is mandatory.
I5 result is optional.
