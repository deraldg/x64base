# Command contract inventory, 2026-09-06 to 2026-09-13 -- snapshot V1

    report_id : AIPR-20260913-001
    produced  : 2026-09-13, Claude (Cowork), as an interactive HTML artifact
    source    : https://claude.ai/artifact/QUKdiqxZcEJsYbosy3BxQN (private to the owner;
                this file is the portal copy and is readable without it)
    added     : 2026-09-21, owner instruction: "add this report to the ai portal"
    verified  : 2026-09-21 against git at dbb6aad57 -- see "Read this first"
    status    : SNAPSHOT. Each command's own @dottalk.usage block is authoritative;
                this is a dated reading of those blocks, not a second source for them.

Every `src/cli/cmd_*.cpp` whose source moved in the seven days to 2026-09-13, with
its `@dottalk.usage v1` block read straight out of the file. Usage forms and examples
are verbatim as they stood that day. Sorted newest first.

## Read this first -- what verification changed

The report's own footer said: *re-cut this against `git log --since` before treating
it as complete.* Adding it to the portal is treating it as a reference, so that was
done first. Four results.

**1. THE SNAPSHOT IS INCOMPLETE BY THREE FILES.** Git shows 26 command files with
commits in the window; all 23 listed here are confirmed, and three are missing:
`cmd_buildlmdb.cpp` (`403cb4072`, 2026-09-06), `cmd_workspace.cpp` (`7f9bc25db`,
2026-09-06) and `cmd_calcwrite.cpp` (`13fbb06c6`, 2026-09-07) -- all committed days
before the report was generated. The report selected by file modification time, and
said in its own footer that mtime is a proxy for git history and not a substitute.
This is that caveat, measured. The three are listed at the end, in their own section,
rather than folded into the snapshot.

**2. THREE ROWS ARE NOW STALE.** `SQLHELP`, `INSERT` and `UPDATE` were `experimental`
on 2026-09-13 and are `supported` at HEAD. So the snapshot's "6 not supported" is
3 of 23 today: `SETPATH` (implementation-helper), `SET LMDB` (developer), `WORKDESK`
(experimental).

**3. EIGHT OF THE 26 FILES HAVE COMMITS SINCE THE SNAPSHOT** -- `REGRESSION` (5),
`COMMIT` (3), `INSERT` (3), `USE` (2), `SQLHELP` (2), `cmd_workspace.cpp` (2), `INIT`
(1), `UPDATE` (1). Their verbatim usage below may no longer match the source. They are
marked **CHANGED SINCE** in the table. Read the file, not this page, for those.

**4. THE GAPS THE REPORT NAMED ARE STILL TRUE AT HEAD.**

- `SET ORDER`, `SET LMDB` and `SET UNIQUE` still carry `@dottalk.usage.voluntary`
  -- offered, not promised -- and still cannot be documented as contract without a
  ruling.
- 13 of the 23 still declare usage forms and no worked example; with the three missing
  files added, it is 15 of 26.
- `lane:` is empty in the `@dottalk.file v1` header of **26 of 26** files; `owns:` is
  empty in 25 of 26.

**AN INSTRUMENT NOTE, because it nearly inverted point 4.** The verifier's first draft
reported `lane:` empty in 0 of 26. Its regex used `\s*` after `lane:`, which matches a
newline, so an empty field captured the NEXT header line as its value. It was caught
by running it against a known positive -- `cmd_version.cpp`, whose empty `lane:` had
been printed on screen minutes earlier -- and fixed to `[ \t]*`. The same parser
reproduced 20 of the 23 snapshot rows exactly, and the three it did not are the three
in point 2; that agreement is what the drift finding rests on.

## Headline numbers

| | as recorded 2026-09-13 | at HEAD `dbb6aad57`, 2026-09-21 |
| --- | --- | --- |
| command files in the window | 23 | **26** (three missed by the mtime cut) |
| under `@dottalk.usage v1` | 20 | 23 of 26 |
| voluntary -- not promised | 3 | 3 |
| no worked example | 13 | 13 of the 23; 15 of 26 |
| not `supported` | 6 | **3** |
| empty `lane:` | all | 26 of 26 |
| empty `owns:` | 22 of 23 | 25 of 26 |

## The inventory, as recorded

| command | file | moved | status then | status now | contract | example | since |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `REGRESSION` | `cmd_regression.cpp` | 2026-09-13 | supported | supported | usage v1 | yes | **CHANGED SINCE** (5) |
| `COMMIT` | `cmd_commit.cpp` | 2026-09-12 | supported | supported | usage v1 | **none** | **CHANGED SINCE** (3) |
| `INIT` | `cmd_init.cpp` | 2026-09-11 | supported | supported | usage v1 | **none** | **CHANGED SINCE** (1) |
| `SETPATH` | `cmd_setpath.cpp` | 2026-09-11 | implementation-helper | implementation-helper | usage v1 | **none** | -- |
| `VERSION` | `cmd_version.cpp` | 2026-09-11 | supported | supported | usage v1 | **none** | -- |
| `CDX` | `cmd_cdx.cpp` | 2026-09-10 | supported | supported | usage v1 | **none** | -- |
| `SETLMDB` | `cmd_setlmdb.cpp` | 2026-09-10 | developer | developer | voluntary | **none** | -- |
| `SETORDER` | `cmd_setorder.cpp` | 2026-09-10 | supported | supported | voluntary | **none** | -- |
| `USE` | `cmd_use.cpp` | 2026-09-10 | supported | supported | usage v1 | **none** | **CHANGED SINCE** (2) |
| `SELECT` | `cmd_select.cpp` | 2026-09-10 | supported | supported | usage v1 | **none** | -- |
| `WORKDESK` | `cmd_workdesk.cpp` | 2026-09-10 | experimental | experimental | usage v1 | **none** | -- |
| `WSREPORT` | `cmd_wsreport.cpp` | 2026-09-10 | supported | supported | usage v1 | **none** | -- |
| `ROLLBACK` | `cmd_rollback.cpp` | 2026-09-10 | supported | supported | usage v1 | yes | -- |
| `SQLSEL` | `cmd_sql_select.cpp` | 2026-09-10 | supported | supported | usage v1 | yes | -- |
| `SORT` | `cmd_sort.cpp` | 2026-09-09 | supported | supported | usage v1 | **none** | -- |
| `COPY` | `cmd_copy.cpp` | 2026-09-09 | supported | supported | usage v1 | yes | -- |
| `SQLHELP` | `cmd_sql_help.cpp` | 2026-09-08 | experimental | **supported** | usage v1 | yes | **CHANGED SINCE** (2) |
| `INSERT` | `cmd_sql_insert.cpp` | 2026-09-07 | experimental | **supported** | usage v1 | yes | **CHANGED SINCE** (3) |
| `UPDATE` | `cmd_sql_update.cpp` | 2026-09-07 | experimental | **supported** | usage v1 | yes | **CHANGED SINCE** (1) |
| `ERASE` | `cmd_erase.cpp` | 2026-09-07 | supported | supported | usage v1 | yes | -- |
| `REPLACE` | `cmd_replace.cpp` | 2026-09-07 | supported | supported | usage v1 | yes | -- |
| `MULTIREP` | `cmd_replace_multi.cpp` | 2026-09-07 | supported | supported | usage v1 | yes | -- |
| `SETUNIQUE` | `cmd_setunique.cpp` | 2026-09-07 | supported | supported | voluntary | **none** | -- |

## Per command, verbatim as of 2026-09-13

### REGRESSION

`cmd_regression.cpp` -- 2026-09-13 -- `supported` -- `@dottalk.usage v1`. **CHANGED SINCE: 5 commit(s) after the snapshot -- read the source.**

Launch curated DotTalk++ regression and smoke DotScript files through the normal DOTSCRIPT runner so regression entrypoints stay discoverable and consistent.

category `test` / effect `execute` / usage-access `REGRESSION USAGE` / mutates `delegates regression scripts session data filesystem log transcript`

Usage:

```text
REGRESSION USAGE
REGRESSION LIST
REGRESSION FIND <words...>
REGRESSION SEARCH <words...>
REGRESSION SHOW <name>
REGRESSION RUN <name> [LOG [<path>]]
REGRESSION <name> [LOG [<path>]]
REGRESSION ALL [LOG [<path>]]
REGRESSION TRIGGERVETO [NORMAL|SELFTEST|MULTIREP|AFTER|RECOVERY]
REGRESSION GRPNATIVE
REGRESSION GRPFAIL
REGRESSION GRPMINT
REGRESSION FIXTURECHECK
```

Examples:

```text
REGRESSION LIST
REGRESSION SHOW NONDESTRUCTIVE
REGRESSION RUN INDEX_X32
REGRESSION RUN X64_METRICS
REGRESSION RUN HARVEST
REGRESSION CURSOR
REGRESSION ALL
REGRESSION ALL LOG
REGRESSION ALL LOG tmp\suite_20260913.log
REGRESSION RUN NULLASSERT LOG
REGRESSION GRPMINT
REGRESSION FIXTURECHECK
```

### COMMIT

`cmd_commit.cpp` -- 2026-09-12 -- `supported` -- `@dottalk.usage v1`. **CHANGED SINCE: 3 commit(s) after the snapshot -- read the source.**

Apply buffered TABLE changes to the current area or all open buffered areas, locking records at commit time and reporting persistence-stage failures.

category `data` / effect `commit` / usage-access `COMMIT USAGE` / mutates `table-data table-buffer memo stale-state index journal`

Usage:

```text
COMMIT USAGE
COMMIT
COMMIT ALL
COMMIT MANUAL
COMMIT INTERACTIVE
COMMIT AUTO
COMMIT ALL MANUAL
COMMIT ALL INTERACTIVE
COMMIT ALL AUTO
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### INIT

`cmd_init.cpp` -- 2026-09-11 -- `supported` -- `@dottalk.usage v1`. **CHANGED SINCE: 1 commit(s) after the snapshot -- read the source.**

Initialize runtime paths, cleanup stale locks, and run system/user init scripts from the executable directory.

category `script` / effect `initialize` / usage-access `INIT USAGE` / mutates `path-state lock-state delegates-command-effects`

Usage:

```text
INIT
INIT USAGE
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### SETPATH

`cmd_setpath.cpp` -- 2026-09-11 -- `implementation-helper` -- `@dottalk.usage v1`.

Path-slot support implementation used by SETPATH and related commands.

category `environment-helper` / effect `path-slot-support` / usage-access `owned-by cmd_setpath_command.cpp` / mutates `path-slots-through-api`

Usage:

```text
This file does not export cmd_SETPATH.
Runtime SETPATH usage is owned by the command handler in cmd_setpath_command.cpp.
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### VERSION

`cmd_version.cpp` -- 2026-09-11 -- `supported` -- `@dottalk.usage v1`.

Report the DotTalk++ version label and build date/time.

category `report` / effect `report` / usage-access `VERSION USAGE` / mutates `none`

Usage:

```text
VERSION
VERSION USAGE
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### CDX

`cmd_cdx.cpp` -- 2026-09-10 -- `supported` -- `@dottalk.usage v1`.

Manage CDX index container metadata: create containers, inspect header/tag directories, add tags, and drop tags.

category `index` / effect `mixed` / usage-access `CDX USAGE` / mutates `index-metadata filesystem`

Usage:

```text
CDX USAGE
CDX INFO [<path.cdx>]
CDX TAGS [<path.cdx>]
CDX CREATE [<path.cdx>]
CDX ADDTAG <name> [<path.cdx>]
CDX DROPTAG <name> [<path.cdx>]
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### SETLMDB

`cmd_setlmdb.cpp` -- 2026-09-10 -- `developer` -- **voluntary -- not under contract**.

Select LMDB-backed CDX ordering per area without touching global LMDB state.

category `index` / effect `configure` / usage-access `SET LMDB USAGE` / mutates `order-state index-backend`

Usage:

```text
SET LMDB
SET LMDB USAGE
SET LMDB 0
SET LMDB <stem>
SET LMDB <container.cdx>
SET LMDB <envdir.cdx.d>
SET LMDB <stem> <tag>
SET LMDB <stem> <tag> --asc
SET LMDB <stem> <tag> --desc
SETLMDB
SETLMDB USAGE
SETLMDB 0
SETLMDB <stem> <tag>
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### SETORDER

`cmd_setorder.cpp` -- 2026-09-10 -- `supported` -- **voluntary -- not under contract**.

FoxPro-style SET ORDER command with CNX and CDX-aware tag activation.

category `index` / effect `configure` / usage-access `SET ORDER USAGE` / mutates `order-state index-backend cursor`

Usage:

```text
SET ORDER
SET ORDER USAGE
SET ORDER 0
SET ORDER PHYSICAL
SET ORDER NATURAL
SET ORDER PHYS
SET ORDER <tag>
SET ORDER TAG <tag>
SET ORDER TAG <tag> IN <alias>
SET ORDER <container> <tag>
SET ORDER <container> <tag> ASC
SET ORDER <container> <tag> DESC
SETORDER
SETORDER USAGE
SETORDER <tag>
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### USE

`cmd_use.cpp` -- 2026-09-10 -- `supported` -- `@dottalk.usage v1`. **CHANGED SINCE: 2 commit(s) after the snapshot -- read the source.**

Open a DBF table into the current work area, with duplicate-open guard, memo auto-attach, optional index auto-attach, and NOINDEX physical-order mode.

category `workspace` / effect `session` / usage-access `USE USAGE` / mutates `session area order memo index`

Usage:

```text
USE USAGE
USE <table>
USE <table.dbf>
USE <path\table.dbf>
USE <table> NOINDEX
USE <table> NOIDX
USE <table> AGAIN
USE <table> IN <n>
USE <table> IN FREE
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### SELECT

`cmd_select.cpp` -- 2026-09-10 -- `supported` -- `@dottalk.usage v1`.

Select the current work area by numeric slot or by work-area/table name.

category `workspace` / effect `select` / usage-access `SELECT USAGE` / mutates `current-area`

Usage:

```text
SELECT USAGE
SELECT <n>
SELECT <name>
SELECT <table.dbf>
SELECT <workspace>:<name>
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### WORKDESK

`cmd_workdesk.cpp` -- 2026-09-10 -- `experimental` -- `@dottalk.usage v1`.

Report the desk -- every open workspace in this session with its areas, identity, lineage and roots.

category `diagnostics` / effect `report` / usage-access `WORKDESK USAGE` / mutates `none`

Usage:

```text
WORKDESK
WORKDESK USAGE
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### WSREPORT

`cmd_wsreport.cpp` -- 2026-09-10 -- `supported` -- `@dottalk.usage v1`.

Print a session status report: open workspaces and their areas, the order/LMDB summary, table-buffer state, and per-area index detail.

category `diagnostics` / effect `report` / usage-access `WSREPORT USAGE` / mutates `none`

Usage:

```text
WSREPORT
WSREPORT USAGE
WSREPORT ALL
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### ROLLBACK

`cmd_rollback.cpp` -- 2026-09-10 -- `supported` -- `@dottalk.usage v1`.

Discard buffered/uncommitted table changes for the current area or all areas.

category `table-buffer` / effect `discard-buffered-changes` / usage-access `ROLLBACK USAGE` / mutates `buffer-state dirty-stale-flags journal`

Usage:

```text
ROLLBACK USAGE
ROLLBACK
ROLLBACK ALL
```

Examples:

```text
ROLLBACK
ROLLBACK ALL
```

### SQLSEL

`cmd_sql_select.cpp` -- 2026-09-10 -- `supported` -- `@dottalk.usage v1`.

Typed set-oriented SELECT and DML over open x64base work areas.

category `sql` / effect `query` / usage-access `SQLSEL USAGE` / mutates `cursor-temporary`

Usage:

```text
SQLSEL USAGE
SQLSEL [SELECT] [DISTINCT] <list> FROM <source> [WHERE <predicate>]
[GROUP BY <list>] [HAVING <predicate>]
[ORDER BY <item>[,<item>...]] [LIMIT <n>]
SQLSEL <select> UNION [ALL] <select> | <select> INTERSECT <select> | <select> EXCEPT <select>
SQLSEL INSERT INTO <table> (<fields>) VALUES (<values>)[,(<values>)...]
SQLSEL UPDATE <table> [[AS] <alias>] SET <field>=<expr>[,...] WHERE <predicate>
SQLSEL DELETE FROM <table> [[AS] <alias>] WHERE <predicate>
```

Examples:

```text
SQLSEL SID,LNAME,FNAME FROM STUDENTS
SQLSEL * FROM STUDENTS LIMIT 5
SQLSEL SID,LNAME FROM STUDENTS WHERE MAJOR = "CSCI"
SQLSEL SID,LNAME FROM STUDENTS ORDER BY LNAME DESC LIMIT 10
SQLSEL COUNT(*) FROM STUDENTS WHERE GPA >= 3.0
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S LEFT JOIN ENROLL E ON S.SID = E.SID
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S RIGHT JOIN ENROLL E ON S.SID = E.SID
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S FULL JOIN ENROLL E ON S.SID = E.SID
SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S CROSS JOIN ENROLL E
SQLSEL DEPT,COUNT(*),AVG(SALARY) FROM STAFF GROUP BY DEPT
SQLSEL SID FROM STUDENTS UNION SELECT SID FROM ALUMNI
SQLSEL SID FROM STUDENTS S WHERE EXISTS (SELECT SID FROM ENROLL E WHERE E.SID=S.SID)
SQLSEL INSERT INTO STUDENTS (SID,LNAME) VALUES (9,'SMITH')
SQLSEL UPDATE STUDENTS SET LNAME=UPPER(LNAME) WHERE SID=9
SQLSEL DELETE FROM STUDENTS WHERE SID=9
```

### SORT

`cmd_sort.cpp` -- 2026-09-09 -- `supported` -- `@dottalk.usage v1`.

Create a sorted DBF copy from the current table using expression keys, optional filters, projection fields, deleted-record selection, and UNIQUE.

category `data` / effect `create` / usage-access `SORT USAGE` / mutates `filesystem dbf-output cursor`

Usage:

```text
SORT USAGE
SORT TO <outdbf> ON <expr>
SORT TO <outdbf> ON <expr> ASC
SORT TO <outdbf> ON <expr> DESC
SORT TO <outdbf> ON <expr>, <expr>
SORT ALL TO <outdbf> ON <expr>
SORT DELETED TO <outdbf> ON <expr>
SORT OVERWRITE TO <outdbf> ON <expr>
SORT TO <outdbf> ON <expr> FOR <expr>
SORT TO <outdbf> ON <expr> WHILE <expr>
SORT TO <outdbf> ON <expr> FIELDS <fieldlist>
SORT TO <outdbf> ON <expr> UNIQUE
SORT TO <outdbf> ON <expr> KEY DROP
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

### COPY

`cmd_copy.cpp` -- 2026-09-09 -- `supported` -- `@dottalk.usage v1`.

Copy the current DBF, convert the current table to a target DBF flavor, or copy a filesystem file.

category `file-table` / effect `copy-or-convert` / usage-access `COPY USAGE` / mutates `filesystem`

Usage:

```text
COPY USAGE
COPY TO <DBFNAME> [WITH SIDECARS] [OVERWRITE]
COPY TO <DBFNAME> AS <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> [KEY DROP] [OVERWRITE]
COPY TO <DBFNAME> AS X64 VECTOR [KEY DROP] [OVERWRITE]
COPY FILE <SRC> TO <DST> [OVERWRITE]
```

Examples:

```text
COPY TO students_copy
COPY TO students_x64 AS X64 VECTOR OVERWRITE
COPY TO students_vfp AS VFP
COPY TO students_backup WITH SIDECARS OVERWRITE
COPY FILE source.txt TO tmp\source_copy.txt OVERWRITE
```

### SQLHELP

`cmd_sql_help.cpp` -- 2026-09-08 -- `experimental` -- `@dottalk.usage v1`. **CHANGED SINCE: 2 commit(s) after the snapshot -- read the source.** Status is now `supported`.

Display or search the SQL helper/reference catalog.

category `reference` / effect `report` / usage-access `SQLHELP USAGE` / mutates `none`

Usage:

```text
SQLHELP
SQLHELP USAGE
SQLHELP LIST-CATEGORIES
SQLHELP <category>
SQLHELP <term>
```

Examples:

```text
SQLHELP
SQLHELP INDEXING
SQLHELP CREATE-INDEX
SQLHELP LIST-CATEGORIES
```

### INSERT

`cmd_sql_insert.cpp` -- 2026-09-07 -- `experimental` -- `@dottalk.usage v1`. **CHANGED SINCE: 3 commit(s) after the snapshot -- read the source.** Status is now `supported`.

Insert a new record into the current DBF work area using SQL-like syntax.

category `sql` / effect `insert-record` / usage-access `INSERT USAGE` / mutates `table-data`

Usage:

```text
INSERT USAGE
INSERT (<field-list>) VALUES (<value-list>)
INSERT <field>=<value> [, <field>=<value> ...]
```

Examples:

```text
INSERT (SID,LNAME,FNAME) VALUES (999,"SMITH","JANE")
INSERT SID=999, LNAME="SMITH", FNAME="JANE"
```

### UPDATE

`cmd_sql_update.cpp` -- 2026-09-07 -- `experimental` -- `@dottalk.usage v1`. **CHANGED SINCE: 1 commit(s) after the snapshot -- read the source.** Status is now `supported`.

Update records in the current DBF work area using SQL-like SET/WHERE syntax.

category `sql` / effect `update-records` / usage-access `UPDATE USAGE` / mutates `table-data`

Usage:

```text
UPDATE USAGE
UPDATE SET <field>=<value>[, ...] [WHERE <expr>]
```

Examples:

```text
UPDATE SET GPA=3.5 WHERE SID = 1001
UPDATE SET MAJOR="CSCI" WHERE MAJOR = "CS"
```

### ERASE

`cmd_erase.cpp` -- 2026-09-07 -- `supported` -- `@dottalk.usage v1`.

Physically delete a DBF table file plus known same-stem sidecars across DBF, INDEXES, and LMDB roots.

category `destructive-file` / effect `delete-table-files` / usage-access `ERASE USAGE` / mutates `filesystem`

Usage:

```text
ERASE USAGE
ERASE <table> [CONFIRM]
ERASE TABLE <table> [CONFIRM]
ERASE DIR <path> [CONFIRM]
```

Examples:

```text
ERASE TABLE clients
ERASE TABLE clients CONFIRM
ERASE students.dbf CONFIRM
ERASE DIR DBF\wbregress CONFIRM
```

### REPLACE

`cmd_replace.cpp` -- 2026-09-07 -- `supported` -- `@dottalk.usage v1`.

Replace one field in the current record by field name or field index, preserving RHS expression evaluation, type validation, memo conversion, and table-buffer semantics.

category `data` / effect `mutate` / usage-access `REPLACE USAGE` / mutates `table-data table-buffer memo stale-state index`

Usage:

```text
REPLACE USAGE
REPLACE <field_index> WITH <value>
REPLACE <field_name> WITH <value>
REPLACE <field_index|field_name> WITH NULL
REPLACE <field_index|field_name> WITH .NULL.
```

Examples:

```text
REPLACE LNAME WITH "Smith"
REPLACE 3 WITH TODAY
REPLACE NOTES WITH "updated memo text"
REPLACE VNAME WITH NULL
```

### MULTIREP

`cmd_replace_multi.cpp` -- 2026-09-07 -- `supported` -- `@dottalk.usage v1`.

Replace multiple fields in the current record with one record lock and one physical write, preserving RHS evaluation, validation, memo handling, and direct index maintenance.

category `data` / effect `mutate` / usage-access `MULTIREP USAGE` / mutates `table-data memo index stale-state`

Usage:

```text
MULTIREP <field> WITH <value>[, <field> WITH <value>]...
```

Examples:

```text
MULTIREP LNAME WITH "Smith", FNAME WITH "John"
MULTIREP DOB WITH 20000101, ACTIVE WITH .T.
```

### SETUNIQUE

`cmd_setunique.cpp` -- 2026-09-07 -- `supported` -- **voluntary -- not under contract**.

Report or configure per-table unique-field registry entries.

category `constraints` / effect `configure` / usage-access `SET UNIQUE USAGE` / mutates `unique-field-registry`

Usage:

```text
SET UNIQUE
SET UNIQUE USAGE
SET UNIQUE FIELD <name> ON
SET UNIQUE FIELD <name> OFF
```

Examples: **none in the contract.** Usage forms only -- a reader gets the shape and not a line they can type.

## Missing from the snapshot -- found by the git re-cut, 2026-09-21

Not in the original report. Recorded here so the population is complete; their usage
was not captured on 2026-09-13 and is not reconstructed -- read the source.

| file | commit in the window | status at HEAD | contract | example at HEAD | since |
| --- | --- | --- | --- | --- | --- |
| `cmd_buildlmdb.cpp` | `403cb4072` 2026-09-06, AIF-157 | supported | usage v1 | **none** | -- |
| `cmd_workspace.cpp` | `7f9bc25db` 2026-09-06 | supported | usage v1 | **none** | **CHANGED SINCE** (2) |
| `cmd_calcwrite.cpp` | `13fbb06c6` 2026-09-07, AIF-156 | supported | usage v1 | yes | -- |

## How the original was built -- its own words, kept

File modification times under `D:\code\ccode\src\cli`, cut at 2026-09-06 00:00 UTC,
then each file's contract header parsed. **mtime is a proxy for git history, not a
substitute:** it counts any write, including three by the author to `cmd_regression.cpp`
that day, and it would miss a command whose behaviour changed from an edit to a file it
depends on. For the documentation push, re-cut this against `git log --since` before
treating it as complete.

It is a better instruction than it looks: it predicted the one defect verification
found. Two misses of the kind it names are possible and only one was measured -- files
committed in the window but written before it (the three above), and commands whose
BEHAVIOUR moved through a dependency. The second is not measured here and a file-level
re-cut cannot measure it.
