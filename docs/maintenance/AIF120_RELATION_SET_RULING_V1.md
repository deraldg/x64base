---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-034
  recorded_at_utc: 2026-08-19T11:00:00Z
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
    baseline_commit: e5a9c868a
  authorization:
    requested_by: maintainer (member.derald), in-session. R21 left two open items --
      two workers rather than one worker and the UI thread, and contention across work
      areas. They are the same experiment.
  report:
    path: docs/maintenance/AIF120_RELATION_SET_RULING_V1.md
    kind: ruling
---

# AIF-120 -- R26: the unit of serialization is the RELATION SET, not the work area

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

R11.4, as R21 corrected it, says work is serialized **per workspace** and that
navigation is what triggers it. Both halves are right and the unit is wrong.

## 1. The experiment

`gui/uidef/relate_test.py`. Parent `STUDENTS.dbf`, 200 records. Child
`ENROLL.dbf`, 686 records across 200 distinct `SID`s. Between them,
`SET RELATION TO sid INTO enroll` -- moving the parent's record pointer
repositions the child's.

Two handlers, both `DISPATCH = worker`, running at the same time:

| handler | what it does | what it locks |
| --- | --- | --- |
| `TotalGpa` | walks the PARENT top to bottom, summing `GPA` | the parent |
| `ListEnrolments` | reads the CHILD rows for one student | the child |

`ListEnrolments` does everything R11.4 asks. It locks the work area it touches. It
never names the parent, never opens it, never takes its lock.

## 2. Measured, 100 trials per mode

| mode | wrong result | returned another student's rows |
| --- | --- | --- |
| no lock at all | 100/100 | 0/100 |
| **each handler locks the work area it touches** | **100/100** | 0/100 |
| each handler locks the whole relation set | **0/100** | 0/100 |

**Correct per-workspace locking scores exactly the same as no locking at all.**

The child handler was never wrong about its own work area. `TotalGpa`'s `SKIP`
moved the child's record pointer through the relation, and from the child's side no
call happened -- there is nothing to lock against, because the mutation did not
arrive through the child's interface.

The failures were a truncated list (2 of 5 enrolments, 33 times) and a **duplicated
row** (65 times) -- the pointer moved backwards under the walk and the same
enrolment was read twice.

## 3. The version that leaks

The handler above survived without showing another student's data for one reason:
it re-checked `SID` on every child row and stopped when it changed. That is
redundant work inside a related child walk -- the relation is supposed to guarantee
it -- and a careful programmer removes it.

`ListTrusting` is the same read with that check removed, reading the number of rows
it was told to expect:

| mode | wrong | rows belonging to ANOTHER student |
| --- | --- | --- |
| each handler locks the work area it touches | 100/100 | **100/100** |
| each handler locks the whole relation set | 0/100 | 0/100 |

Every trial. A five-row list, correctly sized, correctly formatted, two or three of
whose rows are another student's academic record. **This is the failure R21.3
described one level up: not a crash, a plausible answer.** Here it is also a
cross-record disclosure, which is a different class of problem in a frontend that
shows one person's data at a time.

The handler that got away with it was protected by a guard it did not know it
needed.

## 4. The ruling

> **R26.** Where a relation exists between work areas, the unit of serialization is
> the **relation set** -- the transitive closure of related areas -- not the
> individual work area. A handler that locks only the areas it names is not
> serialized, because navigating any area in the set repositions the others without
> passing through their interfaces.

Corollaries:

- **R26.1.** A target cannot compute the lock domain from a handler's code. It has
  to know the relations. `SET RELATION` is document state, not handler state, and
  it belongs with the data source declaration.
- **R26.2.** The `DOC` record's `SOURCE` already carries `Alias`, `Table` and
  `Order` per work area. It does **not** carry relations, so a document with two
  cursors and a relation between them is currently unrepresentable, and a generated
  frontend cannot know its own lock domain. This is a gap, named and not closed
  here.
- **R26.3.** Lock-order inversion follows from R26 and is not separately tested:
  two handlers taking per-area locks in different orders across a relation set can
  deadlock. Locking the set removes the possibility by construction, because there
  is one lock. **Untested** -- stated as a consequence, not as a measurement.

## 5. What this changes

- R11.4's "against one workspace" is narrowed to "against one relation set".
  R21's two corrections to R11.4 stand; this is the third.
- **The design table needs somewhere to put relations** (R26.2). That is the first
  gap in `SOURCE` this lane has found, and it is the owner's call whether it is a
  `SOURCE` key or something larger.
- No target obligation changes shape: it is still "serialize the domain", with a
  bigger domain.

## 6. Still open

- **The relation model here is one-to-many, one level deep.** VFP allows chains and
  multiple children. The transitive closure is what the ruling says; the test
  exercises one edge of it.
- **Deadlock is argued, not measured** (R26.3).
- **This is a Python model of a cursor**, as R21's was. Evidence tier:
  **runtime-proven for the rule, source-evidenced for the relation semantics.**

## 7. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_RELATION_SET_RULING_V1.md
git add docs/maintenance/evidence/AIF120_relation.txt
git add gui/uidef/relate_test.py
git diff --cached --stat
git commit -m "AIF-120: R26 -- the unit of serialization is the relation set; correct per-workspace locking scores the same as none"
```
