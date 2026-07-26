# DD-047 IMPORT Memo Field Assignment Repair Plan v0

Created UTC: `2026-05-28T01:13:06+00:00`

## Purpose

DD-047 captures the repair plan for the defect exposed by DD-046:

```text
CREATE X64 + IMPORT imports rows and C fields,
but IMPORT does not import CSV values into x64 M fields.
```

Runtime proof showed:

```text
REPLACE notes WITH "Manual memo write through REPLACE"
```

writes memo text correctly, so the repair should reuse the proven REPLACE memo-aware path.

## Preferred repair

```text
Extract the x64 memo stored-value helper from cmd_replace.cpp into shared CLI helper code.
Use that helper from both REPLACE and IMPORT.
Keep ordinary IMPORT behavior for non-memo fields.
```

## Boundary

DD-047 v0 is report-only. It does not modify source or run a build.
