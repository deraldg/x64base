<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLSEL

- Catalog/topic: `DOT` / `SQLSEL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Set-oriented SELECT statement over an open work area, plus the legacy predicate-scan form over the current area.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLSEL USAGE
- SQLSEL SELECT &lt;col&gt;[,&lt;col&gt;...] FROM &lt;table&gt; [WHERE &lt;predicate&gt;] [ORDER BY &lt;field&gt; [ASC|DESC]] [LIMIT &lt;n&gt;]
- SQLSEL SELECT * FROM &lt;table&gt;
- SQLSEL SELECT COUNT(*) FROM &lt;table&gt; [WHERE &lt;predicate&gt;]
- SQLSEL [COUNT] [ALL|DELETED] [FOR &lt;expr&gt; | &lt;expr&gt;]
- SQLSEL SELECT &lt;cols&gt;|*|COUNT(*) FROM &lt;table&gt; [WHERE &lt;pred&gt;] [ORDER BY &lt;field&gt; [ASC|DESC]] [LIMIT &lt;n&gt;]

## Usage

- SQLSEL USAGE
- SQLSEL SELECT &lt;col&gt;[,&lt;col&gt;...] FROM &lt;table&gt; [WHERE &lt;predicate&gt;] [ORDER BY &lt;field&gt; [ASC|DESC]] [LIMIT &lt;n&gt;]
- SQLSEL SELECT * FROM &lt;table&gt;
- SQLSEL SELECT COUNT(*) FROM &lt;table&gt; [WHERE &lt;predicate&gt;]
- SQLSEL [COUNT] [ALL|DELETED] [FOR &lt;expr&gt; | &lt;expr&gt;]

## Example

- SQLSEL SELECT SID,LNAME,FNAME FROM STUDENTS
- SQLSEL SELECT * FROM STUDENTS LIMIT 5
- SQLSEL SELECT SID,LNAME FROM STUDENTS WHERE MAJOR = "CSCI"
- SQLSEL SELECT SID,LNAME FROM STUDENTS ORDER BY LNAME DESC LIMIT 10
- SQLSEL SELECT COUNT(*) FROM STUDENTS WHERE GPA &gt;= 3.0
- SQLSEL COUNT
- SQLSEL COUNT FOR GPA &gt;= 3.0
- SQLSEL LNAME = "SMITH"

## Note

- SQLSEL USAGE prints usage before open-table checks.
- A SELECT statement names its own table in FROM; the table must be OPEN.
- A SELECT statement does not read or disturb session state -- not the current area, not the record pointer, not SET FILTER, not SET RELATION.
- A SELECT statement reads committed table data; uncommitted TABLE BUFFER preview overlays remain TUP/TUPLE-facing until SQLSEL DML is promoted.
- SELECT projects bare column names; expression projection is not yet supported and reports rather than emitting empty values.
- ORDER BY sorts the full match set before LIMIT applies, and reports its access path; joins and GROUP BY are not yet implemented.
- LIMIT reports how many rows remain rather than truncating silently.
- The legacy predicate form reads records and may temporarily move the cursor.
- SQLSEL does not mutate table data.

## Related

- SQL
- WHERE

## Provenance

- Topic key: `DOT|SQLSEL`
- Included HELP rows: `38`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
