<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# RELATION

- Catalog/topic: `ED` / `RELATION`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

A relation connects a parent table to a child table.<br><br>Example<br>    STUDENTS -&gt; ENROLL ON SID<br>    ENROLL   -&gt; CLASSES ON CLS_ID<br><br>Meaning<br>    If the current STUDENTS row has SID = 50000020,<br>    the child

- Manage and inspect the DotTalk++ relation graph
- A relation connects a parent table to a child table.
- Example
- STUDENTS -&gt; ENROLL ON SID
- ENROLL   -&gt; CLASSES ON CLS_ID
- Meaning
- If the current STUDENTS row has SID = 50000020,
- the child ENROLL rows with that SID are related rows.
- Public surfaces
- SET RELATION TO SID INTO ENROLL
- REL ADD STUDENTS ENROLL ON SID
- REL LIST
- REL LIST ALL
- REL REFRESH
- Teaching point
- Relations are the backbone of multi-table thinking.
- They let a current parent row lead you into matching child rows.

## Status

- implemented=no; supported=yes

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
- RELATIONS

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

## Provenance

- Topic key: `ED|RELATION`
- Included HELP rows: `37`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
