# tests/conversion -- suite repair record v1

Date: 2026-07-26
Engine: dottalk++ v0.6, build Jul 26 2026 12:52:47
Owner: member.derald   repaired_by: member.ai.claude.cowork
Status: 01 / 02 / 05 repaired and runnable . 03 / 04 documented as capability gaps

## What was wrong

The PDLC maturity review grades **"DBF/xBase and CSV conversion: empirically
demonstrated"** and cites this suite. It is not demonstrated. Every one of the
five scripts was written against syntax the engine does not implement, and none
of them could execute.

Verified against the current command grammar and the live binary:

| script | blocking defect |
| --- | --- |
| 01 | `EXPORT CSV <f> HEADER ON DELIMITER , DATES ISO QUOTES RFC4180` -- EXPORT grammar is `EXPORT [TO] <file> [CSV\|PIPE]`. No DELIMITER / DATES / QUOTES options exist. |
| 02 | `IMPORT CSV <f> SCHEMA <json> REJECTS <csv>` -- IMPORT grammar is `IMPORT <csvfile>` only. Also `USE students_import`: IMPORT appends into the ALREADY-OPEN table, it never creates one. |
| 03 | `BEGIN` is not a registered command (0 hits in shell_commands.cpp). `#SID`-style field substitution inside SCAN has no implementation. |
| 04 | `SQLITE QUERY "..." INTO DBF <f>` -- SQLITE has no `QUERY` subcommand (0 hits) and no INTO-DBF path. |
| ALL | Every script writes to `_drops/`, which **does not exist** under the runtime data root. First write fails regardless of grammar. |

The engine declares its scratch path at startup: `TMP : dottalkpp\data\tmp`.
That is the correct target and the repaired scripts use it.

## How this was found

Not by reading. `10_crosswalk_cascade_items_v1.dts` copied 05's EXPORT line in
good faith; the engine rejected it with a usage error. The corrected form then
failed with `Unable to open _drops/... for write`. Two runs, two findings --
which is the point: **a script that has never been executed is not evidence.**

## Repair principles

1. **Verified grammar only.** Every command in the repaired scripts was checked
   against its `@dottalk.usage` contract AND exercised in a real run. No
   aspirational syntax was preserved, however desirable.
2. **Self-contained fixtures.** The originals depended on a bare `students`
   table. No `students.dbf` exists at the DBF root -- it lives in `sandbox/`,
   `og/`, and `x64/` in four variants with different row counts (215 / 200 /
   210 / 204) and formats. `USE students` is therefore ambiguous at best. The
   repaired suite builds its own fixture from the **sealed Cascade package**
   (`manifest.json` counts verified, `checksums.sha256` verifies), so a failure
   is always the conversion's fault and never the fixture's.
3. **Gaps stay visible.** 03 and 04 require engine capability that does not
   exist. They were NOT rewritten into something that passes. They now prove the
   adjacent capability that does work and state the gap explicitly.

## Capability gaps (not defects -- unbuilt features)

**DBF -> SQLite row pump (03).** Moving rows from an open DBF into SQLite needs
either field substitution inside `SCAN`/`SQLITE EXEC`, or a dedicated bulk
command. Neither exists. `SQLITE EXEC` with literal SQL works; driving it from
cursor values does not.

**SQLite -> DBF materialisation (04).** `SQLITE SELECT` prints a capped result
set to the console. There is no path from a SQLite result into a DBF or a CSV
file. `AUTODBF` can build a DBF from CSV, so the missing link is specifically
"SQLite result set -> file".

Both are legitimate roadmap items for the PDLC lane. Until they exist, the
chain `COBOL -> DBF -> CSV -> SQLite -> x64base` cannot be traversed in the
SQLite direction from inside DotTalk++.

## What IS proven now

`10_crosswalk_cascade_items_v1.dts` (first run 2026-07-26) established, with a
preserved transcript:

- CSV -> x64base DBF: 18 rows, 13 fields, **all 13 type letters** matching the
  derivation from `import_profile.cpp`
- empty cells do not perturb classification (`LIST_PRICE` N with 14 empties)
- `1`/`0` classify INTEGER not LOGICAL (`is_integer_text` tested first)
- NULL fidelity: `LIST_PRICE` renders empty, not `0`
- long names survive with a legacy 10-char descriptor alongside
  (`STANDARD_COST` + `descriptor=STANDARD_C`); 30-char table name intact

## Consequence for the PDLC review

The line "DBF/xBase and CSV conversion: empirically demonstrated" should read:

> **CSV -> x64base DBF: empirically demonstrated** (preserved transcript,
> type/NULL/long-name fidelity verified).
> **DBF -> CSV: repaired, pending first recorded run.**
> **DBF <-> SQLite: capability gap, not demonstrated.**

The capability is real and better than the old scripts implied -- the type
inference and long-name behaviour are genuinely strong. The *evidence* was
missing. That is the same distinction the review applies correctly to the COBOL
hop, now applied to a line it had graded as complete.
