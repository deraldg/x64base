# E2 Guarded HELP Refresh Result V1

Status: PASS

Run: `DOCFLUSH-20260825-001-E2-001`

## Execution

- Runtime exit: 0.
- Legacy rows: 462 commands, 2,614 arguments.
- Current usage mining: 3,507 rows from 207 files.
- Current HELP: 29,480 line rows and 670 reachable topics.
- Runtime reflection: `OK no structural issues found`.
- Direct HELP table join: PASS, no blank or orphan keys.
- Changed from the 39-file before-set: seven files.
- Rollback on successful attempt: not performed.
- Publication authority claimed: no.

## Topic-set disposition

No topic was lost. Three source-derived topics entered the rebuilt store:

- `DOT|FOX PALETTE COMMAND`
- `DOT|HELP RESOLVER`
- `DOT|SAMPLE`

## Rollback evidence

Attempt 1 reached runtime readback but failed on relative evidence-path
normalization. The guard restored the complete before-set; independent SHA-256
comparison found zero mismatches. Attempt 2 used a new byte-verified backup at
`dottalkpp/data/help.bak-20260826-guarded-e2-002`.

Manual rollback remains after-hash guarded by the successful execution record.
It must be used before any later HELP mutation, because later legitimate changes
make the recorded after-set stale and correctly cause refusal.

## Next entry

E2 is closed. E5 is open because five canonical HELP harvest CSVs and five
manifest row counts predate this successful rebuild. Re-export and semantic
readback are required before publication ascent can proceed.
