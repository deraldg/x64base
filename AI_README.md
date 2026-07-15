# AI README

Root start point for a new or resumed AI assistant working in this repository.

## One Canonical Front Door

This file defines the canonical entry order. Other onboarding documents are
reference shelves or task-specific depth, not competing startup queues.

Read in this order and stop when the current task has enough grounded context:

| Step | Read | Why |
| --- | --- | --- |
| 0 | newest `docs/maintenance/SESSION_CLOSEOUT_*.md` | Fastest true resume: what changed, what was proved, and what remains open. |
| 1 | `docs/agents/CURRENT_TARGET.md` | Current objective and public baseline. |
| 2 | `labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md` | Authority roots, promotion chain, branch continuity, and permission boundary. |
| 3 | `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md` when the AI can write or run local tools | Failure modes specific to an acting agent. |
| 4 | `labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md` | Owning lifecycle, lane, proof state, risk, and next gate. |
| 5 | `labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md` before source changes | Mandatory contract preflight. |
| 6 | `labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md` before writing or running DotScript | Current syntax, state, mutation classification, and transcript proof. |
| 7 | `labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md` for hosted/outside proposals | Exact-baseline package and local-integration contract. |

Then inspect only the contracts, source, tests, HELP, proof, and publication
material needed for the assigned task.

## Authority

```text
D:\code\ccode
  authoritative development source, runtime truth, and development history
        |
        | reviewed coherent source changes and selected public projection
        v
C:\x64base
  disposable curated publication staging
        |
        | reviewed commit and push
        v
github.com/deraldg/x64base
  public snapshot
```

`C:\x64base` is not a backup, second development tree, or source authority.
Original work belongs in `D:\code\ccode`. A public-only change is not integrated
until reconciled into authoritative development and proved there.

## Git Pointers

Static onboarding text must not pretend a transient local development branch is
current.

```text
Public repository: https://github.com/deraldg/x64base
Public branch:     main
Development root:  D:\code\ccode
Development branch: discover locally; never guess or inherit from an old chat
```

Before any Git decision, inspect the actual workspace and remote:

```powershell
git remote -v
git branch --show-current
git status --short
git ls-remote --heads origin
```

`origin/*` refs are a cache, not proof of current GitHub state.

## Task Classification

At task start classify the work as one or more of:

- authoritative development;
- publication staging;
- public-repository review or correction;
- website/publication;
- read-only audit.

Record:

```text
Current request:
Owning lifecycle:
SDLC lane:
Authority root:
Public baseline commit:
Files and contracts read:
Truth state:
Proof state:
Risk class:
Mutation scope:
Smallest safe action:
Proof plan:
Next gate:
Residual risk:
```

Unknown fields remain `unknown`; they are not guessed.

## Source and Runtime Start Points

| Area | First locations |
| --- | --- |
| CLI and runtime | `src/cli`, `src/xbase`, `src/xindex`, `src/memo`, `include` |
| Build | `CMakeLists.txt`, `CMakePresets.json`, `vcpkg.json`, `cmake` |
| Bindings | `bindings/pydottalk`, `src/bindings`, `run-pydottalk.ps1` |
| GUI/TUI | `src/gui`, `src/tv`, `docs/gui` |
| Runtime scripts/data | `dottalkpp/data`, `dottalkpp/data/scripts`, `dottalkpp/data/dbf` |
| Contracts/governance | `docs/contracts`, `docs/database`, `docs/governance` |
| AI Portal | `AI_PORTAL.md`, `labtalk/ai_portal`, `labtalk/registries/ai_portal.yaml` |
| LabTalk | `labtalk`, `labtalk/portal`, `labtalk/labs`, `labtalk/proofs` |
| Website source | `D:\dev\x64base-site` |

Authority order:

```text
source defines
runtime/tests prove
HELP explains
metadata organizes
SelfDoc preserves provenance
MDO/manualgen assembles reviewed documentation
website summarizes reviewed truth
AI Portal selects task-relevant context
```

## Native Read-Only Orientation

Inside DotTalk++ begin with read-only surfaces:

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

Before authoring DotScript, query the current runtime and inspect a proven
neighbor script. Do not translate remembered xBase, SQL, or shell syntax into
DotScript.

## Working Rules

- Write access is capability, not authorization.
- Preserve dirty and untracked maintainer work.
- Do not clean, reset, broadly stage, delete, change branches, commit, push, or
  publish without current-task authorization.
- Treat DBF/CDX/CNX/LMDB data, HELP tables, metadata catalogs, generated
  catalogs, publications, fixtures, backups, and archives as report-only unless
  explicitly named for mutation.
- Ground public documentation against the public target, not unpublished dev.
- A successful build does not prove publication completeness; verify required
  source is tracked.
- Long clean builds are maintainer-operated unless explicitly authorized.
- A zero DotScript process exit code is not proof; inspect the transcript and
  assert source path plus specific data.

## Publication State Rule

Development proof and public availability are separate states. For example, the
product/index edition system may be implemented and proved in authoritative
development while public `main` still exposes only the presets documented in
`BUILDING.md`. Label both states explicitly.

## Closeout

After meaningful work report each reached stage separately:

```text
Changed in development:
Development proof:
Promoted to staging:
Staging proof:
Committed:
Pushed/published:
Website state:
AI-facing state documents updated:
Still open / next gate:
```

If lane state changed, update the relevant startup pointer in the same task:

- current objective -> `docs/agents/CURRENT_TARGET.md`;
- branch/remote/authority pointers -> `AI_README.md`;
- lane status/session log -> `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`;
- candidate status -> `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.

Also leave a dated `docs/maintenance/SESSION_CLOSEOUT_<topic>_<YYYY-MM-DD>.md`
for state-changing work. The chat is not the durable record.
