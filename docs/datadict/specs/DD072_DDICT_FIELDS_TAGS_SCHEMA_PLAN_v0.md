# DD-072 DDICT FIELDS/TAGS Schema Inspection and Implementation Plan v0

Created UTC: `2026-05-28T13:46:16+00:00`

## Purpose

DD-072 inspects the actual active catalog schema needed for future read-only surfaces:

```text
DDICT FIELDS <table>
DDICT TAGS <table>
```

Target active catalog tables:

```text
DDOBJECT
DDATTR
DDEDGE
```

## Boundary

DD-072 is schema-inspection and planning only. It does not edit C++ source, registry/build files, active catalog DBFs, CDX/LMDB, HELP/META/CMDHELPCHK, or manual/catalog rows.
