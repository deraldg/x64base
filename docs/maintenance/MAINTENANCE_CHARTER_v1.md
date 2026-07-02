# DotTalk++ Maintenance Charter v1

Status: capture plan / doctrine artifact
Scope: maintenance, SelfDoc, Blackbox, comments, HELP, manualgen, datadict, messaging

## Purpose

DotTalk++ maintenance is a first-class SDLC subsystem. It is not merely a folder of scripts. It records how mutable documentation, metadata, help, catalogs, manuals, source comments, messaging, and runtime evidence are transformed into trustworthy information products.

Maintenance exists to make the system repeatable, teachable, auditable, and repairable.

## Doctrine

- Source defines.
- Runtime proves.
- Metadata organizes.
- HELP explains.
- Manuals teach.
- Maintenance governs.
- Blackbox models transformation.
- Messaging standardizes what the system says.

## Maintenance vs runtime scripts

Runtime scripts live under `dottalkpp/data/scripts` and are intended for DotTalk++ runtime execution through DO or DOTSCRIPT.

Maintenance scripts should live under `dottalkpp/scripts/maintenance` or lane-specific maintenance folders. These scripts are external SDLC tools: report generators, import planners, guarded apply packages, backup/rollback utilities, validators, and cookbook launchers.

Native maintenance support code belongs under `src/maintenance`. Current first-wave inspection/control surfaces such as MAINT and BBOX live in `src/cli`, not in loose PowerShell or Python tools.

## Required lane shape

Every maintenance lane should identify:

- Data in
- Blackbox process
- Information out
- Controls
- Backup requirement
- Rollback requirement
- Runtime smoke
- Boundary ledger
- Last green checkpoint
- Next allowed gate

## Safety policy

Maintenance may observe, report, stage, backup, validate, and smoke by default. Mutation requires an explicit gate. HELP, CMDHELPCHK, metadata catalogs, DBFs, CDX/LMDB, source code, build/project files, publications, and runtime state must each be named separately when mutation is authorized.

## Current path policy

Recommended operational station:

- `dottalkpp/scripts/maintenance`
- `dottalkpp/scripts/maintenance/lanes/<lane>`
- `docs/maintenance`
- `docs/maintenance/lanes/<lane>`
- `src/maintenance` for shared native C++ maintenance support code

## First captured lanes

- comments
- help
- cmdhelpchk
- datadict
- manualgen
- messaging
- blackbox
