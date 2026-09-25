<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# SQLSEL

- Catalog/topic: `DOT` / `SQLSEL`
- Status: `supported`
- Implemented/supported: `T` / `T`
- Primary/confidence: `DOTREF` / `CATALOG`

## Summary

Typed set-oriented SELECT and DML over open x64base work areas.

## Status

- implemented=yes; supported=yes

## Syntax

- SQLSEL SELECT &lt;cols&gt;|*|COUNT(*) FROM &lt;table&gt; [WHERE &lt;pred&gt;] [ORDER BY &lt;field&gt; [ASC|DESC]] [LIMIT &lt;n&gt;]

## Usage

- SQLSEL USAGE
- SQLSEL [SELECT] [DISTINCT] &lt;list&gt; FROM &lt;source&gt; [WHERE &lt;predicate&gt;]
- [GROUP BY &lt;list&gt;] [HAVING &lt;predicate&gt;]
- [ORDER BY &lt;item&gt;[,&lt;item&gt;...]] [LIMIT &lt;n&gt;]
- SQLSEL &lt;select&gt; UNION [ALL] &lt;select&gt; | &lt;select&gt; INTERSECT &lt;select&gt; | &lt;select&gt; EXCEPT &lt;select&gt;
- SQLSEL INSERT INTO &lt;table&gt; (&lt;fields&gt;) VALUES (&lt;values&gt;)[,(&lt;values&gt;)...]
- SQLSEL UPDATE &lt;table&gt; [[AS] &lt;alias&gt;] SET &lt;field&gt;=&lt;expr&gt;[,...] WHERE &lt;predicate&gt;
- SQLSEL DELETE FROM &lt;table&gt; [[AS] &lt;alias&gt;] WHERE &lt;predicate&gt;

## Example

- SQLSEL SID,LNAME,FNAME FROM STUDENTS
- SQLSEL * FROM STUDENTS LIMIT 5
- SQLSEL SID,LNAME FROM STUDENTS WHERE MAJOR = "CSCI"
- SQLSEL SID,LNAME FROM STUDENTS ORDER BY LNAME DESC LIMIT 10
- SQLSEL COUNT(*) FROM STUDENTS WHERE GPA &gt;= 3.0
- SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S JOIN ENROLL E ON S.SID = E.SID
- SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S LEFT JOIN ENROLL E ON S.SID = E.SID
- SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S RIGHT JOIN ENROLL E ON S.SID = E.SID
- SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S FULL JOIN ENROLL E ON S.SID = E.SID
- SQLSEL S.LNAME,E.CLS_ID FROM STUDENTS S CROSS JOIN ENROLL E
- SQLSEL DEPT,COUNT(*),AVG(SALARY) FROM STAFF GROUP BY DEPT
- SQLSEL SID FROM STUDENTS UNION SELECT SID FROM ALUMNI
- SQLSEL SID FROM STUDENTS S WHERE EXISTS (SELECT SID FROM ENROLL E WHERE E.SID=S.SID)
- SQLSEL INSERT INTO STUDENTS (SID,LNAME) VALUES (9,'SMITH')
- SQLSEL UPDATE STUDENTS SET LNAME=UPPER(LNAME) WHERE SID=9
- SQLSEL DELETE FROM STUDENTS WHERE SID=9

## Note

- SQLSEL USAGE prints usage before open-table checks.
- SQLSEL is the select verb; a leading SELECT keyword remains optional.
- A statement names open tables inside the current workspace. SELECT restores the current area and source cursors and ignores SET FILTER/SET RELATION.
- SELECT reads committed data. DML in one explicit transaction reads its own buffered writes; SELECT during that transaction remains a committed view.
- All JOIN forms are statement-scoped ad-hoc set matching. They do not consult a declared relation; every run reports its fence and access path.
- Outer joins render produced-absent cells as &lt;UNMATCHED&gt; and report their extension counts. WHERE uses SQL three-valued logic for that absence.
- CROSS JOIN takes no ON clause. Multi-join chains support INNER/LEFT/CROSS;
- RIGHT/FULL remain two-table forms.
- Projection uses the typed TupleRow expression engine. Aggregates are
- COUNT/SUM/AVG/MIN/MAX; numeric blanks are skipped and reported.
- Set operands require equal arity and compatible tuple types.
- LIMIT reports how many rows remain rather than truncating silently.
- DML reuses APPEND/REPLACE/DELETE semantics through TableBuffer + TBJ1 WAL.
- Explicit BEGIN/COMMIT/ROLLBACK requires SET MODE SQL and is atomic for one target table only. NULL and memo-field DML refuse; DBF blanks remain values.
- The legacy predicate form was RETIRED 2026-09-09 (AIF-074, owner ruling).
- COUNT carries that job -- COUNT FOR &lt;expr&gt;, COUNT LIST, COUNT VERBOSE -- and honours SET FILTER and SET DELETED as the logical rowset.

## Related

- SQL
- WHERE

## Provenance

- Topic key: `DOT|SQLSEL`
- Included HELP rows: `53`
- HELP reference run: `MANRUN-20260924T230323Z-76AD9EBC`
- Disposition run: `MANRUN-20260925T002350Z-BF0876DF`
- Authority: `candidate_only`; `publication_authority_claimed=0`
