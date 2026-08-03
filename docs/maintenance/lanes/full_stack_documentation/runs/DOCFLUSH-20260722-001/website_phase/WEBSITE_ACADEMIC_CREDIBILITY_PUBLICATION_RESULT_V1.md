---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260803-002
  recorded_at_utc: 2026-08-03T16:06:30Z
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
    branch: development
    baseline_commit: dc71f2b97ac5dff77af7d16b21f895d5250f287d
  authorization:
    requested_by: maintainer
    scope: document and publish the approved website credibility and academic-entry slice
  report:
    path: docs/maintenance/lanes/full_stack_documentation/runs/DOCFLUSH-20260722-001/website_phase/WEBSITE_ACADEMIC_CREDIBILITY_PUBLICATION_RESULT_V1.md
    kind: publication_report
---

# Website academic credibility publication result v1 (AIF-048)

Recorded: 2026-08-03.
Result: **PASS - source committed and pushed; GitHub Pages built; live content verified**.

## Scope

The maintainer reviewed the local site for credibility with an academic audience
and approved a narrower, less promotional presentation. The published slice:

- labels the website itself alpha while keeping the x64base engine at active beta;
- describes the public documentation as AI-assisted and source-reviewed;
- removes editorial instructions from visitor-facing prose;
- adds an Academic Start Here path for educators and researchers;
- adds a guided, read-only records/fields/tables exemplar with an explicit proof boundary;
- makes both additions discoverable from LabTalk product and sidebar routes; and
- prevents long inline-code tokens from causing mobile horizontal overflow.

The 10 source paths are:

1. `app/layout.tsx`
2. `app/page.tsx`
3. `components/Prose.tsx`
4. `config/sidebars.ts`
5. `content/docs/labtalk/academic-start.mdx`
6. `content/docs/labtalk/cases-storyboard.mdx`
7. `content/docs/labtalk/lesson-records-fields-tables.mdx`
8. `content/docs/labtalk/overview.mdx`
9. `content/docs/labtalk/student-lessons.mdx`
10. `content/products/labtalk.mdx`

Unrelated dirty Portal, diagram, Python-integration, navigation, product, and
generated-work files in `D:/dev/x64base-site` were not staged or committed.
Two overlapping LabTalk files retained unrelated Python paragraphs as unstaged
working-tree changes.

## Source and build proof

- Website source baseline: `66a15f7ec104eeaad5c9653187e6c268b8f4ab47`.
- Source branch: `codex/lean-sites-publish`.
- Source commit: `561eef1e249b65aaf1994489e54de66b7cfeb4f8`.
- Source push: `origin/codex/lean-sites-publish`, successful.
- Exact committed-tree build used a disposable clean clone.
- Diagram check: PASS, 11 diagrams.
- Public-content guard: PASS.
- TypeScript: PASS.
- Next.js production build: PASS, 138 static pages.
- Sites distribution packaging: PASS.

The ordinary dirty-checkout build had previously failed on three unrelated,
unstaged AI Portal diagram sources. The clean committed-tree build proves those
changes were excluded rather than silently included to make the gate green.

## Publication and live proof

- GitHub Pages commit: `541740c3479090ed874c9718d5fa2c325d09cf81`.
- Pages build: `1130347334`, status `built`, error none.
- HTTPS: enforced.
- Release metadata reports source branch `codex/lean-sites-publish` and source
  commit `561eef1e249b65aaf1994489e54de66b7cfeb4f8`.
- Cache-bypassed HTTP readback returned 200 and found the expected content at:
  - `https://x64base.com/` - `WEBSITE ALPHA`;
  - `https://x64base.com/products/labtalk/` - `Academic Start Here`;
  - `https://x64base.com/docs/labtalk/academic-start/` - `Central Academic Question`;
  - `https://x64base.com/docs/labtalk/lesson-records-fields-tables/` - `Observation Worksheet`.

## Boundary

This publication closes only the approved 10-path academic-credibility slice.
It does not publish the other dirty website work, promote the larger
DOCFLUSH-20260722-001 manual/source candidate, alter `C:/x64base`, or prove
educational outcomes. The private Sites mirror was not requested and was not
attempted. Canonical public publication is GitHub Pages.
