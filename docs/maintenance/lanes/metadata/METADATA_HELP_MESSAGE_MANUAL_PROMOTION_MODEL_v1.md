# Metadata Help Message Manual Promotion Model v1

Status: active top-level family model
Scope: source-comment evidence, live metadata catalogs, HELP artifacts, message identity, manual attachment, diagram normalization, Mermaid/draw.io/manual consumers

## Purpose

This is the beginning-to-end map for the current DotTalk++ documentation and metadata family.

It answers the practical questions:

1. what systems exist now
2. what each system is supposed to own
3. how the attempted normalization work fits together
4. where the current implementation is solid
5. where the implementation is still staged, sparse, or deferred

This is the top-level continuity document for the lane.

## One-line model

The current architecture should be read in this order:

```text
runtime behavior and source structure
    -> source-comment evidence
    -> live metadata catalogs
    -> HELP artifact/render lanes
    -> diagram normalization and attachment staging
    -> manual/media/publication attachment
    -> Mermaid / draw.io / rendered manual outputs
```

Everything above should consume authority from below it.

Nothing above should casually replace the authority below it.

## Shared locale posture

The whole family should recognize language through one shared locale contract.

- canonical identities remain stable and English-first
- localized human text attaches through `LOCALE_ID`
- region/culture scope should be carried structurally through `REGION_ID`
- Messaging is the first proven runtime consumer, but not the only lane that
  must be locale-aware

Practical implication:

- source-comment evidence stays English/source-authority
- metadata must not remain language-blind
- HELP should keep canonical rows plus locale companion rows
- manuals/publication should use canonical rows plus localized companion rows

## The systems

## 1. Source-comment evidence family

Primary role:

- preserve structural facts extracted from source and comments
- keep provenance close to real source files
- carry command, block, line, and usage evidence

Current core tables:

- `SRCFILE`
- `SRCBLOCK`
- `SRCLINE`
- `SRCUSAGE`
- `SRCCLASS`
- `MEMO_LINES`

Current strong joins:

- `SRCFILE -> SRCBLOCK ON FILEID`
- `SRCFILE -> SRCLINE ON FILEID`
- `SRCFILE -> SRCUSAGE ON FILEID`
- `SRCFILE -> SRCCLASS ON FILEID`
- `SRCUSAGE -> SRCCLASS ON COMMAND`

What this family is good at:

- provenance
- source-contract evidence
- command-usage discovery
- data-flow and source-relationship diagrams

What it should not own:

- final HELP presentation
- final manual publication
- final message catalog selection

## 2. Live metadata catalog family

Primary role:

- classify system surfaces
- persist command/function/message/help ownership facts
- provide a normalized catalog layer broader than HELP

Current live tables:

- `SYSCMD`
- `SYSSUBCMD`
- `SYSENTVAR`
- `SYSFUNC`
- `SYSMSG`
- `SYSHELP`
- `SYSARGS`
- `SYSFLDDIC`

What this family is good at:

- canonical command identity
- subcommand and routed-surface modeling
- alias/variant ownership
- help ownership
- message identity staging
- reusable argument and field-dictionary facts

What is already solid:

- runtime DBF lane exists
- x64 relational workspace exists
- `CATALOGCANARY` consumer boundary exists
- metadata is clearly broader than HELP

What is still incomplete:

- seeding breadth is still uneven
- `SYSMSG` exists but is still sparse
- full live integration with the collector/proposal lane is not complete
- locale/region recognition must be made explicit in metadata row design so
  HELP/manual work does not backtrack later

## 3. HELP artifact family

Primary role:

- explain the command surface
- present summaries, syntax, examples, warnings, notes, and artifacts
- act as a rendered/documented consumer of lower-level evidence

Current core structures:

- `HELP_TOPIC`
- `HELP_SECTION`
- `HELP_LINE`
- `HELP_ARTIFACTS`
- command/help harvest outputs such as `HELP_HELP_ARTIFACTS.csv`

What this family is good at:

- reflected command status rows
- curated command documentation
- artifact ownership and rendered help context

What is already solid:

- harvested command-facing identities like `DOT|ABOUT`, `DOT|AREA`, `DOT|ASCEND`
- strong command/help artifact proof through `CMDKEY`
- locale companion tables already exist structurally

What the current normalization attempt got right:

- HELP is not the lowest authority
- HELP can provide trustworthy command-facing attachment keys
- HELP artifacts are a strong bridge into diagram enrichment

What it must not be mistaken for:

- runtime proof
- full metadata authority
- full message-catalog proof

## 4. Messaging / language family

Primary role:

- own typed user-facing message identity and text selection
- support language/locale-aware runtime output
- gradually replace hard-coded command strings with catalog-backed reporting

Current evidence lanes:

- `SYSMSG`
- `SYSTEM_MESSAGES` legacy/alternate references
- `SYSTEM_MESSAGE_TEXT`
- `src/help/message_catalog.cpp`
- `src/help/helpdata_messages.cpp`
- messaging scripts and candidate packs under `docs/messaging`

What is already solid:

- message schema is real
- message workspace/storage lane is real
- runtime messaging direction is explicit
- locale/language integration is already being wired
- shared locale spine already exists outside Messaging-only ownership

What is still thin:

- broad dense seeded `SYSMSG` population
- full proof that HELP status/error/warning names map to promoted live message rows

Important current boundary:

- `COMMAND_STATUS` is a good command/help crosswalk candidate
- it is not yet strong enough to be claimed as a fully proven current `SYSMSG` row

What the normalization attempt got right:

- message identity belongs below HELP/manual prose
- localization should happen through message selection, not by scattering `cout`
- metadata and messaging must meet, but should not be conflated

## 5. Manual / publication family

Primary role:

- attach approved artifacts to publication structure
- keep stable media IDs, anchors, section structure, and publication manifests

Current core structures:

- `MANMEDIA`
- `MANANCHOR`
- `MANSECTION`
- `MANPUB`
- `MANRUN`
- manifest files and accepted media/anchor manifests

What is already solid:

- real `MANMEDIA` / `MANANCHOR` schema
- current manifest media inventory
- accepted media IDs and anchor IDs
- prior doctrine already points manual refresh toward the shared locale contract

What this family is good at:

- stable publication attachment
- media anchoring
- cross-manual artifact management
- future multilingual publication without identity churn

What it should not absorb:

- source structural authority
- metadata command authority
- diagram structural truth

## 6. Diagram metadata family

Primary role:

- normalize the diagram view of facts owned elsewhere
- hold entities, relations, and emitted artifacts
- bridge source evidence, metadata, HELP, and manual attachment

Current staged family:

- `DIAGRUN`
- `DIAGENTITY`
- `DIAGREL`
- `DIAGART`

Current state:

- v1 staged CSVs exist
- v2 headers exist
- proof samples exist
- full structural restage candidates exist
- HELP, message, and manual boundaries are now documented

What this family is good at:

- explicit diagram row kinds
- explicit edge proof levels
- explicit artifact tracking
- feeding Mermaid and draw.io without making them the authority

What the normalization attempt got right:

- preserve structural rows first
- enrich only where real identity exists
- do not mutate selfdoc/design rows into command/message/media rows
- use separate enrichment packets for separate row kinds

## 7. Render consumers

Primary role:

- consume normalized diagram/catalog facts for human output

Current consumer set:

- Mermaid
- draw.io
- rendered manuals
- HELP artifact references

What this layer is good at:

- visualization
- publication
- teaching surfaces

What it must not become:

- the primary truth authority

## Authority model

The clean ownership model is:

- runtime proves behavior
- source-comment evidence preserves structural provenance
- live metadata catalogs normalize command/function/message/help ownership
- HELP renders and explains
- messaging selects runtime-facing text and locale/language variants
- diagram metadata normalizes architecture/relationship views
- manual/publication lanes attach approved artifacts
- Mermaid/draw.io/manual outputs render for humans

That is the intended stack.

## Comparison of normalization attempts

## Attempt 1. Metadata-first classification

This is the strongest architectural direction.

Why it is good:

- metadata is broader than HELP
- command/function/message/help identities fit naturally there
- diagram/render lanes can consume metadata instead of inventing a parallel naming system

Current implementation state:

- partially implemented and already real

## Attempt 2. HELP-first truth

This is useful, but weaker as architecture.

Why it helps:

- HELP harvest already exposes concrete command-facing identities
- `CMDKEY` is strong for command/help artifact joins

Why it is not enough:

- HELP is rendered/explanatory
- HELP does not by itself prove runtime or metadata truth
- HELP status names do not automatically prove current message catalog rows

Current implementation state:

- strong as a consumer/crosswalk lane
- not appropriate as the base authority

## Attempt 3. Message-catalog-first multilingual migration

This is the right long-term direction for runtime text.

Why it helps:

- allows language-aware selection at runtime
- reduces hard-coded console text
- supports coherent warnings/errors/status/help-hint routing

Why it is not complete yet:

- current `SYSMSG` seeding is sparse
- language/locale routing is active but still under development
- many command surfaces still emit hard-coded text

Current implementation state:

- directionally correct
- partially implemented

## Attempt 4. Manual-first diagram attachment

This is correct only at the top of the stack.

Why it helps:

- publication needs stable `MEDIA_ID` and `ANCHOR_ID`
- manuals need attachment, not structural duplication

Why it must stay constrained:

- manual pages, gates, ledgers, and CSVs are not the same thing as media assets
- manual prose should not become the structural authority

Current implementation state:

- strong on attachment identity
- not the place to own source/command/message truth

## Current solid joins

These joins are solid enough to be treated as current working doctrine:

- source evidence on `FILEID`
- source evidence on `COMMAND`
- HELP artifact crosswalk on `CMDKEY`
- command identity through `SYSCMD.CAN_NAME`
- manual attachment through `MANMEDIA.MEDIA_ID` and `MANANCHOR.ANCHOR_ID`
- `RELATIVE_P` as a bridge for artifacts

## Current weak or deferred joins

These should remain staged or candidate-only:

- HELP status-name -> live `SYSMSG` truth where no current seeded message row is proven
- structural selfdoc table rows -> command identity
- structural document/gate rows -> media identity
- full blanket promotion of empty v2 identity columns

## Operational rules

1. Preserve structural rows before enrichment.
2. Enrich only where a feeder already exposes a real identity.
3. Add new row kinds when the identity is different.
4. Keep candidate/proven boundaries explicit.
5. Let HELP, messaging, manuals, and diagrams consume authority instead of replacing it.

## What is ready now

- metadata-first doctrine is strong enough to continue
- diagram v2 candidate shape is stable
- command-facing enrichment pattern is proven
- message boundary is understood
- manual attachment boundary is understood

## What should happen next

1. Continue replacing hard-coded runtime text with message-aware seams in commands.
2. Densify `SYSMSG` and related message harvests before promoting more message identities into diagram metadata.
3. Expand command-facing diagram enrichment only where command/help identities are real.
4. Add true media rows when diagrams become real manual media assets.
5. Keep manuals multilingual at the publication/content layer, while runtime messaging evolves through the message catalog layer.

## Practical bottom line

The family does fit together.

The attempted normalization is mostly correct when read this way:

- source-comment preserves evidence
- metadata classifies system identity
- HELP explains command surfaces
- messaging owns runtime-facing multilingual text
- manuals attach approved artifacts
- diagrams normalize relationships across those families
- Mermaid/draw.io/manual outputs are final consumers

The main remaining problem is not architecture.

It is maturity:

- sparse seeds
- partial harvests
- mixed generations
- and several lanes that are already correct directionally but not yet fully populated

That is a manageable problem, and the lane is now documented tightly enough to continue without losing continuity.
