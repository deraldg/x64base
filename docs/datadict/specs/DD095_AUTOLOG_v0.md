# DD095 AUTOLOG v0

Date: 2026-05-28T22:09:42+00:00
Subsystem: Data Dictionary / Layout Policy Documentation
Intent: Document accepted DATADICT/INDEXES/DATADICT/LMDB/DATADICT layout and no-metadata-collision rule.
Boundary:
- report-only by default
- optional policy document write only with explicit flag
- no source/build/registry edits
- no active catalog mutation
- no DBF/CDX/LMDB mutation or rebuild
- no HELP/META/CMDHELPCHK mutation
- no manual row repair
