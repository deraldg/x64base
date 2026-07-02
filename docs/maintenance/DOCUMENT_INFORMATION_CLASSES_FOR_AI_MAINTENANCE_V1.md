# Document Information Classes For AI Maintenance v1

Status: active maintenance note.

## Purpose

DotTalk++ uses documentation as part of the system, not as an afterthought. This
note groups the document types that are most useful for AI-assisted maintenance
and for turning raw project facts into valid information.

The goal is current, accurate, contextual, usable information.

## Highest-Value Document Classes

| Class | Purpose | Why it matters |
| --- | --- | --- |
| Contracts | Durable rules that constrain future work | Prevents chat decisions and design rules from disappearing |
| Usage contracts | Source-level user-IO/help obligations | Keeps commands discoverable and harvestable by HELP/SelfDoc |
| Architecture notes | Ownership, layering, source-of-truth boundaries | Prevents accidental forks of behavior |
| Workflow notes | Repeatable staged/parallel implementation procedures | Lets work continue across sessions without relying on memory |
| Smoke/proof records | Commands, transcripts, observed runtime evidence | Separates intended behavior from proven behavior |
| Status/closeout notes | Current truth, gaps, next gates, accepted risk | Keeps stale assumptions visible |
| Catalog documents | HELP, messaging, datadict, manualgen, GUI catalog shape | Makes data-backed subsystems understandable and rebuildable |

## Contract Priority

Contracts deserve special handling because they are easy to lose and expensive
to rediscover.

Important contract forms:

- source file headers,
- `@dottalk.usage v1` blocks,
- explicit docs under `docs/contracts`,
- GUI/runtime/database architecture contracts,
- workflow and safety contracts,
- runtime proof reports that close or constrain behavior.

Active contracts should eventually appear in the contract registry or be
discoverable by the contract scanner. Temporary ideas should stay in intake or
status notes until accepted.

## Source Comment Rule

Top-of-file source comments and `@dottalk.usage v1` blocks are evidence, not
decorative prose.

They should be:

- stable enough to harvest,
- current enough to trust,
- explicit about owner, command/surface, usage, status, and mutation behavior,
- preserved by the comments/SelfDoc pipeline.

## Messaging Rule

Localized wording should not create duplicate system identity.

Use stable message keys or message IDs where practical. Translate labels,
status text, and explanations through the messaging/locale lane. Do not fork
command identity, database identity, field identity, or GUI event identity for
language support.

Current GUI state:

- GUI message seed: `dottalkpp/data/messaging/gui_messages.csv`
- C++ generated adapter: `include/gui/core/generated_gui_messages.hpp`
- C++ resolver: `src/gui/core/localization.cpp`
- Python mirror: `tools/gui_preview`

The GUI message seed is aligned with the messaging lane but is not yet fully
merged into the broader DBF-backed runtime message catalog.

## Maintenance Command Surface

`MAINT DOCS` reports this grouping from inside DotTalk++.

`MAINT GUI` reports the current GUI sync lane and message-state boundary.
