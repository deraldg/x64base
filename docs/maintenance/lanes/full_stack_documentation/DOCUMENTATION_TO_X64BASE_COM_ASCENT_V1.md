# Documentation-to-x64base.com ascent v1

Run: `DOCFLUSH-20260716-001`  
Recorded: 2026-07-18 UTC  
Current position: gates 1-9 passed; source commit `43f120a4`, Pages commit
`0ef77ea9`, Pages build `1102357325`, and cache-bypassed live verification all
PASS; the documentation-to-x64base.com ascent is complete.
Final surface: `https://x64base.com/` through the maintained
`D:\dev\x64base-site` repository and GitHub Pages

## Estimate

The vertical contains nine material gates from the current candidate to
verified website publication. All nine gates are complete; zero gates remain.
A gate may take more than one execution step, but it must leave one durable
disposition before the next gate begins.

| Gate | Product | Mutation boundary | Current state |
| ---: | --- | --- | --- |
| 1 | Selective-merge contextual review | Review/report only | PASS |
| 2 | Canonical acceptance preflight | Candidate and exact mutation plan only | PASS — 21 PASS / 1 intentional REVIEW / 0 FAIL |
| 3 | Controlled manual acceptance and rebuild | Accepted manual sections, appendix, reader, and manifests; separately authorized | PASS — 8/8 APPLIED, 0 FINDINGS |
| 4 | Manual publication-readiness proof | Report-only validation of links, TOC, headers, provenance, accessibility, and artifact completeness | PASS — 26 PASS / 0 REVIEW / 0 FAIL after 183/183 authorized apply |
| 5 | Clean x64base source-staging promotion | Reviewed files only into `C:\x64base`, with staged validation and supporting source/docs commit | PASS — 316 reviewed paths committed and pushed as `be935053`; closeout at `1b0625d0`; 18 preserved non-overlay paths remain local and unstaged |
| 6 | Website feed/export packet | Reviewed manual summaries, proof labels, source anchors, and route targets | PASS — 11 route dispositions, exact public-blob provenance, zero findings, zero website mutation |
| 7 | Website integration and local build | `D:\dev\x64base-site` source plus generated public artifact | PASS — 11 paths exact, 117 static pages, post-apply findings 0 |
| 8 | Website publication | Website commit/push and GitHub Pages deployment | PASS — source `43f120a4`, Pages `0ef77ea9`, build 1102357325 built |
| 9 | Live verification and documentation closeout | Cache-bypassed HTTP checks, route/content proof, dashboard and session closeout | PASS — all routes/artifacts 200 and exact; zero findings |

## Gate rules

1. Candidate generation does not accept canonical manual content.
2. Manual acceptance, source-staging promotion, and website publication are
   distinct mutations and require distinct proof.
3. The website consumes reviewed source/manual evidence; website prose does not
   flow backward as technical authority.
4. The maintained public-site repository is `D:\dev\x64base-site`. The older
   IIS copy is not the publication route.
5. GitHub Pages is the canonical x64base.com publication path.
6. A green build is not live-site proof. Final verification reads the deployed
   routes and records the content actually served.

## Current gate inputs

- reviewed selective merge: `MANRUN-20260718T020658Z-BFE7F605`;
- EOF-preserving packaging reconciliation: `MANRUN-20260718T031554Z-F1F59445`;
- passing controlled-acceptance plan: `MANRUN-20260718T031714Z-1A3F1333`;
- authorized apply: `MANRUN-20260718T032528Z-F8C6EB67`;
- passing command-reference candidate: `MANRUN-20260718T034751Z-B7DC1EEB`
  (164/164 pages, 3,119 lineage rows, zero findings);
- passing human review book: `MANRUN-20260718T042100Z-83C94101`
  (164 index links and 164 combined command headings);
- authorized newline reconciliation: 4/4 restored, backup
  `docflush_newline_reconciliation_20260718T042726Z/`;
- accepted appendix newline correction: 1/1 restored, backup
  `docflush_newline_reconciliation_20260718T043529Z/`;
- self-indexing command candidate: `MANRUN-20260718T042750Z-E194D003`;
- marker/status candidate: `MANRUN-20260718T043103Z-631C41CA`;
- Gate 4 exact plan/apply: `MANRUN-20260718T045052Z-0D8F14D6` /
  `MANRUN-20260718T050602Z-2254AACA`;
- accepted reader: `EA2E12A9...A5A8F`, 4,118 lines, 237 headings,
  164 resolved links, and 24/24 section markers;
- Gate 5 supplemental source-gap candidate:
  `MANRUN-20260718T131449Z-A1CA452C` (19/19 pages, 855 lineage rows,
  zero findings/attention labels);
- Gate 5 status review: four logical decisions across seven occurrences;
- Gate 5 disposition approval:
  `GATE5_SOURCE_PACKAGE_DISPOSITION_APPROVAL_2026-07-18.json` (19 pages and
  Navigation accepted for planning; three appendix topics held; 20 manifest
  entries accepted for planning);
- Gate 5 exact development plan: `MANRUN-20260718T132924Z-F08CF081` (25 rows,
  19 create / 6 replace, 183/183 staged index links, zero findings); plan
  manifest `0E4D0859...657A2`, mutation ledger `93B00396...A5447`;
- Gate 5 development apply: `MANRUN-20260718T134313Z-03C8C09F` (25/25,
  zero findings, six before files and 25 finalized outputs retained, guarded
  rollback unused); execution manifest `BC772AA4...DE9BC`;
- post-apply development proof: 183 pages / 183 index links, readiness 26/0/0,
  pointer audit 21/1/0, reader unchanged at `EA2E12A9...A5A8F`;
- staging preservation:
  `docflush_gate5_staging_preservation_20260718T135649Z/` (20/20 files,
  131,935 bytes, zero drift), manifest `D300FB1B...D6D5D7`;
- ordinary full overlay report after recovery-tool correction: 560 files /
  45.96 MB, held because it combines
  adjacent lanes;
- corrected selective Gate 5 overlay: 316 files, 315 create / one replace,
  zero unrelated dirty-path intersections/leaks/findings; the current
  executable hashes are owned by the non-overlaid recovery closeout and
  `C:\code\ccode\recovery\CURRENT_ESCROW.txt` to avoid a self-hashing control
  document;
- public-baseline escrow:
  `docflush_gate5_public_baseline_escrow_20260718T143453Z/`, manifest
  `CE73EFC6...F2612F`; 1,951 files / 92,540,334 bytes, 36 absent from
  development, complete-history bundle `151FF076...31CC3`, tar
  `109B1D23...754A1`, exact 35-file package mirror at `C:\code\ccode`;
- `C:\x64base` preflight: `main` at `fa7c04dc`, 20 dirty paths, seven
  divergent from authoritative development; no staging write performed;
- recovery-bound Gate 5 execution: `STAGEEXEC-20260718T145818Z`; committed
  baseline, 20 ordinary dirty files, one ignored DBF, 36 public-only files, and
  316-file overlay independently verified;
- public-projection regression amendment: development Manualgen 54/54 and
  full-stack 19/19; staging Manualgen 53 pass plus one named evidence skip and
  full-stack 17 pass plus two named evidence skips;
- Git publication: exactly 316 ledger paths, 33,015 insertions / one deletion,
  commit `be9350531251bb682f0476d652d99ca137861577`, pushed and read back from
  `refs/heads/main`; closeout commit `1b0625d0` losslessly reconciled the
  previously preserved AI dashboard, leaving 18 non-overlay paths unstaged;
- Gate 6 website feed: `WEBSITEFEED-20260718T155242Z`, 11 proposed targets
  (two create, eight update, one replace), public manual 4,118 lines / 237
  headings / 24 sections / four appendices / 183 command pages, website manual
  3,828 lines / 212 headings and not exact; website baseline `a69e0ec0` clean
  before and after; independent validation zero findings;
- Gate 7 exact integration plan: `GATE7PLAN-20260718T160428Z`, two creates /
  eight updates / one replacement, nine existing before-hashes exact, two
  create targets absent, branch/head/status exact, 30/30 full-stack tests, and
  independent preflight zero findings; plan `92CD4DF3...A564C`, machine spec
  `829445E1...BBEAA`; all mutation/build/commit/push/deployment authority remains
  false;
- Gate 7 apply: `GATE7APPLY-20260718T162939Z`, exactly 11 changed paths
  (two create / eight update / one replace), 691 insertions / 210 deletions
  including the two new files; public-content guard, TypeScript, 117-page
  production build, `git diff --check`, 32/32 full-stack tests, and post-apply
  validator all PASS; the built manual download is the exact public Git blob
  `09B593E9...B13B`; package, lockfile, hosting configuration, commit, push,
  deployment, and live verification remain unchanged/zero;
- Gate 8 publication: `GATE8PUBLISH-20260718T170022Z`; committed exactly the
  11 Gate 7 paths as `43f120a42d0ccd08d877c6468a705e3ba6d01619`, pushed and
  read back `codex/lean-sites-publish`, rebuilt 117 static pages, and published
  `gh-pages` commit `0ef77ea953313fde639d2ba71c7de99f4a79b84a`; GitHub
  Pages build `1102357325` reports `built` with HTTPS enforced;
- Gate 9 live verification: `GATE9LIVE-20260718T170310Z`; cache-bypassed
  Downloads, Command Reference, and announcement routes all HTTP 200 with
  expected provenance/count tokens and zero local-drive findings; manifest and
  release metadata HTTP 200; live manual exact at `09B593E9...B13B`, 4,118
  lines, and 237 headings;
- approved prose: `MANRUN-20260718T020630Z-9367A5BA`;
- two additive section copies, one candidate appendix, one contextual reader;
- three diffs, 161 aggregate additions across their separate review surfaces,
  zero deletions, and zero canonical hash changes;
- publication authority claimed: `0`.

## Expected review points

- `REGRESSION` and `TEST` remain proof launchers, not proof by exit code alone;
- `GENERIC` remains canary-level;
- `ARCTICTALK` and `FOXPRO` remain build-conditioned UI entries;
- partial HELP for `CANARY`, `DO`, and `RUN` remains visibly partial rather than
  silently promoted to full reference authority.

## Next action

Close `DOCFLUSH-20260716-001` as a passing nine-gate vertical. Continue the
separate `METACOLLECT-238-20260717-001` mission only as its own authorized
documentation/metadata task; it was not mutated by this ascent.
