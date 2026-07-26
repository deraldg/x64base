---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260718-010
  recorded_at_utc: 2026-07-18T03:28:32Z
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 1ce8f45d79d4a5d80ef7d006c784e54420bd4541
  authorization:
    requested_by: maintainer
    scope: apply the exact eight-row canonical manual package MANRUN-20260718T031714Z-1A3F1333
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_MANUAL_CONTROLLED_ACCEPTANCE_APPLY_2026-07-18.md
    kind: session_closeout
---

# Session Closeout — Manual controlled-acceptance apply

Date: 2026-07-18.  
Owning lifecycle: DotTalk++ Manualgen and x64base.com documentation ascent.  
Truth state: canonical manual acceptance applied and verified.  
Publication state: manual accepted locally; website unchanged.

## Outcome

The maintainer authorized the exact eight-row plan
`MANRUN-20260718T031714Z-1A3F1333`. Apply run
`MANRUN-20260718T032528Z-F8C6EB67` completed all eight rows with zero findings
and zero rollback findings.

Accepted surfaces:

- Runtime Evidence section: 33 additions, 0 deletions;
- Command Surface section: 22 additions, 0 deletions;
- new Partial HELP appendix;
- rebuilt appendix aggregate;
- primary reader: 102 publication additions, 0 deletions;
- regenerated primary-reader and canonical evidence records;
- append-only DOCFLUSH appendix acceptance record.

The reader pointer path was not changed.

## Current reader

- SHA-256:
  `7437C555BA108DF56A9DE30556239945873072653900C26D2D85A2EBF21D6C0E`;
- lines: 4,082;
- headings: 237;
- candidate-only banner occurrences: 0;
- Partial HELP occurrences: one each in the reader, appendix aggregate, and
  standalone appendix.

## Backup and rollback

The complete before set, staged-after set, package/authorization evidence,
execution manifest, and guarded rollback tool are retained under:

`docs/manuals/developer/manualgen/backups/docflush_controlled_acceptance_MANRUN-20260718T032528Z-F8C6EB67/`

Rollback requires Python 3.12 and the exact plan-run confirmation. It was not
needed or executed.

## Post-apply wording correction

The finalized appendix acceptance record initially retained a stale preview
instruction after its status became final. That sentence was removed without
changing manual content or authority. The original execution manifest remains
historical; `post_apply_current_manifest.json` records the correction hashes
and the complete current eight-row state. All eight current hashes validate.

## Verification

- pointer audit: 21 PASS, 1 intentional role-split REVIEW, 0 FAIL;
- reader hash/count evidence agrees with the accepted records;
- 8 current target hashes and sizes match the post-apply manifest;
- full-stack documentation tests: 14 passed;
- Manualgen tests: 35 passed;
- interpreter: Python 3.12.9;
- MAN* catalogs, HELP/META, source staging, website, commit, push, and
  deployment: unchanged.

## Next gate

Gate 4 is a report-only publication-readiness proof over the accepted manual:
links, TOC/headings, section markers, provenance labels, appendix inventory,
accessibility, and artifact completeness. Six material gates remain through
live x64base.com verification.
