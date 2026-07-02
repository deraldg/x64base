# MAINT Native Command Design Plan v1

MAINT is the native C++ maintenance/SDLC inspection surface for DotTalk++.

## Purpose

MAINT should expose the maintenance lane catalog, cookbook index, boundary doctrine, and current status reports from inside DotTalk++ without becoming a script runner in the first wave.

## First-wave command surface

- MAINT
- MAINT USAGE
- MAINT STATUS
- MAINT LANES
- MAINT COOKBOOK <lane>
- MAINT BOUNDARY

## First-wave safety

MAINT is read-only. It may read maintenance docs and status artifacts. It must not execute builds, run CMDHELP BUILD, mutate source, mutate HELP, write DBFs, rebuild CDX/LMDB, replace publications, or run external scripts.

## Source plan

Future command file: `src\cli\cmd_maint.cpp`.
Future support code may live under `src\maintenance`.
