# A Script That Has Never Been Run Is Not Evidence v0

Status: draft
Audience: developer, maintainer, technical writer, ai_partner
Registry ID: lesson.career.a_script_never_run_is_not_evidence
Observed: 2026-07-26 (run COWORK-20260726-001)

## Career Lesson

Its companion lesson, `lesson.career.proof_first_development`, says: make the
system leave a trail that documentation can trust.

This lesson is the sharp edge of that idea:

```text
a claim is evidence only when a transcript exists
```

A script that has never been executed is not a weaker proof. It is not a proof
at all. It is a wish written in the imperative mood, and it reads exactly like
the real thing.

## The Day This Was Measured

One session, 2026-07-26. Nearly every defect found that day was found by
EXECUTING something that had only ever been WRITTEN. None were visible to
careful reading, and several sat inside artifacts already cited as evidence.

### 1. The test suite that could not run

`tests/conversion/` was cited by the PDLC maturity review as evidence that
"DBF/xBase and CSV conversion" was empirically demonstrated. All five scripts
were unrunnable:

- `EXPORT ... DELIMITER , QUOTES RFC4180` -- those options do not exist
- `IMPORT ... SCHEMA <json> REJECTS <csv>` -- IMPORT takes only `<csvfile>`
- `SQLITE QUERY "..." INTO DBF` -- no QUERY subcommand, no INTO-DBF path
- `BEGIN` -- not a registered command
- all five wrote to `_drops/`, a directory that does not exist

They were not stale. They were **aspirational** -- written against the syntax
someone wished the engine had. Reading them looked like evidence. Running one
produced a usage error on line 2.

### 2. The hop blamed on a missing toolchain

The COBOL hop was graded "runtime-capable, proof incomplete", attributed to an
absent GnuCOBOL transcript. GnuCOBOL was installed the whole time. Running the
hop exposed the actual blockers:

- `COBOL BUILD` appends `.exe` on Windows; `COBOL RUN` did a bare
  `fs::exists()` with no fallback -- so the documented BUILD-then-RUN sequence
  could not work *immediately after a successful BUILD*
- the sample program's `ASSIGN` named a path nothing had ever written to, so
  `OPEN INPUT` failed with libcob status 35 right after a successful export

Two latent defects, invisible for as long as nobody ran the thing. The
diagnosis "we lack a transcript" was correct; the attributed cause was not.

### 3. The number that would have destroyed data

A coverage generator read a 40-row CSV snapshot and reported 14.9% coverage.
The canonical table held 203 rows; the true figure was 78.4%. Acting on the
low number -- seeding the "missing" rows -- would have ERASED 15 live rows
that were deliberate maintainer decisions.

A coverage metric is only as canonical as its input. Verify which artifact a
tool actually reads before acting on its number.

### 4. Gates green, artifacts disagreeing

- Gate 4 recorded PASS at 191 pages / 26 parts / 14,542 lines. Its own
  preserved assembly report says 183 / 23 / 13,879.
- The published PDF predates by 3h35m the assembly it is evidence for.
- Two divergent shadow HELP sets sit where a tool given the wrong root
  consumes months-old data and reports success.

A stage can report green while its inputs or outputs belong to a different
build entirely.

## The Corollary: the author is not exempt

The same session, the same failure mode, committed by the agent writing the
proofs:

- **Invented expected values.** A NULL count and a cost sum were written
  because they looked plausible rather than computed. Both were wrong. Had
  they shipped, a CORRECT conversion would have appeared to fail.
- **An asserted distinction never checked.** A record length was declared
  "not the DBF's 109" when it was exactly 109 plus CRLF -- on the very line
  meant to be the fidelity proof.
- **A flag read and not applied.** Fixed-format comments were added to a
  free-format COBOL source *after* the `-free` compile flag had already been
  read, turning a clean build into ~60 syntax errors.

Every one was caught by running, none by re-reading.

## The Rules

1. **A claim is evidence only if a transcript exists.** Capability and proof
   are different states. Say which one you have.
2. **Expected values must be DERIVED** -- from the code, or from sealed and
   checksummed data. Never written because they look plausible.
3. **Check which artifact produced a number** before acting on it.
4. **Running the proof is not the last step of documenting a capability.** It
   is the step that finds out whether the capability is real.
5. **A refusal that explains itself beats a silent success.** Where a
   conversion declined with a clear message, that was better engineering than
   a lossy write that reported OK.

## What Running Actually Bought

The same session, once things were executed rather than described:

- fixed-record COBOL to DBF: 200 records, 22,200 bytes = 200 x 111 exactly,
  program compiled, ran, `RECORDS READ: 0000200`, exit 0
- dBASE III -> FoxPro 2.6 -> VFP -> x64 -> x64 VECTOR: 200 rows and 9 fields
  at every rung, dates and decimals intact, indexes migrated with the dialect
- the COBOL copybook FD sums to 109 bytes -- identical, field for field, to
  the dBASE III record. The copybook IS the crosswalk.

None of that was knowable from the files alone. All of it came from four
transcripts and the defects they exposed.

## LabTalk Reading

Companion to the AIF-062 `proofs.yaml` finding one layer down: there, real
evidence was invisible to a clone; here, absent evidence looked real. Both
produce wrong records that propagate -- and a wrong record is worse than a
blank one, because someone will build on it.

## Student Use

A strong student exercise, because the punchline is verifiable in one command:

1. read a script and predict what it will do
2. run it
3. record the difference

The gap between step 1 and step 3 is the lesson.
