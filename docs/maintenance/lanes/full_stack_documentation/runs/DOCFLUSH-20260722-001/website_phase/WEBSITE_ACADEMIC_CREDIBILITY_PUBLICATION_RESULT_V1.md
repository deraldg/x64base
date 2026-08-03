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

## Follow-up closure: AI Reports remain local-only

The separate AI Reports preview is classified **very early alpha / local-only**
by maintainer ruling on 2026-08-03. It is not part of the approved 10-path
academic publication and is not approved for public source or deployment.

A follow-up boundary audit found that these static files were already present
on the live `gh-pages` branch from an earlier publication history:

- `reports/index.html`;
- `reports/AI_PORTAL_REPORT.html`; and
- `reports/BBS_BOARDS_REPORT.html`.

They were removed from `gh-pages`, committed as `9c02dc9b`, and pushed. GitHub
Pages reported the withdrawal build `built` with no error. Cache-bypassed live
readback then returned 404 for `/reports/`, `/reports/index.html`,
`/reports/AI_PORTAL_REPORT.html`, and `/reports/AI_PORTAL_REPORT/`.

The local preview remains available at `http://localhost:3000/reports/` and the
AI Portal report remains available through both its canonical `.html` URL and
its compatibility route. All returned 200 in the final local readback. The
three report files were removed from tracked website source and pushed in
`a4c5b5228`, preventing a future clean build from restoring the public copies.
Their physical localhost copies and the `app/reports` compatibility routes are
retained under checkout-local Git exclude rules. A future public release
requires a new, explicit maintainer authorization.

### Leak recurrence guard

The checkout-local exclusion alone was insufficient: ignored files can still be
copied by Next.js into `out/reports`, so a clean-looking working tree could
republish them. Website source `6c9dc904d` closes that path at three levels:

1. the production build removes local-only report directories before packaging;
2. Sites packaging and GitHub Pages publication refuse to continue if a report
   directory remains; and
3. the public AI Portal page no longer links to `/reports/` or claims that the
   snapshots are published.

The exact source passed the diagram and public-content gates, TypeScript, a
138-page production build, and Sites packaging in a disposable clean clone.
Both `out/reports` and `dist/server/public/reports` were absent. GitHub Pages
commit `f00b6ab4` built with no error. Cache-bypassed live verification found all
four report URL forms at 404, found the local-only ruling on the public AI
Portal page, found no `/reports/` link or publication claim, and confirmed
release metadata source `6c9dc904da1151acd82767662ac82fb4677c9565`.
