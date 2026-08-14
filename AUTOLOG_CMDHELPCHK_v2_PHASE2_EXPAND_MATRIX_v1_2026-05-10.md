AUTOLOG 2026-05-10
Subsystem: CMDHELPCHK v2 Phase 2 metadata evidence expansion

Files added:
  data/scripts/help/cmdhelpchk_metadata_expand_matrix_v1.dts

Intent:
  Broaden runtime-proven metadata evidence before integrating Phase 2 bridge into main scanner.
  Use compact locate-only DotScript output to identify which additional rows are seeded.

Behavior preserved:
  No DBF/DBT/CDX/LMDB parsing outside DotTalk++ runtime.
  No metadata mutation.
  No wide LIST output.
  No TUP after failed LOCATE.
