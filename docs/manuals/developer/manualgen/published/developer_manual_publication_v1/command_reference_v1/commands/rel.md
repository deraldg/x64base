<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# REL

- Catalog/topic: `DOT` / `REL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Relations engine commands (native DotTalk++ relation graph).<br><br>Subcommands:<br>    REL LIST<br>    REL LIST ALL<br>    REL REFRESH<br>    REL ENUM [LIMIT &lt;n&gt;] &lt;child1&gt; [&lt;child2&gt; ...] TUPLE &lt;tuple-expr&gt;<br>    REL SAV

- Manage and inspect the DotTalk++ relation graph
- Dispatch relation list, refresh, join, enumeration, persistence, add, and clear operations.
- Relations engine commands (native DotTalk++ relation graph).
- Subcommands:
- REL LIST
- REL LIST ALL
- REL REFRESH
- REL ENUM [LIMIT &lt;n&gt;] &lt;child1&gt; [&lt;child2&gt; ...] TUPLE &lt;tuple-expr&gt;
- REL SAVE [path] | REL SAVE AS &lt;dataset&gt;
- REL LOAD [path] | REL LOAD AS &lt;dataset&gt;
- REL ADD &lt;parent&gt; &lt;child&gt; ON &lt;field&gt;[,&lt;field&gt;...]
- REL CLEAR &lt;parent&gt;|ALL
- Examples:
- REL ADD STUDENTS ENROLL ON SID
- REL ADD ENROLL CLASSES ON CLS_ID
- REL ENUM LIMIT 10 ENROLL CLASSES TASSIGN TEACHERS TUPLE ;
- STUDENTS.SID,STUDENTS.LNAME,ENROLL.CLS_ID,CLASSES.CID,TEACHERS.LNAME
- Conceptual Model:
- REL maintains a directed relation graph between work areas.
- REL ADD defines edges.
- REL REFRESH recalculates relation state.
- REL ENUM traverses the graph and emits tuple rows.
- Traversal Behavior:
- REL ENUM performs depth-first traversal of the relation chain.
- Each successful path produces one tuple row.
- Example chain:
- STUDENTS -&gt; ENROLL -&gt; CLASSES -&gt; TASSIGN -&gt; TEACHERS
- Matching:
- Current implementation uses same-name field equality:
- parent.FIELD == child.FIELD
- Notes:
- REL is the native DotTalk++ relation system.
- FoxPro-style SET RELATION commands map into this backend.
- REL ENUM is the row enumeration engine used by relational
- browsers and tuple views.

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

## Provenance

- Topic key: `DOT|REL`
- Included HELP rows: `68`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
