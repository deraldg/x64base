# DD-036 Next Actions v0

1. Install the DD-036 repo drop-in.
2. Run the strict closure against `DD034-check-DDBASE-stable-v2-current`.
3. Run the explicit report-only acceptance with `--accept-acceptance-artifacts` if all rows are baseline/proof artifacts.
4. If accepted, record a DD-036 local proof runlog.
5. Next package should patch DD-034 so daily status can recognize acceptance/proof artifacts directly, or provide a normal daily command that returns a final closure status without needing a separate manual DD-036 run.
