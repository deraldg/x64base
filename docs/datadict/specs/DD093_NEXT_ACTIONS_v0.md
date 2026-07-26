# DD-093 Next Actions

1. Install DD-093.
2. Run preflight without `--apply-source-patch`.
3. Inspect path-root presence, catalog-table presence, source patch ledger, and generated diff.
4. If clean, apply with `--apply-source-patch`.
5. Build dottalkpp.
6. Run DDICT path-remap smoke:

```text
SETPATH
DO ddbase
DDICT STATUS
DDICT TABLES
DDICT TAGS DDATTR
DDICT REL DDOBJECT OUT
DDICT EVIDENCE DDOBJECT

```

7. If runtime proof is green, proceed to DD093A path-remap runtime closure.
