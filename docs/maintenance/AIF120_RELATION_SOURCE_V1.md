---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-044
  recorded_at_utc: 2026-08-19T12:50:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 0fcccaf28
  authorization:
    requested_by: maintainer (member.derald), in-session, standing "continue" -- R26.2
      named this gap and made it a correctness requirement rather than a convenience.
  report:
    path: docs/maintenance/AIF120_RELATION_SOURCE_V1.md
    kind: ruling
---

# AIF-120 -- R36: a document states its own lock domain

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R26 proved that a handler locking only the work areas it names is not serialized --
100 trials out of 100 wrong, identical to no locking at all, because navigating any
area in a relation set repositions the others without passing through their
interfaces. It then recorded the gap that made the rule unusable:

> **R26.2.** The `DOC` record's `SOURCE` carries `Alias`, `Table` and `Order` per
> work area. It does **not** carry relations, so a document with two cursors and a
> relation between them is currently unrepresentable, and a generated frontend
> cannot know its own lock domain.

## 1. The information was in the source and the importer threw it away

A `.SCX` DataEnvironment holds `relation` records, and `relation` is in the
importer's `SKIP` set. Measured: **8 relation records across 6 corpus files**, each
carrying everything the rule needs:

```
parentalias = "customer"   childalias = "orders"
relationalexpr = "cust_id" childorder = "cust_id"
```

So while R26 was being written, the importer was discarding the exact data R26.2
said the format could not express. Third time this session: `CLASS` in R31,
`InputMask` in R25, relations here. **The source keeps carrying what the table is
said to lack.**

## 2. R36.1 -- `SOURCE` gains a `Relation` line

Additive, so nothing that reads `Alias`, `Table` or `Order` breaks:

```
Alias = customer
Table = customer
Alias = orders
Table = orders
Alias = orditems
Table = orditems
Alias = products
Table = products
Relation = customer -> orders ON cust_id
Relation = orders -> orditems ON order_id
Relation = orditems -> products ON product_id
```

That is a real corpus form with a **three-level chain**, which is the case R26.3
could only argue about.

## 3. R36.2 -- the manifest computes the closure, before any window exists

`manifest.py` unions the relation edges and reports the domains:

```
REQUIRE  lock domain {customer, orders, orditems, products}
         R26: these work areas move together, so a mutating handler must
         serialize against the whole set, not the area it names
```

**Four work areas in one lock domain, from three declared edges, computed from the
table alone.** A target now learns what it must serialize against before it
dispatches anything -- which is what R24.1 argued a manifest is for, arriving at the
one case where the answer is a correctness requirement rather than a convenience.

A document with several work areas and **no** declared relations gets a `NOTE`
rather than silence, because "each area is its own domain" and "the document did not
say" are different states and the format cannot currently tell them apart.

## 4. What else the same run surfaced

The manifest reported, on the same form:

```
DERIVE  15 of 23 control(s) lack TABORDINAL -- a partial tab order is the
        worst case: the gaps must be derived and interleaved with the
        declared stops
```

R27 wrote that clause defensively and this is the first real document to hit it: a
form where some controls declare a focus order and most do not. The partial case is
worse than either extreme and it occurs in the wild.

## 5. Still open

- **Relation direction is carried and not used.** `parent -> child` matters for
  navigation semantics -- moving the parent moves the child and not the reverse --
  but a lock domain is undirected, so the closure ignores it. A target that wants
  to know which way the pointer propagates has the data; nothing consumes it.
- **`childorder` is dropped.** The relation needs the child's index to resolve, and
  R36 keeps only the expression.
- **Nothing enforces the domain.** The manifest states it; no generated frontend
  takes a lock. `relate_test.py` proves the rule in a model, and the gap between
  the model and a generated app is exactly the gap R35 named for dispatch.
- **8 relations in 170 files** is thin. The rule is right because R26 measured its
  violation, not because the corpus is full of relations.

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_RELATION_SOURCE_V1.md
git add docs/maintenance/evidence/AIF120_relations.txt
git add tools/uidef/import_scx.py
git add tools/uidef/manifest.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R36 -- SOURCE carries relations and the manifest computes the lock domain; R26.2 closed"
```
