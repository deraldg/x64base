# The Worst Failure Is the One That Returns a Number v0

Status: draft
Audience: developer, maintainer, educator
Registry ID: lesson.career.a_wrong_answer_that_looks_right
Concepts: concept.evidence.review, concept.contract.usage
Proofs: proof.engine.scan_limit_reports_truncation, proof.sqlsel.select_statement_matches_sqlite
Proof state: runtime_observed
Observed: 2026-07-29 (AIF-073 / AIF-074)

## Career Lesson

A crash is a gift. It carries a stack, a line number, and an unambiguous
instruction to go look. It interrupts you at the moment the fault occurs,
which is the cheapest moment there will ever be.

The expensive failure is the other one:

```text
a wrong answer that looks exactly like a right one
```

It raises nothing. It returns a value of the correct type, in the correct
shape, at the correct time. A reader accepts it, writes it into a report, and
the defect propagates outward wearing the costume of a result.

Three defects found in one lane shared this shape. That is what makes it a
lesson rather than an anecdote -- it is a **class**, and classes can be
designed against.

## The Day This Was Measured

### 1. The scan that stopped at its cap and said nothing

A relation scan had an internal limit. When a scan hit that limit it stopped
and returned what it had collected so far, with no indication that it had
stopped early. The partial result was well-formed and plausible. Nothing
distinguished "here are all the matching rows" from "here are the matching
rows I got to before I gave up."

Fixed by making the truncation speak. At limit 1 the run now reports:

```text
REL: scan limit (1) reached; results may be incomplete.
```

exactly once per command. At the restored default the same command is
**silent**. That asymmetry is the entire design: the message exists to mark an
abnormal condition, so emitting it on the normal path would train people to
ignore it. `REL SCANLIMIT` also gave the limit CLI reach for the first time,
so the cap became inspectable rather than folklore.

Recorded as `proof.engine.scan_limit_reports_truncation` (AIF-073, finding
RDB-06).

### 2. The SELECT that scanned 200 records and answered "0"

A `SELECT ... FROM` statement the parser could not read did not report a
syntax error. It scanned 200 records, emitted 200 lines of debug output, and
returned **0 rows**.

Zero is a legitimate answer to a query. That is precisely the problem. A user
reading "0" has no way to tell "no rows matched your predicate" from "I never
understood your predicate." The debug output was noise, not signal -- it
looked like the engine working hard, which made the wrong answer more
convincing rather than less.

After the fix, the same statement over the same data returns row sets equal to
an in-process SQLite oracle: projection, star, `WHERE` and `LIMIT` all match.
Corrective errors now fire for an unopened table, an expression select-item,
and a bad `LIMIT` -- **never a silent wrong answer**.

The before/after pair on identical data is the teaching exhibit, and it is
worth showing students in that order. Recorded as
`proof.sqlsel.select_statement_matches_sqlite` (AIF-074).

### 3. The boolean that stringified to nothing

A proof marker was written by stringifying a boolean. The false case produced
an empty string, so the marker did not read "false" -- it **vanished**. The
transcript looked like a run in which that check had never been reached.

An absent line is the hardest defect to see, because there is nothing on the
page to be suspicious of. The eye has no purchase on a gap.

## The Rule This Produces

The remedy is not more testing. Tests are written by the same person holding
the same assumption, and each of these three defects would have passed a test
that asserted on the returned value.

The remedy is a design rule:

```text
separate the error axis from the value axis
```

A **failure** reports on the error axis. A **legitimate empty result** stays
quiet on it. When both conditions share one channel -- a return value, a
printed line, a stringified flag -- they become indistinguishable, and the
system loses the ability to tell you it is confused.

Practical tests you can apply while writing code:

- If this function cannot do its job, what does the caller see? If the answer
  is "the same thing it sees on an unremarkable success," fix that first.
- Does an abnormal condition produce output that the normal path does not? If
  the message fires on both, it will be ignored on both.
- Can an empty, zero, or blank result mean two different things here? If so,
  they need different channels, not a better comment.

## Ties

- `proof.engine.scan_limit_reports_truncation` -- truncation announces itself.
- `proof.sqlsel.select_statement_matches_sqlite` -- oracle equality, corrective
  errors, and the before/after pair.
- `lesson.career.a_script_never_run_is_not_evidence` -- the companion failure:
  a claim that reads like evidence because nobody executed it.

Owner: `member.derald`.
