<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# RELATIONS

- Catalog/topic: `DOT` / `RELATIONS`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Inspect and manage active relation definitions, relation files, and relation enumeration helpers.

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
- RELATIONS
- RELATIONS USAGE
- RELATIONS ALL
- SET RELATIONS
- SET RELATIONS USAGE
- SET RELATIONS ADD &lt;parent&gt; &lt;child&gt; ON f1[,f2...] [TO child_f1[,child_f2...]]
- SET RELATIONS CLEAR &lt;parent|ALL&gt;
- RELATIONS [USAGE|ALL]

## Usage

- RELATIONS
- RELATIONS USAGE
- RELATIONS ALL
- SET RELATIONS
- SET RELATIONS USAGE
- SET RELATIONS ADD &lt;parent&gt; &lt;child&gt; ON f1[,f2...] [TO child_f1[,child_f2...]]
- SET RELATIONS CLEAR &lt;parent|ALL&gt;

## Example

- REL LIST
- REL ADD STUDENTS ENROLL ON SID
- REL ADD SYS_CMD SYS_SUBCMD ON CAN_NAME TO PARENT
- REL REFRESH
- REL ENUM LIMIT 10 ENROLL CLASSES TUPLE STUDENTS.SID,CLASSES.CID
- RELATIONS
- RELATIONS ALL
- SET RELATIONS ADD STUDENTS ENROLL ON SID
- SET RELATIONS CLEAR ALL

## Note

- REL is the native relation backend
- FoxPro-style SET RELATION syntax routes into this model where implemented
- REL ENUM traverses relation paths and emits tuple projections
- RELATIONS USAGE prints usage and does not inspect or mutate relation state.
- SET RELATIONS USAGE prints usage and does not mutate the relation graph.
- SET RELATIONS ADD/CLEAR mutate relation definitions.
- RELATIONS ALL reports a recursive tree rooted at the current parent.

## Alias

- REL_LIST

## Related

- RBROWSE
- TUPLE
- WORKSPACE

## Provenance

- Topic key: `DOT|RELATIONS`
- Included HELP rows: `55`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
