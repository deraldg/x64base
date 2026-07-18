<!-- MDO-103B: promoted from reviewed candidate into manual draft workspace. -->
<!-- Decision: MDO-103A ACCEPT_FOR_PROMOTION; gate READY_FOR_HUMAN_PROMOTION_REVIEW. -->

# Workspaces, Areas, and Session State

<!-- HISTORICAL STATUS: PROMOTED_TO_MANUAL_DRAFT / REVIEW_REQUIRED -->
Status: REVIEWED_FOR_PUBLICATION

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

## Commands in this section

- [AREA](../../command_reference_v1/commands/area.md)
- [ERSATZ](../../command_reference_v1/commands/ersatz.md)
- [SCHEMAS](../../command_reference_v1/commands/schemas.md)
- [SELECT](../../command_reference_v1/commands/select.md)
- [USE](../../command_reference_v1/commands/use.md)
- [WORKSPACE](../../command_reference_v1/commands/workspace.md)

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

## Command roles

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
