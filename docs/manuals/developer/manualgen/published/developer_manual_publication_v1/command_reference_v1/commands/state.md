<!-- CANDIDATE ONLY: report-only command-reference page; no publication authority. -->
# STATE

- Catalog/topic: `ED` / `STATE`
- Status: `supported`
- Implemented/supported: `F` / `T`
- Primary/confidence: `EDREF` / `CATALOG`

## Summary

State is one of the most important DotTalk++ concepts.

- Definition
- State means the current internal condition of the session.
- Examples of session state
- - current work area
- - current table
- - current record pointer
- - active order/tag
- - active filter
- - relation graph
- - buffering on/off
- - path settings
- Why it matters
- Commands do not operate in a vacuum.
- They operate against the current state.
- Example
- SELECT STUDENTS
- SET ORDER TO TAG LNAME
- SEEK TAYLOR
- Here SEEK depends on:
- - STUDENTS being current
- - an order being active
- - the key format of that order
- Teaching point
- Learning DotTalk++ means learning stateful programming.

## Status

- implemented=no; supported=yes

## Syntax

- ENGINE STATE

## Provenance

- Topic key: `ED|STATE`
- Included HELP rows: `27`
- HELP reference run: `MANRUN-20260902T151703Z-1CA7DB89`
- Disposition run: `MANRUN-20260902T151704Z-6F39AFBC`
- Authority: `candidate_only`; `publication_authority_claimed=0`
