<!-- MDO-110: promoted from reviewed candidate into manual draft workspace v2. -->
<!-- Decision: MDO-109 ACCEPT_FOR_PROMOTION; gate READY_FOR_HUMAN_PROMOTION_REVIEW. -->

# Getting Started and Session Basics

<!-- HISTORICAL STATUS: PROMOTED_TO_MANUAL_DRAFT / REVIEW_REQUIRED -->
Status: REVIEWED_FOR_PUBLICATION

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
