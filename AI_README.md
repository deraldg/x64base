# AI README

Root start point for a new AI assistant working in this repo.

## Purpose

Use this file when prior chat history, hosted memory, or model-specific context
is unavailable. It points to the repo-local AI portal, seed documents, and
runtime start points.

## Start Here

Read these files first, in order:

1. `docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md`
2. `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`
3. `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`
4. `docs/agents/AI_BABY_BOOTSTRAP_CARD.md`
5. `docs/agents/CURRENT_TARGET.md`
6. `DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`
7. `docs/contracts/README.md`
8. `docs/contracts/CONTRACT_LIFECYCLE_V1.md`
9. `labtalk/README.md`
10. `labtalk/portal/README.md`
11. `labtalk/ai_portal/README.md`

If a file is missing, record that as drift and continue with the next available
repo-local source.

## AI Portal

The AI assimilation portal is the durable front door:

```text
docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md
```

The seed book is:

```text
docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md
```

The local collection point is:

```text
src/AIPortal/
```

## Repository Info

Local workspace:

```text
D:\code\ccode
```

Current observed Git remote and branch at the time this file was updated:

```text
origin: https://github.com/deraldg/x64base.git
branch: homegrown-cnx-20251112-branch
```

Always re-check before making Git decisions:

```powershell
git remote -v
git branch --show-current
git status --short
```

Repository boundary pointers:

- `docs/governance/README.md`
- `docs/governance/REPO_BOUNDARIES_RUNTIME_GUI_LABTALK_v1.md`
- `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`

Current public repository identities documented in governance:

- `deraldg/x64base` owns runtime/source truth.
- `deraldg/dottalkpp` is currently a product/runtime identity, not a forced
  source split.
- `deraldg/labtalk` owns campus, portal, labs, proofs, and teaching overlays.

## Source Locations

Use the repo-local source map before searching broadly:

| Area | First locations |
| --- | --- |
| C++ runtime and command shell | `src/cli`, `src/xbase`, `src/xindex`, `src/memo`, `src/cnx`, `include` |
| Build and dependency metadata | `CMakeLists.txt`, `CMakePresets.json`, `vcpkg.json`, `vcpkg-wsl.json`, `cmake` |
| Python bindings and bridge work | `bindings/pydottalk`, `src/bindings`, `python_misc`, `py`, `run-pydottalk.ps1` |
| GUI/TUI/workbench lanes | `src/gui`, `src/tv`, `docs/gui`, `run-wx.ps1`, `run-wx-next.ps1`, `tk.run.ps1` |
| Runtime scripts and data | `dottalkpp/data`, `dottalkpp/data/scripts`, `dottalkpp/data/dbf` |
| Documentation, contracts, governance | `docs`, `docs/contracts`, `docs/governance`, `docs/maintenance` |
| AI Friendly and agent bootstrap | `docs/ai-friendly`, `docs/agents`, `AI_README.md` |
| LabTalk campus and portal | `labtalk`, `labtalk/portal`, `labtalk/registries`, `labtalk/labs`, `labtalk/proofs` |
| LabTalk above-runtime staging | `C:\labtalk` |
| Tools and maintenance scripts | `tools`, `scripts`, `dottalkpp/scripts/maintenance`, root launchers |
| Side projects and prototypes | `pycrud`, `Side Projects`, `sqlite-gui`, `dottalk-webui` |

Authority rule: source defines runtime behavior; runtime proof validates it;
HELP/manual/website text must not outrun source and proof.

## Website And Publication Locations

Public website:

```text
https://x64base.com/
```

Public docs start points:

- `https://x64base.com/docs/`
- `https://x64base.com/docs/getting-started/overview/`
- `https://x64base.com/docs/engine/feature-crosswalk/`
- `https://x64base.com/docs/dottalk/dotscript-language-guide/`
- `https://x64base.com/docs/dev/selfdoc-website-publication/`
- `https://x64base.com/docs/dev/important-documents/`

Repo-local website/publication pointers:

- `README.md`
- `docs/contracts/WEBSITE_SELFDOC_PUBLICATION_CONTRACT_V1.md`
- `docs/maintenance/SELF_DOC_APPS_INDEX_v1.md`
- `docs/maintenance/SELF_DOC_SUBSYSTEM_MATRIX_v1.md`
- `labtalk/portal/README.md`
- `C:\labtalk\README.md`
- `C:\labtalk\STAGING_POLICY.md`
- `C:\labtalk\publication\labtalk-website-pipeline.md`

The website is a publication surface, not runtime proof. When website text and
source/runtime evidence disagree, follow the authority order in
`docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`.

## Promotion And Staging Convention

Use this as the default local authority map:

- primary implementation/source truth: `D:\code\ccode`
- DotTalk++ runtime tree: `D:\code\ccode\dottalkpp`
- Laboratory Campus / LabTalk tree: `D:\code\ccode\labtalk`
- clean staging mirror: `C:\x64base`
- staged DotTalk++ mirror: `C:\x64base\dottalkpp`
- website source tree: `D:\dev\x64base-site`

Normal source flow:

```text
D:\code\ccode -> C:\x64base -> GitHub repository
```

Normal website flow:

```text
D:\dev\x64base-site -> build/public artifact -> GitHub Pages -> x64base.com
```

Normal documentation evidence flow:

```text
D:\code\ccode source/runtime
-> HELP / metadata / comments / contracts
-> SelfDoc / MDO / manualgen reports
-> reviewed manual sections
-> reviewed website summaries
```

Do not reverse the authority chain by copying website prose into manuals or
source docs as technical truth.

## LabTalk Portal

Launch the LabTalk portal from the repo root:

```powershell
python .\labtalk\portal\labtalk_portal.py
```

or:

```powershell
.\launch_portal.ps1
```

Portal docs:

```text
labtalk/portal/README.md
```

Headless checks:

```powershell
python .\labtalk\portal\labtalk_portal.py --audit-write
python .\labtalk\portal\labtalk_portal.py --run-item runtime.database_literacy_starter
```

Active **Alpha/Experimental** AI Portal hardening work:

```text
labtalk/ai_portal/README.md
labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md
labtalk/registries/ai_portal.yaml
```

## Runtime Start Points

Main DotTalk++ runtime:

```powershell
& D:\code\ccode\build\src\Release\dottalkpp.exe
```

Build:

```powershell
cmake --build build --config Release --target dottalkpp
```

Convenience launchers from the repo root:

```powershell
.\run-cli.ps1
.\run-erp.ps1
.\run-bible.ps1
.\run-wx.ps1
.\run-pydottalk.ps1
.\run-pycrud.ps1
```

## Native Orientation Commands

Inside DotTalk++ prefer read-only orientation first:

```text
MAINT
MAINT USAGE
MAINT AI
MAINT AI DASHBOARD
MAINT AI ASSIMILATE
MAINT CONTRACTS
CMDHELP MAINT
CMDHELPCHK
HELP
```

## Coding Standards, Conventions, And Rules

Start with pointers instead of inventing a new style guide:

- `.editorconfig` for charset, indentation, final newline, whitespace, and line
  ending defaults.
- `.gitattributes` for CRLF/LF and binary file handling.
- `.gitignore` for generated build/runtime artifacts and local state.
- `.github/PULL_REQUEST_TEMPLATE.md` for expected PR review shape.
- `.github/CODEOWNERS` for ownership hints.
- `.github/copilot-instructions.md` for GitHub Copilot-specific repository
  instructions.
- `docs/maintenance/DOTTALKPP_SDLC_CHARTER_v0.md` for runtime SDLC gates.
- `docs/maintenance/MAINTENANCE_SCRIPT_ROOT_POLICY_v1.md` for script placement
  and regression bootstrap rules.
- `docs/contracts/README.md` and `docs/contracts/CONTRACT_LIFECYCLE_V1.md` for
  durable rules and contract promotion.
- `docs/database/DATABASE_SAFETY_CONTRACT_V1.md` for database mutation safety.
- `docs/database/VALUE_LOCALE_COLLATION_CONTRACT_V1.md` for value, locale, and
  collation policy.
- `docs/governance/manual_safety_rules.md` and
  `docs/governance/authority_order.md` for manual/governance rules.

Observed local formatting defaults:

- UTF-8.
- Spaces, 4-space indentation by default.
- CRLF by default for most files.
- LF for `.sh`, `.yml`, and `.yaml`.
- Markdown does not trim trailing whitespace by `.editorconfig`.

General implementation conventions:

- Prefer existing subsystem patterns over new abstractions.
- Keep edits scoped to the owning lane.
- Do not silently move runtime truth into LabTalk or publication surfaces.
- For runtime behavior changes, identify HELP/CMDHELP/CMDHELPCHK and proof
  impact.
- For `.dts` regression scripts, bootstrap the runtime environment explicitly;
  see `docs/maintenance/MAINTENANCE_SCRIPT_ROOT_POLICY_v1.md`.

## Working Rules

- Do not rely on lost chat history or model memory.
- Use repo-local evidence.
- Preserve dirty and untracked work unless the user explicitly authorizes
  cleanup.
- Inspect source and authority docs before changing files.
- Treat raw AI interaction material as source material, not authority.
- Promote only after material is classified, distilled, anchored, routed, and
  reviewed.
- Default to report-only when touching DBF/CDX/LMDB data, HELP tables,
  metadata, generated catalogs, manuals, proofs, backups, or archives.

## Minimal New-AI Checklist

```text
Current request:
Owning lane:
Files read:
Source of truth:
Generated/candidate files:
Mutation risk:
Smallest safe action:
Proof/test:
Residual risk:
```

## Closeout Shape

After meaningful work, report:

```text
Changed:
- path and purpose

Verified:
- build, runtime command, report, readback, or reason verification was not run

AI-facing docs updated (or reason not applicable):
- path and what changed
- OR: "no lane state changed this session"

Still open:
- review, proof, drift, or promotion gate
```

The third block is the **closeout-updates-startup** gate (AIF-006). If the
session changed lane state — objective, branch, authority pointer, contract,
dashboard status, intake row — the AI-facing document describing that state
must be updated in the same session, or the omission explicitly justified. See
`AI_PORTAL.md` -> "Closeout Updates Startup".
