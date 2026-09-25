<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# REL

- Catalog/topic: `DOT` / `REL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Dispatch relation list, refresh, join, enumeration, persistence, add, and clear operations.

## Status

- implemented=yes; supported=yes

## Syntax

- REL LIST
- REL LIST ALL
- REL REFRESH
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;field&gt;
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;parentField&gt; TO &lt;childField&gt;
- REL CLEAR &lt;parent&gt;
- REL CLEAR ALL
- REL ENUM [LIMIT &lt;n&gt;] &lt;path...&gt; TUPLE &lt;projection&gt;
- REL SAVE [path]
- REL LOAD [path]
- REL &lt;subcommand&gt; ...
- REL LIST [ALL]
- REL JOIN [ONE] [DISTINCT|ALL] [LIMIT &lt;n&gt;] [&lt;child&gt; ...] TUPLE &lt;alias&gt;.&lt;field&gt;[, ...]
- REL ENUM [DISTINCT|ALL] [LIMIT &lt;n&gt;] [&lt;child&gt; ...] TUPLE &lt;alias&gt;.&lt;field&gt;[, ...]
- ONE       emit exactly one row using the current relation context (REL JOIN only;
- DISTINCT  de-duplicate tuples (field lists only)
- ALL       allow duplicates (default; overrides DISTINCT)
- REL SAVE [path] | REL SAVE AS &lt;dataset&gt;
- REL LOAD [path] | REL LOAD AS &lt;dataset&gt;
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;field&gt;[,&lt;field&gt;...]
- same-field relation
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;parent_field&gt; TO &lt;child_field&gt;
- asymmetric relation
- REL CLEAR &lt;parent&gt;|ALL
- alias of SET RELATIONS CLEAR
- REL SCANLIMIT [&lt;n&gt;]
- records scanned PER HOP -- caps what is FOUND

## Usage

- REL
- REL USAGE
- REL LIST [ALL]
- REL REFRESH
- REL JOIN [ONE] [DISTINCT|ALL] [LIMIT &lt;n&gt;] [&lt;child1&gt; &lt;child2&gt; ...] TUPLE &lt;alias&gt;.&lt;field&gt;[, ...]
- REL ENUM [DISTINCT|ALL] [LIMIT &lt;n&gt;] [&lt;child1&gt; &lt;child2&gt; ...] TUPLE &lt;alias&gt;.&lt;field&gt;[, ...]
- REL SAVE [path] | REL SAVE AS &lt;dataset&gt;
- REL LOAD [path] | REL LOAD AS &lt;dataset&gt;
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;field&gt;[,&lt;field&gt;...]
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;parent_field&gt; TO &lt;child_field&gt;
- REL CLEAR &lt;parent&gt;|ALL
- REL SCANLIMIT [&lt;n&gt;]

## Argument

- NOTHING
- Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.

## Example

- REL LIST
- REL ADD STUDENTS ENROLL ON SID
- REL ADD SYS_CMD SYS_SUBCMD ON CAN_NAME TO PARENT
- REL REFRESH
- REL ENUM LIMIT 10 ENROLL CLASSES TUPLE STUDENTS.SID,CLASSES.CID

## Note

- REL is the native relation backend
- FoxPro-style SET RELATION syntax routes into this model where implemented
- REL ENUM traverses relation paths and emits tuple projections
- REL forwards each subcommand to the owning relation handler.
- REL ADD and REL CLEAR mutate relation definitions; REL REFRESH refreshes relation state.
- REL SCANLIMIT reports or sets the relation engine's PER-HOP record budget.
- It caps what a traversal FINDS, not what is displayed: lowering it changes match counts and drops join rows. ERSATZ LIMIT is the display cap.
- Shipped since AIF-074 P1.3 and absent from this contract until 2026-08-28.
- ONE is REL JOIN ONLY and REL ENUM DOES NOT ACCEPT IT -- the two lines are deliberately not identical. ONE emits a single row from the CURRENT relation pointers; given a child chain it REFUSES rather than discarding it (AIF-147), because reporting success for a traversal that never happened is the shape this codebase hunts.
- DISTINCT de-duplicates tuples (FIELD LISTS ONLY); ALL allows duplicates and is the default, overriding DISTINCT. Both are real on both verbs -- DISTINCT is backed by a seen-set, not parsed and ignored. Wording here is taken from
- MessageId::RelJoinUsageText rather than restated, because that catalog entry is the authority and had all three flags documented correctly the whole time.
- TUPLE takes a COMMA-SEPARATED &lt;alias&gt;.&lt;field&gt; list, not an expression. The proven spelling is in data/scripts/main/rel_join_enum_regression.dts.
- CONTRACT SWEEP, 2026-09-03. REL JOIN's usage had THREE HOMES and only the newest was right:
- 1. this comment block            -- LIMIT and TUPLE only        (was stale)
- 2. rel_usage() below, printed by REL USAGE  -- same omission     (was stale)
- 3. MessageId::RelJoinUsageText, printed by a bare REL JOIN
- -- ONE, DISTINCT and ALL, each with a description            (CORRECT)
- So the answer a user got depended on HOW THEY ASKED: `REL USAGE` returned an incomplete list and `REL JOIN` with no arguments returned the complete one.
- Same question, two answers, decided by route. Homes 1 and 2 now quote home 3.
- The SCANLIMIT note above records this same defect closed for ONE keyword on 2026-08-28; that fix corrected its line and did not sweep the block it was standing in, which is how the rest survived.
- WHEN A KEYWORD IS ADDED TO A PARSER HERE: update the catalog entry, then make
- BOTH copies in this file quote it. Do not restate it in a third voice.

## Related

- SET RELATION, SET RELATIONS, RELATIONS, TUPLE, WORKSPACE

## Provenance

- Topic key: `DOT|REL`
- Included HELP rows: `118`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
