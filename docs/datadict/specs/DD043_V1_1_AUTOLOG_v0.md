# DD043 v1.1 AUTOLOG v0

Date: 2026-05-27T21:29:47+00:00
Subsystem: Data Dictionary / Runtime Readback
Intent: Harden pydottalk import path by prepending repo build/python automatically.
Boundary:
- no DBF writes
- no CDX creation
- no LMDB writes
- no HELP/META/CMDHELPCHK mutation
- no source edits
- no active catalog promotion
