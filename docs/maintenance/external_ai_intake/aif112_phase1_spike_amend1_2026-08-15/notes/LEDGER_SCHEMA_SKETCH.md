# Ledger schema sketch (DBF-native, amended)

**Constraint:** express this through x64base / DotTalk++ surfaces only.
Follow WORKSPACES and identity-catalog patterns. Prefer reuse of existing
lock/grant/reservation tables before creating new ones.

House convention: physical names <= 10 chars; 64-bit ids/epochs as N(20,0)
with 0 = unset; enums as small N codes; bools as L.

This is a sketch for the spike, not a frozen schema.

## INVITEM (7 chars) -- inventory items

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| ID | N(20) PK | stable id |
| IKEY | C(64) | portable key |
| KIND | N(2) | 0 File, 1 Capsule, 2 Doc, 3 Sample, 4 Other |
| REF | C(200) | opaque; NOT assumed a filesystem path |
| TITLE | C(64) | short human label |
| MERGEABLE | L | Y = advisory OK; N = exclusive preferred |
| CREATEDBY | N(20) | FK SYSMEMBER via current_member() |
| CREATEDAT | N(20) | epoch |
| STATUS | N(2) | |
| VFROM | N(20) | bi-temporal, 0 = unset |
| VTHRU | N(20) | |
| ROWVER | N(20) | optimistic concurrency |

## INVCHKOUT (9 chars) -- append-only check-outs

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| ID | N(20) PK | max+1 under catalog FLOCK |
| ITEMID | N(20) | FK INVITEM |
| MEMBERID | N(20) | FK SYSMEMBER |
| MODE | N(2) | 0 Exclusive, 1 Advisory |
| STATE | N(2) | 0 Held, 1 Released, 2 Broken, 3 Expired |
| ACQAT | N(20) | acquired epoch |
| RELAT | N(20) | 0 while held |
| EXPAT | N(20) | lease expiry; 0 = none; SYSGRANT-style mitigation for I5 |
| RUNID | C(32) | AIPR-YYYYMMDD-NNN |
| NOTE | C(120) | optional |
| SUPERBY | N(20) | 0 = current |
| ROWVER | N(20) | |

Current state = highest ACQAT per ITEMID where STATE=0
(same pattern as SYSPOST / SYSRULING).

## INVEVENT

Omitted per P3. INVCHKOUT append-history carries the event stream.

## Permissions (reuse SYSPERM)

Gate via SYSPERM with deny-precedence through agent_permitted(perm):
  inv.register, inv.checkout, inv.release, inv.break

inv.break is maintainer-only (mirrors FORCE UNLOCK).

## Design notes

1. Reuse first. Inspect SYSGRANT, WORKSPACES, session_coordinator lock
   surfaces before creating INVITEM/INVCHKOUT.
2. Capsule REF must accept a workspace/capsule id without path assumption.
3. Exclusive semantics: while STATE=0 and MODE=0 for an ITEMID, a second
   exclusive acquire must fail. Prefer engine-enforced refusal over
   SELECT-then-decide convention.
4. Private runtime state. Not committed to Git.
5. EXPAT lease is the Phase-1 mitigation for I5 without wiring release_held.

## Open questions the spike must answer

- Does I5 reproduce on a normal area close?
- Is EXPAT lease reclaim reachable without FORCE UNLOCK / engine change?
- Exact create path through the runtime for INVITEM / INVCHKOUT.
- Member identity: bind to SYSMEMBER via current_member() (preferred).
