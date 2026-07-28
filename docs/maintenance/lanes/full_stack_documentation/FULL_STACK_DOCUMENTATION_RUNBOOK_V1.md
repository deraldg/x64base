# Full-stack documentation flush -- runbook (beginning to end)

- **Owner**: member.derald
- **Recorded**: 2026-07-27 (Cowork), run family `DOCFLUSH-*`
- **Goal**: take current source truth all the way to a verified publication on
  `https://x64base.com/`, one auditable stage at a time.

This is the operator runbook. Every stage proves one thing, leaves one durable
disposition, and only then feeds the next. Nothing downstream is trusted until
its upstream is green.

## The stack in one line

```
source contracts
  -> SYS* catalogs        (metacollect / generate_syscmd, guarded)
  -> HELP DATA            (CMDHELP BUILD)
  -> HELP/META harvest    (HELP_META_HARVEST_EXPORT feeder -> CSV)
  -> MANUAL (intermediary)(manualgen: assemble/normalize/validate/publish/catalog)
  -> WEB                  (x64base.com ascent, 9 gates: static / data-driven / stamp)
```

Read the BBOX lanes as the mental model (`BBOX LANES` at the CLI): each stage is a
black box, `data -> process -> information`. BBOX only TEACHES; the runnable
executors are the commands below. MAINT is the maintenance/execution surface.

## Repositories and roles (do not confuse them)

- `D:\code\ccode` -- the **development** worktree (authoritative source). All edits,
  builds, catalog seeds, guards, and manualgen runs happen here.
- `C:\x64base` -- **publish-only staging** (reviewed files promoted at gate 5).
- `D:\dev\x64base-site` -- the maintained **website** repo (GitHub Pages source).
- The older IIS copy is NOT the publication route.

## Governance (applies to every commit in every phase)

1. Concurrent AI sessions share ONE working tree -> commit as **scoped per-path
   slices**. NEVER `git add -A` / `git add .`.
2. Claim a lane number first:
   `python tools/coordination/session_coordinator.py claim-aif --member <member> --run <RUN> --lane <lane>`
   and commit the resulting `coordination/aif/AIF-NNN.claim`.
3. Between add and commit, verify with `git diff --cached --name-only` (shows ONLY
   the staged set -- cleaner than `git status --short` in this large tree).
4. The pre-commit **prepush gate** runs automatically (install once per clone:
   `python tools/staging/prepush_gate.py --install-hook`). It hard-blocks build
   trees/binaries and duplicate AIF numbers; it runs the normalization guards
   advisory when source/catalog surfaces are touched (`--strict-norm` to block).
5. PowerShell continuation is a backtick, not `^`. Keep `git add` on one line.
6. No em-dashes in scripts/docs (use `--` / `->`). Inline comment marker is `&&`.

---

## Phase 0 -- Prep and baseline

0.1 Confirm you are in the dev worktree on the `development` branch (the prepush
    repository-role-guard also checks this).

0.2 Capture a runtime baseline / entry point for the run under
    `docs/maintenance/lanes/full_stack_documentation/runs/<RUN>/`.

---

## Phase 1 -- Source truth and build

The source is the only authority for command/function existence. If runtime and
docs disagree, runtime wins until docs are repaired.

1.1 Make source-level edits (implement functions/commands; author/repair
    `@dottalk.usage` / `@dottalk.file` / `@dottalk.subusage` contracts).

1.2 Build (MSVC Release, `pro-md`):

```
cmake --build build --target dottalkpp --config Release
```

    (Add `dottalk_bbsd` and `metacollect` targets when those are needed; stop the
    `DotTalkBBSD` scheduled task before rebuilding the daemon.)

1.3 Prove new behavior at the CLI before cataloguing it, e.g.:

```
.\datarun.ps1 -CommandLines '? PROPER("john smith")','? PADL("7",4,"0")'
```

**Gate:** build green + the command/function actually exists at runtime.

---

## Phase 2 -- Catalog normalization (SYS*)

The SYS* catalogs (`dottalkpp\data\metadata\SYS*.dbf`) are the machine-readable
spine the manual's data-driven pages derive from. Table is authority; the tracked
CSV is its shadow (EXPORT direction, never blind import).

2.1 Re-harvest functions with the source-reflection collector, then seed:

```
.\build\Release\metacollect.exe D:\code\ccode --sysfunc-import-out dottalkpp\data\scripts\metadata\SYSFUNC_IMPORT_v1.csv
.\datarun.ps1 -CommandLines 'DOTSCRIPT D:\code\ccode\dottalkpp\data\scripts\metadata\SYSFUNC_SEED_v1.dts'
```

2.2 Regenerate + seed SYSCMD from the mined contracts:

```
python tools\fullstack_docs\generate_syscmd.py --root . --write
.\datarun.ps1 -CommandLines 'DOTSCRIPT D:\code\ccode\dottalkpp\data\scripts\metadata\SYSCMD_SEED_v1.dts'
```

    Note: `generate_syscmd` mines only **git-tracked** `.cpp` (`git ls-files`).
    A registered command whose only contract lives in an UNTRACKED file shows as
    "registered but uncontracted" -- commit the file to catalogue it.

**Gate:** seed row counts match the live tables; `--report` shows 0 IDENTITY ERRORS.

---

## Phase 3 -- Normalization guards

Two read-only guards keep the four description layers (registry, SYS*, `*ref`,
command_catalog) from drifting.

```
python tools\fullstack_docs\refcheck_v1.py --root .     # *ref entries resolve to cmd/fn/sub-form
python tools\fullstack_docs\normcheck_v1.py .           # cross-authority identity/coverage lanes
```

**Gate:** `refcheck` PASS (0 dotref/foxref phantoms); `normcheck` has 0 findings in
any `fail`-severity lane (IDENTITY, FN_IDENTITY). Warn lanes (HELP/coverage) may
carry labelled items. These guards are wired into prepush (advisory).

---

## Phase 4 -- HELP lane (CMDHELP BUILD)

HELP DATA is the user-facing explanation surface and the source for the manual's
command/function reference sections. It re-mines `registry U foxref U dotref U
edref U usage-contracts`.

```
.\datarun            # interactive, then:
. cmdhelp build . d:\code\ccode\src
```

    (or a scripted `.\datarun.ps1 -CommandLines 'CMDHELP BUILD . d:\code\ccode\src'`).
    Writes HELP DATA tables under `dottalkpp\data\help`.

**Gate:** `CMDHELP` report reflects the new work (function count, corrected names);
`CMDHELPCHK` structural checks OK.

---

## Phase 5 -- HELP/META harvest export (the feeder)

The manual is assembled from a 14-file CSV harvest, NOT from the live tables. The
harvest workspace is gitignored, regenerable exhaust; the reproducible feeder is
the MAINT-lane script pair `HELP_META_HARVEST_EXPORT_v1.{dts,ps1}`.

```
pwsh -File dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1
```

This exports the 10 CURRENT tables (6 `HELP_*` from `data\help`, 4 `META_*` --
SYSCMD/SYSFUNC/SYSARGS/SYSSUBCMD -- from `data\metadata`) into
`docs\manuals\developer\manualgen\harvested\export_runs\HELPMETA-<utc>\`, carries
the 4 stale `META_*` (SYSENTVAR/SYSFLDDIC/SYSHELP/SYSMSG) forward LABELLED, and
writes a hashed manifest.

**Gate:** manifest shows all 14 files; `META_SYSCMD`/`META_SYSFUNC` counts match
the seeded catalogs. Owed: refresh the 4 stale sources before trusting them.

---

## Phase 6 -- MANUALGEN (the intermediary; Python 3.12)

`tools\manualgen\manualgen.py`, always with
`--repo-root D:\code\ccode --manual developer
--publication-workspace developer_manual_publication_v1_media_section_v1
--harvest-workspace <the export_runs\HELPMETA-... dir>`.
Every step below is read-only / candidate-only until an explicit authorized apply.

6.1 `inventory`   -- confirm the harvest resolves (14 files, right counts).
6.2 `validate`    -- 0 FAIL / 0 REVIEW / 0 boundary FAIL.
6.3 `build-dry-run` -- assemble without writing sections.
6.4 `build-reference-candidate` -- render the command/function reference candidate.
6.5 `parity-review` -- candidate vs published delta (the gate-1/gate-2 preflight).
6.6 curation chain: `build-curation-candidate` -> `build-disposition-candidate`
    -> `build-structural-reconciliation` -> `build-section-delta-candidates`
    -> `build-prose-review-batch` -> `build-selective-merge-candidate`.
6.7 `build-controlled-acceptance-plan --candidate-run <MANRUN> --pointer-audit <...>
    --context-decision <...>` then, only after a written authorization record,
    `apply-controlled-acceptance --plan-run <MANRUN> --authorization-record <...>`.
    This is the ONLY manualgen step that mutates accepted sections + MAN* catalog.
6.8 Inspect results read-only: `MANUAL CATALOG STATUS` / `do manuals` (8 MAN* tables).

**Gate:** accepted manual + MAN* catalog regenerated from current evidence; manual
publication-readiness proof (links/TOC/headers/provenance/accessibility) 0 FAIL.

---

## Phase 7 -- Web ascent to x64base.com (9 gates)

Authoritative plan: `DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md`. Only the
DATA-DRIVEN pages (command/function reference) and changed STAMP pages (version)
move; STATIC pages carry through untouched, so the packet stays small.

1. Selective-merge contextual review (report only).
2. Canonical acceptance preflight (candidate + exact mutation plan only).
3. Controlled manual acceptance + rebuild (authorized apply; == Phase 6.7).
4. Manual publication-readiness proof (report-only).
5. Clean `C:\x64base` source-staging promotion (reviewed files only; separate
   source/docs commit). Tools under `tools\staging\`.
6. Website feed/export packet: `python tools\fullstack_docs\build_website_feed_packet.py`
   then `validate_website_feed_packet.py` (route dispositions, public-blob
   provenance, zero website mutation).
7. Website integration + local build in `D:\dev\x64base-site` (generated static
   pages). `stage_assembled_manual_to_site.py` / `validate_website_integration_plan.py`.
8. Website publication: commit/push the site repo -> GitHub Pages deploy.
9. Live verification: cache-bypassed HTTP checks of the deployed routes/content;
   record what is actually served; close out the run.

**Gate (each):** one durable disposition before the next gate begins. A green build
is NOT live-site proof -- gate 9 reads the deployed routes.

---

## Closeout

- Write a session/run closeout under `docs/maintenance/` (per-lane, with proof
  counts and owed items), and update the flush triage board.
- Commit scoped slices (source; catalogs/scripts; docs) with `AIF-NNN:` messages.
- Record what remains owed (e.g. stale META feeders, DDICT PDLC turnover, browser
  rename commit) so the next flush starts from a known state.

## Quick command index

| stage | command |
|---|---|
| build | `cmake --build build --target dottalkpp --config Release` |
| SYSFUNC | `metacollect.exe . --sysfunc-import-out ...` + `DOTSCRIPT SYSFUNC_SEED_v1.dts` |
| SYSCMD | `generate_syscmd.py --root . --write` + `DOTSCRIPT SYSCMD_SEED_v1.dts` |
| guards | `refcheck_v1.py --root .` ; `normcheck_v1.py .` |
| HELP | `CMDHELP BUILD . d:\code\ccode\src` |
| harvest | `pwsh -File dottalkpp\data\scripts\metadata\HELP_META_HARVEST_EXPORT_v1.ps1` |
| manual | `manualgen.py ... inventory` -> `validate` -> `build-dry-run` -> `build-reference-candidate` -> `parity-review` -> acceptance |
| web feed | `build_website_feed_packet.py` + `validate_website_feed_packet.py` |
| AIF claim | `session_coordinator.py claim-aif --member <m> --run <RUN> --lane <lane>` |
| commit check | `git diff --cached --name-only` |
