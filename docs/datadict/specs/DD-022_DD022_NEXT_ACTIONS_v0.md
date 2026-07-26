# DD-022 Next Actions v0

Recommended next steps:

1. Review the DD-022 orchestrator contract.
2. Decide whether DD-023 should be a repo-installation patch package or another report-only readiness audit.
3. Before installing tools into the repo, select the stable target paths from DD-021/DD-022.
4. Keep the first repo-integrated orchestrator in dry-run/report-only mode.
5. Do not add catalog promotion, HELP mutation, or documentation regeneration behavior until separate gates are accepted.

Recommended DD-023 options:

```text
Option A: DD-023 Repo Tool Installation Plan
  Report-only patch plan for copying reviewed tools into tools/datadict.

Option B: DD-023 Orchestrator Dry-Run Against Repo Package
  Run DD-022 plan-only/source-scan mode against the corrected repo zip extraction and report exact outputs.

Option C: DD-023 Change-Detection/Diff Contract
  Define how one redocumentation run compares to a previous run.
```

Preferred next move: DD-023 Change-Detection/Diff Contract, because repeatability becomes much more useful when each run can show what changed.
