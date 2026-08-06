# AI README

Root start point for a new AI assistant working in this repo.

## STOP: Repository Roles Before Any Other Read

| Location | Branch | Role |
| --- | --- | --- |
| `D:\code\ccode` | `development` | Sole development and authoring workspace |
| `C:\x64base` | `main` | Sterilized publication staging for GitHub `main` |

Never work on original changes in `C:\x64base`. Never push or merge
`development` to `main`. A push from `D:\code\ccode` may target only
`development`; only the reviewed staging workflow in `C:\x64base` may update
`main`. See `docs/contracts/REPOSITORY_ROLE_AND_PROMOTION_CONTRACT_V1.md`.

## Purpose

Use this file when prior chat history, hosted memory, or model-specific context
is unavailable. It points to the repo-local AI portal, seed documents, and
runtime start points.

## THIS FILE IS THE ONE FRONT DOOR

There are several onboarding documents in this repo — `AI_PORTAL.md`,
`AI_ASSIMILATION_PORTAL_V1.md`, `AI_ASSIMILATION_BOOK_V1.md`,
`AI_BABY_BOOTSTRAP_CARD.md`, `labtalk/ai_portal/README.md`. They overlap because
they grew at different times. **Do not try to read all of them first.** They are
depth-on-demand, not a queue.

Start here, in this order, and stop when you have enough for the task:

Invariants first, then state: read the 8 KB seed before the perishable resume.

| Step | Read | Why |
| --- | --- | --- |
| 0 | **`labtalk/ai_portal/AI_TIER1_SEED_V1.md` -- read FIRST** | The 8 KB budgeted "safe to act" seed: where you are, what you may do, git safety, house conventions, and a five-question stopping rule. Invariants before state -- the cheapest read and the only one that makes you *safe*, not merely informed. |
| 1 | **Newest `docs/maintenance/SESSION_CLOSEOUT_*.md`** | Fastest true resume. What the last session did, and what it left open. If none exists, skip. |
| 1b | If the BBS daemon is up: AUTH and `BBS READ board.worklog LAST 20` for your lane's live handoff; post one back on finishing (AIF-057, see `AI_BBS_OPERATIONS_RUNBOOK_V1.md` sec 11). | The live, identity-bound pickup/dropoff. Optional and simplex -- the closeout is authority; the board is the fast handoff. Skip if the daemon is down. |
| 2 | `docs/agents/CURRENT_TARGET.md` | The active objective. |
| 3 | `labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` | Where the authoritative tree is; what you may and may not do. |
| 4 | If you can **write** to the repo: `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` | The failure modes specific to an agent that acts, not just proposes. |
| 5 | `labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md` | Which lifecycle owns the task; the gates. |
| 6 | For material work: `labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md` | Mode, change class, actual build target, product/index profile, and smallest sufficient gates. |
| 7 | Before touching source: `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` | The engineering standards + **definition of done**: usage contracts (`@dottalk.usage`), regression doctrine (self-asserting/sandboxed/registered + socket smoke), the lane close-out checklist, and house conventions. Read this so you apply the standards, not reverse-engineer them. |
| 8 | Before touching source: `labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md` | The contract preflight. |
| 9 | Before writing DotScript: `labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md` | Learn the command surface from source + runtime, not memory. |

Everything else — the assimilation book, the bootstrap card, the older portal
docs — is context you pull *when the task needs it*, not a mandatory prefix.

**Looking for a prior report or a received external-AI package** (e.g. "the Grok
post about virtual databases")? Do **not** grep the tree. Look it up by
`report_id`, provider, or concept alias in
`labtalk/registries/ai_report_index.yaml`. Received external-AI packages land
under `docs/maintenance/external_ai_intake/`; the index is kept current by
`python labtalk/ai_portal/audit_trail.py --emit-index`.

**Retired 2026-07-31 (AIF-082, 6.5b):** an eleven-item "Start Here" list used to
sit here, marked superseded but still presented as a numbered reading order under
a "Start Here" heading. A numbered list under that heading is an instruction
regardless of the disclaimer above it, and a cold agent follows instructions. Git
holds it; `git log -- AI_README.md` recovers it. The table above is the only
entry sequence.

If a file named above is missing, record that as drift and continue with the next
available repo-local source.

## AI Portal

The canonical startup order is the table at the top of this file. The older AI
assimilation portal remains a depth-on-demand context source:

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

Public repository identity:

```text
origin: https://github.com/deraldg/x64base.git
public (stable) branch: main
development integration branch: development
```

The `development` branch on origin is the named integration branch (renamed on
GitHub from the earlier dated `homegrown-cnx-20251112-branch`). It carries
current workspace state and moves quickly. Always confirm the checked-out branch
locally before making Git decisions — do not assume a branch name from this file.

Always re-check before making Git decisions:

```powershell
git remote -v
git branch --show-current
git status --short
```

### Remote / hosted agents -- MANDATORY branch enumeration

If you cannot read `D:\code\ccode` (you are a hosted/remote AI seeing only GitHub
and the website), you MUST enumerate the published branches before choosing a
baseline. Do NOT default to `main`:

```
git ls-remote --heads https://github.com/deraldg/x64base.git
```

- `main` is a **lagging public snapshot**, not the authority for active work.
- `development` is **also published on GitHub** and is the **richer, current**
  integration branch -- the baseline for feature, source, and prior-art work.

Baseline on `development` and record its exact commit; use `main` only if the
maintainer names it for the task. "Confirm the branch; do not hard-code a
transient name" means **discover** the branch, not assume `main`. Skipping
enumeration and building against `main` is a hard onboarding failure (observed
2026-08). If you cannot reconcile against `development`, say so explicitly and
mark the work provisional -- never claim `main` == authority.

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
- sterilized publication staging: `C:\x64base`
- staged DotTalk++ projection: `C:\x64base\dottalkpp`
- website source tree: `D:\dev\x64base-site`

Normal source flow:

```text
D:\code\ccode (development authoring)
-> reviewed promotion
-> C:\x64base (sterilized main staging)
-> GitHub main
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

### WSL working environment (added 2026-07-31, AIF-082 / C8)

MSVC is **not** required for engine work. The wsl presets carry
`DOTTALK_INDEX_MODE: LMDB`, so LMDB paths are provable on Linux. A prior session
lost most of its runtime evidence to the belief that MSVC was mandatory.

```bash
cd /mnt/d/code/ccode
./wslbuild.sh                        # configure if needed, build, stage
./wslbuild.sh dottalkpp -a           # build + REGRESSION ALL
./wslbuild.sh dottalkpp -t IDXSTALE  # build + REGRESSION RUN <NAME>
```

Preset `wsl-lean` builds to `build-wsl-lean/`, staged to
`dottalkpp/bin-wsl-lean/`. Run from the data root:

```bash
cd /mnt/d/code/ccode/dottalkpp/data
printf '%s\n' 'CMD1' 'CMD2' | ../bin-wsl-lean/dottalkpp
```

Rules, each of which has already cost a session:

- **Do NOT reintroduce the `vcpkg.json` / `vcpkg-wsl.json` swap.**
  `VCPKG_MANIFEST_FEATURES=index` in the preset already excludes
  tvision/wx/pybind11. An unswapped run under the old scheme destructively
  reconciled the installed tree ("Removing 53/53 tvision:x64-linux"). The
  reasoning is at the top of `wslbuild.sh`; read it before touching the build.
- **`ninja: no work to do` is not proof your change is in the binary.** Two
  differing build stamps in `ABOUT` is genuinely ambiguous. Compare object mtime
  against source mtime, or grep the linked ELF for a string you just added. This
  has already caught one false-green.
- **Capture with `SET ALTERNATE`, never `DOTSCRIPT ... OUT`.** Measured
  2026-07-31, same script and binary: 89 lines vs 42. ALTERNATE is a strict
  superset; `DOTSCRIPT OUT` silently drops everything routed through
  `cli::cmdout`, which is the entire user-facing command surface. The DOTSCRIPT
  help text claims otherwise and is wrong (AIF-081, unfixed).
- **`DOTTALK_INDEX_TRACE` and `DOTTALK_APPEND_TRACE` default ON**
  (`index_manager.cpp:449-457`, `append_support.cpp:74-82`). They are opt-OUT.
  Pin them explicitly for reproducible figures.

### A sandbox is not the WSL host

An AI partner running in a mounted Linux sandbox (for example Cowork) is **not**
in the maintainer's WSL and generally cannot build or run:

| | WSL host | Cowork sandbox, measured 2026-07-31 |
| --- | --- | --- |
| Distro | Ubuntu 24.04 | Ubuntu 22.04.5 |
| glibc | 2.38 | 2.35 |
| GLIBCXX | 3.4.32 | 3.4.30 |
| cmake / ninja | present | **absent** |
| lmdb / sqlite3 / nlohmann / sodium headers | present | **absent** |

The staged `bin-wsl-lean` ELF is readable there but **will not execute** -- it
needs glibc 2.38 and GLIBCXX 3.4.32. The practical ceiling in such a sandbox is
per-translation-unit `g++ -fsyntax-only`. Builds and runs are therefore
maintainer-operated handoffs: the agent prepares the exact command and the
expected evidence.

**A sandboxed agent must run NO git commands.** Even `git status` refreshes the
index, takes `.git/index.lock`, and cannot reliably unlink it across the mount,
which then blocks the maintainer's commits. This happened on 2026-07-31. Read
files freely; run git only host-side. `claim-aif` shells out to `git grep`, so
it is host-side too. See `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md`.

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

**Tooling is cross-platform. This is not negotiable.** x64base is cross-platform C++ on
deliberately cross-compatible libraries, and its tooling holds the same line. Write
**Python 3 + stdlib** (the `tools/**` convention) or DotScript. ASCII output. A `.ps1` or
`.sh` is acceptable only as a thin wrapper around a cross-platform tool, never as the place
logic lives. Recorded exception: the `afb-`/`bbsd-startup` scripts register Windows
Scheduled Tasks and have no cross-platform equivalent.

**Test the tool; do not merely write it.** Two shipped-looking tools carried confident,
wrong claims until they were exercised against purpose-built throwaway fixtures. Untested
tooling does not fail loudly -- it succeeds while being wrong.

Full rules: `labtalk/ai_portal/AI_ENGINEERING_STANDARDS_SEED_V1.md` section 4.

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
Already built?      (grep src/ before asserting absence -- the repo UNDER-reports itself)
Vantage point:      (are you reading state your machine can actually see?)
```

**Those last two are not filler.** Both cost this project real time: a partner reported a
crash-proven write-ahead log as missing because a stale header comment said "stubs" and the
proofs were untracked; and three separate claims about repository state turned out to be
artifacts of an agent sandbox that could not see the maintainer's drives. Absence of
evidence *from where you are standing* is not evidence of absence.

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

**Authoring your closeout (AIF-074 lesson, 2026-07-29 -- three gate rejections
taught this):**

1. START FROM `docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md`. Copy it; do not
   reconstruct the envelope from memory or from any draft that never passed
   the gate.
2. The ENFORCED envelope schema is whatever
   `labtalk/registries/ai_report_audit.yaml` says (currently
   `ai-report-audit-v1` with its exact `required_fields` list). The v2 spec
   (`AI_REPORT_AUDIT_V2_SPEC.md`) is SPECIFIED BUT NOT YET ENFORCED; v2 fields
   are welcome additively, but the schema string and required set must satisfy
   the registry or the pre-commit gate hard-blocks the commit.
3. The envelope is real YAML front matter: `---` on line 1, `---` after, THEN
   the title. A fenced ```yaml block does not count.
4. General trust order when authoring ANY portal artifact, highest first: a
   passing in-tree example > the enforced policy registry > the spec document >
   your memory. Self-generated artifacts that never passed a gate rank below
   all of these.
