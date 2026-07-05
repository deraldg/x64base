# LabTalk Portal

P0 local campus launcher for LabTalk.

Run from this workspace with:

```powershell
python .\labtalk\portal\labtalk_portal.py
```

Current behavior:

- reads `registries/portal.yaml`
- reads referenced LabTalk registries
- shows Docs, Apps, Labs, Concepts, Proofs, and Runtime sections
- opens files/directories with the system default handler
- runs registered DotTalk++ scripts and commands
- launches registered repo-level PowerShell app launchers
- launches registered WSL build/runtime entry points
- captures transcripts under `proofs/runs`

Headless proof run:

```powershell
python .\labtalk\portal\labtalk_portal.py --run-item runtime.database_literacy_starter
```

Runtime path configuration:

```text
labtalk.local.example.yaml
```

Copy it to `labtalk.local.yaml` for machine-local overrides.

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

These are interactive launchers. The portal starts them as external PowerShell
or WSL processes instead of trying to capture them as short proof runs.
