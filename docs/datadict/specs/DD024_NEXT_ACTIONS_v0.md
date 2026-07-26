# DD-024 Next Actions v0

1. Install the DD-024 repo drop-in from the repository root.
2. Confirm the patched orchestrator help works.
3. Run two stable full scans back-to-back.
4. Diff the two stable scans.
5. If diff is clean, append a DD-024 local smoke note.
6. If diff still shows additions, inspect the added-file CSV and extend the default exclusion contract in DD-025.

No catalog promotion, HELP mutation, CMDHELPCHK mutation, or runtime proof capture is authorized by this package.
