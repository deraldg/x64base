# Maintenance Launcher Index Plan v1

Status: plan-only.

This plan defines proposed report-only launcher names for the external DotTalk++ maintenance root.

Shared workflow/doctrine for the comments/help family:

- `docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md`

## Roots

- External maintenance root: `dottalkpp\scripts\maintenance`
- Runtime DotTalk script root: `dottalkpp\data\scripts`
- Future native C++ maintenance source root: `src\maintenance`

## Policy

- Launchers start as report-only.
- No launcher may mutate source, runtime scripts, HELP, META, CMDHELPCHK, DBFs, CDX/LMDB, publications, or media without a separate guarded package.
- Launchers should call existing reports/cookbooks before attempting any maintenance action.
- Runtime scripts remain under `dottalkpp\data\scripts`; external maintenance scripts remain under `dottalkpp\scripts\maintenance`.

## Proposed Launchers

- `maint_status.ps1` (maintenance): Report maintenance root, lane, and cookbook status.
- `maint_lanes.ps1` (maintenance): List maintenance lanes, docs roots, script roots, and runtime surfaces.
- `maint_comments_pipeline_scan.ps1` (comments): Scan comments/SRC* pipeline tools and report source-contract evidence paths.
- `maint_help_pipeline_scan.ps1` (help): Trace HELP DATA build, CMDHELP proof, DOTREF routing, and HELP /DOT inputs and outputs.
- `maint_cmdhelpchk_status.ps1` (cmdhelpchk): Report CMDHELPCHK inputs, expected checks, and current validation artifacts.
- `maint_manualgen_status.ps1` (manualgen): Report manualgen active publication, MAN* catalog, and regeneration-cycle evidence.
- `maint_datadict_status.ps1` (datadict): Report DD* catalog, x64 DATA_DICTIONARY_* roots, bridge policy, and DDICT status evidence.
- `maint_messaging_inventory.ps1` (messaging): Report message catalog seeds, SET LANGUAGE/LOCALE hook, and hard-coded output extraction candidates.
- `maint_blackbox_map.ps1` (blackbox): Report Blackbox lanes using DATA IN / PROCESS / INFORMATION OUT framing.

## Next Gate

MDO-306 may create non-executable launcher placeholders only after explicit authorization.
