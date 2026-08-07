# AI Systems Integration SDLC Requirements v1

Status: **M1 discovery assessment candidate complete; owner review required**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Run: `AIPR-20260803-004`
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycles: **DotTalk++ SDLC**, **LabTalk SDLC**, **maintenance SDLC**, and **PDLC**
SDLC lane: `design` (M1 requirements)
Operating mode: `maintenance`
Change class: `C3`
Build target: `documentation_only`
Owner and final authority: `member.derald`
Steward and author: `member.ai.codex.local`

## 1. Phase boundary

The owner accepted the AIF-086 M0 system map on 2026-08-03. M1 converts that
map into testable requirements. It does not select a machine-graph schema,
change a report generator, alter runtime authorization, rename files, change
website navigation, or publish material.

The normative words **MUST**, **MUST NOT**, **SHOULD**, and **MAY** identify
requirement strength. A future implementation cannot claim compliance merely
because a document, registry row, command, or generated page exists.

### 1.1 Recursive discovery and needs-assessment requirements

The lifecycle is recursive in control flow and cyclical across improvement
runs. New evidence can reopen an earlier phase even after later-phase artifacts
exist. Re-entry does not erase those artifacts; it marks their assumptions for
revalidation.

The correction pass is recorded in
`docs/maintenance/AI_SYSTEMS_INTEGRATION_DISCOVERY_AND_NEEDS_ASSESSMENT_M1_V1.md`.
It completes the named four-surface census as an owner-review candidate. It does
not self-approve these requirements or authorize disposition or M2 entry.

| ID | Requirement |
| --- | --- |
| `R-01` | Every empirical prior-art or orphan-work scan MUST begin as non-mutating discovery and needs assessment. |
| `R-02` | Discovery MUST inventory each candidate's purpose, maturity, owning lifecycle or owner, authority class, dependencies, evidence, and current integration state. |
| `R-03` | Discovery MUST cross-walk candidates to existing requirements and identify satisfied, partial, missing, duplicate, conflicting, superseded, and unknown work. |
| `R-04` | Unknown or apparently misplaced work MUST NOT be equated with disposable work. Disposition requires a separately recorded classification and review gate. |
| `R-05` | A phase re-entry MUST name its trigger, reopened gate, potentially stale downstream artifacts, new exit evidence, and resulting process lesson. |
| `R-06` | Reversible Sidecar movement MAY preserve a reviewed disposition candidate, but MUST NOT substitute for discovery, classification, or integration analysis. |
| `R-07` | When disposition occurs before discovery is complete, the affected material MUST remain recoverable, MUST re-enter the discovery evidence set, and further disposition MUST pause until the missed gate is satisfied. |
| `R-08` | Recursive re-entry MUST be treated as recovery and learning, not as a substitute for proportionate up-front execution of classical SDLC steps. |
| `R-09` | An agent with authorized analysis scope and repository read access MUST proactively perform the applicable non-mutating steps: problem and needs definition, prior-art inventory, authority and ownership mapping, risk assessment, requirements and acceptance criteria, traceability, and review preparation. |
| `R-10` | The discovery record MUST distinguish genuinely emergent evidence from avoidable omissions in the earlier pass; both trigger correction, but only the latter triggers a process-defect record. |
| `R-11` | Before changing from analysis to disposition or from one subtask to another, the actor MUST trace the proposed action back to the original requested outcome and its current phase gate. |

## 2. Authority and ownership requirements

| ID | Requirement |
| --- | --- |
| `A-01` | Every governed component and artifact MUST identify exactly one owning lifecycle or a deterministic rule that selects one per record. |
| `A-02` | An incorporating lifecycle MUST NOT acquire ownership merely by scheduling, indexing, rendering, transporting, or teaching another lifecycle's work. |
| `A-03` | Every projection MUST identify its canonical source and MUST NOT be described as a system of record. |
| `A-04` | A lane or project state transition MUST resolve to an authorized actor, durable record, owning lifecycle, and evidence or explicit evidence gap. |
| `A-05` | A claim, session check-in, lock, worktree, BBS post, dashboard row, or chat message MUST NOT be treated as authorization by itself. |
| `A-06` | A correction MUST preserve the superseded record and identify the later ruling; it MUST NOT silently rewrite history. |
| `A-07` | Unresolved identity conflicts, including the two current meanings of AIF-064, MUST remain blocked from silent incorporation until owner adjudication. |

## 3. Naming requirements

| ID | Requirement |
| --- | --- |
| `N-01` | **AI** SHOULD be the umbrella navigation label for AI Portal, onboarding, coordination, memory, and internal AI-operational material. |
| `N-02` | **AI Operations** MUST identify internal generated status, access, boards, rulings, and similar operational projections. |
| `N-03` | **Reports** MUST be reserved for reviewed public-interest reports, whitepapers, and reviewed educational cases. Raw operational projections and audit records MUST NOT enter Reports merely because their filenames contain `REPORT`. |
| `N-04` | `AIF_RULINGS_REPORT.html` MUST be presented to people as **AIF Open Rulings** and MUST identify its ruling-sheet sources and incomplete coverage. The filename MAY remain for compatibility until migration is designed. |
| `N-05` | **Pseudo-Chat** MUST remain an umbrella interaction pattern, never a system-of-record name. Records and interfaces MUST name the actual component that carried the interaction. |
| `N-06` | Documents discussing a lifecycle MUST use its explicit name: AI Systems Integration SDLC, DotTalk++ SDLC, LabTalk SDLC, maintenance SDLC, or PDLC. A bare "the SDLC" is insufficient when scope could be ambiguous. |

## 4. Document-class requirements

Every governed report-like artifact MUST have one primary class:

| Class | Meaning | Default publication posture |
| --- | --- | --- |
| `operational_projection` | Generated view of current operational state. | local/internal |
| `audit_record` | Actor, task, authorization, evidence, or external-intake record. | local/internal; sensitivity review required |
| `public_report` | Reviewed public-interest technical or research report. | public only after explicit approval |
| `whitepaper` | Stable evidence-backed argument or architecture paper for an academic audience. | public only after editorial and sensitivity review |
| `educational_case` | Worked case derived from actual lifecycle evidence. | reviewed educational/public delivery only |

| ID | Requirement |
| --- | --- |
| `D-01` | Each artifact MUST declare or deterministically inherit `document_class`, `owning_lifecycle`, `canonical_source`, `authority_class`, `sensitivity`, `audience`, `freshness_owner`, and `proof_or_review`. |
| `D-02` | A generated artifact MUST retain the class of its purpose; generation does not promote an operational projection into a public report. |
| `D-03` | An artifact with more than one plausible class MUST select one primary class and MAY list secondary uses. Secondary use MUST NOT weaken the primary class's controls. |
| `D-04` | `ai_report_index.yaml` MAY provide discoverability but MUST NOT become authority for the indexed content or imply complete coverage until a completeness gate exists. |
| `D-05` | Report names containing `latest` MUST expose generation time, source identity, and a staleness rule. |

## 5. Sensitivity and publication requirements

The existing report tooling uses `public`, `internal`, and `private`. M1 fixes
their required meaning without changing the implementation:

| Sensitivity | Required meaning |
| --- | --- |
| `private` | MUST NOT enter a public build or public repository projection. |
| `internal` | Default-deny. MAY become a publication candidate only through artifact-specific review and an explicit allow-list decision. |
| `public` | Review has passed for the named artifact and revision; publication still requires the separate publication authority and build gate. |

| ID | Requirement |
| --- | --- |
| `S-01` | A missing, unknown, or unrecognized sensitivity MUST fail closed and be excluded from public output. |
| `S-02` | Public generation MUST start from an explicit artifact allow-list. It MUST NOT publish a directory or include every artifact not marked `private`. |
| `S-03` | An `internal` artifact MUST NOT be emitted by public mode until a reviewed record changes that exact artifact and revision to `public`. |
| `S-04` | Authentication surfaces, member keys, credential-presence indicators, permission matrices, private protocol details, and unratified owner rulings MUST remain `private`. |
| `S-05` | Board publication MUST be selected per board and MUST review post bodies. A board's harmless structure does not make its posts public. |
| `S-06` | Absolute local paths, internal infrastructure details, proof command lines, and identity data MUST receive a sensitivity review before public use. |
| `S-07` | Publication authorization MUST remain separate from document review, public-build generation, commit, push, and live readback. Passing one stage MUST NOT imply another. |
| `S-08` | A public build MUST prove that all `private`, unreviewed `internal`, missing-sensitivity, and non-allow-listed artifacts are absent. |
| `S-09` | Website-to-repository network access MUST remain outside this requirements slice; importing public material does not justify granting agent egress. |

The present `build_reports.py --public` behavior is not claimed compliant with
`S-01` through `S-03`: it currently suppresses `private` items but does not
require `internal` items to be explicitly promoted to `public`. That is a
recorded implementation gap for M3/M4, not an M1 code change.

## 6. Trespass and delegated-authorization requirements

The normative detail is in
`docs/contracts/TRESPASS_AND_DELEGATED_AUTHORIZATION_CONTRACT_V1.md`.

| ID | Requirement |
| --- | --- |
| `T-01` | Trespass controls MUST apply to human and AI actors through the same scope rule. |
| `T-02` | The owner/admin ask-for-permission exemption MUST NOT remove attribution, evidence, or accountability. |
| `T-03` | A delegated grant MUST resolve a validated actor, parent grant, grantor, grantee, project/lane, resource, action, risk, time, delegation permission, depth, proof, and closeout obligation. |
| `T-04` | A child grant MUST be no broader than the intersection of every active ancestor grant and MUST become ineffective when an ancestor expires or is revoked. |
| `T-05` | Coordination state MUST be checked before protected mutation, but coordination MUST NOT substitute for authorization. |
| `T-06` | Commit, promotion, and publication preflight MUST compare the exact changed paths and effects with the resolved authorization chain. |
| `T-07` | No document or registry change in M1 creates operative delegated authorization or a runtime trespass gate. |

## 7. Pseudo-Chat, BBS, and handoff requirements

| ID | Requirement |
| --- | --- |
| `P-01` | External intake packets, session coordination, BBS transport, worklog handoff, guest messages, and future duplex chat MUST have distinct component identities. |
| `P-02` | BBS transport and worklog posts MUST be treated as transport or handoff evidence, not canonical project or lane state. |
| `P-03` | A protected BBS-originated action MUST resolve the authenticated member, authorization, run, lane, and resulting durable closeout or state record. |
| `P-04` | An unauthenticated or guest message MAY enter review intake but MUST NOT authorize work or change state. |
| `P-05` | Future duplex interaction MUST remain labeled unimplemented until concurrent request/response behavior is runtime-proven. |

## 8. Freshness, evidence, and teaching requirements

| ID | Requirement |
| --- | --- |
| `F-01` | Every generated projection MUST identify its source set, generation time, freshness owner, and regeneration trigger. |
| `F-02` | A disagreement between canonical state and a projection MUST be reported as drift; the projection MUST NOT silently overwrite the canonical record. |
| `F-03` | Requirement compliance evidence MUST distinguish `planned`, `source_defined`, `runtime_observed`, reviewed, promoted, and published states. |
| `F-04` | Evidence cited as clone-verifiable MUST resolve to a tracked artifact. |
| `F-05` | Every later architecture, design, implementation, and publication decision MUST trace to one or more M1 requirement IDs or record an approved exception. |
| `F-06` | The project MUST preserve its real requirements, defects, corrections, test results, and exceptions as the LabTalk educational case. |
| `F-07` | A local AI operational page MUST derive its response from the current canonical source set at request time or from a bounded cache that is automatically invalidated when an input changes. Manual regeneration MUST NOT be the normal freshness mechanism. |
| `F-08` | A dynamic operational response MUST expose its source identity and observation time. If a source is unavailable or freshness cannot be established, the page MUST display a visible stale or error state rather than silently serving last-known content as current. |
| `F-09` | Static HTML MAY be produced as an explicitly dated export or reviewed publication artifact, but MUST NOT be presented as the normal local AI Portal view. The export remains a non-authoritative projection. |

## 9. M1 acceptance matrix

| Gate | Evidence required | State |
| --- | --- | --- |
| Discovery and needs assessment are complete | Empirical inventory covers `D:\code\ccode\docs`, `D:\code\ccode\tools`, `D:\code\ccode\dottalkpp\docs`, and `D:\code\ccode\dottalkpp\tools`; includes the Sidecar batch; and cross-walks findings under `R-01` through `R-11`. | owner-review candidate |
| Naming is unambiguous | `N-01` through `N-06` reviewed against the cross-walk. | candidate |
| Document classes are complete enough for M2 | Every report-like component maps to one primary class or an explicit open question. | candidate |
| Sensitivity fails closed | `S-01` through `S-09` reviewed against portal registry and generator behavior; implementation gaps remain labeled. | candidate |
| Ownership is preserved | Every requirement points to an owning lifecycle and none transfers incorporated ownership. | candidate |
| Authority is not inflated | Coordination, transport, generation, publication, and teaching surfaces remain non-authoritative unless their owning contract says otherwise. | candidate |
| Delegation is requirements-only | No runtime grant, resolver, permission, DBF, command, or enforcement claim is introduced. | candidate |
| Local operational projections are dynamic | `F-07` through `F-09` distinguish the live local view, bounded cache behavior, visible failure state, and static export role. The owner authorized an immediate visibility prototype to inform design and testing. | runtime-observed local prototype; final architecture pending |
| M2 is bounded | Architecture may select schemas and source-of-record mappings only after owner acceptance of this requirements set. | candidate |

## 10. M1 exclusions

Except for the explicitly authorized local visibility prototype, M1 does not:

- select or create the canonical component/edge registry;
- rename existing report files or navigation;
- change `portal.yaml`, report generators, stored report output, or website
  content; the prototype generates into a temporary directory per request and
  proxies the existing local website without changing it;
- modify identity, authorization, BBS, DBF, or socket behavior;
- create operative human-to-AI or AI-to-AI delegation;
- promote or publish any artifact.

The visibility prototype MAY read the existing canonical inputs and expose
their derived local view. It MUST remain read-only, local-only, visibly marked
as dynamic, and non-authoritative. Its observations feed M1 review and M2
architecture; its existence does not pre-approve the final server or cache
design.

## 11. M1 exit gate

M1 exits only when the owner confirms that:

1. the empirical discovery and needs-assessment cross-walk satisfies `R-01`
   through `R-11`;
2. the requirements contain no ownership transfer;
3. coordination, transport, projection, publication, and education have not
   been inflated into authority;
4. sensitivity and publication requirements fail closed;
5. trespass and delegation remain actor-neutral and safely attenuated;
6. the M2 architecture task is sufficiently bounded by requirement IDs.

Until that ruling, this document remains a candidate and AIF-086 remains in
M1 Requirements. The discovery assessment is available; owner review is now the
gate.
