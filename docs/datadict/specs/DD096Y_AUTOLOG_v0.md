# DD096Y AUTOLOG v0

Date: 2026-05-29T02:35:59+00:00
Subsystem: Data Dictionary / x64 Staged Import
Intent: Map staged DD096 candidate rows into the DD096X x64 proof schema.
Boundary:
- no active datadict replacement
- generator performs no DBF writes
- runtime DTS targets SANDBOX proof tables when used as instructed
- no source/HELP/CMDHELPCHK/manual mutation
