# DD-035 Next Actions

1. Install the repo drop-in from Downloads.
2. Run `baseline_v2_readiness.py --help`.
3. Run strict DD-035 against `DD034-daily-current-after-wrapper-cleanup-v0`.
4. Review blocked maintenance rows.
5. If acceptable, rerun with `--accept-maintenance-evidence --accept-datadict-self-update --accept-manualgen-evidence`.
6. If status is `READY_FOR_BASELINE_V2_AFTER_FRESH_STABLE_PROOF`, inspect and optionally run `dd035_accept_baseline_v2_commands.ps1`.
