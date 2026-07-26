# DD093 AUTOLOG v0

Date: 2026-05-28T20:50:18+00:00
Subsystem: Data Dictionary / DDICT Runtime Path Remap
Intent: Repair DDICT catalog root from metadata/datadict to data/datadict.
Boundary:
- guarded source-path repair only
- no build file edits
- no registry edits
- no active catalog mutation
- no DBF/CDX/LMDB mutation or rebuild
- no HELP/META/CMDHELPCHK mutation
- no manual row repair
