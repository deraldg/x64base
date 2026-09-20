---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260810-004
  recorded_at_utc: 2026-08-10T16:58:05Z
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
    id: CODEX-20260810-DATABASE-ECOLOGY-REMEDIATION-001
    chat_reference: not_exposed
    run_id: AIPR-20260810-004
    chat_handle: ""
    handle_binding: NOT_RESOLVABLE
    continues_run: AIPR-20260810-003
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
      Apply safe remediation to the documented database orphans, using the
      existing D:/code/ccode.sidecar aging lane and preserving all evidence.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_DATABASE_ECOLOGY_REMEDIATION_2026-08-10.md
    kind: session_closeout
---

# Session Closeout -- Database ecology preventive remediation (AIF-105)

Date: 2026-08-10.
Truth state: runtime-observed tooling; sidecar movement remains review-needed.

## Outcome

Replaced the hand-measured database census with a tested read-only scanner,
installed a Cascade duplicate preflight, and produced a verified 239-file,
hash-bound aging candidate for `D:\code\ccode.sidecar`. No database artifact
was moved, deleted, or opened for write. Added a visible localhost schema room
to present the SQLite and x64base carriers without overstating parity.

## Remediation

- Added `tools/database_ecology/database_ecology.py` with `scan`,
  `check-registry`, `cascade-preflight`, `sidecar-plan`, and
  `verify-sidecar-plan` commands.
- Added three unit regressions covering carrier/integrity detection, exact and
  timestamp-only Cascade duplicate recognition, and safe sidecar planning.
- Updated the Cascade runner to fail before mutation when legacy root artifacts
  make output authority ambiguous.
- Generated
  `docs/maintenance/database_ecology/SIDECAR_INTAKE_CANDIDATE_DBECO-20260810-001.csv`.
  It records 239 candidate files, original relative paths, byte sizes, SHA-256,
  Git state, proposed holding destinations, and dispositions. All 239 are
  untracked and ordinary-intake eligible, but all remain
  `candidate_not_approved`.

## Safety finding caught by the gate

The first sidecar plan incorrectly contained 454 rows because Windows
case-insensitive globbing matched the canonical `cascade_erp` directory as
well as root `CASCADE_*` files. No move occurred. Glob expansion now accepts
files only; a regression proves the canonical directory is excluded. The
correct plan contains 215 Cascade files plus 24 other candidate files.

## Public localhost presentation

The authoritative website source at `D:\dev\x64base-site` now includes:

- a top-level `/schemas/` route and `Schemas` navigation entry;
- a dedicated schema catalog page rather than a homepage schema feature;
- Mermaid sources and provenance-checked SVGs for the seven-module Cascade
  relational map and the dual-carrier contract;
- all 34 table names and all 9 analytical view names in the public page;
- a separate "Other database schemas" section for MCC, HELP, runtime metadata,
  identity/RBAC, AI-BBS, AI Portal tracking, data dictionary, source comments,
  manual assembly, messaging, locale, PyCRUD, fixtures, and sandbox/probe
  families;
- `LMS` retained as requested, with explicit no-enrollment/no-grading language
  and module, skill, and plugin packaging paths; and
- Architecture removed from top navigation and demoted below the LMS boundary
  on the homepage.

The website remains a local development change on branch
`codex/lean-sites-publish`; it was not deployed or published.

## Verification

- Database ecology unit tests: 3 of 3 passed.
- Live registry drift gate: passed against `D:\code\ccode` and
  `D:\code\docs`.
- Sidecar plan verification: 239 of 239 source paths, sizes, and SHA-256 values
  passed; zero destinations already exist; zero files moved.
- Cascade preflight: intentionally blocked on 215 legacy root artifacts.
- PyYAML is used for governed registry reads; carrier scanning and Cascade
  preflight remain Python-standard-library only.
- Website diagram gate: passed for 18 diagrams.
- Website public-content guard: passed.
- Website production build: 157 static pages generated; `/schemas/` included.
- Local readback: `/` and `/schemas/` returned HTTP 200; the homepage contained
  no schema feature, LMS preceded supporting Architecture, and the dedicated
  catalog contained Cascade plus the other named schema families and all three
  schema SVGs.

## Contracts

Read and preserved the Database Safety Contract, Sidecar Retention and Aging
Contract, Contract Registry, and Contract Lifecycle. In particular, intake is
path-specific and hash-bound, original relative paths are preserved, tracked
files are excluded from ordinary housekeeping, and review is not deletion
authority.

## Publication state

Development working trees only. Not staged, committed, promoted, pushed, or
published. The sidecar candidate is a plan, not an executed intake batch. The
website view is live only at the local development server.
