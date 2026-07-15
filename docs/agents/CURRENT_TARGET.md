# Current Target

Status: active.
Updated: 2026-07-15.
Supersedes: the completed staging-restoration/publication target recorded below.

## Current Objective — Reconcile Public Corrections Into Development

Public AI Portal consistency work was completed through:

- `100169433b583e5f51eafdeea130607d71942376` — public-state reconciliation;
- `a0cf52654c4f8e834e969e3c2524fd397d627a95` — canonical AI startup path.

Those changes were made against the public GitHub snapshot. They are not yet
integrated project work under the authority contract because this session could
not inspect or modify the authoritative development tree:

```text
D:\code\ccode
```

The next local-access session must:

1. inspect the current development versions of the affected Markdown files;
2. reconcile the public corrections selectively without overwriting newer local
   facts;
3. record the actual development branch and working-tree state;
4. verify the reconciled documents against development source and runtime proof;
5. promote through `C:\x64base` only if a reviewed development-to-public delta
   remains.

Primary handoff:

```text
docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_PUBLIC_CONSISTENCY_2026-07-15.md
```

Do not reverse the authority chain by treating the GitHub versions as newer
truth merely because they were published later.

## Previous Objective Resolution — 2026-07-15

The staging-restoration and first-publication objective recorded below is
complete. The public state at completion was
`b9d480215c036178ba99b5109a8a2489ee89b215`; later documentation-only
reconciliation advanced `main` through the commits listed above.

The cold-clone fixes were published in:

- `46e021594bee25fd40fe9b79e318c691e1a714a0` — self-contained clone journey,
  location-honest launch/databuild scripts, and proof records;
- `b9d480215c036178ba99b5109a8a2489ee89b215` — valid DotScript `&&` comment
  syntax in the printed `DO X64` example.

The remaining sections are preserved as the state and reasoning that existed
when this previous target was active on 2026-07-14.

## Authority Restatement

```text
D:\code\ccode              authoritative development source and runtime truth
C:\x64base                 clean staging repository -> github.com/deraldg/x64base
github.com/deraldg/x64base public snapshot
```

`C:\x64base` is the **clean staging repository**, maintainer-declared
2026-07-14. It is not a backup. Earlier text in this file called it a backup;
that was wrong and has been removed. The authoritative statement lives in
`AI_PORTAL.md` under "What `C:\x64base` Is — and Is Not".

## Task

Restore `C:\x64base` to a clean staging state, so that what is published to
`github.com/deraldg/x64base` is exactly the reviewed, relevant subset of
`D:\code\ccode`.

## Staging State — RESOLVED 2026-07-14

`C:\x64base` is now clean and on `main`.

| Check | State |
| --- | --- |
| Remote | `https://github.com/deraldg/x64base.git` |
| Checked-out branch | **`main`**, tracking `origin/main` |
| HEAD | `a625ea1d` — *Merge pull request #6 from deraldg/codex/labtalk-dottalk-sdlc-planning* |
| Position vs `origin/main` | even |

### What the earlier confusion was

The staging repo had been sitting on `codex/labtalk-dottalk-sdlc-planning` with
a two-day-old remote cache. That branch's 11 commits **had already been merged**
as PR #6, and GitHub had auto-deleted the branch on merge. Local `origin/*` refs
still showed it, because nobody had fetched.

Lesson, recorded so it is not relearned: **`origin/*` refs are a cache, not the
remote.** Working-copy and remote-tracking state do not prove GitHub state. Check
`.git/FETCH_HEAD` age, or run `git ls-remote`, before reasoning about what is
published.

### Safety nets left in place

- `git stash` `stash@{0}` — the 101 tracked modifications that were in the
  staging working tree before the reset. All 13 modified C++/header files were
  verified byte-identical to `D:\code\ccode`, so nothing original was lost.
- `$HOME\x64base_uncommitted_2026-07-14.patch` — same content as a patch file.
- `rescue-codex-sdlc` — local branch pinned to the pre-merge branch tip.

All three are redundant now that the merge story is understood. Drop them when
you are satisfied.

There is also an **older, pre-existing `stash@{1}`** — *"local staged gui and
source work before github sync"*, from `upgrade/selfdoc-usage-contract`. It
predates this work and was not touched. Review before discarding.

## Expected Fix

1. Stop the litter at the source: `.gitignore` in `D:\code\ccode` now excludes
   `*.bak_*` and `*.before_mdo_*` sidecar patterns, so they are never promoted.
2. Confirm the promotion filter honours those patterns before the next sync.
3. Verify publication completeness with `git ls-files`, not a green build.
   `src/CMakeLists.txt` uses `file(GLOB_RECURSE ...)`, so an untracked `.cpp`
   in staging compiles locally while remaining absent from GitHub.

## Next — the first clean PR

Staging is on `main` and clean. The work below lands as one reviewable PR
against a current baseline.

**Done in `D:\code\ccode`, uncommitted:**

1. `.gitignore` — sidecar patterns (`*.bak_*`, `*.before_mdo_*`, `*.save`) and
   the LMDB exclusion (`/dottalkpp/data/lmdb/`, `**/*.cdx.d/`). 53 GB measured.
2. Sidecar purge — 148 files, 15.1 MB removed. Manifest in
   `docs/maintenance/SIDECAR_PURGE_20260714-094942.txt`.
3. AI portal authority corrections + the AIF-006 closeout gate.
4. Index-expression contract drift repaired across 13 files. See
   `docs/contracts/reports/CONTRACT_DRIFT_INDEX_EXPRESSION_2026-07-14.md`.
5. MCC fixture rebuild lane — `dottalkpp/data/scripts/mcc/`.

**Not yet run:**

6. `dottalkpp/scripts/mcc/extract_mcc_og.ps1` — unpack the canonical archive.
7. The three flavor scripts under `DOTSCRIPT TRACE`. They are
   `CANDIDATE / REVIEW_BEFORE_EXECUTION` and have never been executed. A zero
   exit code is not proof; review the transcripts.
8. `tools/staging/promote_data_fixtures.ps1` — dev -> staging, LMDB blocked by
   a hard deny-list gate that throws rather than let a `*.cdx.d` through.
9. Branch, commit, push, PR.

## Deliberately Out Of Scope

- **Development-tree hygiene beyond sidecars.** Root-level scratch `.txt` files,
  `src/gui.zip`, `src/$envVCPKG_ROOT = ...txt`. A separate lane. Do not let it
  creep into the fixture PR.
- **`stash@{1}` in `C:\x64base`** — pre-existing parked work from
  `upgrade/selfdoc-usage-contract`. Not this task's business.

## Do Not Touch

- Do not clean, reset, or broadly stage the `D:\code\ccode` working tree.
  A dirty development tree is normal and is not a release risk signal.
- Do not make original changes in `C:\x64base`. Promote from `D:\code\ccode`.
- Do not mutate DBF data, HELP tables, metadata catalogs, generated catalogs,
  publication outputs, runtime fixtures, backups, or archives unless the
  current task explicitly authorizes it.
- Do not create, switch, or rename branches without explicit instruction.

## Proof Needed

- `git status --short` in each root before and after any promotion pass.
- A `git ls-files` check that every source required by the CMake glob is
  tracked.
- A relocation checklist before any file moves.

## History

The previous target (2026-06-29) described two clean x64base repo copies, named
`D:\code\ccode\x64base` as the recent staged GitHub version, and treated
`C:\x64base` as its backup.

That target is closed as stale on two counts, both verified 2026-07-14:

- `D:\code\ccode\x64base` **does not exist** on disk.
- `C:\x64base` is the staging repository, not a backup, and is checked out on
  `codex/labtalk-dottalk-sdlc-planning` — not the
  `upgrade/selfdoc-usage-contract` branch that target recorded.

An onboarding document drifting this far out of date is the failure mode the
closeout-updates-startup gate is meant to prevent. That gate is queued as
`AIF-006` in `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md`.
