# Session Closeout — MCC Databuild, Repo Hygiene, AI Portal Corrections

Date: 2026-07-14.
Owning lifecycle: DotTalk++ SDLC (maintenance + publication lanes).
SDLC lane: publication (merged to GitHub main).
Truth state: runtime-proven where marked; documentation elsewhere.
Proof state: DotScript transcripts captured; git state verified.

This is the durable record of a single working session. It exists so the next
session — AI or human — can resume without reading a lost chat. Per the
project's own rule: the repo is the memory.

## One-line summary

Turned the MCC sample data into a reproducible databuild lane, repaired a
13-file documentation contract drift, corrected the AI portal's description of
`C:\x64base`, and published a clean dev-stage first PR to
`github.com/deraldg/x64base`.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Databuild lane | `dottalkpp/scripts/mcc/*.ps1`, `dottalkpp/data/scripts/mcc/*.dts`, README | New. og -> x32 -> vfp -> x64, one guarded entry point. |
| Repo hygiene | `.gitignore` | Excludes LMDB (53 GB), `*.cdx.d`, `data/dbf/og`, sidecars, `*.exe`, probe/scratch. |
| Sidecar purge | `tools/hygiene/purge_dev_sidecars.ps1` | Removed 148 files (15.1 MB). Manifest: `SIDECAR_PURGE_20260714-094942.txt`. |
| Contract drift | 13 schema/README files + `CONTRACT_REGISTRY_V1.md` + drift report | Index-expression syntax. See report below. |
| AI portal | `AI_PORTAL.md`, `AI_README.md`, `AI_ASSIMILATION_BOOK_V1.md`, `CURRENT_TARGET.md`, intake queue | C:\x64base authority, Local-Access rule, AIF-006 gate. |
| Promotion tooling | `tools/staging/promote_pr_20260714.ps1` | Explicit manifest + 53 GB deny-list guard. |

## Verified (runtime-proven this session)

DotScript transcripts, 2026-07-14:

- **Databuild builds clean from virgin state.** Every `CNX CREATE` / `CDX
  CREATE` reported `created:` (a real build, not a REINDEX of stale
  containers). Every `CDX ADDTAG` reported `added`. All 23 tags per table.
- **Freshness proven by data, not shape.** STUDENTS = 200 records, record 1 =
  `50000000 Taylor Quinn` on all three lanes. (The stale hand-edited table had
  201 records and FNAME "Derald" — that discrepancy is what caught a silent
  path bug.)
- **Index lane split confirmed.** x32/vfp opened `(v32)` and attached CNX; x64
  opened `(v64)` and attached CDX. `BUILDLMDB` materialized all 12 envs.
- **CDX order == LMDB order** for the same tag (SID). `SETLMDB 0` cleared to
  physical.
- **Contract: INDEX ON takes a field, not an expression.** Confirmed against
  `cmd_index.cpp`, the Command Reference, and 40+ corpus `INDEX ON` statements.

## AI-facing docs updated (AIF-006 gate)

- `docs/agents/CURRENT_TARGET.md` — rewritten; the stale "backup" description
  of `C:\x64base` corrected to "staging repository", branch story recorded.
- `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` — AIF-006 (closeout
  gate) anchored/merged; AIF-007 (a withdrawn proposal) rejected with reasons.
- `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` — lane state updated (this
  session).

## Published

GitHub `main` advanced across this session:

```text
a625ea1d  (start: PR #6 already merged; branch auto-deleted)
  49279cdf  Reproducible MCC sample data, repo hygiene, AI portal corrections
  f834fd3d  Remove probe/scratch artifacts from the databuild set
  c8826725  Remove stray scratch table.cdx from metadata lane   (current tip)
```

`main` is now a dev-stage repo where one clone gives a user the full
`dottalkpp` scaffold (bin, ini, directory layout), the MCC + OG + help sample
data, and the databuild scripts. **No compiled binary. No scratch. No LMDB.**
User path: build the exe (onboarding steps 3-4), run
`dottalkpp/scripts/mcc/build_mcc_demo_bases.ps1` (step 5), query real data.

## Still open — for the next session

### Runtime bugs found, documented, NOT fixed
These touch source and go through `SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`.
Now queued as review rows in `docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md`
("Runtime Findings" table, AIF-011) — no longer only in the MCC README. Each
awaits a maintainer decision.

1. `SETLMDB PHYSICAL` is not a valid form — fails as a missing container
   `PHYSICAL.cdx.d`. Correct form is `SETLMDB 0`. Also present and failing
   silently in `mcc_exhaustive_full_regression_canaries_lmdb.dts`.
2. `BUILDLMDB` and `SETLMDB` report different env directories for the same
   container (`LMDB\x64\...` vs `INDEXES\x64\...`). `SET INDEX` agrees with
   `BUILDLMDB`; `SETLMDB` is the outlier.
3. `SHOW TABLE` misreports the table path (drops the `dbf\<lane>` segment) and,
   on the VFP readback, reported an `indexes\x32` container while the VFP one
   was attached. Behavior correct; display wrong.
4. Bare `ASC` takes an argument (`ASC expects 1 argument(s)`); it does not undo
   `DESC`. Use `SET ORDER TO TAG <tag>`.

### Deferred data lanes (each its own future PR + environment)
`messaging`, `selfdoc`, `metadata`, `datadict`, `sandbox`, `cobol`, `memo`.
Currently untracked in `C:\x64base`. The maintainer noted messaging, selfdoc,
metadata and other schemas will need their own environments later.

### Housekeeping
`git prune` in `C:\x64base` to clear loose-object debris from this session's
amend/reset churn (git's own gc nag).

## AI Portal improvements made this session (AIF-008..011)

The maintainer asked for the portal to be kept current and improved; it is
"on purpose open to rapid change." Four changes, all promoted:

- **AIF-008 — session-closeout convention.** This file is the first instance.
  Rule in `AI_PORTAL.md` -> "Leave a Session Closeout"; template at
  `docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md`; indexed in the dashboard
  Session Log.
- **AIF-009 — local-access agent checklist.** `labtalk/ai_portal/
  LOCAL_ACCESS_AGENT_CHECKLIST_V1.md`. The portal assumed hosted propose-only
  AI; this covers the write-capable failure mode.
- **AIF-010 — one canonical entry order.** `AI_README.md` now has a single
  ordered table (newest closeout first); the ~5 overlapping onboarding docs are
  marked depth-on-demand.
- **AIF-011 — runtime findings queued** into `CONTRACT_INTAKE_QUEUE_V1.md`.

## Provenance pointers

- Databuild lane doc: `dottalkpp/data/scripts/mcc/README.md`
- Contract drift report: `docs/contracts/reports/CONTRACT_DRIFT_INDEX_EXPRESSION_2026-07-14.md`
- Contract registry rows: `docs/contracts/CONTRACT_REGISTRY_V1.md` (Index Key
  Is A Field; Index Lane Split)
- Runtime findings: `docs/contracts/CONTRACT_INTAKE_QUEUE_V1.md` (Runtime Findings)
- AIF-006 gate text: `AI_PORTAL.md` -> "Closeout Updates Startup"
- Session-closeout template: `docs/maintenance/SESSION_CLOSEOUT_TEMPLATE.md`
- Local-access checklist: `labtalk/ai_portal/LOCAL_ACCESS_AGENT_CHECKLIST_V1.md`
- Sidecar purge manifest: `docs/maintenance/SIDECAR_PURGE_20260714-094942.txt`
