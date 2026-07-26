# DD096Z-D2Y AUTOLOG v0

Date: 2026-05-29T16:23:07+00:00
Subsystem: Data Dictionary / Candidate CDX-LMDB Rebuild
Intent: Rebuild candidate CDX/LMDB by opening one candidate DATA_DICTIONARY_* table at a time from the candidate root, verifying with SL, then closing.
Boundary: no active replacement, no active index/mirror rebuild, no source/build/workspace/HELP/manual mutation.
