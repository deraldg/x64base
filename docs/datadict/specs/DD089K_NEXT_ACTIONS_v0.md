# DD-089K Next Actions

1. Install DD-089K.
2. Run preflight without `--apply-repair`.
3. Inspect patch ledger and generated diff.
4. Apply with `--apply-repair` if clean.
5. Rebuild dottalkpp.
6. If build succeeds, capture DDICT smoke and run DD-089I closure.
7. If build fails with new errors, stop and package DD-089L from the new evidence.
