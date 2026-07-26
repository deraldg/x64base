# DD-093B Next Actions

1. Install DD-093B.
2. Run preflight without `--apply-source-patch`.
3. Inspect artifact presence, patch ledger, and generated diff.
4. If patch-ready, apply with `--apply-source-patch`.
5. Build dottalkpp.
6. Run this smoke, with final blank line:

```text
SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT TAGS DDOBJECT
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT

```
