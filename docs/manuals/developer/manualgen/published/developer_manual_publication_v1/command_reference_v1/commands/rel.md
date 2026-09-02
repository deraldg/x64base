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
- REL
- REL USAGE
- REL LIST [ALL]
- REL JOIN [LIMIT &lt;n&gt;] [&lt;child1&gt; &lt;child2&gt; ...] TUPLE &lt;expr&gt;
- REL ENUM [LIMIT &lt;n&gt;] [&lt;child1&gt; &lt;child2&gt; ...] TUPLE &lt;expr&gt;
- REL SAVE [path] | REL SAVE AS &lt;dataset&gt;
- REL LOAD [path] | REL LOAD AS &lt;dataset&gt;
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;field&gt;[,&lt;field&gt;...]
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;parent_field&gt; TO &lt;child_field&gt;
- REL CLEAR &lt;parent&gt;|ALL
- REL SCANLIMIT [&lt;n&gt;]
- REL &lt;subcommand&gt; ...
- same-field relation
- asymmetric relation
- alias of SET RELATIONS CLEAR
- records scanned PER HOP -- caps what is FOUND

## Usage

- REL
- REL USAGE
- REL LIST [ALL]
- REL REFRESH
- REL JOIN [LIMIT &lt;n&gt;] [&lt;child1&gt; &lt;child2&gt; ...] TUPLE &lt;expr&gt;
- REL ENUM [LIMIT &lt;n&gt;] [&lt;child1&gt; &lt;child2&gt; ...] TUPLE &lt;expr&gt;
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

## Related

- SET RELATION, SET RELATIONS, RELATIONS, TUPLE, WORKSPACE

## Provenance

- Topic key: `DOT|REL`
- Included HELP rows: `91`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
