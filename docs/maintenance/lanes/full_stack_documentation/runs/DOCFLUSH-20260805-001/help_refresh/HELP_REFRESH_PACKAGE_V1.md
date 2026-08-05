# HELP refresh package v1 (Phase 3)

Run: `DOCFLUSH-20260805-001`
Gate: 3, reviewed HELP refresh package (full-stack doc flush v4)
Prepared: 2026-08-05 (sandbox; report-only -- no mutation performed here)
Status: AUTHORIZED by member.derald 2026-08-05 (Gate 3 passed). Build runs on the
host; sandbox cannot build. Order confirmed: `CMDHELP BUILD LEGACY` then
`CMDHELP BUILD . D:\code\ccode\src` (the second pass generates the dotref commands).

## Finding that shapes this package

The Phase 2 baseline transcript already shows every v4-touched topic resolving
against live HELP DATA:

```
CMDHELP NET          -> DOT|NET
CMDHELP CANARY       -> DOT|CANARY
CMDHELP CMDREL       -> DOT|CMDREL FOX|CMDREL
CMDHELP FORMULA      -> DOT|FORMULA FOX|FORMULA EDU|FORMULA
CMDHELP EDIT         -> DOT|EDIT FOX|EDIT EDU|EDIT
CMDHELP DDICT        -> DOT|DDICT
CMDHELP EVALDIFF     -> DOT|EVALDIFF
CMDHELP BUILDVECTORS -> DOT|BUILDVECTORS
```

Zero "No help found" in the targeted tail; reflection PASS; 525 topics. The HELP
DATA store DBFs are timestamped 2026-08-05 09:49. So the store already reflects the
v4 dotref adds (BBS/NET/CANARY/CMDREL/FORMULA/EDIT) and the normalized contracts
(DDICT et al.). The "pre-refresh" baseline in fact captured a POST-build store.

Consequence: this package does NOT stage a corrective mutation. It authorizes a
deliberate, recorded rebuild for provenance and to guarantee LEGACY-store currency
(the 09:49 build's LEGACY coverage is unverified), with an EXPECTED near-zero diff
against the Phase 2 baseline. A near-zero diff is itself the Gate 4 evidence that
source and HELP DATA agree.

## Why a build is authorized

- `include/dotref.hpp` changed this pass (BBS/NET/CANARY/CMDREL/FORMULA/EDIT added;
  arrow glyphs normalized). The plan's conditional order makes a dotref.hpp change
  the trigger for `CMDHELP BUILD LEGACY` followed by `CMDHELP BUILD . <src>`.
- `@dottalk` contracts were added/normalized across `src/cli/cmd_*.cpp` and
  `src/edu/edu_*.cpp` (Phase 0.5), and DDICT's block contract was converted to
  `// @dottalk.usage` (Phase 1).
- The engine already carries these (runtime `dottalk++ v0.6 (5928e2eb dirty)`, dotref
  895 entries). The build recompiles HELP DATA + LEGACY from that engine.

## Inputs changed (authoritative list)

- `include/dotref.hpp` -- native command reference (rebuilt into the exe).
- `src/cli/cmd_ddict.cpp` -- contract format normalize.
- Phase 0.5 contract-bearing `src/cli/*` and `src/edu/*` files.
- `include/foxref.hpp` -- NORMALIZE + browser de-duplication. CONFIRMED (maintainer,
  2026-08-05): foxref feeds the LEGACY build. So `CMDHELP BUILD LEGACY` is REQUIRED
  to reflect these changes -- not merely a provenance rebuild. Expect a real LEGACY
  delta here (one NORMALIZE dup + 5 browser entries removed).

## HELP / legacy files expected to change

Primary HELP DATA store (`dottalkpp/data/help`):
`HELP_LINE.dbf`, `HELP_ARTIFACTS.dbf`, `HELP_TOPIC.dbf`, `HELP_SECTION.dbf`,
`COMMANDS.dbf`, `CMD_ARGS.dbf` (and their `.dbt`/`.dtx` sidecars).
LEGACY store (`dottalkpp/data/help/FULL`, `.../MINEALL`, `.../V32_help`): expected
change only if the LEGACY build path re-emits; confirm from the build transcript.

Given the finding above, expected magnitude is near-zero (idempotent rebuild).

## Pre-build backup manifest (reference hashes, current store)

Back up `dottalkpp/data/help` in full to a timestamped sibling before building.
Reference sizes + hash prefixes of the current (already-current) store:

```
HELP_LINE.dbf        13475282  d8a6a81386a699a9
HELP_ARTIFACTS.dbf    3628877  b1edc46c477bf93e
HELP_TOPIC.dbf         307914  7d338d7792386fab
HELP_SECTION.dbf      2661209  b431b71e72fca4fc
COMMANDS.dbf            48590  a8070d69a2456515
CMD_ARGS.dbf           299724  bebbc51f4bda4f7c
```

## Rollback

Restore the backup directory over `dottalkpp/data/help` (stop the `DotTalkBBSD`
task first if it holds the store), then re-run `CMDHELPCHK` to confirm reflection
PASS on the restored store. No git action -- the store is not version-controlled.

## Post-build checks (Gate 4 inputs)

1. `CMDHELPCHK` reflection structural status == PASS; blank artifact texts == 0.
2. `CMDHELP` line/topic counts >= Phase 2 baseline (28,368 / 525); record deltas.
3. Targeted topics still resolve: BBS/NET/CANARY/CMDREL/FORMULA/EDIT/DDICT/EVALDIFF/
   BUILDVECTORS (same evidence shape as Phase 2).
4. `command_catalog_sync.py check` fallback == 0 (no unreadable contracts).
5. Diff the post-build transcript against the Phase 2 baseline; near-zero expected.

## Authorized host command sequence (maintainer runs; sandbox cannot build)

```powershell
# 0. quiesce the daemon if it holds the store
Stop-ScheduledTask -TaskName 'DotTalkBBSD'

# 1. backup the HELP store
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
Copy-Item -Recurse D:\code\ccode\dottalkpp\data\help `
  "D:\code\ccode\dottalkpp\data\help.bak-$stamp"

# 2. authorized build (dotref.hpp changed -> LEGACY then full)
#    run inside the CLI over the work data:
./datarun.ps1 -CommandLines 'CMDHELP BUILD LEGACY','CMDHELP BUILD . D:\code\ccode\src'

# 3. post-build capture (report-only). datarun.ps1 has NO -Script/-script param;
#    the exe's --script pass-through gets mangled and lands on stdin as a command.
#    Proven path: source the .dts lines into -CommandLines (datarun stages them into
#    its own temp .dts). Use ABSOLUTE paths -- datarun pushes cwd to the data root.
$run = 'D:\code\ccode\docs\maintenance\lanes\full_stack_documentation\runs\DOCFLUSH-20260805-001\help_refresh'
./datarun.ps1 -CommandLines (Get-Content "$run\fullstack_post_refresh_runtime_v1.dts") `
  | Tee-Object "$run\fullstack_post_refresh_runtime_v1.txt"
Set-Location D:\code\ccode

# 4. restart the daemon
Start-ScheduledTask -TaskName 'DotTalkBBSD'
```

The post-build `.dts` mirrors the Phase 2 baseline script (ABOUT, CMDHELP*,
CMDHELPCHK*, DOTHELP/FOXHELP/HELP, MANUAL STATUS/COUNTS, the 9 targeted topics,
QUIT) so the two transcripts diff cleanly.

## Derivative (downstream of the build, not an engine mutation)

Regenerate the website command catalog from source and reconcile the site repo:

```powershell
python .\tools\fullstack_docs\command_catalog_sync.py emit `
  --source-root D:\code\ccode\src `
  --out D:\dev\x64base-site\content\docs\dottalk\command-catalog.mdx
```

(`command_catalog_sync` requires Python 3.12; run on the host interpreter.) Commit
the `.mdx` on the site repo as a separate slice, per the two-repo promotion rule.

## Gate 3 acceptance

- Maintainer authorizes the named mutation package (build LEGACY + full).
- Backup/rollback and affected paths are concrete (above).
- The build is NOT bundled with manual publication (Phase 6) or metadata import
  (Phase 5). This package is engine-HELP only plus the catalog derivative.
