# DD-048 Next Actions

1. Install DD-048 from Downloads.
2. Run the guard pass without `--apply-source-patch`.
3. Inspect the generated diff.
4. Run with `--apply-source-patch` only if the diff is acceptable.
5. Build.
6. Rerun DD-046 CREATE X64 / IMPORT / memo probe.
7. If green, plan shared-helper cleanup or canonical catalog rebuild.
