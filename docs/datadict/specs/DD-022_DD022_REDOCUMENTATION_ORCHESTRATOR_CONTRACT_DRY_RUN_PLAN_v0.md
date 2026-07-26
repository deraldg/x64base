# DD-022 Redocumentation Orchestrator Contract / Dry-Run Plan v0

Date: 2026-05-27  
Boundary: REPORT_ONLY / PLAN_ONLY / NO_REPO_MUTATION / NO_RUNTIME_LAUNCH / NO_CATALOG_PROMOTION

## Purpose

DD-022 defines the first orchestration contract for the DotTalk++ / x64base data-dictionary redocumentation system.

The goal is not a one-time pass. The goal is a repeatable cycle:

```text
scan
  -> extract
  -> reconcile
  -> stage
  -> validate
  -> review
  -> promote only when explicitly authorized
  -> regenerate documentation only when explicitly authorized
  -> savepoint / AUTOLOG
```

DD-022 turns the prior DD packages into a pipeline shape while preserving the same safety boundary.

## What DD-022 adds

DD-022 adds:

- an orchestrator step contract;
- a tool-chain contract mapping DD package skeletons to future repo tool locations;
- a run-manifest schema;
- a dry-run orchestrator Python 3.12 skeleton;
- artifact-flow and retention rules;
- gate and failure-mode policy;
- a repo-integration contract for where orchestrator outputs should live;
- a sample dry-run manifest.

## Current package inputs

DD-022 is built on the prior work:

| Prior package | Role in orchestrator |
|---|---|
| DD-006 | physical dictionary manifest schema |
| DD-007 | physical/source/schema extractor skeleton |
| DD-008 | source-contract and MetaFact extension |
| DD-009 / DD-010 | HELP/message/CMDHELPCHK scan and validation planning |
| DD-011 / DD-012 | rules, constraints, xexpr, and rule artifact planning |
| DD-013 / DD-014 | workspace/relation/tuple map and transcript proof plan |
| DD-015 | transcript parser skeleton |
| DD-016 / DD-017 | physical DBF/CDX/MEMO proof plan and static DBF parser |
| DD-018 | evidence reconciliation/projection skeleton |
| DD-019 | catalog-staging import plan |
| DD-020 | staging artifact validator skeleton |
| DD-021 | repo placement and redocumentation-cycle plan |

Observed available rows from prior artifacts in this workspace:

```text
DD-018 projected objects: 17
DD-018 evidence stack rows: 17
DD-019 catalog table plan rows: 12
DD-019 import order rows: 10
DD-021 cycle steps: 15
```

## Orchestrator principle

The orchestrator should be conservative:

```text
Source scan can run report-only.
Extractor tools can run report-only.
Reconciliation can run report-only.
Staging package generation can create generated artifacts only.
Validation can run report-only.
Runtime proof capture is blocked unless explicitly run locally.
Catalog promotion is blocked unless explicitly authorized.
Documentation regeneration is blocked unless explicitly authorized.
HELP mutation is blocked unless explicitly authorized.
```

## Profiles

The orchestrator must preserve the profile boundary:

```text
ENGINE
  x64base engine/core evidence; no required student artifacts.

PROFESSIONAL
  DotTalk++ runtime/professional evidence; student/case/media surfaces hidden or optional.

EDUCATIONAL
  LabTalk, cases, student commands, teaching media, and storyboards as optional overlays.

DEV
  developer-only diagnostics, probes, scaffolding, and internal validation surfaces.
```

## Current status

DD-022 is a contract/skeleton package only.

It does not install the orchestrator into the repo. It does not run the full DD pipeline. It does not launch DotTalk++. It does not create or import x64base catalog DBFs. It does not regenerate HELP or manuals.
