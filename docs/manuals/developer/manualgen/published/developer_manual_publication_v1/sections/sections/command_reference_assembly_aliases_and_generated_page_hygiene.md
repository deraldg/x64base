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

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- generated pages draft evidence not final reference
- duplicate rows slug collisions reviewed before publication
- aliases variants not canonical without review
- append blank append_blank variant canonicalization example
- load guard preserve no top-level load scoped codasyl load workspace load
- set-family canonicalization deferred
- aggs internal owner unless accepted public surface
- help cmdhelpchk metadata guide not runtime source closure
- command reference hygiene no generated page deletion
- sysentvar syscmd syssubcmd sysargs syshelp feeder alignment

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- generated pages are framed as draft evidence, not final reference;
- duplicate rows and slug collisions are review items, not automatic deletion targets;
- aliases and variants are not collapsed into canonical commands;
- APPEND BLANK and APPEND_BLANK remain review examples;
- LOAD guard preserves no top-level LOAD page while preserving scoped forms;
- SET-family canonicalization remains deferred;
- AGGS remains internal/family-owner evidence unless accepted;
- HELP/CMDHELPCHK/metadata are review guides but do not close runtime/source canaries alone;
- no generated command page deletion or production mutation is authorized.

Recommended required tokens for later PIP-003:
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

