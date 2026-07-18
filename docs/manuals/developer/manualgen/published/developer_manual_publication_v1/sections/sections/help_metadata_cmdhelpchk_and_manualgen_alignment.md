# HELP, Metadata, CMDHELPCHK, and Manualgen Alignment




Pippets used:
- PIP-001 Target Selection
- MDO-173 Target Selection
- MDO-174 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches truth authority doctrine, manual assembly workflow, HELP evidence, metadata evidence, CMDHELPCHK validation, SelfDoc provenance, source authority, and future feeder alignment.
- Do not send this directly to generic PIP-003.
- Run a slow-lane authority/alignment review first.

Evidence tokens under review:
- HELP
- HELP GIANT
- HELP_LINE
- HELP_ARTIFACTS
- CMDHELP
- CMDHELPCHK
- META
- metadata
- SYSCMD
- SYSSUBCMD
- SYSENTVAR
- SYSARGS
- SYSHELP
- SYSMSG
- SYSFUNC
- SOURCE
- SOURCE_FACT
- SelfDoc
- manualgen
- PIP
- validator
- crosswalk
- report-only
- truth authority
- assembly workflow

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- HELP/META/CMDHELPCHK-first is a manual assembly workflow, not a replacement for truth authority.
- Source remains implementation authority even when manualgen starts from HELP, metadata, and CMDHELPCHK.
- Sparse metadata feeders are future alignment lanes, not dead ends.
- Temporary evidence lanes must be labeled and crosswalked to future META feeders.
- Manualgen and SelfDoc work remain report-only unless explicitly authorized to mutate production artifacts.

## Purpose of this section

This section explains how the Developer Manual should align HELP, metadata, CMDHELPCHK, SelfDoc, and manualgen without confusing their roles.

It follows the command-surface section because recent sections repeatedly relied on the same evidence pattern. Manualgen has been reading HELP broadly, reading metadata semantically, validating with CMDHELPCHK, verifying with source, proving with runtime, and assembling manual sections. That is a useful assembly workflow. It is not a replacement for truth authority.

The goal of this section is to prevent drift. Readers should understand which evidence lane explains, which organizes, which validates, which proves, which defines implementation, and which assembles manual output.

## Core doctrine

The manual should use this doctrine consistently:

- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains behavior, vocabulary, command usage, examples, and concepts.
- Metadata organizes identity, ownership, arguments, variants, messages, and alignment.
- CMDHELPCHK validates HELP/catalog consistency and detects drift.
- SelfDoc preserves provenance and report-only evidence.
- Manualgen assembles drafts, reviews, gates, and promoted draft workspaces.

The doctrine matters because each lane is useful but limited. HELP can be excellent explanatory evidence without proving runtime behavior. Metadata can organize a future target even when currently sparse. CMDHELPCHK can catch alignment drift without replacing runtime tests or source review.

## Assembly workflow versus truth authority

Manual assembly can use a HELP/META/CMDHELPCHK-first workflow:

- read HELP broadly;
- read META semantically;
- validate with CMDHELPCHK;
- verify with source;
- prove with runtime;
- assemble with manuals.

That workflow is practical because HELP, metadata, and CMDHELPCHK give manualgen a wide map of the system. But it must not be described as the truth authority doctrine.

Truth authority remains role-separated:

- runtime proves observed behavior;
- source defines implementation and subsystem ownership;
- HELP explains;
- metadata organizes;
- CMDHELPCHK validates.

Safe wording:
- HELP/META/CMDHELPCHK-first is assembly order.
- It is not authority order.
- Source is not demoted to a sidecar outside implementation truth.
- Runtime proof remains required for behavior claims.

## HELP lane

HELP is one of the strongest manual assembly feeders.

Current HELP evidence may include:
- HELP topics;
- HELP GIANT output;
- HELP_LINE rows;
- HELP_ARTIFACTS rows;
- CMDHELP artifacts;
- generated HELP reports;
- usage text;
- warnings;
- examples;
- concept notes.

HELP explains the command surface and conceptual model. It can also expose vocabulary that manualgen should review.

Safe wording:
- HELP explains.
- HELP may reveal intended behavior or documented behavior.
- HELP should not be treated as runtime proof.
- HELP should be crosswalked to source, runtime, metadata, and CMDHELPCHK where claims matter.

## Metadata lane

Metadata organizes the system.

Current and future metadata feeders include:
- SYSCMD
- SYSSUBCMD
- SYSENTVAR
- SYSARGS
- SYSHELP
- SYSMSG
- SYSFUNC
- SOURCE_FACT
- HELP_LINE
- HELP_ARTIFACTS

Metadata may be sparse, partially seeded, or split between older and newer schema forms. Sparse metadata is not a reason to ignore the lane. Sparse metadata should be labeled as a future alignment feeder until seeded and verified.

Safe wording:
- Metadata organizes identity and relationships.
- Metadata does not automatically prove runtime behavior.
- Sparse metadata tables are future feeders, not dead ends.
- Alternate metadata schemas should be crosswalked rather than collapsed casually.

## CMDHELPCHK lane

CMDHELPCHK is a validator and system contract checker.

It can:
- identify missing or inconsistent HELP rows;
- compare command surfaces against HELP/catalog evidence;
- report drift;
- support manual assembly gates;
- validate generated HELP and metadata alignment.

Safe wording:
- CMDHELPCHK validates.
- CMDHELPCHK can identify drift and gaps.
- CMDHELPCHK does not prove runtime execution.
- CMDHELPCHK does not replace source ownership.

## SelfDoc lane

SelfDoc preserves provenance.

SelfDoc evidence includes:
- source-comment contracts;
- harvested source evidence;
- report-only metadata staging;
- provenance reports;
- canary ledgers;
- source/miner evidence;
- manualgen run records;
- savepoint journals.

SelfDoc should keep evidence visible and traceable. It should not silently mutate production HELP, metadata, CMDHELPCHK, catalogs, source, or runtime data during draft assembly.

Safe wording:
- SelfDoc preserves provenance.
- SelfDoc defaults to report-only.
- SelfDoc can identify evidence and drift.
- SelfDoc changes to production artifacts require explicit authorization.

## Manualgen lane

Manualgen assembles.

Manualgen creates:
- draft prose;
- reviewed candidates;
- promoted draft workspaces;
- pippet run records;
- summary reports;
- gate reports;
- savepoint records;
- package bundles.

Manualgen does not publish final manuals by itself. Promoted draft workspaces are still draft workspaces unless final publication is explicitly authorized.

Safe wording:
- Manualgen assembles.
- Manualgen gates and records decisions.
- Manualgen does not mutate HELP, META, CMDHELPCHK, catalogs, source, or runtime data during manual draft assembly.
- Manualgen promoted drafts are not final publication.

## Source lane

Source defines implementation and subsystem ownership.

Source evidence is required when the manual makes claims about:
- implementation ownership;
- parser routing;
- command handlers;
- backend ownership;
- relation traversal semantics;
- expression evaluation ownership;
- memo payload lifecycle;
- message emission;
- runtime behavior that is not proven by a direct test.

Source may be consulted later in the workflow, but later does not mean weaker. In manual assembly order, source may be a verification lane. In truth authority, source remains implementation authority.

Safe wording:
- Source defines implementation.
- Source verifies ownership and routing.
- Source is not merely a provenance sidecar.
- Source claims should be tied to files, comments, contracts, or source-miner evidence.

## Runtime lane

Runtime proves behavior.

Runtime evidence includes:
- observed command runs;
- smoke tests;
- shakedown transcripts;
- exact command output;
- pass/fail test logs;
- canary reproduction;
- before/after behavior.

Runtime evidence is especially important for:
- command execution;
- parser ambiguity;
- error output;
- no-active-table behavior;
- not-found behavior;
- deleted-record behavior;
- relation traversal;
- memo backend attachment;
- index/order behavior.

Safe wording:
- Runtime proves observed behavior.
- Runtime proof should include concrete commands and outputs where possible.
- Runtime proof should be dated or tied to a build/session when possible.
- Runtime proof does not by itself describe implementation ownership without source.

## Temporary evidence lanes

Manualgen may need to use temporary evidence when future metadata feeders are sparse.

Temporary evidence examples:
- generated command pages;
- HELP GIANT exports;
- current HELP rows;
- manually curated canary notes;
- runtime shakedown notes;
- older metadata schema files;
- seed scripts;
- user/MDO handoff notes;
- source-contract reports;
- manualgen pippet reports.

Temporary evidence is allowed when labeled.

Safe wording:
- This source is temporary evidence for the current manual pass.
- Future feeder should be SYSFUNC, SYSMSG, SYSCMD, SYSSUBCMD, SYSENTVAR, SYSARGS, SYSHELP, or related metadata.
- Temporary evidence should be crosswalked to future META feeders when the metadata system matures.
- Temporary evidence must not be promoted as final authority without verification.

## Future META alignment

This section should explicitly preserve future feeder alignment.

Expected future feeders:
- SYSCMD for command identity, handler alignment, visibility, public surface, display reach, owner, source authority, source file, and help topic.
- SYSSUBCMD for subcommand and command-family identity.
- SYSENTVAR for aliases, variants, compatibility spellings, shortcut forms, and entry points.
- SYSARGS for argument shapes, predicates, filters, scopes, validation surfaces, and repeatable flags.
- SYSHELP for curated and generated help text.
- SYSMSG for diagnostics, warnings, statuses, parser messages, and typed message catalog alignment.
- SYSFUNC for function identity, categories, argument ranges, handler links, CALC/CALCWRITE reach, public surface, self-registration, and function-command bridge surfaces.
- HELP_LINE and HELP_ARTIFACTS for current HELP evidence lanes.
- SOURCE_FACT and source-contract evidence for source/comment provenance.
- manualgen reports and PIP records for assembly provenance and gate evidence.

Sparse feeders should be kept visible. The manual should not ignore SYSFUNC, SYSMSG, SYSCMD, SYSSUBCMD, SYSENTVAR, SYSARGS, or SYSHELP because they are empty or only partially seeded today.

## Crosswalk discipline

Crosswalks prevent drift.

Useful crosswalks include:
- HELP topic to command identity;
- command identity to SYSCMD;
- subcommand to SYSSUBCMD;
- alias or entry variant to SYSENTVAR;
- argument shape to SYSARGS;
- help text to SYSHELP;
- diagnostic text to SYSMSG;
- function reference to SYSFUNC;
- source comment to SOURCE_FACT;
- generated command page to canonical command and variant review;
- manualgen section to evidence tokens and pippet reports.

Crosswalks should preserve uncertainty. A crosswalk can say "candidate match" or "future feeder" without claiming final authority.

## Safety boundaries

This alignment section should restate the safety boundaries.

Default manualgen/SelfDoc boundary:
- no generated command page deletion;
- no HELP mutation;
- no META mutation;
- no CMDHELPCHK mutation;
- no catalog apply;
- no source edits;
- no production SelfDoc metadata promotion;
- no final publication without explicit authorization.

Report-only work is the default.

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- help meta cmdhelpchk first is assembly workflow not truth authority
- runtime source help metadata cmdhelpchk truth authority roles
- help explains not runtime proof
- metadata sparse feeders not dead ends
- cmdhelpchk validates not runtime source proof
- sysfunc sysmsg syscmd syssubcmd sysentvar sysargs syshelp sparse feeder alignment
- selfdoc provenance report-only boundaries
- manualgen assembles no mutation
- temporary evidence lanes labeled crosswalked
- source remains implementation authority

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- HELP/META/CMDHELPCHK-first is framed as assembly workflow, not truth authority;
- runtime/source/HELP/metadata/CMDHELPCHK authority roles are preserved;
- HELP is not treated as runtime proof;
- metadata sparse feeders remain visible;
- CMDHELPCHK is not treated as runtime/source proof;
- SYSFUNC, SYSMSG, SYSCMD, SYSSUBCMD, SYSENTVAR, SYSARGS, and SYSHELP are included as future/current feeders;
- SelfDoc report-only provenance boundaries are visible;
- manualgen no-mutation boundary is visible;
- temporary evidence lanes are labeled and crosswalked;
- source remains implementation authority.

Recommended required tokens for later PIP-003:
- HELP
- HELP GIANT
- HELP_LINE
- HELP_ARTIFACTS
- CMDHELP
- CMDHELPCHK
- META
- metadata
- SYSCMD
- SYSSUBCMD
- SYSENTVAR
- SYSARGS
- SYSHELP
- SYSMSG
- SYSFUNC
- SOURCE
- SOURCE_FACT
- SelfDoc
- manualgen
- PIP
- validator
- crosswalk
- report-only
- truth authority
- assembly workflow

## Boundary

- prose draft fill only
- slow-lane review still required
- no reviewed candidate generated
- no final prose promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion

