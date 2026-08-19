---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260820-COWORK-070
  recorded_at_utc: 2026-08-20T06:40:00Z
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
    baseline_commit: 64dedf551
  authorization:
    requested_by: maintainer (member.derald), in-session -- "note: x64base is NOT
      foxpro language compatible, just similar, with a sql ish flavor".
  report:
    path: docs/maintenance/AIF120_NOT_FOXPRO_V1.md
    kind: ruling
---

# AIF-120 -- R62: x64base is not FoxPro, and the lane has been quoting a language that is not there

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-20.

## 0. Correction 42 -- the frame, not a fact

The maintainer: *"x64base is NOT foxpro language compatible, just similar, with a sql
ish flavor."*

This lane has reasoned in FoxPro semantics throughout. R52.1 was withdrawn in R54 for
resting on an unmeasured claim about `FLOCK()`; the deeper error was assuming there
was a `FLOCK()` to be right or wrong about. The lane's charter -- derive a UI language
**from VFP's designer formats** -- justifies reading `.SCX` and `.VCX`. It does not
license importing VFP's *runtime* vocabulary, and the two got blurred.

Measured:

| assumed | actually |
|---|---|
| `FLOCK()` | not a verb. One occurrence, inside a regression-test **description string** (`cmd_regression.cpp:136`, prose about "FLOCK per append") |
| `RLOCK()` | not a verb. `rlocked` in `cmd_lock.cpp:109` is a local `bool` |
| `SET REPROCESS` | **does not exist.** The only "reprocess" in `cmd_set.cpp` is `preprocess_for_dispatch` at line 1956 -- a plural-form rewrite, unrelated to locking |

The lock verbs are `LOCK` and `UNLOCK` (R50), and there is no retry setting.

## 1. R62.1 -- withdrawn: the `SET REPROCESS` open item

R47 section 5 and R48 section 7 both carry:

> *"`SET REPROCESS` has no UIDEF field. The owner ruled for plain refusal, and real
> VFP lets a program ask for N retries or a timeout. A document cannot express that
> today. If it should, it is a schema change and therefore the owner's."*

**Withdrawn.** There is nothing to expose. A UIDEF field for `SET REPROCESS` would
model a FoxPro setting x64base does not have, and putting it in front of the owner as
a pending schema decision was asking about someone else's product.

**What survives untouched** is the behaviour R47 measured and the owner ruled on: a
busy domain **refuses** rather than queues, proven against the binary in R50 and
across two typed frontends in R60. That result never depended on VFP; only its *name*
did. Calling it "FLOCK semantics" was borrowed vocabulary for a measured behaviour,
and the vocabulary carried a compatibility claim the behaviour never made.

## 2. R62.2 -- the SQL surface, and what UIDEF cannot say

The "sql ish flavor" is a real and substantial surface:

```
src/cli/  cmd_sql.cpp        cmd_sql_select.cpp   cmd_sql_insert.cpp
          cmd_sql_update.cpp cmd_sql_show.cpp     cmd_sql_erase.cpp
          cmd_sqlite.cpp     cmd_importsql.cpp    cmd_select.cpp
```

```
SQLSEL SELECT <col>[,<col>...] FROM <table> [WHERE <predicate>]
       [ORDER BY <field> [ASC|DESC]] [LIMIT <n>]
SQLSEL SELECT SID,LNAME FROM STUDENTS WHERE MAJOR = "CSCI"
SQLSEL SELECT COUNT(*) FROM STUDENTS WHERE GPA >= 3.0
```

**UIDEF cannot express a form backed by any of that.** Section 10's `SOURCE` names
`Alias`, `Table`, `Order` and `Relation` -- work-area navigation, entirely. Section
10b's `BINDING` is `alias.field`, which presumes an alias, which presumes a work
area. A control bound to `SELECT ... WHERE MAJOR = "CSCI"` has no alias to name.

This is not a defect in the contract; v1 was derived from VFP forms, and VFP forms
bind to work areas. It is a **limit the contract does not state**, and stating limits
is what section 13 exists for -- *"What v1 does not do, stated so nobody has to
discover it."*

**Owner question, and it is a real fork:**

1. **Say so in section 13.** UIDEF v1 binds to work areas; query-backed forms are out
   of scope. Cheapest, honest, and closes the question.
2. **Give `SOURCE` a query form.** An `Alias` whose source is a statement rather than
   a table. This is a schema change, and it collides with R26's lock domain -- a
   query's lock domain is every table it reads, which `SOURCE` would have to state or
   the runtime would have to infer.
3. **Defer.** Leave it unstated, which is what the contract does today, and which
   gate 11 already criticised the document for elsewhere.

I recommend **1 now**, because a stated limit is worth more than an unstated
intention, and 2 is a design with a lock-domain problem inside it that deserves its
own ruling rather than a clause.

## 3. What this changes about how the lane reasons

The rule going forward: **VFP is the source of the DOCUMENT formats and nothing
else.** `.SCX`, `.VCX`, `.FRX`, `.MNX`, the font cache line, `ControlSource`,
`FontBold` -- reading those is the charter. Runtime semantics come from x64base,
measured, and where this lane has quoted VFP for a runtime rule it was decoration at
best and an error at worst.

That is the same shape as the prior-art rule (R54) one level up: **look at what is
there, not at what the ancestor did.**

## 4. Still open

- **Section 13 does not state the query limit.** R62.2, pending the owner's choice.
- Unchanged: R55.2, the mutation model (R61.2), R53.4's `USE` (R61.6), the 2^31 lock
  test (R61.5), and pinocchio-scale.

## 5. Good Neighbor note

- **What changed.** Nothing in code. This ruling withdraws an open item from R47 and
  R48 and records a framing correction.
- **Whose area.** AIF-120's own. `src/cli/` was read only.
- **What authorization.** Maintainer (member.derald), in-session, quoted above.
- **How to verify or undo.** Verify: `grep -rn -i reprocess src/cli/cmd_set.cpp`
  returns one hit, `preprocess_for_dispatch`; `grep -n -i flock src/cli/*.cpp`
  returns a description string. Nothing to undo.

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_NOT_FOXPRO_V1.md
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R62 -- x64base is not FoxPro; the SET REPROCESS open item is withdrawn and the SQL surface is a limit the contract does not state"
```
