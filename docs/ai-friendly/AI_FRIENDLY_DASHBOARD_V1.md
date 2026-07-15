# AI Friendly Dashboard v1

Status: seed dashboard.
Purpose: User-visible status surface for AI-assisted DotTalk++ / LabTalk work.

## Current Visibility Contract

The user should be able to see:

- what AI is working on,
- what evidence it read,
- what files or systems it touched,
- whether mutation was performed or only proposed,
- where each useful interaction was routed,
- what still needs review, proof, or promotion.

## Current Lane State

| Area | Status | Anchor |
| --- | --- | --- |
| Lane manifest | seeded | `docs/ai-friendly/AI_FRIENDLY_LANE_MANIFEST_V1.md` |
| Workflow | seeded | `docs/ai-friendly/AI_FRIENDLY_WORKFLOW_V1.md` |
| Intake queue | seeded | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` |
| Dashboard | seeded | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` |
| Assimilation portal | seeded | `docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md` |
| Assimilation book | seeded | `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md` |
| LabTalk portal integration | active seed | `labtalk/registries/portal.yaml` |
| AI Portal hardening lane | Alpha/Experimental — active | `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md` |
| Generated report integration | not started | future report under `docs/ai-friendly/reports` |
| Closeout-updates-startup gate (AIF-006) | **promoted 2026-07-14** | `AI_PORTAL.md` -> "Closeout Updates Startup" |
| Session closeout convention | **active** | `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` |
| Public AI Portal consistency audit | **published 2026-07-15; authoritative-development reconciliation pending** | `docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_PUBLIC_CONSISTENCY_2026-07-15.md` |
| MCC databuild lane (sample foundation) | **runtime-proven 2026-07-14** | `dottalkpp/data/scripts/mcc/README.md` |
| Cold-clone journey and released-entry-point hardening (AIF-016) | **published and certified 2026-07-15** | `docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md` |
| Developer profile publication boundary (AIF-012) | **historical review needed; public branch exposure confirmed 2026-07-14** | `labtalk/LABTALK_DEVELOPER_PROFILE_v0.md` |
| Recursive human/AI coproject model (AIF-013) | **design-intended 2026-07-14** | `labtalk/docs/co-development/recursive_coproject_model_v1.md` |
| xbase/xindex/pydottalk build architecture | **NONE, LEGACY, and LMDB core matrix proven; `USE` optional-provider decision active; index-mutation hardening pending 2026-07-14** | `docs/maintenance/XBASE_OPTIONAL_INDEX_ARCHITECTURE_DECISION_V1.md`; `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` |
| Engine/product-edition separation (AIF-015) | **implemented and proven in authoritative development; public source publication pending Path A** | `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md`; `docs/maintenance/EDITION_PUBLICATION_PLAN_A_V1.md` |

## Session Log

Newest first. Each row is a durable closeout; the chat is not the record.

| Date | Session | Lane state changed | Closeout |
| --- | --- | --- | --- |
| 2026-07-15 | AI Portal public consistency audit | Corrected public state drift through PRs #8 and #9, established one canonical startup path, closed an overbroad draft unmerged, and set authoritative-development reconciliation as the next gate. | `docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_PUBLIC_CONSISTENCY_2026-07-15.md` |
| 2026-07-15 | Cold-clone journey certification and publication | Proved clone -> build -> runtime staging -> databuild -> ordered query; published location-honest launch/databuild fixes in `46e02159` and corrected DotScript banner syntax in `b9d48021`. | `docs/maintenance/SESSION_CLOSEOUT_CLONE_JOURNEY_CERTIFICATION_2026-07-15.md` |
| 2026-07-14 | x64base engine/edition separation implementation | Inverted xbase/xindex, proved LEAN + NONE CLI and Python builds, split product commands/sources, and replaced recursive packaging with tracked allow-lists; project licensing: To be determined. | `docs/maintenance/SESSION_CLOSEOUT_X64BASE_ENGINE_EDITION_SEPARATION_IMPLEMENTATION_2026-07-14.md` |
| 2026-07-14 | x64base engine/edition separation research | Separated index capability from product edition; proposed LEAN essentials versus full education; measured source and package risks; recorded the implementation/proof plan; project licensing: To be determined. | `docs/maintenance/SESSION_CLOSEOUT_X64BASE_ENGINE_EDITION_SEPARATION_RESEARCH_2026-07-14.md` |
| 2026-07-14 | xbase build proof continuation | Added two registered pydottalk CTests; proved read plus disposable physical-order update/append/delete/reopen with no sidecars and unchanged source fixture; preserved the no-index-binary distinction | `docs/maintenance/SESSION_CLOSEOUT_XBASE_PROOF_MATRIX_2026-07-14.md` |
| 2026-07-14 | AI Portal outcome digestion and build architecture review | Corrected developer-profile exposure; routed recursive co-development doctrine; established that current xbase structurally depends on xindex; passed a read-only pydottalk table smoke without claiming index semantics | `docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_BUILD_ARCHITECTURE_2026-07-14.md` |
| 2026-07-14 | MCC databuild, hygiene, AI portal corrections | Databuild lane runtime-proven; AIF-006 promoted; `CURRENT_TARGET` corrected; index-expression drift repaired (13 files); first clean PR merged to GitHub main (`c8826725`) | `docs/maintenance/SESSION_CLOSEOUT_MCC_DATABUILD_2026-07-14.md` |

## User Status Buckets

| Bucket | Meaning | Current items |
| --- | --- | --- |
| captured | Useful AI-assisted material has been noticed. | Seed rows AIF-001 through AIF-004. |
| classified | Material has candidate tags and a route. | Seed rows AIF-001 through AIF-004. |
| distilled | Raw interaction has been reduced to a durable artifact. | Manifest, workflow, intake queue, dashboard. |
| anchored | Item points to source, proof, contract, report, or design-intent evidence. | AIF-001, AIF-002, AIF-003, AIF-006, AIF-013, AIF-014, AIF-015, AIF-016, AIF-017. |
| routed | Item has a destination lane. | AIF-001 through AIF-006, AIF-008 through AIF-017. |
| promoted | Item has moved into its destination lane with evidence. | AIF-008, AIF-009, AIF-010, AIF-016; existing agent card and contract lifecycle predate this lane. |
| review-needed | Human review or stronger evidence is needed. | AIF-004; AIF-011; AIF-012 profile wording and public-branch exposure; AIF-017 manual drift; xindex CDX/CNX/LMDB runtime behavior. |
| rejected | Item is explicitly not part of the system. | AIF-007. |
| superseded | Item has been replaced by a stronger artifact. | none yet. |

## Authority Levels

Use this table when reading any AI Friendly item:

| Level | User meaning |
| --- | --- |
| chat-only | Conversation material only; not durable. |
| captured | Saved or referenced for possible review. |
| draft | Written in repo, not yet reviewed or proven. |
| design-intended | Accepted as a design direction, not runtime-proven. |
| source-defined | Current source declares or implements it. |
| runtime-proven | A command, test, transcript, or smoke run proves it. |
| HELP-documented | HELP/CMDHELP exposes it to users. |
| CMDHELPCHK-validated | Validation has checked the HELP/contract surface. |
| publication-ready | SelfDoc/manualgen can publish it with evidence. |
| student-ready | LabTalk can present it to learners. |
| rejected | Reviewed and excluded. |
| superseded | Replaced by a newer or stronger artifact. |

## Current AI Work Log

| Date | Work | Mutation | Evidence read | Result |
| --- | --- | --- | --- | --- |
| 2026-07-04 | Seed AI Friendly lane | docs only | LabTalk docs, contract lifecycle, agent bootstrap card, SelfDoc lab docs | Created lane manifest, workflow, intake queue. |
| 2026-07-04 | Add user visibility surface | docs only | AI Friendly seed docs | Created dashboard and linked it from README. |
| 2026-07-04 | Add new-AI assimilation portal/book | docs and MAINT visibility | AI Friendly docs, agent bootstrap card, DotScript handoff | Created durable onboarding path for new or second-opinion AI. |
| 2026-07-14 | Publish SDLC-first website and AI Portal update | website source, validated artifacts, staging mirror, GitHub Pages, and private Sites source/version | Website publication contract, AI Portal seeds, maintainer build transcript, live cache-bypassed readback | Website source `f29471e0` is pushed on `codex/lean-sites-publish`; `C:\x64base\dottalk-webui\public-site` is synchronized; GitHub Pages commit `cb907fc6` is built and live without local-drive text; the social card and replacement Campus graphic are live. Private Sites version 12 is saved from the same source, but its owner-only deployment failed in the Sites authentication callback service with HTTP 400, so Sites remains on version 11 pending service repair. |
| 2026-07-14 | Restore useful version 11 AI Portal detail | website source, validated artifacts, staging mirror, GitHub Pages, and private Sites source/version | Direct comparison of Sites version 11 source `8184c765` with current website source plus maintainer build and live readback | Commit `c499ec7e` restores the implementation inventory, APH-0 through APH-6 hardening roadmap, frontal-memory explanation, detailed safety rules, and Campus role without reverting the newer fast-start and SDLC model. `C:\x64base\dottalk-webui\public-site` is synchronized and GitHub Pages commit `2a4c6cf6` is built and live with all restored sections and no local-drive text. Private Sites version 13 is saved from the same source, but its owner-only deployment again failed in the Sites authentication callback service with HTTP 400; Sites remains on version 11 pending service repair. |
| 2026-07-14 | Digest AI Portal outcome and review xbase/xindex/pydottalk build shape | docs only; read-only artifact and DBF checks | AI Portal/co-development docs, live Git refs, current CMake target graph, generated Visual Studio projects, Release artifacts, PE dependencies, pydottalk read-only smoke | Corrected AIF-012 publication claims, added AIF-013, strengthened the recursive coproject model, and established the present build boundary: pydottalk consumes xbase and xindex; xbase cannot currently be selected without xindex; table access works, while index semantics remain unproven. |
| 2026-07-14 | Establish xbase physical-order proof matrix | binding test source, additive CTest registration, docs; temporary DBF copy only | Contract shelf/registry/lifecycle, database safety/collation contracts, INDEX/REINDEX/USE usage contracts, current build graph, existing pydottalk artifact | Added AIF-014 and two passing CTests. Physical-order xbase CRUD is runtime-proven through the existing module; clean builds and native xindex semantics remain open. |
| 2026-07-14 | Implement engine/index and lean/education product separation | CMake, C++, Python, manifests, docs, tests | xbase/xindex lifecycle, CLI registry, pydottalk, build graph, runtime command transcript, tracked package inputs | `xbase` is table-only and optional-provider neutral; LEAN + NONE builds without xindex; full LabTalk and index commands are absent; product allow-lists replace recursive data installation. Project licensing: To be determined. Public source publication remains pending Path A. |
| 2026-07-14 | Research engine/index and lean/education product separation | docs only | Current xbase/xindex/CMake graph, command and HELP metadata, DD-001/DD-002/DD-004, data install contents, project status, vcpkg notices, official third-party terms | Added AIF-015 and a staged separation plan. Confirmed two independent build axes, proposed `EDU_ESSENTIALS` versus `LABTALK_FULL`, and found that the prior recursive install could package ignored/untracked artifacts. |
| 2026-07-15 | Certify and publish the cold-clone journey | launcher and MCC script fixes, fixtures, build/publication docs, proof record | Fresh clone build, runtime staging, MCC rebuild, LMDB build, ordered readback, public commit inspection | A fresh clone proved the full journey. Location-honest fixes published in `46e02159`; printed DotScript comment corrected in `b9d48021`. |
| 2026-07-15 | Reconcile public AI Portal state and startup paths | public Markdown only | AI Portal authority seeds, current target, dashboard, intake queue, cold-clone closeout, Path A plan, public PR/commit state | PR #7 was rejected as overbroad; PRs #8 and #9 merged narrowly. Public consistency is corrected; authoritative-development reconciliation remains the next gate. |

## Items Needing User Review

| ID | Item | Review question | Suggested outcome |
| --- | --- | --- | --- |
| AIF-004 | AI Friendly lane proposal | Does this lane shape match the intended operating model? | Mark design-intended after review, then add a contract registry row only if it becomes a durable constraint. |
| AIF-012 | Developer profile and prior public-branch exposure | Are the profile facts and wording acceptable, and does the already-public historical branch require any separate privacy/history action? | Keep it off `main` and publication surfaces until reviewed; do not mistake a later deletion for history removal. |

## Items Needing Proof

| Item | Needed proof | Route |
| --- | --- | --- |
| AI Portal public-to-development reconciliation | Compare the affected public Markdown files with their current `D:\code\ccode` versions, preserve newer local facts, and verify the reconciled development state before any promotion. | `docs/maintenance/SESSION_CLOSEOUT_AI_PORTAL_PUBLIC_CONSISTENCY_2026-07-15.md` |
| AI Portal hardening APH-0 | Baseline tests, reproducible startup, and zero unexplained missing paths | `labtalk/ai_portal` |
| xindex mutation hardening | Add attached-index replace/append/delete/recall/pack synchronization, public CDX/LMDB workflow, and stale/collation rejection tests | `docs/maintenance/XBASE_XINDEX_BUILD_PROOF_MATRIX_V1.md` |
| LEAN catalog completeness | Add HELP/DDICT/script component leak tests beyond the proven source, command, manifest, and installed-runtime boundaries | `docs/maintenance/X64BASE_ENGINE_EDITION_SEPARATION_PLAN_V1.md` |
| Edition-system public publication | Publish the coherent edition source/build changeset and certify the full stranger journey from a cold clone | `docs/maintenance/EDITION_PUBLICATION_PLAN_A_V1.md` |
| Future generated AI Friendly inventory report | Read-only scanner/report run | `docs/ai-friendly/reports` |
| Future assimilation smoke | Runtime check for `MAINT AI ASSIMILATE` after MAINT integration | `src/cli/cmd_maint.cpp` |

## Drift Risks

| Risk | Mitigation |
| --- | --- |
| AI Friendly becomes a duplicate documentation shelf. | Route to existing lanes first. |
| Raw chat is treated as authority. | Keep chat material as source material until distilled and anchored. |
| Useful interactions are hoarded instead of curated. | Capture only material with reuse value. |
| Claims outrun source/runtime proof. | Use authority levels and proof gates before promotion. |
| Public-only correction is mistaken for integrated development state. | Reconcile into `D:\code\ccode` before treating the public edit as project authority. |

## Next Practical Step

Reconcile the AI Portal consistency corrections from public `main` into the
current authoritative development tree at `D:\code\ccode`. Preserve any newer
local facts, verify the resulting documents against development source and
runtime evidence, and promote again only if a reviewed development-to-public
delta remains.
