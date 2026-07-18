<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# EDUCATIONAL_USE

- Catalog/topic: `ED` / `EDUCATIONAL_USE`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

A practical study order<br><br>1. Open a table<br>    USE STUDENTS<br>    STRUCT<br>    FIELDS<br>    LIST 5<br><br>2. Learn navigation<br>    TOP<br>    SKIP 1<br>    BOTTOM<br>    RECNO<br><br>3. Learn ordering<br>    SET INDEX TO students.cdx

- A practical study order
- 1. Open a table
- USE STUDENTS
- STRUCT
- FIELDS
- LIST 5
- 2. Learn navigation
- TOP
- SKIP 1
- BOTTOM
- RECNO
- 3. Learn ordering
- SET INDEX TO students.cdx
- SET ORDER TO TAG LNAME
- 4. Learn predicates
- LOCATE LNAME = Taylor
- SMARTLIST 5 FOR GPA &gt;= 3.5
- 5. Learn tuple projection
- TUPLE *
- TUPLE LNAME,FNAME
- 6. Learn relations
- SET RELATION TO SID INTO ENROLL
- REL LIST
- 7. Learn relation traversal
- REL ENUM ...
- 8. Learn buffering
- TABLE ON
- REPLACE ...
- COMMIT
- 9. Learn scripting
- IF / ELSE / ENDIF
- LOOP / ENDLOOP
- SCAN / ENDSCAN
- Teaching principle
- Move from single table -&gt; ordered navigation -&gt; predicate logic -&gt;
- projection -&gt; relations -&gt; scripting.

## Status

- implemented=no; supported=yes

## Syntax

- HOW TO STUDY THIS SYSTEM

## Provenance

- Topic key: `ED|EDUCATIONAL_USE`
- Included HELP rows: `38`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
