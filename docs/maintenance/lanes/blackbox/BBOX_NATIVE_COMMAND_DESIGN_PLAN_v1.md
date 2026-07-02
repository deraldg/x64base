# BBOX Native Command Design Plan v1

BBOX is the educational Blackbox command surface for DotTalk++.

## Teaching model

DATA IN -> BLACKBOX PROCESS -> INFORMATION OUT

BBOX should teach that source comments, DBFs, scripts, metadata, manuals, and messages are data inputs; scanners/builders/importers/validators are processes; and HELP, CMDHELP, DDICT, MANUAL, reports, diagrams, and localized messages are information outputs.

## First-wave command surface

- BBOX
- BBOX USAGE
- BBOX MODEL
- BBOX LANES
- BBOX COMMENTS
- BBOX HELP
- BBOX MANUALGEN
- BBOX DATADICT
- BBOX MESSAGING

## First-wave safety

BBOX is read-only. It explains and reports. It does not run maintenance scripts, mutate HELP, write DBFs, build indexes, or change source.

## Source plan

Future command file: `src\cli\cmd_bbox.cpp`.
Future support code may live under `src\maintenance` if shared with MAINT.
