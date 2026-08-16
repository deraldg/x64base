# AI Systems Integration SDLC Charter v1

Status: **M1 accepted 2026-08-05; M2 architecture active; bounded M3 schema candidate**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Initial run: `AIPR-20260803-003`
Current contribution run: `AIPR-20260816-001`
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycles: **DotTalk++ SDLC**, **LabTalk SDLC**, **maintenance SDLC**, and **PDLC**
Incorporated lanes: see section 4
SDLC lane: `architecture/design` (M2 active; bounded M3 schema candidate)
Operating mode: `maintenance`
Instructional overlay: `laboratory`
Change class: `C3`
Owner and final authority: `member.derald`
Initial steward: `member.ai.codex.local`
Current steward: `member.ai.claude.cowork`
Contributing agent for the 2026-08-16 assignment-link slice: `member.ai.codex.local`

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

### 3.1 Recursive and cyclical re-entry rule

The phase names describe required concerns, not a one-way conveyor. The AI
Systems Integration SDLC is recursive when viewed as control flow and cyclical
when viewed across successive improvements. New evidence, prior art, changed
needs, failed assumptions, or a process defect MAY return work to an earlier
phase. A later artifact does not waive an earlier gate when the cycle returns.

Recursion is a recovery property, not a substitute for doing the first pass
well. The lifecycle MUST reduce avoidable surprise through proportionate
up-front problem definition, needs assessment, prior-art discovery, inventory,
authority and ownership mapping, risk assessment, requirements elicitation,
acceptance criteria, traceability, and review. Re-entry addresses genuinely new
evidence and corrects omissions; it does not retroactively make an avoidable
omission acceptable.

An agent authorized to analyze an integration scope and able to read the
relevant repository MUST take initiative on those classical, non-mutating SDLC
steps unless the owner explicitly narrows or waives them. The owner should not
have to enumerate standard discovery work. This initiative duty does not grant
mutation, delegation, commit, promotion, or publication authority.

Every re-entry MUST record:

1. the evidence or defect that caused the return;
2. the earlier phase and gate being reopened;
3. downstream artifacts whose assumptions may now be stale;
4. the evidence required to leave the reopened phase again; and
5. the process improvement that will be taught from the correction.

An empirical prior-art or orphan-work scan is a discovery and needs-assessment
activity before it is a housekeeping activity. Its first result MUST be an
inventory and cross-walk of purpose, maturity, ownership, authority,
dependencies, requirement coverage, duplication, conflict, and evidence gaps.
Disposition -- including Sidecar movement, archival, deletion candidacy, or
incorporation -- follows a review gate. A reversible move does not substitute
for discovery and does not prove that classification was correct.

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
| D10 | The requested empirical orphan-work scan was misclassified as housekeeping, and reversible Sidecar disposition began before the discovery inventory and requirements cross-walk were produced. | Re-enter M1 discovery, include the Sidecar batch in the evidence set, complete needs assessment before further disposition, and retain this defect as the teaching case for recursive phase re-entry. |
| D11 | Local AI operational pages are manually generated HTML snapshots and can lag both the repository and an older preview copy. | Make local AI Operations views dynamic, read-only projections over canonical sources. Reserve static HTML for explicitly dated export or reviewed publication. |
| D12 | A prior-art scan created a duplicate crosswalk and competing AIF-089 diagram lane before finding AIF-086. | Preserve AIF-086 as the single owner; require discovery of `docs/maintenance/` and `coordination/aif/` before minting a lane. AIF-089 was reverted and is not revived by later diagrams. |
| D13 | Agent identity, governed assignment, provider chat identity, project, run, BBS thread, language, timestamps, and mutable UI position had no single durable relationship record. | Define `SYSCHATLNK` with immutable `LINKKEY` and shared `CONVKEY`; expose its contract and diagrams through the AI Portal while keeping production persistence behind a later gate. |

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

### Phase decision record

| Decision | Result | Authority | Evidence |
| --- | --- | --- | --- |
| M0 exit | passed 2026-08-03 | `member.derald` | Owner ruling: "Yes this looks good for M0"; M0 charter, cross-walk, prior-art reconciliation, and defect register at commit `1a61e9e6a`. |
| M1 entry | active 2026-08-03 | `member.derald` | Owner direction: "next M1?"; bounded requirements run `AIPR-20260803-004`. |
| M1 discovery re-entry | active 2026-08-03 | `member.derald` | Owner identified that the empirical `docs` and `tools` scan was part of requirements/needs assessment. D10 reopens discovery before further curation or M1 exit review. |
| M1 discovery assessment | owner-review candidate 2026-08-03 | `member.ai.codex.local` | `AI_SYSTEMS_INTEGRATION_DISCOVERY_AND_NEEDS_ASSESSMENT_M1_V1.md` measures the four named surfaces, includes the Sidecar batch, cross-walks prior art, and proposes no disposition. |
| M1 local-projection requirement | accepted requirement 2026-08-03 | `member.derald` | Owner ruling: "the pages should be dynamic." Local AI operational pages must derive current canonical state on request or through an automatically invalidated bounded cache; static snapshots are exports, not the normal Portal view. |
| M1 visibility prototype | authorized and runtime-observed 2026-08-03 | `member.derald` | Owner promoted immediate local implementation because a visible UI is needed for further design, testing, and SDLC decisions. `tools/reports/serve_dynamic_reports.py` now serves request-time local reports on port 3000 and proxies the website on port 3002. This is an evidence-producing prototype, not public or production deployment. |
| M1 exit | passed 2026-08-05 | `member.derald` | Owner ruling recorded in `AI_SYSTEMS_INTEGRATION_STEWARD_ASSIGNMENT_AND_M1_CONTINUATION_2026-08-05_V1.md`: "I already approved M1." Historical pending-review records remain preserved. |
| M2 entry | active 2026-08-16 | `member.derald` | Owner directed AIF-lane integration of the agent/assignment/chat relationship and its portal artifacts. `SYSCHATLNK` supplies a bounded component and edge model; it does not close the full M2 gate. |
| M2/M3 bounded contribution | source-defined plus disposable X64 proof 2026-08-16 | `member.ai.codex.local`, contributing agent | Contract, 35-field schema, maintenance manual, standalone PFD/DFD, portal registry, regression, and accepted transcript under run `AIPR-20260816-001`. No production catalog or writer is claimed. |
| M2 relational normalization plan | source-defined design candidate 2026-08-16 | `member.ai.codex.local`, contributing agent | Run `AIPR-20260816-002` narrows `SYSCHATLNK` to the assignment/conversation participation edge and diagrams the related conversation, connector, runtime-session, route, language, context, UI, post-provenance, and recovery records. It explicitly models `dottalkpp`, the separate `dottalk_bbsd` executable, and daemon connection sessions. No production table or M2 exit is claimed. |

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

## 9.1 Bounded M2/M3 contribution: agent-assignment conversation link

The 2026-08-16 owner request adds one stable integration component without
transferring ownership from identity, BBS, project, or run registries:

| Field | Record |
| --- | --- |
| Stable component | `ai.link.agent_assignment_conversation` |
| Physical design name | `SYSCHATLNK` |
| Row grain | one `SYSASSIGN` assignment participating in one local conversation |
| Unique binding | `LINKKEY` |
| Shared multi-agent conversation | `CONVKEY` |
| Identity edges | `MEMBERID -> SYSMEMBER.ID`; `ASSIGNID -> SYSASSIGN.ID` |
| Evidence and BBS edges | `RUNID -> ai_runs`; `BBSTHRID -> SYSTHREAD.ID` |
| Portal edge | `PROJKEY` plus mutable title/section/position observation |
| Language and time | UTF-8, BCP 47 `LOCALE`, `CODELANG`, UTC epoch creation/modification/observation |
| Canonical contract | `docs/contracts/AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md` |
| Portal registry | `labtalk/registries/agent_assignment_links.yaml` |

Artifact set:

- `docs/contracts/AI_AGENT_ASSIGNMENT_LINK_CONTRACT_V1.md`
- `docs/maintenance/AI_AGENT_ASSIGNMENT_LINK_MAINTENANCE_MANUAL_V1.md`
- `dottalkpp/data/schemas/syschatlnk_v1.schema.json`
- `dottalkpp/data/scripts/ddl/syschatlnk_x64_regression.dts`
- `labtalk/diagrams/ai_agent_assignment_link_pfd_v1.mmd`
- `labtalk/diagrams/ai_agent_assignment_link_dfd_v1.mmd`
- `labtalk/proofs/runs/20260816_101951_agent_assignment_link_regression.txt`

The schema was validated and a physical DBF was created and read back only at
`dottalkpp/data/tmp/SYSCHATLNK.dbf`. That DBF and its four sidecars were removed
after proof. No table exists in production metadata, and no other DBF table was
created, modified, or deleted by this contribution. A production writer,
catalog location, migration, physical indexes, relation enforcement, and
rollback proof remain later gates.

## 9.2 Relational normalization plan

The next design candidate is
`docs/maintenance/AI_PORTAL_BBS_PSEUDO_CHAT_RELATIONAL_SCHEMA_PLAN_V1.md`.
It preserves the existing `LINKKEY` and `CONVKEY` contract while separating the
different record grains currently carried by one 35-field candidate row:

- shared conversation identity;
- governed assignment participation;
- connector, runtime session, and transport route, including distinct
  `dottalkpp`, `dottalk_bbsd`, and daemon-connection boundaries;
- provider-native, BBS-thread, and document-relay route details;
- multilingual tags, Portal context, and append-only UI observations;
- BBS/provider message provenance with origin, principal, writer connector,
  exact reply parent, and run context;
- a recoverable multi-table write intent plus ordered transaction-item manifest
  for cross-process mutation.

Maintained diagram sources:

- `labtalk/diagrams/ai_portal_bbs_pseudo_chat_relational_erd_v1.mmd`
- `labtalk/diagrams/ai_portal_bbs_pseudo_chat_relational_dfd_v1.mmd`
- `labtalk/diagrams/ai_portal_bbs_pseudo_chat_relational_pfd_v1.mmd`

This plan corrects an architectural relationship and prepares owner/steward
decisions. It does not modify the current schema JSON, register a production
catalog, write identity/BBS data, or authorize a website projection.

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
