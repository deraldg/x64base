# DD-029 Next Actions

1. Install the DD-029 drop-in bundle.
2. Run `artifact_disposition.py --help`.
3. Run DD-029 against `docs/datadict/reports/DD028-check-current-v0`.
4. Review the generated disposition report.
5. If root-level `mdo_*` package folders are accepted as generated maintenance evidence, use DD-030 to update stable-exclusion/disposition policy safely.
6. Only after disposition is clean, rerun DD-028 and consider accepting `DDBASE-stable-v1`.

DD-029 does not authorize deletion, moving, exclusion, or promotion by itself. It reports what needs disposition.
