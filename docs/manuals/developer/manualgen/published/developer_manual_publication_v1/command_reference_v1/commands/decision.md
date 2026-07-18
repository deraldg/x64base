<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# DECISION

- Catalog/topic: `ED` / `DECISION`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

Programming Construct 2: Decision Flow<br><br>Definition<br>    Decision flow chooses between alternatives based on a condition.<br><br>Current DotTalk++ form<br>    IF &lt;expr&gt;<br>        ...<br>    ELSE<br>        ...<br>    ENDIF

- Programming Construct 2: Decision Flow
- Definition
- Decision flow chooses between alternatives based on a condition.
- Current DotTalk++ form
- IF &lt;expr&gt;
- ...
- ELSE
- ENDIF
- Concept
- IF asks a yes/no question.
- If true, the IF branch runs.
- Otherwise, the ELSE branch runs, if present.
- Example
- IF GPA &gt; 3.5
- ECHO HONOR STUDENT
- ECHO REGULAR STUDENT
- Educational importance
- This is how a script becomes selective instead of merely linear.
- Typical uses
- - react to a calculation
- - guard a destructive operation
- - separate normal and exceptional paths
- Teaching point
- Decision logic is about controlling execution, not merely testing truth.

## Status

- implemented=no; supported=yes

## Syntax

- DECISION / IF

## Provenance

- Topic key: `ED|DECISION`
- Included HELP rows: `26`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
