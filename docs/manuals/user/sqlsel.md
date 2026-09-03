# SQLsel: Set-Oriented Queries in x64base

```yaml
page_id: USER-SQLSEL-01
title: SQLsel
audience: knows xBase, new to SQLsel
status: DRAFT
last_verified: 2026-09-03
runtime_scope: development
```

## Who this is for

This chapter is for an xBase user who wants a row set without changing the
way the surrounding session is positioned. It assumes you already know how to
open a table with `USE`, choose a work area with xBase `SELECT <area>`, and
inspect ordinary DBF fields.

`SQLSEL HELP` and `SQLSEL USAGE` own the exact grammar accepted by the running
program. This chapter explains what the grammar means, how the pieces compose,
where SQLsel deliberately differs from a general SQL engine, and how to recover
from the refusals you are likely to meet.

This revision documents the current `development` runtime. Single-table
selection and INNER JOIN are default-suite features. LEFT, RIGHT, FULL, and
CROSS JOIN are runtime-proven candidates with named regression gates. They may
not yet exist in an older public or staged build.

---

## Part 1 -- The model

### SQLsel is the select verb

The product name is **SQLsel**. The command is typed as `SQLSEL`.

The canonical statement starts with one select verb:

```text
SQLSEL SID,LNAME FROM STUDENTS
```

The compatibility spelling with a second `SELECT` is still accepted:

```text
SQLSEL SELECT SID,LNAME FROM STUDENTS
```

Prefer the first form in new work. Do not confuse either form with xBase
`SELECT <area>`, which changes the current work area.

### SQLsel reads open work areas

`FROM STUDENTS` does not open a file. It resolves an already-open work area by
name. Open every source table first:

```text
SET PATH DBF DBF/x64
SELECT 1
USE STUDENTS

SQLSEL SID,LNAME,MAJOR FROM STUDENTS LIMIT 5
```

A table does not have to be current when SQLsel reads it. It only has to be
open and uniquely identifiable by its table name.

### A statement is session-neutral

A SQLsel statement names its own table or tables and produces a row set. It
does not use these parts of the ambient xBase session:

- the current work area;
- the current record pointer;
- `SET FILTER`;
- `REL` or `SET RELATION` state.

When the statement finishes, the current area and every source cursor are put
back where they were. This is true on ordinary success and on the guarded
failure paths covered by the regression suite.

The statement does honor the data actually stored in the open tables. Records
marked deleted are excluded from statement-form SQLsel queries.

### SQLsel and RelTalk are different relational tools

| Question | SQLsel | REL / RelTalk |
|---|---|---|
| Starting point | all live rows named by the statement | the current parent record |
| Relationship | written ad hoc in `JOIN ... ON` | declared relation graph |
| Session state | ignored and restored | intentionally cursor-oriented |
| Result | a row set | a traversal projection |
| Best use | selection, sorting, counting, ad hoc matching | walking a known relationship from the current record |

Neither surface is a replacement for the other. A declared `REL` does not make
a SQLsel JOIN, and a SQLsel JOIN does not declare or alter a relationship.

---

## Part 2 -- Statement grammar at a glance

The current statement family is:

```text
SQLSEL <columns> FROM <table> [[AS] <alias>]
       [WHERE <predicate>]
       [ORDER BY <field> [ASC|DESC]]
       [LIMIT <n>]

SQLSEL * FROM <table>

SQLSEL COUNT(*) FROM <table> [WHERE <predicate>]

SQLSEL <columns> FROM <left> [[AS] <left-alias>]
       [INNER] JOIN <right> [[AS] <right-alias>]
       ON <left-alias.field> = <right-alias.field>
       [WHERE <predicate>]
       [ORDER BY <field> [ASC|DESC]]
       [LIMIT <n>]

SQLSEL <columns> FROM <left> [[AS] <left-alias>]
       LEFT|RIGHT|FULL JOIN <right> [[AS] <right-alias>]
       ON <left-alias.field> = <right-alias.field>
       [ORDER BY <field> [ASC|DESC]]
       [LIMIT <n>]

SQLSEL <columns> FROM <left> [[AS] <left-alias>]
       CROSS JOIN <right> [[AS] <right-alias>]
       [WHERE <predicate>]
       [ORDER BY <field> [ASC|DESC]]
       [LIMIT <n>]
```

The brackets above mean optional syntax; do not type the brackets.

Current structural limits are important:

- one source table, or exactly two tables joined once;
- two distinct open tables for a JOIN; self-join is not yet supported;
- a select list of column names or `*`, not computed expressions;
- one `ORDER BY` field;
- one equality condition in `ON` for non-CROSS joins;
- qualified `ON` fields, such as `S.SID = E.SID`;
- no `ON` clause for CROSS JOIN.

When a request falls outside those limits, SQLsel reports a corrective error.
It does not silently replace the unsupported request with a scan or an empty
result.

---

## Part 3 -- Single-table queries

### Project selected columns

```text
SQLSEL SID,LNAME,FNAME FROM STUDENTS
```

SQLsel prints a header, one result line per selected row, and a row count. The
select list may contain unqualified columns or columns qualified by the table
name or alias:

```text
SQLSEL S.SID,S.LNAME FROM STUDENTS AS S
```

Names and aliases are matched without regard to letter case. A qualifier must
name the table or the alias used in the `FROM` clause.

### Project every column

```text
SQLSEL * FROM STUDENTS LIMIT 5
```

Use `*` when you want the complete stored row. SQLsel v1 does not mix `*` with
other select-list items.

### Filter with WHERE

```text
SQLSEL SID,LNAME,MAJOR FROM STUDENTS WHERE MAJOR = "CSCI"
```

The predicate is compiled once, then evaluated against each candidate row.
Logical combinations and supported expression functions work through the
shared expression engine:

```text
SQLSEL SID,LNAME,GPA FROM STUDENTS WHERE ALLTRIM(MAJOR) = "CSCI" AND GPA >= 3.0
```

Unknown fields, malformed trailing input, and incompatible comparisons report
an error. A misspelled field must not look like a legitimate empty result.

### Sort before limiting

```text
SQLSEL SID,LNAME,MAJOR FROM STUDENTS WHERE MAJOR = "CSCI" ORDER BY LNAME LIMIT 3
```

`ORDER BY` is applied to the full matching set. `LIMIT` is applied after the
sort. SQLsel reports both the number of hidden rows after a limit and the sort
access path. The current single-table path is a materialized sort.

Use `DESC` for descending order:

```text
SQLSEL SID,LNAME FROM STUDENTS ORDER BY LNAME DESC LIMIT 10
```

Without `ORDER BY`, do not treat the observed row order as a durable contract.

`LIMIT` accepts zero or a positive integer. `LIMIT 0` selects no display rows
but still represents a deliberate limit, not a syntax error.

### Count rows

```text
SQLSEL COUNT(*) FROM STUDENTS
SQLSEL COUNT(*) FROM STUDENTS WHERE GPA >= 3.0
```

`COUNT(*)` is the one aggregate implemented in the current statement surface.
It returns one output row. `ORDER BY` does not apply to `COUNT(*)` and is
refused.

`COUNT(field)`, `SUM`, `AVG`, `MIN`, `MAX`, `GROUP BY`, and `HAVING` are planned
but are not current grammar. When numeric aggregates arrive, the recorded
x64base rule is to skip blank non-numeric cells and report both the contributing
and blank counts. That future rule does not turn a DBF blank into SQL NULL.

---

## Part 4 -- Joining two open tables

Open both inputs in separate work areas before running the statement:

```text
SET PATH DBF DBF/x64

SELECT 1
USE STUDENTS

SELECT 2
USE ENROLL

SELECT 1
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID ORDER BY E.CLS_ID LIMIT 5
```

The shipped x64 `ENROLL` table stores the class identifier in `CLS_ID`. Use
`E.CLS_ID`, not a generic `E.COURSE` name copied from another schema.

### Aliases are more than decoration

Aliases make ownership explicit:

```text
FROM STUDENTS AS S JOIN ENROLL AS E ON S.SID = E.SID
```

The `AS` keyword is optional:

```text
FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID
```

Use aliases for every join and qualify every projected field. SQLsel refuses an
ambiguous unqualified column instead of guessing which table you meant. The two
`ON` operands must be qualified.

### INNER JOIN

`JOIN` and `INNER JOIN` mean the same thing. Only matched pairs are emitted:

```text
SQLSEL S.SID,S.LNAME,E.CLS_ID FROM STUDENTS S INNER JOIN ENROLL E ON S.SID = E.SID
```

If one student matches three enrollment records, the result contains three
rows. That multiplication is relational behavior, not a duplicate-removal bug.

INNER JOIN permits a `WHERE` predicate over the joined row:

```text
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID WHERE E.CLS_ID = "F25ARTS102"
```

### LEFT JOIN

LEFT JOIN preserves every live left row. A left row with no match receives
produced-absent cells on the right:

```text
SQLSEL S.SID,S.LNAME,E.CLS_ID FROM STUDENTS S LEFT JOIN ENROLL E ON S.SID = E.SID
```

### RIGHT JOIN

RIGHT JOIN preserves every live right row. An enrollment with no matching
student receives produced-absent cells on the left:

```text
SQLSEL S.SID,S.LNAME,E.CLS_ID FROM STUDENTS S RIGHT JOIN ENROLL E ON S.SID = E.SID
```

### FULL JOIN

FULL JOIN preserves unmatched rows from both inputs:

```text
SQLSEL S.SID,S.LNAME,E.CLS_ID FROM STUDENTS S FULL JOIN ENROLL E ON S.SID = E.SID
```

### CROSS JOIN

CROSS JOIN emits the Cartesian product of the live rows in both tables. It has
no `ON` clause:

```text
SQLSEL S.SID,E.CLS_ID FROM STUDENTS S CROSS JOIN ENROLL E LIMIT 10
```

The full shipped example is large: 200 students by 686 enrollments before
deleted-row exclusions means up to 137,200 pairs. Use a selective `WHERE` or a
small `LIMIT` while exploring, but remember that the current implementation
forms and filters the candidate pairs before `LIMIT` trims the displayed set.

CROSS JOIN permits `WHERE` because every result cell comes from an actual input
row:

```text
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S CROSS JOIN ENROLL E WHERE S.SID = 50000112 AND E.SID = 50000112
```

### Outer JOIN and WHERE

`WHERE` on LEFT, RIGHT, or FULL JOIN is currently refused. The predicate seam
has true, false, and error, but does not yet have SQL's UNKNOWN truth state for
produced-absent cells. Refusal is safer than treating absence as a DBF blank and
returning a plausible wrong answer.

Prepare a filtered source table explicitly when that is appropriate, or wait
for the three-valued predicate phase. Do not rewrite an outer join as an inner
join and assume it means the same thing.

---

## Part 5 -- Blanks, absence, and the lack of SQL NULL

x64base DBF data has no stored SQL NULL literal in SQLsel v1. A blank character
or numeric cell is a value in the xBase model.

Outer joins still need to show that one side did not produce a row. SQLsel
carries that state internally as produced absence and renders it as:

```text
<UNMATCHED>
```

This marker is display, not stored table data and not a new NULL literal.
SQLsel also reports how many rows were extended on each absent side.

Three cases must stay distinct even if two look alike on screen:

| Case | Meaning |
|---|---|
| an ordinary blank cell | the input row exists and the field is blank |
| produced `<UNMATCHED>` | no input row existed on that side of the outer join |
| stored text `<UNMATCHED>` | the input row exists and literally contains those characters |

The internal row carrier distinguishes all three. Plain text output cannot
visually distinguish the last two by their cell text alone, so use the join's
extension report and key columns when interpreting or testing output.

---

## Part 6 -- Access paths and the JOIN read fence

### Every JOIN says how it ran

For an equality join, SQLsel looks at the right-hand table. If that work area
has an attached CDX/LMDB index whose active tag matches the right `ON` field,
SQLsel can seek once per live left row. Otherwise it uses a nested-loop scan.

The statement reports one of these paths:

- `CDX seek`;
- `nested-loop scan`;
- `hybrid CDX seek + nested-loop scan` if a seek attempt must fall back.

The path report is part of the result evidence. Equal rows do not prove that an
index was used. If performance matters, read the path line instead of inferring
the plan from which index files exist on disk.

An index must be attached and its tag active in the right work area. Merely
having a `.cdx` file beside the DBF is not enough. Use the ordinary index and
order commands for that area, then run SQLsel and confirm the path it reports.

CROSS JOIN has no equality key and therefore reports the scan path.

### A JOIN takes a cooperative statement read fence

Before reading either table, a JOIN requests cooperative table locks for both
inputs in canonical path order. The order prevents two SQLsel statements from
creating an A-then-B versus B-then-A deadlock. The request is non-blocking: if a
cooperating writer owns either table, the whole statement refuses before it
reads one side.

If the caller already owns one of the table locks in the current process,
SQLsel borrows it and leaves it owned when the statement ends. Locks acquired
by SQLsel are released by SQLsel.

This fence gives one statement a stable cooperative read interval across two
tables. It is not:

- MVCC or a historical snapshot;
- a general SQL transaction;
- cross-table write atomicity;
- a repair for a non-cooperating process that ignores x64base locks.

Single-table SQLsel does not use this two-table fence. SQLsel does not mutate
table data.

---

## Part 7 -- Committed truth and TABLE BUFFER

SQLsel statement form reads committed table data. An uncommitted TABLE BUFFER
edit that a preview surface can show is not overlaid onto either projection or
`WHERE` evaluation.

That split is deliberate:

- `TUP` and `TUPLE` may be preview surfaces for buffered edits;
- SQLsel is a statement surface and reads committed truth until SQLsel DML is
  implemented.

Projection and filtering within one SQLsel statement therefore observe the
same committed source. Commit the buffered edit before expecting a SQLsel
statement to see it.

---

## Part 8 -- Workspaces and name resolution

SQLsel works with open work areas, not with the workspace catalog as a query
namespace. Its resolver currently sees process-wide open table names.

This leads to a strict practical rule:

> Keep every table name used by one SQLsel statement unique among the open work
> areas in the process.

A table opened as `STUDENTS` in one workspace and a different `STUDENTS` opened
in another do not become addressable as `workspace.STUDENTS`. SQLsel has no
`IN <workspace>` qualifier and does not consult the workspace relation graph.
Behavior with duplicate open table names is not a cross-workspace contract.

SQLsel can join two areas that happen to belong to different workspaces when
their process-wide table names are unique. That is an implementation consequence
of area resolution, not proof of a supported multi-workspace SQL namespace.

If names collide, close the unneeded handle or reopen the tables under a session
posture that makes the names unique. Do not depend on whichever duplicate a
particular build happens to find first.

See [Workspaces and MiniDBs](workspaces-and-minidbs.md) for workspace membership
and duplicate-handle behavior.

---

## Part 9 -- The legacy predicate-scan form

Before statement-form SQLsel, the command also supplied a diagnostic count over
the current area. That form remains for compatibility:

```text
SQLSEL COUNT
SQLSEL COUNT ALL
SQLSEL COUNT DELETED
SQLSEL COUNT FOR GPA >= 3.0
SQLSEL LNAME = "SMITH"
```

Its model is different from a statement:

| Legacy scan | Statement form |
|---|---|
| reads the current area | names tables in `FROM` |
| may move the current cursor | restores all source cursors |
| `ALL` and `DELETED` select deletion modes | statement rows always exclude deleted records |
| emits per-record diagnostic lines and a count | emits a row set or `COUNT(*)` |
| no `FROM` keyword | identified by top-level `FROM` |

Use statement form for new set-oriented work. Use the legacy form when you
specifically want its current-area diagnostic scan.

`SQLSEL COUNT` is legacy. `SQLSEL COUNT(*) FROM STUDENTS` is statement form.
The parentheses and `FROM` are not cosmetic.

---

## Part 10 -- Common refusals and recovery

### `table '<name>' is not open`

Cause: `FROM` names no open work area.

Recovery: select any convenient area, `USE <name>`, then rerun the statement.
The source table does not have to remain current.

### `column '<name>' is ambiguous`

Cause: both joined tables own the unqualified projected or ordered name.

Recovery: qualify it with the alias, such as `S.SID` or `E.SID`.

### `JOIN ON columns must be qualified`

Cause: one side of `ON` was written as a bare field.

Recovery:

```text
ON S.SID = E.SID
```

### `one statement accepts exactly one JOIN`

Cause: the statement tries to join three or more tables.

Recovery: split the work into supported two-table queries. Do not assume the
intermediate text output can be fed back as a table without an explicit export
and import step.

### `self-join is not yet supported`

Cause: both table references resolve to the same open area, even if aliases
differ.

Recovery: redesign the query or use two deliberately distinct table handles
only after checking whether the current resolver can identify them uniquely.
Aliases alone do not create a second handle.

### `CROSS JOIN does not accept an ON clause`

Cause: CROSS was combined with `ON`.

Recovery: remove `ON`. Put a supported filter in `WHERE`, or use INNER JOIN if
the equality condition is the relationship you intend.

### Outer JOIN with WHERE refuses

Cause: SQLsel has not yet promoted SQL UNKNOWN semantics.

Recovery: do not coerce produced absence to a blank. Use a query shape that
does not require filtering the outer result, or wait for the tri-state phase.

### `not a bare column name`

Cause: the select list contains an expression such as `ALLTRIM(LNAME)`.

Recovery: project stored columns only. Functions belong in a supported `WHERE`
predicate today, not in the select list.

### `LIMIT expects a non-negative integer`

Cause: the limit is negative, non-numeric, or has trailing text.

Recovery: use `LIMIT 0` or a positive whole number.

### The query is correct but slow

Read the reported access path. For a JOIN, make sure the right work area has an
attached CDX/LMDB index with an active tag on the right `ON` field. For a CROSS
JOIN, reduce the inputs or add a selective supported `WHERE`; there is no join
key to seek.

---

## Part 11 -- Current capability boundary

| Capability | Current development state |
|---|---|
| single-table column projection and `*` | supported |
| `WHERE` through the shared expression engine | supported |
| one-field `ORDER BY`, `ASC` or `DESC` | supported |
| `LIMIT` after sort/filter | supported |
| `COUNT(*)` | supported |
| two-table INNER JOIN | supported and default-suite gated |
| LEFT JOIN | runtime-proven candidate |
| RIGHT, FULL, CROSS JOIN | runtime-proven candidate |
| CDX-assisted equality join with reported fallback | runtime-proven |
| DISTINCT | not implemented |
| UNION, UNION ALL, INTERSECT, EXCEPT | not implemented |
| GROUP BY, HAVING, SUM, AVG, MIN, MAX | not implemented |
| subqueries, IN, EXISTS | not implemented |
| expression projection | not implemented |
| more than one JOIN | not implemented |
| self-join | not implemented |
| outer-join WHERE | refused pending UNKNOWN semantics |
| stored SQL NULL literal | not present in v1 |
| SQLsel INSERT, UPDATE, DELETE | not implemented |
| SQL BEGIN, COMMIT, ROLLBACK | not implemented |
| workspace-qualified table names | not implemented |

The implementation plan includes the remaining modern relational algebra, but
a plan is not a runtime feature. If `SQLSEL HELP` in your build does not show a
form listed as a candidate here, treat the running build as authoritative.

---

## Part 12 -- Three complete working patterns

### Pattern A: a small sorted report

```text
SET PATH DBF DBF/x64
SELECT 1
USE STUDENTS
GO 2

SQLSEL SID,LNAME,MAJOR FROM STUDENTS WHERE MAJOR = "CSCI" ORDER BY LNAME LIMIT 10

? "cursor still here: " + ALLTRIM(LNAME)
CLOSE
```

What to check:

- the result contains only `CSCI` rows;
- the visible rows are in `LNAME` order;
- a limit report says whether more rows existed;
- the final expression reads the same record parked by `GO 2`.

### Pattern B: an ad hoc two-table match

```text
SET PATH DBF DBF/x64

SELECT 1
USE STUDENTS
GO 2

SELECT 2
USE ENROLL
GO 4

SELECT 1
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID ORDER BY E.CLS_ID LIMIT 5

SELECT 1
? "left cursor: " + ALLTRIM(LNAME)
SELECT 2
? "right cursor: " + ALLTRIM(CLS_ID)

CLOSE
SELECT 1
CLOSE
```

What to check:

- SQLsel reports the two-table read fence;
- SQLsel reports CDX seek, scan, or an honest hybrid;
- both final expressions read the records parked before the query.

### Pattern C: preserve unmatched rows

```text
SQLSEL S.SID,S.LNAME,E.CLS_ID FROM STUDENTS S LEFT JOIN ENROLL E ON S.SID = E.SID ORDER BY S.SID
```

What to check:

- students with multiple enrollments produce multiple rows;
- students without an enrollment remain present;
- produced right-side absence displays as `<UNMATCHED>`;
- SQLsel reports the count of left-extended rows;
- no `WHERE` follows the LEFT JOIN in the current grammar.

---

## Part 13 -- Maintainer verification

The SQLsel regressions create disposable SANDBOX tables, compare result blocks
with SQLite where applicable, and fail closed when expected evidence is absent.
Run the named gates rather than treating a clean launch or a visual sample as a
correctness proof:

```text
REGRESSION SQLSEL_SELECT_V1
REGRESSION SQLSEL_INNER_JOIN
REGRESSION SQLSEL_JOIN_EDGES
REGRESSION SQLSEL_LEFT_JOIN
REGRESSION SQLSEL_JOIN_FAMILY
REGRESSION SQLSEL_BUFFER_VIS
REGRESSION EVALDIFF
```

The JOIN validators check answers and access paths separately. The SELECT and
JOIN validators compare marked result sets with embedded SQLite oracles. The
evaluator gate pins exact true, false, and error counts rather than accepting
mere parity between two evaluators.

These commands are verification tools, not a substitute for reading the
corrective text from the query you are actually running.

---

## Quick reference

For a new SQLsel statement:

1. Open every source table with `USE`.
2. Keep source table names unique among the process's open work areas.
3. Start with `SQLSEL <columns> FROM <table>`.
4. Use aliases and qualify every join field.
5. Add `WHERE`, then `ORDER BY`, then `LIMIT` in that order.
6. Read the limit, sort, join-path, extension, and fence reports.
7. Remember that statement SQLsel excludes deleted records and reads committed
   truth.
8. Treat `<UNMATCHED>` as an outer-join display marker, not stored NULL.
9. Expect outer-join `WHERE`, expression projection, set operations, grouping,
   and subqueries to refuse until their phases are implemented.
10. Use `SQLSEL HELP` against the exact executable you are running.
