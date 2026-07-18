# Relations and Tuple Views

<!-- HISTORICAL STATUS: DRAFT_PROSE_REWRITE / REVIEW_REQUIRED -->
Status: REVIEWED_FOR_PUBLICATION

Purpose:
Explain how relation definitions, tuple-oriented projection, and relation-aware browser surfaces fit together without collapsing them into one ownership model.

Promotion boundary:
- This section is refreshed manual-draft prose.
- Linked command pages remain evidence-backed drafts, not final authority by themselves.
- Runtime behavior still governs exact edge semantics.
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

## Overview

Relations and tuple views belong together because they answer one practical question: once more than one table matters, how does DotTalk++ express connected data without pretending that the browser, tuple row, or display surface owns the underlying relation truth?

This section should stay conservative. Relation definitions, tuple projections, and relation-aware browsers clearly interact, but they are not interchangeable layers.

## Relation ownership

The relation subsystem owns relation definitions and the intent of parent/child traversal between open areas.

That means a relation command may establish or refresh connected traversal state, but the visible tuple or browser output is still downstream from that relation state. A relation result may prove that a path is usable. It does not, by itself, become the authority for how relations are defined internally.

Safe ownership rule:

- relation commands own relation definition and relation-state control
- area/table systems own open-table context
- tuple systems own projected row composition across related contexts
- browser surfaces render projected results for inspection

## Tuple projection

Tuple-oriented commands belong here because they project relation-aware state into a visible row or record bundle.

The manual should describe tuples as projection structures: they gather values from current and related contexts into a browsable or exportable view. That is useful for teaching, reporting, and inspection, but it is still projection, not storage ownership and not relation-definition ownership.

This distinction prevents the manual from accidentally saying that a tuple command "creates the relation model" when it is really consuming relation state that was already established elsewhere.

## Relation-aware browsing

ERSATZ, relation result browsers, and tuple-aware views are evidence surfaces for connected data.

They matter because they are often the clearest visible proof that a relation path works. They also tempt documentation drift. Once a browser looks convincing, it becomes easy to describe the browser as if it owns the relation logic.

The safer wording is:

- relation-aware browsers show connected data
- tuple surfaces show projected connected rows
- relation systems determine how those connections are traversed
- workspace/session systems may restore relation context, but restoration is still separate from projection

## Workbench rule

This section also inherits the broader workbench rule now used across the manual.

CLI tuple displays, ERSATZ result browsers, TUI displays, wx workbench panes, and Python preview consumers should all mirror runtime relation truth rather than invent their own graph or cursor semantics.

If a browser and the runtime disagree about the current relation path, the runtime is the authority and the projection layer must be repaired.

## Runtime-proof boundary

This is a proof-sensitive section.

Useful runtime evidence already exists for:

- MCC/x32 relation paths
- ERSATZ relation browsing
- tuple-oriented connected-row inspection

But the manual should still preserve path sensitivity. A proven x32 relation/browser path does not automatically prove every x64 workspace restore path or every browser mode. The section should say what has been observed without overstating what is universal.

## View and export boundary

Commands such as TUPEXPORT, TUPLE, TUPTALK, or related surfaces may sound like they define a "view system." The safer interpretation is that they sit on the projection side of the relation family.

That means:

- export is downstream of projection
- projection is downstream of relation state
- relation state is downstream of open areas/workspaces

Keeping those layers separate makes later metadata alignment much easier.

## Future metadata alignment

This section is a natural downstream consumer of the documentation metadata system.

Expected feeders:

- SYSCMD for canonical command identity and handler mapping
- SYSSUBCMD for relation-family variants and scoped subcommands
- SYSARGS for relation names, tuple fields, export arguments, and projection options
- SYSMSG for relation warnings, missing-area diagnostics, and projection/export diagnostics
- SYSHELP for curated relation/tuple/browser concept help

## Review notes before promotion

- Keep relation definition separate from tuple projection.
- Keep tuple projection separate from browser rendering.
- Keep workspace/session restore behavior separate from relation ownership.
- Preserve path-sensitive runtime proof language.
- Do not let browser output become the authority for relation semantics.

## Boundary

- refreshed manual-draft prose only
- review still required before promotion
- no generated command page deletion
- no HELP mutation
- no META mutation
- no CMDHELPCHK mutation
- no catalog apply
- no source edits outside this manual section
- no production SelfDoc metadata promotion
