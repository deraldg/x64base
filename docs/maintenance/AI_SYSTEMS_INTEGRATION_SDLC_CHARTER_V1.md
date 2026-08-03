# AI Systems Integration SDLC Charter v1

Status: **active seed; analysis and requirements**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Initial run: `AIPR-20260803-003`
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycles: **DotTalk++ SDLC**, **LabTalk SDLC**, **maintenance SDLC**, and **PLDC**
Incorporated lanes: see section 4
SDLC lane: `design` (M0 analyze and M1 requirements seed)
Operating mode: `maintenance`
Instructional overlay: `laboratory`
Change class: `C3`
Owner and final authority: `member.derald`
Initial steward: `member.ai.codex.local`

## 1. Mission

Integrate the AI Portal, AI Friendly curation, onboarding, memory, reports,
agent coordination, Pseudo-Chat, AI-BBS, authorization, evidence, and public
projections into one understandable and maintainable system.

This SDLC owns the relationships, shared vocabulary, cross-system requirements,
and end-to-end acceptance gates. It does not take ownership away from the
incorporated projects and lanes.

## 2. Named lifecycle rule

Documents must say **AI Systems Integration SDLC**, **DotTalk++ SDLC**,
**LabTalk SDLC**, or **maintenance SDLC**. A bare phrase such as "the SDLC" is
not sufficient when more than one lifecycle could apply.

Every work record identifies:

```text
owning_lifecycle:
incorporating_lifecycle:
sdlc_lane:
project_id:
incorporated_lanes:
related_lifecycles:
```

The owning lifecycle controls the artifact or behavior. The incorporating
lifecycle schedules and integrates it. A related lifecycle supplies or consumes
evidence. Incorporation never transfers ownership by implication.

## 3. Teaching-Grade Congruence Rule

This project inherits the rule recorded in
`labtalk/LABTALK_SDLC_FRAMEWORK_v0.md`: every SDLC must practice the process it
teaches.

```text
Perform the work -> preserve evidence -> evaluate the process -> improve the
process -> document the improvement -> teach from the real example.
```

Each phase produces both an operational artifact and an educational account of
what was actually done. Gates not exercised are not taught as completed.
Mistakes, corrections, and superseded decisions remain visible with dates and
evidence. The implementation is part of the curriculum.

## 4. Prior art incorporated, not duplicated

| Prior work | Contribution | Ownership retained by |
| --- | --- | --- |
| AIF-006, AIF-021, AIF-024 | startup reconciliation, corrective audit discipline, and document-as-work evidence capture | maintenance SDLC |
| AIF-020, AIF-050, AIF-062, AIF-071 | report audit, run attribution, clone-verifiable evidence, discoverability, and pre-push enforcement | maintenance SDLC |
| AIF-045 | identity, permission eligibility, scoped authorization, grant expiry, and revocation | DotTalk++ SDLC / `project.x64base.identity` |
| AIF-052, AIF-054, AIF-055 | AI-BBS server, standalone daemon, authenticated guest path, and local transport | DotTalk++ SDLC |
| AIF-056, AIF-058 | portal onboarding standards and explicit AI-role boundaries | LabTalk SDLC |
| AIF-057 | asynchronous BBS pickup and handoff convention | DotTalk++ SDLC |
| AIF-060 | agency model plus operational-report sensitivity and publication analysis | maintenance SDLC |
| AIF-073 | working, episodic, prospective, semantic, procedural, and evidence memory | maintenance SDLC / `project.ai_friendly.agent_memory` |
| AIF-075, AIF-076, AIF-083 | BBS authorization/provenance, Pseudo-Chat separation, and remaining agency defects | DotTalk++ SDLC |
| AIF-082 | Tier 0, Tier 1, recall graph, stopping test, and acceptance measurement | LabTalk SDLC |
| AIF-084 | physical isolation design for concurrent work | DotTalk++ SDLC |
| AIF-085 | cross-platform, tested workflow-tool rule | maintenance SDLC |
| AI Portal Hardening | proof-aware context compiler and guarded execution | LabTalk SDLC |

## 5. Initial system model

The maintained human-readable component map is
`docs/maintenance/AI_SYSTEMS_CROSSWALK_V1.md`.

The authority order is:

```text
owner decision and durable contracts
-> authoritative source and owned registries
-> runtime proof and accepted evidence
-> closeouts and governed state records
-> generated operational projections
-> reviewed educational or public publication
```

Transport, dashboards, reports, chat, and website pages do not become authority
merely because they are convenient or visible.

## 6. Integration defect register

| ID | Defect | Planned correction |
| --- | --- | --- |
| D1 | Pseudo-Chat names packets, coordination, BBS transport, worklog handoff, and future duplex interaction. | Keep Pseudo-Chat as an umbrella pattern and assign stable names and records to each component. |
| D2 | "Reports" conflates internal operational views, AI-authored audit records, and public reports or whitepapers. | Define document classes and make public Reports a reviewed publication collection. Internal generated views live under AI operations. |
| D3 | `ai_report_index.yaml` is not a complete catalog of AI reports or AIF work. | Define a complete discoverability projection over closeouts, external intake, AIF records, and generated views without making the projection authoritative. |
| D4 | `AIF_RULINGS_REPORT.html` can be mistaken for a report of all AIF work. | Name it **AIF Open Rulings** and expose its ruling-sheet source and coverage. |
| D5 | Queue rows, current target, run pointers, closeouts, and generated reports can disagree. | Select canonical state fields, generate projections, and validate disagreements instead of hand-reconciling silently. |
| D6 | Older publication guidance conflicts with the current local-only posture for raw AI reports. | Supersede it with default-deny sensitivity and explicit per-artifact publication decisions. |
| D7 | BBS and worklog convenience can be mistaken for authority. | Require lane, run, actor, authorization, and promotion links; only a governed closeout or registry transition changes authoritative state. |
| D8 | AIF-064 names the Retro VM/emulator lane in the intake queue but also names registry-fragment tooling in that tool and the AIF-084 worktree charter. | Treat the number as unresolved prior-art identity debt; do not silently adopt either meaning. Reconcile or renumber it through the owner and atomic claim process. |
| D9 | `SDLC_FAST_START_SEED_V1.md` calls its mandatory task block a 20-field superset, but the enumerated block contains 19 fields. | Preserve all 19 named fields, report the mismatch, and resolve the declared count or schema in AIF-082 rather than inventing a field here. |

## 7. Actor-neutral boundary and trespass

Humans and AI follow the same scoped-authorization rule. The owner/admin is the
sole structural exception to the ask-for-permission protocol.

The candidate contract is
`docs/contracts/TRESPASS_AND_DELEGATED_AUTHORIZATION_CONTRACT_V1.md`.
It defines trespass, validated delegation, attenuation, expiry, revocation, and
acceptance tests. No runtime delegation or trespass gate is claimed by this
charter.

The owner explicitly authorized the AIF-086 integration mission and later its
bounded housekeeping plus exact-path commit and push to `development`. Work
inside the scope recorded by run `AIPR-20260803-003` is therefore authorized,
not trespass. Runtime, staging-repository, `main`, and publication authority
remain outside that grant.

## 8. SDLC phases and gates

| Phase | Required result | Exit gate |
| --- | --- | --- |
| M0 Analyze | charter, prior-art reconciliation, system cross-walk, defect register | Owner agrees the map names the right systems and owners. |
| M1 Requirements | document classes, naming rules, trespass and delegation contract, sensitivity rules | Requirements contain no ownership transfer or authority inflation. |
| M2 Architecture | canonical component/edge model and source-of-record matrix | Every projection resolves to a canonical record; no duplicate system of record. |
| M3 Design | schemas, generators, validators, APIs, migration and rollback plans | Review proves deterministic generation and reversible adoption. |
| M4 Implementation | report/status reconciliation and Pseudo-Chat component separation | Targeted tests pass; existing consumers remain supported or explicitly migrated. |
| M5 Agency enforcement | parent-child grants, attenuation, trespass preflight and audit events | Human/AI delegation matrix passes, including denial, expiry, revocation, and scope-amplification tests. |
| M6 Publication | AI navigation, public Reports collection, local-only enforcement | Default-deny public build and live readback pass; internal artifacts remain absent. |
| M7 Maintenance and teaching | freshness ownership, regression cadence, worked LabTalk case | A new participant can explain and operate the integrated system from generated evidence. |

## 9. Planned implementation waves

1. Vocabulary, project registration, charter, cross-walk, and candidate contract.
2. Canonical status and report classification.
3. Generated catalog and drift validators.
4. Pseudo-Chat and BBS boundary reconciliation.
5. Delegated authorization and trespass enforcement.
6. Public AI and Reports separation.
7. LabTalk worked case and maintenance feedback.

Each wave receives its own exact mutation scope. An incorporated lane is not
changed merely because it appears in this charter.

## 10. M0 exclusions

This initial slice does not:

- change runtime identity, authorization, BBS, or socket behavior;
- authorize an AI to delegate authority;
- alter DBF or other persistent runtime data;
- regenerate or publish reports;
- change website navigation;
- rewrite Git history;
- promote development work to staging or public branches.

## 11. Definition of done

The SDLC is complete only when:

1. every component has a stable identity, owning lifecycle, authority class,
   sensitivity, freshness rule, and proof path;
2. Pseudo-Chat components are distinguishable in records and interfaces;
3. generated status and report views reconcile with canonical state;
4. trespass is prevented or detected for humans and AI through the same rule;
5. delegated authorization cannot exceed or outlive its parent;
6. local-only information cannot enter a public build by default;
7. the project teaches from the exact artifacts and gates it used.
