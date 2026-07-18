# Messages, Errors, and Diagnostics




Pippets used:
- PIP-001 Target Selection
- MDO-159 Target Selection
- MDO-160 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches message-catalog, HELP, metadata, validation, and runtime-reporting boundaries.
- Do not send this directly to generic PIP-003.
- Run a slow-lane message/diagnostic review first.

Evidence tokens under review:
- SYSMSG
- SYSTEM_MESSAGES
- MSG_ID
- SYMBOL
- ENUM_NAME
- SEVERITY
- FACILITY
- SHORT_TXT
- SUG_ACT
- HELP
- HELP GIANT
- CMDHELPCHK
- WARNING
- ERROR
- STATUS
- SHARED_MSG
- diagnostic
- message catalog
- typed message
- parser warning
- nonnumeric aggregate
- no active table
- not found

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Generated command draft pages remain draft evidence, not final command prose.
- SYSMSG is preserved as a future typed message feeder even if current metadata seeding is sparse.
- SYSTEM_MESSAGES may represent an older or alternate long-form metadata schema and must be crosswalked carefully.
- HELP explains and CMDHELPCHK validates; neither should be treated as runtime proof.
- Message catalog doctrine must not mutate HELP, META, CMDHELPCHK, catalogs, source, or runtime data during manual draft assembly.

## Purpose of this section

This section explains how DotTalk++ developer documentation should treat messages, errors, warnings, statuses, diagnostics, and future typed message catalog work.

It follows the expression and aggregate section because that section introduced several diagnostic-heavy cases: nonnumeric aggregate values, parser ambiguity, empty or deleted-only aggregate inputs, no-active-table conditions, not-found outcomes, and expression/function argument errors. Those cases need a shared diagnostic vocabulary before the manual expands deeper into command families and subsystem behavior.

The goal is not to claim that the full typed messaging system is already complete. The goal is to preserve the intended direction while keeping current proof boundaries visible.

## Evidence lanes

This draft uses several evidence lanes.

Current HELP evidence lane:
- HELP
- HELP GIANT
- HELP_LINE
- HELP_ARTIFACTS
- WARNING rows
- ERROR rows
- STATUS rows
- SHARED_MSG rows

Current metadata evidence lane:
- SYSMSG
- SYSTEM_MESSAGES
- SYSHELP
- SYSCMD
- SYSSUBCMD
- SYSFUNC
- SYSARGS
- SYSENTVAR

Diagnostic concept lane:
- message
- diagnostic
- warning
- error
- status
- trace
- log
- test output
- parser warning
- message catalog
- typed message

Runtime/source proof lane:
- parser warnings require runtime/source evidence;
- expression errors require runtime/source evidence;
- aggregate errors require runtime/source evidence;
- no-active-table messages require runtime/source evidence;
- not-found messages require runtime/source evidence.

Future catalog lane:
- the messaging layer should become the single typed, catalog-backed reporting path;
- current coverage must be verified before final manual claims;
- sparse metadata seeding is a future feeder, not a reason to ignore the lane.

## Authority boundaries

The same doctrine applies here:

- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains behavior and command surface intent.
- Metadata organizes identity, ownership, argument shapes, help text, and message catalog alignment.
- CMDHELPCHK validates HELP/catalog consistency.
- SelfDoc preserves provenance.
- Manualgen assembles.

This section must be careful because HELP and diagnostics are tempting to treat as proof. HELP output can explain intended or cataloged behavior, but it does not by itself prove runtime execution. CMDHELPCHK can validate consistency, but it does not by itself prove runtime behavior either.

## Message vocabulary

The manual should not collapse every output line into the same kind of message.

Useful distinctions:
- A message is a reported unit of text or structured information.
- A diagnostic explains a condition that may require interpretation or action.
- A warning reports a risk or questionable condition.
- An error reports a failed operation or invalid condition.
- A status reports state or completion information.
- A trace reports internal execution evidence.
- A log records events for later inspection.
- A test result reports expected versus observed behavior.
- HELP text explains usage, concepts, warnings, examples, and reference material.
- A catalog row organizes message identity and metadata.

These categories may overlap in implementation, but the manual should not collapse them until source and metadata evidence prove the ownership model.

## Typed message catalog direction

The project direction is that the messaging layer should become the single typed, catalog-backed reporting path for:
- commands;
- errors;
- help text;
- syntax issues;
- warnings;
- traces;
- UI/status messages;
- logs;
- tests;
- HELP validation;
- upper-layer metadata reporting and collection.

This is directionally important, but not automatically complete. The manual should say:
- intended direction: typed, catalog-backed reporting;
- current proof: must be verified by source, runtime, HELP, and metadata evidence;
- draft boundary: no HELP/META/CMDHELPCHK/catalog/source/runtime mutation during manual assembly.

## SYSMSG and SYSTEM_MESSAGES

SYSMSG is the compact/current metadata feeder identified for message catalog work. Its fields include message identity and message metadata such as:
- MSG_ID
- SYMBOL
- ENUM_NAME
- SEVERITY
- FACILITY
- SHORT_TXT
- IMPL_STAT
- VIS_TIER
- OWNER
- SRC_AUTH
- SRC_FILE
- PUB_SURF
- USED_RUN
- ACTIVE
- VER_AT
- SUG_ACT
- NOTES

SYSTEM_MESSAGES appears in earlier or alternate metadata material as a long-form schema name. It should not be assumed identical to SYSMSG without a crosswalk.

Safe wording:
- SYSMSG is the current compact future feeder for message metadata where seeded and verified.
- SYSTEM_MESSAGES may be legacy or alternate long-form metadata evidence.
- The manual should crosswalk them carefully before treating them as one authority.

## HELP rows as diagnostic evidence

HELP GIANT and HELP tables provide useful evidence for diagnostic text and categories.

Evidence examples:
- WARNING rows;
- ERROR rows;
- STATUS rows;
- SHARED_MSG rows;
- SOURCE_FACT rows;
- HELP_LINE records;
- HELP_ARTIFACTS records.

But HELP rows are explanation/catalog evidence, not runtime proof. A WARNING row in HELP means the help system has a warning artifact; it does not prove the runtime command currently emits that warning.

## SHARED_MSG caution

SHARED_MSG rows are useful because they suggest text or messages shared across HELP or command surfaces.

Safe wording:
- SHARED_MSG rows are evidence.
- They may be sparse.
- They should not be treated as complete message catalog coverage.
- They should be crosswalked to SYSMSG/SYSTEM_MESSAGES and source/runtime evidence before final implementation claims.

## CMDHELPCHK role

CMDHELPCHK validates HELP/catalog consistency. It is a validator and system contract checker, not just documentation.

Safe wording:
- CMDHELPCHK can identify gaps, inconsistencies, or contract drift.
- CMDHELPCHK supports manual assembly by checking HELP/catalog alignment.
- CMDHELPCHK does not replace runtime proof.
- CMDHELPCHK does not replace source ownership.

This matters because manual assembly can use HELP/META/CMDHELPCHK-first workflow, but truth authority remains runtime/source/HELP/metadata/CMDHELPCHK according to their roles.

## Runtime diagnostic examples

Expressions and aggregates introduced diagnostic examples that should eventually map into message evidence:
- nonnumeric aggregate expression;
- character expression used with AVG;
- empty or deleted-only aggregate input;
- invalid field or expression;
- parser ambiguity between command and function form;
- no active table;
- not found;
- unsupported command syntax;
- missing argument;
- invalid argument count.

This draft does not claim all of those are cataloged today. It says they are natural future candidates for SYSMSG and source/runtime review.

## Severity vocabulary

Severity vocabulary must not be invented.

Possible severity words include:
- ERROR
- WARNING
- STATUS
- INFO
- TRACE
- DEBUG

But final wording should only claim severity categories when evidence supports them through SYSMSG, HELP, source, or runtime behavior. The draft should avoid inventing a complete severity taxonomy.

## Parser warnings and syntax diagnostics

Parser warnings and syntax diagnostics are important because command-line behavior can bridge commands and functions. Examples include:
- command/function ambiguity;
- unknown command;
- missing argument;
- unsupported syntax;
- scalar function form versus aggregate command form.

The expressions section preserved MIN/MAX parser ambiguity. This diagnostics section should explain that such cases need typed messages or at least consistent diagnostic reporting, but it should not claim the final routing is complete without source/runtime proof.

## No-active-table and not-found messages

No-active-table and not-found messages are common diagnostic candidates.

They should be handled conservatively:
- no-active-table behavior depends on command context;
- not-found behavior depends on search command, index/order context, and runtime state;
- exact wording and severity need runtime/source evidence;
- future SYSMSG rows should eventually organize the message identities.

## Message catalog and HELP alignment

Message catalog work should eventually align:
- SYSMSG message identity;
- HELP text;
- command/function ownership;
- argument validation;
- runtime emission;
- CMDHELPCHK validation;
- SelfDoc provenance.

This section should preserve that alignment goal but avoid claiming it is finished.

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- typed catalog-backed reporting path coverage
- HELP CMDHELPCHK not runtime proof
- SYSMSG SYSTEM_MESSAGES schema variation
- SHARED_MSG sparse evidence
- parser expression aggregate no-active-table not-found runtime evidence
- diagnostics warnings errors statuses traces logs tests help catalog distinction
- SYSMSG future feeder sparse seed
- no mutation during manual message catalog draft assembly
- severity vocabulary not invented
- typed-message ownership future catalog alignment

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Future META alignment

This section should eventually align with the metadata system.

Expected future feeders:
- SYSMSG for message identity, symbol, enum name, severity, facility, short text, implementation status, visibility tier, owner, source authority, source file, public surface flag, used-at-runtime flag, suggested action, notes, and active status.
- SYSTEM_MESSAGES for legacy or alternate long-form message schema evidence that must be crosswalked carefully.
- SYSHELP for help text connected to message owners, diagnostic concepts, generated text, and curated text.
- SYSCMD for command owners that emit diagnostics.
- SYSSUBCMD for subcommand diagnostic surfaces when command families own messages.
- SYSFUNC for function-related diagnostics such as argument count, nonnumeric value, parser ambiguity, and calculation errors.
- SYSARGS for arguments involved in diagnostic validation and error reporting.
- SYSENTVAR for aliases or variants that may affect diagnostic routing.
- HELP_LINE and HELP_ARTIFACTS as current HELP evidence lanes for WARNING, ERROR, STATUS, SHARED_MSG, and related text.

Temporary evidence is acceptable only when marked as temporary and crosswalked to future META feeders.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- generated command pages are treated as draft evidence;
- HELP explains and CMDHELPCHK validates, but neither is presented as runtime proof;
- SYSMSG and SYSTEM_MESSAGES are not collapsed casually;
- SHARED_MSG is treated as sparse evidence;
- diagnostic categories are separated;
- severity vocabulary is not invented;
- parser warnings and expression/aggregate diagnostics are runtime/source gated;
- SYSMSG remains a future feeder even if sparse;
- no manual draft work mutates HELP, META, CMDHELPCHK, catalogs, source, or runtime data.

Recommended required tokens for later PIP-003:
- SYSMSG
- SYSTEM_MESSAGES
- MSG_ID
- SYMBOL
- ENUM_NAME
- SEVERITY
- FACILITY
- SHORT_TXT
- SUG_ACT
- HELP
- HELP GIANT
- CMDHELPCHK
- WARNING
- ERROR
- STATUS
- SHARED_MSG
- diagnostic
- message catalog
- typed message
- parser warning
- nonnumeric aggregate
- no active table
- not found

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

