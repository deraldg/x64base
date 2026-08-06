# Full-stack documentation flush -- recipe book v1

Lane: `full_stack_documentation`
Owner: `member.derald`
Recorded: 2026-08-05 (distilled from run `DOCFLUSH-20260805-001`)
Companion to: `FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md` (doctrine + gates).
Nature: **living and recurring.** The full-stack flush is a standing part of the
thesis (self-documenting, AI-maintained systems); it never "finishes." This book is
refined every run, and each run is expected to leave it more accurate -- new recipes,
retired footguns, corrected commands. Treat it as version-forward, not frozen.

This is the **operational how-to**: exact commands per phase and the footguns that
bite. The plan says *what* each gate requires and *why*; this says *how* to run it.
When they disagree, the plan wins -- fix this book. When a run teaches something new,
add it here so the next run does not re-derive it (that is the whole point).

## 0. Environment and roles

- Development tree: `D:\code\ccode` on branch `development` (the only tree that
  refreshes HELP and commits the flush).
- Runtime data root: `dottalkpp\data`. HELP store: `dottalkpp\data\help`.
- Website tree (separate repo): `D:\dev\x64base-site`.
- Interpreters: Python 3.12 is the repository standard
  (`C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe`, recorded in
  `.python-version`). Some tools hard-check it.
- A mounted Linux sandbox agent can read/write files and run Python 3.10, but it
  CANNOT build the engine and MUST run no git. It prepares host commands.

## 1. Standing rules (read once, obey always)

1. **Sandbox runs no git.** A killed git leaves `.git/index.lock` and wedges the
   maintainer's commits. Prepare commands; the maintainer runs them.
2. **`datarun.ps1` pushes cwd to the data root.** Use ABSOLUTE paths for every
   input/output. It has NO `-Script` parameter; the exe `--script` does not survive
   its pass-through. Replay an existing `.dts` with
   `./datarun.ps1 -CommandLines (Get-Content "<ABS>.dts")`.
3. **House-style: ASCII only on added lines.** Use `--` and `->`, never an em-dash.
   Do not quote mojibake verbatim into a doc -- describe it.
4. **Do not save what you can recreate.** Run-directory `*.csv` are gitignored
   (`docs/maintenance/lanes/**/runs/**/*.csv`); the gate record binds them by
   SHA-256 and they reproduce from the tool.
5. **`SESSION_CLOSEOUT_*.md` needs an `ai_report_audit` YAML envelope** or the
   report-audit gate hard-blocks the commit. Gate records named `GATE*_...` do not.
6. **Scoped commits only.** Never `git add -A` on this shared worktree; add exact
   paths and check `git status --short` between add and commit.
7. **Python 3.12 tools** (`command_catalog_sync.py`, `manualgen.py`) run with
   `py -3.12` on the host. In the 3.10 sandbox: `command_catalog_sync` runs if you
   set `m.MIN_PYTHON=(3,10)` after import; `manualgen` runs directly (only its
   `PYTHON_312` self-check fails, harmlessly).
8. **A dotref.hpp change means a LEGACY build.** foxref feeds the LEGACY store, so
   run `CMDHELP BUILD LEGACY` then `CMDHELP BUILD . <ABS src>`. Back up the HELP
   store first and stop the daemon (it locks the store).
9. **Discovery before creation.** Before opening any lane or number, search
   `docs/maintenance/` and `coordination/aif/`. (Defect D12: a duplicate crosswalk
   and lane were created because the scan looked only in the AI-portal folders.)
10. **Public promotion is its own lane.** The dev-tree run closes at Gate 7; source
    promotion (`ccode -> C:\x64base -> github`) and website publish are handed off.
11. **Website: source, don't hand-edit output; normalize the fact.** Consult
    `x64base-site` `content/docs/dev/website-documentation-matrix.mdx` (page classes)
    and `config/nav.ts` BEFORE editing any page. Never hand-edit a `generated` /
    `derived` / `maintained_current` region (e.g. `current-work.mdx`,
    `current-work-v1.json`, command catalog) -- fix the registry/source and run its
    generator. Hand-edit only `static`/`maintained` pages (home framing, news,
    brand, licensing). As a website-feed step every flush: advance the registry
    `as_of_date`, reconcile the flush block, then run `build_current_work_feed.py`,
    `command_catalog_sync`, and `build_gptbase_bundle.py` (the three consumers:
    current-work, website catalog, GPTbase advisor bundle -- all derive the same
    `as_of_date` from the registry). A stored fact that can be measured (date, HELP
    counts) is a normalization bug -- derive it. **Closeout: once the website is
    approved, update and re-audit `content/docs/dev/website-documentation-matrix.mdx`
    (advance `Last audited`, reclassify changed pages, record new diagrams/feeds) --
    the run does not close on a stale matrix (fail-closed website signoff gate).**
    (See the Phase 8 first-attempt lessons in the ascent plan.)

## 2. Phase recipes

Paths below are absolute for copy-paste; `$RUN` = the run directory
`docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-YYYYMMDD-NNN`.

### Phase 0 -- run envelope (Gate 0)

Create `$RUN`. Record run id, owner, branch, and scope. No mutation.

### Phase 0.5 -- contract coverage (owner's step 1)

Every source file: `@dottalk.file`. Command files: add `@dottalk.usage`. External
apps/commands: `@dottalk.external`. Then prove coverage:

```powershell
py -3.12 .\tools\fullstack_docs\docpush_preflight.py            # source_census + catalog check + ASCII scan
py -3.12 .\tools\fullstack_docs\command_catalog_sync.py check `
    --source-root D:\code\ccode `
    --catalog D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx
```

Target: `source_census` 100 percent; catalog `fallback 0`. A block-form contract the
extractor cannot read (the classic `DDICT` case) must be normalized to
`// @dottalk.usage`.

### Phase 1 -- inventory and classify drift (Gate 1)

Use the lane's own tools; do not hand-roll a crosswalk.

```powershell
py -3.12 .\tools\fullstack_docs\build_reference_identity_inventory.py    # ref/registry/usage/HELP/metadata identities
py -3.12 .\tools\fullstack_docs\build_reference_authority_crosswalk.py   # cross-walk; stops at review rows (no silent replace)
py -3.12 .\tools\fullstack_docs\reference_disposition_recommend.py       # report-only disposition per review row
py -3.12 .\tools\fullstack_docs\refcheck_v1.py                           # dotref/foxref phantom guard
py -3.12 .\tools\fullstack_docs\normcheck_v1.py                          # cross-authority identity gate
```

Record dispositions in a `PHASE1_GATE1_REFERENCE_DISPOSITION_RECORD`. Deliberate
structure (aliases, subforms, FoxPro functions) is accepted; genuine defects
(duplicate registrations) are named with evidence and deferred to a follow-up lane.

### Phase 2 -- pre-refresh runtime baseline (Gate 2)

Author `$RUN\runtime_baseline\fullstack_pre_refresh_runtime_v1.dts` (ABOUT,
CMDHELP*, CMDHELPCHK*, DOTHELP/FOXHELP/HELP, MANUAL STATUS/COUNTS, plus targeted
`CMDHELP <topic>` for changed commands, QUIT). Capture:

```powershell
$run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-YYYYMMDD-NNN\runtime_baseline'
./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_pre_refresh_runtime_v1.dts") `
  | Tee-Object "$run\fullstack_pre_refresh_runtime_v1.txt"
Set-Location D:\code\ccode
```

Gate 2 review binds SHAs (script, transcript, exe) and confirms reflection PASS,
manual 8/8, line/topic counts. Read the transcript for mojibake (source em-dashes
render as a CP437 garble) and record it.

### Phase 3 -- reviewed HELP refresh package (Gate 3)

State why the build is required, which inputs changed, expected file changes,
backup manifest (hash the `help\` DBFs), rollback, and post-build checks. A
`dotref.hpp` change requires the LEGACY build (foxref feeds LEGACY). Helper:
`tools\fullstack_docs\prepare_help_refresh_package.py`. Owner authorizes.

### Phase 4 -- execute HELP refresh + validate (Gate 4)

```powershell
Stop-ScheduledTask -TaskName 'DotTalkBBSD'                      # it locks the store
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -Recurse D:\code\ccode\dottalkpp\data\help "D:\code\ccode\dottalkpp\data\help.bak-$stamp"
./datarun.ps1 -CommandLines 'CMDHELP BUILD LEGACY','CMDHELP BUILD . D:\code\ccode\src'
$run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-YYYYMMDD-NNN\help_refresh'
./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_post_refresh_runtime_v1.dts") `
  | Tee-Object "$run\fullstack_post_refresh_runtime_v1.txt"
Set-Location D:\code\ccode
Start-ScheduledTask -TaskName 'DotTalkBBSD'
```

Gate 4: reflection PASS; line/topic counts >= baseline; targeted topics resolve;
LEGACY delta visible (foxref changes); primary store often idempotent. Diff with
`tools\fullstack_docs\compare_runtime_baselines.py`.

### Website catalog derivative (downstream of Phase 4)

```powershell
py -3.12 .\tools\fullstack_docs\command_catalog_sync.py emit `
    --source-root D:\code\ccode `
    --out D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx
```

Commit on the SITE repo as its own scoped slice. Source cells render with
backslashes by design; with `fallback 0` the page is uniformly so.

### Phase 5 -- metadata candidates (Gate 5)

`metacollect` is a standalone external tool -- see
`METACOLLECT_RUNBOOK_V1.md` for build (`-DDOTTALK_BUILD_METACOLLECT=ON`) and the
`--syscmd/sysfunc/sysargs-import-out` run. Candidate-only; import into live
metadata is a separate gate. Gate 5 record binds the candidate CSVs by SHA; the
CSVs stay gitignored.

### Phase 6 -- manual candidate (Gate 6)

manualgen (Python 3.12; runs on sandbox 3.10 with only the version self-check
failing). See `tools\manualgen\README.md`.

```powershell
$py12 = 'C:\Users\deral\vcpkg\installed\x64-windows\tools\python3\python.exe'
$base = '--repo-root','D:\code\ccode','--manual','developer',
        '--publication-workspace','developer_manual_publication_v1_media_section_v1',
        '--harvest-workspace','docs\manuals\developer\manualgen\harvested'
& $py12 .\tools\manualgen\manualgen.py @base inventory
& $py12 .\tools\manualgen\manualgen.py @base validate
& $py12 .\tools\manualgen\manualgen.py @base export-manifest
& $py12 .\tools\manualgen\manualgen.py @base build-dry-run
```

Candidate-only: `boundary_fail_rows=0`, no publication replacement. If the harvest
predates the Phase-4 rebuild, re-export it (feeds `build-reference-candidate`) so
the manual includes new commands.

### Phase 7 -- review and close the dev-tree run (Gate 7)

Review five states for pointer agreement: candidate workspace, accepted/canonical
manifest, active reader artifact, publication manifest, website projection. Write a
closeout that separates dev-refresh / candidate / promotion / staging / commit /
push. Gate 7: the development-tree run closes; public promotion and website publish
go to their own lane. Do NOT claim a public push from here.

### Phase 7 -> 8 entry check (run before any publication)

Closing the dev-tree run is necessary but not sufficient to publish. Prove all 8
fail-closed conditions before Phase 8 starts (details:
`FULL_STACK_DOCUMENTATION_PHASE8_PUBLICATION_ASCENT_PLAN_V1.md`):

- E1 dev-tree run closed at Gate 7 (closeout says CLOSED)
- E2 HELP current + `CMDHELPCHK` reflection PASS
- E3 contracts 100 percent; catalog `fallback 0`
- E4 `refcheck_v1.py` + `normcheck_v1.py` PASS
- E5 HELP/META harvest re-exported AFTER the Phase-4 build (else the manual omits
  new commands) -- the one runs usually fail first
- E6 `command-catalog.mdx` regenerated, fallback 0
- E7 HELP store backup exists; rollback path named
- E8 owner authorization for each distinct mutation (manual accept, source stage,
  website publish)

If any row is unproven, Phase 8 does not start; reopen the relevant dev-tree phase.

### Phase 8 -- publication ascent (consumers; separate lanes)

The manual and website are CONSUMERS of this system. Phase 8 is the entry gate
plus the pull seam to the two reader surfaces; the consumers' internal steps live
in the manual-assembly and website-ascent lanes. Reuse the proven 9-gate
`DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md`; recipes and the manual ladder are in
`FULL_STACK_DOCUMENTATION_PHASE8_PUBLICATION_ASCENT_PLAN_V1.md`. A flush is not
full until both consumers are live and verified.

## 3. Tool index

- Coverage/preflight: `docpush_preflight.py`, `command_catalog_sync.py`.
- Reference drift: `build_reference_identity_inventory.py`,
  `build_reference_authority_crosswalk.py`, `reference_disposition_recommend.py`,
  `refcheck_v1.py`, `normcheck_v1.py`.
- HELP refresh: `prepare_help_refresh_package.py`, `compare_runtime_baselines.py`,
  `compare_help_meta_harvest.py`.
- External tool runbooks: `METACOLLECT_RUNBOOK_V1.md`, `tools\manualgen\README.md`.
- Reference automation (candidate): `dotref_autogen.py`.

## 4. Where records go

- Run artifacts: `.../runs/DOCFLUSH-YYYYMMDD-NNN/` (baseline, help_refresh,
  metacollect_phase, manualgen_phase).
- Gate records: `GATE<N>_..._V1.md` in the relevant phase dir (no audit envelope).
- Run closeout / continuation: in the run dir; `SESSION_CLOSEOUT_*` needs the audit
  envelope, `NEXT_PUSH_CONTINUATION` does not.
- Regenerable CSVs: left untracked (gitignored); bound by SHA in the record.
