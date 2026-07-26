# DD-028 Next Actions

1. Install the repo-level drop-in.
2. Run `baseline_check.py --help`.
3. Run the check against `docs/datadict/baselines/DDBASE-stable-v0`.
4. If status is PASS, preserve the run as the current no-change proof.
5. If status is REVIEW or BLOCKED_REVIEW, inspect `DD028_BASELINE_COMPARE_REPORT.md` and the DD-026 triage output.
6. Do not replace the accepted baseline without a separate DD-029 baseline update/acceptance package.
