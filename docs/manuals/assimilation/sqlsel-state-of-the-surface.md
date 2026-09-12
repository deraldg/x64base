# SQLSEL -- what it is, and what the tree says it is

```yaml
page_id: ASSIM-SQL-01
title: SQLSEL -- state of the surface
audience: assimilation -- a reader or AI arriving cold at this verb
status: DRAFT
last_verified: 2026-09-12
verified_at_commit: 7c4044afb
```

## Why this page exists

SQLSEL is the most capable surface in this tree and the worst described. Three
separate authorities currently assert things about it that stopped being true on
2026-09-09, and none of the mechanical checks can see it, because every one of
them compares COUNTED FACTS and nothing counted moved.

This page is not syntax. `HELP`, `CMDHELP` and `SQLSEL USAGE` own syntax. This
page exists so a reader arriving cold does not believe the catalog.

**If you read only one thing:** the catalog says SQLSEL does bare column names
only, with no joins and no GROUP BY, and that its legacy predicate form is still
accepted. All three clauses are false. Read Part 1, then Part 2.

---

## Part 1 -- the measured surface

Read off the tree at `ae0ad786d`. `src/cli/sqlsel_statement.cpp` is 4,037 lines.

**Reads.** `SELECT` with expression projection and `DISTINCT`. `INNER`, `LEFT`,
`RIGHT`, `FULL` and `CROSS JOIN`. `GROUP BY` with `HAVING`. `ORDER BY` with
`ASC`/`DESC`, applied to the full match set BEFORE `LIMIT`. `UNION`,
`UNION ALL`, `INTERSECT`, `EXCEPT`. `EXISTS` and `NOT EXISTS` subqueries.
`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`.

**Writes.** `INSERT ... VALUES`, `UPDATE ... SET`, `DELETE`. `DELETE` without a
`WHERE` is refused outright.

**Transactions.** `BEGIN [TRANSACTION]`, `COMMIT`, `ROLLBACK`. `BEGIN` requires
`SET MODE SQL`, so a native `COMMIT` cannot bypass the SQL transaction's state.
Since `e44caedbc` a transaction MAY SPAN SEVERAL TABLES: each enlisted member
prepares durably, one group-log row decides all of them, and the apply follows.
A cross-table commit says so in the transcript --
`SQLSEL: N tables committed as ONE decision (group commit).`

**Graded by.** At least nine registered regression specs, most in the default
suite, several comparing result sets against an in-process SQLite oracle over
identical data in the same run: `SQLSEL_SELECT_V1`, `SQLSEL_BUFFER_VIS`,
`SQLSEL_INNER_JOIN`, `SQLSEL_LEFT_JOIN`, `SQLSEL_JOIN_EDGES`,
`SQLSEL_JOIN_FAMILY`, `SQLSEL_SET_OPS`, `SQLSEL_AGGREGATES`, `SQLSEL_DML`.

That is a SQL engine, not a query helper.

## Part 2 -- three authorities carrying a dead claim

On 2026-09-09 the owner ruled (a) on AIF-074 and `1a96dac9b` landed it:
`cmd_sql_select.cpp` went from 618 lines to 225. The legacy predicate scan --
its private `DelMode`, its `include_row()` policy, its raw
`do { ... } while (A.skip(+1) ...)` walk -- was DELETED. The verb now has one
path, and answers a non-statement with a corrective error naming `COUNT`.

The file says so itself, in its own usage contract:

>     The legacy predicate form was RETIRED 2026-09-09 (AIF-074, owner ruling).
>       COUNT carries that job -- COUNT FOR <expr>, COUNT LIST, COUNT VERBOSE.

Three other authorities carried the dead claim. Two are now corrected; one is
not.

1. **The DOTREF catalog summary -- STILL WRONG.** It is what `CMDHELP` prints
   and what any reader browsing commands sees first:

   > Bare column names only in v1 (no expression projection, joins, or GROUP
   > BY). The legacy predicate-scan form SQLSEL [COUNT] [FOR <expr>] is still
   > accepted.

   Both halves false. The first describes a v1 that has not existed since the
   join and aggregate work landed; the second describes a form that was
   deleted. It lives behind `src/cli/cmdhelp.cpp`.

2. **`SQLSEL_SELECT_V1`'s registry blurb -- CORRECTED at `7c4044afb`.** It
   ended *"Legacy predicate form preserved."* for three days after the
   deletion, and NOTHING WENT RED, because the spec never exercised the retired
   form. A spec summary is PROSE sitting inside a C++ array of specs, and
   proximity to executable claims does not make it one. The corrected text
   records the three days rather than quietly reading true.

3. **The public site -- WAS ALREADY CORRECT, and this page said otherwise.**
   `products/sqlsel.mdx` points at `COUNT`; `sqlsel-and-sql-conformance.mdx`
   states the retirement in the past tense. The site-artifacts advisory that
   describes four stale sentences is describing a failure ALREADY FOUND AND
   FIXED -- it reads like a live report and is not one. An earlier revision of
   this page asserted it as live. Recorded here rather than quietly deleted,
   because misreading a historical note as a live one is the same error class
   this page is about.

**WHY NO INSTRUMENT SEES A RETIREMENT.** The freshness checks compare exact
values, and the shipped-capability sweep reads a list of WHAT SHIPS and looks
for shipped things described as planned or missing. A RETIREMENT is the
opposite polarity: a page asserting a REMOVED surface has no entry to match
against. A removal reaches code immediately and prose only when a person
carries it.

**AND THE OTHER POLARITY FAILED TOO, FOR A DIFFERENT REASON.** Cross-table
atomic commit shipped 2026-09-11 and SIX statements across three site pages
denied it -- a shipped capability described as missing, which is precisely what
the sweep exists to catch. It reported `0 flag, 0 review` and was right to: its
authority is generated from `kRegressionSpecs`, and this capability's arms are
`SQLSEL_DML` plus two HAND-DISPATCHED ops, `GRPFAIL` and `GRPNATIVE`, which
could not be named. The sweep was comparing pages against a list that had never
heard of the capability. Fixed at `c85d9428b` (prose), `2980a74e6` (the
generator now accepts an explicit-run op as an arm) and `a7c7935e7` (regenerated
authority).

So both polarities have now failed within a week, for unrelated reasons, and
neither failure moved a counted fact.

## Part 3 -- the boundary that must not be blurred

SQLSEL is STATEMENT-SCOPED by ruling. It names its own table in the statement,
ignores session filter and cursor state on every read path, restores every
cursor it moves, and reads COMMITTED table truth -- not the dirty table buffer.
`SQLSEL_BUFFER_VIS` is the arm that holds that line: `TUPLE` previews the dirty
current-row buffer while SQLSEL reads committed truth, and the split is graded
against an oracle.

**SQLSEL's JOIN declares its own `ON` per statement. It does NOT consult `REL`
or the workspace relation graph.**

That matters for what may be claimed. This tree's strongest correctness result
is that TWO INDEPENDENT WALKERS agreed over ONE DECLARED relation graph --
`SET RELATION` navigation and a second route -- to the record, over a 34-table
schema with 58 foreign-key relations. SQLSEL JOIN is NOT a third walker over
that graph. It is an independent join path that happens to be able to express
the same question.

Do say: SQLSEL has an oracle-checked join family. Do NOT extend the
two-walkers-over-one-declared-graph claim to it, and do not merge it with
`REL JOIN` in a sentence.

## Part 4 -- what the transaction actually does

Worth knowing before you reason about failure.

**The record lock is taken when SQLSEL STAGES a change, not when the commit
applies it.** A lock already held when the statement runs is caught by
fail-fast -- `SQLSEL: UPDATE refused -- record locked` -- the table never
enlists, and no group is ever decided. That is the refuse-on-contention
contract working as ruled.

**Teardown closes the journal handle.** `release_sql_transaction` walks its
enlistments in reverse enlistment order into `journal_note_rollback`, which
refuses to delete a journal whose group already decided AND closes its handle.
The consequence is not obvious and was measured on 2026-09-12: after a SQLSEL
transaction, a retry `COMMIT` writes nothing, because `journal_begin_commit`
returns early on a null `FILE*`. The equivalent retry after `GROUPCOMMIT` --
which has no teardown at all -- reaches a LIVE handle. The two verbs differ in
exactly that, and `REGRESSION GRPNATIVE` is the arm that measures it.

## Part 5 -- what is thin, stated rather than implied

- The `X1` block is EYEBALLED, not oracle-compared. A SQLite twin for `SQLDML2`
  would close it.
- `sqlsel_statement.cpp:3365` sets buffer persistence DIRECTLY, past the
  guarded surface every other caller goes through.
- A standing finding records that SQLSEL infers commit success from an empty
  buffer.
- 4,037 lines behind one verb, with nine specs pointed at it.

## Part 6 -- how to prove this page is stale

This page describes a surface that moves. Do not trust its date; run the check.

    git log --oneline -5 -- src/cli/sqlsel_statement.cpp \
                            src/cli/cmd_sql_select.cpp

If anything lands after `ae0ad786d`, Part 1 is a claim rather than a reading.
Then:

    git grep -c "@dottalk.usage v1" -- src/cli/cmd_sql_select.cpp
    git grep -n "legacy predicate" -- src/cli/ docs/

The second is the specific test for Part 2. As of `7c4044afb` the expected hits
are `cmd_sql_select.cpp`'s own retirement note, `cmd_regression.cpp`'s corrected
blurb, and this page. **Anything else is a fourth authority nobody has found
yet.** The DOTREF summary will not appear in that grep -- it does not use the
phrase -- so check it directly:

    git grep -n "predicate-scan form" -- src/cli/cmdhelp.cpp

When that returns nothing, Part 2 item 1 is closed and the whole section should
be rewritten as history rather than as a live defect.

**THE CHECK IS THE POINT.** Part 2 exists because three authorities drifted for
days with every gate green. A page that cannot tell you how to falsify it is
the fourth.

---

Ships review-needed. The author does not self-approve.
