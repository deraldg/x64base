# LabTalk Portal

P0 local campus launcher for LabTalk.

Run from this workspace with:

```powershell
python -m pip install -r .\labtalk\requirements.txt
python .\labtalk\portal\labtalk_portal.py
```

Current behavior:

- reads `registries/portal.yaml`
- reads referenced LabTalk registries
- shows Docs, Apps, Labs, Lessons, Concepts, Proofs, and Runtime sections
- includes a reserved LMS section with a local Moodle-candidate communications pipe
- opens files/directories with the system default handler
- opens a generated diagram's registered `derived_from` source artifact with a
  dedicated one-click action
- runs registered DotTalk++ scripts and commands
- launches registered repo-level PowerShell app launchers
- launches registered WSL build/runtime entry points
- captures transcripts under `proofs/runs`
- audits the portal as a collection of pinned truths and writes Markdown/JSON
  reports under `reports/portal`

Headless proof run:

```powershell
python .\labtalk\portal\labtalk_portal.py --run-item runtime.database_literacy_starter
```

Reserved LMS pipe status:

```powershell
python .\labtalk\portal\labtalk_portal.py --run-item lms.pipe.status
```

This status check is local-only. It reads the outbox and never contacts Moodle.

Truth audit:

```powershell
python .\labtalk\portal\labtalk_portal.py --audit-write
```

The audit checks registry sections, duplicate item IDs, runnable items, proof
records, LabTalk document paths, and the pinned x64base.com SelfDoc/SDLC
publication pages.

DotScript output acceptance:

- registered `dottalk_script` runs reject unknown commands, missing scripts,
  transcript-open failures, and nesting-limit failures even when the runtime
  process returns zero;
- registry items may require proof markers with `required_output_patterns` and
  reject task-specific failures with `reject_output_patterns`;
- the proof transcript records both the runtime process code and the portal's
  output-acceptance decision;
- an intentional negative test must explicitly set
  `use_default_dotscript_reject_patterns: false`.

Runtime path configuration:

```text
labtalk.local.example.yaml
```

Copy it to `labtalk.local.yaml` for machine-local overrides. Relative
`dottalkpp_exe` and `dottalkpp_workdir` values resolve from the repository
root. The checked-in example is deliberately checkout-relative so development,
staging, and public clones cannot silently call one another's runtime.

Registry path policy:

- `portal.yaml` uses repo-relative paths
- PowerShell launchers resolve from the repo root through `..`
- WSL launchers resolve through repo-relative shell scripts so the same entries
  work from `D:\code\ccode`, `C:\x64base`, or another checkout

Launcher section:

- `datarun.ps1`
- `erprun.ps1`
- `biblerun.ps1`
- `wx.run.ps1`
- `wx.next.run.ps1`
- `tk.run.ps1`
- `tk.run.sh`
- `arctictalk.datarun.ps1`
- `arctictalk.datarun.sh`
- `artic.datarun.ps1`
- `artic.datarun.sh`
- `run-cli.ps1`
- `run-erp.ps1`
- `run-bible.ps1`
- `run-wx.ps1`
- `run-wx-next.ps1`
- `run-pydottalk.ps1`
- `wsl_build_dottalkpp.sh`
- `datarun_wsl.sh`
- `dottalkpp/wslrun.sh`

Binding note:

- `run-pydottalk.ps1` expects the LabTalk/pydottalk lane to be built first.
- Canonical Windows bindings build root: `D:\code\ccode\build-labtalk`
- Canonical launcher/build entrypoint: `D:\code\ccode\labtalk\aops\build-labtalk.ps1`

These are interactive launchers. The portal starts them as external PowerShell
or WSL processes instead of trying to capture them as short proof runs.
