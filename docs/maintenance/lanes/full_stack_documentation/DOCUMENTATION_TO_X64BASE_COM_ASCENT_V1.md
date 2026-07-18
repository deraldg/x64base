# Documentation-to-x64base.com ascent v1

Run: `DOCFLUSH-20260716-001`  
Recorded: 2026-07-18 UTC  
Current position: gates 1-5 passed; Gate 5 published to `origin/main` at
`be9350531251bb682f0476d652d99ca137861577`  
Final surface: `https://x64base.com/` through the maintained
`D:\dev\x64base-site` repository and GitHub Pages

## Estimate

The vertical contains nine material gates from the current candidate to
verified website publication. Gates 1 through 5 are complete; four gates remain.
A gate may take more than one execution step, but it must leave one durable
disposition before the next gate begins.

| Gate | Product | Mutation boundary | Current state |
| ---: | --- | --- | --- |
| 1 | Selective-merge contextual review | Review/report only | PASS |
| 2 | Canonical acceptance preflight | Candidate and exact mutation plan only | PASS — 21 PASS / 1 intentional REVIEW / 0 FAIL |
| 3 | Controlled manual acceptance and rebuild | Accepted manual sections, appendix, reader, and manifests; separately authorized | PASS — 8/8 APPLIED, 0 FINDINGS |
| 4 | Manual publication-readiness proof | Report-only validation of links, TOC, headers, provenance, accessibility, and artifact completeness | PASS — 26 PASS / 0 REVIEW / 0 FAIL after 183/183 authorized apply |
| 5 | Clean x64base source-staging promotion | Reviewed files only into `C:\x64base`, with staged validation and supporting source/docs commit | PASS — 316 reviewed paths committed and pushed as `be935053`; closeout at `1b0625d0`; 18 preserved non-overlay paths remain local and unstaged |
| 6 | Website feed/export packet | Reviewed manual summaries, proof labels, source anchors, and route targets | PENDING |
| 7 | Website integration and local build | `D:\dev\x64base-site` source plus generated public artifact | PENDING |
| 8 | Website publication | Website commit/push and GitHub Pages deployment | PENDING |
| 9 | Live verification and documentation closeout | Cache-bypassed HTTP checks, route/content proof, dashboard and session closeout | PENDING |

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

Begin Gate 6: build a report-only website feed/export packet from the public
commit. The packet must identify the manual summaries, proof labels, source
anchors, and proposed x64base.com routes without editing
`D:\dev\x64base-site`. Website integration, build, push, and deployment remain
separate Gates 7 and 8.
