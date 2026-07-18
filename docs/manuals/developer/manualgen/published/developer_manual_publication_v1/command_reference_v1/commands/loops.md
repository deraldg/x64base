<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LOOPS

- Catalog/topic: `ED` / `LOOPS`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

Programming Construct 3: Iteration / Looping<br><br>Definition<br>    A loop repeats work.<br><br>DotTalk++ loop families<br>    LOOP ... ENDLOOP<br>    WHILE ... ENDWHILE<br>    UNTIL ... ENDUNTIL<br>    SCAN ... ENDSCAN<br><br>1. L

- Programming Construct 3: Iteration / Looping
- Definition
- A loop repeats work.
- DotTalk++ loop families
- LOOP ... ENDLOOP
- WHILE ... ENDWHILE
- UNTIL ... ENDUNTIL
- SCAN ... ENDSCAN
- 1. LOOP
- Repeats a fixed number of times.
- Example
- LOOP 3 TIMES
- ECHO HELLO
- ENDLOOP
- 2. WHILE
- Repeats while a condition stays true.
- Example concept
- WHILE counter &lt; 10
- ...
- ENDWHILE
- 3. UNTIL
- Repeats until a condition becomes true.
- 4. SCAN
- Record-oriented loop over table rows.
- SCAN
- TUPLE *
- ENDSCAN
- Teaching point
- LOOP / WHILE / UNTIL are general control-flow constructs.
- SCAN is a data-aware loop specialized for table traversal.

## Status

- implemented=no; supported=yes

## Syntax

- LOOPS

## Provenance

- Topic key: `ED|LOOPS`
- Included HELP rows: `32`
- HELP reference run: `MANRUN-20260717T222026Z-28C704E0`
- Disposition run: `MANRUN-20260717T230554Z-DB3F2DC8`
- Authority: `candidate_only`; `publication_authority_claimed=0`
