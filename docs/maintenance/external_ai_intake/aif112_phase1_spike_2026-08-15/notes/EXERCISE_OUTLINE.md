# Exercise outline (run against live x64base)

**Rule:** every step goes through the product. No side-channel sqlite3.

Use pydottalk, DotTalk++ CLI, or any existing runtime API that can:

- open / select a work area
- run SQLITE / DDL / DML through the engine
- list tables / query rows

Exact command names may differ; adapt to the live surface while keeping the dogfood rule.

## Setup

1. Start a live x64base / DotTalk++ instance (local development tree).
2. Confirm SQLITE (or equivalent) is reachable from that instance.
3. Choose a private data location that will never be staged to GitHub.
4. Record the instance identity / version / tip in the evidence note.

## Steps

### A. Schema

1. Inspect existing tables for anything already usable as a lock / reservation / grant ledger. Record findings.
2. If nothing suitable exists, create INV_ITEM, INV_CHECKOUT (and INV_EVENT if needed) through the runtime.
3. Confirm the tables are visible via the runtime (work area / table list / query).

### B. Register inventory

1. Insert at least three INV_ITEM rows:
   - one FILE (e.g. a docs path)
   - one SAMPLE or DOC
   - one CAPSULE-shaped REF (synthetic id is fine for the spike)
2. Query and show the registered items.

### C. Exclusive check-out

1. ACQUIRE exclusive on item 1 as member spike.a.
2. Confirm STATE=HELD, MODE=E.
3. Attempt ACQUIRE exclusive on the same item as member spike.b (or second session). Must fail.
4. List current check-outs; confirm only the held lock appears as active.

### D. Release and re-acquire

1. RELEASE the lock held by spike.a.
2. Confirm STATE=RELEASED (or equivalent) and no active exclusive holder.
3. ACQUIRE exclusive again (same or other member). Must succeed.

### E. Advisory (light touch)

1. On a MERGEABLE=Y item, ACQUIRE advisory as spike.a.
2. Optionally ACQUIRE advisory as spike.b (advisory may allow concurrent holders -- record actual behavior).
3. Note whether the runtime surface made exclusive vs advisory distinction natural or awkward.

### F. Capsule reference

1. Confirm the CAPSULE item can be locked and listed without treating REF as a filesystem path.
2. Record any friction.

### G. Cleanup / leave private

1. Leave tables in the private data area (or drop them if the spike is disposable).
2. Confirm nothing was added under paths that promote to GitHub / public site.

## Deliverable from the exercise

Fill notes/EVIDENCE_TEMPLATE.md (copy into the tree or return via package) with commands used, observed results, and any gap that would justify revisiting Fossil.
