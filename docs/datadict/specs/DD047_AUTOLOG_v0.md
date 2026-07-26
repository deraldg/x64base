# DD047 AUTOLOG v0

Date: 2026-05-28T01:13:06+00:00
Subsystem: Data Dictionary / IMPORT Memo Repair
Intent: Capture source-level repair plan for IMPORT x64 M-field assignment.
Finding: IMPORT uses plain a.set(fi, cols[c]); REPLACE uses proven memo-aware path.
Boundary:
- report-only
- no source mutation
- no build
- no active/sandbox catalog mutation
Next: guarded implementation patch, then rerun DD-046.
