# DEV-17 Contributor Rules

```yaml
page_id: DEV-17
title: Contributor Rules
status: DRAFT_PATCHED
last_verified: 2026-07-07
```

## Done definition

A change is not done until source, HELP, META, CMDHELPCHK, runtime proof, canaries, manual evidence, and AUTOLOG are all checked or explicitly marked pending/canary.

## Core rule

```text
If you change behavior, update evidence.
If you change evidence, verify behavior.
If you write the manual, cite the evidence.
If something disagrees, create a canary or gap report.
```

## Current command/help refresh rule

If a command surface, usage contract, or reference-header catalog changed, the
current default operator sequence is:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Practical meaning:

- `CMDHELP BUILD LEGACY` keeps the classic `commands.dbf` / `cmd_args.dbf` lane
  synchronized when `dotref.hpp` changed
- the explicit source-root build refreshes the richer HELP DATA lane
- `CMDHELPCHK` is the structural gate after rebuild

## Regression maintenance rule

If a regression DotScript is still useful:

- make it bootstrap its own environment
- keep it curated under stable regression entrypoints
- prefer promotion into the `REGRESSION` launcher over leaving it as
  unclassified historical debris

If it is no longer useful, retire it instead of leaving a misleading script in
place.

## Report-first safety boundary

Safe default actions: read evidence, produce inventories, produce crosswalks, produce gap reports, produce diagrams, produce manual drafts.

Actions requiring explicit authorization: mutate HELP DBFs, mutate META DBFs, rewrite source comments, change CMDHELPCHK behavior, change classifier policy, rebuild HELP DATA, or change public/internal surface classification.

## Accessibility / inclusive design rule

This is a scholastic project. Accessibility and inclusive design are part of the
done definition, not a final presentation pass.

For source-backed manuals, generated reports, diagrams, websites, downloads,
GUI/TUI surfaces, and classroom artifacts:

- provide text alternatives for non-text content;
- do not use color as the only status signal;
- keep keyboard navigation and visible focus in mind for UI surfaces;
- preserve screen-reader-friendly structure with real headings, table headers,
  and prose summaries for code or diagrams;
- label promoted artifacts with accessibility status when review is pending.

Accessibility gaps should be recorded as `GAP`, `REVIEW`, or `CANARY` rather
than hidden behind polished publication copy.
