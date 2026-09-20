---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260810-003
  recorded_at_utc: 2026-08-10T16:43:48Z
  agent:
    provider: OpenAI
    product: Codex
    model: GPT-5.6-sol
    member: member.ai.codex.local
    access_mode: local_write
  attribution:
    authored_by: member.ai.codex.local
    planned_by: member.derald
    owner: member.derald
    committer: member.derald
  session:
    id: CODEX-20260810-DATABASE-ECOLOGY-001
    chat_reference: not_exposed
    run_id: AIPR-20260810-003
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: AIPR-20260810-002
  project:
    id: project.labtalk.historical_database_migration
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: ff5f50058bd4ee5b8c431c47f702836a174f43bf
    head_commit: ff5f50058bd4ee5b8c431c47f702836a174f43bf
  authorization:
    requested_by: maintainer
    scope: >
      Scan D:/code/docs and D:/code/ccode for every database in the
      DotTalk++ / LabTalk ecology, make the result curatable and documented,
      and find orphans without mutating database files.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_DATABASE_ECOLOGY_INVENTORY_2026-08-10.md
    kind: session_closeout
---

# Session Closeout -- Database ecology inventory and orphan audit (AIF-105)

Date: 2026-08-10.
Owning lifecycle: LabTalk PDLC.
SDLC lane: inventory, curation, and maintenance.
Truth state: source-observed and read-only runtime-inspected.
Proof state: filesystem census, signatures, SQLite catalog reads, hashes, Git
visibility, companion checks, source references, YAML parse, and portal tests.

## One-line summary

Established a curatable registry and documented inventory for the full local
database ecology, separated 1,281 primary-store files into logical families,
and opened an evidence-backed orphan review queue without deleting data.

## Changed

- Added `labtalk/registries/database_ecology.yaml` as the machine-curatable
  inventory and orphan queue.
- Added `docs/maintenance/DOTTALKPP_LABTALK_DATABASE_ECOLOGY_INVENTORY_V1.md`
  as the human-readable interpretation and curation plan.
- Added Database Ecology to the LabTalk portal and registry list.
- Updated AIF-105 dashboard/intake state and the next-agent handoff.

## Measured result

`D:\code\docs` contains eight files and no database artifacts. The scan of
`D:\code\ccode` found 853 DBFs, 388 LMDB environments, and 40 SQLite files by
signature. Thirty-five SQLite files belong to the temporary Edge manual-render
profile; five are ecology files, including a byte-identical Bible package
replica. The primary-store total is 1,281 physical files, not 1,281 independent
logical databases.

The companion census found 388 LMDB locks, 273 CDX, 33 CNX, 146 DBT, and 10 FPT
files. There were zero orphan memo companions, zero generated sidecars without
their DBF, and zero incomplete LMDB data/lock pairs.

Git visibility is the main curation boundary: 62 of 853 DBFs are tracked; all
40 SQLite files and all 388 LMDB environments are untracked. Untracked does not
mean orphan, but it does block clean-checkout durability unless tracked inputs
and rebuild proof exist.

## Orphan findings

High-confidence review candidates are the duplicate 215-file Cascade output at
the DBF root, misplaced DataDict `MANANCHOR` LMDB environment, completed
`M372E_ART` probe index/environment without its DBF, two AutoDBF LMDB cleanup
residues, five named `zz_*` probe indexes without backing DBFs, and generic
`table`/`TINY` parser or probe containers without named table authority.

The Edge profile, conversion probe, CNX smoke decoy, Bible package replica, and
`STUDENTS.dbf.bad` quarantine evidence were classified separately and were not
misreported as unexplained orphans.

## Verification

- Signature sweep: 55,362 files readable; 40 SQLite headers found.
- SQLite read-only catalog inspection succeeded for all ecology SQLite files.
- Bible runtime/package copies have the same SHA-256.
- Cascade duplicate check: all 43 DBFs and static sidecars match; load receipts
  differ only by completion timestamp.
- YAML parse passed for the database registry and portal registry.
- LabTalk portal tests: 10 of 10 passed.
- Portal audit: 16 sections, 274 items, zero duplicate IDs, zero AI-report
  findings, and zero missing Database Ecology paths.
- ASCII and whitespace checks passed for the new files; `git diff --check`
  reported only pre-existing line-ending notices on unrelated paths.

## Published

Not staged, committed, promoted, pushed, or published. No DBF, SQLite, LMDB,
memo, index, schema, proof, backup, or temporary database file was mutated.

## Still open

1. Review each registry family and accept its authority class.
2. Prove clean-checkout rebuilds for canonical ignored databases.
3. Resolve the duplicate Cascade output root before admission.
4. Independently verify each orphan candidate before any deletion.
5. Replace hand-measured census counts with a tested read-only inventory tool
   before calling the registry self-refreshing.

## Provenance

- `labtalk/registries/database_ecology.yaml`
- `docs/maintenance/DOTTALKPP_LABTALK_DATABASE_ECOLOGY_INVENTORY_V1.md`
- `labtalk/registries/portal.yaml`
- `docs/maintenance/CASCADE_ERP_GATE0_HOUSEKEEPING_V1.md`
