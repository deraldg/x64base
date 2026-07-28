---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260728-004
  recorded_at_utc: 2026-07-28T21:59:50Z
  agent:
    provider: Anthropic
    product: Cowork (Claude)
    model: claude-opus-4-8
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 07e22d1e9fb2a78e88cca09122824c34961f615a
  authorization:
    requested_by: maintainer
    scope: >
      Add a governed --public build mode to tools/reports/build_reports.py (AIF-060
      reports lane) so public report generation is driven by portal.yaml
      sensitivity, and publish the resulting public reports to x64base.com.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_REPORTS_PUBLIC_BUILD_MODE_2026-07-28.md
    kind: session_closeout
---

# Session Closeout — Reports Public Build Mode (AIF-060)

**Lane:** AIF-060 (reports) · **Author:** Claude Cowork (`member.ai.claude.cowork`,
`local_write`). **Date:** 2026-07-28.

## Why

The report generator emitted four full internal HTML reports to `docs/reports/`;
publishing to x64base.com required a manual redaction pass, which the reports'
own publication note (`REPORTS_PUBLICATION_NOTE_V1.md`) warned is forgettable and
recommended replacing with a `--public` build mode governed by the per-report
`sensitivity:` markings already recorded in `labtalk/registries/portal.yaml`
(`portal.reports`).

## What changed

`tools/reports/build_reports.py` gained `--public`:

- It reads `portal.yaml` sensitivity (a recursive walk mapping each report
  basename to its `sensitivity`), and **skips any report marked `private`** — so
  `BBS_ACCESS_REPORT.html` (the authentication-surface map) is never emitted in
  public mode.
- For the emitted reports it applies the documented omissions: the boards
  connection recipe (`AUTH <member> <token>`) is dropped, the internal absolute
  path `C:\x64base` is genericized, the INTERNAL/PRIVATE band becomes a public
  snapshot note, the footer drops the internal generator path, and the index
  lists only the published reports.
- The agent handoff worklog **is** kept in the public boards report (maintainer
  decision, 2026-07-28).

Default mode is unchanged: it still writes all four full internal reports to
`docs/reports/`.

## Proof

- `python tools/reports/build_reports.py --out <tmp>` — regression: all four
  reports written as before.
- `python tools/reports/build_reports.py --public --out <tmp>` — emits
  `index.html`, `AI_PORTAL_REPORT.html`, `BBS_BOARDS_REPORT.html`; prints
  `SKIPPED (private per portal.yaml): BBS_ACCESS_REPORT.html`. Verified across the
  output: zero occurrences of `C:\x64base`, the INTERNAL banner, the
  `AUTH member.derald` recipe, or a link to the access report; the worklog
  handoff (`RUN=...`) present.
- The public set was generated into `D:/dev/x64base-site/public/reports/` and is
  linked from the public AI Portal page.

## Boundaries

Read-only over the store (opens DBFs read-only, no lock). No engine/source code
changed. Local `docs/reports/` originals (including the private access map) remain
untouched — full maintainer visibility is preserved; only the public build omits
the private material.
