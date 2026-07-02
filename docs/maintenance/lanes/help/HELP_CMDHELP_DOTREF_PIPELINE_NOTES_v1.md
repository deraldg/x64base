# HELP / CMDHELP / DOTREF Pipeline Notes v1

Status: captured maintenance manifest
Lane: help

## Purpose

The HELP lane turns registry, source contracts, curated references, and mined evidence into user/developer help surfaces.

## Known surfaces

- HELP
- HELP /DOT
- DOTHELP
- FOXHELP
- CMDHELP
- CMDHELP BUILD
- CMDHELP BUILD LEGACY
- CMDHELP LEGACY
- CMDHELPCHK

## Observed split

Recent MANUAL/DDICT work proved that current HELP DATA and DOTHELP routing are related but not identical.

Historical investigation state:

- MANUAL runtime command worked.
- MANUAL USAGE worked.
- CMDHELP MANUAL worked.
- CMDHELP DDICT worked.
- HELP /DOT MANUAL was red during that investigation.
- HELP /DOT DDICT was red during that investigation.

Current runtime smoke on 2026-06-26:

- DOTHELP MANUAL: green
- HELP /DOT MANUAL: green
- DOTHELP DDICT: green
- HELP /DOT DDICT: green
- DOTHELP DOTHELP: green
- HELP /DOT DOTHELP: green
- DOTHELP FOXHELP: green
- HELP /DOT FOXHELP: green
- HELP: green
- HELP HELP: green
- HELP /DOT HELP: green
- HELP /FOX REL: green
- CMDHELP: green
- CMDHELP USAGE: green
- FOXHELP: green
- FOXHELP APPEND: green
- FH REL: green

Current same-pass closeout on 2026-06-26:

- [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md:1)
- `CMDHELPCHK`: green
- `CMDHELPCHK ARTIFACTS . 5`: green
- `CMDHELP DDICT`: green
- `CMDHELP MANUAL`: green
- `DDICT HELP`: green
- `MANUAL USAGE`: green

This means two things remain true:

- CMDHELP visibility still does not by itself prove DOTHELP/HELP /DOT visibility.
- the earlier MANUAL/DDICT router red state is no longer an active defect in the current repo runtime.

And one more thing is now true:

- `DDICT` and `MANUAL` are no longer pending checkpoint work; both are closed through the current same-pass `CMDHELPCHK` / HELP DATA / CMDHELP / DOTREF-router validation chain.

Recent direct proof artifacts:

- [DOTHELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/DOTHELP_COMMENTS_HELP_PROOF_REPORT_v1.md:1)
- [FOXHELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/FOXHELP_COMMENTS_HELP_PROOF_REPORT_v1.md:1)
- [HELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/HELP_COMMENTS_HELP_PROOF_REPORT_v1.md:1)
- [CMDHELP_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/CMDHELP_COMMENTS_HELP_PROOF_REPORT_v1.md:1)
- [DDICT_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_COMMENTS_HELP_PROOF_REPORT_v1.md:1)
- [MANUAL_COMMENTS_HELP_PROOF_REPORT_v1.md](D:/code/ccode/docs/maintenance/reviews/MANUAL_COMMENTS_HELP_PROOF_REPORT_v1.md:1)
- [DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md](D:/code/ccode/docs/maintenance/reviews/DDICT_MANUAL_CMDHELPCHK_CLOSEOUT_20260626_v1.md:1)

Current parent-surface continuity note:

- `HELP` is green end to end.
- `CMDHELP` is green end to end.
- the earlier parent-surface comments-lane defect was caused by line-oriented `IMPORT`; after making `IMPORT` CSV-record aware, `SOURCE_COMMENT_RESET_RELOAD` imported all `909` `SRCFILE` rows and both `HELP` and `CMDHELP` landed correctly in live `SRCFILE`.

## Inputs

- runtime command registry
- source `@dottalk.usage v1`
- source comments
- `dotref.hpp`
- `foxref.hpp`
- curated rows
- source miner facts
- legacy commands/cmd_args where applicable

## Process

- CMDHELP BUILD writes current HELP DATA.
- CMDHELP BUILD LEGACY writes or reports legacy command help tables depending on command implementation.
- DOTHELP/HELP /DOT consult DOTREF routing.
- CMDHELP reports current HELP DATA.

Current locale rule:

- normal `CMDHELP <topic>` remains canonical/source-authority HELP
- locale companion rows are preserved as sidecars
- a later locale-aware consumer should preview locale rows explicitly instead of silently replacing canonical HELP text

## Outputs

- help_line.dbf
- help_topic.dbf
- help_artifacts.dbf
- commands.dbf
- cmd_args.dbf
- CMDHELP reports
- HELP runtime output
- DOTHELP runtime output

## Required cookbook rule

Do not patch HELP DATA blindly when HELP /DOT fails. First classify the failing layer:

1. runtime command surface
2. source usage contract
3. comments/SRC* evidence
4. HELP DATA/CMDHELP
5. DOTREF source/catalog
6. compiled binary/install copy
7. HELP router

## Controls

HELP mutation requires:

- pre-apply baseline
- backup
- rollback script
- apply result
- post-apply CMDHELP smoke
- post-apply HELP/HELP /DOT smoke
- boundary ledger

Locale-aware HELP mutation also requires:

- proof that canonical HELP rows remain intact
- proof that locale rows resolve by canonical identity plus `LOCALE_ID`
- proof that missing or draft locale rows fall back to canonical HELP text
