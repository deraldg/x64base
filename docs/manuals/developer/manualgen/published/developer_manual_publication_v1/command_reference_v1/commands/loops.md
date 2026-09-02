<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# LOOPS

- Catalog/topic: `ED` / `LOOPS`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

Programming Construct 3: Iteration / Looping

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
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
