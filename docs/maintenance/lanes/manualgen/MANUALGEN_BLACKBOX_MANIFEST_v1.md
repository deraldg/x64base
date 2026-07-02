# Manualgen Blackbox Manifest v1

Status: captured maintenance manifest
Lane: manualgen
Runtime inspector: MANUAL

## Purpose

The manualgen lane transforms manual sections, appendices, media anchors, manifests, and review queues into published manuals and MAN* catalog evidence.

## Data in

- section Markdown
- appendices
- media anchors
- publication manifests
- review queues
- regeneration cycle records

## Process

- assemble
- normalize
- validate
- publish
- catalog
- smoke runtime inspector

## Information out

- published developer manual
- MAN* catalog
- MANUAL runtime inspection
- regeneration cookbook
- publication reports

## Safety boundary

Manual publication replacement, appendix promotion, source edits, catalog imports, and HELP integration require separate gates.

## Current lesson

MANUAL command work showed that runtime command, CMDHELP visibility, and HELP /DOT visibility are separate proof layers.
