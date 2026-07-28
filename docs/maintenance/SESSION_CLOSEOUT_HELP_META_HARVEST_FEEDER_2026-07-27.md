---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260727-BF1
  recorded_at_utc: 2026-07-27T23:51:26Z
  agent:
    provider: not_exposed
    product: not_exposed
    model: not_exposed
    access_mode: human_operated_tool
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 6d9009df9
  authorization:
    requested_by: maintainer
    scope: >
      Envelope reconstructed 2026-07-28 during AI-portal audit backfill
      (AIPR-20260728-002). AI-authored, human-committed (introducing commit
      6d9009df9, 2026-07-27); original session/agent identity was not recorded and is
      marked not_exposed; access_mode human_operated_tool per
      AI_REPORT_AUDIT_CONTRACT_V1.md.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_HELP_META_HARVEST_FEEDER_2026-07-27.md
    kind: session_closeout
---

# Session Closeout -- HELP/META harvest feeder rebuilt (all affected lanes)

- **Run**: DOCFLUSH-20260722-001
- **Recorded**: 2026-07-27 (Cowork), `member.ai.claude.cowork`
- **Boundary**: read-only w.r.t. tables/indexes/LMDB/source; wrote only `data\tmp`
  and a gitignored harvest run dir. The only tracked new artifacts are the two
  feeder scripts. No manual, HELP DATA, publication, or website mutation.

## What was found

The manualgen system consumes a 14-file HELP/META CSV harvest, but:

- The harvest workspace (`docs/manuals/developer/manualgen/harvested/`) and the
  whole `generated/` tree are **gitignored, regenerable exhaust** -- 0 tracked
  files. A fresh clone has no harvest.
- The producer was mostly **never committed**: of the 14 per-table exports, only
  `SYSCMD_EXPORT_MIRROR_v1.dts` existed (1/14). The export manifest was a
  `PENDING_EXPORT` scaffold with a blank `export_method`.
- The on-disk harvest was **May 24--25** -- it predated this entire flush, so
  running manualgen against it would have missed SYSCMD 212, SYSFUNC 74, the five
  new functions, and the `BROWSE->BROWSER` rename.

This was the "part of the system we dropped": the runtime -> CSV export feeder.
The capability (C++ runtime `EXPORT ... CSV`, driven by `.dts`) was always
present; the reproducible scripts were not.

## What was built

`dottalkpp/data/scripts/metadata/HELP_META_HARVEST_EXPORT_v1.dts` + `.ps1` -- the
reproducible feeder, modelled on `SYSCMD_EXPORT_MIRROR_v1.dts`. Table is
authority; CSV is its shadow. It exports the 10 currently-maintained tables and
promotes/hashes them into a stamped, self-describing run, carrying the 4 stale
`META_*` forward labelled. Lane: **MAINT** scaffolding (BBOX is a lesson lane and
only teaches; a native MAINT harvest verb should eventually replace the script).

## What was produced (proof)

Run `HELPMETA-20260727T233835Z`, all counts matching the normalized catalogs:

| file | rows | state |
|---|---|---|
| HELP_COMMANDS | 463 | EXPORTED (current) |
| HELP_CMD_ARGS | 2,371 | EXPORTED |
| HELP_HELP_ARTIFACTS | 14,099 | EXPORTED |
| HELP_HELP_LINE | 28,196 | EXPORTED |
| HELP_HELP_SECTION | 14,099 | EXPORTED |
| HELP_HELP_TOPIC | 710 | EXPORTED |
| META_SYSCMD | **212** | EXPORTED (v64) |
| META_SYSFUNC | **74** | EXPORTED (v64) |
| META_SYSARGS | 249 | EXPORTED |
| META_SYSSUBCMD | 31 | EXPORTED |
| META_SYSENTVAR / SYSFLDDIC / SYSHELP / SYSMSG | (May) | CARRIED_STALE_MAY |

Manifest with row counts + SHA-256 written to the run dir, replacing the
`PENDING_EXPORT` scaffold with real evidence.

## Affected lanes (documentation update)

- **MANUALGEN lane** -- its harvest INPUT is now regenerable and current. The
  read-first sequence (`inventory -> validate -> build-dry-run ->
  build-reference-candidate -> parity-review`) can now run against a run dir that
  carries this flush's work. Point `--harvest-workspace` at
  `harvested/export_runs/HELPMETA-20260727T233835Z`.
- **HELP lane** -- the 6 `HELP_*` exports are now a reproducible artifact of
  `CMDHELP BUILD`'s output (`data\help`), not a hand-made snapshot.
- **METADATA lane** -- 4 `META_*` (SYSCMD/SYSFUNC/SYSARGS/SYSSUBCMD) export
  clean and current. The other 4 (`SYSENTVAR/SYSFLDDIC/SYSHELP/SYSMSG`) are stale
  May seeds/stubs, **owed**, and outside the normalization guards.
- **MESSAGING lane** -- clarified: the live message catalog is
  `SYSTEM_MESSAGES` (1,006) / `SYSTEM_MESSAGE_TEXT` (1,270); `META_SYSMSG` is a
  ~1 KB stale metadata stub, not the real data. Do not treat `META_SYSMSG` as the
  messaging authority.
- **DATADICT lane** -- the 11 `DD*` tables are entirely `PLANNED_DDL_DEFINITION`
  (skeleton), not populated evidence; not part of the harvest.
- **BBOX** -- abandoned for this work: it is a **lesson lane** (read-only
  teacher), not an executor. The executor is the MAINT-lane feeder above.
- **SelfDoc lane** -- this closeout is the provenance record; the feeder is the
  tool the SelfDoc/pipeline inventory should list.

## Owed (carried forward)

- Refresh the four stale `META_*` sources, then extend the feeder to export them
  (or drop them from the required set if the manual does not need them).
- A native **MAINT** harvest verb to replace the `.ps1`/`.dts` scaffolding
  (per MAINT's "PowerShell is MDO scaffolding only" note).

## Canonical doc touched

`docs/HELP_METADATA_SELFDOC_WORKFLOW_v1.md` -- Manual promotion lane gained a
"Harvest export (feeder)" subsection recording the above.
