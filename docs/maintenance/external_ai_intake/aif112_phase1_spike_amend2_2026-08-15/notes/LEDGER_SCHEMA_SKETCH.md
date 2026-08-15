# Ledger schema sketch (DBF-native, amended -- Handoff 2)

**Scribe note.** This file is GROK-004's sketch with the steward's Handoff 2
rulings applied. Two fields changed (attribution) plus one clarified note (id
allocation); everything else is unchanged. Authority: steward ruling sections 2
and 3. See the amendment MANIFEST, "Scribe-applied deltas."

**Constraint:** express this through x64base / DotTalk++ surfaces only.
Follow WORKSPACES and identity-catalog patterns. Prefer reuse of existing
lock/grant/reservation tables before creating new ones.

House convention: physical names <= 10 chars; 64-bit ids/epochs as N(20,0)
with 0 = unset; enums as small N codes; bools as L.

This is a sketch for the spike, not a frozen schema.

## INVITEM (7 chars) -- inventory items

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| ID | N(20) PK | stable id; max(id)+1 under catalog FLOCK |
| IKEY | C(64) | portable key |
| KIND | N(2) | 0 File, 1 Capsule, 2 Doc, 3 Sample, 4 Other |
| REF | C(200) | opaque; NOT assumed a filesystem path |
| TITLE | C(64) | short human label |
| MERGEABLE | L | Y = advisory OK; N = exclusive preferred |
| CREATEDBY | C(32) | **string stamp** via current_member(), `member#<id>/kind<n>` |
| CREATEDAT | N(20) | epoch |
| STATUS | N(2) | |
| VFROM | N(20) | bi-temporal, 0 = unset |
| VTHRU | N(20) | |
| ROWVER | N(20) | optimistic concurrency |

## INVCHKOUT (9 chars) -- append-only check-outs

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| ID | N(20) PK | max(id)+1 under catalog FLOCK |
| ITEMID | N(20) | FK INVITEM |
| MEMBERID | C(32) | **string stamp** via current_member(), `member#<id>/kind<n>` |
| MODE | N(2) | 0 Exclusive, 1 Advisory |
| STATE | N(2) | 0 Held, 1 Released, 2 Broken, 3 Expired |
| ACQAT | N(20) | acquired epoch |
| RELAT | N(20) | 0 while held |
| EXPAT | N(20) | lease expiry; 0 = none; SYSGRANT-style mitigation |
| RUNID | C(32) | AIPR-YYYYMMDD-NNN |
| NOTE | C(120) | optional |
| SUPERBY | N(20) | 0 = current |
| ROWVER | N(20) | |

Current state = highest ACQAT per ITEMID where STATE=0
(same pattern as SYSPOST / SYSRULING).

## Attribution (steward ruling, Handoff 2 section 2)

WORKSPACES uses a string stamp, not a foreign key:

```
static std::string author_stamp() {
    dottalk::identity::current_member(id, kind);
    return "member#" + std::to_string(id) + "/kind" + std::to_string(kind);
}
```

Phase-1 matches that proven precedent. Normalizing to an N(20) FK against
SYSMEMBER is a separate design choice and must not be assumed inside the spike.
The owner may later rule to normalize.

## ID allocation (steward ruling, Handoff 2 section 3)

max(id)+1 under the catalog FLOCK, same as WORKSPACES. Self-healing after a
manual edit, and forward-compatible with the x64 header slot autoq_next when
that engine lane lands. No new id mechanism.

## INVEVENT

Omitted per P3. INVCHKOUT append-history carries the event stream.

## Permissions (reuse SYSPERM)

Gate via SYSPERM with deny-precedence through agent_permitted(perm):
  inv.register, inv.checkout, inv.release, inv.break

inv.break is maintainer-only. Model: cmd_net.cpp, which gates
host.network.egress as Critical / requires_approval, owner exempt, AI denied.

## Design notes

1. Reuse first. Inspect SYSGRANT, WORKSPACES, session_coordinator lock
   surfaces before creating INVITEM/INVCHKOUT.
2. Capsule REF must accept a workspace/capsule id without path assumption.
3. Exclusive semantics: under the catalog FLOCK, scan for a Held row on the
   ITEMID and refuse a second exclusive acquire. The refusal is enforced
   because check and insert share one lock scope -- not by a SELECT-then-decide
   outside the lock.
4. Private runtime state. Not committed to Git.
5. The ledger takes a transient RAII FLOCK per append and releases it in the
   same scope (WsLock / bbs_store idiom). It never holds a lock across
   operations, so the I5 defect does not apply.
6. EXPAT lease is the recovery path. It must work without any force path:
   force_unlock_table and force_unlock_record exist in the engine but are
   called by nothing and are unreachable from any command.

## Open questions the spike must answer

- Does check-and-append under the FLOCK correctly refuse a second exclusive
  acquire on a held ITEMID?
- Is EXPAT lease reclaim reachable with no force path?
- Exact create path through the runtime for INVITEM / INVCHKOUT.
- Does REF carry a capsule id with nothing downstream assuming a path?
