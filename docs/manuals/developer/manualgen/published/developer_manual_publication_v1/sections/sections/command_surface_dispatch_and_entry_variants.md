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

### GENERIC remains a developer-utility canary

`GENERIC` is present in the supported DOTREF surface as a developer utility
placeholder. Keep it visible for dispatch and metadata reconciliation, but do
not present it as a normal user workflow until runtime behavior and intended
audience are separately established. Its current value is as a command-surface
canary: registration, HELP identity, handler ownership, and runtime availability
can be compared without inventing stronger behavior prose.

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

### Application-style UI entry points

`ARCTICTALK` and `FOXPRO` are application launch entries rather than ordinary
data commands. When Turbo Vision support is present, `ARCTICTALK` opens the
ArcticTalk shell and `FOXPRO` opens the FoxPro-style workbench. `FOXTALK` is the
legacy alias for `ARCTICTALK`.

These names may be registered or documented even when a particular build does
not contain the corresponding Turbo Vision surface. Describe availability from
the selected build and runtime evidence; do not infer universal availability
from registration alone. Neither entry currently exposes a separate usage
branch, so the bare command form is the documented launch surface.

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

## Future META alignment

This section should eventually align with the metadata system.

Expected future feeders:
- SYSCMD for canonical command identity, command key, canonical name, qualified name, token, handler, visibility, public surface, display reach, owner, source authority, source file, help topic, active flag, and notes.
- SYSSUBCMD for command-family subcommands such as SET ORDER, SET INDEX, REL variants, WORKSPACE variants, and other scoped command surfaces.
- SYSENTVAR for aliases, entry variants, shortcut spellings, compatibility forms, app-style function entries, and reviewed variants.
- SYSARGS for command argument shapes, expression arguments, predicates, tag names, scopes, deleted filters, required arguments, and repeatable arguments.
- SYSHELP for help text connected to command owners, canonical commands, subcommands, variants, warnings, examples, and reference material.
- SYSMSG for parser diagnostics, unknown command messages, syntax errors, invalid arguments, and ambiguity warnings.
- SYSFUNC for function-command bridge cases where scalar function entry overlaps command-like syntax.
- HELP_COMMANDS and generated command pages as draft evidence lanes that require dedupe, alias, and slug-collision review.

Temporary evidence is acceptable only when marked as temporary and crosswalked to future META feeders.

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- AGGS internal family owner exposure
- SET family canonicalization deferred
- command function bridge preserves scalar entry
- generated command pages duplicates aliases slug collisions
- SYSCMD SYSSUBCMD SYSENTVAR sparse feeder alignment
- HELP CMDHELPCHK not runtime source authority
- parser dispatch handler visibility display reach evidence
- aliases variants subcommands canonical commands not collapsed
- public command surface separated from internal scaffolding
- command reference generation no delete rewrite

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- generated command pages are treated as draft evidence;
- public command surface is separated from internal owner/family scaffolding;
- AGGS is not promoted as public command surface without explicit acceptance;
- SET-family canonicalization remains deferred;
- function bridge behavior preserves scalar entry while respecting command ownership;
- generated command pages with duplicates, aliases, and slug collisions remain draft evidence;
- SYSCMD, SYSSUBCMD, and SYSENTVAR are included as feeders even if sparse;
- HELP and CMDHELPCHK are not treated as runtime/source authority;
- parser dispatch, handlers, public visibility, and display reach remain evidence-gated;
- aliases, variants, subcommands, and canonical commands are not collapsed without review;
- command reference generation does not delete or rewrite generated command pages.

Recommended required tokens for later PIP-003:
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

