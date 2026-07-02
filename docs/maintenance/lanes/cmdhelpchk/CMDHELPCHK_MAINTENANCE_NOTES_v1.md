# CMDHELPCHK Maintenance Notes v1

Status: captured maintenance manifest
Lane: cmdhelpchk

## Purpose

CMDHELPCHK validates HELP/catalog/registry/source-contract alignment. It should become a checkpoint between source changes, HELP generation, comments evidence, and user-facing help surfaces.

## Expected future role

CMDHELPCHK should compare:

- runtime command registry
- command usage contracts
- comments/SRC* evidence
- current HELP DATA
- DOTREF/FOXREF curated catalogs
- legacy command tables where applicable
- runtime HELP and CMDHELP smoke evidence

## Safety boundary

CMDHELPCHK should default to validation/reporting. Any HELP, registry, source, or metadata mutation should be a separately authorized lane.

## Current lesson

A command can be visible in CMDHELP but not in HELP /DOT. CMDHELPCHK should eventually identify that mismatch explicitly.
