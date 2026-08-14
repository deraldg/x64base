# DotTalk++ Professional Manual Blueprint v1

Status: manual expansion blueprint  
Audience: human developer, AI development agent, documentation maintainer  
Source root: `D:\code\ccode`  
Created: 2026-06-28

DotTalk++ is large enough to deserve a professional manual measured in hundreds of pages, not a short quickstart. The manual should be built as a family of reader-facing books backed by anchors, prose roles, command catalogs, proof transcripts, and data dictionary rows.

## Manual Family

The final reader-facing documentation should be a family, not one overloaded file:

| Book | Target size | Purpose |
|---|---:|---|
| User Guide | 120-180 pages | Teach ordinary use: tables, records, indexes, scripts, import/export, HELP. |
| Command and Function Reference | 200-400 pages | Catalog every command, function, operator, argument, alias, status, caveat, and example. |
| Database Administration Guide | 100-180 pages | Locking, buffering, commit/rollback, work areas, index maintenance, integrity checks, backups. |
| Developer Handoff Manual | 120-220 pages | Source layout, trinity headers, command registry, HELP/META/SelfDoc/manualgen lanes, proof workflow. |
| Data Dictionary Manual | 100-250 pages | Schemas, DBF structures, fields, indexes, memo formats, evidence tables, generated catalog rows. |
| LabTalk Case Manual | 80-160 pages | Optional educational case studies and teaching paths. |

The current `DOTTALKPP_READER_MANUAL_V1.md` should become the front door, not the whole library.

The maturity rules for promoting material are in:

- `DOTTALKPP_MANUAL_MATURITY_MODEL_V1.md`

## Professional Manual Spine

The full User Guide should grow toward this structure:

1. What DotTalk++ Is
2. Installation, Build, and Runtime Profiles
3. Shell Model and Command Language
4. Tables, Records, Fields, and Types
5. Work Areas and Cursor Control
6. Creating Tables
7. Opening, Closing, and Selecting Tables
8. Navigation and Record Pointers
9. Editing Data
10. Record Locking and Table Locking
11. Table Buffering
12. Commit and Rollback
13. Deleted Records, Recall, and Pack Behavior
14. Indexes, Orders, Tags, CNX, CDX, INX, and LMDB
15. Filters, Locates, Scans, and Query Behavior
16. Import and Export
17. Memos and Large Text Storage
18. x64base Structures and Limits
19. Vectored Table and Field Names
20. DotScript Automation
21. HELP and Metadata
22. Data Dictionaries
23. Runtime Proof and Diagnostics
24. Troubleshooting
25. Appendices

## Database Administration Guide Spine

The DBA-style manual should cover:

1. Runtime Safety Model
2. Work Areas and Open Table State
3. Current Area, Current Record, and Cursor Restoration
4. Lock Ownership
5. Record Locks
6. Table Locks
7. Lock Status and Lock Inspection
8. Editing Under Locks
9. Table Buffer Modes
10. Dirty, Clean, Stale, and Fresh State
11. Buffered Field Changes
12. Commit Semantics
13. Partial Commit Handling
14. Rollback Semantics
15. Memo Flush Behavior
16. Index Update and Rebuild Policy
17. CNX versus CDX/LMDB Maintenance
18. Persistent Buffering Roadmap
19. Recovery Scenarios
20. Proof Scripts and Operational Checklists

## Command Reference Spine

Every command entry should follow this shape:

```text
Name
Aliases
Kind
Purpose
Syntax
Arguments
Preconditions
Effects
Mutation scope
Cursor behavior
Locking behavior
Buffering behavior
Index/order behavior
Memo behavior
Examples
Expected output/readback
Failure modes
Related commands
Anchor IDs
Proof transcripts
Reader status
```

The command reference must be generated from HELP/META/catalog data and then edited for prose quality.

## Advanced Database Topics To Promote Early

These sections should be promoted before the manual grows into hundreds of pages:

| Topic | Current evidence | Manual stance |
|---|---|---|
| `LOCK` / `UNLOCK` | `src/cli/cmd_lock.cpp`; `src/cli/cmd_unlock.cpp`; help message catalog | Supported command surface; needs fresh transcript examples. |
| `TABLE BUFFER` | `src/cli/table_buffer.cpp`; `src/cli/table_state.hpp`; message catalog | Supported table-buffer control; persistent journal is stubbed/future. |
| `COMMIT` | `src/cli/cmd_commit.cpp` | Supported buffered apply; locks records at commit time; partial commit possible. |
| `ROLLBACK` | `src/cli/cmd_rollback.cpp` | Supported discard of buffered changes; table data is not mutated by rollback. |
| Cursor control | `src/cli/cmd_recno.cpp`; workarea/browser/cursor code | Supported navigation/reporting; cursor restoration exists in selected workflows. |
| Work areas | `src/cli/workareas.hpp`; shell engine area model | Core runtime model; needs reader examples. |
| CDX/LMDB commit policy | `src/cli/cmd_commit.cpp`; order state | COMMIT does not rebuild CDX/LMDB; mutation hooks own lifecycle. |
| Vectored x64 names | `include/xbase_64.hpp`; `X64M` metadata | Current default is 128-byte table/field names by compile-time policy; longer builds require proof and regeneration. |

## Expansion Method

Use this process for each new chapter:

1. Select an anchor or create one.
2. Inspect source, HELP/META rows, and existing proof transcripts.
3. Classify current behavior as `proven`, `observed`, `candidate`, `drift`, or `deferred`.
4. Write orientation prose first.
5. Add tutorial prose only from successful transcripts.
6. Add reference entries from HELP/META.
7. Add caveats for failed or unproven edges.
8. Add proof tasks for missing runtime validation.

## Immediate Next Chapters

The next high-value manual chapters are:

1. Work Areas and Cursor Control
2. Record and Table Locking
3. Table Buffering
4. Commit and Rollback
5. Operational Safety Checklist
6. Vectored Names and Self-Describing x64 Files

These chapters should make the manual feel like documentation for a real database system, because the runtime already has the corresponding command surfaces and state machinery.

## Quality Gates

Each professional chapter must pass these gates before it is considered reader-ready:

| Gate | Requirement |
|---|---|
| Anchor gate | The section has one or more anchor IDs. |
| Source gate | Source, HELP, META, or data dictionary evidence is named. |
| Proof gate | Runtime behavior is proven by transcript, or the proof gap is explicit. |
| Prose gate | The section has a reader purpose, not only catalog facts. |
| Safety gate | Mutation, lock, buffer, cursor, memo, and index side effects are stated where relevant. |
| Recovery gate | Failure modes include recovery or next diagnostic step. |

The final manual can be hundreds of pages only if those pages are disciplined. Volume without gates will rot. Anchored, proof-backed prose can grow safely.
