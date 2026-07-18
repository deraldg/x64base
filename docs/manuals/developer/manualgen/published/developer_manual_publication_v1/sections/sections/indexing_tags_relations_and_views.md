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

## Open index architecture note

The indexing lane is intentionally open enough to teach and inspect.

That means the manual should preserve the distinction between:

- canonical runtime indexing surfaces such as CNX, CDX, active order, and rebuild paths
- physical backend boundaries such as LMDB for x64 storage
- educational or lab-facing index experiments such as INX, SCX, or SIX

The important manual rule is not to flatten those families into one generic word. They overlap conceptually, but they do not all serve the same role.

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

## Ownership reminder

Index systems own:

- tag metadata
- active-order semantics
- rebuild and verification semantics
- attach/open behavior

Projection layers such as LIST, BROWSE, ERSATZ, GUI, and TUI may reveal ordered traversal, but they do not own index truth. They are evidence surfaces, not index authorities.

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


