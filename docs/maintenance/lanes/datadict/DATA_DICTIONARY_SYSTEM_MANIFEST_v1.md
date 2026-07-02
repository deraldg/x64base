# Data Dictionary System Manifest v1

Status: captured maintenance manifest
Lane: datadict
Runtime inspector: DDICT

## Purpose

The Data Dictionary lane records and exposes DotTalk++ / x64base catalog knowledge through a guarded catalog bridge and read-only runtime inspection surface.

## Runtime roots

Current active layout should distinguish data dictionary DBFs, indexes, LMDB mirrors, candidates, reports, and source tooling. Active runtime roots are not candidate roots.

## Runtime command surface

DDICT is the read-only runtime inspector. Known surfaces include:

- DDICT HELP
- DDICT STATUS
- DDICT TABLES
- DDICT OBJECTS
- DDICT FIELDS <table>
- DDICT TAGS <table>
- DDICT REL <object> [IN|OUT|BOTH]
- DDICT EVIDENCE <object>

## Catalog naming policy

Long x64 table names are real physical names where used. Compact DD* names may remain metadata owners. Use a bridge. Do not hardcode one spelling family. Reports should show both the physical artifact and metadata owner where applicable.

## Bridge rule

A resolver/bridge should be responsible for mapping compact names, aliases, metadata owners, and physical artifact names.

## Safety boundary

DDICT runtime inspection is read-only. Candidate staging, active replacement, CDX/LMDB rebuilds, and schema promotion require explicit guarded lanes.

## Closure evidence

A Data Dictionary maintenance lane is not closed until it records:

- preconditions
- candidate/input manifest
- DBF readback proof
- CDX/LMDB status where applicable
- DDICT runtime smoke
- boundary ledger
- backup/rollback if mutation occurred
- next gate

## Reusable lesson

This lane is a model for MAN*, SRC*, MSG*, and other catalog families. MAINT and BBOX are read-only runtime inspection surfaces that should consume this same discipline of compact owners, physical artifacts, resolver bridges, and evidence.
