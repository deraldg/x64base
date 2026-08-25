# Full-stack documentation flush complete handoff v1

Run: `DOCFLUSH-20260722-001`  
AI Portal intake: `AIF-048`  
Recorded: 2026-07-26  
Authority root: `D:\code\ccode`  
Website root: `D:\dev\x64base-site`  
Staging root: `C:\x64base`  
Python authority: `D:\code\ccode\.venv312\Scripts\python.exe` (3.12.9)  
Current state: **Gates 0-5 PASS locally; Gates 6-7 PENDING**  

## Purpose

This is the restartable human and AI handoff for the second full-stack
documentation vertical. It records:

- the authority chain from source contracts to public readback;
- the exact run, source, manual, website, and AI Portal files;
- the commands needed to audit, rebuild, preview, publish, and verify;
- the dirty-worktree and staging boundaries;
- the difference between completed local work and work that is actually live.

The complete file-by-file run inventory is:

`FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv`

That CSV lists every other file under this run by relative path, phase, file
name, extension, byte count, and UTC modification time. It intentionally
excludes itself so that its own size does not make the inventory circular.
Run CSV files match the repository's
`docs/maintenance/lanes/**/runs/**/*.csv` ignore rule, so this inventory and
the progress ledger will not enter a normal `git add`. Gate 6 must explicitly
decide whether to retain them as local evidence or force-add the two reviewed
CSV files; do not weaken the global ignore rule.

## Outcome at handoff

| Gate | State | Bound result |
| --- | --- | --- |
| 0 -- mission/baseline | PASS | C4 maintenance vertical, authority order, runtime/Python/site roots, and dirty-tree boundaries recorded |
| 1 -- comments/contracts | PASS | 1,032 files; 243 complete live `SRCUSAGE` contracts after the coverage repair |
| 2 -- references/crosswalk | PASS | six reference repairs; 212 aligned commands; 593 entities; zero duplicate logical IDs |
| 3 -- HELP | PASS | 459 legacy commands; 2,566 arguments; 575 current topics; 29,197 lines; clean `CMDHELPCHK` |
| 4 -- manual/SelfDoc | PASS | 191 command pages; 4,604 lineage rows; 26 parts; 14,542 lines; 298-page PDF |
| 5 -- website candidate | PASS LOCAL | 117/117 declared pages; 132 static routes; current-work, VDISK, identity/security, family tree, and 21-file source museum locally inspectable |
| 6 -- commit/publication | **PENDING** | source evidence is not selectively committed; website candidate is dirty and uncommitted; no deploy performed |
| 7 -- live readback/closeout | **PENDING** | new historical routes and artifact are 404 live; live manual differs from local candidate |

The local work is therefore complete through reviewable website assembly, not
complete from source through public publication.

## Authority chain

```text
runtime proof
  -> implementation and embedded @dottalk.usage contracts
  -> comments SRC* evidence
  -> dotref.hpp / foxref.hpp / edref.hpp
  -> legacy HELP + current HELP
  -> CMDHELPCHK
  -> SelfDoc and accepted evidence
  -> manualgen and manifest-driven manual assembly
  -> website maintained/generated/derived/reported views
  -> committed source and website identities
  -> GitHub Pages / x64base.com
  -> cache-bypassed live readback
```

`METACOLLECT-238-20260717-001` is a separate mission. Its 175 command and 63
function findings must not be silently absorbed into this run.

## Front doors and governance files

Read these first:

```text
D:\code\ccode\AI_README.md
D:\code\ccode\AI_PORTAL.md
D:\code\ccode\docs\agents\CURRENT_TARGET.md
D:\code\ccode\docs\ai-friendly\AI_FRIENDLY_DASHBOARD_V1.md
D:\code\ccode\docs\AI-Friendly\AI_INTERACTION_INTAKE_QUEUE_V1.md
D:\code\ccode\labtalk\registries\projects.yaml
D:\code\ccode\labtalk\registries\ai_portal_tasks.yaml
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\README.md
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\FULL_STACK_DOCUMENTATION_FLUSH_PLAN_V1.md
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\DOCUMENTATION_TO_X64BASE_COM_ASCENT_V1.md
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001.md
```

Do not replace `docs\agents\CURRENT_TARGET.md` for this lane. It is an
engineering-target pointer; the documentation run is an adjacent governed
vertical.

## Run control and progress files

```text
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\DOCUMENTATION_FLUSH_PROGRESS_LOG_V1.md
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\documentation_flush_progress_ledger_v1.csv
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\baseline_manifest_v1.json
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\baseline_help_hashes_v1.csv
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\FULLSTACK_DOCUMENTATION_FLUSH_COMPLETE_HANDOFF_V1.md
D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001\FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv
```

The run directory contains the following evidence phases. The CSV manifest is
the authoritative complete list of their individual files:

```text
comments_audit\
comments_reharvest\
documentation_coverage_repair\
help_refresh_candidate\
manualgen_phase\
promotion_execution\
promotion_preflight\
promotion_rollback\
reference_crosswalk\
runtime_baseline\
source_contract_repair\
website_phase\
```

The rollback directories are evidence and recovery material. They account for
most of the run's size. Do not broad-stage, move, compress, or delete them.

## Current worktree boundaries

Recorded 2026-07-26:

### Authoritative development

```text
root:   D:\code\ccode
branch: development
HEAD:   65c8dd422ec5f2e6d7e26c0e401d454fb8cba67f
tracked modifications observed:
  tools\fullstack_docs\source_census.py
  tools\staging\prepush_gate.py
untracked population: large and mixed, including this documentation run
```

Preserve all unrelated work. Never use `git clean`, `git reset --hard`,
`git checkout -- .`, or broad `git add -A` here.

### Website candidate

```text
root:       D:\dev\x64base-site
branch:     codex/lean-sites-publish
HEAD:       24480861372b4e59a86d40ed6e330d27cd56e1ad
state:      25 modified paths and 12 untracked path groups at inspection
Sites ID:   appgprj_6a46ac6764c88191ba9a5a500a2a6ee8
```

Candidate website files:

```text
app\docs\page.tsx
app\downloads\page.tsx
app\layout.tsx
app\page.tsx
config\sidebars.ts
config\site-status.ts
content\docs\dev\current-lanes.mdx
content\docs\dev\developer-manual.mdx
content\docs\dev\documentation-progress.mdx
content\docs\dev\full-stack-documentation-push.mdx
content\docs\dev\historical-family-tree.mdx
content\docs\dev\historical-source-files.mdx
content\docs\dev\historical-source-lineage.mdx
content\docs\dev\important-documents.mdx
content\docs\dev\manual-assembly.mdx
content\docs\dev\roadmap.mdx
content\docs\dev\selfdoc-feed-pipeline.mdx
content\docs\dev\website-documentation-matrix.mdx
content\docs\dottalk\command-catalog.mdx
content\docs\dottalk\command-reference.mdx
content\docs\engine\feature-crosswalk.mdx
content\docs\engine\identity-security.mdx
content\docs\engine\ram-dbf-vdisk.mdx
content\docs\labtalk\agent-sync.mdx
content\docs\labtalk\current-work.mdx
public\artifacts\current-work-v1.json
public\artifacts\documentation-progress-v1.json
public\artifacts\source-lineage\historical-source-files-v1.csv
public\artifacts\source-lineage\historical-source-files-v1.json
public\artifacts\source-lineage\historical-source\
public\artifacts\source-lineage\xbase-product-family-tree-v1.csv
public\downloads\current\DEVELOPER_MANUAL_LATEST.json
public\downloads\current\DOWNLOAD_MANIFEST.json
public\downloads\current\developer-manual-latest.html
public\downloads\current\developer-manual-latest.md
public\downloads\current\developer-manual-latest.pdf
scripts\check-public-content.mjs
```

The historical-source directory contains 21 escaped HTML viewers and 21
byte-preserved `.txt` downloads. Its JSON and CSV manifests bind their archive
member names, sizes, dates, and SHA-256 values.

### Rebuildable staging

```text
root:   C:\x64base
branch: main
HEAD:   7f0d1efa2a23cb691688309767f7ddd8aa066513
state:  clean at inspection
drift:  one local commit ahead and fourteen cached-upstream commits behind
```

Do not copy development or website artifacts into staging yet. Fetch and
reconcile its unique/restorable artifacts before any overlay or rebuild.

## Command conventions

Run commands from PowerShell. Use Python 3.12 explicitly:

```powershell
Set-Location -LiteralPath 'D:\code\ccode'
$Py = 'D:\code\ccode\.venv312\Scripts\python.exe'
$Runtime = 'D:\code\ccode\build\src\Release\dottalkpp.exe'
$Run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260722-001'
$Site = 'D:\dev\x64base-site'
& $Py --version
```

Top-level `--script` does not share every `DOTSCRIPT`/`REGRESSION` comment
semantic. Keep generated runner comments as `*` unless that separate drift is
resolved.

## Gate 0 -- status and immutable baseline checks

Read-only worktree identity:

```powershell
git -C 'D:\code\ccode' branch --show-current
git -C 'D:\code\ccode' rev-parse HEAD
git -C 'D:\code\ccode' status --short
git -C 'D:\dev\x64base-site' branch --show-current
git -C 'D:\dev\x64base-site' rev-parse HEAD
git -C 'D:\dev\x64base-site' status --short
git -C 'C:\x64base' branch --show-current
git -C 'C:\x64base' rev-parse HEAD
git -C 'C:\x64base' status --short
```

Runtime identity:

```powershell
Get-Item -LiteralPath $Runtime | Select-Object FullName,Length,LastWriteTimeUtc
Get-FileHash -Algorithm SHA256 -LiteralPath $Runtime
Get-Process -Name dottalkpp -ErrorAction SilentlyContinue |
    Select-Object Id,Path,StartTime
```

Do not cross a protected DBF/HELP mutation gate while a runtime is open.

## Gate 1 -- source comments and contracts

Canonical source-comment reload script:

```text
D:\code\ccode\dottalkpp\data\scripts\comments\SOURCE_COMMENT_RESET_RELOAD.dts
```

This run's approved and executed mutation script:

```text
promotion_preflight\SOURCE_COMMENT_RESET_RELOAD_DOCFLUSH_20260722_001.dts
```

The run-specific script is historical evidence and must not be casually
rerun. A future reharvest must create a new run-specific script and a new
preflight/rollback package.

Read-only census and test commands:

```powershell
& $Py '.\tools\fullstack_docs\source_census.py' --help
& $Py -m unittest discover -s '.\tools\comments\tests' -p 'test_*.py'
```

Governed reload form, only after a new authorization and zero-process check:

```powershell
& $Runtime --script (Join-Path $Run 'promotion_preflight\SOURCE_COMMENT_RESET_RELOAD_DOCFLUSH_20260722_001.dts')
```

Recovery authority:

```text
promotion_rollback\20260722T205759\
documentation_coverage_repair\promotion_rollback\20260723T070924Z\
```

The first package protects the 242-contract promotion. The second protects the
243-contract coverage-repair promotion. Use the package matching the failed
mutation; never mix their files.

## Gate 2 -- references and crosswalk

Primary reference authorities:

```text
D:\code\ccode\include\dotref.hpp
D:\code\ccode\include\foxref.hpp
D:\code\ccode\include\edref.hpp
D:\code\ccode\include\reference\
```

Reusable tools:

```text
tools\fullstack_docs\build_reference_identity_inventory.py
tools\fullstack_docs\build_reference_authority_crosswalk.py
tools\fullstack_docs\audit_help_contract_continuation.py
tools\fullstack_docs\audit_supported_command_publication_coverage.py
```

Always inspect each command surface before reusing inherited evidence:

```powershell
& $Py '.\tools\fullstack_docs\build_reference_identity_inventory.py' --help
& $Py '.\tools\fullstack_docs\build_reference_authority_crosswalk.py' --help
& $Py '.\tools\fullstack_docs\audit_help_contract_continuation.py' --help
& $Py '.\tools\fullstack_docs\audit_supported_command_publication_coverage.py' --help
```

The crosswalk must receive explicit current-run input paths and `--run-id
DOCFLUSH-20260722-001`. Do not accept default paths inherited from the July 16
run. The passing evidence is under `reference_crosswalk\` and
`documentation_coverage_repair\continuation_audit_v4\`.

## Gate 3 -- compile and HELP refresh

Compile the current Release runtime:

```powershell
cmake --build 'D:\code\ccode\build' --config Release --target dottalkpp
if ($LASTEXITCODE -ne 0) { throw "Release build failed: $LASTEXITCODE" }
Get-FileHash -Algorithm SHA256 -LiteralPath $Runtime
```

Legacy-first/current HELP script:

```text
help_refresh_candidate\BUILD_LEGACY_THEN_CURRENT_HELP_V1.dts
```

Coverage-repaired successor:

```text
documentation_coverage_repair\BUILD_REPAIRED_HELP_CANDIDATE_V1.dts
```

Their essential command order is:

```text
CMDHELP BUILD LEGACY . D:\code\ccode\src D:\code\ccode\include D:\code\ccode\bindings
CMDHELP BUILD . D:\code\ccode\src D:\code\ccode\include D:\code\ccode\bindings
CMDHELPCHK
CMDHELPCHK ARTIFACTS . 20
CMDHELPCHK . 20
```

Execute only against a newly prepared isolated target or a separately
authorized live gate:

```powershell
& $Runtime --script (Join-Path $Run 'documentation_coverage_repair\BUILD_REPAIRED_HELP_CANDIDATE_V1.dts')
```

Passing transcripts and promotion records:

```text
promotion_execution\COMMENTS_HELP_PROMOTION_RESULT_V1.md
promotion_execution\HELP_POST_PROMOTION_PROOF_V1_stdout.txt
promotion_execution\LANGUAGE_SHAKEDOWN_CANARY_POST_PROMOTION_stdout.txt
documentation_coverage_repair\COMMENTS_HELP_COVERAGE_REPAIR_PROMOTION_RESULT_V1.md
documentation_coverage_repair\HELP_POST_PROMOTION_PROOF_V2_stdout.txt
```

## Gate 4 -- Manualgen, assembly, formats, and SelfDoc

Manual authorities:

```text
D:\code\ccode\tools\manualgen\manualgen.py
D:\code\ccode\tools\manualgen\manual_assembly_manifest.yaml
D:\code\ccode\tools\manualgen\assemble_manual.py
D:\code\ccode\tools\manualgen\check_manual_drift.py
D:\code\ccode\tools\manualgen\render_manual_formats.ps1
D:\code\ccode\docs\manuals\developer\manualgen\generated\assembled\
D:\code\ccode\docs\manuals\command_reference\
D:\code\ccode\selfdoc\
```

Inventory and validation:

```powershell
& $Py '.\tools\manualgen\manualgen.py' --repo-root 'D:\code\ccode' --manual developer inventory
& $Py '.\tools\manualgen\manualgen.py' --repo-root 'D:\code\ccode' --manual developer validate
& $Py -m unittest discover -s '.\tools\manualgen\tests' -p 'test_*.py'
& $Py -m unittest discover -s '.\tools\fullstack_docs\tests' -p 'test_*.py'
```

Assemble and fail closed on drift:

```powershell
& $Py '.\tools\manualgen\assemble_manual.py'
if ($LASTEXITCODE -ne 0) { throw "Manual assembly failed: $LASTEXITCODE" }
& $Py '.\tools\manualgen\check_manual_drift.py'
if ($LASTEXITCODE -ne 0) { throw "Manual drift gate failed: $LASTEXITCODE" }
```

Render Markdown/HTML/PDF:

```powershell
& '.\tools\manualgen\render_manual_formats.ps1' -RepositoryRoot 'D:\code\ccode'
```

Stage the accepted assembled formats to the website candidate:

```powershell
& $Py '.\tools\fullstack_docs\stage_assembled_manual_to_site.py' --site-root $Site
```

The latest local PDF at handoff:

```text
D:\dev\x64base-site\public\downloads\current\developer-manual-latest.pdf
SHA-256: 33D969758D195DD8BE2B8A763CEA1B81BE259687FD9BA8BA368B9412B798B036
pages: 298
```

## Gate 5 -- website feeds, historical source, build, and preview

Generate the current project/task view from the AI Portal registries:

```powershell
& $Py '.\tools\fullstack_docs\build_current_work_feed.py' `
  --projects '.\labtalk\registries\projects.yaml' `
  --tasks '.\labtalk\registries\ai_portal_tasks.yaml' `
  --out-json (Join-Path $Site 'public\artifacts\current-work-v1.json') `
  --out-mdx (Join-Path $Site 'content\docs\labtalk\current-work.mdx')
```

Regenerate the inspectable historical source museum:

```powershell
& $Py '.\tools\fullstack_docs\build_historical_source_museum.py' `
  --archive 'D:\code\xbase\xbase.zip' `
  --out-files (Join-Path $Site 'public\artifacts\source-lineage\historical-source') `
  --out-page (Join-Path $Site 'content\docs\dev\historical-source-files.mdx') `
  --out-json (Join-Path $Site 'public\artifacts\source-lineage\historical-source-files-v1.json') `
  --out-csv (Join-Path $Site 'public\artifacts\source-lineage\historical-source-files-v1.csv')
```

Focused generator tests:

```powershell
& $Py -m unittest tools.fullstack_docs.tests.test_build_current_work_feed
& $Py -m unittest tools.fullstack_docs.tests.test_build_historical_source_museum
```

Website guard, TypeScript, and production build:

```powershell
Set-Location -LiteralPath $Site
npm run check:public-content
& '.\node_modules\.bin\tsc.cmd' --noEmit --incremental false -p '.\tsconfig.json'
npm run build
```

The build performs public-content checking, clean output, Next.js static build,
and Sites artifact assembly. The accepted local result was 132 static routes.

Serve the production export:

```powershell
& $Py -m http.server 3000 --directory (Join-Path $Site 'out')
```

Local review routes:

```text
http://127.0.0.1:3000/
http://127.0.0.1:3000/docs/dev/documentation-progress/
http://127.0.0.1:3000/docs/dev/full-stack-documentation-push/
http://127.0.0.1:3000/docs/labtalk/current-work/
http://127.0.0.1:3000/docs/engine/ram-dbf-vdisk/
http://127.0.0.1:3000/docs/engine/identity-security/
http://127.0.0.1:3000/docs/dev/historical-family-tree/
http://127.0.0.1:3000/docs/dev/historical-source-files/
http://127.0.0.1:3000/downloads/current/developer-manual-latest.pdf
```

Stop the preview by returning to the server console and pressing `Ctrl+C`.

## AI Portal and audit commands

Headless portal audit:

```powershell
Set-Location -LiteralPath 'D:\code\ccode'
& $Py '.\labtalk\portal\labtalk_portal.py' --audit-write
```

AI-report audit:

```powershell
& $Py '.\labtalk\ai_portal\audit_trail.py'
```

At handoff, the broader report audit still reports 16 pre-existing
front-matter or Git-envelope findings in unrelated July 18-22 closeouts. They
are a separate remediation lane. Do not report the overall audit as green and
do not rewrite historical closeouts merely to make this run pass.

If a GUI portal is desired, first verify `tkinter` exists in the exact Python
3.12 interpreter. Headless audit is the required path and does not depend on
Tk.

## Gate 6 -- commit and publication procedure

**STOP: this gate has not run.**

Before any commit:

1. Create and review an exact source-evidence path list.
2. Exclude rollback payloads, unrelated dirty files, build products, and
   private/local-only material.
3. Stage only that path list in `D:\code\ccode`.
4. Inspect the staged diff and public-content implications.
5. Commit and push source evidence first.
6. Regenerate all source-commit-bound website artifacts.
7. Rebuild and review the website.
8. Commit and push the website candidate.
9. Publish the clean website commit.

Safe inspection commands:

```powershell
git -C 'D:\code\ccode' status --short
git -C 'D:\code\ccode' diff --stat
git -C 'D:\code\ccode' diff --cached --stat
git -C 'D:\code\ccode' diff --cached --check
git -C 'D:\dev\x64base-site' status --short
git -C 'D:\dev\x64base-site' diff --stat
git -C 'D:\dev\x64base-site' diff --check
```

Do not invent the selective source list from the current 1,000-plus-row
worktree during a publication run. Preparing and approving that list is the
next missing Gate 6 artifact.

To inspect the intentional CSV ignore before that decision:

```powershell
git -C 'D:\code\ccode' check-ignore -v -- `
  (Join-Path $Run 'documentation_flush_progress_ledger_v1.csv') `
  (Join-Path $Run 'FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv')
```

If and only if the reviewed Gate 6 scope explicitly includes those two
machine-readable records, stage their exact paths with `git add -f -- <path>`;
never force-add the run directory.

GitHub Pages publication command, only after the website worktree is clean and
its exact commit is approved:

```powershell
Set-Location -LiteralPath 'D:\dev\x64base-site'
npm run publish:github-pages
```

That script:

- refuses a dirty website source tree;
- fetches and rebases the `gh-pages` worktree;
- rebuilds the site with the source commit identity;
- writes `/artifacts/site-release.json`;
- replaces the deploy worktree contents;
- commits and pushes `gh-pages`.

It is mutating and public. Do not run it as a verification command.

Sites publication is a separate provider action. Reuse project
`appgprj_6a46ac6764c88191ba9a5a500a2a6ee8`, push the exact committed source
state, save a version, deploy only that saved version, and inspect deployment
status. GitHub Pages success does not imply Sites success.

## Gate 7 -- live readback and closeout

Current live discrepancy recorded 2026-07-26:

```text
https://www.x64base.com/docs/dev/documentation-progress/                 200
https://www.x64base.com/docs/dev/historical-family-tree/                 404
https://www.x64base.com/docs/dev/historical-source-files/                404
https://www.x64base.com/artifacts/source-lineage/historical-source-files-v1.json 404
https://www.x64base.com/downloads/current/developer-manual-latest.pdf    200
```

The live PDF SHA-256 was:

```text
E6E155CE650F85186396DFB649B79FD70FECF1A145237838305EF5DE7B7346DF
```

It differs from the local candidate. After publication, verify with a
cache-bypass token:

```powershell
$Stamp = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$Urls = @(
  "https://www.x64base.com/?cb=$Stamp",
  "https://www.x64base.com/docs/dev/documentation-progress/?cb=$Stamp",
  "https://www.x64base.com/docs/dev/full-stack-documentation-push/?cb=$Stamp",
  "https://www.x64base.com/docs/labtalk/current-work/?cb=$Stamp",
  "https://www.x64base.com/docs/engine/ram-dbf-vdisk/?cb=$Stamp",
  "https://www.x64base.com/docs/engine/identity-security/?cb=$Stamp",
  "https://www.x64base.com/docs/dev/historical-family-tree/?cb=$Stamp",
  "https://www.x64base.com/docs/dev/historical-source-files/?cb=$Stamp",
  "https://www.x64base.com/artifacts/source-lineage/historical-source-files-v1.json?cb=$Stamp",
  "https://www.x64base.com/downloads/current/developer-manual-latest.pdf?cb=$Stamp"
)
foreach ($Url in $Urls) {
  $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing
  [pscustomobject]@{
    Status = [int]$Response.StatusCode
    Bytes = $Response.RawContentLength
    Type = $Response.Headers['Content-Type']
    Url = $Url
  }
}
```

Download and compare the live manual:

```powershell
$LivePdf = Join-Path $env:TEMP 'x64base-developer-manual-live.pdf'
Invoke-WebRequest `
  -Uri "https://www.x64base.com/downloads/current/developer-manual-latest.pdf?cb=$Stamp" `
  -OutFile $LivePdf
Get-FileHash -Algorithm SHA256 -LiteralPath $LivePdf
Get-FileHash -Algorithm SHA256 -LiteralPath `
  'D:\dev\x64base-site\public\downloads\current\developer-manual-latest.pdf'
```

Close Gate 7 only when:

- all intended routes and machine artifacts return 200;
- public and local expected hashes agree;
- `/artifacts/site-release.json` names the approved website commit;
- current-state dates and AI-generation notices are correct;
- source viewers contain the expected files and navigation;
- public-content checks find no private workstation path leakage;
- the progress log, machine ledger, AI dashboard, and run root record the
  actual public commit and live readback.

## Complete run-file inventory command

Rebuild the complete filename manifest with Python 3.12:

```powershell
Set-Location -LiteralPath 'D:\code\ccode'
& $Py '.\tools\fullstack_docs\build_fullstack_handoff_manifest.py' `
  --run-root $Run `
  --output (Join-Path $Run 'FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv')
```

Quick inventory queries:

```powershell
Import-Csv (Join-Path $Run 'FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv') |
  Group-Object phase |
  Sort-Object Name |
  Select-Object Name,Count

Import-Csv (Join-Path $Run 'FULLSTACK_DOCUMENTATION_FLUSH_FILE_MANIFEST_V1.csv') |
  Where-Object extension -eq '.dts' |
  Select-Object relative_path
```

## Handoff validation

The completed handoff was checked on 2026-07-26:

- Manualgen suite: 58/58 PASS.
- Full-stack documentation suite: 46/46 PASS.
- AI Portal task registry: YAML parses; eight task entries; current run date,
  132-route count, and Gate 6 state verified.
- File inventory: 581 actual files equal 581 CSV rows; zero missing paths,
  zero extra paths, and zero duplicates.
- Markdown structure: all command fences are balanced and all eight gate
  sections are present.

## Immediate next action

Gate 6 needs a selective source-promotion scope manifest. It must name only the
documentation-flush source/manual/AI Portal evidence intended for publication
and explicitly exclude the large rollback packages and unrelated worktree.
After that manifest receives review, commit source evidence, regenerate the
website against the real source commit, rebuild locally, and request the
separate public deployment decision.
