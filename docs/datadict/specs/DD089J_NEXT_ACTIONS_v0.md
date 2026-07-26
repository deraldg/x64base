# DD-089J Next Actions

1. Install DD-089J.
2. Run preflight without `--apply-repair`.
3. Inspect patch ledger and generated diffs.
4. Apply with `--apply-repair` if clean.
5. Rebuild dottalkpp.
6. If build succeeds, rerun DD-089I closure with build/runtime proof.
7. If build fails with new errors, stop and package DD-089K from the new evidence.
