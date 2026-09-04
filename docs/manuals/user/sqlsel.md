# SQLsel: Typed SQL Over x64base Work Areas

```yaml
page_id: USER-SQLSEL-01
title: SQLsel
audience: knows xBase, new to SQLsel
status: DEVELOPMENT-RUNTIME-VERIFIED
last_verified: 2026-09-03
runtime_scope: development
```

## Purpose and authority

SQLsel is the house SQL surface for x64base. It provides SQL-shaped selection,
joins, set operations, grouping, subqueries, and guarded data changes without
replacing the x64base storage engine.

The important architectural fact is simple: SQLsel is not a second database.
It resolves existing open work areas, carries their declared field types in
typed TupleRows, evaluates through the house expression engine, and sends data
changes through the existing table buffer, TBJ1 write-ahead journal, locks,
index maintenance, and COMMIT path.

`SQLSEL HELP` and `SQLSEL USAGE` are the grammar authority for the executable
you are actually running. This chapter explains the model and the boundaries.
It documents the current `development` runtime; an older staged or public build
may expose less.

## 1. Two ways to type SQLsel

In native mode, prefix a statement with `SQLSEL`:

```text
SQLSEL SID,LNAME FROM STUDENTS WHERE MAJOR = 'CSCI'
SQLSEL INSERT INTO STUDENTS (SID,LNAME) VALUES (9,'SMITH')
```

`SQLSEL` is itself the select verb. A second `SELECT` is accepted for
compatibility, but is optional:

```text
SQLSEL SELECT SID,LNAME FROM STUDENTS
```

SQL mode supplies familiar aliases:

```text
SET MODE SQL
SELECT SID,LNAME FROM STUDENTS
UPDATE STUDENTS SET LNAME = UPPER(LNAME) WHERE SID = 9
SET MODE NATIVE
```

In SQL mode, `SELECT`, `INSERT`, `UPDATE`, `DELETE`, `BEGIN`, `COMMIT`, and
`ROLLBACK` route to SQLsel. Native `SELECT <area>` and REL commands are not
available until you return to native mode. `SQLSEL` itself remains accepted in
either mode.

## 2. Tables, workspaces, and session state

### Open the tables first

SQLsel does not open files named in `FROM`, `INSERT INTO`, `UPDATE`, or
`DELETE FROM`. Open the tables with the ordinary xBase commands first:

```text
SET PATH DBF DBF/x64
SELECT 1
USE STUDENTS
SELECT 2
USE ENROLL
```

### Names are scoped to the current workspace

SQLsel resolves table names only among areas belonging to the current
workspace. If workspace A and workspace B both have a table named `STUDENTS`,
a SQLsel statement issued while A is current reaches A's table. It does not
pick the lowest matching slot from another workspace.

SQLsel does not currently accept a `workspace.table` qualifier. Switch to the
workspace you intend to query, then issue the statement. One statement cannot
join across two workspaces.

### SELECT is cursor-neutral

A SQLsel SELECT does not consume:

- the current record pointer;
- `SET FILTER`;
- `REL` or `SET RELATION` state.

It restores the current area and every source cursor after success or guarded
failure. Statement SELECT excludes records marked deleted.

SQLsel JOIN and RelTalk answer different questions. JOIN matches sets described
inside one statement. REL follows a declared, cursor-oriented relationship
graph. A JOIN does not declare a relation, and a declared relation does not
change SQLsel's result.

## 3. SELECT grammar and typed expressions

The general query shape is:

```text
SQLSEL [SELECT] [DISTINCT] <select-list>
       FROM <source>
       [WHERE <predicate>]
       [GROUP BY <group-list>]
       [HAVING <predicate>]
       [ORDER BY <item> [ASC|DESC] [, ...]]
       [LIMIT <non-negative-integer>]
```

The select list may contain stored columns, `*`, aggregates, and supported
house expressions with optional aliases:

```text
SQLSEL SID,LNAME FROM STUDENTS
SQLSEL * FROM STUDENTS LIMIT 5
SQLSEL UPPER(LNAME) AS SURNAME,GPA + 0.25 AS PROJECTED_GPA FROM STUDENTS
```

The expression engine sees the TupleRow's field types. Numeric, logical, date,
and character values do not become an untyped bag of strings merely because
the result is printed as text. Unknown columns, malformed trailing input, and
incompatible operations refuse instead of silently returning an empty set.

`WHERE` retains rows for which the predicate is TRUE:

```text
SQLSEL SID,LNAME,GPA FROM STUDENTS
       WHERE ALLTRIM(MAJOR) = 'CSCI' AND GPA >= 3.0
```

`ORDER BY` may name multiple result columns. Sorting happens before `LIMIT`:

```text
SQLSEL MAJOR,LNAME,SID FROM STUDENTS
       ORDER BY MAJOR ASC,LNAME DESC LIMIT 20
```

SQLsel reports materialized sorting and reports when LIMIT hides additional
rows. Without `ORDER BY`, observed output order is not a durable contract.

## 4. Joins

### Two-table joins

SQLsel supports INNER, LEFT, RIGHT, FULL, and CROSS joins over open tables:

```text
SQLSEL S.SID,S.LNAME,E.CLS_ID
       FROM STUDENTS S
       JOIN ENROLL E ON S.SID = E.SID

SQLSEL S.SID,S.LNAME,E.CLS_ID
       FROM STUDENTS S
       LEFT JOIN ENROLL E ON S.SID = E.SID
```

`JOIN` means `INNER JOIN`. CROSS JOIN has no ON clause. Aliases should be
distinct, and qualification is required when a bare name would be ambiguous.

ON is a typed predicate, not just a single textual key comparison. Composite
conditions work:

```text
SQLSEL E.NAME,B.AMT
       FROM EMPLOYEE E
       JOIN BONUS B ON E.ID = B.ID AND E.DEPT = B.DEPT
```

Self-joins work when aliases distinguish the two roles:

```text
SQLSEL E.NAME,M.NAME
       FROM EMPLOYEE E
       JOIN EMPLOYEE M ON E.MGR = M.ID
```

### Join chains

Three or more sources can be chained with INNER, LEFT, and CROSS stages:

```text
SQLSEL E.NAME,B.KIND,C.LABEL
       FROM EMPLOYEE E
       JOIN BONUS B ON E.ID = B.ID
       JOIN CATEGORY C ON B.KIND = C.KIND
       ORDER BY E.NAME
```

RIGHT and FULL remain two-table forms. A chain containing a RIGHT or FULL stage
refuses rather than rewriting the query.

### Outer absence and three-valued logic

x64base DBFs do not store SQL NULL. Nevertheless, an outer join needs to carry
the fact that no row was produced on one side. SQLsel represents that fact as
a typed `ProducedAbsent` cell and renders it as:

```text
<UNMATCHED>
```

Produced absence is not a DBF blank, and stored text that happens to equal
`<UNMATCHED>` is still ordinary text. Comparisons involving produced absence
evaluate to SQL UNKNOWN. WHERE keeps TRUE and rejects FALSE or UNKNOWN, so
outer-join filters behave without pretending that a blank is NULL.

### Read fences and access paths

A multi-table SELECT takes cooperative table locks in canonical path order. It
refuses immediately on contention, before reading a partial set. Locks already
owned by the caller are borrowed and preserved; locks acquired by SQLsel are
released when the statement finishes.

This is a statement read fence, not MVCC and not a historical snapshot. A
process that ignores x64base locking is outside the guarantee.

For a two-table equi-join, SQLsel can use the active attached CDX/LMDB tag on
the right key. It reports `CDX seek`, `nested-loop scan`, or an honest hybrid.
Join chains currently report correctness-first nested-loop stages. Equal row
sets do not prove the requested access path; read the report.

## 5. DISTINCT and set operations

DISTINCT removes duplicate typed rows:

```text
SQLSEL DISTINCT MAJOR FROM STUDENTS
```

SQLsel supports:

```text
<select> UNION <select>
<select> UNION ALL <select>
<select> INTERSECT <select>
<select> EXCEPT <select>
```

Example:

```text
SQLSEL SID,LNAME FROM STUDENTS
UNION
SELECT SID,LNAME FROM ALUMNI
```

Each operand must return the same number of columns with compatible TupleRow
types. SQLsel refuses incompatible operands instead of coercing them. UNION,
INTERSECT, and EXCEPT remove duplicates; UNION ALL preserves them. INTERSECT
binds more tightly than UNION and EXCEPT.

The current set-expression surface does not accept an outer ORDER BY or LIMIT.
Filter or materialize the operands before combining them.

## 6. Grouping and aggregates

Supported aggregates are `COUNT`, `SUM`, `AVG`, `MIN`, and `MAX`:

```text
SQLSEL COUNT(*),COUNT(SALARY),SUM(SALARY),AVG(SALARY),MIN(SALARY),MAX(SALARY)
       FROM STAFF

SQLSEL DEPT AS DEPARTMENT,
       COUNT(*) AS ROWS,
       AVG(SALARY) AS MEAN_PAY
       FROM STAFF
       WHERE ACTIVE = .T.
       GROUP BY DEPT
       HAVING COUNT(*) >= 2
       ORDER BY DEPARTMENT
```

`COUNT(*)` counts input rows. `COUNT(field)` counts contributing nonblank field
values. Numeric aggregates skip blank numeric cells and report both the
contributing count and the blank count. Therefore AVG divides by the number of
contributing nonblank values, matching the SQL result without declaring the DBF
blank to be a stored NULL.

SUM and AVG require numeric input. MIN and MAX preserve the relevant field
type, including dates. A projected nonaggregate column must appear in GROUP BY.
Aggregate arguments are columns or `*` where the aggregate permits it; arbitrary
expressions such as `SUM(SALARY+1)` are currently refused.

Grouping can consume a joined result as well as one table:

```text
SQLSEL D.LABEL,COUNT(*),AVG(A.SALARY)
       FROM STAFF A JOIN DEPARTMENT D ON A.DEPT = D.DEPT
       GROUP BY D.LABEL ORDER BY D.LABEL
```

## 7. Subqueries

SQLsel supports scalar subqueries, IN, NOT IN, EXISTS, and NOT EXISTS:

```text
SQLSEL SID,NAME FROM STUDENTS S
       WHERE S.SID IN (SELECT E.SID FROM ENROLL E)

SQLSEL SID,NAME FROM STUDENTS S
       WHERE EXISTS (SELECT E.SID FROM ENROLL E WHERE E.SID = S.SID)

SQLSEL SID,NAME FROM STUDENTS S
       WHERE S.SID = (SELECT MAX(SID) FROM STUDENTS WHERE SID < 100)
```

Uncorrelated subqueries are cached. Correlated subqueries are evaluated against
the current outer TupleRow and report the actual evaluation count. Scalar
subqueries must produce at most one row and one column. IN operands must have
compatible types.

A subquery may correlate to a single-table outer query. Correlation against a
joined outer scope is currently refused explicitly.

## 8. INSERT, UPDATE, and DELETE

In native mode, use the SQLSEL prefix:

```text
SQLSEL INSERT INTO STAFF (ID,NAME,SALARY,ACTIVE)
       VALUES (10,'ALPHA',100.00,.T.),(11,'BETA',125.00,.T.)

SQLSEL UPDATE STAFF
       SET NAME = UPPER(NAME), SALARY = SALARY + 5
       WHERE ID = 10

SQLSEL DELETE FROM STAFF WHERE ID = 11
```

INSERT requires an explicit field list. UPDATE and DELETE require an explicit,
nonempty WHERE predicate. This is a safety rule: a whole-table change must be
expressed through a deliberately different house operation, not by omitting a
clause accidentally.

SQLsel validates field type, width, decimals, logical syntax, and date shape
through the same storage gate used by REPLACE. INSERT ends at the existing
`appendBlank()` storage primitive during COMMIT. UPDATE and DELETE likewise use
the existing change flags and commit machinery. SQLsel does not maintain a
second physical write implementation.

DELETE marks matching xBase records deleted. It does not PACK the table.
RECALL can unmark a record according to the normal xBase rules.

Outside an explicit SQL transaction, each DML statement is atomic for its one
target table and commits automatically through TableBuffer and TBJ1 WAL.

## 9. Explicit transactions

Explicit SQL transactions require SQL mode:

```text
SET MODE SQL
BEGIN TRANSACTION
UPDATE STAFF SET SALARY = SALARY + 5 WHERE DEPT = 'ENG'
INSERT INTO STAFF (ID,NAME,SALARY,ACTIVE) VALUES (12,'GAMMA',90.00,.T.)
COMMIT
SET MODE NATIVE
```

Use `ROLLBACK` instead of `COMMIT` to discard the staged changes.

The first DML statement takes the target table fence and opens a private
TableBuffer/TBJ1 scope. Later DML in the transaction reads its own inserts,
updates, and deletes. A SQLsel SELECT issued before COMMIT deliberately remains
a committed-truth view; it does not overlay the pending DML buffer.

The transaction is atomic for one target table. A statement targeting a second
table refuses because x64base does not claim cross-table atomic commit across
DBF, memo, and index stores. Changing out of SQL mode also refuses while a SQL
transaction is active, so native COMMIT cannot bypass SQLsel's state.

If COMMIT cannot clear the buffered work, the transaction remains available
for retry or rollback. A caller-owned table lock remains owned by the caller.

## 10. Blanks, NULL, and memo fields

SQLsel does not add a stored NULL representation to x64base. DBF blanks remain
typed xBase values. This rule is why aggregate blank handling and outer-join
absence are explicit rather than implicit conversions.

In DML, the literal `NULL` refuses with guidance to write an explicit typed
blank instead. Memo-field DML also refuses for now. A memo write can allocate a
separate object, and that store has not joined the DBF WAL atomicity boundary;
claiming one transaction across both would be false.

These are deliberate boundaries, not parser omissions:

| Request | Current result |
|---|---|
| ordinary DBF blank | stored typed blank value |
| outer-join missing side | transient ProducedAbsent / UNKNOWN |
| INSERT or UPDATE with NULL | refused |
| INSERT or UPDATE of memo text | refused in SQLsel DML |
| native REPLACE of memo text | continues through native memo machinery |

## 11. Refusals that protect correctness

Common corrective results include:

- table not open in the current workspace: switch/open the intended workspace;
- ambiguous column: qualify it with the table alias;
- incompatible set columns: align arity and TupleRow types;
- scalar subquery returned more than one row: make it scalar deliberately;
- RIGHT/FULL in a multi-join chain: use a two-table form or materialize a stage;
- second DML target inside one transaction: commit/rollback, then begin another;
- DML NULL or memo field: use a supported typed value/native memo workflow;
- UPDATE or DELETE without WHERE: supply an explicit predicate;
- table-buffer capacity exceeded: reduce the transaction batch;
- lock contention: let the competing owner finish, then retry.

Do not recover from a refusal by weakening the query until it merely runs. Read
the message, preserve the intended semantics, and change the data preparation
or statement shape deliberately.

## 12. Current development capability boundary

| Capability | State |
|---|---|
| typed column and expression projection | implemented |
| WHERE with fail-closed parsing | implemented |
| multi-column ORDER BY and LIMIT | implemented |
| two-table INNER/LEFT/RIGHT/FULL/CROSS | implemented |
| self-join and composite ON | implemented |
| INNER/LEFT/CROSS join chains | implemented |
| RIGHT/FULL inside a join chain | refused |
| outer-join UNKNOWN semantics | implemented |
| CDX-assisted two-table equi-join | implemented and path-reported |
| DISTINCT and UNION/UNION ALL/INTERSECT/EXCEPT | implemented |
| GROUP BY, HAVING, COUNT/SUM/AVG/MIN/MAX | implemented |
| scalar/IN/NOT IN/EXISTS/NOT EXISTS subqueries | implemented |
| correlation to a single-table outer scope | implemented and counted |
| correlation to a joined outer scope | refused |
| INSERT/UPDATE/DELETE | implemented through house write machinery |
| autocommit DML | implemented, one target table |
| BEGIN/COMMIT/ROLLBACK | implemented in SQL mode, one target table |
| duplicate table names in simultaneous workspaces | current-workspace scoped |
| workspace-qualified table syntax | not implemented |
| stored SQL NULL | not present |
| memo-field SQLsel DML | refused pending an atomic store boundary |
| cross-table write atomicity | not claimed |
| cost-based optimizer or EXPLAIN | not implemented |

## 13. Maintainer verification

The SQLsel regression fixtures are executable specifications. Where SQLite can
act as a referee, validators compare marked x64base and SQLite result blocks and
fail closed on missing output. Separate assertions pin access-path reports,
cursor restoration, lock behavior, transaction evidence, and refusal text.

Run the focused gates from a clean enough runtime session:

```text
REGRESSION RUN SQLMODE_SMOKE
REGRESSION RUN SQLSEL_SELECT_V1
REGRESSION RUN SQLSEL_INNER_JOIN
REGRESSION RUN SQLSEL_JOIN_EDGES
REGRESSION RUN SQLSEL_LEFT_JOIN
REGRESSION RUN SQLSEL_JOIN_FAMILY
REGRESSION RUN SQLSEL_SET_OPS
REGRESSION RUN SQLSEL_AGGREGATES
REGRESSION RUN SQLSEL_SUBQUERIES
REGRESSION RUN SQLSEL_ADVANCED_JOIN
REGRESSION RUN SQLSEL_BUFFER_VIS
REGRESSION RUN EVALDIFF
REGRESSION RUN SQLSEL_DML
REGRESSION RUN SQLSEL_WORKSPACE
```

The DML and workspace fixtures are self-erasing. The workspace fixture mints
catalog rows and therefore must run inside the regression catalog bracket, not
as an unguarded copied script.

Parity is not correctness. EVALDIFF pins exact truth-table counts so two
evaluators cannot agree on the same wrong answer and call that green. The JOIN
gates compare row answers and access paths separately. Mutation runs have also
shown that changing an oracle row makes the DML and workspace validators fail.

## Quick working checklist

1. Open every source or target table before entering SQL mode.
2. Switch to the workspace that owns those areas.
3. Use aliases and qualify names in joins.
4. Read fence, access-path, aggregate-blank, subquery-evaluation, and LIMIT
   reports; they are part of the statement evidence.
5. Remember that SELECT sees committed truth, while DML inside one transaction
   reads its own staged writes.
6. Treat `<UNMATCHED>` as produced outer-join absence, not stored NULL.
7. Keep an explicit transaction to one target table.
8. COMMIT or ROLLBACK before leaving SQL mode.
9. Use native REPLACE for memo writes until the memo store shares the SQLsel
   atomicity boundary.
10. Check `SQLSEL HELP` on the exact executable you are running.
