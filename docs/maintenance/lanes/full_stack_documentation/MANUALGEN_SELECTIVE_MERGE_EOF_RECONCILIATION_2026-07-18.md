# Manualgen selective-merge EOF reconciliation

Decision: approved for canonical acceptance preflight.  
Recorded: 2026-07-18 UTC.  
Selective merge: `MANRUN-20260718T031554Z-F1F59445`.  
Superseded packaging run: `MANRUN-20260718T020658Z-BFE7F605`.  
Canonical mutation authorized: no.  
Publication authorized: no.

## Reason

The first controlled-acceptance dry-run
`MANRUN-20260718T031402Z-B472B856` failed closed because the original
selective-merge writer trimmed two trailing blank lines from the Runtime
Evidence section candidate and one from the Command Surface section candidate.
Its manifest diff was calculated before that write-time trim and therefore
claimed zero deletions while the written files did not.

## Reconciliation

The writer now preserves each canonical section's existing EOF whitespace.
The selective merge was regenerated from the same approved prose batch and
unchanged canonical inputs.

- both regenerated section candidates are text-identical to the reviewed
  versions after trailing whitespace normalization;
- the Partial HELP appendix is byte-identical;
- the full contextual reader is byte-identical at
  `FC5FF6526E0E73B69A69478FE4D489CDE2FBAAD6750B39A8829419E24237E897`;
- Runtime Evidence remains 33 additions and 0 deletions;
- Command Surface remains 22 additions and 0 deletions;
- combined reader remains 106 additions and 0 deletions;
- canonical hashes changed: 0;
- publication authority claimed: 0.

This is a packaging correction, not a prose or placement change. The original
context approval carries forward to the regenerated run. No canonical manual,
accepted evidence, pointer, source, catalog, or website file changed.
