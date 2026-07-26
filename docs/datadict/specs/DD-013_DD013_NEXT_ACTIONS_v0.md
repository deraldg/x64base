# DD013 Next Actions v0

## Recommended next package

**DD-014 — Workspace / Relation Transcript Proof Plan**

Goal: define a guarded proof sequence for read-only workspace and relation commands, using controlled sample data and clear mutation gates.

Candidate read-only proof commands:

```text
WORKSPACE
AREA
RELATIONS
RELATIONS ALL
REL LIST
TUPLE * --HEADER
TUPVALIDATE <spec>
```

Candidate mutation-gated commands, not to run without explicit authorization:

```text
SET RELATION TO ... INTO ...
SET RELATIONS ADD ...
REL ADD ...
REL CLEAR ...
REL REFRESH
REL SAVE / REL LOAD
WORKSPACE LOAD / WORKSPACE OPEN
```

## DD-014 should produce

```text
DD_WORKSPACE_SNAPSHOT proof plan
DD_WORKAREA proof plan
DD_REL proof plan
DD_REL_FIELD proof plan
DD_TUPLE_SPEC proof plan
DD_TUPLE_COLUMN proof plan
DD_REL_VERIFY gates
```

## Important follow-up

The known memo64 issue belongs in this lane too: normal USE memo attach is green, but WORKSPACE OPEN DBF previously opened MEMO_X64 without attaching memo backend. DD-014 or DD-015 should make that a dictionary verification point, not merely a one-off bug note.
