---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260810-005
  recorded_at_utc: 2026-08-10T17:33:44Z
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
    id: CODEX-20260810-SCHEMA-CATALOG-001
    chat_reference: not_exposed
    run_id: AIPR-20260810-005
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: AIPR-20260810-004
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
      Correct schema presentation to use a dedicated public-facing localhost
      page and include the rest of the DotTalk++ and LabTalk schema ecology.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_DATABASE_SCHEMA_CATALOG_2026-08-10.md
    kind: session_closeout
---

# Session Closeout -- Dedicated database schema catalog (AIF-105)

Date: 2026-08-10.
Truth state: source-derived catalog; local development only.

## Outcome

Corrected the first website treatment so schema content is not a homepage
feature. `Schemas` remains a top-navigation destination, and `/schemas/` is now
the dedicated public-facing catalog for Cascade and the broader database
ecology.

## Catalog coverage

- Cascade: seven ERP modules, 34 tables, 9 analytical views, and the explicit
  SQLite-authority/x64base-mirror carrier contract.
- Education/reference: MCC x64, x32, VFP, and original; Bible x64; Pinocchio.
- Runtime/governance: HELP, runtime metadata, identity/RBAC, AI-BBS, AI Portal
  tracking, and data dictionary.
- Documentation/language: source comments, manual assembly, messaging, locale.
- Applications/fixtures: PyCRUD, memo/dialect fixtures, sandbox/probe stores.

The page distinguishes table-bearing schemas from LMDB, CDX, and CNX derived
indexes and excludes backups and browser residue from the public catalog.

## Website behavior

- Removed the schema feature from the homepage.
- Kept the homepage LMS label and explicit no-enrollment/no-grading boundary.
- Kept supporting Architecture below LMS and out of top navigation.
- Added one Mermaid source, generated SVG, and provenance record for the wider
  database ecology; retained the two Cascade diagrams.
- Updated the maintained website documentation matrix.

## Verification

- Diagram gate: 18 of 18 passed.
- Public-content guard: passed.
- Production build: 157 static pages generated, including `/schemas`.
- Local gateway and upstream: HTTP 200 for `/` and `/schemas/`.
- Rendered-content assertions: homepage has no schema feature and no `LMM`;
  LMS remains; schema page contains Other database schemas, MCC x64, HELP,
  Runtime metadata, Data dictionary, and the catalog SVG.
- Six unrelated AI Portal SVG/provenance files regenerated nondeterministically
  by Mermaid were restored exactly to `HEAD`.

## Publication state

The website source remains a local working-tree change on
`codex/lean-sites-publish`. The ccode governance updates remain on
`development`. Nothing was staged, committed, promoted, pushed, or published.
