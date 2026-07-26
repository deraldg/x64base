# DD-093R Next Actions

1. Install DD-093R.
2. Run discovery without `--apply-source-patch`.
3. Inspect:
   - `dd093r_source_contexts.csv`
   - `dd093r_patch_candidate_ledger.csv`
   - generated diff
4. If status is PATCH_READY, apply with `--apply-source-patch`.
5. Build dottalkpp.
6. Run this smoke, including the final blank line:

```text
SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT

```
