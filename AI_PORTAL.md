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

Before selecting gates, apply the scope-calibration seed. Name the operating
mode, change class, actual build target, product profile, and index profile.
`xbase` engine-only, full `dottalkpp`, and the `LEAN` / `PROFESSIONAL` /
`EDUCATIONAL` / `DEVELOPMENT` compositions are legitimate different boundaries;
do not silently plan against the largest assembly.

After that canonical start, use these task-specific sources only when relevant:

- [`labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`](labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md)
- [`labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md`](labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md)
- [`labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md`](labtalk/ai_portal/SCOPE_CALIBRATION_SEED_V1.md)
- [`labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`](labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md)
- [`labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`](labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md) when DotTalk++ or DotScript is involved
- [`labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md`](labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md) when work will return as a patch or package
- [`labtalk/ai_portal/README.md`](labtalk/ai_portal/README.md) for the complete Alpha/Experimental lane

Then inspect only the contracts, source, tests, HELP, and proof material needed
for the assigned task.

## AI-Friendly Dev-Tools — Ask for Limited Permission First

x64base ships tools designed for AI development partners to extend and exercise the
engine directly:

- **Runtime DEF family** — `DEFCMD` / `UNDEFCMD` (commands) and `DEFFN` / `UNDEFFN`
  (expression functions): mint **session-only** commands/functions at runtime, no rebuild.
  Bodies are currently inert (echo / return text); custom functions resolve in
  `?` / `CALC` / `WHERE` and compose with builtins. See `RUNTIME_DEF_FAMILY_LANE_V1.md`.
- **`EXAMPLE`** — minimal token-routing / command-wiring testbed built-in.
- The **write → compile → run → read-output loop** for agents that build and run `dottalkpp`.

**Permission protocol (binding).** Any agent — AI or human — must obtain *limited*,
scoped permission before using these dev-tools. This requirement is **global**; the
project owner (Derald Grimwood) is the sole exemption. Ask for the specific tool and the
specific task — do not assume blanket access.

The technical gate (`include/cli/ai_devtools_policy.hpp`) is shipped **dormant**: it
permits by default, so nothing is blocked today. The requirement is enforced by git
review and the promotion gate until the owner activates enforcement
(`DOTTALK_DEVTOOLS_REQUIRE_PERMISSION=1`, with a scoped `DOTTALK_DEVTOOLS_GRANT=1`).

Loop-closing agents (e.g. Codex) are **not gated** — the compile/run loop stays smooth —
but are bounded by git visibility, an isolated dev tree, the host-shell block
(`DOTTALK_ALLOW_HOST_COMMANDS` off by default), and the human-reviewed promotion gate.

Full threat model and controls:
[`docs/maintenance/AI_DEV_TOOLS_SECURITY_DOCTRINE_V1.md`](docs/maintenance/AI_DEV_TOOLS_SECURITY_DOCTRINE_V1.md).

The durable identity / RBAC / authorization **backing** for this permission protocol is being
built as **`project.x64base.identity`** (AIF-045): `USERS → TEAM_MEMBER → TEAM_ASSIGNMENT →
{ROLE, PERMISSION, AUTHORIZATION_GRANT}`, with the operational security policy kept independent
as the final constraint (*permission = eligibility; authorization = this action*). Contract v1 +
a proven permission resolver exist; see
[`docs/maintenance/IDENTITY_RBAC_MANAGEMENT_LANE_V1.md`](docs/maintenance/IDENTITY_RBAC_MANAGEMENT_LANE_V1.md)
and [`docs/maintenance/IDENTITY_RBAC_CONTRACT_V1.md`](docs/maintenance/IDENTITY_RBAC_CONTRACT_V1.md).

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

### External toolchain paths (agents stumble here)

The build is **not** self-contained: it resolves its dependency toolchain from an
environment variable, so the path is deliberately never hardcoded in the repo —
which is exactly why agents that assume a default location fail to configure.

- **vcpkg** — the build reads `$env:VCPKG_ROOT` (see `CMakePresets.json` and
  `build.ps1`; some presets use `$env:VCPKG_INSTALLATION_ROOT`). On this
  maintainer's machine the vcpkg tree lives under the **OneDrive root** —
  `%OneDrive%\vcpkg` — **not** the `C:\Users\deral\vcpkg` default that agents
  habitually assume, and not inside either source tree. Resolve it from
  `$env:VCPKG_ROOT` (or `vcpkg` on `PATH`); never hardcode a guessed path. The
  CMake toolchain file is `%VCPKG_ROOT%\scripts\buildsystems\vcpkg.cmake`.
- Rule: when a path lives outside `D:\code\ccode` and `C:\x64base` (toolchains,
  OneDrive backup drops under `%OneDrive%\dev\dottalkpp_drops`, the website tree),
  it is resolved from an environment variable or a documented constant — never
  assumed. If an agent is "stumbling over" a path, the fix is to read the env var,
  not to invent a default.

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

## Representative by Design — the Teaching-Grade Standard (AIF-037)

DotTalk++ / x64base is a teaching system. The engine source, the LabTalk lessons,
and the sample databases are all read by learners as worked examples. Whatever they
model, students learn. So the code, the lab exercises, and the sample data must be
**representative** — idiomatic, best-practice, and free of the anti-patterns a
reviewer would flag — because here **source teaches**, and source must be worth
teaching from.

This extends the authority chain: *runtime proves, source defines, HELP explains —
and source teaches.*

Concretely:

- Prefer established best practices wherever they apply: single-source-of-truth
  (DRY), clear separation of concerns, named contracts over ad-hoc code, and
  behavior backed by tests.
- **Duplication a review would flag is a teaching defect, not merely a maintenance
  cost.** Consolidate to one canonical implementation rather than copying (e.g. one
  shared comment/line lexer, not five drifting copies).
- **The Rule of Three (maintainer's rule of thumb):** the first time you write
  something it's code; the second time you tolerate the copy; **the third time you
  write the same thing, turn it into a function or procedure.** A third copy is the
  signal to consolidate, not a decision to defer. (The comment/line lexer was at
  five — long past the line.)
- Sample databases and lab schemas must be well-formed and the example queries
  idiomatic — representative of how a practitioner would actually build it, not a
  toy that models bad habits.
- When a shortcut is genuinely unavoidable, mark it explicitly (a status label, a
  TODO with a lane reference) so it is never mistaken for the recommended pattern.

This is a standard, not a stylistic preference: a change that ships a
non-representative pattern into teachable surface (engine source, lessons, sample
DB) is incomplete until the pattern is made representative — or explicitly labeled
non-exemplary with a tracked follow-up. First application: consolidating the
duplicated comment/line-lexing helpers (five drifting copies) into one shared
module.

### Observed failure modes (proven case studies)

The two rules above — *one canonical implementation* (DRY) and *one authoritative
tree, promoted outward* — are the same principle at two scales: a file and a
repository. Each has now failed in practice during AIF-043, and the failures are
recorded here as scar tissue so the doctrine carries its own evidence rather than
standing on assertion alone.

**1. Duplicate-implementation shadow (file scale — the single-canonical rule).**
AIF-043 (in-memory tables) burned days on a symptom that read as impossible:
`CREATE X64` wrote the table to disk while `USE`/open read it back from RAM — same
engine, same path string, same in-process registry, opposite results. The root
cause was a *second* `create_dbf`: a stale `src/core/dbf_create.cpp` duplicating
`src/xbase/dbf_create.cpp`. Both defined the same symbol. The CLI glob compiled the
`src/core` copy into the executable, and at link **an executable's own object
silently wins over a static-library member**, so the exe ran the stale,
non-ramfs-aware `create_dbf` while `open` — which existed only once, in
`xbase.lib` — used the correct RAM path. No clean rebuild could surface it because
both copies compiled cleanly; the tell was a diagnostic string present in
`xbase.lib`'s object yet absent from the linked `.exe`. This is precisely the
"duplication a review would flag" this doctrine warns against, and it cost real
time *because the duplicate was silent*. Fix: delete the dup (one canonical
`create_dbf`), plus a configure-time **duplicate-basename shadow guard** that fails
the build loudly if any CLI source ever again shares a filename with a
library-owned object. Evidence: `AIF_043_M1_PROOF_GREEN_CLOSEOUT_V1`.

> Lesson made concrete: a silent duplicate is worse than a loud one. When a
> duplicate cannot be deleted immediately, add a guard that turns its recurrence
> into a build failure, not a future debugging session.

**2. Dual-authoring the staging tree (repo scale — the promote-outward rule).**
While promoting AIF-043 to `C:\x64base`, the same documentation fix was nearly
authored *independently in both trees*, and staging files were briefly hand-edited
directly. That is the repository-scale form of the identical defect: two copies of
the truth, free to drift. The instant staging is edited as if it were a source,
neither tree is authoritative and the promotion gate becomes a fork. Correct flow,
per this portal: author once in `D:\code\ccode`, promote the identical artifact
outward, verify it in staged form, commit, push — and prove `source == mirror` with
a byte-level diff, never re-type it downstream. Evidence: this session's `dotref.hpp`
audit fix was authored in ccode, copied verbatim to staging, and confirmed identical.

> Lesson made concrete: the test that a mirror is still a mirror is a byte-diff
> against its source, run at promotion time. If the two differ by anything typed by
> hand downstream, a fork has already begun.

Both reduce to one sentence: **there must be exactly one authoritative copy of any
given thing — one implementation, one tree — and every other copy must be derived
from it and provably identical, or the system has no source of truth.**

## Projects, Lanes, and Promotion (AIF-040)

Work is organized in three tiers, and items move between them:

- **Project** — a first-class program with its own identity and lifecycle,
  registered in `labtalk/registries/projects.yaml`, owning a set of lanes
  (e.g. `project.x64base.runtime`, `project.labtalk.campus`). Project ids validate
  in the AI report-audit envelope.
- **Lane** — a work track within a project (or a standalone intake lane, `AIF-NNN`),
  carrying a lane doc, milestones, and proof gates.
- **Milestone** — a proven step within a lane.

**A lane may be promoted to a project** when it outgrows a single track — when it
spawns sub-lanes, gains an independent lifecycle, or becomes a program others build
under. Promotion is: create a `projects.yaml` entry (`id: project.<domain>.<name>`
with its own `lanes:` list), keep the originating `AIF-NNN` intake row as the
promotion record, and let child lanes reference the parent project. Demotion is
equally valid: a speculative project that stays small folds back to a lane. The
precedent is already in the tree — **LMS** is a lane in `project.labtalk.campus`
*and* its own `project.labtalk.lms`.

Every `AIF-NNN` intake lane SHOULD name its parent project (or `standalone`) so the
lane and project registries stay reconciled. This keeps the two views — the intake
queue (work in flight) and `projects.yaml` (programs and their lanes) — from
drifting apart.

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

## Staying Current — the Live Agent Sync Page (doc-only portal)

Outside AI systems read GitHub, and this `AI_PORTAL.md` moves only on full engine
snapshots — so between snapshots an outside AI's picture of lane state, Phase-0
decisions, and doctrine can go stale. Hosted partners (e.g. ChatGPT) also cannot read
the maintainer's local `D:\code\ccode` tree at all. The **doc-only live portal** closes
that gap:

- A public, frequently updated page — **AI Agent Sync — Live Current State**, at
  `/docs/labtalk/agent-sync` on the x64base website — carries the current governance
  surface (working agreement, doctrine, the canonical-Value decision, active-track
  state, open questions), dated, and refreshed at each maintainer-session closeout.
- It publishes on the **website's** cadence, independent of engine snapshots, so it is
  the freshest public state an outside agent can reach without local-drive access.
- Source: `D:\dev\x64base-site/content/docs/labtalk/agent-sync.mdx`. It is
  documentation only — no engine source, no build dependency — so it can be republished
  as often as state changes.
- Precedence: the live Agent Sync page is fresher than this GitHub portal between
  snapshots; the maintainer's `D:\code\ccode` reconciliation remains authoritative over
  both. The page is not autonomous authority and does not bypass a proof gate.
- **Pseudo-Chat (the return lane):** the Agent Sync page is two-way, not just broadcast.
  Its **Pseudo-Chat** section carries a partner-reply protocol and a dated reply log, and
  its Open questions are a tracked Q/Status table. It is deliberately **not real-time** —
  it moves at closeout cadence, hence "pseudo." An outside partner's answers are
  transcribed into the Pseudo-Chat log at closeout and flip the matching Open question's
  Status, so the dialogue is visible on one page instead of scattered across chat
  transcripts. It is the return path that makes the doc-only portal a loop, not a megaphone.
  Full spec: `docs/maintenance/PSEUDO_CHAT_RETURN_LANE_V1.md` (what/why/not, roles, the
  `RE:` reply protocol, the turn cycle, a worked example, and the closeout integration).

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

### Document As You Work (AIF-024)

Closeout is a **rollup, not a reconstruction**. Document each material step as it
happens, while the facts are still in hand — do not defer all recording to the
end and re-derive it from memory or the chat.

A step is material (and gets recorded when it lands, not later) when it:

- changes source, data, or an AI-facing doc;
- produces a build or proof result, a hash, or a measured number;
- makes a decision that constrains later work, or discovers a finding.

Record it in the appropriate durable place as you go: the running Session
Closeout / progress log, an intake or contract row, a proof transcript with its
hash. The chat is never the record. If a step's evidence (a hash, a timing, a
before/after count) is not captured at the moment it is produced, it is treated
as **not proven** — a later recollection does not substitute.

Rationale, recorded so it is not relitigated: reconstructing a session's trail at
the end loses the evidence that was cheapest to capture in the moment (exact
hashes, timings, the reason a path was rejected) and invites overclaiming. The
2026-07-16 corrective audit (AIF-021) is the worked example — a session that
deferred its records understated its own diff, skipped the Session Log row, and
called surfaces ready before proof. Documenting continuously makes AIF-006
closeout a summary of an already-written trail instead of a scramble.

This does not add a new artifact. It uses the same durable places AIF-006 and the
session-closeout convention already name; it only fixes **when** they are written
— continuously, not at the end.

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
| The outside-AI live current state (lane / decision / doctrine an external partner relies on) | `D:\dev\x64base-site/content/docs/labtalk/agent-sync.mdx` — refresh its content + freshness date, transcribe any external-partner replies into the **Pseudo-Chat log** (and update the matching Open-question Status), then republish the site |

The Agent Sync row above is what keeps the doc-only live portal honest: if a closeout
changed something an outside AI (e.g. ChatGPT) depends on — a lane's proven state, a
Phase-0 decision, a doctrine rule — the live page is refreshed and re-dated in the same
closeout, not left to drift to the next engine snapshot. The same step closes the loop in
the other direction: any external-partner reply gathered since the last closeout is
transcribed into the page's **Pseudo-Chat** return lane, so the dialogue lives on the
portal rather than only in a chat transcript.

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

## Pre-Push Gate

The exclusion rule in the **Outside-AI Delivery Rule** above — *"Do not include
binaries, build directories, generated runtime data, unrelated formatting,
cleanup, or branch operations"* — is not only for hosted partners packaging a
patch. It governs **every** commit and push out of `D:\code\ccode`, by human or
AI. This section promotes it into an explicit checklist and names the mechanical
guard that enforces it, so it is a gate you run, not a paragraph you hope was
read.

**Why this exists.** The `D:\code\ccode` working tree is deliberately dirty and
mixed — many lanes are in flight at once, test runs regenerate DBF/CDX/LMDB
fixtures, and old build artifacts linger tracked. Surveying `git status` and
reaching for "everything" is the near-miss this gate prevents. A push is a
*scoped, themed slice*, never a sweep of the whole tree.

**Before staging a commit or push, confirm the change set is:**

1. **Source / docs / config / manifests only** — the substance of the named
   task. No `.exe/.dll/.lib/.pdb/.obj`, no `build*/` or `*/CMakeFiles/` trees,
   no `.sln/.vcxproj`, no `cmake_install.cmake` / `*.tlog` / `*.recipe`.
2. **Free of incidental data-fixture churn** — regenerated `dottalkpp/data/**`
   DBF/DBT/FPT/CNX/CDX/INX, LMDB, or generated HELP/metadata/manual catalogs are
   *report-only unless the current task names that mutation* (see the
   Local-Access AI Rule). A deliberate fixture promotion is fine; a test-run
   byproduct is not.
3. **Sliced by lane, not blobbed** — commit one coherent theme at a time
   (e.g. the identity lane, then the source-contract embedding), not an
   accumulation of unrelated work in one commit.
4. **Free of cleanup/formatting riders and branch operations** — vendored-tree
   deletions, line-ending renormalization, and branch moves are their own
   deliberate passes, never smuggled into a feature commit.

**The mechanical guard.** `tools/staging/prepush_gate.py` enforces this list
against the staged index (or a commit range). It hard-blocks build trees and
binaries (exit 2), warns-and-requires-acknowledgement on data/fixture churn and
oversized change sets (exit 3, cleared with `--allow-data` / `--allow-mass`), and
passes on a clean source/docs/config slice. It reads the same exclusion list
stated here, so this section and the script stay a single source of truth.

```text
python tools/staging/prepush_gate.py                 # check the staged slice
python tools/staging/prepush_gate.py --range HEAD..@{u}   # check a push range
python tools/staging/prepush_gate.py --install-hook   # enforce on every commit
```

Reading this portal — this section in particular — is a **mandatory pre-push
read**. The gate is the belt; consulting the portal first is the suspenders.
Neither replaces the maintainer's authorization.
