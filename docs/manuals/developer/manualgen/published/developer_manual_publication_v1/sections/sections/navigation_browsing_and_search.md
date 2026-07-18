# Navigation, Browsing, and Search

<!-- HISTORICAL STATUS: DRAFT_PROSE_REWRITE / REVIEW_REQUIRED -->
Status: REVIEWED_FOR_PUBLICATION

Purpose:
Explain how a user moves through open-table data, searches for target records, and chooses an appropriate display surface without overclaiming index, browser, or backend ownership.

Promotion boundary:
- This section is refreshed manual-draft prose.
- Linked command pages remain evidence-backed drafts, not final authority by themselves.
- Runtime behavior still governs exact edge semantics.
- Review before promotion into the finished Developer Manual.

## Commands in this section

- [BROWSE](../../command_reference_v1/commands/browse.md)
- [BROWSER](../../command_reference_v1/commands/browser.md)
- [CONTINUE](../../command_reference_v1/commands/continue.md)
- [FIND](../../command_reference_v1/commands/find.md)
- [GO](../../command_reference_v1/commands/go.md)
- [GOTO](../../command_reference_v1/commands/goto.md)
- [LIST](../../command_reference_v1/commands/list.md)
- [LOCATE](../../command_reference_v1/commands/locate.md)
- [SCAN](../../command_reference_v1/commands/scan.md)
- [SEEK](../../command_reference_v1/commands/seek.md)
- [SKIP](../../command_reference_v1/commands/skip.md)
- [SMARTLIST](../../command_reference_v1/commands/smartlist.md)
- [TOP](../../command_reference_v1/commands/top.md)
- [BOTTOM](../../command_reference_v1/commands/bottom.md)

## Overview

This section assumes the reader already understands the basic session loop introduced earlier: a table is opened into a work area, one area is current, and many commands operate against that current context by default.

Within that live context, navigation changes the current record position, search finds records that match a key or condition, and browsing commands project the resulting state back to the user. Those ideas belong together because they answer the same practical question: once data is open, how do you move through it and inspect it safely?

## Record-position commands

GO and GOTO are the direct positioning commands. TOP and BOTTOM move to the beginning or end of the current traversal. SKIP moves relative to the current record position.

The important manual rule is that these commands describe movement, not mutation. They change where the reader or script is standing inside the current table context. They do not, by themselves, explain index storage, filters, memo behavior, or relation ownership.

Traversal context still matters. Active order, scope, filtering, or deleted-record visibility may affect what "first," "last," or "next" means in practice. Those exact rules should be proven by runtime evidence and kept aligned with the indexing and filtering sections.

## Search commands

SEEK, FIND, LOCATE, and CONTINUE all help the user reach a desired record, but they should not be collapsed into a single generic search concept.

SEEK and FIND belong to the key-oriented search family and may depend on the current order or other lookup context. LOCATE belongs to the predicate-oriented family and searches for records that satisfy a condition. CONTINUE resumes the current locate-style search path where supported.

That distinction matters in the manual because users need to know whether they are asking for key lookup behavior or condition-based traversal. Exact syntax and edge behavior remain the responsibility of runtime proof, command pages, and later metadata crosswalks.

## SCAN and repeated traversal

SCAN belongs in this section because it turns navigation into repeatable traversal. Instead of moving to one record, it walks a series of records according to the current command context.

The manual should keep the explanation conservative: SCAN is an iteration surface that can work with current traversal rules and, where supported, conditions or other scope controls. Expression details and predicate mechanics belong in the expressions/querying lane, not here.

## Display and browsing surfaces

LIST and SMARTLIST are record-display surfaces. They are valuable because they expose what the current traversal really looks like to the user. That makes them especially useful during manual review, help review, and runtime confirmation work.

BROWSE and BROWSER belong to the richer browsing/projection family. They may be interactive, browser-like, or relation-aware depending on the runtime surface in use, but they still remain projection tools rather than owners of the underlying database state.

The ownership rule should remain explicit:
- DbArea owns live table and record state.
- Order and index systems influence traversal where active.
- Expression and predicate systems define conditions where used.
- Browsing and listing commands display the resulting state.

## Projection versus ownership

Projection surfaces make runtime state visible, but they do not define that state.

A LIST result may reveal the current traversal order, but the order system owns that behavior. A browser may show the current row and connected context, but the browser is still interpreting state supplied by lower-level table, relation, tuple, memo, and order systems.

Keeping that boundary clear prevents user-facing prose from accidentally turning display commands into the authority for storage, search, or relational semantics.

## Workbench consumer rule

The same ownership rule now extends beyond classic console browsing.

CLI listings, TUI surfaces, ERSATZ browsers, wx workbench views, and Python preview lanes should all be treated as consumers of runtime truth. They may present record position, logical order, search results, or relation context in different ways, but they should not invent an independent cursor model or redefine what the engine believes is current.

That matters for manual prose because the visible browser is often the easiest thing to describe. The easier description is not the safer one. The safer rule is:

- the engine owns cursor and order truth
- search and relation systems contribute traversal truth
- projection surfaces display the resulting state

When a front end drifts from runtime state, the runtime wins and the projection layer must be repaired.

## Index and filter boundary

This section may acknowledge that navigation and key-style search can be affected by active order, index choice, or traversal rules. It should stop there.

Detailed behavior for SET ORDER, tags, CDX/CNX behavior, LMDB-backed order state, and other index-specific semantics belongs in the indexing section. Likewise, full filtering semantics belong in the filtering/query lane once those pages are promoted.

## Future metadata alignment

This section is a natural downstream consumer of the documentation metadata system.

Expected feeders:
- SYSCMD for canonical command identity and handler mapping.
- SYSARGS for argument shapes such as record target, skip count, search key, and locate condition.
- SYSMSG for not-found, invalid-target, no-table-open, and traversal-boundary messages.
- SYSHELP for curated navigation/search/browsing help text.
- SYSENTVAR for aliases or variants once they are reviewed and intentionally seeded.

## Example path for a later prose pass

Examples should be added only after runtime transcripts are sampled and command wording is verified. A safe later example path is:

1. Open and confirm table context from the earlier workspace section.
2. Use TOP, BOTTOM, GO, GOTO, or SKIP to demonstrate record movement.
3. Use SEEK or FIND for key-style lookup and LOCATE or CONTINUE for predicate-style lookup.
4. Use LIST or SMARTLIST to confirm visible traversal.
5. Introduce BROWSE or BROWSER only after the projection-versus-ownership boundary is clear.

## Review notes before promotion

- Confirm GO/GOTO, TOP/BOTTOM, and SKIP wording against runtime behavior.
- Confirm SEEK/FIND versus LOCATE/CONTINUE wording stays distinct.
- Keep LIST/SMARTLIST and BROWSE/BROWSER described as projection surfaces, not owners.
- Keep GUI/TUI/browser workbench layers described as consumers of runtime truth.
- Do not overclaim index semantics here.
- Keep compatibility references gated until they are explicitly reviewed.

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

