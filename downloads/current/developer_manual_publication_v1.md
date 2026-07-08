# DotTalk++ / x64base Developer Manual

Publication artifact: MDO-214 final publication package from the 24-section normalized public body.

Source public-copy workspace: `docs\manuals\developer\manualgen\generated\developer_manual_normalized_public_copy_v1`

Boundary: this publication artifact does not mutate HELP, META, CMDHELPCHK, catalogs, source, runtime data, or production SelfDoc metadata.

---

<!-- BEGIN SECTION: sections\command_reference_assembly_aliases_and_generated_page_hygiene.md -->

# Command Reference Assembly, Aliases, and Generated Page Hygiene




Pippets used:
- PIP-001 Target Selection
- MDO-188 Target Selection
- MDO-189 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches generated command pages, duplicate command rows, aliases, entry variants, canonical command identity, slug collisions, LOAD guard behavior, SET-family canonicalization, AGGS exposure, and command-reference publication readiness.
- Do not send this directly to generic PIP-003.
- Run a slow-lane command-reference hygiene review first.

Evidence tokens under review:
- command reference
- generated command pages
- HELP_COMMANDS
- HELP
- HELP GIANT
- CMDHELP
- CMDHELPCHK
- SYSCMD
- SYSSUBCMD
- SYSENTVAR
- SYSARGS
- SYSHELP
- alias
- variant
- canonical command
- slug collision
- duplicate command
- APPEND BLANK
- APPEND_BLANK
- LOAD guard
- SET-family
- AGGS
- internal owner
- public surface
- manualgen
- PIP
- crosswalk
- report-only
- no mutation

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Generated command pages are draft evidence, not final command reference prose.
- Duplicate command rows and slug collisions must be reviewed before publication.
- Aliases and entry variants must not be treated as canonical commands without review.
- APPEND BLANK and APPEND_BLANK may map to the same slug but may represent variant or canonicalization evidence.
- LOAD guard must preserve no top-level LOAD page while preserving scoped CODASYL LOAD and WORKSPACE LOAD.
- SET-family canonicalization remains deferred unless separately repaired or accepted.
- AGGS remains internal or family-owner evidence unless explicitly accepted as public command surface.
- HELP, CMDHELPCHK, and metadata can guide command reference review but cannot settle runtime or source canaries alone.
- Command reference hygiene packages must not delete generated command pages during manual draft assembly.

## Purpose of this section

This section explains how the Developer Manual should treat generated command pages, command-reference assembly, aliases, variants, canonical commands, and generated-page hygiene.

It follows the Command Surface, HELP/Metadata/CMDHELPCHK Alignment, and Runtime Evidence sections because those sections established the boundaries needed here. Command reference work needs all three: a model of command surface and entry variants, an alignment model for HELP and metadata, and an evidence model for runtime/source/canary closure.

The goal is not to publish the final command reference in this section. The goal is to define safe rules for assembling the future command reference from generated pages and other evidence without losing alias/variant information, publishing internal scaffolding, or deleting generated evidence prematurely.

## Authority model for command reference assembly

The same doctrine applies:

- Runtime proves command behavior.
- Source defines implementation and command ownership.
- HELP explains usage and concepts.
- Metadata organizes command identity, arguments, variants, and help alignment.
- CMDHELPCHK validates HELP/catalog consistency.
- SelfDoc preserves provenance.
- Manualgen assembles drafts, reviews, and promoted workspaces.

Generated command pages are an evidence lane. They are not the authority by themselves.

Safe wording:
- Generated pages feed review.
- Generated pages do not replace review.
- Generated pages may expose duplicates, aliases, scaffolding, or internal owners.
- Final command-reference prose needs dedupe, alias/variant review, HELP/metadata alignment, and runtime/source checks where behavior or ownership is claimed.

## Generated command pages

Generated command pages are useful because they preserve broad command-surface evidence.

They may show:
- command names;
- aliases;
- variants;
- generated slugs;
- usage text;
- HELP extraction;
- metadata alignment candidates;
- duplicate rows;
- command-family scaffolding;
- internal owner entries.

But generated pages can also expose draft artifacts.

Safe wording:
- Generated command pages are draft evidence.
- They are not final command reference prose.
- They should be reviewed, deduped, and crosswalked before publication.
- They should not be deleted or rewritten during ordinary manual draft assembly.

## Duplicate command rows

Duplicate command rows can mean different things.

A duplicate may be:
- a true duplicate that should be collapsed later;
- an alias;
- an entry variant;
- a compatibility spelling;
- a scoped subcommand;
- a generated slug collision;
- an internal owner or command-family scaffold;
- a public command that shares a root token with another command.

Safe wording:
- Duplicate rows are review input.
- Duplicate rows should not be collapsed automatically.
- A duplicate row is not proof that one page is wrong.
- Dedupe should preserve evidence until canonical command, alias, variant, and scope are reviewed.

## Aliases and variants

Aliases and variants are not automatically canonical commands.

An alias may be a shortcut spelling. A variant may be a compatibility form, app-style entry point, scoped command form, or user-facing convenience form. The command reference should preserve those distinctions until metadata and evidence review decide how they should be presented.

Safe wording:
- Aliases and variants must not be treated as canonical commands without review.
- SYSENTVAR should eventually organize aliases, variants, shortcut spellings, compatibility forms, generated page entries, and app-style entry points.
- Generated command pages may represent aliases or variants rather than separate canonical commands.
- Manual prose should avoid treating every distinct token as a separate command until dedupe and variant review are complete.

## Canonical command identity

Canonical command identity is the reviewed identity used for final reference organization.

A canonical command should eventually align with:
- SYSCMD command identity;
- handler or source ownership where relevant;
- public surface status;
- help topic;
- argument model;
- aliases and variants;
- generated page crosswalk;
- runtime/source evidence where behavior or ownership is claimed.

Safe wording:
- Canonical command identity should be reviewed.
- Canonical command identity should not be inferred from slug text alone.
- Canonical command identity should not erase useful alias or variant evidence.
- Metadata can organize identity, but runtime/source evidence may still be required for behavior and ownership claims.

## Slug collisions

A slug collision occurs when two different generated entries map to the same or confusing page slug.

Slug collisions may happen because:
- spaces and underscores collapse;
- punctuation is normalized;
- aliases share words;
- variants differ only by formatting;
- scoped command names are flattened;
- generator rules remove important distinctions.

Safe wording:
- Slug collisions are review items.
- Slug collisions should not be resolved by deleting generated pages during manual draft assembly.
- Slug collision repair should preserve source evidence, generated evidence, and future metadata crosswalks.
- A later command-reference hygiene pass may choose canonical slugs after review.

## APPEND BLANK and APPEND_BLANK

APPEND BLANK and APPEND_BLANK are useful review examples.

They may map to the same slug or appear related in generated evidence, but the manual should not force a final answer here. They may represent:
- a command plus argument form;
- a compatibility form;
- a generated normalization issue;
- an alias or variant;
- a canonicalization candidate.

Safe wording:
- APPEND BLANK and APPEND_BLANK should remain variant/canonicalization review examples.
- Do not treat one as wrong solely because of slug shape.
- Do not publish a final command-reference rule until evidence review decides canonical command, variant, and argument treatment.

## LOAD guard

LOAD is a known generated-page guard canary.

The guard should preserve:
- no top-level LOAD page where that surface is intentionally suppressed;
- scoped CODASYL LOAD where supported;
- WORKSPACE LOAD where supported;
- evidence rows that explain why top-level LOAD is guarded.

Safe wording:
- LOAD guard must preserve no top-level LOAD page while preserving scoped CODASYL LOAD and WORKSPACE LOAD.
- LOAD guard is not permission to delete all LOAD-related evidence.
- Scoped LOAD forms should remain visible for review if they are evidenced.
- A guard is a publication boundary, not an evidence deletion rule.

## SET-family canonicalization

SET-family canonicalization remains deferred.

SET-family entries may include:
- SET ORDER;
- SET INDEX;
- other SET-scoped command surfaces;
- compatibility forms;
- generated pages that flatten or split command/subcommand identities.

Safe wording:
- SET-family canonicalization remains deferred unless separately repaired or accepted.
- SET-family generated pages should be treated as draft evidence.
- Indexing owns order/tag semantics; command-reference hygiene owns command identity and reference organization.
- Final reference organization should not be settled by prose alone.

## AGGS boundary

AGGS is a known command-reference canary.

Current doctrine:
- AGGS is intended as an internal owner or aggregate-family grouping.
- Direct aggregate verbs such as SUM, AVG, MIN, and MAX are the intended user-facing aggregate command surface where evidenced.
- AGGS appearing in generated command pages may indicate internal owner exposure, scaffold leakage, or family grouping evidence.
- AGGS should not be published as a public command surface unless explicitly accepted.

Safe wording:
- AGGS remains internal or family-owner evidence unless explicitly accepted as public command surface.
- Generated AGGS evidence should be retained for review.
- Generated AGGS evidence should not become final public command-reference prose by default.

## Internal owner and public surface

Command-reference assembly must separate internal owner evidence from public command surface.

An internal owner may be:
- a command-family grouping;
- handler scaffolding;
- parser dispatch label;
- generated metadata row;
- development/debug surface;
- owner used for help organization.

A public surface is what users are intended to invoke.

Safe wording:
- Internal owner evidence is useful.
- Internal owner evidence is not automatically public command surface.
- Public surface requires intent and evidence.
- PUB_SURF, VIS, DISP_REACH, HELP, runtime behavior, and source ownership may all participate in review.

## HELP and CMDHELPCHK

HELP and CMDHELPCHK are important command-reference inputs.

HELP can explain:
- usage;
- concepts;
- examples;
- warnings;
- aliases;
- command families.

CMDHELPCHK can validate:
- HELP/catalog consistency;
- missing topics;
- generated HELP drift;
- command catalog alignment.

Safe wording:
- HELP explains command reference intent.
- CMDHELPCHK validates command-reference alignment.
- Neither HELP nor CMDHELPCHK replaces runtime proof or source ownership.
- HELP and CMDHELPCHK can guide command-reference hygiene.

## Metadata feeders

Future and current metadata feeders should remain visible.

Expected feeders:
- SYSCMD for canonical command identity, canonical name, handler, visibility, public surface, display reach, owner, source authority, and help topic.
- SYSSUBCMD for scoped subcommand identity such as SET ORDER, SET INDEX, scoped LOAD forms, and command-family subcommands.
- SYSENTVAR for aliases, variants, shortcut spellings, compatibility forms, generated page entries, and app-style entry points.
- SYSARGS for command argument shapes, scopes, deleted filters, predicates, tag names, workspace files, and rebuild options.
- SYSHELP for curated and generated command help text.
- SYSMSG for parser, syntax, unknown command, invalid argument, and ambiguity diagnostics.
- SYSFUNC for function-command bridge cases where scalar functions overlap command-like syntax.

Sparse feeders are still alignment lanes. They should not be ignored because they are incomplete.

## Command-reference crosswalks

Crosswalks should connect generated pages to reviewed command identity without collapsing evidence.

Useful crosswalks include:
- generated page to SYSCMD canonical command;
- generated page to SYSENTVAR alias or variant;
- generated page to SYSSUBCMD scoped subcommand;
- generated usage to SYSARGS argument model;
- HELP topic to SYSHELP;
- command diagnostic to SYSMSG;
- function-command bridge entry to SYSFUNC;
- generated slug to reviewed final slug;
- command-family owner to public command entries.

Safe wording:
- Crosswalks may be candidate, partial, or verified.
- Crosswalks should preserve uncertainty.
- Crosswalks should not delete evidence.
- Crosswalks help future metadata absorb temporary generated-page evidence.

## Publication readiness

A generated command page is not publication-ready by default.

Before a command page becomes final reference prose, review should check:
- canonical command identity;
- alias and variant treatment;
- duplicate row handling;
- slug selection;
- HELP alignment;
- argument model;
- public surface status;
- internal owner exposure;
- runtime behavior where behavior is claimed;
- source ownership where ownership is claimed;
- metadata crosswalk;
- CMDHELPCHK consistency;
- no unresolved canaries.

Safe wording:
- Command-reference publication is a later gate.
- Draft generated pages are review material.
- This section does not publish the final reference.
- Publication should be guarded by evidence, crosswalks, and human acceptance.

## No-delete and no-mutation safety

Command-reference hygiene must preserve generated evidence during manual draft assembly.

Default boundary:
- no generated command page deletion;
- no HELP mutation;
- no META mutation;
- no CMDHELPCHK mutation;
- no catalog apply;
- no source edits;
- no runtime data mutation;
- no production SelfDoc metadata promotion;
- no final publication.

Safe wording:
- Review can flag generated pages.
- Review can recommend later repair.
- Review must not delete generated pages during manual draft assembly.
- Production mutation requires explicit authorization.

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


<!-- END SECTION: sections\command_reference_assembly_aliases_and_generated_page_hygiene.md -->

---

<!-- BEGIN SECTION: sections\command_surface_dispatch_and_entry_variants.md -->

# Command Surface, Dispatch, and Entry Variants




Pippets used:
- PIP-001 Target Selection
- MDO-166 Target Selection
- MDO-167 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches parser dispatch, public command surface, internal command-family ownership, aliases, variants, subcommands, function bridge behavior, and generated command-reference canaries.
- Do not send this directly to generic PIP-003.
- Run a slow-lane command-surface review first.

Evidence tokens under review:
- COMMANDS
- SYSCMD
- SYSSUBCMD
- SYSENTVAR
- CMDKEY
- CAN_NAME
- QUAL_NAME
- TOKEN
- HANDLER
- VIS
- PUB_SURF
- DISP_REACH
- HELP
- CMDHELPCHK
- parser
- dispatch
- handler
- command surface
- entry variant
- alias
- subcommand
- canonical command
- AGGS
- SET family
- FUNCTION bridge

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Generated command draft pages remain draft evidence, not final command reference prose.
- Public command surface must be separated from internal owner/family scaffolding.
- AGGS is treated as internal/family-owner evidence unless explicitly accepted as a public command surface.
- SET-family canonicalization remains deferred unless separately repaired or accepted.
- Function bridge behavior must preserve scalar/function entry while respecting command ownership.
- SYSCMD, SYSSUBCMD, SYSENTVAR, SYSARGS, SYSHELP, SYSMSG, and SYSFUNC remain future/current feeders even when sparse.

## Purpose of this section

This section explains how the Developer Manual should talk about command surface, parser dispatch, command handlers, canonical command identity, aliases, entry variants, subcommands, and function-bridge entry.

It follows Navigation, Indexing, Expressions, and Messages because those sections repeatedly depended on command/function routing and ownership boundaries. The manual now needs a section that explains how commands should be described without collapsing public command surface, internal command-family owners, generated command evidence, parser dispatch, and future metadata feeders into one authority.

The goal is not to publish the final command reference. The goal is to preserve a safe model for developer prose: command surface is what the user can intentionally invoke; dispatch is how input reaches implementation; metadata organizes identity and variants; HELP explains; CMDHELPCHK validates; runtime/source evidence still decides behavior and ownership.

## Evidence lanes

This draft uses several evidence lanes.

Current command evidence lane:
- COMMANDS
- generated command pages
- HELP command topics
- CMDHELPCHK reports
- HELP_COMMANDS exports where available

Current metadata evidence lane:
- SYSCMD
- SYSSUBCMD
- SYSENTVAR
- SYSARGS
- SYSHELP
- SYSMSG
- SYSFUNC

Dispatch concept lane:
- parser
- dispatch
- handler
- command surface
- public command
- internal family owner
- entry variant
- alias
- subcommand
- canonical command
- function bridge

Canary lane:
- AGGS internal owner exposure;
- SET family canonicalization;
- command/function bridge behavior;
- generated command duplicate and slug-collision evidence;
- sparse metadata feeder coverage;
- aliases and variants that should not be collapsed into canonical commands without review.

## Authority boundaries

The same doctrine applies here:

- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains command surface and intended usage.
- Metadata organizes canonical identity, variants, arguments, handlers, visibility, and help alignment.
- CMDHELPCHK validates HELP/catalog consistency.
- SelfDoc preserves provenance.
- Manualgen assembles.

The command-surface section must not let generated command pages or metadata rows become stronger proof than they are. A generated command page is draft evidence. A metadata row organizes identity. A HELP row explains. A handler in source defines implementation. A runtime test proves observed behavior.

## Command surface

Command surface means the command vocabulary that a user can intentionally invoke.

Safe wording:
- A public command surface should be documented as public only when HELP, metadata, source, and/or runtime evidence support that status.
- A word that appears in generated command pages is not automatically a final public command.
- A word that appears as an internal owner or command family should not be promoted as user-facing without explicit acceptance.
- Visibility and public-surface flags should eventually be checked against metadata such as VIS and PUB_SURF.

This matters for command families, scaffolding, debug commands, and internal owner commands.

## Canonical commands

A canonical command is the main command identity used for documentation, metadata, and command-reference organization.

Safe wording:
- A canonical command may have aliases or entry variants.
- A canonical command may own subcommands.
- A generated page slug is not automatically the canonical identity.
- A handler name is implementation evidence, not necessarily the public name.
- CMDKEY, CAN_NAME, and QUAL_NAME should eventually help separate command identity levels.

The manual should preserve a difference between:
- token typed by a user;
- canonical command identity;
- qualified command/subcommand identity;
- generated page path;
- source handler;
- metadata row;
- HELP topic.

## Subcommands and command families

Some command surfaces are naturally scoped through families or subcommands.

Examples needing careful treatment:
- SET family
- SET ORDER
- SET INDEX
- REL variants
- WORKSPACE LOAD
- CODASYL LOAD
- aggregate-family ownership
- AGGS as a possible internal owner

Safe wording:
- A family or owner command may organize related verbs or subcommands.
- A subcommand should be documented under its scoped owner when evidence supports that structure.
- A family name should not be treated as public executable command unless accepted and evidenced.
- SET-family canonicalization remains deferred until repaired or explicitly accepted.

## Aliases and entry variants

Aliases and entry variants are not automatically separate canonical commands.

Safe wording:
- An alias may route to a canonical command.
- An entry variant may preserve compatibility vocabulary, shortcut spelling, or a user-facing convenience form.
- A generated command page may represent an alias or variant rather than a canonical command.
- SYSENTVAR should eventually organize aliases, variants, shortcut spellings, compatibility forms, and app-style entry points.

Manual prose should avoid treating every distinct token as a separate command until dedupe and variant review are complete.

## Parser dispatch and handlers

Parser dispatch is the route from user input to implementation. A handler is the implementation endpoint or command function that receives the routed input.

Safe wording:
- Parser dispatch and handler ownership require source evidence.
- Runtime evidence proves observed routing behavior.
- HELP and metadata can explain or organize dispatch but do not prove runtime routing.
- Handler names may be internal and should not be exposed as public command names unless explicitly intended.

This section should avoid claiming the exact parser algorithm unless source/runtime evidence is attached.

## Function bridge behavior

DotTalk++ allows some function/app forms to be used directly from the command line. Prior runtime notes include examples such as UPPER and LEFT.

This is a command-surface canary because function names can look like command verbs.

Safe wording:
- FUNCTION bridge behavior should preserve scalar/function entry where supported.
- A function-style command-line entry does not necessarily make the function a command.
- A command verb may shadow a scalar function name.
- MIN/MAX ambiguity remains a separate canary from the expression section.
- SYSFUNC and SYSENTVAR should eventually help organize function-command bridge forms.

## AGGS boundary

AGGS is a known command-surface canary.

Current doctrine:
- AGGS is intended as an internal owner or aggregate-family grouping.
- Direct aggregate verbs such as SUM, AVG, MIN, and MAX are the intended user-facing aggregate command surface where evidenced.
- AGGS appearing as executable or printing usage may be scaffold/debug leakage unless explicitly accepted.
- Generated command pages for AGGS are draft evidence, not final public-surface proof.

This section should preserve AGGS internal family owner exposure as a visible canary.

## SET family boundary

SET-family canonicalization remains deferred.

Safe wording:
- SET ORDER and SET INDEX are scoped command surfaces that need canonicalization review.
- SET-family pages may exist as generated draft evidence.
- Final command reference organization should not be settled in this section without dedicated SET-family review.
- Indexing owns order/tag semantics; this section owns command-surface identity and dispatch cautions.

## Generated command pages

Generated command pages are useful evidence, but they are not final command reference.

Known generated-page issues:
- duplicates;
- aliases;
- variants;
- slug collisions;
- SET-family canonicalization;
- internal owner exposure;
- command/function ambiguity.

Safe wording:
- Generated pages identify draft evidence.
- They should be deduped and reviewed before publication.
- Command reference generation must not delete or rewrite generated command pages during manual draft assembly.
- Generated pages should feed review, not replace review.

## HELP and CMDHELPCHK

HELP explains command usage, concepts, and warnings. CMDHELPCHK validates HELP/catalog consistency.

Safe wording:
- HELP can explain command surface intent.
- CMDHELPCHK can detect gaps and drift.
- Neither HELP nor CMDHELPCHK replaces runtime proof.
- Neither HELP nor CMDHELPCHK replaces source ownership.

Manual assembly may use HELP/META/CMDHELPCHK-first workflow, but truth authority remains role-separated.

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


<!-- END SECTION: sections\command_surface_dispatch_and_entry_variants.md -->

---

<!-- BEGIN SECTION: sections\documentation_modeling_and_project_notes.md -->

# Documentation, Modeling, and Project Notes

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [COMMANDSHELP](../../command_reference_v1/commands/commandshelp.md)
- [DECISION](../../command_reference_v1/commands/decision.md)
- [DRAWIO](../../command_reference_v1/commands/drawio.md)
- [EXAMPLE](../../command_reference_v1/commands/example.md)
- [GLOSSARY](../../command_reference_v1/commands/glossary.md)
- [GPS](../../command_reference_v1/commands/gps.md)
- [IMAGE](../../command_reference_v1/commands/image.md)
- [INTRO](../../command_reference_v1/commands/intro.md)
- [MODEL](../../command_reference_v1/commands/model.md)
- [PROJECTS](../../command_reference_v1/commands/projects.md)
- [RULE](../../command_reference_v1/commands/rule.md)
- [SECURITY](../../command_reference_v1/commands/security.md)
- [TEXT](../../command_reference_v1/commands/text.md)
- [WSREPORT](../../command_reference_v1/commands/wsreport.md)
<!-- BEGIN SECTION: sections\educational_and_demo_commands.md -->

# Educational and Demo Commands

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [AREA51](../../command_reference_v1/commands/area51.md)
- [BIBLETALK](../../command_reference_v1/commands/bibletalk.md)
- [CANARY](../../command_reference_v1/commands/canary.md)
- [CHRISTMAS](../../command_reference_v1/commands/christmas.md)
- [CODASYL](../../command_reference_v1/commands/codasyl.md)
- [EDUCATIONAL_USE](../../command_reference_v1/commands/educational_use.md)
- [MCC](../../command_reference_v1/commands/mcc.md)
- [STUDENTECHO](../../command_reference_v1/commands/studentecho.md)
- [STUDENTHELLO](../../command_reference_v1/commands/studenthello.md)
<!-- BEGIN SECTION: sections\expressions_querying_and_aggregates.md -->

# Expressions, Querying, and Aggregates




Pippets used:
- PIP-001 Target Selection
- MDO-151 Target Selection
- MDO-152 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches known command/function and parser canaries.
- Do not send this directly to generic PIP-003.
- Run a slow-lane expression/function/aggregate review first.

Evidence tokens under review:
- CALC
- CALCWRITE
- WHERE
- FOR
- LOCATE
- CONTINUE
- SCAN
- COUNT
- SUM
- AVG
- MIN
- MAX
- AGGS
- FUNCTION
- FUNCTIONS
- PREDICATES
- MIN()
- MAX()
- xexpr
- DELETED
- NOT DELETED
- !DELETED

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Generated command draft pages remain draft evidence, not final command prose.
- xexpr owns expression evaluation surfaces unless current source proves a narrower owner for a specific path.
- SYSFUNC is a future semantic feeder even if current seeding is sparse.
- Scalar function forms and aggregate command forms must remain separate until runtime/source evidence closes the ambiguity.
- AGGS is treated as internal/family-owner evidence unless explicitly accepted as a user-facing command surface.

## Purpose of this section

This section explains expression evaluation, predicates, query filters, aggregate commands, and function surfaces in DotTalk++.

It follows Navigation and Indexing because those sections establish record movement, search context, active order, tags, projection, and relation boundaries. Expressions sit beneath many of those surfaces. Predicates decide which records are considered. Aggregate commands summarize values across records. Function calls support scalar calculation, command-line function applications, and calculated command behavior.

The goal is not to publish a final function reference. The goal is to establish safe developer-manual prose that preserves the boundaries between expression evaluation, command parsing, predicate filtering, aggregate traversal, scalar functions, and future metadata feeders.

## Evidence lanes

This draft uses several evidence lanes.

Current DotTalk evidence lane:
- CALC
- CALCWRITE
- WHERE
- FOR
- LOCATE
- CONTINUE
- SCAN
- COUNT
- SUM
- AVG
- MIN
- MAX
- AGGS
- FUNCTION
- FUNCTIONS
- PREDICATES
- MIN()
- MAX()
- xexpr
- DELETED
- NOT DELETED
- !DELETED

Generated command-reference lane:
- Generated command pages may identify draft command evidence.
- They are not final prose and should not be quoted as final command authority.
- AGGS and MIN/MAX require extra review because generated pages can expose implementation or family-owner concepts that may not be intended as public command surface.

Runtime evidence lane:
- Runtime examples have shown direct aggregate verbs SUM, AVG, MIN, and MAX working against an open table.
- Runtime examples have shown WHERE and FOR producing matching aggregate results in tested cases.
- Runtime examples have shown deleted-record filters affecting aggregate outputs in tested cases.
- Runtime examples have shown command-line function application behavior for functions such as UPPER and LEFT.
- Runtime examples have shown MIN/MAX parser ambiguity that must remain canary-sensitive.

Concept lane:
- An expression computes a value.
- A predicate is an expression used as a true/false condition.
- A query filter selects records.
- An aggregate command computes a result across records.
- A scalar function computes a result from arguments.
- A command parser may route command-like input differently from expression-function input.

Compatibility lane:
- xBase/FoxPro lineage can explain vocabulary, but compatibility evidence must not be promoted as current DotTalk behavior without runtime proof.
- Function names that overlap with command verbs are especially compatibility-sensitive.

Future META feeder lane:
- SYSFUNC should eventually carry canonical function identity, display name, category, argument range, handler, CALC_CALL, PUB_SURF, SELF_REG, MSG_CAT, and active status.
- SYSARGS should eventually carry function and command argument shapes, required/repeatable flags, predicate shapes, deleted filters, and expression values.
- SYSCMD should eventually carry command identity for COUNT, SUM, AVG, MIN, MAX, CALC, CALCWRITE, LOCATE, CONTINUE, SCAN, and related command surfaces.
- SYSSUBCMD should eventually carry aggregate-family or predicate-related subcommands if the command model keeps subcommand ownership.
- SYSENTVAR should eventually carry command/function variants, aliases, and app-style function entry points after seed hygiene review.
- SYSHELP should eventually carry curated/generated help text for functions, predicates, aggregate commands, and expression concepts.
- SYSMSG should eventually carry expression errors, nonnumeric aggregate values, no-active-table messages, not-found messages, deleted-filter outcomes, and parser ambiguity warnings.

## Expression evaluation surfaces

Expression evaluation is shared infrastructure. The manual should treat xexpr as the expression engine unless current source evidence proves otherwise for a specific path.

Expression surfaces include:
- CALC
- CALCWRITE
- command arguments that accept value expressions
- predicates in WHERE or FOR style clauses
- function calls
- calculated values used by aggregate commands

The developer manual should make a distinction between expression syntax and command syntax. A command may accept an expression, but that does not make the command itself the expression engine.

## CALC and CALCWRITE

CALC and CALCWRITE are expression-oriented command surfaces. They are useful places to explain evaluated expressions without requiring table traversal.

Safe wording:
- CALC evaluates an expression and displays or returns the result according to its command contract.
- CALCWRITE evaluates and writes or displays according to its command contract.
- Exact output behavior should be verified with HELP and runtime evidence before final wording.

These commands are natural cross-references for function help and the xexpr engine.

## Predicates, WHERE, and FOR

A predicate is an expression used as a condition. WHERE and FOR are predicate-bearing clauses or surfaces.

Safe wording:
- WHERE and FOR can restrict which records participate in a command where supported.
- Runtime evidence has shown matching aggregate results for equivalent WHERE and FOR predicates in tested aggregate cases.
- This equivalence should not be generalized across all commands without evidence.

The manual should not imply that WHERE and FOR are always identical. It should say that they can serve related predicate-filter roles and that each command surface must be checked.

## LOCATE, CONTINUE, and SCAN

LOCATE, CONTINUE, and SCAN connect predicates with traversal.

Safe distinctions:
- LOCATE searches for records matching a condition.
- CONTINUE resumes a prior locate-style search where supported.
- SCAN iterates over records and may use predicate or scope rules depending on command syntax.

These commands connect this section with Navigation and Indexing:
- Navigation owns movement and current record context.
- Indexing owns active order and tag-sensitive traversal context.
- Expressions own predicate evaluation.
- Commands own their own syntax and side effects.

## COUNT and aggregate commands

COUNT, SUM, AVG, MIN, and MAX belong to aggregate command discussion when they operate across records.

Safe aggregate wording:
- COUNT counts records or matched records according to command syntax and scope.
- SUM computes a total for a numeric expression across records.
- AVG computes an average for a numeric expression across records.
- MIN and MAX compute minimum and maximum aggregate results where command syntax and runtime support them.

The final manual should attach runtime proof for each command surface before claiming exact syntax, deleted-record behavior, or null/empty-set behavior.

## Direct aggregate verbs and AGGS

Direct aggregate verbs should be treated as the user-facing command surface where runtime and HELP evidence support them:
- SUM
- AVG
- MIN
- MAX

AGGS should be treated carefully. Current doctrine is:
- AGGS is intended as an owner/internal grouping for aggregate verbs.
- AGGS being executable or printing usage may be debug/scaffold leakage unless explicitly accepted.
- Generated command pages for AGGS are draft evidence, not final public-surface proof.

The manual should explain aggregate family ownership without accidentally publishing an internal owner as a user command.

## Scalar functions versus aggregate commands

MIN and MAX are the important canary.

There are two concepts:
- scalar function form: MIN() or MAX() as a function over supplied arguments;
- aggregate command form: MIN <value_expr> or MAX <value_expr> over records.

These must not be collapsed.

Known runtime canary:
- command-style input has shown MIN/MAX aggregate behavior.
- function-app and command-line function bridging exists for functions such as UPPER and LEFT.
- MIN(2,1) versus MIN 2,1 parser behavior must remain canary-sensitive until current runtime/source evidence closes it.

The manual should preserve the ambiguity:
- MIN/MAX aggregate commands are command surfaces.
- MIN()/MAX() scalar functions are function surfaces if current function registry/runtime evidence confirms them.
- Parser dispatch and command/function shadowing must be documented carefully.

## Function command-line bridge

DotTalk++ allows some function/app forms to be used directly from the command line.

Examples in prior runtime notes include:
- UPPER with a string-like value
- LEFT with a value and length argument

This is important because function names may appear command-like when typed at the prompt. The manual should explain that some command-line input can bridge into scalar/function-app evaluation.

However, the bridge must not override command ownership:
- A direct command verb may own a word such as MIN or MAX.
- A scalar function may also exist with the same name.
- The parser/dispatcher decides which surface receives the input.

## Deleted-record filters

Aggregate commands may support deleted-record filters.

Evidence-sensitive filter vocabulary:
- DELETED
- NOT DELETED
- !DELETED

Safe wording:
- Deleted-record filters may affect which records participate in aggregate results where supported.
- Runtime evidence has shown DELETED returning empty/null-like aggregate behavior in tested cases and NOT DELETED matching full nondeleted results in tested cases.
- Exact behavior must be verified per command, expression type, and data state.

The manual should not generalize deleted-record behavior beyond tested aggregate surfaces without proof.

Proof boundary:
- deleted-record aggregate filters are proof-aware.
- DELETED, NOT DELETED, and !DELETED should not be generalized beyond tested aggregate surfaces.
- Final wording must remain tied to command, expression type, and data-state evidence.

## Error and null behavior

Aggregate and expression commands can produce errors or null-like results.

Examples needing proof-aware wording:
- nonnumeric expression supplied to a numeric aggregate;
- character expression supplied to AVG;
- unknown field or expression;
- empty or deleted-only record sets;
- no active table;
- invalid function argument count.

SYSMSG is the intended future feeder for error symbols, severity, short text, suggested actions, and implementation status.

## HELP FUNCTIONS and FUNCTION help

HELP FUNCTIONS and HELP FUNCTION <name> should be included as user-facing discovery surfaces for expression functions.

The manual should distinguish:
- command help for command verbs;
- function help for expression functions;
- generated command draft pages;
- future SYSFUNC metadata.

SYSFUNC is important even when sparsely seeded because it is the future semantic feeder for canonical function identity, argument ranges, handlers, public surface status, and message-catalog alignment.

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



<!-- END SECTION: sections\expressions_querying_and_aggregates.md -->

---

<!-- BEGIN SECTION: sections\functions_and_expression_helpers.md -->

# Functions and Expression Helpers

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [ALLTRIM](../../command_reference_v1/commands/alltrim.md)
- [ASC](../../command_reference_v1/commands/asc.md)
- [ASCII](../../command_reference_v1/commands/ascii.md)
- [AT](../../command_reference_v1/commands/at.md)
- [ATC](../../command_reference_v1/commands/atc.md)
- [CHR](../../command_reference_v1/commands/chr.md)
- [CONCAT](../../command_reference_v1/commands/concat.md)
- [CTOD](../../command_reference_v1/commands/ctod.md)
- [DATE](../../command_reference_v1/commands/date.md)
- [DTOC](../../command_reference_v1/commands/dtoc.md)
- [EVAL](../../command_reference_v1/commands/eval.md)
- [EVALUATE](../../command_reference_v1/commands/evaluate.md)
- [EXPFUNCS](../../command_reference_v1/commands/expfuncs.md)
- [EXPRESSION](../../command_reference_v1/commands/expression.md)
- [LEFT](../../command_reference_v1/commands/left.md)
- [LEN](../../command_reference_v1/commands/len.md)
- [LOWER](../../command_reference_v1/commands/lower.md)
- [LTRIM](../../command_reference_v1/commands/ltrim.md)
- [NAVIGATION](../../command_reference_v1/commands/navigation.md)
- [NORMALIZE](../../command_reference_v1/commands/normalize.md)
- [PADC](../../command_reference_v1/commands/padc.md)
- [PADL](../../command_reference_v1/commands/padl.md)
- [PADR](../../command_reference_v1/commands/padr.md)
- [PREDHELP](../../command_reference_v1/commands/predhelp.md)
- [PREDICATE](../../command_reference_v1/commands/predicate.md)
- [PREDICATES](../../command_reference_v1/commands/predicates.md)
- [PROJECTION](../../command_reference_v1/commands/projection.md)
- [PROPER](../../command_reference_v1/commands/proper.md)
- [REPLICATE](../../command_reference_v1/commands/replicate.md)
- [RIGHT](../../command_reference_v1/commands/right.md)
- [RTRIM](../../command_reference_v1/commands/rtrim.md)
- [SPACE](../../command_reference_v1/commands/space.md)
- [STATE](../../command_reference_v1/commands/state.md)
- [STR](../../command_reference_v1/commands/str.md)
- [STRUCT](../../command_reference_v1/commands/struct.md)
- [STU_REPEAT](../../command_reference_v1/commands/stu_repeat.md)
- [STU_UPPER](../../command_reference_v1/commands/stu_upper.md)
- [STUFF](../../command_reference_v1/commands/stuff.md)
- [SUBSTR](../../command_reference_v1/commands/substr.md)
- [TIME](../../command_reference_v1/commands/time.md)
- [TRIM](../../command_reference_v1/commands/trim.md)
- [UPDATE](../../command_reference_v1/commands/update.md)
- [UPPER](../../command_reference_v1/commands/upper.md)
- [VAL](../../command_reference_v1/commands/val.md)
- [VALIDATE](../../command_reference_v1/commands/validate.md)
<!-- BEGIN SECTION: sections\getting_started_and_session_basics.md -->

# Getting Started and Session Basics

Status: PROMOTED_TO_MANUAL_DRAFT / REVIEW_REQUIRED

Evidence class:
- Reviewed prose candidate assembled from MDO-107 draft prose and evidence review.
- Runtime behavior remains the source of truth.
- This candidate is not final manual prose.
- This candidate does not mutate HELP, META, CMDHELPCHK, catalogs, source files, or production SelfDoc metadata.

Promotion gate:
- READY_FOR_HUMAN_PROMOTION_REVIEW

## Overview

This section is the front door for the Developer Manual. It introduces the basic interactive command surface before the reader reaches table context, work areas, browsing, indexing, relations, storage bridges, and SelfDoc/manualgen workflows.

The purpose is orientation, not completeness. A new reader should leave this section knowing how to ask for help, identify the running program, inspect basic status, adjust simple display behavior, and leave the session.

## First commands to know

HELP is the safest first command. It points the user into the command documentation surface without requiring a table to be open or a work area to be selected.

ABOUT and VERSION identify the program or build context. STATUS belongs in the same introductory group because it helps the user or developer understand visible session state from the command surface. These commands should be described as orientation commands, not as table commands.

## Session display comfort

COLOR and CLEAR are introductory session-comfort commands. COLOR changes the display environment. CLEAR resets the visible screen. In this section, describe them only as user-interface or session-display conveniences unless command-page evidence supports more specific claims.

These commands should not be described as data mutation, metadata mutation, or storage behavior.

## Leaving the session

QUIT is the exit command. The conservative manual wording is that QUIT leaves the interactive DotTalk++ session. Do not overclaim cleanup behavior unless runtime evidence or command-page evidence supports the stronger statement.

## Relationship to the next section

This section intentionally stops before table-opening and workspace behavior. USE, AREA, SELECT, and WORKSPACE are introduced in the next section, Workspaces, Areas, and Session State. Keeping that boundary clear prevents the manual from mixing session orientation with table context.

## Command map

- ABOUT: identifies the project or runtime context.
- CLEAR: clears or resets the visible command display.
- COLOR: changes the session display environment.
- HELP: opens the command documentation surface.
- QUIT: leaves the interactive session.
- STATUS: reports visible command/session status where supported.
- VERSION: reports build or version identity where supported.

## Example path for a later prose pass

Examples should be added only after command syntax and runtime transcripts are checked. A safe later example path is:

1. Use ABOUT or VERSION to identify the running program.
2. Use HELP to find command documentation.
3. Use COLOR or CLEAR for display comfort.
4. Use STATUS only with evidence-backed wording.
5. Use QUIT to leave the session.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion

<!-- END SECTION: sections\getting_started_and_session_basics.md -->

---

<!-- BEGIN SECTION: sections\help_metadata_and_selfdoc.md -->

<!-- MDO-116: promoted from reviewed candidate into manual draft workspace v3. -->
<!-- Decision: MDO-115 ACCEPT_FOR_PROMOTION; gate READY_FOR_HUMAN_PROMOTION_REVIEW. -->
<!-- Pipeline ledger: generated/pipeline_docs_v1/MANUALGEN_PIPELINE_LEDGER_v1.md remains supporting draft evidence. -->

# HELP, Metadata, and SelfDoc

Status: PROMOTED_TO_MANUAL_DRAFT / REVIEW_REQUIRED

Evidence class:
- Reviewed prose candidate assembled from MDO-112 draft prose and MDO-113 evidence review.
- Runtime behavior remains the source of truth.
- This candidate is not final manual prose.
- This candidate does not mutate HELP, META, CMDHELPCHK, catalogs, source files, or production SelfDoc metadata.

Promotion gate:
- READY_FOR_HUMAN_PROMOTION_REVIEW

## Overview

This section explains the evidence system behind the Developer Manual. DotTalk++ documentation is not meant to be a free-written description detached from the running program. It is assembled from runtime behavior, source contracts, HELP output, metadata rows, validation reports, command-reference pages, review gates, and human decisions.

The working doctrine is: runtime proves, source defines, HELP explains, metadata organizes, CMDHELPCHK validates, SelfDoc preserves provenance, and manualgen assembles human-facing manuals from evidence.

## Why this matters

The manual is part of the system, not just an after-the-fact book. Each generated section should have a trail showing where its claims came from, what was checked, what was deferred, and what was not mutated.

This keeps the manuals aligned with the project instead of letting them drift into a separate version of reality.

## HELP explains the command surface

HELP is the user-facing explanation layer. It exposes command syntax, usage, examples, notes, and related material. The manual can draw from HELP, but it should not silently replace HELP or invent behavior beyond the command evidence.

CMDHELP belongs to the command-help maintenance path. CMDHELPCHK belongs to the validation path. In this manual lane, CMDHELPCHK is especially important because it helps check whether generated HELP and artifact rows are structured well enough to be used downstream.

A successful HELP or CMDHELPCHK-related step is evidence. It is not, by itself, final publication.

## Metadata organizes evidence

Metadata gives the project structured rows that can be inspected, compared, exported, reconciled, and reviewed. It helps organize command facts, field facts, HELP facts, and documentation facts.

METADATA and TABLEMETA belong in this section as command surfaces for metadata-related inspection or reporting. The manual should keep their claims conservative until each command page and runtime behavior are reviewed.

The important distinction is that metadata organizes evidence. Metadata alone does not prove runtime behavior.

## SelfDoc preserves provenance

SelfDoc is the provenance-preserving role in this documentation system. It keeps source comments, usage contracts, HELP artifacts, metadata rows, generated pages, reports, canaries, manual drafts, and save points connected to the evidence trail.

This is why the MDO process repeatedly records boundaries. Those boundaries state whether a step generated draft evidence, reviewed a gate, promoted a draft workspace, or mutated nothing. They are not decoration. They are the safety rails that keep documentation work reversible and auditable.

## Manualgen assembles, reviews, and gates

Manualgen is the assembly lane. It starts from harvested HELP and metadata evidence, builds command-reference material, organizes that material into a TOC and skeleton, drafts prose, reviews evidence, creates reviewed candidates, records human decisions, and promotes accepted sections into versioned manual draft workspaces.

The current proven manualgen path is documented in the Manualgen Pipeline Ledger. The pipeline includes harvest, reconcile, assemble, normalize, structure, draft, review, candidate, decision, promote, and record phases.

The ledger itself is a project artifact. It should be updated when a repeatable phase, repair pattern, or promotion gate is proven.

## Runtime inspection and teaching surfaces

The documentation family is no longer visible only through reports and generated
files. Several read-only runtime surfaces already expose the live model of these
lanes.

- `MANUAL` is the runtime inspector for accepted `MAN*` manualgen catalog state.
- `DDICT` is the runtime inspector for the active Data Dictionary catalog,
  including fields, tags, relations, and evidence.
- `BBOX` is the teaching surface that explains these lanes as blackbox systems:
  data in, process, information out.
- `MAINT` is the maintenance/control-surface inspector for status, boundaries,
  docs, GUI, AI Friendly, and contracts.

This distinction matters. The manual should not describe manualgen, datadict,
blackbox, and maintenance as if they were only document concepts when the
runtime already exposes them as separate read-only command surfaces.

## Command map

- CMDARGCHK: supports command argument checking or review in the documentation/validation lane.
- CMDHELP: supports command-help generation, maintenance, or inspection.
- CMDHELPCHK: validates HELP and command-help artifact consistency.
- MANUAL: inspects accepted manual catalog state.
- DDICT: inspects accepted Data Dictionary catalog state.
- BBOX: teaches the documentation/maintenance blackbox model.
- MAINT: reports the maintenance/control surface around these lanes.
- METADATA: exposes metadata-related inspection or reporting surfaces.
- TABLEMETA: exposes table-metadata inspection or reporting surfaces.

## Workflow map

- Harvest: collect HELP and META inputs without mutating them.
- Reconcile: compare harvested rows and create review queues.
- Assemble: generate command-reference draft pages.
- Normalize: handle aliases, collisions, symbol commands, and deferred families.
- Structure: build TOC and skeleton files.
- Draft: write section prose from evidence.
- Review: check command pages and generate a promotion gate.
- Candidate: tighten prose without final promotion.
- Decision: capture human acceptance, revision, hold, or rejection.
- Promote: copy accepted prose into a versioned manual draft workspace.
- Record: update save points and pipeline ledgers.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion

<!-- END SECTION: sections\help_metadata_and_selfdoc.md -->

---

<!-- BEGIN SECTION: sections\help_metadata_cmdhelpchk_and_manualgen_alignment.md -->

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

<!-- MDO-303E removed process scaffold heading 'Future META alignment' from reader clean copy; preserved in reports. -->
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

<!-- MDO-303E removed process scaffold heading 'Slow-lane canary tracking names' from reader clean copy; preserved in reports. -->
<!-- MDO-303E removed process scaffold heading 'Review notes before PIP-003' from reader clean copy; preserved in reports. -->
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


<!-- END SECTION: sections\help_metadata_cmdhelpchk_and_manualgen_alignment.md -->

---

<!-- BEGIN SECTION: sections\import_export_and_storage_bridges.md -->

# Import, Export, and Storage Bridges

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [AUTODBF](../../command_reference_v1/commands/autodbf.md)
- [BUILDLMDB](../../command_reference_v1/commands/buildlmdb.md)
- [EXPORT](../../command_reference_v1/commands/export.md)
- [EXPORTSQL](../../command_reference_v1/commands/exportsql.md)
- [IMPORT](../../command_reference_v1/commands/import.md)
- [IMPORTSQL](../../command_reference_v1/commands/importsql.md)
- [LMDB](../../command_reference_v1/commands/lmdb.md)
- [LMDB_UTIL](../../command_reference_v1/commands/lmdb_util.md)
- [LMDBDUMP](../../command_reference_v1/commands/lmdbdump.md)
- [SQL](../../command_reference_v1/commands/sql.md)
- [SQLERASE](../../command_reference_v1/commands/sqlerase.md)
- [SQLHELP](../../command_reference_v1/commands/sqlhelp.md)
- [SQLITE](../../command_reference_v1/commands/sqlite.md)
- [SQLSEL](../../command_reference_v1/commands/sqlsel.md)
- [SQLVER](../../command_reference_v1/commands/sqlver.md)
<!-- BEGIN SECTION: sections\indexing_order_and_relations.md -->

# Indexing, Order, and Relations

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [ASCEND](../../command_reference_v1/commands/ascend.md)
- [CDX](../../command_reference_v1/commands/cdx.md)
- [CNX](../../command_reference_v1/commands/cnx.md)
- [DESCEND](../../command_reference_v1/commands/descend.md)
- [IDX](../../command_reference_v1/commands/idx.md)
- [INDEX](../../command_reference_v1/commands/index.md)
- [ORDER](../../command_reference_v1/commands/order.md)
- [REBUILD](../../command_reference_v1/commands/rebuild.md)
- [REINDEX](../../command_reference_v1/commands/reindex.md)
<!-- BEGIN SECTION: sections\indexing_tags_relations_and_views.md -->

# Indexing, Tags, Relations, and Views




Pippets used:
- PIP-001 Target Selection
- MDO-143 Target Selection
- MDO-144 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches known canaries.
- Do not send this directly to promotion review.
- Run a canary-aware evidence review before PIP-003 is allowed to produce a reviewed candidate.

Evidence tokens under review:
- INDEX
- REINDEX
- REBUILD
- SET ORDER
- SET INDEX
- ASCEND
- DESCEND
- SEEK
- FIND
- CNX
- CDX
- LMDB
- BUILDLMDB
- REL
- RELATIONS
- ERSATZ
- VIEW

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Generated command draft pages remain draft evidence, not final command reference prose.
- The section preserves the distinction between logical/user-facing abstractions and physical backend details.
- CDX/CNX language should be reviewed against current implementation and HELP/META evidence before final wording.
- SET-family canonicalization remains deferred unless separately repaired or accepted.
- Relations, tuple traversal, browser rendering, and views must not be collapsed into one ownership model.

## Purpose of this section

This section explains the concepts that control ordered traversal, indexed lookup, relation-aware traversal, and view/projection terminology in DotTalk++.

It follows Navigation, Browsing, and Search because that section deliberately deferred index-specific and relation-specific behavior. Navigation can say that traversal and search may depend on context. This section explains the important context: active order, tags, logical index surfaces, physical backend boundaries, relations, and views.

The goal is not to publish a final index command reference. The goal is to establish safe developer-manual prose that keeps ownership boundaries visible and prevents logical abstractions from being confused with physical backends.

## Evidence lanes

This draft uses several evidence lanes.

Current DotTalk evidence lane:
- INDEX
- REINDEX
- REBUILD
- SET ORDER
- SET INDEX
- ASCEND
- DESCEND
- SEEK
- FIND
- CNX
- CDX
- LMDB
- BUILDLMDB
- REL
- RELATIONS
- ERSATZ
- VIEW

Generated command-reference lane:
- Generated command pages may identify available draft command evidence.
- They are not final prose and should not be quoted as final manual authority.
- Duplicate commands, aliases, slug collisions, and SET-family canonicalization still require command-reference review.

Concept lane:
- Indexing provides ordered or keyed access paths.
- Tags name or select logical orders.
- Active order affects traversal and key-style search where supported.
- Relations connect areas or tables through traversal rules.
- Views and browser output are projection surfaces unless proven otherwise.

Compatibility lane:
- xBase/FoxPro lineage can explain vocabulary, but compatibility material must not be promoted as current DotTalk behavior without runtime proof.
- SET-family commands are especially compatibility-sensitive.

Future META feeder lane:
- SYSCMD should eventually carry command identity and handler alignment.
- SYSSUBCMD should eventually carry SET ORDER, SET INDEX, REL, and related subcommand identity.
- SYSENTVAR should eventually carry aliases, variants, and shortcut spellings after seed hygiene review.
- SYSARGS should eventually carry tag names, key expressions, relation/view arguments, and rebuild options.
- SYSMSG should eventually carry missing tag, order not found, backend build, relation warning, and rebuild diagnostics.
- SYSHELP should eventually carry curated/generated concept help for indexes, tags, relations, views, and traversal.

## Indexing vocabulary

Indexing vocabulary needs careful separation.

A user may think about indexes as a way to find records faster or view records in a useful order. A developer manual should be more precise: an index or order is a traversal/access structure that can influence how commands move through or locate records.

Important terms:
- index: a structure or command surface associated with ordered/keyed access.
- order: the currently selected traversal order where supported.
- tag: a named logical order within a multi-tag abstraction.
- rebuild/reindex: operations that refresh or rebuild index structures.
- key expression: the value or expression used to derive ordered/keyed lookup behavior.

The section should avoid claiming that every navigation or search command always uses an index. That behavior must be proven per command and context.

## Logical order and active order

The active order is a current traversal context. It may affect display, movement, and search behavior depending on the command path.

A safe explanation is:
- table state has a current record position;
- ordered traversal may change the sequence in which records are visited;
- commands such as LIST can expose the actual traversal order;
- key-style commands such as SEEK or FIND may depend on active order or key context where supported.

Known canary:
- Reported active order must agree with actual traversal order before an order path is marked proven.
- A command saying an order is active is not enough. LIST, SEEK, rebuild, and runtime smoke evidence must agree.

## Tags and tag availability

A tag names a logical order. In a multi-tag model, selecting a tag should select a user-facing logical order.

This section should preserve this rule:
- tag availability and reported active tag must be verified against actual traversal behavior.

Known proof-sensitive case:
- A tag may be reported as selected before it is actually available or rebuilt.
- After rebuild, traversal may become consistent.
- This should remain a canary until runtime proof closes it.

Do not hide this from developer documentation. The manual may keep user-facing prose simple, but the Developer Manual must preserve the proof boundary.

## CDX, CNX, and LMDB boundary

The preferred doctrine is:

- CDX/CNX are logical or user-facing index abstractions.
- LMDB is a physical backend and should remain hidden from ordinary command-surface prose unless the section is explicitly backend/developer-facing.

This does not mean LMDB is unimportant. It means ordinary command documentation should avoid making users think they are operating directly on the physical backend when they are really selecting orders, tags, or logical index structures.

Developer-facing prose may explain:
- the logical abstraction seen by commands;
- the physical backend used internally;
- where the backend boundary must not leak into public command vocabulary.

This boundary should be reviewed against current source and HELP/META evidence before final manual promotion.

## SET-family boundary and canonicalization canary

SET-family commands are known to require careful canonicalization.

The section may mention:
- SET ORDER
- SET INDEX
- SET-family command surfaces
- the need to distinguish aliases, variants, and canonical commands

But it should not resolve canonicalization casually.

Known canary:
- SET-family canonicalization remains deferred.
- Generated command-reference pages for SET-family items should remain draft evidence until canonicalization is repaired or explicitly accepted.

Manual rule:
- Keep SET-family wording conservative.
- Do not treat duplicate or variant generated command pages as final canonical command identity.

## SEEK and FIND active-order boundary

Navigation, Browsing, and Search introduced SEEK and FIND as search vocabulary but deferred index-specific behavior. This section owns the active-order boundary for those commands.

A safe statement is:
- SEEK and FIND are key-style search commands whose exact behavior may depend on active order, tag, or index context.
- The final manual should attach runtime proof before claiming exact behavior.
- If a command falls back to physical order, reports active order incorrectly, or requires rebuild first, that must remain visible as a canary.

This section should not collapse SEEK/FIND with LOCATE. LOCATE is more naturally predicate-oriented and belongs with expression/predicate search behavior, even if it appears in navigation prose.

## Reindexing and rebuild behavior

REINDEX, REBUILD, and BUILDLMDB touch refresh/build behavior.

A conservative explanation is:
- rebuild/reindex commands update index or backend structures;
- their exact scope and backend effects must be verified by command evidence;
- public-facing wording should focus on refreshing logical orders or tags;
- backend-specific wording belongs in developer/backend notes.

Known risk:
- BUILDLMDB and LMDB terminology can pull physical storage details into user-facing prose.
- Keep public/user wording logical unless a developer/backend section explicitly opens the physical layer.

## Relations and relation traversal

Relations connect work areas or tables so that a parent context can lead to related child records.

This section should explain relation traversal without making browser output the owner of relation semantics.

Ownership rule:
- relation subsystem owns relation definitions and traversal intent;
- tuple infrastructure owns relation-aware row projection;
- browser and ERSATZ surfaces render or navigate projected relation state;
- workspace/session systems own restored area and relation context.

This section can cross-reference the Workspaces and Tuple sections rather than fully restating them.

Known proof:
- MCC/x32 relation paths and ERSATZ browser output have provided useful runtime evidence.
- x64 workspace/ERSATZ load reporting remains canary-sensitive.

## Views and projection boundary

The word view is dangerous because it can mean a saved query, a projection, a browser surface, or a conceptual display. The manual should not assume one meaning until HELP/META/source evidence classifies the actual command surface.

Safe language:
- a view/projection presents selected or arranged data;
- projection is not storage ownership;
- relation-aware projection is not the same as relation definition;
- browser output is not the same as table or relation ownership.

This section should preserve that ambiguity until the command-reference and source evidence clarify VIEW and related surfaces.

## ERSATZ and browser caution

ERSATZ and relation-aware browser output are valuable evidence surfaces, but they are path-specific.

Known cautions:
- plain ERSATZ/no-arg paths and MCC/x32 relation browser paths have useful proof value;
- ERSATZ GRID was previously deferred because its snapshot branch did not preserve the same complete BrowserSnapshot;
- browser output may be usable even when workspace load reporting is noisy;
- projection output should not be promoted to semantic ownership.

Use ERSATZ evidence to explain what can be seen. Do not use it alone to prove every underlying workspace/relation/load behavior.

## Known canaries

This section must keep the following canaries visible:

- SET-family canonicalization is deferred.
- SET ORDER and active tag reporting must agree with actual traversal before order behavior is marked proven.
- CDX/CNX must remain logical/user-facing abstractions unless developer/backend context is explicit.
- LMDB is a physical backend and should not leak into ordinary command-surface prose.
- SEEK/FIND active-order behavior requires runtime proof.
- Generated command pages remain draft evidence.
- Relations, tuple traversal, browser rendering, and views require separate ownership language.
- ERSATZ/browser evidence is path-specific.
- x64 workspace/ERSATZ load reporting remains canary-sensitive.


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



<!-- END SECTION: sections\indexing_tags_relations_and_views.md -->

---

<!-- BEGIN SECTION: sections\legacy_and_compatibility_surfaces.md -->

# Legacy and Compatibility Surfaces

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [COBOL](../../command_reference_v1/commands/cobol.md)
- [DOTHELP](../../command_reference_v1/commands/dothelp.md)
- [DOTSCRIPT](../../command_reference_v1/commands/dotscript.md)
- [ERP](../../command_reference_v1/commands/erp.md)
- [FOXHELP](../../command_reference_v1/commands/foxhelp.md)
- [FOXPRO](../../command_reference_v1/commands/foxpro.md)
- [FOXSTANDARD](../../command_reference_v1/commands/foxstandard.md)
- [FOXTALK](../../command_reference_v1/commands/foxtalk.md)
- [RETRO](../../command_reference_v1/commands/retro.md)
- [SCX](../../command_reference_v1/commands/scx.md)
- [SIX](../../command_reference_v1/commands/six.md)
- [TVISION](../../command_reference_v1/commands/tvision.md)
<!-- BEGIN SECTION: sections\messages_errors_and_diagnostics.md -->

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

## Current runtime messaging and locale surfaces

The messaging lane is no longer only future doctrine.

Current runtime evidence shows a real command/provider/data stack:

- `MSGMGR` is the runtime messaging-manager command house.
- `SYSTEM_MESSAGES.dbf` and `SYSTEM_MESSAGE_TEXT.dbf` are active runtime catalog
  tables under `dottalkpp/data/messaging`.
- `SYSTEM_MESSAGE_TEXT.dtx` is part of the active message-text storage path.
- `message_catalog.cpp` is the runtime provider boundary for localized catalog
  lookup and reviewed seed/apply maintenance.

Current `MSGMGR` surface includes:

- `MSGMGR`
- `MSGMGR USAGE`
- `MSGMGR STATUS`
- `MSGMGR CHECK`
- `MSGMGR SEED PRIORITYA CHECK|APPLY`
- `MSGMGR SEED PRIORITYB CHECK|APPLY`
- `MSGMGR SEED PRIORITYC CHECK|APPLY`

Important boundary:

- `STATUS` and `CHECK` are read/report surfaces.
- reviewed `SEED ... APPLY` mutates the runtime messaging catalog tables.
- the command explicitly does not mutate HELP DATA, CMDHELPCHK, manualgen, Data
  Dictionary, SelfDoc, or source-derived catalogs.

Related runtime surfaces named by the command:

- `SET MESSAGE CATALOG CHECK`
- `SET MESSAGE CATALOG GET`
- `SET LANGUAGE`
- `SET MESSAGE EMIT`

The operator-facing shell entrypoint is broader than `MSGMGR` alone.

Current `SET` command evidence shows these messaging/locale surfaces:

- `SET LANGUAGE`
- `SET LANGUAGE TO <locale|DEFAULT>`
- `SET LOCALE`
- `SET LOCALE TO <locale|DEFAULT>`
- `SET LANGUAGE CHECK`
- `SET LANGUAGE REPORT`
- `SET LOCALE CHECK`
- `SET LOCALE REPORT`
- `SET MESSAGE CATALOG CHECK`
- `SET MESSAGE CATALOG STATUS`
- `SET MESSAGE PROOF ON|OFF|CHECK`
- `SET MESSAGE EMIT <symbol> [LOCALE <locale>] [ARG <name> <value>]`

So the current safe split is:

- `SET ...` is the normal shell/operator control surface for locale selection,
  provider checks, routing proof, and direct message emission.
- `MSGMGR` is the manager/report/seed surface for the runtime messaging catalog
  itself.

The locale lane also has a real structural/runtime spine:

- `SYSTEM_LOCALES.dbf`
- `SYSTEM_LOCALE_FALLBACK.dbf`
- provider boundary in `locale_spine_catalog.cpp`

That means the manual should now distinguish two different but related truths:

- `SYSMSG` remains the compact metadata feeder for message identity, severity,
  ownership, and publication alignment.
- `SYSTEM_MESSAGES` / `SYSTEM_MESSAGE_TEXT` are active runtime catalog/provider
  tables used by the current message-rendering path.

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


<!-- END SECTION: sections\messages_errors_and_diagnostics.md -->

---

<!-- BEGIN SECTION: sections\navigation_browsing_and_search.md -->

# Navigation, Browsing, and Search




Pippets used:
- PIP-001 Target Selection
- PIP-002 Draft Prose
- MDO-138B Clean Scaffold and Factory Patch
- MDO-139 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Evidence tokens under review:
- LIST
- SMARTLIST
- BROWSE
- BROWSER
- SEEK
- FIND
- LOCATE
- CONTINUE
- SCAN
- SKIP
- GO
- GOTO
- TOP
- BOTTOM

Draft notes:
- This is conservative manual prose for evidence review.
- Generated command draft pages remain draft evidence, not final command reference prose.
- This section explains navigation, browsing, and search at the user/concept level.
- Detailed index semantics, SET ORDER behavior, tags, and index storage belong in the indexing section.
- Runtime proof and source verification still need to be attached by the evidence review step.

## Purpose of this section

This section explains how a reader should understand moving through records, finding records, and viewing records in DotTalk++.

It follows the earlier manual sections on getting started, workspaces, and the table/record/data model. Those sections establish that commands operate inside a current area or workspace context. This section builds on that foundation by explaining how a user moves within an open table, searches for relevant records, and chooses a viewing surface.

The goal is not to produce a final command reference. The goal is to provide a stable narrative bridge between the data model and later sections on indexing, expressions, relations, and browsers.

## Evidence lanes

This draft uses the following evidence lanes.

Current DotTalk evidence lane:
- LIST
- SMARTLIST
- BROWSE
- BROWSER
- SEEK
- FIND
- LOCATE
- CONTINUE
- SCAN
- SKIP
- GO
- GOTO
- TOP
- BOTTOM

Generated command-reference lane:
- Generated command pages may identify available draft evidence.
- They are not final prose and should not be quoted as final manual authority.

Concept lane:
- Navigation means changing the current record position.
- Search means locating records by a key, value, expression, or predicate.
- Browsing means presenting table or record state through a display/projection surface.

Compatibility lane:
- Any FoxPro or xBase compatibility references must remain gated.
- Compatibility evidence may explain lineage or vocabulary, but it must not be promoted as current DotTalk behavior without runtime proof.

Future META feeder lane:
- SYSCMD should eventually carry command identity and handler alignment.
- SYSARGS should eventually carry argument shapes for navigation/search commands.
- SYSMSG should eventually carry warnings, not-found messages, and navigation/search diagnostics.
- SYSHELP should eventually carry curated or generated concept help for this section.
- SYSENTVAR may eventually carry aliases or command variants if those are seeded and reviewed.

## Navigation basics

Navigation commands operate against the current table context. In DotTalk terms, that means they depend on the selected work area, the open table in that area, the current record pointer, and any active traversal context.

The manual should teach navigation as movement through record position, not as storage mutation.

The main navigation vocabulary in this draft includes:
- GO or GOTO for moving to a specific record position or target where supported.
- TOP and BOTTOM for moving to the beginning or end of the current traversal.
- SKIP for moving relative to the current record.
- Record-position vocabulary that may be explained together with RECNO in the data-model section.

This section should avoid overclaiming edge behavior until evidence review attaches runtime proof. Examples needing proof include beginning-of-file behavior, end-of-file behavior, deleted-record visibility, filtered traversal, and interaction with active order.

## Record-position commands: GO, GOTO, TOP, BOTTOM, and SKIP

GO and GOTO belong to the record-position family. They should be explained as commands that change the current record context. TOP and BOTTOM describe movement to the first or last record in the current traversal context. SKIP describes relative movement.

A conservative explanation is:

- GO/GOTO changes where the current record pointer is positioned.
- TOP moves to the start of the current traversal.
- BOTTOM moves to the end of the current traversal.
- SKIP moves forward or backward relative to the current record.

Important evidence boundary:
- If an active order or filter changes traversal order, that belongs to the ordering/filtering evidence path.
- This section may mention that traversal context matters, but it should not define index behavior.
- SET ORDER and tag behavior belong to the indexing section.

## Search commands: SEEK, FIND, LOCATE, and CONTINUE

Search commands help the user reach records that match some condition or value.

This section should distinguish two broad search ideas:

1. Key-style search:
   - SEEK and FIND may depend on index/order context or key-style lookup behavior.
   - Exact semantics require evidence review and runtime proof.

2. Predicate-style search:
   - LOCATE searches for records matching a condition.
   - CONTINUE resumes a prior locate-style search where supported.

This draft should not collapse SEEK, FIND, and LOCATE into the same operation. They may share the user goal of finding records, but they can travel through different implementation and evidence paths.

The final prose should be conservative until PIP-003 and later command crosswalks attach:
- HELP evidence for syntax and user-facing explanation.
- Source evidence for handler and implementation ownership.
- Runtime proof for behavior in open-table contexts.
- Future SYSARGS and SYSMSG metadata for arguments and messages.

## Scan and iteration commands

SCAN represents a record-iteration concept. It belongs in this section because it connects navigation and repeated record processing.

A conservative explanation is:

- SCAN walks a set of records according to the current command context.
- It may use a condition, scope, or current traversal state depending on command syntax and runtime implementation.
- Final details should wait for command evidence and runtime examples.

SCAN should also be cross-referenced with later expression and predicate sections, because scanning often depends on conditions or expressions.

## Display and browsing commands: LIST, SMARTLIST, BROWSE, and BROWSER

Display and browsing commands present record or table state.

LIST is a key display/proof surface because it can show the actual traversal order. This is especially important when testing whether an order or tag is really affecting traversal.

SMARTLIST should be treated as a smarter or higher-level display surface until evidence review defines its exact contract.

BROWSE and BROWSER belong to the browsing/projection family. They help inspect data interactively or through a richer display. They should not be treated as the owner of table storage, record identity, relation semantics, or command truth.

A safe ownership rule is:

- DbArea owns table and record state.
- Index/order systems influence traversal where active.
- Expression/predicate systems decide conditions where used.
- Browser and list surfaces display or project the resulting state.

## Projection versus ownership

Projection surfaces are useful because they make database state visible. But they do not define the database state.

LIST, SMARTLIST, BROWSE, and BROWSER may show records, fields, order, and current context. However, their output must be interpreted through the subsystem that owns the underlying state.

Examples:
- A LIST result can reveal traversal order, but the index/order subsystem owns ordering behavior.
- A browser can show a table, but DbArea owns the table state.
- A relation-aware browser can show connected rows, but the relation and tuple systems own relation traversal semantics.
- A memo field may display differently depending on memo backend attachment, but MemoManager owns memo payload lifecycle.

This section should preserve that boundary so user-facing prose does not accidentally make projection surfaces the authority for runtime behavior.

## Index boundary note

This section may mention that some navigation and search behavior can be affected by the active order, index, or tag. It must not attempt to define the full indexing model.

The indexing section owns:
- SET ORDER
- tags
- logical order
- CDX/CNX behavior
- LMDB backend details
- SEEK/FIND behavior that depends on active order
- SET-family canonicalization concerns

This section should only say that traversal and key-style search may depend on context, and that index-specific behavior is explained later.

## Compatibility and draft-evidence cautions

Compatibility evidence can be useful for explaining lineage. It should not be treated as proof of current DotTalk behavior.

Generated command draft pages are also not final prose. They are useful evidence artifacts for manualgen review, not polished command documentation.

Therefore, before this section becomes a reviewed candidate, PIP-003 should check that:
- compatibility-only material is not presented as current runtime behavior;
- generated command pages are not treated as final authority;
- current DotTalk evidence items are separated from concept and compatibility evidence;
- canary behavior is either avoided or explicitly labeled.

## Boundary

- prose draft fill only
- no reviewed candidate generated
- no final prose promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion


<!-- END SECTION: sections\navigation_browsing_and_search.md -->

---

<!-- BEGIN SECTION: sections\promoted_draft_review_header_normalization_and_publication_readiness.md -->

# Promoted Draft Review, Header Normalization, and Publication Readiness




Pippets used:
- PIP-001 Target Selection
- MDO-196 Target Selection
- MDO-197 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches promoted draft review, review packet practice, candidate note cleanup, reviewed candidate status cleanup, header normalization, path repair, canonical path verification, table of contents checks, section order checks, final publication boundaries, generated command page no deletion, and no mutation safety.
- Do not send this directly to generic PIP-003.
- Run a slow-lane promoted-draft readiness review first.

Evidence tokens under review:
- promoted draft
- review packet
- inspection packet
- human review
- candidate note
- reviewed candidate status
- header normalization
- publication readiness
- final publication
- table of contents
- section order
- section count
- path repair
- canonical path
- slug
- generated command pages
- no deletion
- HELP
- CMDHELPCHK
- metadata
- SelfDoc
- manualgen
- PIP
- report-only
- no mutation

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Promoted draft workspace assembly is not final publication.
- Candidate note headers in promoted draft sections must not be normalized casually one section at a time.
- Reviewed candidate status blocks in promoted draft sections must be handled by a systematic promoted-draft header normalization pass.
- Header normalization must not rewrite substantive prose without explicit review.
- Path and slug verification must use canonical section ids and inspectable files.
- Table of contents and section order must be verified against actual section files.
- Review packets should remain the preferred human-inspection surface before authorization.
- Generated command pages and evidence artifacts must not be deleted during publication-readiness work.
- Publication readiness may recommend repairs, but it should not silently publish or normalize.

## Purpose of this section

This section explains how the Developer Manual should review a promoted draft workspace, prepare for header normalization, and separate publication readiness from final publication.

It follows the Command Reference Assembly section because that section exposed a concrete promoted-section path problem. MDO-194 reported a successful promotion, but MDO-194A was needed to repair and verify the canonical promoted section path. That experience proves that status reports are not enough. A promoted draft must be inspectable, path-checked, section-counted, and reviewed as a workspace.

The goal is not to publish the manual. The goal is to define a safe review lane between promoted draft assembly and any later final publication step.

## Promoted draft workspace

A promoted draft workspace is an assembled manual draft.

It may contain:
- reviewed candidate prose copied into section files;
- candidate note headers;
- reviewed candidate status blocks;
- promoted section paths;
- generated section ordering;
- table of contents material or future table of contents inputs;
- evidence of promotion history;
- known draft-workspace debt.

Safe wording:
- A promoted draft is not final publication.
- A promoted draft is a reviewable workspace.
- A promoted draft can contain review artifacts that are useful during assembly but inappropriate for final publication.
- Final publication should require a later explicit gate.

## Inspectable files

The user should be able to inspect the actual prose.

Inspectable files matter because status reports can be green while path or filename issues remain. MDO-194A showed why the canonical path must be checked directly.

Safe wording:
- Review must include actual section files, not only status CSVs.
- Canonical paths should be opened or tested directly.
- A readable section file is stronger evidence than a report that only says a section exists.
- Review packets should make prose easy to inspect before authorization.

## Review packets and inspection packets

Review packets are human-inspection surfaces.

They should provide:
- the prose to read;
- a checklist;
- known canaries;
- a summary;
- a hold, repair, or accept decision point.

Safe wording:
- Review packets should remain the preferred human-inspection surface before authorization.
- Review packets should not create human decisions by themselves.
- Review packets should not promote.
- Review packets should help the reviewer decide HOLD, REPAIR, or ACCEPT_FOR_PROMOTION.

## Candidate note headers

Candidate note headers are useful during review.

They preserve:
- origin of the candidate;
- promotion-gate provenance;
- review warning;
- draft status.

But candidate note headers can become clutter in a final manual.

Safe wording:
- Candidate note headers in promoted draft sections must not be normalized casually one section at a time.
- Candidate note headers should be handled by a systematic promoted-draft header normalization pass.
- Candidate note headers should not be removed until the manual has a defined normalization rule.
- Header normalization should preserve provenance in reports even if public-facing prose is cleaned later.

## Reviewed candidate status blocks

Reviewed candidate status blocks are also useful during review.

They say that a section passed a reviewed-candidate lane, but they are not necessarily final publication text.

Safe wording:
- Reviewed status blocks should not be removed casually one section at a time.
- Reviewed status blocks should be recorded in normalization reports if removed from public-facing prose.
- A section can be accepted for promoted draft assembly without being final-publication-ready.

## Header normalization

Header normalization is the process of turning review-oriented section headers into final-manual section headers.

Header normalization may include:
- removing Candidate note blocks from public-facing copies;
- preserving provenance in reports;
- standardizing title and section metadata;
- checking section order and table of contents alignment.

Safe wording:
- Header normalization must not rewrite substantive prose without explicit review.
- Header normalization must be systematic.
- Header normalization should report every section changed.
- Header normalization should preserve originals or backups.
- Header normalization is not final publication by itself.

## Substantive prose boundary

Header normalization should not become stealth editing.

Substantive prose includes:
- conceptual explanations;
- evidence doctrine;
- command behavior claims;
- canary language;
- examples;
- scope boundaries;
- future metadata feeder descriptions.

Safe wording:
- Header normalization may clean review headers.
- Header normalization should not change substantive prose without explicit authorization.
- Substantive repairs should go through a repair/review path, not a normalization pass.
- If a header-normalization script changes body prose, that is a failure unless explicitly authorized.

## Path repair and canonical path verification

Promoted drafts should verify canonical paths.

Path repair and canonical path verification should check:
- section id;
- expected filename;
- actual file existence;
- readable content;
- hash match with source candidate where expected;
- legacy or non-canonical path leftovers;
- duplicate section files.

Safe wording:
- Path and slug verification must use canonical section ids and inspectable files.
- A status report is not enough if the file cannot be opened.
- Path repair should preserve evidence and avoid deletion unless separately authorized.
- Canonical path verification should be part of publication-readiness review.

## Slugs and section ids

A slug or filename is not just formatting. It controls whether humans and scripts can find the section.

Safe wording:
- Slugs should be derived from reviewed section ids.
- Slug changes should be reported.
- Non-canonical slugs should be flagged before publication.
- Slug repair should preserve old evidence until cleanup is explicitly authorized.

## Section count

Section count is a basic workspace integrity check.

A promoted draft review should report:
- total section files;
- expected required sections;
- missing required sections;
- extra or duplicate sections;
- sections with candidate headers;
- sections with reviewed-status blocks;
- sections needing header normalization.

Safe wording:
- Section count is a workspace health check.
- Section count does not prove prose quality.
- Section count should be combined with inspectable file checks.

## Section order

Section order matters because the manual should read coherently.

A section-order review should check:
- onboarding and orientation before deep internals;
- data model before navigation;
- navigation before indexing;
- indexing before expressions where appropriate;
- command surface before command reference;
- evidence doctrine before publication readiness;
- appendices or reference sections after concepts.

Safe wording:
- Section order should be explicit.
- Section order should be reviewable.
- Section order should not be inferred only from directory listing order.
- A future table of contents or manifest should own final order.

## Table of contents

A table of contents is the public navigation surface for the manual.

Publication readiness should eventually verify:
- every TOC entry has a section file;
- every required section file appears in the TOC or is intentionally excluded;
- titles match;
- order is intentional;
- section ids and slugs are stable;
- no draft-only sections appear accidentally;
- no evidence-only reports appear as public manual chapters.

Safe wording:
- Table of contents checks belong to publication readiness.
- TOC readiness is not the same as final publication.
- TOC generation should not delete source sections.
- TOC generation should preserve auditability.

## Final publication boundary

Final publication is separate from promoted draft workspace assembly.

Safe wording:
- Final publication requires explicit authorization.
- Promotion into a draft workspace is not final publication.
- Header normalization is not final publication.
- TOC readiness is not final publication.
- Publication readiness may recommend repairs, but it should not silently publish or normalize.

## Generated command pages and evidence artifacts

Generated command pages and evidence artifacts remain protected.

Publication-readiness work must not delete:
- generated command pages;
- HELP evidence;
- metadata reports;
- CMDHELPCHK reports;
- review packets;
- PIP reports;
- source evidence reports;
- canary reports;
- promoted draft history.

Safe wording:
- Generated command pages and evidence artifacts must not be deleted during publication-readiness work.
- Cleanup recommendations may be reported.
- Deletion or mutation requires a separate explicit authorization path.

## HELP, CMDHELPCHK, and metadata boundaries

Publication-readiness review may read HELP, CMDHELPCHK, and metadata evidence.

It must not mutate:
- HELP;
- META;
- CMDHELPCHK;
- catalogs;
- source;
- runtime data;
- production SelfDoc metadata.

Safe wording:
- HELP explains.
- CMDHELPCHK validates.
- Metadata organizes.
- Manualgen publication-readiness review remains report-only.
- No mutation occurs without explicit authorization.

## Report-only publication readiness

Publication readiness should start as report-only.

Report-only readiness can produce:
- section inventory;
- candidate header inventory;
- reviewed status inventory;
- canonical path check;
- slug check;
- table of contents check;
- section order check;
- review packet inventory;
- unresolved canary inventory;
- publication blocker list;
- recommended repairs.

Safe wording:
- Report-only readiness is safe by default.
- Report-only readiness can recommend repair.
- Report-only readiness must not silently normalize, publish, or delete evidence.

## Human review

Human review remains the decision point.

Human review should decide:
- HOLD;
- REPAIR;
- ACCEPT_FOR_PROMOTION;
- READY_FOR_HEADER_NORMALIZATION;
- READY_FOR_PUBLICATION_REVIEW;
- NOT_READY_FOR_PUBLICATION.

Safe wording:
- Human review should inspect prose, not only reports.
- Human review should be recorded.
- Authorization should follow inspection.
- Publication should not be implied by prior section acceptance.

<!-- MDO-303E removed process scaffold heading 'Slow-lane canary tracking names' from reader clean copy; preserved in reports. -->
<!-- MDO-303E removed process scaffold heading 'Review notes before PIP-003' from reader clean copy; preserved in reports. -->
## Boundary

- prose draft fill only
- slow-lane review still required
- no reviewed candidate generated
- no final prose promotion
- no final publication
- no header normalization
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion


<!-- END SECTION: sections\promoted_draft_review_header_normalization_and_publication_readiness.md -->

---

<!-- BEGIN SECTION: sections\relations_and_tuple_views.md -->

# Relations and Tuple Views

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [CMDREL](../../command_reference_v1/commands/cmdrel.md)
- [REL](../../command_reference_v1/commands/rel.md)
- [REL ENUM](../../command_reference_v1/commands/rel_enum.md) - aliases: REL_ENUM
- [REL_REFRESH](../../command_reference_v1/commands/rel_refresh.md)
- [RELATION](../../command_reference_v1/commands/relation.md)
- [RELATIONS](../../command_reference_v1/commands/relations.md)
- [TUPEXPORT](../../command_reference_v1/commands/tupexport.md)
- [TUPLE](../../command_reference_v1/commands/tuple.md)
- [TUPLEDELTA](../../command_reference_v1/commands/tupledelta.md)
- [TUPTALK](../../command_reference_v1/commands/tuptalk.md)
- [TUPVALIDATE](../../command_reference_v1/commands/tupvalidate.md)
<!-- BEGIN SECTION: sections\runtime_evidence_source_verification_and_canary_closure.md -->

# Runtime Evidence, Source Verification, and Canary Closure




Pippets used:
- PIP-001 Target Selection
- MDO-180 Target Selection
- MDO-181 Draft Fill

Evidence boundary:
- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

Slow-lane warning:
- This section touches runtime proof, source verification, canary lifecycle, legacy evidence cautions, report-only boundaries, and no-mutation safety.
- Do not send this directly to generic PIP-003.
- Run a slow-lane runtime/source/canary review first.

Evidence tokens under review:
- runtime
- source
- SOURCE
- SOURCE_FACT
- SelfDoc
- manualgen
- PIP
- canary
- canary ledger
- smoke test
- shakedown
- regression
- proof
- verification
- evidence
- build
- release
- HELP
- CMDHELPCHK
- metadata
- crosswalk
- report-only
- no mutation

Draft notes:
- This is conservative manual prose for slow-lane evidence review.
- Runtime proof should include concrete commands, output, build context, and date where possible.
- Source verification should identify implementation ownership and should not be demoted to sidecar evidence.
- Canary rows remain visible until closed with evidence.
- Closing a canary requires current evidence, not optimism or old design intent.
- Legacy documents may be useful context but should not be treated as current fact without verification.
- Manualgen and SelfDoc remain report-only unless explicitly authorized.
- HELP, CMDHELPCHK, and metadata can guide review but cannot close runtime or source canaries by themselves.
- Evidence packages should not mutate HELP, META, CMDHELPCHK, catalogs, source, or runtime data during manual draft assembly.

## Purpose of this section

This section explains how the Developer Manual should use runtime evidence, source verification, and canary closure.

It follows the HELP, Metadata, CMDHELPCHK, and Manualgen Alignment section because that section established the authority doctrine. This section operationalizes that doctrine into daily engineering practice: how runtime evidence is captured, how source verification is attached, how canaries remain visible, and how canaries are closed only with evidence.

The goal is not to turn every manual claim into a test case. The goal is to prevent unsupported claims from becoming permanent prose and to make sure important uncertainties remain visible until they are resolved.

## Evidence doctrine in practice

The working doctrine remains:

- Runtime proves behavior.
- Source defines implementation and subsystem ownership.
- HELP explains.
- Metadata organizes.
- CMDHELPCHK validates.
- SelfDoc preserves provenance.
- Manualgen assembles.

In practice, this means a claim may need several evidence lanes before it is safe for final manual prose.

Examples:
- A command behavior claim needs runtime evidence.
- An implementation ownership claim needs source verification.
- A HELP wording claim needs HELP evidence.
- A metadata alignment claim needs metadata evidence.
- A consistency claim may need CMDHELPCHK evidence.
- A provenance claim needs SelfDoc or manualgen run evidence.

## Runtime evidence

Runtime evidence proves observed behavior.

Useful runtime evidence includes:
- exact commands that were run;
- exact output or relevant output excerpts;
- build configuration;
- release/debug mode;
- dataset or workspace used;
- command path or script path;
- date and session context;
- pass/fail result;
- any unexpected warnings or canary behavior.

Safe wording:
- Runtime evidence proves what was observed in that run.
- Runtime evidence should be labeled with enough context to reproduce or understand it.
- Runtime evidence does not automatically define implementation ownership.
- Runtime evidence can close behavior canaries when the observed behavior is current and relevant.

Examples of runtime evidence lanes:
- smoke test;
- shakedown;
- regression run;
- build output;
- release verification;
- manual command transcript;
- script output;
- comparison before and after a repair.

## Source verification

Source verification attaches implementation and ownership evidence.

Useful source verification includes:
- source file path;
- header path;
- function or class name;
- source-comment contract;
- source-miner report;
- SOURCE_FACT row;
- SelfDoc source-comment evidence;
- handler or parser ownership note;
- subsystem boundary note.

Safe wording:
- Source defines implementation and subsystem ownership.
- Source verification should identify the relevant file or owner where possible.
- Source may verify why runtime behavior occurs.
- Source is not merely a sidecar; it is authority for implementation structure.

Source verification is especially important for claims about:
- parser dispatch;
- command handlers;
- storage ownership;
- relation traversal ownership;
- expression evaluation ownership;
- memo payload lifecycle;
- message emission;
- backend boundaries;
- generated/help/metadata alignment.

## Runtime and source together

Runtime and source answer different questions.

Runtime answers:
- What happened in this run?
- What behavior can be observed?
- Did the smoke/shakedown/regression pass?

Source answers:
- Which subsystem owns the behavior?
- Which implementation path handles it?
- Is the observed behavior intentional, scaffold leakage, compatibility behavior, or a bug?

Safe wording:
- Runtime proves behavior.
- Source defines ownership.
- A strong manual claim often needs both.
- HELP, metadata, and CMDHELPCHK can guide the search, but they do not replace runtime/source evidence.

## Canary lifecycle

A canary is a visible uncertainty, risk, or proof-sensitive behavior that must not disappear silently.

A canary can be:
- open;
- deferred;
- narrowed;
- reproduced;
- partially closed;
- closed with evidence;
- superseded by a better canary;
- converted into an issue or work item.

A canary should not be:
- hidden because it is inconvenient;
- closed because the expected behavior seems obvious;
- closed because old design intent says it should work;
- closed using HELP, metadata, or CMDHELPCHK alone when runtime/source proof is required.

## Opening a canary

A canary should be opened when evidence shows a behavior, mismatch, ambiguity, or risk that could affect manual accuracy or project correctness.

Good canary records include:
- short name;
- observed behavior;
- evidence source;
- date or session;
- affected subsystem;
- proof needed for closure;
- current status;
- next recommended action.

Examples:
- SET ORDER active tag reporting.
- x64 workspace ERSATZ load reporting.
- MIN/MAX command/function ambiguity.
- AGGS internal family owner exposure.
- memo backend attach on workspace open.
- generated command page duplicate or slug collision.

## Keeping canaries visible

Canaries remain visible until closed with evidence.

Visibility matters because older project documents, generated reports, and runtime sessions can overlap. A canary keeps the manual honest by saying: this claim is not ready for final prose, or this behavior needs proof-sensitive wording.

Safe wording:
- Canary rows remain visible until closed with evidence.
- Canaries can be deferred, but deferred does not mean resolved.
- Canaries can be narrowed when evidence shows only part of the risk remains.
- Canaries should be carried forward in review reports until closed, superseded, or explicitly transferred.

## Closing a canary

Closing a canary requires current evidence.

Closure evidence may include:
- runtime run showing the behavior;
- source verification showing the implementation path;
- regression test output;
- smoke test result;
- CMDHELPCHK report when the canary is about HELP/catalog consistency;
- metadata readback when the canary is about metadata coverage;
- manualgen report when the canary is about assembly output;
- explicit human decision when the canary is a policy or surface decision.

Safe wording:
- Closing a canary requires evidence.
- The closure record should name the evidence.
- The closure record should preserve enough context to audit the decision later.
- Old design intent is not closure evidence by itself.

## Legacy documents

Legacy documents are useful context.

They may contain:
- old design intent;
- old architecture notes;
- historical problems;
- early terminology;
- superseded assumptions;
- useful examples;
- project memory.

But legacy documents should not be treated as current fact without verification.

Safe wording:
- Old documents remember.
- Recent summaries steer.
- SelfDoc verifies.
- Runtime proves.
- Source defines.
- Manuals explain.

Legacy evidence should be labeled when it is used:
- historical context;
- design intent;
- superseded note;
- unverified claim;
- candidate canary;
- verified current behavior.

## Smoke tests, shakedowns, regressions, builds, and releases

Different runtime evidence lanes serve different purposes.

Smoke test:
- quick proof that a feature or path starts and behaves basically as expected.

Shakedown:
- broader exploratory runtime evidence, often with manual commands and transcript notes.

Regression:
- evidence that a previously fixed or expected behavior still works.

Build:
- evidence that code compiles and links in a given configuration.

Release:
- evidence attached to a release-ready state, usually after build and smoke checks.

Safe wording:
- Build success is not behavior proof.
- Smoke success is limited behavior proof.
- Shakedown is useful runtime evidence but should be scoped.
- Regression evidence is strong for previously known behavior.
- Release evidence should identify build configuration and major checks.

## HELP, CMDHELPCHK, and metadata in evidence practice

HELP, CMDHELPCHK, and metadata are powerful review guides.

They can:
- identify expected command vocabulary;
- expose missing help or command topics;
- organize arguments, messages, variants, and functions;
- detect catalog/help drift;
- point to canaries;
- guide runtime/source verification.

They cannot by themselves:
- prove runtime behavior;
- define implementation ownership;
- close runtime canaries;
- close source ownership canaries.

Safe wording:
- HELP explains.
- CMDHELPCHK validates.
- Metadata organizes.
- Runtime/source evidence closes runtime/source canaries.

## SelfDoc and manualgen evidence

SelfDoc preserves provenance. Manualgen assembles.

SelfDoc evidence may include:
- source-comment contract reports;
- SOURCE_FACT rows;
- source inventory;
- classifier reports;
- diagram reports;
- canary ledgers;
- provenance notes.

Manualgen evidence may include:
- pippet run records;
- target selection reports;
- draft fill reports;
- slow-lane reviews;
- PIP-003 evidence gates;
- PIP-004 reviewed candidates;
- PIP-005 human decisions;
- PIP-006 promotion patches;
- promoted draft workspaces.

Safe wording:
- SelfDoc and manualgen are evidence systems.
- They default to report-only.
- They must not mutate HELP, META, CMDHELPCHK, catalogs, source, or runtime data during manual draft assembly.
- Production mutation requires explicit authorization.

## Evidence crosswalks

Crosswalks connect evidence lanes without collapsing them.

Useful crosswalks include:
- runtime transcript to canary row;
- canary row to source file;
- source file to SOURCE_FACT;
- HELP topic to command identity;
- command identity to SYSCMD;
- function claim to SYSFUNC;
- diagnostic claim to SYSMSG;
- argument claim to SYSARGS;
- alias/variant claim to SYSENTVAR;
- manual section to evidence tokens;
- PIP report to promoted draft section.

Safe wording:
- Crosswalks preserve traceability.
- Crosswalks can be candidate, partial, or verified.
- Crosswalks should not pretend a weak source is strong evidence.
- Crosswalks help future metadata feeders absorb temporary evidence.

<!-- MDO-303E removed process scaffold heading 'Future META alignment' from reader clean copy; preserved in reports. -->
## No-mutation safety

Evidence packages should not mutate production artifacts during manual draft assembly.

Default boundary:
- no generated command page deletion;
- no HELP mutation;
- no META mutation;
- no CMDHELPCHK mutation;
- no catalog apply;
- no source edits;
- no runtime data mutation;
- no production SelfDoc metadata promotion;
- no final publication.

Report-only work is the default.

<!-- MDO-303E removed process scaffold heading 'Slow-lane canary tracking names' from reader clean copy; preserved in reports. -->
## Canary non-disappearance boundary

This exact review anchor is intentionally retained for slow-lane evidence review:

- A canary may be deferred/narrowed/reproduced/closed, but should not disappear silently.

The anchor is not final user-facing prose by itself. It preserves the boundary already described in this section: canaries remain visible until closed, superseded, transferred, or explicitly deferred with evidence.
<!-- MDO-303E removed process scaffold heading 'Review notes before PIP-003' from reader clean copy; preserved in reports. -->
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



<!-- END SECTION: sections\runtime_evidence_source_verification_and_canary_closure.md -->

---

<!-- BEGIN SECTION: sections\scripting_and_control_flow.md -->

# Scripting and Control Flow

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [DO](../../command_reference_v1/commands/do.md)
- [ELSE](../../command_reference_v1/commands/else.md)
- [ENDIF](../../command_reference_v1/commands/endif.md)
- [ENDLOOP](../../command_reference_v1/commands/endloop.md)
- [ENDSCAN](../../command_reference_v1/commands/endscan.md)
- [ENDUNTIL](../../command_reference_v1/commands/enduntil.md)
- [ENDWHILE](../../command_reference_v1/commands/endwhile.md)
- [IF](../../command_reference_v1/commands/if.md)
- [LOOP](../../command_reference_v1/commands/loop.md)
- [LOOP_BUFFER](../../command_reference_v1/commands/loop_buffer.md)
- [LOOPS](../../command_reference_v1/commands/loops.md)
- [RUN](../../command_reference_v1/commands/run.md)
- [SCAN](../../command_reference_v1/commands/scan.md)
- [SCAN_BUFFER](../../command_reference_v1/commands/scan_buffer.md)
- [SCRIPT](../../command_reference_v1/commands/script.md)
- [SHUTDOWN](../../command_reference_v1/commands/shutdown.md)
- [UNTIL](../../command_reference_v1/commands/until.md)
- [UNTIL_BUFFER](../../command_reference_v1/commands/until_buffer.md)
- [WHILE](../../command_reference_v1/commands/while.md)
- [WHILE_BUFFER](../../command_reference_v1/commands/while_buffer.md)
<!-- BEGIN SECTION: sections\system_shell_and_files.md -->

# System, Shell, and Files

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [CLOSE](../../command_reference_v1/commands/close.md)
- [DIR](../../command_reference_v1/commands/dir.md)
- [DUMP](../../command_reference_v1/commands/dump.md)
- [ERASE](../../command_reference_v1/commands/erase.md)
- [INIT](../../command_reference_v1/commands/init.md)
- [PSHELL](../../command_reference_v1/commands/pshell.md)
- [SECHO](../../command_reference_v1/commands/secho.md)
- [SFTP](../../command_reference_v1/commands/sftp.md)
- [SHELLO](../../command_reference_v1/commands/shello.md)
- [SHOWINI](../../command_reference_v1/commands/showini.md)
- [WEB](../../command_reference_v1/commands/web.md)
- [ZIP](../../command_reference_v1/commands/zip.md)
<!-- BEGIN SECTION: sections\tables_records_and_data_editing.md -->

# Tables, Records, and Data Editing

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [APPEND](../../command_reference_v1/commands/append.md)
- [COPY](../../command_reference_v1/commands/copy.md)
- [CREATE](../../command_reference_v1/commands/create.md)
- [DELETE](../../command_reference_v1/commands/delete.md)
- [EDIT](../../command_reference_v1/commands/edit.md)
- [PACK](../../command_reference_v1/commands/pack.md)
- [RECALL](../../command_reference_v1/commands/recall.md)
- [REPLACE](../../command_reference_v1/commands/replace.md)
- [TURBOPACK](../../command_reference_v1/commands/turbopack.md)
- [UNDELETE](../../command_reference_v1/commands/undelete.md)
- [ZAP](../../command_reference_v1/commands/zap.md)
<!-- BEGIN SECTION: sections\tables_records_and_data_model.md -->

# Tables, Records, and Data Model



Pippets used:
- PIP-004 Reviewed Candidate Pippet
- PIP-003 Evidence Review Pippet
- PIP-011 Source Reference Inventory Pippet

Evidence lineage:
- MDO-120 original draft
- MDO-128 source-lane repaired draft
- MDO-133 field-note drift repaired v4 draft
- MDO-134 evidence review gate

Repair reason:
- MDO-121 detected evidence/prose drift in the first Tables, Records, and Data Model draft.
- MDO-128 recovers or rebuilds the repair plan, then generates the source-lane repaired draft.

Evidence class:
- Repaired draft assembled from MDO-120 draft intent, MDO-121 evidence gate where available, source-lane crosswalk or recovered repair plan, and registry v4.
- Runtime behavior remains the source of truth.
- This draft does not mutate HELP, META, CMDHELPCHK, catalogs, source files, or production SelfDoc metadata.

## Purpose of this section

This section explains the table, record, field, schema, memo, and record-view vocabulary that later manual sections depend on. It follows the Getting Started and Workspaces sections: the reader should already know how the system starts, how areas frame context, and why the manual carries evidence boundaries.

The repaired draft is deliberately conservative. It does not assume every linked evidence page is the same kind of source. Some pages support current DotTalk command prose, some are educational concepts, some are compatibility references, and some need additional review before being described as runtime behavior.

## Source-lane rule for this section

A DOTREF/current evidence item may support command-facing prose after evidence review. An EDREF concept item explains vocabulary or teaching structure. A FOXREF compatibility item must be gated before being described as current runtime behavior. SQL or shell reference lanes should be routed to bridge or appendix material.

This rule prevents concept pages such as TABLE_RECORD_FIELD from being documented as if they were ordinary runtime commands, and prevents compatibility-only material from being promoted as current DotTalk behavior without proof.

## Tables, records, and fields

The core data model starts with tables, records, and fields. TABLE supports table-level vocabulary. RECORD and RECNO support record identity and record-position vocabulary. FIELDS and FIELDMGR support field-level vocabulary and field-management evidence.

TABLE_RECORD_FIELD is concept evidence for the relationship among tables, records, and fields. It should explain the model, not be presented as a user command unless a separate runtime command page proves that behavior.

## Schema and DDL

SCHEMA and DDL belong together in this section because they describe structure. SCHEMA supports table-structure vocabulary. DDL supports definition-level or schema-language vocabulary. This draft keeps DDL wording structural and avoids claiming specific DDL behavior until command evidence and runtime examples are reviewed.

## Record views and memo fields

RECORDVIEW supports record-oriented presentation or view vocabulary. MEMO supports memo-field discussion. Memo behavior is a sensitive storage and persistence topic, so final prose should distinguish visible memo fields from backend memo storage and should not overclaim persistence details without runtime evidence.

## Work areas as context, not the main topic

WORKAREA may appear in the evidence set, but the main explanation of work areas belongs in the already promoted Workspaces section. Here, WORKAREA should be used only to remind the reader that table and record commands operate in a current area/session context.

## Compatibility and bridge material

Compatibility evidence appears in this section and must be handled cautiously:

- DBAREAS: appears as compatibility evidence. Do not promote it as current DotTalk behavior without runtime proof.

Compatibility evidence can support historical or compatibility notes, but it should not be promoted as current DotTalk behavior without runtime proof.

## Command and concept map

- DBAREA [DOT_COMMAND_EVIDENCE / DOTREF]: is current/DotTalk reference evidence and may support command prose after evidence review.
- DBAREAS [COMPATIBILITY_EVIDENCE / FOXREF]: appears as compatibility evidence. Do not promote it as current DotTalk behavior without runtime proof.
- DDL [DOT_COMMAND_EVIDENCE / DOTREF]: describes schema-definition language or definition-level behavior. Treat it as structural doctrine, not a simple record command.
- FIELDMGR [DOT_COMMAND_EVIDENCE / DOTREF]: belongs to field-management evidence. Use it to discuss how field metadata and field-level operations are organized, not as ordinary user prose without review.
- FIELDS [DOT_COMMAND_EVIDENCE / DOTREF]: supports field-list and field-description discussion.
- MEMO [DOT_COMMAND_EVIDENCE / DOTREF]: supports memo/large-object field discussion. Keep memo storage details conservative unless command evidence or runtime transcripts prove more.
- RECNO [DOT_COMMAND_EVIDENCE / DOTREF]: supports record-position vocabulary.
- RECORD [DOT_COMMAND_EVIDENCE / DOTREF]: supports current-record or record-identity vocabulary.
- RECORDVIEW [DOT_COMMAND_EVIDENCE / DOTREF]: supports record-oriented presentation or viewing vocabulary.
- SCHEMA [DOT_COMMAND_EVIDENCE / DOTREF]: supports table-structure and schema vocabulary.
- TABLE [DOT_COMMAND_EVIDENCE / DOTREF]: supports table-level vocabulary.
- TABLE_RECORD_FIELD [CONCEPT_EVIDENCE / EDREF_CONCEPT]: is concept evidence for the relationship among tables, records, and fields. Do not treat it as a runtime command unless separately proven.
- WORKAREA [CONCEPT_EVIDENCE / EDREF_CONCEPT]: is concept or workspace-adjacent evidence. Mention only as context and keep detailed work-area behavior in the Workspaces section.

## What this section should not do yet

- Do not document unrelated commands from the first draft that are not in the linked evidence set.
- Do not treat EDREF concept pages as ordinary runtime commands.
- Do not treat FOXREF compatibility entries as current DotTalk behavior without runtime evidence.
- Do not add examples for mutating or destructive behavior until syntax and runtime transcripts are sampled.
- Do not move detailed workspace/session behavior out of the Workspaces section.

## Review notes before candidate generation

- Rerun PIP-003 evidence review on this repaired draft.
- Confirm the drift rows from MDO-121 are cleared or intentionally explained.
- Confirm the command/concept split is acceptable.
- Confirm MEMO wording does not overclaim backend persistence.
- Confirm DDL wording stays structural until examples are proven.

## Boundary

- repaired prose draft only
- no reviewed candidate generated
- no final prose promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits
- no production SelfDoc metadata promotion

<!-- END SECTION: sections\tables_records_and_data_model.md -->

---

<!-- BEGIN SECTION: sections\transactions_locking_and_buffering.md -->

# Transactions, Locking, and Buffering

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [BUFFERING](../../command_reference_v1/commands/buffering.md)
- [COMMIT](../../command_reference_v1/commands/commit.md)
- [LOCK](../../command_reference_v1/commands/lock.md)
- [ROLLBACK](../../command_reference_v1/commands/rollback.md)
- [TABLE_BUFFER](../../command_reference_v1/commands/table_buffer.md)
- [UNLOCK](../../command_reference_v1/commands/unlock.md)
<!-- BEGIN SECTION: sections\workspaces_areas_and_session_state.md -->

# Workspaces, Areas, and Session State

Status: PROMOTED_TO_MANUAL_DRAFT / REVIEW_REQUIRED

Evidence class:
- Reviewed prose candidate assembled from MDO-100 draft prose and MDO-101 evidence review.
- Runtime behavior remains the source of truth.
- This candidate is not final manual prose.
- This candidate does not mutate HELP, META, CMDHELPCHK, catalogs, source files, or production SelfDoc metadata.

Promotion gate:
- READY_FOR_HUMAN_PROMOTION_REVIEW

## Overview

A DotTalk++ session is organized around live table context. A table is opened into a work area, one work area is current, and many commands operate against that current area unless they are given a more specific target. The workspace layer then gives the session a way to inspect, close, save, load, or restore a larger collection of open areas and related session state.

This section introduces that session model without treating it as a storage-format chapter. Work areas, selected areas, and workspaces are live runtime concepts. They are the foundation for later sections on browsing, relations, tuple views, indexing, import/export, and SelfDoc/manualgen evidence review.

## The core context loop

The smallest useful context loop is: open a table, confirm where it is, and choose which area commands should use.

- USE opens a table into live session context.
- AREA reports the current work-area state.
- SELECT changes or reports the active work area.

Those three commands should be explained together. USE makes table data available to the command surface. AREA helps the user confirm the current context. SELECT helps the user choose the active area when more than one table is open.

## USE opens table context

USE is the command that brings a table into the live DotTalk++ session. In this section, describe USE at the command-surface level: it opens a table so other commands can operate on it. Avoid turning USE into a backend-storage explanation here. Physical table layout, index backends, memo payloads, and storage bridge details belong in later developer sections.

Once a table is open, other commands can reason from that context. Navigation commands, display commands, relation tools, tuple views, and workspace operations all depend on knowing which areas are live and which one is current.

## AREA and SELECT keep the current context visible

AREA and SELECT are complementary. AREA is primarily a context report. SELECT is the command used to choose or report the current work area. When a session has multiple open tables, these two commands help keep the command surface predictable.

This matters because DotTalk++ preserves classic xBase-style working context. The current area affects which table many commands see by default. Clear area state also matters for relation browsing, tuple views, and workspace save/load behavior.

## WORKSPACE organizes the whole live session

WORKSPACE is the higher-level session organizer. It is about the collection of open work areas and related live session state, not the physical storage format of a table. A user can use WORKSPACE to inspect open areas and, where supported by the command surface, open groups of tables, close areas, and save or load workspace/session state.

Manual prose should keep this distinction clear: a table file stores data; a work area is a live session slot; a workspace is the live arrangement of open areas and related state.

## SCHEMAS and dtschemas naming

SCHEMAS belongs in this section as a compatibility and naming bridge. In the current project doctrine, dtschema and dtschemas terminology can be used as the x64base-oriented equivalent of schemas when the goal is to avoid confusion with SQL database schemas.

The manual should not collapse these terms. SQL schemas, x64base schema/workspace scripts, and live workspace state are related but different ideas. This section should explain the user-facing relationship briefly and leave detailed dtschema syntax for a later schema or workspace-persistence section.

## ERSATZ and relational/session inspection

ERSATZ should be introduced after USE, AREA, SELECT, and WORKSPACE because it depends on meaningful session context. It can be described cautiously as a relational or session inspection surface that helps users see the open-table and relation arrangement.

Do not overclaim ERSATZ behavior in the core workspace section. Its deeper behavior belongs in a later relational browsing or tuple-view section after runtime examples are sampled.

## Command map

- AREA: reports current work-area state and context.
- ERSATZ: supports relational/session inspection and browser-style review.
- SCHEMAS: compatibility and naming bridge around schema/workspace terminology.
- SELECT: changes or reports the active work area.
- USE: opens a table into live session context.
- WORKSPACE: organizes open areas and live workspace/session state.

## Example path for a later prose pass

Examples should be added only after command syntax and runtime transcripts are checked. A safe future example path is:

1. Open a table with USE.
2. Confirm context with AREA.
3. Open or switch areas with SELECT.
4. Use WORKSPACE to list the open areas.
5. Use WORKSPACE save/load only with evidence-backed syntax.
6. Introduce ERSATZ only after the live workspace and relation context are clear.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion

<!-- END SECTION: sections\workspaces_areas_and_session_state.md -->

---
