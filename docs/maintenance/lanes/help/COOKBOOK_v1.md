# help Blackbox cookbook v1

## Data in
registry, DOTREF, FOXREF, source usage contracts, curated rows

## Blackbox process
CMDHELP BUILD, legacy comparison, HELP DATA generation, lookup smoke

## Information out
help_line/help_topic/help_artifacts, commands/cmd_args, HELP output, CMDHELP output, DOTHELP/HELP /DOT output

## Current proof layers
- `CMDHELP BUILD` builds current HELP DATA from registry, source usage contracts, curated rows, and direct source mining.
- `CMDHELP` proves current HELP DATA visibility.
- `DOTHELP` / `HELP /DOT` prove compiled DOTREF/router visibility.
- These proof surfaces are related, but one green surface does not prove the others.
- `COMMENTS` evidence now has to be checked first because the canonical reload path is part of the live continuity chain.

## Controls
- Start report-only unless a separate apply gate is explicitly authorized.
- Name inputs, outputs, backups, rollback, smoke tests, and next gate before mutation.
- Runtime scripts remain under dottalkpp/data/scripts; maintenance scripts live here.
- Source code remains outside this lane unless a separate source-mutation package is authorized.
- When staged/live comments rows diverge, inspect the staged import snapshot and canonical reload path before blaming HELP DATA or DOTREF.
- Treat canonical HELP rows as source-authority and locale HELP rows as companion overlays until a later consumer explicitly requests locale preview.

## Current doctrine set
- [COMMENTS_HELP_PROOF_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/COMMENTS_HELP_PROOF_WORKFLOW_v1.md)
- [HELP_LOCALE_WORKFLOW_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_LOCALE_WORKFLOW_v1.md)
- [HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_CMDHELP_DOTREF_PIPELINE_NOTES_v1.md)
- [HELP_FAMILY_STATUS_MANIFEST_v1.md](D:/code/ccode/docs/maintenance/lanes/help/HELP_FAMILY_STATUS_MANIFEST_v1.md)

## Current next gate
curated `CMDHELPCHK` closeout is now green for the parent help-family surfaces; the next locale-aware gate is a controlled `CMDHELP` locale preview consumer with canonical fallback
