# Ledger schema sketch (minimal)

**Constraint:** express this through x64base / DotTalk++ SQLITE surfaces (or existing table mechanisms). Prefer reuse of existing patterns (work areas, known table-creation paths, existing naming conventions).

This is a sketch for the spike, not a frozen schema. The spike may discover that some columns already exist under different names or that a thinner model is enough.

## INV_ITEM -- inventory items

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| ITEM_ID | integer / key | stable id |
| KIND | char/text | FILE, CAPSULE, DOC, SAMPLE, OTHER |
| REF | text | path or capsule identifier |
| MERGEABLE | logical / char | Y = advisory locks OK; N = exclusive preferred |
| TITLE | text | short human label |
| CREATED_AT | datetime/text | when registered |
| CREATED_BY | text | member |

## INV_CHECKOUT -- current and historical check-outs

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| CO_ID | integer / key | |
| ITEM_ID | integer | FK to INV_ITEM |
| MEMBER | text | who holds / held the lock |
| MODE | char | E = exclusive, A = advisory |
| STATE | char | HELD, RELEASED, BROKEN |
| ACQUIRED_AT | datetime/text | |
| RELEASED_AT | datetime/text | null while held |
| NOTE | text | optional |

## INV_EVENT -- simple history (optional if CHECKOUT history is enough)

| Column | Type (sketch) | Notes |
|--------|---------------|-------|
| EV_ID | integer / key | |
| ITEM_ID | integer | |
| MEMBER | text | |
| ACTION | char/text | REGISTER, ACQUIRE, RELEASE, BREAK |
| AT | datetime/text | |
| DETAIL | text | |

## Design notes for the spike

1. Reuse first. Before creating new tables, inspect whether the runtime already has lock, grant, or reservation tables that can be extended or mirrored.
2. Capsule reference. REF for KIND=CAPSULE should accept a workspace/capsule identifier without forcing the item to be a filesystem path.
3. Exclusive semantics. While STATE=HELD and MODE=E for an ITEM_ID, a second exclusive ACQUIRE must fail.
4. Private. These tables live in the private development / runtime data area, never staged to the public site tree.
5. Naming. Prefer a clear INV_ prefix (or whatever local convention the runtime already uses for similar ledgers) so the tables are obvious in a work-area list.

## Open questions the spike should answer

- Exact create path: SQLITE DDL through the runtime, or an existing table-definition mechanism?
- Member identity: free text for the spike, or must it bind to the identity stack (USERS / TEAM_MEMBER)? Prefer reuse if identity is already easy to read; otherwise free text is acceptable for Phase-1 only.
- Do we need INV_EVENT, or is INV_CHECKOUT history sufficient?
