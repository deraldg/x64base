# x64base AI Portal

Status: **Alpha/Experimental**
Audience: AI development partners and maintainers
Published location: repository root as `AI_PORTAL.md`

This is the public AI Portal summary for ChatGPT, Codex, Gemini, Grok, Copilot,
and other AI systems asked to review or change x64base.

It is not a student portal for accessing an AI service. It prepares an AI to
work as a development partner using repo-local authority, contracts, runtime
evidence, safety gates, and task recipes.

## Mandatory Start

`AI_README.md` is the one canonical front door. Follow its ordered table first:
newest session closeout, current target, authority seed, local-access checklist
when applicable, SDLC fast start, source-mutation gate, and DotScript readiness
when `.dts` work is involved.

After that canonical start, use these task-specific sources only when relevant:

- [`labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`](labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md)
- [`labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md`](labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md)
- [`labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`](labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md)
- [`labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`](labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md) when DotTalk++ or DotScript is involved
- [`labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md`](labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md) when work will return as a patch or package
- [`labtalk/ai_portal/README.md`](labtalk/ai_portal/README.md) for the complete Alpha/Experimental lane

Then inspect only the contracts, source, tests, HELP, and proof material needed
for the assigned task.

## Authority

```text
D:\code\ccode
  authoritative development source and runtime work
        |
        | reviewed, relevant, clean files only
        v
C:\x64base
  clean Git publication staging repository
        |
        | commit and push
        v
github.com/deraldg/x64base
  public snapshot used by outside AI systems
```

GitHub is the public baseline, not authority over unpublished development work.
An outside AI must identify the exact public commit on which its proposal is
based.

### What `C:\x64base` Is — and Is Not

Maintainer-declared, 2026-07-14. This statement supersedes any other
description of `C:\x64base` in this repository.

`C:\x64base` **is** the clean staging repository that publishes to
`github.com/deraldg/x64base`. It is a promotion gate, not a workspace.

`C:\x64base` is **not**:

- a backup copy of `D:\code\ccode`;
- a second development tree;
- a competing source authority;
- a place to make original changes.

Consequences:

- Original work happens in `D:\code\ccode` and is promoted outward. Never the
  reverse.
- Only reviewed, relevant, clean files are promoted. Development litter —
  `*.bak_*` sidecars, `*.before_mdo_*` snapshots, scratch notes, generated
  reports, runtime data churn — must not ride along.
- Staging cleanliness is a publication property. Because
  `src/CMakeLists.txt` uses `file(GLOB_RECURSE ...)`, an untracked `.cpp` in
  staging will compile locally while remaining absent from GitHub. A green
  build does not prove publication completeness. Verify with `git ls-files`.
- Development-tree dirtiness in `D:\code\ccode` is normal and is **not** a
  release risk signal. Release readiness is judged from staged validation
  state in `C:\x64base`.

Any document that describes `C:\x64base` as a backup is stale. Report it as
drift rather than acting on it.

## Source Mutation Rule

Before changing source code, report:

```text
Target source files:
Owning subsystem:
Baseline commit:
Owning lifecycle and SDLC lane:
Truth state, proof state, risk class, and next gate:
Contracts read:
Applicable @dottalk.contract / @dottalk.usage blocks:
Constraints and conflicts:
Expected behavior change:
Proof/test plan:
```

If the request conflicts with an active contract, stop and describe the
conflict. Do not rewrite the contract merely to make a patch convenient.

## Outside-AI Delivery Rule

Hosted AI systems do not modify `D:\code\ccode` directly. Return a reviewable
change package tied to the stated commit. The package must contain:

1. a unified patch;
2. a manifest of changed and new files;
3. contracts and source usage blocks read;
4. behavioral effects, mutations, and risks;
5. build and test instructions;
6. expected runtime proof;
7. unresolved questions, drift, or conflicts.

The manifest must preserve the owning lifecycle, SDLC lane, truth state, proof
state, risk class, next gate, and status. PLDC or publication work cannot bypass
the underlying DotTalk++, maintenance, or LabTalk SDLC gate.

Do not include binaries, build directories, generated runtime data, unrelated
formatting, cleanup, or branch operations.

## Local Integration Rule

Returned packages are reviewed and applied selectively in `D:\code\ccode`.
They are compiled and tested there first. Only proven, relevant files are
promoted to `C:\x64base`, verified again in staged form, committed, and pushed.

Website work is separate. When verified behavior changes public documentation,
update and build `D:\dev\x64base-site`, then commit and publish that repository
with a reference to the supporting x64base source commit.

## Required Closeout

Report each state separately:

- patch reviewed;
- development files changed;
- development build/test result;
- files promoted to `C:\x64base`;
- staged verification result;
- x64base commit and pushed branch;
- website files changed and build result;
- website commit and pushed branch.

Never claim a later state merely because an earlier one succeeded.

### Closeout Updates Startup (AIF-006)

If a session changed **lane state** — a new or superseded contract, a promoted
item, a new commit or branch, a dashboard status change, a new intake row, or a
corrected authority statement — then closeout must also update the AI-facing
document that describes that state:

| If this changed | Update |
| --- | --- |
| The current objective | `docs/agents/CURRENT_TARGET.md` |
| Branch, remote, or authority pointers | `AI_README.md` |
| Lane status or work log | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` |
| A candidate's review status | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` |

This is not a separate remembered chore. It is part of closeout. A session is
not complete until this step is done, or explicitly declined with a stated
reason (for example: "read-only review, no lane state changed").

Rationale, recorded so it is not relitigated: on 2026-07-14
`docs/agents/CURRENT_TARGET.md` was found to name a directory that did not
exist and to describe `C:\x64base` as a backup rather than the staging
repository. It had drifted for weeks because updating onboarding material was
an unenforced good intention rather than a gate. The rest of this project's
evidence system exists to prevent exactly that failure mode; onboarding
material was the one lane not covered by it.

An AI-facing doc update is never self-certifying. It is proposed, reviewed, and
promoted like any other contract or HELP change, under the authority order in
`docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`.

### Leave a Session Closeout

Updating the scattered pointers (above) keeps the *current state* correct. But a
pointer does not tell the next session *what happened* or *why*. For that, a
session that changed lane state also drops a dated closeout:

```text
docs/maintenance/SESSION_CLOSEOUT_<topic>_<YYYY-MM-DD>.md
```

Template: `docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md`.
Worked example: `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md`.

Then add one row to the **Session Log** in
`docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`.

Why a closeout and not just the pointers: the pointers are a snapshot; the
closeout is the trail. A new session's fastest true start is "read the newest
session closeout" — it resumes from one file instead of re-deriving state from
the whole tree. This is what turns the portal from a filing cabinet into a
memory. The chat is never the record; the closeout is.

## AI Session Operator Contract

Purpose: keep AI work aligned with the real promotion flow and avoid false risk
signals from development-only state.

### Evaluation Rule

Do **not** treat `D:\code\ccode` working-tree dirtiness as release risk by
itself. Release and publish readiness are judged from the staged validation
state in `C:\x64base`.

### Required Status Reporting Format

Report all progress and closeout by stage:

1. **Dev** (`D:\code\ccode`)
2. **Promoted to Staging** (`C:\x64base`)
3. **Validated in Staging** (build / confirm / test / proof)
4. **Published** (commit, branch, remote push status)

Never claim a later stage succeeded because an earlier stage succeeded.

### Mutation Guard

Default to report-only unless mutation is explicitly authorized. For source
mutations, state target files, subsystem, expected behavior change, and
validation plan before applying edits.

## Local-Access AI Rule

The Outside-AI Delivery Rule above governs hosted AI systems that cannot write
to disk. Some AI partners **do** have direct write access to `D:\code\ccode`.
They are not thereby exempt from any gate — write access is a capability, not
an authorization.

A local-access AI must:

- complete the same mandatory reads, contract preflight, and SDLC lane
  declaration required of any other partner;
- obtain explicit maintainer authorization before mutating, and keep the
  change narrowly scoped to the authorized task;
- make original changes only in `D:\code\ccode`, never directly in
  `C:\x64base` or on GitHub;
- preserve dirty and untracked maintainer work rather than "cleaning" it;
- treat DBF/CDX/LMDB data, HELP tables, metadata catalogs, generated
  catalogs, publication outputs, fixtures, backups, and archives as
  report-only unless the current task names that mutation;
- leave branch operations to the maintainer;
- report by stage, and never report a stage it did not reach.

Direct file access removes the packaging step. It does not remove the gate.
An AI that can edit the repository without being asked is the failure mode this
portal exists to prevent.
