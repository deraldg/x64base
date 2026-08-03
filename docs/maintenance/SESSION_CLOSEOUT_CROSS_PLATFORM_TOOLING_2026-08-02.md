---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260802-001
  recorded_at_utc: 2026-08-02T19:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 99b32f5e6966b3c63d6c65f8dee94952ae37a90e
  authorization:
    requested_by: maintainer
    scope: >
      Adopt the cross-platform tooling rule at maintainer direction ("no fixes using
      powershell or bash can be used unless we have a solution that works on all
      platforms"), port the session's Windows-only workflow scripts to Python, test
      each against purpose-built fixtures, open AIF-084 worktree lane isolation, and
      record the session with its corrections.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_CROSS_PLATFORM_TOOLING_2026-08-02.md
    kind: session_closeout
---

# Session Closeout -- Cross-Platform Tooling, Lane Isolation, Registry Fragments

**Run:** AIPR-20260802-001. **Date:** 2026-08-02. **Branch:** `development`.
**Member:** `member.ai.claude.cowork` (implementer). **Owner / committer:** `member.derald`.
**Lanes:** AIF-084 (worktree lane isolation), AIF-062 follow-through, AIF-061 (unchanged, still open).
**Result:** tooling landed and tested. Several corrections recorded, including to this
session's own earlier output.

## What was asked, and how it turned

The session began with reports and project-management surfaces, and turned into a
**document/file version-control problem**: "we start one project and it clobbers the
other." That produced two structural fixes and one standing rule.

---

## 1. The measured problem

A session worked for several hours against `development` and then found that **191 commits
had landed** from parallel work. Three of four queued operations were already done by
someone else; its prepared scripts targeted a repository that no longer existed.

Nothing was lost, but only because guards failed closed. The near-misses were real: an
obsolete script was one keystroke from a redundant 546-file commit, and a broad `git add`
would have recorded the deletion of eight files.

Root cause: **every session edits the same working tree on the same branch**, and the
registries are append hotspots that guarantee a conflict even when the trees are separate.

---

## 2. What landed

### AIF-084 -- worktree lane isolation (`tools/lanes/lane.py`)

`list` / `new` / `finish` / `prune`. One `.git`, many working directories, so two sessions
physically cannot edit the same file.

- `new` refuses a lane id already present in the intake queue, registries, or `.d`
  fragments. Lane collision is not hypothetical -- AIF-047 was claimed three times.
- `new` writes a `LANE.md` so a session landing in that directory knows its lane, branch,
  base commit, rules, and finish command without being told.
- `finish` **refuses** a worktree with uncommitted work and prints what is uncommitted
  rather than discarding it; refuses to merge into a dirty integration tree; refuses to
  delete a branch holding unmerged commits.

The finish half matters as much as the new half. **Abandonment is the failure mode** -- git
worktree was already in use here and had drifted out of routine because closing was never
as cheap as opening.

**Narrows AIF-059.** Worktrees make the *working* collision structurally impossible, so the
advisory Hot Potato lock only ever needed to cover the *merge* step -- a far smaller and
more enforceable scope than the convention it had been carrying.

### Registry fragments (`tools/registries/registry_fragments.py`, + `migrate`)

`ai_runs.yaml`, `proofs.yaml`, `lessons.yaml` were **guaranteed** conflict points: every
session appends to the same few files, so two sessions collide there every time, by
construction. Worktrees make that *worse* by enabling more parallelism into one bottleneck.

Fix is the `conf.d` / systemd drop-in pattern: one file per record under a `.d` directory,
written by exactly one session and never touched again. The flat `.yaml` is regenerated, so
no consumer changes.

`current_by_lane` / `current_by_project` become **computed** from the run fragments rather
than hand-maintained -- one fewer file every session had to edit. Verified the derived index
matches the hand-maintained one exactly: 17 lanes, zero drift.

`migrate` runs check -> backup -> split -> merge -> **verify against the backup**, and
restores automatically if verification fails. Sandbox-verified: 69 records, zero lost, zero
gained, zero changed, headers intact. A fragment was then deleted deliberately to confirm
loss is **visible** (47 -> 46) rather than silent.

### `tools/git/restore_lfs.py`

Eight `tools/*.zip` are committed as **LFS pointer blobs** while `.gitattributes` declares
`*.zip binary` -- no `filter=lfs`. Nothing converts pointer to content on checkout, so they
read as deleted. `git lfs checkout` cannot help (no attribute routes them), and
`git checkout --` would write the 129-byte pointer text into the files, which is worse
because it looks fixed. Copying from `.git/lfs/objects` is exactly what a smudge filter
would do.

The durable `.gitattributes` decision is left to the maintainer, with both options stated.

### `tools/reports/stage_public.py`

The site's `public/reports/` had been populated by a plain **copy** of the internal build. A
copy cannot apply `--public`, so nothing enforced the `sensitivity:` marks in `portal.yaml`
-- it only happened to be correct that day. The site is now fed by **regeneration**.

Guards proven by deliberately relaxing `portal.yaml`, watching the tool refuse, and
restoring it.

### `tools/reports/dev_status.py`

Local close-work view: uncommitted state, closeout capture ratio, open lanes with proof-state
spread, last worklog handoffs, what awaits a build. Git reads are read-only and take no index
lock, so it is safe mid-commit; they time out and degrade visibly rather than hanging.

---

## 3. Rule adopted -- tooling is cross-platform

> **No PowerShell-only or bash-only solutions.** Python 3 + stdlib, or DotScript. ASCII
> output. `.ps1` / `.sh` only as thin wrappers, never where logic lives.

The project is cross-platform C++ on deliberately cross-compatible libraries; the tooling
now holds the same line. Adopted after this session produced **a dozen Windows-only
workflow scripts** that had to be ported. The maintainer named the rule; it should have been
inferable from the project's own values.

**Recorded exception, not a violation:** `afb-startup`, `bbsd-startup`, and their `register-`
counterparts stay PowerShell -- they register Windows Scheduled Tasks and have no
cross-platform equivalent.

**Outstanding debt:** `bbs_smoke.ps1` still needs porting. The standards seed names it the
canonical socket regression, so it blocks the PowerShell cleanup.

### Companion rule -- test the tool, do not just write it

Testing the ported tools caught **two real bugs the untested originals carried**:

1. `restore_lfs` promised `git status` would be clean afterward. It will not: restored files
   read as **modified**, because the committed blob is the pointer while the file is now real
   bytes. Corrected, with a note that committing that state *is* the drop-LFS option
   half-done.
2. `registry_fragments migrate` had a `load()` signature mismatch that would have crashed
   **during the verify step, after writing**. Only an end-to-end sandbox run surfaced it.

---

## 4. Corrections to this session's own output

Recorded rather than quietly amended, because the pattern matters more than any one error.

**Three vantage-point errors, same shape.** Reporting from a partial view as though it were
the whole one:

| Claim | Reality |
|---|---|
| "x64base has no write-ahead log" | It has one, crash-proven since 2026-07-19. The header said "stubs"; the design doc and proofs were untracked. |
| "Both worktrees are stale (`prunable`)" | Read from a Linux sandbox that cannot see `C:` at all. One is live and populated. |
| "git-lfs is not installed" | Read from the same sandbox. The real cause is the missing `filter=lfs` attribute. |

The lane doc now carries a method note: **staleness or absence observed from an agent
sandbox is not evidence about the maintainer's machine**, and acceptance criteria must be
checked where the paths are real.

**Two process errors.** A `--public` mode was rebuilt that already existed and was better
designed (registry-driven rather than hardcoded) -- a survey-first failure hours after
writing that rule. And a file was truncated from 622 lines to 58 by a deletion loop whose
terminating condition never matched; recovered via `git show HEAD:` rather than `checkout`,
because a stale `index.lock` was present.

**One over-correction, reversed.** `board.worklog` was hardcoded out of the public report
build on the reasoning that agent handoffs are internal. The maintainer overruled it: this
is an alpha open-source project and the agent-handoff surface is the interesting part.
Redaction is now opt-in and registry-driven via `redacted_boards:`, default empty.

---

## 5. Still open

Six items were open when this closeout was first written. Four closed later the same
evening; the table records both states rather than being quietly overwritten, because
what closed and what did not is the useful signal.

| Item | State |
|---|---|
| `.gitattributes` -- LFS-manage the zips or drop LFS | **CLOSED** -- dropped LFS. Restored from `.git/lfs/objects` and committed as ordinary blobs. At 1-4 KB each LFS bought nothing, and pointer-without-attribute is what produced the phantom deletions. |
| Registry migration | **CLOSED** -- run on the live tree. 71 records, zero lost/gained/changed, verified against a backup before acceptance. |
| M3 `--strict` gate promotion | **CLOSED** -- `run_gates.py` is strict by default as of 2026-08-02, promoted on a measured clean tree (census 1046/1046; registry 185 citations, zero findings). `--advisory` remains for surveying a knowingly dirty tree. |
| Evidence layer citations | **CLOSED** -- 6 unverifiable citations taken to 0: 3 cited-but-untracked artifacts added, 3 cross-repo site citations dropped (scope preserved as prose), 3 declared-but-missing lesson bodies written. |
| AIF-061 memo WAL | open -- proposal filed; needs build + fault injection **against baseline first** |
| `bbs_smoke.ps1` port | open -- blocks PowerShell cleanup |
| Site repo `.mdx` edits | open -- separate repo, uncommitted |
| Registries as DBF tables | open -- raised, not decided; see below |

**What the four closures cost, and what they revealed.** None of them was the work
originally estimated. The registry migration failed its own verify on the first live run
(`gained=2`) and was right to -- two proofs had been authored as `.d` fragments before the
migration that establishes the convention, so `merge` legitimately produced more records
than the flat file held. The fix was to fold fragment-only records into the baseline
*before* the backup, keeping verify at full strength rather than relaxing it.

The `--strict` promotion is the one worth remembering. Coverage hit 100% on 2026-07-25 and
had decayed to 99.4% by 2026-08-02 -- six files, no fault, just new work nobody re-ran the
gate against. That decay curve, measured over eight days, is the argument for the
promotion and it is the same argument `check_session_log_row.py` makes with its 33 percent.

**The open architectural question.** The registry tooling is doing database work in Python
against YAML: `registry_fragments` merges records, `dev_status` joins and reports,
`validate_registries` performs a referential-integrity check the engine can *model* via
`RELATION_EDGES` but not yet *enforce*. There is a real case that registries should be DBF
tables with DotScript tools over them -- dogfooding the engine on genuine work. The
counterweight is bootstrapping: a tool that reports on a broken build cannot require that
build. Suggested split if pursued: Python for anything that must work when the build is
broken; engine/DotScript for the registries themselves.

---

## 6. Method note for the next session

This session ran very long, and the error rate climbed with its length. **Who caught what**
matters more than the count, because it says which safeguards actually work:

| Error | Caught by |
|---|---|
| "x64base has no write-ahead log" | **Maintainer** -- corrected from memory, pointed at the table buffer |
| `board.worklog` redacted from the public build | **Maintainer** -- "board.worklog is important" |
| A dozen Windows-only workflow scripts | **Maintainer** -- named the cross-platform rule |
| "Both worktrees are stale" | **Self** -- found while investigating an unrelated bug |
| "git-lfs is not installed" | **Self**, after the maintainer questioned it -- the tool's own check disproved it |
| Rebuilding a `--public` mode that already existed | **Self** -- caught mid-edit by surveying first, too late |
| File truncated 622 -> 58 lines | **Self** -- immediately, by checking the result |
| `restore_lfs` promising a clean `git status` | **The test** -- a purpose-built repo reproducing the failure |
| `migrate` crash in the verify step | **The test** -- an end-to-end sandbox run |

Roughly a third were caught by the maintainer, a third by self-checking during the work, and
a third by tests written for the tools themselves. **The maintainer's three were the ones
self-checking could not reach** -- each required knowledge of what the project had already
built or already decided. That is the ignorance-bleed problem the portal exists to close, and
it is the argument for the standards seed and the evidence layer being load-bearing rather
than decorative.

The two the tests caught would otherwise have shipped as confident, wrong tooling. That is
the argument for the "test the tool" rule earning its place beside the others.

The cost was real regardless: a long session spends the maintainer's attention on correction
rather than on direction. Shorter sessions with a clean handoff would spend it better.

Pick-up points are in `docs/ai-friendly/OLLAMA_GPTBASE_EDUCATION_UPDATE_V1.md` and the
`board.worklog` handoff.

Owner: `member.derald`. Steward: `member.ai.claude.cowork`.
