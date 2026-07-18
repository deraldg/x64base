<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# REL ENUM

- Catalog/topic: `DOT` / `REL ENUM`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Traverse a relation chain and emit tuple rows.<br><br>Syntax:<br>    REL ENUM [LIMIT &lt;n&gt;] &lt;child1&gt; [&lt;child2&gt; ...] TUPLE &lt;tuple-expr&gt;<br><br>Example:<br>    REL ENUM LIMIT 5 ENROLL CLASSES TASSIGN TEACHERS<br>        TUPLE

- Traverse a relation chain and emit tuple rows.
- Syntax:
- REL ENUM [LIMIT &lt;n&gt;] &lt;child1&gt; [&lt;child2&gt; ...] TUPLE &lt;tuple-expr&gt;
- Example:
- REL ENUM LIMIT 5 ENROLL CLASSES TASSIGN TEACHERS
- TUPLE STUDENTS.SID,STUDENTS.LNAME,TEACHERS.LNAME
- Execution Model:
- 1. Current selected area is the root.
- 2. Each child token represents the next relation edge.
- 3. Traversal expands matches depth-first.
- Example traversal:
- STUDENTS
- -&gt; ENROLL
- -&gt; CLASSES
- -&gt; TASSIGN
- -&gt; TEACHERS
- Each complete path emits one tuple row.
- LIMIT:
- LIMIT applies to emitted rows, not intermediate matches.
- Projection:
- The TUPLE clause defines which fields are emitted.
- Used By:
- SIMPLEBROWSER
- SMARTBROWSER
- relational tuple views.

## Status

- implemented=no; supported=yes

## Syntax

- REL ENUM [LIMIT &lt;n&gt;] &lt;path...&gt; TUPLE &lt;tuple-expr&gt;

## Provenance

- Topic key: `DOT|REL ENUM`
- Included HELP rows: `27`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
