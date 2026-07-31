# x64base staging tools

`rebuild-staging.ps1` expands `PROMOTE.manifest` and is report-only unless
`-Execute` is supplied. `-Fresh -Execute` is destructive to the existing
staging working state and must not be used until that state is preserved or
explicitly discarded.

`preserve_staging_worktree.py` runs only under Python 3.12. It binds the current
staging branch, HEAD, status rows, and file hashes to a reviewed baseline, then
copies every dirty file into a development-side backup with a byte-verified
manifest and binary tracked-worktree patch. It never writes `C:\x64base`.

`plan_gate5_staging_overlay.py` binds the reviewed Gate 5 manifest-delta
candidate, the preservation package, and the clean staging Git baseline. It
expands every proposed file and compares its Git blob identity to the clean
HEAD without writing staging. It fails if the selective plan intersects any
preserved dirty path other than the expected `PROMOTE.manifest` delta.

`create_public_baseline_escrow.py` closes the offline-recovery gap in the old
"staging is disposable" model. It creates a verified Git bundle, exact tar
snapshot, per-file SHA-256 ledger, public-baseline-only reconciliation ledger,
and self-contained copies of the dirty-state preservation, ignored-state
preservation, and Gate 5 plan. A fresh reset is safe only when the committed
baseline, preserved dirty layer, preserved ignored layer, and authorized
overlay are treated as separate restore layers.

`execute_gate5_staging_rebuild.py` is the exact recovery-bound Gate 5 executor.
It is report-only unless `--execute` is supplied. It verifies the current
staging/escrow/source bindings, fetches and refuses a moved public baseline,
resets staging, restores ordinary dirty and ignored layers, applies only the
bound selective ledger, and verifies the index, public-only paths, restored
layers, and overlay. A failed post-reset verification automatically reconstructs
the pre-execution staging state from escrow.

Post-apply regression suites distinguish self-contained product checks from
development-evidence integrations. Missing candidate metacollect inputs,
manualgen generated runs, or locally retained benchmark transcripts are
reported as named skips in the public projection. Those inputs are not copied
into staging merely to satisfy a test; the same assertions continue to run in
development where the hash-bound evidence is present.
