# Developer Manual Harvest Inspection v1

Status: INSPECTION_ONLY. This file is generated so the harvested manual material can be read end-to-end and judged for human consumption. It is not a promoted publication and it does not change the accepted MAN* catalog.

Generated: 2026-06-28 from local repository files in `D:/code/ccode`.

Companion files:

- `README.md` explains this inspection bundle.
- `manual_harvest_inspection_manifest_v1.csv` lists every included source and SHA-256 hash.
- `manual_harvest_inspection_quality_scan_v1.md` summarizes readiness and review markers.

## Included Source Order

1. Developer Manual Publication v1 With Media Section (`docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md`)
2. Developer Manual Publication v1 Appendices (`docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_appendices.md`)
3. MAN* Catalog Visibility Reference (`docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/manualgen_man_catalog_visibility_reference.md`)
4. Manual Mutation Cycle Reference (`docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/references/manual_mutation_cycle_reference_v1.md`)
5. DotTalk++ DotScript and Developer Handoff v1 (`DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`)
6. LabTalk Source to Case Inventory v1 (`LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md`)
7. LabTalk Overlay Boundary v1 (`LABTALK_OVERLAY_BOUNDARY_V1.md`)
8. LabTalk ENG Runtime Proof Plan v1 (`LABTALK_ENG_RUNTIME_PROOF_PLAN_V1.md`)
9. LabTalk Case Review v2 (`LABTALK_CASE_REVIEW_V2.md`)
10. README_CASES_v0.md (`docs/cases/README_CASES_v0.md`)
11. REGISTRY_CASES_v0.md (`docs/cases/REGISTRY_CASES_v0.md`)
12. CASE_FRAMEWORK.md (`docs/cases/CASE_FRAMEWORK.md`)
13. CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB (`docs/cases/CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB.md`)
14. CASE_ENG_020_SEEK_VS_SCAN (`docs/cases/CASE_ENG_020_SEEK_VS_SCAN.md`)
15. CASE_ENG_030_BUFFERING_COMMIT_LIFECYCLE (`docs/cases/CASE_ENG_030_BUFFERING_COMMIT_LIFECYCLE.md`)
16. CASE_ENG_040_METADATA_DATA_DICTIONARY (`docs/cases/CASE_ENG_040_METADATA_DATA_DICTIONARY.md`)
17. CASE_ENG_050_FILE_ENGINE_SEPARATION (`docs/cases/CASE_ENG_050_FILE_ENGINE_SEPARATION.md`)
18. CASE_HIST_000_DATA_TRAIL_OVERVIEW (`docs/cases/CASE_HIST_000_DATA_TRAIL_OVERVIEW.md`)
19. CASE_HIST_010_COBOL_CONNECTED_COMPUTERS (`docs/cases/CASE_HIST_010_COBOL_CONNECTED_COMPUTERS.md`)
20. CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM (`docs/cases/CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM.md`)
21. CASE_HIST_030_UNISYS_CODASYL_ALCOA (`docs/cases/CASE_HIST_030_UNISYS_CODASYL_ALCOA.md`)
22. CASE_HIST_040_XBASE_MAJOR_PLATFORM (`docs/cases/CASE_HIST_040_XBASE_MAJOR_PLATFORM.md`)
23. CASE_HIST_050_EARTHKIDS_CAREPAX (`docs/cases/CASE_HIST_050_EARTHKIDS_CAREPAX.md`)
24. CASE_HIST_060_TITLESCAN_PAXON_DATABASE_TRANSFERS (`docs/cases/CASE_HIST_060_TITLESCAN_PAXON_DATABASE_TRANSFERS.md`)
25. CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE (`docs/cases/CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE.md`)
26. CASE_HIST_080_HYNIX_SEMICONDUCTOR_PROCESS_DATA (`docs/cases/CASE_HIST_080_HYNIX_SEMICONDUCTOR_PROCESS_DATA.md`)
27. CASE_HIST_090_DOTTALK_LABTALK_AI_FUTURE (`docs/cases/CASE_HIST_090_DOTTALK_LABTALK_AI_FUTURE.md`)

---

# Source: Developer Manual Publication v1 With Media Section

Path: `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_media_section_v1.md`

<!-- BEGIN SOURCE CONTENT -->

<!-- MDO-226 build/rebuild dry-run artifact. Not a publication replacement. -->
<!-- publication_id: developer_manual_publication_v1_media_section_v1 -->
<!-- created_utc: 2026-05-27T12:06:25Z -->

# Media, Storyboards, and the Data-Trail Teaching Layer

Status: inserted by MDO-220 into the controlled media-section publication revision workspace.

This section explains how the Developer Manual handles images, storyboards, screenshots, diagrams, and other media as evidence-bearing documentation assets rather than loose illustrations.

The media assets listed here remain in docs/media. MDO-220 does not move, rename, delete, or copy media files. It anchors them to stable media IDs, hashes, captions, and manual-section targets so future manual regenerations can rebuild the media layer deliberately.

## Why media needs an anchor manifest

Text sections can be regenerated from accepted manifests and reviewed workspaces. Media needs the same discipline. A storyboard image should have a stable ID, a source path, a hash, a planned manual anchor, and a review status. Otherwise, images become detached from the evidence trail that produced them.

For DotTalk++ / x64base, the current media layer teaches the systems-history trail: business data, connected computers, institutional records, network databases, xBase, document transfer, ERP, industrial traceability, and the AI-facing reason that data literacy still matters.

## Review note

These storyboards are current teaching/media artifacts, not final historical claims by themselves. Before external publication or classroom release, review captions, spelling, AI-rendered screen text, factual framing, and whether each board belongs in the Developer Manual, Student Manual, User Manual, or a separate teaching deck.

## Anchored storyboard assets

<a id="media-storyboards-data-trail-overview"></a>

### MEDIA-STORY-OVERVIEW-01: Data-trail overview board A

- Media ID: `MEDIA-STORY-OVERVIEW-01`
- Anchor: `media-storyboards-data-trail-overview`
- Planned use: `overview`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 10_56_24 AM.png`
- SHA-256: `08CAFA885C672F90592570FA8CF3C138A108538CF900E31B7FF73C85D6223122`
- Note: Overview board for the whole systems-history data trail toward DotTalk++ / LabTalk.

![Data-trail overview board A](<../../../../../../media/ChatGPT Image May 26, 2026, 10_56_24 AM.png>)

<a id="media-storyboards-data-trail-overview"></a>

### MEDIA-STORY-OVERVIEW-02: Data-trail overview board B

- Media ID: `MEDIA-STORY-OVERVIEW-02`
- Anchor: `media-storyboards-data-trail-overview`
- Planned use: `overview`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_04_49 AM.png`
- SHA-256: `C18BFD13092EAB059C439B9F6610B6EE10BDE51BABABAD96A1DE73BFC381A67B`
- Note: Alternate overview board for the whole systems-history data trail toward DotTalk++ / LabTalk.

![Data-trail overview board B](<../../../../../../media/ChatGPT Image May 26, 2026, 11_04_49 AM.png>)

<a id="media-storyboard-cobol-connected-computers"></a>

### MEDIA-STORY-001: Foundations: COBOL and Connected Computers

- Media ID: `MEDIA-STORY-001`
- Anchor: `media-storyboard-cobol-connected-computers`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_18 AM (1).png`
- SHA-256: `74336722678EE83C0E752D986C7C36F02DEC7C75D41CE860DB9F2B65B69A28F6`
- Note: Storyboard on COBOL, business data, and connected computers.

![Foundations: COBOL and Connected Computers](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_18 AM (1).png>)

<a id="media-storyboard-jumps-army-system"></a>

### MEDIA-STORY-002: Case Study One: JUMPS Army System

- Media ID: `MEDIA-STORY-002`
- Anchor: `media-storyboard-jumps-army-system`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_18 AM (2).png`
- SHA-256: `E861382658FC03BF20CE58829573FC81A0078C0C5ACD7BBBFBBC3A1ACA3A1E40`
- Note: Storyboard on military pay, personnel records, and large institutional data processing.

![Case Study One: JUMPS Army System](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_18 AM (2).png>)

<a id="media-storyboard-unisys-codasyl-alcoa"></a>

### MEDIA-STORY-003: Unisys / CODASYL COBOL at ALCOA

- Media ID: `MEDIA-STORY-003`
- Anchor: `media-storyboard-unisys-codasyl-alcoa`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_18 AM (3).png`
- SHA-256: `7CBB00FB05887BC46E0F7E722A774C0D949C4033787035CAE091CFAAD87C62FF`
- Note: Storyboard on industrial data, network databases, and linked records.

![Unisys / CODASYL COBOL at ALCOA](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_18 AM (3).png>)

<a id="media-storyboard-xbase-major-platform"></a>

### MEDIA-STORY-004: xBase as a Major Platform

- Media ID: `MEDIA-STORY-004`
- Anchor: `media-storyboard-xbase-major-platform`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_18 AM (4).png`
- SHA-256: `05ABDA0D842A45BF2A41BAB7A294147B79A90F1FF4B696425FD8D64293E9ADF3`
- Note: Storyboard on dBASE, Clipper, FoxPro, Visual FoxPro, and Microsoft data pipelines.

![xBase as a Major Platform](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_18 AM (4).png>)

<a id="media-storyboard-earthkids-carepax"></a>

### MEDIA-STORY-005: Earthkids to CAREPAX

- Media ID: `MEDIA-STORY-005`
- Anchor: `media-storyboard-earthkids-carepax`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_19 AM (5).png`
- SHA-256: `C5F5396AFF6D28299E406A8B769FEAD7899ACB03EB0D798D59BDE2AB5C8367C2`
- Note: Storyboard on daycare administration, vaccination scheduling, and market reality.

![Earthkids to CAREPAX](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_19 AM (5).png>)

<a id="media-storyboard-digital-transfer-erp-industrial-scale"></a>

### MEDIA-STORY-006: Digital Transfer, ERP, and Industrial Scale

- Media ID: `MEDIA-STORY-006`
- Anchor: `media-storyboard-digital-transfer-erp-industrial-scale`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_19 AM (6).png`
- SHA-256: `575CD0A2C4AD2BC04D54266DADFF858F8C66788CB939ABBCA056DB6D69A6F65E`
- Note: Storyboard on document imaging, ERP, transactions, and semiconductor process data.

![Digital Transfer, ERP, and Industrial Scale](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_19 AM (6).png>)

<a id="media-storyboard-dottalk-labtalk-ai-future"></a>

### MEDIA-STORY-007: DotTalk++ / LabTalk and the AI Future

- Media ID: `MEDIA-STORY-007`
- Anchor: `media-storyboard-dottalk-labtalk-ai-future`
- Planned use: `storyboard`
- Storage: `docs\media\ChatGPT Image May 26, 2026, 11_23_20 AM (7).png`
- SHA-256: `3B1AD12CC45C9E42501E809871702D15126169BC416D2DD4CA9B684F4C208640`
- Note: Storyboard on DotTalk++ as a path-not-taken and a bridge to AI literacy.

![DotTalk++ / LabTalk and the AI Future](<../../../../../../media/ChatGPT Image May 26, 2026, 11_23_20 AM (7).png>)

## Regeneration rule

Future manual regeneration should treat this section as a generated/controlled media section. New media should first be inventoried, hashed, assigned a stable ID, and accepted into a media anchor manifest before any publication rebuild or SelfDoc metadata promotion.


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- MIN/MAX scalar function versus aggregate command ambiguity
- AGGS internal family owner exposure
- direct aggregate verbs versus scalar function forms
- command parser function bridge
- WHERE FOR predicate equivalence
- DELETED NOT DELETED !DELETED aggregate filters
- xexpr owns expression evaluation surfaces
- HELP FUNCTIONS FUNCTION name SYSFUNC future feeder
- generated command pages draft evidence
- MIN(2,1) versus MIN 2,1 parser behavior

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Future META alignment

This section should eventually align with the metadata system.

Expected future feeders:
- SYSFUNC for canonical function identity, display name, category, argument range, implementation status, visibility tier, owner, source authority, source file, handler, CALC_CALL, PUB_SURF, SELF_REG, MSG_CAT, active status, and notes.
- SYSARGS for function and command argument shapes, predicates, deleted filters, repeatable arguments, and required values.
- SYSCMD for command identity and handler alignment for CALC, CALCWRITE, COUNT, SUM, AVG, MIN, MAX, LOCATE, CONTINUE, and SCAN.
- SYSSUBCMD for aggregate-family or predicate-related subcommands if those are modeled as subcommands.
- SYSENTVAR for variants, aliases, and command-line function-app entry points after seed hygiene review.
- SYSHELP for generated and curated help text connected to command and function owners.
- SYSMSG for expression, aggregate, predicate, and parser diagnostics.

Temporary evidence is acceptable only when marked as temporary and crosswalked to future META feeders.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- generated command pages are treated as draft evidence;
- AGGS is not promoted as a public user command without explicit acceptance;
- MIN/MAX scalar function and aggregate command forms are separated;
- function-command bridge behavior is described conservatively;
- WHERE and FOR equivalence is evidence-gated;
- deleted-record filters are proof-aware;
- xexpr ownership is preserved;
- HELP FUNCTIONS, HELP FUNCTION <name>, and SYSFUNC future feeder notes are present;
- compatibility evidence is not presented as runtime proof;
- parser ambiguity remains visible.

Recommended required tokens for later PIP-003:
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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


<!-- MDO-110: promoted from reviewed candidate into manual draft workspace v2. -->
<!-- Decision: MDO-109 ACCEPT_FOR_PROMOTION; gate READY_FOR_HUMAN_PROMOTION_REVIEW. -->

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

## Review notes before promotion

- Confirm HELP wording against command page and runtime behavior.
- Confirm ABOUT, STATUS, and VERSION wording before adding examples.
- Confirm COLOR and CLEAR remain limited to display/session comfort.
- Confirm QUIT wording does not overclaim cleanup behavior.
- Keep workspace/table-opening content out of this section.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion


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

## Command map

- CMDARGCHK: supports command argument checking or review in the documentation/validation lane.
- CMDHELP: supports command-help generation, maintenance, or inspection.
- CMDHELPCHK: validates HELP and command-help artifact consistency.
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

## Review notes before promotion

- Confirm all five command pages before promotion.
- Keep HELP, metadata, CMDHELPCHK, SelfDoc, and manualgen roles distinct.
- Do not imply that metadata alone proves behavior.
- Do not imply that reviewed candidate status is final publication.
- Keep the pipeline ledger as draft evidence until it is reviewed and accepted.
- Preserve known canaries and deferred issues, including SET-family canonicalization and LOAD scoping.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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


## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- SET-family canonicalization
- SET ORDER active tag reporting
- CDX/CNX logical abstraction
- LMDB physical backend boundary
- SEEK/FIND active order dependency
- relation tuple browser ownership
- ERSATZ path-specific evidence
- x64 workspace ERSATZ load reporting

These anchors preserve the canaries that the prose already discusses in ordinary language. They should remain until the section is promoted through evidence review.
## Future META alignment

This section should eventually align with the metadata system.

Expected future feeders:
- SYSCMD for command identity and handler mapping.
- SYSSUBCMD for SET ORDER, SET INDEX, REL, and other subcommand identity.
- SYSENTVAR for aliases, variants, and shortcuts after seed hygiene review.
- SYSARGS for tag names, key expressions, relation names, view arguments, rebuild flags, and backend options.
- SYSMSG for diagnostics about missing tags, unavailable orders, not-found search results, relation warnings, backend build failures, and rebuild results.
- SYSHELP for curated/generated concept help about indexing, tags, relations, views, and traversal.

Temporary evidence is acceptable only when marked as temporary and crosswalked to future META feeders.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- no placeholder markers remain;
- all required tokens are represented or intentionally excluded;
- generated command pages are treated as draft evidence;
- SET-family canonicalization is not resolved by prose alone;
- CDX/CNX/LMDB boundary is preserved;
- SEEK/FIND behavior is not overclaimed;
- relation, tuple, browser, and view ownership are not collapsed;
- canaries are present and explicit;
- future META feeders are named;
- no compatibility evidence is presented as runtime proof;
- no backend implementation detail is accidentally promoted into user command prose.

Recommended required tokens for later PIP-003:
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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Future META alignment

This section should eventually align with the metadata system.

Expected future feeders:
- SYSCMD for canonical command identity and handler mapping.
- SYSARGS for arguments such as record number, skip count, search key, predicate, or scope.
- SYSMSG for messages such as not found, no table open, invalid record target, or end-of-file/beginning-of-file conditions.
- SYSHELP for curated/generated help about navigation, browsing, and search concepts.
- SYSENTVAR for aliases, variants, or shortcut spellings after seed hygiene review.

Current temporary evidence is acceptable, but it must remain marked as temporary until the relevant META crosswalks exist.

## Review notes before PIP-003

PIP-003 should verify:
- no TODO markers remain;
- required tokens are represented or intentionally excluded;
- unsupported runtime claims are zero;
- actionable drift rows are zero;
- index behavior is not overclaimed;
- compatibility evidence is gated;
- generated command pages remain draft evidence;
- future META feeders are named.

Recommended PIP-003 required tokens:
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

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- candidate note headers not normalized one section at a time
- reviewed candidate status blocks systematic normalization
- header normalization no substantive prose rewrite
- final publication separate from promoted draft assembly
- canonical path slug verification inspectable files
- table of contents section order actual files
- review packets preferred human inspection before authorization
- generated command pages evidence artifacts no deletion
- help meta cmdhelpchk source runtime selfdoc no mutation
- publication readiness recommends not silently publishes

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.

## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- promoted draft workspace review is distinct from final publication;
- candidate note headers are not normalized casually one section at a time;
- reviewed candidate status blocks are handled systematically;
- header normalization does not rewrite substantive prose;
- canonical path and slug verification use inspectable files;
- section count, section order, and table of contents checks are represented;
- review packets are preserved as human-inspection surfaces;
- generated command pages and evidence artifacts are protected from deletion;
- HELP, META, CMDHELPCHK, source, runtime data, and production SelfDoc metadata are not mutated;
- publication readiness may recommend repairs but does not silently publish or normalize.

Recommended required tokens for later PIP-003:
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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Future META alignment

This section should eventually align with evidence metadata.

Expected future feeders and evidence lanes:
- SOURCE_FACT for source/comment provenance and implementation ownership evidence.
- SRCFILE, SRCBLOCK, SRCLINE, SRCUSAGE, SRCCLASS, SRCDISP, SRCALIAS, and MEMO_LINES for SelfDoc source-comment evidence where available.
- SYSCMD and SYSSUBCMD for command and subcommand identity tied to evidence.
- SYSFUNC for function evidence and function-command bridge canaries.
- SYSMSG for diagnostic and message canaries.
- SYSHELP for help alignment and curated help evidence.
- SYSARGS for argument-shape evidence and validation surfaces.
- SYSENTVAR for aliases, variants, and command/function entry variants.
- Manualgen PIP reports for gate evidence and assembly provenance.
- Canary ledger reports for open, deferred, reproduced, narrowed, and closed canary rows.

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

## Slow-lane canary tracking names

The slow-lane review tracks these canaries by exact name. These names are review anchors, not final user-facing prose.

- runtime proof concrete commands output build context date
- source verification implementation ownership not sidecar
- canary rows visible until closed with evidence
- canary closure requires current evidence not optimism old design intent
- legacy documents context not current fact without verification
- manualgen selfdoc report-only unless authorized
- help cmdhelpchk metadata guide not close runtime source canaries
- build smoke shakedown regression labeled dated
- evidence packages no mutation
- canary deferred narrowed reproduced closed not disappear

These anchors preserve the canaries that the prose discusses in ordinary language. They should remain until the section is promoted through evidence review.


## Canary non-disappearance boundary

This exact review anchor is intentionally retained for slow-lane evidence review:

- A canary may be deferred/narrowed/reproduced/closed, but should not disappear silently.

The anchor is not final user-facing prose by itself. It preserves the boundary already described in this section: canaries remain visible until closed, superseded, transferred, or explicitly deferred with evidence.
## Review notes before PIP-003

This is a slow-lane section. Before generic PIP-003 is allowed to create a reviewed-candidate path, an MDO slow-lane evidence review should check:

- all required tokens are represented or intentionally excluded;
- runtime proof concrete commands/output/build/date boundary is present;
- source verification/implementation ownership boundary is present;
- canary visibility and closure rules are present;
- old design intent and legacy documents are not treated as current fact without verification;
- HELP/CMDHELPCHK/metadata are review guides, not canary closure evidence by themselves;
- build, smoke, shakedown, regression, and release evidence are scoped correctly;
- SelfDoc/manualgen report-only and no-mutation boundaries are visible;
- future META/evidence feeders are preserved.

Recommended required tokens for later PIP-003:
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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


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

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.


<!-- MDO-103B: promoted from reviewed candidate into manual draft workspace. -->
<!-- Decision: MDO-103A ACCEPT_FOR_PROMOTION; gate READY_FOR_HUMAN_PROMOTION_REVIEW. -->

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

## Review notes before promotion

- Confirm USE wording against runtime behavior and command page text.
- Confirm SELECT and AREA examples before adding syntax examples.
- Confirm WORKSPACE save/load wording before promotion.
- Keep SCHEMAS, dtschema, and dtschemas wording aligned with project naming doctrine.
- Keep ERSATZ wording cautious until deeper runtime evidence is reviewed.

## Boundary

- promoted to manual draft workspace, still review required
- not final published manual prose
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no production SelfDoc metadata promotion


<!-- MDO-261 MAN* CLI visibility reference insertion start -->
# MAN* Catalog and Manualgen CLI Visibility Reference

This reference exists because CLI-first systems can be useful and still be invisible. The Developer Manual now records the accepted MAN* catalog baseline and the read-only manualgen commands that expose it.

## Accepted baseline locations

- Accepted MAN* catalog baseline: docs/manuals/developer/manualgen/accepted_catalogs/man_catalog_v1
- Accepted MAN* CLI docs: docs/manuals/developer/manualgen/accepted_docs/man_cli_v1
- Accepted MAN* DBFs: docs/manuals/developer/manualgen/accepted_catalogs/man_catalog_v1/dbf

## Read-only command surface

The following commands are read-only and were hardened and captured by the MDO-255 through MDO-259 lane:

`powershell
$py = "D:\code\ccode\build\vcpkg_installed\x64-windows\tools\python3\python.exe"

& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog status
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog tables
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog counts
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog drift
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog export
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual sections
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual media
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual review
`

## Boundary

These commands are intended to report and verify the accepted MAN* manualgen catalog. They do not write DBFs, run x64base imports, replace publication, mutate media, or touch HELP/META/CMDHELPCHK.

## Integration status

This reference was inserted into a controlled revision workspace by MDO-261. It does not replace the active Developer Manual publication. A later explicitly authorized package must promote or replace a publication artifact if this reference is to become the active public manual.
<!-- MDO-261 MAN* CLI visibility reference insertion end -->


<!-- MDO-270 MANUAL_MUTATION_CYCLE_REFERENCE_START -->

## Manual Mutation Cycle

# Manual Mutation Cycle and Guarded Publication Workflow

Status: DRAFT INSERTION CANDIDATE

This reference documents the controlled mutation cycle used for the living DotTalk++ / x64base Developer Manual. It is intended to make manual mutation visible to future operators and AI sessions without relying on tribal memory.

## Core doctrine

Runtime proves. Source defines. HELP explains. Metadata organizes. CMDHELPCHK validates. SelfDoc preserves provenance. Manualgen assembles the living manual.

The Developer Manual is not a static artifact. It is a regenerated and controlled publication with evidence, gates, backups, rollback paths, and closeout records.

## Mutation classes

Manual mutation work must declare what it is allowed to change before execution:

- Plan/report only: writes reports and drafts, but does not mutate the active manual.
- Controlled revision workspace: creates or modifies a revision copy, not the active publication.
- Controlled publication replacement: replaces the active publication only after explicit authorization, backup, and validation.
- Source mutation: changes tooling such as `tools/manualgen/manualgen.py`; requires explicit authorization.
- Protected-system mutation: HELP, META, CMDHELPCHK, runtime data, production SelfDoc metadata, and C++ integration remain blocked unless explicitly authorized in a separate lane.

## Standard cycle

```text
Plan -> Stage -> Validate -> Authority Gate -> Execute -> Post-Validate -> Closeout/Hold
```

A package should not jump directly from idea to publication mutation. It should first produce plan evidence, then stage or revise safely, then validate, then request authority before replacing an active artifact.

## Required evidence

Each guarded manual mutation package should produce:

- status summary CSV
- summary Markdown
- action-specific manifest or comparison report
- boundary ledger
- rollback or backup evidence when active publication is touched
- savepoint append only after green status

## False-red discipline

A red package is not automatically a project failure. It may be a wrapper, path, CSV, or validation-assumption defect. The correct response is:

1. stop and do not append the savepoint;
2. inspect the status, summary, manifest, and boundary rows;
3. distinguish actual mutation/content failure from report/checker failure;
4. patch the package or rollback only after evidence supports that choice.

## Rollback and savepoint discipline

A package that replaces an active publication must create a backup first and prove the backup matches the pre-promotion active artifact. The savepoint journal is appended only after green validation, not merely after a script runs.

## Worked example: MAN* visibility lane

The MAN* visibility lane demonstrates the cycle:

- MDO-248 through MDO-251 created, validated, and promoted MAN* DBFs into an accepted manualgen catalog baseline.
- MDO-255 and MDO-256 added and hardened read-only manualgen CLI commands.
- MDO-257 through MDO-260 documented and planned visibility.
- MDO-261 through MDO-265 inserted, promoted, and post-validated the Developer Manual visibility reference.
- MDO-266 closed the lane on hold.
- MDO-267 and MDO-268 hardened and smoke-tested the DotTalk++ runtime bridge to the accepted MAN* DBFs.

## Hold rule

When a lane is closed with `HOLD_UNLESS_NEW_LANE_AUTHORIZED`, further work should begin as a new explicitly authorized lane rather than silently extending the prior one.


Reference artifact: 
eferences/manual_mutation_cycle_reference_v1.md

<!-- MDO-270 MANUAL_MUTATION_CYCLE_REFERENCE_END -->

<!-- END SOURCE CONTENT -->

---

# Source: Developer Manual Publication v1 Appendices

Path: `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/developer_manual_publication_v1_appendices.md`

<!-- BEGIN SOURCE CONTENT -->

# DotTalk++ / x64base Developer Manual Appendices v1

Generated by MDO-215 from optional non-section appendix candidates after MDO-214 publication.

Boundary: this addendum does not change the 24-section public body and does not mutate source, HELP, META, CMDHELPCHK, catalogs, runtime data, or production SelfDoc metadata.

## Appendix Manifest

- Appendix 1: appendices\command_reference_general_review.md
- Appendix 2: appendices\review_and_deferred_alias_and_variant_review.md
- Appendix 3: appendices\review_and_deferred_set_family.md

---

# Appendix 1: appendices\command_reference_general_review.md

# Appendix: Command Reference: General Review

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [BANG](../../command_reference_v1/commands/bang.md)
- [BELL](../../command_reference_v1/commands/bell.md)
- [BETA](../../command_reference_v1/commands/beta.md)
- [ENUM](../../command_reference_v1/commands/enum.md)
- [GENERIC](../../command_reference_v1/commands/generic.md)
- [HIER](../../command_reference_v1/commands/hier.md)
- [INSERT](../../command_reference_v1/commands/insert.md)
- [MULTIREP](../../command_reference_v1/commands/multirep.md)
- [PRN](../../command_reference_v1/commands/prn.md)
- [SB](../../command_reference_v1/commands/sb.md)
- [SEQUENTIAL](../../command_reference_v1/commands/sequential.md)
- [SM](../../command_reference_v1/commands/sm.md)
- [SMART](../../command_reference_v1/commands/smart.md)
- [TEST](../../command_reference_v1/commands/test.md)
- [TESTING](../../command_reference_v1/commands/testing.md)
- [VAR](../../command_reference_v1/commands/var.md)
- [VUSE](../../command_reference_v1/commands/vuse.md)
- [WA](../../command_reference_v1/commands/wa.md)

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.

---

# Appendix 2: appendices\review_and_deferred_alias_and_variant_review.md

# Appendix: Review and Deferred: Alias and Variant Review

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [APPEND BLANK](../../command_reference_v1/commands/append_blank.md) - aliases: APPEND BLANK - command key: APPEND_BLANK
- [ERROR CLEAR](../../command_reference_v1/commands/error_clear.md) - aliases: ERROR CLEAR - command key: ERROR_CLEAR
- [ERROR STATUS](../../command_reference_v1/commands/error_status.md) - aliases: ERROR STATUS - command key: ERROR_STATUS
- [ERROR TEST](../../command_reference_v1/commands/error_test.md) - aliases: ERROR TEST - command key: ERROR_TEST

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.

---

# Appendix 3: appendices\review_and_deferred_set_family.md

# Appendix: Review and Deferred: SET-family

Status: SECTION_SKELETON_DRAFT_REPAIRED / REVIEW_REQUIRED

Purpose:
Skeleton section generated from the revised manual TOC draft.

Promotion boundary:
- This section is a structural draft.
- Linked command pages are evidence-backed drafts, not final prose.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [SET](../../command_reference_v1/commands/set.md) - deferred
- [SET CASE](../../command_reference_v1/commands/set_case.md) - deferred
- [SET FILTER](../../command_reference_v1/commands/set_filter.md) - deferred
- [SET INDEX](../../command_reference_v1/commands/set_index.md) - deferred
- [SET ORDER](../../command_reference_v1/commands/set_order.md) - deferred
- [SET PATH](../../command_reference_v1/commands/set_path.md) - deferred
- [SET RELATION](../../command_reference_v1/commands/set_relation.md) - deferred
- [SET UNIQUE](../../command_reference_v1/commands/set_unique.md) - deferred
- [SET VAR](../../command_reference_v1/commands/set_var.md) - aliases: SET VAR! - deferred
- [SETCASE](../../command_reference_v1/commands/setcase.md) - deferred
- [SETCDX](../../command_reference_v1/commands/setcdx.md) - deferred
- [SETCNX](../../command_reference_v1/commands/setcnx.md) - deferred
- [SETFILTER](../../command_reference_v1/commands/setfilter.md) - deferred
- [SETINDEX](../../command_reference_v1/commands/setindex.md) - deferred
- [SETLMDB](../../command_reference_v1/commands/setlmdb.md) - deferred
- [SETNEAR](../../command_reference_v1/commands/setnear.md) - deferred
- [SETORDER](../../command_reference_v1/commands/setorder.md) - deferred
- [SETPATH](../../command_reference_v1/commands/setpath.md) - deferred

## Notes for future prose pass

- Add narrative explanation for this section after command-page sampling.
- Keep runtime-proven evidence separate from design intent.
- Preserve command/help/catalog provenance when promoting prose.

<!-- END SOURCE CONTENT -->

---

# Source: MAN* Catalog Visibility Reference

Path: `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/manualgen_man_catalog_visibility_reference.md`

<!-- BEGIN SOURCE CONTENT -->

# MAN* Catalog and Manualgen CLI Visibility Reference

This reference exists because CLI-first systems can be useful and still be invisible. The Developer Manual now records the accepted MAN* catalog baseline and the read-only manualgen commands that expose it.

## Accepted baseline locations

- Accepted MAN* catalog baseline: docs/manuals/developer/manualgen/accepted_catalogs/man_catalog_v1
- Accepted MAN* CLI docs: docs/manuals/developer/manualgen/accepted_docs/man_cli_v1
- Accepted MAN* DBFs: docs/manuals/developer/manualgen/accepted_catalogs/man_catalog_v1/dbf

## Read-only command surface

The following commands are read-only and were hardened and captured by the MDO-255 through MDO-259 lane:

`powershell
$py = "D:\code\ccode\build\vcpkg_installed\x64-windows\tools\python3\python.exe"

& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog status
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog tables
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog counts
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog drift
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual catalog export
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual sections
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual media
& $py .\tools\manualgen\manualgen.py --repo-root D:\code\ccode --manual developer manual review
`

## Boundary

These commands are intended to report and verify the accepted MAN* manualgen catalog. They do not write DBFs, run x64base imports, replace publication, mutate media, or touch HELP/META/CMDHELPCHK.

## Integration status

This reference was inserted into a controlled revision workspace by MDO-261. It does not replace the active Developer Manual publication. A later explicitly authorized package must promote or replace a publication artifact if this reference is to become the active public manual.

<!-- END SOURCE CONTENT -->

---

# Source: Manual Mutation Cycle Reference

Path: `docs/manuals/developer/manualgen/published/developer_manual_publication_v1_media_section_v1/references/manual_mutation_cycle_reference_v1.md`

<!-- BEGIN SOURCE CONTENT -->

# Manual Mutation Cycle and Guarded Publication Workflow

Status: DRAFT INSERTION CANDIDATE

This reference documents the controlled mutation cycle used for the living DotTalk++ / x64base Developer Manual. It is intended to make manual mutation visible to future operators and AI sessions without relying on tribal memory.

## Core doctrine

Runtime proves. Source defines. HELP explains. Metadata organizes. CMDHELPCHK validates. SelfDoc preserves provenance. Manualgen assembles the living manual.

The Developer Manual is not a static artifact. It is a regenerated and controlled publication with evidence, gates, backups, rollback paths, and closeout records.

## Mutation classes

Manual mutation work must declare what it is allowed to change before execution:

- Plan/report only: writes reports and drafts, but does not mutate the active manual.
- Controlled revision workspace: creates or modifies a revision copy, not the active publication.
- Controlled publication replacement: replaces the active publication only after explicit authorization, backup, and validation.
- Source mutation: changes tooling such as `tools/manualgen/manualgen.py`; requires explicit authorization.
- Protected-system mutation: HELP, META, CMDHELPCHK, runtime data, production SelfDoc metadata, and C++ integration remain blocked unless explicitly authorized in a separate lane.

## Standard cycle

```text
Plan -> Stage -> Validate -> Authority Gate -> Execute -> Post-Validate -> Closeout/Hold
```

A package should not jump directly from idea to publication mutation. It should first produce plan evidence, then stage or revise safely, then validate, then request authority before replacing an active artifact.

## Required evidence

Each guarded manual mutation package should produce:

- status summary CSV
- summary Markdown
- action-specific manifest or comparison report
- boundary ledger
- rollback or backup evidence when active publication is touched
- savepoint append only after green status

## False-red discipline

A red package is not automatically a project failure. It may be a wrapper, path, CSV, or validation-assumption defect. The correct response is:

1. stop and do not append the savepoint;
2. inspect the status, summary, manifest, and boundary rows;
3. distinguish actual mutation/content failure from report/checker failure;
4. patch the package or rollback only after evidence supports that choice.

## Rollback and savepoint discipline

A package that replaces an active publication must create a backup first and prove the backup matches the pre-promotion active artifact. The savepoint journal is appended only after green validation, not merely after a script runs.

## Worked example: MAN* visibility lane

The MAN* visibility lane demonstrates the cycle:

- MDO-248 through MDO-251 created, validated, and promoted MAN* DBFs into an accepted manualgen catalog baseline.
- MDO-255 and MDO-256 added and hardened read-only manualgen CLI commands.
- MDO-257 through MDO-260 documented and planned visibility.
- MDO-261 through MDO-265 inserted, promoted, and post-validated the Developer Manual visibility reference.
- MDO-266 closed the lane on hold.
- MDO-267 and MDO-268 hardened and smoke-tested the DotTalk++ runtime bridge to the accepted MAN* DBFs.

## Hold rule

When a lane is closed with `HOLD_UNLESS_NEW_LANE_AUTHORIZED`, further work should begin as a new explicitly authorized lane rather than silently extending the prior one.

<!-- END SOURCE CONTENT -->

---

# Source: DotTalk++ DotScript and Developer Handoff v1

Path: `DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`

<!-- BEGIN SOURCE CONTENT -->

# DotTalk++ DotScript and Development Handoff v1

Status: developer/AI handoff  
Audience: human developer, AI coding agent, maintainer  
Project root: `D:\code\ccode`

## Purpose

This document explains how I have been working inside DotTalk++ and x64base: not as a loose pile of files, but as a database runtime with source-defined contracts, runtime proof, data dictionary thinking, review gates, and scriptable maintenance lanes.

The core working model is:

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
DotScript executes reviewed procedures.
MDO packages preserve maintenance intent and closeout evidence.
```

That sentence is the best short description of how to continue development safely.

## What DotTalk++ Is in Practice

DotTalk++ should be treated like a serious commercial data/runtime system, even though it is homemade. The working pieces already behave like product subsystems:

- `x64base`: engine/runtime foundation, storage and indexing concepts, DBF/CDX/LMDB direction.
- DotTalk++ shell: command surface, work areas, HELP, scripts, runtime commands, validation commands.
- DotScript: repeatable runtime procedure language and smoke/regression harness.
- Data dictionary packages: schema, command, script, source, metadata, and proof planning.
- SelfDoc: evidence and provenance system, not an oracle and not an auto-repair engine.
- manualgen/MDO: controlled documentation and maintenance lifecycle.
- LabTalk: optional educational overlay, case catalog, teaching material, and story layer.

Do not flatten these into one undifferentiated documentation folder. Their separation is part of the architecture.

## Development Doctrine

The strongest pattern in the repo is controlled promotion:

1. Observe current source/runtime state.
2. Write a report or inventory.
3. Classify the finding.
4. Keep uncertainty explicit.
5. Propose a narrow repair or promotion.
6. Mutate only the intended artifact.
7. Capture runtime or structural proof.
8. Write a closeout/status record.

This is why many files are named as `PLAN`, `STATUS`, `REVIEW`, `CANDIDATE`, `PROOF`, or `PACKAGE`. Those names are not noise. They describe lifecycle state.

## DotScript Role

DotScript is best treated as the operational script layer for DotTalk++.

Use DotScript for:

- reproducible runtime procedures
- smoke tests
- schema/table creation candidates
- import/export experiments
- guarded maintenance execution
- command transcript generation
- repeatable proof capture

Do not use DotScript as a place to hide arbitrary mutation. A `.dts` file should make the intended runtime steps visible.

Typical DotScript responsibilities:

```text
set runtime paths
open or create a workspace
create or validate tables
load fixture data
run commands
capture output
prove expected behavior
close with a clear pass/fail status
```

When a DotScript mutates DBF/CDX/LMDB state, the handoff should say so plainly.

## Running DotTalk++ and DotScript

Use the current built executable when capturing runtime proof:

```powershell
& D:\code\ccode\build\src\Release\dottalkpp.exe
```

Inside the shell, the reliable script runner is:

```text
DOTSCRIPT <file.dts>
DOTSCRIPT <file.dts> OUT <transcript-file>
DOTSCRIPT TRACE <file.dts> OUT <transcript-file>
```

Use `DOTSCRIPT ... OUT ...` when the result is meant to prove behavior. The transcript is the artifact a human or AI should review later.

Existing `.dts` files often use lines such as:

```text
DO X64
DO path\to\other_script.dts
```

Treat that as established script vocabulary inside the DotScript estate. From the interactive shell and handoff docs, prefer the explicit `DOTSCRIPT` command because it has the clear usage contract and transcript support.

DotScript comments are skipped when they begin with `*`, `//`, `&&`, or `;` after trimming. Script resolution tries the typed path, then `.dts`, then `scripts/`, then `tests/`. Nesting is intentionally limited: main script plus one subscript.

## The Meaning of `DO X64`

`DO X64` appears in existing x64 canary scripts as the setup switch before `CREATE X64 ...`. It should be treated as a profile/setup operation used by the script estate to put the runtime into the expected x64 working mode.

When a future agent sees this pattern:

```text
DO X64
CREATE X64 VECALIAS (...)
```

do not remove it as noise. It is part of the x64 test/canary ceremony. If proving behavior from the shell, preserve the same sequence in the DotScript used for proof.

## Creating an X64 DBF Directly

The simplest way to create an x64 table is the `CREATE X64` command.

Pattern:

```text
DO X64
CREATE X64 <table> (<field> <type>, <field> <type>, ...)
STRUCT
```

Concrete example:

```text
DO X64
CREATE X64 DEV_STUDENTS (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2), ACTIVE L)
STRUCT
APPEND
REPLACE SID WITH 1001
REPLACE LNAME WITH "MARTIN"
REPLACE FNAME WITH "ADA"
REPLACE GPA WITH 3.75
REPLACE ACTIVE WITH .T.
LIST
```

Important `CREATE` rules from the command contract:

- `CREATE X64 <name> (...)` writes a DBF through the configured DBF path slot.
- It closes the current area before creating the table.
- It opens the new table after successful creation.
- It clears active order state.
- Memo fields (`M`) attempt memo attach after open.
- X64 applies descriptor fallback/name policy for DBF descriptor safety.
- Long or colliding field names can receive fallback tokens while retaining authoritative logical names where supported.

Use `STRUCT`, `FIELDS`, `LIST`, `TUPLE`, or `STATUS` as readback proof after creation.

## Creating a DBF From `schema.json`

The schema-driven path is `DDL CREATE DBF`.

Pattern:

```text
DDL CREATE DBF <out.dbf> FROM <schema.json>
DDL CREATE DBF <out.dbf> FROM <schema.json> OVERWRITE
DDL CREATE DBF <out.dbf> FROM <schema.json> SEED BLANK <n>
DDL CREATE DBF <out.dbf> FROM <schema.json> EMIT SIDECARS
```

Path rules:

- Relative schema inputs resolve under the `SCHEMAS` path first, then current working directory.
- Relative DBF outputs resolve under the `TMP` path by default.
- Existing DBF output is refused unless `OVERWRITE` is supplied.
- `SEED CSV` is recognized in the command surface but is not implemented in this drop-in.
- `EMIT SIDECARS` writes companion schema/load/index metadata files.

Minimal `schema.json` shape:

```json
{
  "version": "1.0",
  "name": "students",
  "encoding": "UTF-8",
  "date_policy": "ISO",
  "null_policy": "EMPTY_AS_EMPTY",
  "logical_policy": "TF",
  "fields": [
    { "name": "SID", "type": "N", "length": 9, "decimals": 0, "required": true },
    { "name": "LNAME", "type": "C", "length": 20, "required": true, "trim": "right" },
    { "name": "FNAME", "type": "C", "length": 15, "required": true, "trim": "right" },
    { "name": "DOB", "type": "D", "length": 8, "zero_date": "ALLOW" },
    { "name": "ACTIVE", "type": "L" }
  ],
  "indexes": [
    { "name": "SID_PK", "engine": "CNX", "order": ["SID ASC"], "unique": true, "nullable": "DISALLOW" },
    { "name": "NAME1", "engine": "CNX", "order": ["LNAME ASC", "FNAME ASC"], "collation": "nocase", "trim": "right" }
  ]
}
```

The active schema contract at `src\cli\schema_json_v1.schema.json` supports field types `C`, `N`, `D`, `L`, and `M` for `DDL CREATE DBF`. Do not assume every direct `CREATE` type is valid in the JSON schema path.

## Schema Rules for Future Agents

When working with a schema, classify it before using it:

| Schema kind | Meaning | Handling |
|---|---|---|
| `schema.json` | Table field/index/relation contract for DDL/import work. | Candidate until runtime-created/read back. |
| `.dtschema` / `.dtschemas` | x64base workspace/session schema: areas and optional relations. | Do not confuse with SQL schemas. |
| JSON Schema | Validator/specification for another artifact. | Use for structural validation, not runtime proof by itself. |
| Data dictionary package schema | Contract for generated reports/import candidates. | Keep package-local until promoted. |

Rules:

- Keep candidate schemas separate from active schemas.
- Never overwrite active schemas without an explicit promotion package.
- If a schema has indexes, also define how those indexes are created or activated at runtime.
- If a schema has relations, capture workspace/relation proof separately from table creation proof.
- A schema that parses is not proven. A schema is only proven after runtime creation/open/readback.
- For DBF work, prove with `STRUCT` and at least one data navigation/readback command.
- For index work, prove physical order versus logical order.
- For workspace schema work, prove `WORKSPACE` load/save/readback if the runtime supports it for that case.

## Creating and Using an Index

The direct index command builds an INX file from the current open table.

Pattern:

```text
USE <table>
INDEX ON <field> TAG <name>
INDEX ON <field> TAG <name> DESC
INDEX ON <field> TAG <name> ASC 2INX
SET INDEX TO <name>.inx
```

Important rules:

- `INDEX` requires an open table.
- It reads records and writes an index file.
- It does not mutate table records.
- Deleted records are excluded.
- Default direction is `ASC`.
- Default output format is `2INX`.
- `TAG` names an INX file target; non-`.inx` extensions are refused.
- Field-number tokens are accepted by the parser, but field names are clearer in docs and proof.

Use `SET INDEX TO <container>` to attach an index container. For CDX/CNX-style tag activation, use `SET ORDER`.

Patterns:

```text
SET INDEX TO students.cdx
SET ORDER TO TAG LNAME
SET ORDER TO 0
SET ORDER PHYSICAL
```

Key distinction:

```text
SET INDEX names or attaches the index container.
SET ORDER chooses the active logical traversal order.
INDEX creates an INX file from the currently open table.
```

Do not claim an index works until runtime output proves the order changed or a seek uses the expected access path.

## Minimal End-to-End Proof Script

A future AI can use this as a starting pattern. Put it in a temporary `.dts` file, run it with `DOTSCRIPT ... OUT ...`, and review the transcript.

```text
* Status: SMOKE / MUTATING_SANDBOX
* Purpose: Create x64 DBF, add row, build index, attach index, prove readback.
* Mutation: writes DBF and INX in configured runtime paths.

DO X64
ERASE DEV_STUDENTS CONFIRM

CREATE X64 DEV_STUDENTS (SID N(6,0), LNAME C(20), FNAME C(15), GPA N(4,2))
STRUCT

APPEND
REPLACE SID WITH 1001
REPLACE LNAME WITH "MARTIN"
REPLACE FNAME WITH "ADA"
REPLACE GPA WITH 3.75

APPEND
REPLACE SID WITH 1002
REPLACE LNAME WITH "BROWN"
REPLACE FNAME WITH "GRACE"
REPLACE GPA WITH 3.90

LIST
INDEX ON LNAME TAG DEV_STUDENTS_LNAME ASC 2INX
SET INDEX TO DEV_STUDENTS_LNAME.inx
TOP
LIST
CLOSE
```

Proof expectations:

- `STRUCT` shows the expected fields.
- First `LIST` shows inserted rows in table/physical order.
- `INDEX ON` writes the index target without table mutation.
- `SET INDEX` attaches the INX target where the current runtime supports that path.
- For logical-order proof, prefer a CDX/CNX fixture with `SET INDEX TO <container>` and `SET ORDER TO TAG <tag>`, or capture clear INX navigation output if that is the behavior under test.

If the transcript does not visibly prove changed order or indexed access, do not fake the proof. Record the gap and use a CDX/CNX `SET ORDER` proof or a dedicated index fixture.

## DotScript Safety Classes

Class DotScript files before running or promoting them:

| Class | Meaning | Default action |
|---|---|---|
| REPORT_ONLY | Reads runtime/source state and emits evidence. | Safe to inspect; run only if paths are understood. |
| PLAN_ONLY | Documents intended work but should not execute mutation. | Do not execute as a live script. |
| CANDIDATE | Proposed runtime/import/schema action. | Review before execution. |
| OPERATOR_RUN_REQUIRED | Intended to run later under explicit authorization. | Do not run casually. |
| MUTATING | Writes DBF/CDX/LMDB/source/generated docs. | Requires explicit gate and proof plan. |
| SMOKE | Reproducible runtime proof. | Prefer read-only fixtures unless mutation is the behavior under test. |

The existing style often marks guarded scripts directly in comments. Preserve that habit.

## DotScript Pattern

A good DotScript or DotScript-adjacent package should answer these questions:

```text
What subsystem does it touch?
What paths does it read?
What paths does it write?
Does it mutate DBF/CDX/LMDB?
Does it mutate HELP, CMDHELPCHK, manualgen, source, or schemas?
What fixture or workspace does it need?
What output proves success?
What is the rollback or non-promotion path?
```

For future scripts, prefer headers like:

```text
* Status: CANDIDATE / REVIEW_BEFORE_EXECUTION
* Safety: REPORT_ONLY or MUTATING
* Purpose: one-sentence intent
* Inputs: explicit files/directories
* Outputs: explicit reports/tables/transcripts
* Mutation: none / DBF / CDX / LMDB / docs / source
* Gate: who or what must approve before promotion
```

## Schema Practice

The repo has been using schemas as contracts, not as decorative docs.

Good schema work usually has three layers:

1. Human-readable design: Markdown package or plan.
2. Machine-readable contract: `.dtschema`, JSON schema, CSV manifest, or registry row.
3. Runtime proof: DotScript/native command transcript showing the contract is usable.

When building schemas for the homemade database, treat them with the same rigor as a commercial migration:

- define fields intentionally
- preserve source provenance
- mark nullable/required assumptions
- separate candidate schemas from active schemas
- avoid promoting a schema just because it parses
- include field/tag/index reconciliation when CDX/LMDB behavior matters

Do not silently overwrite active schema files. Prefer candidate folders and promotion packages.

## DBF/CDX/LMDB Handling

The runtime has several storage/index concepts that should stay distinct:

| Concept | Developer meaning |
|---|---|
| DBF/XDBF | Table/storage layer and record layout. |
| CDX | User-facing logical index/tag container concept. |
| LMDB | Backend/index environment detail in some paths. |
| DbArea/work area | Runtime session state: open table, cursor, alias, order, filter. |
| Tuple/projection | Rendered relational or query-shaped view of underlying data. |

A common mistake would be to treat an index, a table, and a rendered list as the same thing. DotTalk++ is valuable because it can show those differences.

For proofs, capture the difference between:

```text
physical record order
logical order
active tag/order
current cursor
filtered/predicate view
projected tuple output
persisted table state
buffered or dirty state
```

## HELP, CMDHELPCHK, and Metadata

HELP is not just user text. It is part of the command contract system.

The intended chain is:

```text
source usage contracts
  -> command/help catalog
  -> HELP output
  -> CMDHELPCHK validation
  -> manualgen/manual publication
  -> SelfDoc provenance
```

Avoid raw HELP DBF edits unless a specific guarded package authorizes it. Most repair work should start from source contracts, generated candidates, or validation reports.

When command behavior and HELP disagree, do not immediately patch prose. First determine whether the drift belongs to:

- source command implementation
- usage metadata
- generated HELP artifact
- stale manualgen output
- CMDHELPCHK expectation
- alias/variant policy
- intentional compatibility shim

## SelfDoc Pattern

SelfDoc reports are evidence, not verdicts.

Use SelfDoc to classify, preserve, and route findings. Do not let it become an unreviewed mutation engine.

Useful lanes:

```text
CONFIRMED
LIKELY
STALE_EVIDENCE
CLASSIFIER_REVIEW
CAPTURE_REVIEW
POLICY_REVIEW
SOURCE_REVIEW
INTENTIONAL_EXCEPTION
DO_NOT_REPAIR
```

This matters because many apparent defects are actually:

- stale generated output
- scanner limitations
- command aliases
- backup files under source roots
- compatibility shims
- intentionally optional LabTalk/education material

The correct response is often a review report, not a patch.

## MDO and Manualgen Pattern

MDO packages are maintenance work orders and closeout records. Treat them as the project memory of how a change was reasoned through.

Good MDO-style work has:

- one clear objective
- explicit safety class
- source/evidence paths
- mutation boundary
- generated reports
- validation command or proof
- status/closeout file
- recommended next package

Manualgen work should follow the same promotion flow:

```text
candidate section
  -> evidence review
  -> reviewed candidate
  -> human decision/status
  -> promoted draft
  -> publication artifact
```

Do not skip from raw generated text to final manual prose.

## LabTalk Boundary

LabTalk is an optional educational overlay, not a required engine dependency.

Keep these layers separate:

```text
source evidence DOCX/images/decks
  -> normalized docs/cases/CASE_*.md records
  -> runtime CASE command
  -> manuals/decks/storyboards/publication products
```

The CASE catalog work follows the same doctrine:

- source evidence is preserved
- normalized case files are runtime-readable derivatives
- publication gates remain explicit
- runtime proof is required for engineering claims
- educational material should not leak into engine/professional profiles unless enabled

## How I Have Been Working With DotTalk++

The successful pattern has been:

1. Read existing reports before touching code.
2. Search with `rg` for command names, schemas, and status files.
3. Identify which layer owns the issue: source, runtime, HELP, metadata, SelfDoc, manualgen, LabTalk, or data dictionary.
4. Prefer report-only inventories first.
5. Patch only the narrow artifact that is actually misaligned.
6. Preserve source evidence folders.
7. Run the current executable when possible to capture proof.
8. Write a new review/closeout document instead of rewriting history.

That is why recent LabTalk work fixed registry drift, added inventory and proof scaffolds, and left publication gates closed instead of declaring the cases finished.

## AI Agent Rules

Future AI agents should follow these rules:

- Never assume all generated files are junk.
- Never delete or move source DOCX/case/evidence folders casually.
- Never promote candidate schemas or scripts just because they look complete.
- Never treat SelfDoc classifications as automatic repair authorization.
- Never mutate DBF/CDX/LMDB/HELP/manualgen outputs without an explicit safety gate.
- Prefer small reports, registries, and proof packets over broad rewrites.
- Keep optional overlays optional.
- Preserve dirty user work; inspect before editing.
- If a command can prove behavior, run the runtime and capture the proof.
- If proof requires fixture setup, say that and leave the gate open.

## Human Developer Rules

Human developers can move faster, but the same boundaries matter:

- Put new commands near their owner subsystem and add usage metadata.
- Add HELP/CMDHELPCHK expectations only after runtime behavior is stable.
- Add schema contracts before import/promote scripts.
- Add DotScript smoke tests for repeatable behavior.
- Capture runtime transcripts for important claims.
- Store publication material as derived output, not as the only source.
- Use MDO/status documents to leave a trail for the next maintainer.

## Naming Patterns Worth Preserving

The repo uses names as lifecycle markers. Keep using them:

| Pattern | Meaning |
|---|---|
| `*_PLAN_*` | Design or proposed route, no mutation implied. |
| `*_STATUS.*` | Current closeout/status statement. |
| `*_REVIEW_*` | Evidence review or human/agent assessment. |
| `*_CANDIDATE_*` | Generated or proposed artifact not yet canonical. |
| `*_PROOF_*` | Runtime or structural evidence. |
| `*_PACKAGE_*` | Bundled action or promotion unit. |
| `*_REGISTRY_*` | Catalog of governed objects. |
| `*_BOUNDARY_*` | Explicit separation of ownership/safety/profile. |

## Practical Next Work Pattern

For any new feature or repair:

1. Create or update a short plan/status doc.
2. Identify source-of-truth files.
3. Identify generated/candidate outputs.
4. Define safety class.
5. Make the narrow change.
6. Run runtime or structural validation.
7. Save proof.
8. Update the relevant registry.
9. Leave open gates explicit.

Example closeout shape:

```text
Changed:
- registry alignment
- case front matter
- proof packet scaffold

Verified:
- 15 loader-visible files
- no missing sections
- runtime CASE LIST passes

Still open:
- behavioral fixture proof
- media review
- human publication approval
```

That style is more valuable here than a large undocumented code drop.

## Current Mental Model

The project is strongest when treated as a transparent database engine with a documentation and teaching system wrapped around it.

The goal is not merely to make commands work. The goal is to make records, indexes, relations, schemas, scripts, metadata, HELP, and history explain themselves well enough that a developer, student, or AI agent can reason about the system without guessing.

That is the pattern to continue.

<!-- END SOURCE CONTENT -->

---

# Source: LabTalk Source to Case Inventory v1

Path: `LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md`

<!-- BEGIN SOURCE CONTENT -->

# LabTalk Source-to-Case Inventory v1

Status: controlled planning artifact.

This inventory maps source/evidence material to normalized runtime-readable case records. It does not move, rewrite, or promote historical source files.

## Source Roots

| Root | Role | Handling |
|---|---|---|
| `dottalkpp/cases` | Primary source/evidence folder for uploaded DOCX files and older case folders. | Preserve as source evidence. Do not normalize in place. |
| `dottalkpp/docs/dottalkpp_legacy_doc_review_2026_05_09/02_EDU_CURRICULUM_INCUBATOR` | Legacy education/curriculum intake material. | Use as additional source evidence after review. |
| `docs/cases` | Runtime-readable normalized case catalog. | Maintain as derived CASE_*.md records and registries. |
| `x64base/docs` | Storyboard deck and LabTalk publication notes. | Treat as derived publication/media material. |

## Evidence Files Seen

| File | Current source path | Notes |
|---|---|---|
| `Case Studies Core Track.docx` | `dottalkpp/cases/Case Studies Core Track.docx` | Broad source for overview and engineering case framing. |
| `DottalkEd.docx` | `dottalkpp/cases/DottalkEd.docx` | Source for DotTalk++/LabTalk education framing. |
| `FoxPro -> DotTalkpp crosswalk (1).docx` | `dottalkpp/cases/FoxPro -> DotTalkpp crosswalk (1).docx` | Source for xBase/FoxPro crosswalk. Registry now preserves the actual filename spelling. |
| `Army_73C.docx` | `dottalkpp/cases/case001/Army_73C.docx` | Source for JUMPS/73C case. |
| `JUMPS in 1983 ran on IBM mainframes.docx` | `dottalkpp/cases/case001/JUMPS in 1983 ran on IBM mainframes.docx` | Source for JUMPS/73C case. |
| `unisys.docx` | `dottalkpp/cases/case003/unisys.docx` | Source for Unisys/CODASYL/ALCOA case. |
| `PAXON.docx` | `dottalkpp/cases/case004/PAXON.docx` | Source candidate for TitleSCAN/Paxon transfer case. |
| `LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx` | `x64base/docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck.pptx` | Derived storyboard/publication deck. |
| `LabTalk_DotTalkpp_Systems_Storyboard_Deck_NOTES.md` | `x64base/docs/LabTalk_DotTalkpp_Systems_Storyboard_Deck_NOTES.md` | Derived storyboard notes. |

## Case State Matrix

| Case | Source state | Normalized CASE_*.md | Storyboard/media | Runtime state | Publication state |
|---|---|---|---|---|---|
| HIST-000 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate. |
| HIST-010 | Source still needs attachment/review. | Yes, stub. | Media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-020 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate, needs fact review. |
| HIST-030 | Source doc identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate, needs source review. |
| HIST-040 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate, needs source review. |
| HIST-050 | Source still needs attachment/review. | Yes, stub. | Media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-060 | PAXON source candidate identified. | Yes, stub. | Shared media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-070 | Source still needs attachment/review. | Yes, stub. | Shared media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-080 | Source still needs attachment/review. | Yes, stub. | Media registered. | Runtime-readable, hidden. | Stub only. |
| HIST-090 | Source docs identified. | Yes. | Media registered. | Runtime-readable, hidden. | First-wave review candidate. |
| ENG-010 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-020 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-030 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-040 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |
| ENG-050 | Source doc identified. | Yes. | No media claimed. | Runtime-readable, proof scaffold attached. | Needs runtime proof. |

## Promotion Gate

The five first-wave historical cases are promoted only to `first_wave_review_candidate`. They remain `hidden_until_reviewed` until source review, factual review, media review, and runtime/lab review are complete.

<!-- END SOURCE CONTENT -->

---

# Source: LabTalk Overlay Boundary v1

Path: `LABTALK_OVERLAY_BOUNDARY_V1.md`

<!-- BEGIN SOURCE CONTENT -->

# LabTalk Overlay Boundary v1

LabTalk is an optional educational/publication layer over DotTalk++ and x64base. It must not become a hard dependency of the core engine.

## Boundaries

| Layer | Owns | Must not require |
|---|---|---|
| x64base engine | Storage, indexing, low-level runtime behavior, metadata-capable structures. | LabTalk cases, storyboards, student examples, or publication media. |
| DotTalk++ runtime | Command shell, HELP, data navigation, work areas, relations, tuples, runtime proof. | Published LabTalk material. |
| LabTalk overlay | CASE catalog, teaching sequence, case studies, labs, storyboards, classroom/publication products. | Core engine changes unless a runtime behavior is genuinely missing. |
| SelfDoc/manualgen | Provenance, review gates, generated/manual publication products. | Unreviewed case content as final source truth. |

## Packaging Rule

Educational material belongs in optional overlay packages or clearly marked documentation paths. A build or runtime profile that only wants x64base/DotTalk++ professional behavior should remain usable without LabTalk source docs, case media, or storyboards.

## Runtime Rule

The CASE command may read normalized `docs/cases/CASE_*.md` records. Those records are derived catalog entries, not the source of truth. Source DOCX files, images, and deck files stay preserved as evidence and publication artifacts.

## Publication Rule

No case should be marked publication-ready until all of these are complete:

- source review
- factual review
- media review
- runtime/lab proof, when the case claims executable behavior

<!-- END SOURCE CONTENT -->

---

# Source: LabTalk ENG Runtime Proof Plan v1

Path: `LABTALK_ENG_RUNTIME_PROOF_PLAN_V1.md`

<!-- BEGIN SOURCE CONTENT -->

# LabTalk Engineering Case Runtime Proof Plan v1

Status: catalog-read proof captured, behavioral fixture proof still open.

The ENG cases are runtime-lab candidates. Each now has a proof packet and catalog-read proof from `CASE SHOW <id>`. Each still needs a behavioral fixture transcript before it can move beyond `needs_runtime_proof_attachment`.

## Proof Packet Contract

Each proof packet should contain:

- command script or exact manual command sequence
- expected output summary
- captured output or transcript
- build/runtime version or commit identifier
- data fixture path
- pass/fail status
- reviewer/date

## Case Proof Targets

| Case | Proof packet | Minimum proof |
|---|---|---|
| ENG-010 | `runtime_proofs/ENG-010_RUNTIME_PROOF.md` | Show physical order versus active index/logical order using CDX or LMDB-backed navigation. |
| ENG-020 | `runtime_proofs/ENG-020_RUNTIME_PROOF.md` | Show SEEK behavior compared with SCAN/predicate traversal on the same fixture. |
| ENG-030 | `runtime_proofs/ENG-030_RUNTIME_PROOF.md` | Show buffering/dirty state and COMMIT/ROLLBACK lifecycle or document why the current runtime lacks the full behavior. |
| ENG-040 | `runtime_proofs/ENG-040_RUNTIME_PROOF.md` | Show metadata/help/catalog evidence and a validation check such as CMDHELPCHK or equivalent report. |
| ENG-050 | `runtime_proofs/ENG-050_RUNTIME_PROOF.md` | Show file/table/index/backend separation with a fixture that proves storage and navigation are distinct concerns. |

## Gate

Do not change ENG case `review_status` until its proof packet contains behavioral captured output and reviewer acceptance.

<!-- END SOURCE CONTENT -->

---

# Source: LabTalk Case Review v2

Path: `LABTALK_CASE_REVIEW_V2.md`

<!-- BEGIN SOURCE CONTENT -->

# LabTalk Case Catalog Review v2

Safety: REPORT_ONLY / NO SOURCE-EVIDENCE MUTATION.

## Summary

- case_files: 15
- runtime_loadable_failures: 0
- registry_alignment_warn_or_fail: 0
- media_reference_warn_or_fail: 0
- first_wave_review_candidate: 5
- stub_registered: 5
- runtime_lab_candidate: 5
- gate: REVIEW_V2_STRUCTURE_GREEN_MEDIA_DRIFT_CLOSED_CATALOG_PROOF_CAPTURED_BEHAVIORAL_PROOF_OPEN

## Changes Since v1

The catalog no longer has active media-reference drift. Historical stub cases now reference media IDs that exist in `MEDIA_ASSET_REGISTRY_v0.csv`. Engineering runtime-lab cases no longer claim placeholder media IDs; they now point to runtime proof packets instead.

The FoxPro crosswalk source filename is aligned to the observed source spelling: `FoxPro -> DotTalkpp crosswalk (1).docx`.

The five strongest historical cases are now marked `first_wave_review_candidate`:

- HIST-000 The Data Trail Overview
- HIST-020 JUMPS / 73C Army System
- HIST-030 Unisys / CODASYL at ALCOA
- HIST-040 xBase as a Major Platform
- HIST-090 DotTalk++ / LabTalk and the AI Future

These are not publication-ready. They remain `hidden_until_reviewed`.

## New Control Artifacts

- `LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md`
- `LABTALK_OVERLAY_BOUNDARY_V1.md`
- `LABTALK_ENG_RUNTIME_PROOF_PLAN_V1.md`
- `runtime_proofs/ENG-010_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-020_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-030_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-040_RUNTIME_PROOF.md`
- `runtime_proofs/ENG-050_RUNTIME_PROOF.md`

The five ENG proof packets include catalog-read proof from `CASE SHOW ENG-010` through `CASE SHOW ENG-050` against `D:\code\ccode\build\src\Release\dottalkpp.exe` on 2026-06-28. Behavioral fixture proof remains open.

## Open Gates

The current structure is green, but publication gates remain open:

- first-wave historical cases still need source/factual/media review closure
- ENG cases still need behavioral fixture proof beyond catalog rendering
- all cases remain hidden until reviewed

## Boundary

LabTalk remains an optional education overlay. No source DOCX, storyboard deck, case media, or student-facing case prose is required for the x64base engine boundary.

<!-- END SOURCE CONTENT -->

---

# Source: README_CASES_v0.md

Path: `docs/cases/README_CASES_v0.md`

<!-- BEGIN SOURCE CONTENT -->

# DotTalk++ / LabTalk Case Catalog Seed v0

Generated normalization seed for docs/cases.

## Contents

- 15 runtime-readable CASE_*.md files
- CASE_FRAMEWORK.md template/boundary file
- REGISTRY_CASES_v0.csv and REGISTRY_CASES_v0.md
- MEDIA_ASSET_REGISTRY_v0.csv
- ../../LABTALK_SOURCE_TO_CASE_INVENTORY_V1.md source-to-case state matrix
- ../../LABTALK_OVERLAY_BOUNDARY_V1.md optional overlay boundary
- ../../LABTALK_ENG_RUNTIME_PROOF_PLAN_V1.md and runtime_proofs/* proof scaffolds
- INSTALL_CASES.ps1 staging helper

## First-wave review candidates

- HIST-000 The Data Trail Overview
- HIST-020 JUMPS / 73C Army System
- HIST-030 Unisys / CODASYL at ALCOA
- HIST-040 xBase as a Major Platform
- HIST-090 DotTalk++ / LabTalk and the AI Future

These are review candidates, not publication-ready cases. They remain hidden until source, factual, media, and runtime/lab review gates are closed.

## Stubbed or candidate cases

The remaining HIST-* and ENG-* cases are present from the start so they are not forgotten, but they are not publication-ready.

## Installation target

Copy the docs/cases directory into the repository root so DotTalk++ can discover it at:

    <repo-root>/docs/cases

The current loader searches docs/cases, ../docs/cases, and ../../docs/cases.

## Boundary

LabTalk case files are an optional educational overlay. Core x64base and professional DotTalk++ runtime behavior should remain usable without case media, storyboards, or source DOCX files.

<!-- END SOURCE CONTENT -->

---

# Source: REGISTRY_CASES_v0.md

Path: `docs/cases/REGISTRY_CASES_v0.md`

<!-- BEGIN SOURCE CONTENT -->

# Case Registry v0

| ID | File | Title | Status | Review | Runtime |
|---|---|---|---|---|---|
| HIST-000 | `CASE_HIST_000_DATA_TRAIL_OVERVIEW.md` | The Data Trail Overview | first_wave_review_candidate | normalized_draft | hidden_until_reviewed |
| HIST-020 | `CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM.md` | JUMPS / 73C Army System | first_wave_review_candidate | needs_fact_review | hidden_until_reviewed |
| HIST-030 | `CASE_HIST_030_UNISYS_CODASYL_ALCOA.md` | Unisys / CODASYL at ALCOA | first_wave_review_candidate | needs_source_review | hidden_until_reviewed |
| HIST-040 | `CASE_HIST_040_XBASE_MAJOR_PLATFORM.md` | xBase as a Major Platform | first_wave_review_candidate | needs_source_review | hidden_until_reviewed |
| HIST-090 | `CASE_HIST_090_DOTTALK_LABTALK_AI_FUTURE.md` | DotTalk++ / LabTalk and the AI Future | first_wave_review_candidate | normalized_draft | hidden_until_reviewed |
| HIST-010 | `CASE_HIST_010_COBOL_CONNECTED_COMPUTERS.md` | COBOL and Connected Computers | stub_registered | needs_source_review | hidden_until_reviewed |
| HIST-050 | `CASE_HIST_050_EARTHKIDS_CAREPAX.md` | Earthkids to CAREPAX | stub_registered | needs_source_review | hidden_until_reviewed |
| HIST-060 | `CASE_HIST_060_TITLESCAN_PAXON_DATABASE_TRANSFERS.md` | TitleSCAN / Paxon Database Transfers | stub_registered | needs_source_review | hidden_until_reviewed |
| HIST-070 | `CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE.md` | ERP, SQL, Auto-ID, and Industrial Scale | stub_registered | needs_source_review | hidden_until_reviewed |
| HIST-080 | `CASE_HIST_080_HYNIX_SEMICONDUCTOR_PROCESS_DATA.md` | HYNIX Semiconductor Process Data | stub_registered | needs_source_review | hidden_until_reviewed |
| ENG-010 | `CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB.md` | Indexed Navigation: CDX / LMDB | runtime_lab_candidate | needs_runtime_proof_attachment | hidden_until_reviewed |
| ENG-020 | `CASE_ENG_020_SEEK_VS_SCAN.md` | SEEK vs SCAN | runtime_lab_candidate | needs_runtime_proof_attachment | hidden_until_reviewed |
| ENG-030 | `CASE_ENG_030_BUFFERING_COMMIT_LIFECYCLE.md` | Buffering and COMMIT Lifecycle | runtime_lab_candidate | needs_runtime_proof_attachment | hidden_until_reviewed |
| ENG-040 | `CASE_ENG_040_METADATA_DATA_DICTIONARY.md` | Metadata and Data Dictionary | runtime_lab_candidate | needs_runtime_proof_attachment | hidden_until_reviewed |
| ENG-050 | `CASE_ENG_050_FILE_ENGINE_SEPARATION.md` | File-Based DB to Engine-Based DB | runtime_lab_candidate | needs_runtime_proof_attachment | hidden_until_reviewed |

<!-- END SOURCE CONTENT -->

---

# Source: CASE_FRAMEWORK.md

Path: `docs/cases/CASE_FRAMEWORK.md`

<!-- BEGIN SOURCE CONTENT -->

# CASE_FRAMEWORK

This file is intentionally named CASE_FRAMEWORK.md so the current case catalog loader skips it.

## Purpose

The normalized CASE_*.md files are runtime-readable derivatives of source/evidence material. They are not the source of truth by themselves.

## Current loader contract

The uploaded case_catalog.cpp loader expects files under docs/cases whose filenames start with CASE_ and end in .md. It reads simple front matter fields id, title, type, era, level, lab, and domains. It extracts these body sections:

- SUMMARY
- PROBLEM
- WORKFLOW
- MODEL
- TAKEAWAY

## Boundary

- Source DOCX files and images remain evidence assets.
- CASE_*.md files are normalized catalog entries.
- runtime_visibility: hidden_until_reviewed means registered but not student/runtime-published.
- manual_visibility: outline_only means table-of-contents presence only.
- Engineering cases need an attached runtime proof packet before promotion.
- LabTalk/cases/media are optional overlay artifacts, not required x64base engine dependencies.

## Promotion rule

A case should not become publication-ready until source review, factual review, media review, and runtime/lab review have passed.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB

Path: `docs/cases/CASE_ENG_010_INDEX_NAVIGATION_CDX_LMDB.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: ENG-010
title: Indexed Navigation: CDX / LMDB
type: engine_case
era: 1985-present
level: student
lab: LAB_CASE_INDEX_NAVIGATION
domains: [xbase, indexes, cdx, lmdb, logical-order]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-010_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case demonstrates that logical order is not the same thing as physical record order. It uses FoxPro-style index navigation, CDX tags, and the LMDB-backed index environment as the teaching bridge.

## PROBLEM

Sequential scans are easy to understand but slow and limited. Students need to see why indexes are navigation structures, not only lookup accelerators.

## WORKFLOW

Run USE STUDENTS, SET INDEX TO STUDENTS, SET ORDER TO TAG LNAME, SMARTLIST, TOP, and SKIP. Observe the difference between physical recno and logical order.

## MODEL

The model is record storage plus an order/index layer. CDX is the user-facing logical container. LMDB is backend implementation detail. DotTalk++ should expose the order concept without leaking backend terminology into ordinary teaching prose.

## TAKEAWAY

Indexes are navigation systems. SQL often hides this behind ORDER BY and optimizer choices; DotTalk++ can show it directly.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_ENG_020_SEEK_VS_SCAN

Path: `docs/cases/CASE_ENG_020_SEEK_VS_SCAN.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: ENG-020
title: SEEK vs SCAN
type: engine_case
era: 1985-present
level: student
lab: LAB_CASE_SEEK_VS_SCAN
domains: [seek, scan, predicate, index, execution-plan]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-020_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case contrasts point lookup through an active order with sequential predicate evaluation.

## PROBLEM

Finding a record is not one operation internally. A system may seek through an index, scan records, or combine strategies. Students should learn to distinguish exact keyed lookup from predicate search.

## WORKFLOW

Run SET ORDER TO TAG LNAME, then SEEK a known key with tracing. Compare with a scan or predicate-style query. Observe key comparison, early termination, and fallback behavior.

## MODEL

The model is access-path selection. Old xBase exposes SEEK and SCAN/LOCATE directly; modern SQL describes similar choices as index seek and index scan inside an execution plan.

## TAKEAWAY

All databases still make this decision. DotTalk++ can make the decision visible.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_ENG_030_BUFFERING_COMMIT_LIFECYCLE

Path: `docs/cases/CASE_ENG_030_BUFFERING_COMMIT_LIFECYCLE.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: ENG-030
title: Buffering and COMMIT Lifecycle
type: engine_case
era: 1990s-present
level: student
lab: LAB_CASE_BUFFERING_COMMIT
domains: [buffering, commit, rollback, transaction, lmdb]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-030_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case shows that transactions are lifecycle orchestration, not just a COMMIT command.

## PROBLEM

Buffered edits need safety before persistence, and index backends may have to detach and reattach around physical writes and rebuilds. The project has already observed a COMMIT/BUILDLMDB lifecycle canary.

## WORKFLOW

Use table buffering, perform a REPLACE, then COMMIT. Observe staged state, persisted state, backend detach/rebuild/reattach expectations, and any canary output.

## MODEL

The model is staged mutation plus persistence plus index synchronization. The correct teaching surface should distinguish buffered values, persisted records, and rebuilt navigation structures.

## TAKEAWAY

COMMIT is not magic. It is an ordered lifecycle that protects consistency.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_ENG_040_METADATA_DATA_DICTIONARY

Path: `docs/cases/CASE_ENG_040_METADATA_DATA_DICTIONARY.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: ENG-040
title: Metadata and Data Dictionary
type: engine_case
era: 1980s-present
level: student
lab: LAB_CASE_METADATA_DICTIONARY
domains: [metadata, catalog, help, commands, functions, data-dictionary]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-040_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case explains the project pivot from hardcoded documentation toward catalog-backed metadata.

## PROBLEM

Commands, functions, help text, usage contracts, source comments, and system messages can drift unless they are cataloged and validated. Sidecars are fragile if they cannot be regenerated or checked.

## WORKFLOW

Use HELP and catalog/report commands to show how command/function metadata can be harvested, compared, validated, and eventually repaired. Keep the lab report-only until mutation is explicitly authorized.

## MODEL

The model is metadata-backed documentation: source defines, runtime proves, HELP explains, metadata organizes, CMDHELPCHK validates, and SelfDoc preserves provenance.

## TAKEAWAY

A serious teaching system needs a data dictionary for its own behavior, not only for user tables.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_ENG_050_FILE_ENGINE_SEPARATION

Path: `docs/cases/CASE_ENG_050_FILE_ENGINE_SEPARATION.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: ENG-050
title: File-Based DB to Engine-Based DB
type: engine_case
era: 1980s-present
level: student
lab: LAB_CASE_FILE_ENGINE_SEPARATION
domains: [dbf, xdbf, cdx, lmdb, storage-abstraction]
status: runtime_lab_candidate
review_status: needs_runtime_proof_attachment
evidence_class: source_doc_plus_project_status
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx]
media_assets: []
runtime_proof: [runtime_proofs/ENG-050_RUNTIME_PROOF.md]
---

## SUMMARY

This runtime case explains how database systems separate table storage, indexing, execution, and projection.

## PROBLEM

Flat files are understandable but do not fully explain modern database behavior. Students need to see how file format, index abstraction, and backend engine responsibilities differ.

## WORKFLOW

Run STATUS and AREA, inspect open work areas and paths, then compare DBF/XDBF table data, CDX logical index containers, and backend index environment paths. Use this case carefully so backend details teach architecture rather than confuse beginners.

## MODEL

The model separates raw table storage from logical indexing and physical backend implementation. DbArea owns records and mutation; CDX owns user-facing logical tags; LMDB remains physical backend; projection commands render views of the same underlying data.

## TAKEAWAY

Modern databases separate storage, indexing, execution, and projection. DotTalk++ makes that separation visible enough to teach.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_000_DATA_TRAIL_OVERVIEW

Path: `docs/cases/CASE_HIST_000_DATA_TRAIL_OVERVIEW.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-000
title: The Data Trail Overview
type: historical_case
era: 1970s-present
level: student
lab: LAB_CASE_DATA_TRAIL_OVERVIEW
domains: [data-history, systems-history, database-literacy, ai-literacy]
status: first_wave_review_candidate
review_status: normalized_draft
evidence_class: synthesis_from_uploaded_sources
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Case Studies Core Track.docx, DottalkEd.docx]
media_assets: [MEDIA_CASE_DATA_TRAIL_OVERVIEW_V1]
---

## SUMMARY

This overview case provides the spine for the full DotTalk++ / LabTalk case universe. The story is not a set of disconnected anecdotes. It is a continuous data trail: paper records, punch cards, batch runs, terminals, navigational databases, xBase, document indexing, ERP, industrial data capture, semiconductor-scale process data, and finally DotTalk++ / LabTalk as an explainable teaching environment.

## PROBLEM

Students often see database systems as isolated products. The project needs a stable storyline that shows how records, fields, workflows, indexes, reports, validations, and exceptions evolved across real systems.

## WORKFLOW

Use this case as the opening orientation. Present each later case as one stop on the data trail. Do not try to teach every technical detail at once. The progression should move from structured records to batch processing, from navigational access to xBase, from file systems to engines, from automation to explanation, and finally to AI-era literacy.

## MODEL

The model has three cooperating layers: DotTalk++ executes and exposes system behavior; LabTalk sequences the demonstrations and explains what to observe; the Case Studies explain why the systems existed and what design pressure each era created. Source DOCX files and storyboard images remain evidence assets; CASE_*.md files are normalized runtime-readable derivatives.

## TAKEAWAY

The catalog should preserve the whole story from the beginning. Developed cases and stubs belong in the same registry so later manuals, decks, and runtime lessons do not drift into different versions of reality.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_010_COBOL_CONNECTED_COMPUTERS

Path: `docs/cases/CASE_HIST_010_COBOL_CONNECTED_COMPUTERS.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-010
title: COBOL and Connected Computers
type: historical_case
era: 1950s-1970s
level: student
lab: 
domains: [cobol, mainframe, business-data, early-networking]
status: stub_registered
review_status: needs_source_review
evidence_class: stub_from_project_memory_and_uploaded_assets
runtime_visibility: hidden_until_reviewed
manual_visibility: outline_only
source_docs: [to_be_attached_or_reviewed]
media_assets: [MEDIA_CASE_COBOL_CONNECTED_COMPUTERS_V1]
---

## SUMMARY

Stub registered. Stub registered for the early business-computing and connected-computers foundation. This case will explain records, files, batch programs, COBOL, terminals, and the move toward connected systems.

This file exists now so the case is present in the catalog from the start, but it is not publication-ready.

## PROBLEM

To be developed.

## WORKFLOW

To be developed.

## MODEL

To be developed.

## TAKEAWAY

To be developed.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM

Path: `docs/cases/CASE_HIST_020_JUMPS_73C_ARMY_SYSTEM.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-020
title: JUMPS / 73C Army System
type: historical_case
era: 1983-1985
level: student
lab: LAB_CASE_JUMPS_73C
domains: [batch-processing, structured-data, forms, finance, mainframe, workflow]
status: first_wave_review_candidate
review_status: needs_fact_review
evidence_class: lived_history_plus_reconstruction
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [Army_73C.docx, JUMPS in 1983 ran on IBM mainframes.docx]
media_assets: [MEDIA_CASE_JUMPS_BOARD_V1]
---

## SUMMARY

This case turns the 73C Army finance workflow into a teaching module about structured data, forms, validation, batch processing, rejects, correction loops, and human-in-the-middle systems. The core scenario is the PCS arrival workflow where entitlements and travel settlement feed into the same JUMPS batch cycle.

## PROBLEM

A soldier arrival created multiple structured obligations: update entitlements, process travel, encode records, assemble a batch, wait for mainframe results, read outputs, correct rejects, and run again. The challenge was not just clerical entry; it was structured reasoning under strict formats and delayed feedback.

## WORKFLOW

Start with DA Form 3685 and DD Form 1351-2 as schemas. Then walk the integrated pipeline: finance inprocessing, entitlement update, travel voucher, punch-card encoding, batch assembly, JUMPS run, LES/travel settlement/rejects, correction, and rerun. LabTalk can later simulate this with commands such as 3685.UPDATE, 1351.NEW, CARD.OUT, CARD.VERIFY, BATCH.ASSEMBLE, BATCH.RUN, OUTPUT.GET, REJECTS.LIST, and REJECTS.FIX.

## MODEL

The model is a batch system with typed records, fixed-field forms, validation rules, rate/date computation, delayed output, and human correction loops. This should be framed as a precursor to ETL, business-rule engines, validation pipelines, and batch-oriented enterprise processing. Hardware/language claims that are not independently confirmed must remain marked as reconstruction or inference.

## TAKEAWAY

The 73C case is one of the strongest bridges between lived workflow and database literacy. It shows that structured data is not abstract: it controls money, travel, exceptions, and real human outcomes.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_030_UNISYS_CODASYL_ALCOA

Path: `docs/cases/CASE_HIST_030_UNISYS_CODASYL_ALCOA.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-030
title: Unisys / CODASYL at ALCOA
type: historical_case
era: 1970s-1980s
level: student
lab: LAB_CASE_CODASYL_SETS_RINGS
domains: [codasyl, network-database, sets, rings, industrial-data, relations]
status: first_wave_review_candidate
review_status: needs_source_review
evidence_class: lived_history_plus_source_docs
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [unisys.docx]
media_assets: [MEDIA_CASE_CODASYL_ALCOA_V1]
---

## SUMMARY

This case explains the network database model through the remembered Unisys / CODASYL vocabulary of sets and rings, then connects that older navigational mindset to DotTalk++ REL and REL ENUM.

## PROBLEM

Before SQL-style declarative querying became dominant, many systems required programmers to know the path through data. Relationships were not merely logical; they could also be access paths that had to be traversed procedurally.

## WORKFLOW

Teach SET as an owner/member relationship and RING as the physical chain of related members. Then show how a COBOL-style program might find an owner and walk members one by one. Finally compare the idea with DotTalk++ relation traversal, where REL defines the relationship and REL ENUM can enumerate related tuples without exposing physical pointer rings.

## MODEL

The conceptual model is navigational access. Old systems walked paths. Relational systems describe desired results. DotTalk++ can teach both: it can preserve the idea of relationship traversal while making the relationship inspectable and explainable.

## TAKEAWAY

This case gives students a vocabulary for why SQL was a major shift and why relation traversal still matters. It also prevents REL ENUM from looking like a random DotTalk++ feature; it becomes part of a historical lineage.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_040_XBASE_MAJOR_PLATFORM

Path: `docs/cases/CASE_HIST_040_XBASE_MAJOR_PLATFORM.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-040
title: xBase as a Major Platform
type: historical_case
era: 1980s-2000s
level: student
lab: LAB_CASE_XBASE_PLATFORM
domains: [xbase, dbase, clipper, foxpro, visual-foxpro, access, odbc, excel]
status: first_wave_review_candidate
review_status: needs_source_review
evidence_class: project_doctrine_plus_crosswalk
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [FoxPro -> DotTalkpp crosswalk (1).docx, DottalkEd.docx]
media_assets: [MEDIA_CASE_XBASE_PLATFORM_V1]
---

## SUMMARY

This case elevates xBase from a side note to a major platform chapter. It covers the world where dBASE, Clipper, FoxPro, Visual FoxPro, Access, Excel, ODBC, and SQL Server shaped business database work.

## PROBLEM

Students may assume xBase was only a legacy file format. The case should show that xBase was a practical application-development platform with commands, navigation, indexing, reports, and business workflows.

## WORKFLOW

Use commands such as USE, LIST, DISPLAY, TOP, SKIP, SEEK, DELETE, RECALL, PACK, APPEND, COPY TO, EXPORT, IMPORT, SET ORDER, and SET DELETED to connect FoxPro-style work to DotTalk++ behavior. Then contrast direct command navigation with hidden optimizer behavior in SQL systems.

## MODEL

The model is a stateful command shell over records, fields, areas, orders, filters, indexes, expressions, and projections. DotTalk++ does not merely imitate this: it makes the state observable and then links that observability to ED/ARCH/HELP/LabTalk concepts.

## TAKEAWAY

The xBase case is the bridge between historical business programming and DotTalk++ as the path not taken: a serious continuation of xBase ideas into a 64-bit, explainable, metadata-aware teaching runtime.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_050_EARTHKIDS_CAREPAX

Path: `docs/cases/CASE_HIST_050_EARTHKIDS_CAREPAX.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-050
title: Earthkids to CAREPAX
type: historical_case
era: 1990s
level: student
lab: 
domains: [daycare-administration, receivables, vaccination-scheduling, adoption, market-fit]
status: stub_registered
review_status: needs_source_review
evidence_class: stub_from_project_memory_and_uploaded_assets
runtime_visibility: hidden_until_reviewed
manual_visibility: outline_only
source_docs: [to_be_attached_or_reviewed]
media_assets: [MEDIA_CASE_EARTHKIDS_CAREPAX_V1]
---

## SUMMARY

Stub registered. Stub registered for the Earthkids/CAREPAX adoption lesson. This case must use the corrected framing: daycare time/attendance, receivables, and vaccination scheduling, not environmental education marketing.

This file exists now so the case is present in the catalog from the start, but it is not publication-ready.

## PROBLEM

To be developed.

## WORKFLOW

To be developed.

## MODEL

To be developed.

## TAKEAWAY

To be developed.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_060_TITLESCAN_PAXON_DATABASE_TRANSFERS

Path: `docs/cases/CASE_HIST_060_TITLESCAN_PAXON_DATABASE_TRANSFERS.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-060
title: TitleSCAN / Paxon Database Transfers
type: historical_case
era: 1990s-2000s
level: student
lab: 
domains: [title-records, document-indexing, database-transfer, search, conversion]
status: stub_registered
review_status: needs_source_review
evidence_class: stub_from_project_memory_and_uploaded_assets
runtime_visibility: hidden_until_reviewed
manual_visibility: outline_only
source_docs: [PAXON.docx]
media_assets: [MEDIA_CASE_TRANSFER_ERP_INDUSTRIAL_V1]
---

## SUMMARY

Stub registered. Stub registered for the TitleSCAN/Paxon database-transfer and title-records case. Personal/public-record details from source notes should not be promoted into student-facing prose; focus on title plants, indexing, records, conversion, and searchability.

This file exists now so the case is present in the catalog from the start, but it is not publication-ready.

## PROBLEM

To be developed.

## WORKFLOW

To be developed.

## MODEL

To be developed.

## TAKEAWAY

To be developed.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE

Path: `docs/cases/CASE_HIST_070_ERP_SQL_AUTOID_INDUSTRIAL_SCALE.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-070
title: ERP, SQL, Auto-ID, and Industrial Scale
type: historical_case
era: 1990s-2010s
level: student
lab: 
domains: [erp, sql, sap, barcode, auto-id, industrial-workflow]
status: stub_registered
review_status: needs_source_review
evidence_class: stub_from_project_memory_and_uploaded_assets
runtime_visibility: hidden_until_reviewed
manual_visibility: outline_only
source_docs: [to_be_attached_or_reviewed]
media_assets: [MEDIA_CASE_TRANSFER_ERP_INDUSTRIAL_V1]
---

## SUMMARY

Stub registered. Stub registered for the ERP/SQL/Auto-ID industrial-scale case. This should connect transaction capture, enterprise integration, SQL data stores, reports, and workflow standardization.

This file exists now so the case is present in the catalog from the start, but it is not publication-ready.

## PROBLEM

To be developed.

## WORKFLOW

To be developed.

## MODEL

To be developed.

## TAKEAWAY

To be developed.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_080_HYNIX_SEMICONDUCTOR_PROCESS_DATA

Path: `docs/cases/CASE_HIST_080_HYNIX_SEMICONDUCTOR_PROCESS_DATA.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-080
title: HYNIX Semiconductor Process Data
type: historical_case
era: 2000s-2010s
level: student
lab: 
domains: [semiconductor, process-data, yield, manufacturing, traceability]
status: stub_registered
review_status: needs_source_review
evidence_class: stub_from_project_memory_and_uploaded_assets
runtime_visibility: hidden_until_reviewed
manual_visibility: outline_only
source_docs: [to_be_attached_or_reviewed]
media_assets: [MEDIA_CASE_HYNIX_PROCESS_DATA_V1]
---

## SUMMARY

Stub registered. Stub registered for semiconductor process data. This should show the jump from business records to high-volume precision manufacturing data, yield, traceability, and process control.

This file exists now so the case is present in the catalog from the start, but it is not publication-ready.

## PROBLEM

To be developed.

## WORKFLOW

To be developed.

## MODEL

To be developed.

## TAKEAWAY

To be developed.

<!-- END SOURCE CONTENT -->

---

# Source: CASE_HIST_090_DOTTALK_LABTALK_AI_FUTURE

Path: `docs/cases/CASE_HIST_090_DOTTALK_LABTALK_AI_FUTURE.md`

<!-- BEGIN SOURCE CONTENT -->

---
id: HIST-090
title: DotTalk++ / LabTalk and the AI Future
type: historical_case
era: present-future
level: student
lab: LAB_CASE_DOTTALK_AI_FUTURE
domains: [dottalkpp, labtalk, ai-literacy, database-literacy, observability, help, metadata]
status: first_wave_review_candidate
review_status: normalized_draft
evidence_class: project_doctrine_plus_uploaded_sources
runtime_visibility: hidden_until_reviewed
manual_visibility: draft_outline
source_docs: [DottalkEd.docx, Case Studies Core Track.docx]
media_assets: [MEDIA_CASE_DOTTALK_LABTALK_AI_FUTURE_V1]
---

## SUMMARY

This capstone case presents DotTalk++ and LabTalk as an explainable database literacy environment for the AI age. The premise is that students who can understand records, fields, indexes, relations, reports, state, and workflows are better prepared to work with AI systems.

## PROBLEM

Modern systems often hide too much. Users see outputs without understanding state, structure, provenance, validation, or transformation. AI can make that risk worse if students lack a language for data and systems.

## WORKFLOW

Use DotTalk++ to open real data, navigate records, change order, observe filters, inspect fields, enumerate relations, project tuples, and ask HELP/ED/ARCH what concepts mean. Use LabTalk to sequence these observations into labs rather than leaving students to wander through commands.

## MODEL

The model is engine plus teaching layer plus historical context: DotTalk++ executes and exposes behavior; LabTalk guides experiments; the case catalog provides the story and source links. HELP explains commands, ED explains concepts, ARCH explains internal design, Metadata organizes, and SelfDoc preserves provenance.

## TAKEAWAY

DotTalk++ should be framed not as nostalgia but as a teaching-grade xBase-compatible relational runtime: a working system that can explain database behavior as it runs.

<!-- END SOURCE CONTENT -->

---
