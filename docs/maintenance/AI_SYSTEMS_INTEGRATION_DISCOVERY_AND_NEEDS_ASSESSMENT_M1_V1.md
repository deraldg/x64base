# AI Systems Integration SDLC M1 Discovery and Needs Assessment v1

Status: **owner review candidate; discovery complete for the named four-surface census**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Run: `AIPR-20260803-004`
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycles: **DotTalk++ SDLC**, **LabTalk SDLC**, **maintenance SDLC**, and **PLDC**
SDLC lane: `design` (M1 requirements and needs assessment)
Truth state: empirical filesystem and Git census plus source-defined prior-art review
Proof state: report; no runtime behavior is newly claimed
Owner and final authority: `member.derald`
Steward: `member.ai.codex.local`
Measured root: `D:\code\ccode`
Measured branch and baseline: `development` at `6268c47f5b0b`
Measured date: 2026-08-03

## 1. Decision this assessment supports

Determine what AI Portal, AI Friendly, AI-BBS, Pseudo-Chat, onboarding,
identity, agency, memory, report, coordination, educational, and supporting
tooling work already exists or is in progress before AIF-086 selects an M2
architecture or performs more housekeeping.

This is a requirements and needs assessment. It is not a deletion list. An
orphan is a work item whose ownership, registration, traceability, integration,
or current authority is unclear. It is not synonymous with trash.

## 2. Why M1 re-entered discovery

The owner requested an empirical scan of these surfaces:

```text
D:\code\ccode\docs
D:\code\ccode\tools
D:\code\ccode\dottalkpp\docs
D:\code\ccode\dottalkpp\tools
```

The request was intended to discover prior art and requirements coverage. It
was misclassified as housekeeping, and a small reversible Sidecar intake began
before the inventory and cross-walk were produced. The governing defect is D10
in `AI_SYSTEMS_INTEGRATION_SDLC_CHARTER_V1.md`.

This assessment corrects the sequence. The existing Sidecar batch is included
as evidence. No additional file was moved, deleted, archived, restored,
generated, staged, promoted, or published during this discovery pass.

## 3. Classical discovery method

The pass used the standard non-mutating sequence that should have preceded the
Sidecar work:

1. Restate the need, lifecycle, owner, authority, mutation boundary, and exit
   evidence.
2. Census every file under the four named surfaces with hidden and ignored
   material visible.
3. Separate complete population counts from a focused prior-art content set so
   generated bulk remains measured but does not dominate interpretation.
4. Measure Git visibility: tracked, untracked, and ignored or other.
5. Review the AI Portal authority chain, registries, AIF queue, closeouts,
   contracts, reports, and relevant source-defined lane records.
6. Compare claimed canonical entry points with filesystem existence and Git
   tracking.
7. Scan script hashes and basename collisions as lineage signals, not automatic
   duplication verdicts.
8. Cross-walk findings to existing components and M1 requirements.
9. Propose classifications and owner decisions without taking disposition.

The focused filename filter used AI, AIF, agent, BBS, Pseudo-Chat, portal,
onboarding, memory, reports, authorization, delegation, trespass, worklog,
handoff, coordination, intake, and SDLC terms. Generated, archive, package,
backup, and run-evidence subtrees were counted in the census and excluded only
from the first focused filename list. Content and authority references were
then reviewed directly.

## 4. Four-surface census

| Surface | Files | Tracked | Untracked | Ignored or other | Structural observation |
| --- | ---: | ---: | ---: | ---: | --- |
| `docs` | 22,403 | 791 | 4,254 | 17,358 | Most volume is manualgen, messaging, and Data Dictionary evidence or generated material. |
| `tools` | 1,639 | 1,399 | 0 | 240 | The root tool tree is predominantly tracked; most residual files are caches. |
| `dottalkpp/docs` | 1,928 | 21 | 1,206 | 701 | 1,659 files are under `generated`; the curated and tool material is mostly local-only. |
| `dottalkpp/tools` | 46 | 4 | 30 | 12 | Four HELP tools are tracked, 30 are local-only, and 12 are Python caches. |
| **Total** | **26,016** | **2,215** | **5,490** | **18,311** | Repository visibility, authority, and generated state must be evaluated separately. |

The first focused filename pass found 168 non-generated/non-archive candidates.
The script estate contained 1,809 `.py`, `.ps1`, `.psm1`, `.bat`, `.cmd`, or
`.sh` files across the four surfaces. SHA-256 grouping found 177 exact-duplicate
groups and 181 basename-collision groups. Most sampled duplicates are deliberate
package, report, or backup snapshots. The counts are a lineage-review signal,
not permission to deduplicate.

Two concentrated local-only estates require explicit ownership:

- `dottalkpp/docs/tools`: 141 files, all 141 untracked;
- `dottalkpp/tools`: 46 files, 4 tracked, 30 untracked, 12 ignored caches.

## 5. AI report and AIF evidence census

The mandatory report audit measured:

```text
session closeouts:             90
grandfathered closeouts:        9
enforced closeouts:            81
valid enforced closeouts:      81
hard findings:                  0
external intake records:        2
external intake advisories:     3
ai_report_index entries:        3
```

The audit validator sees the report corpus and is green. The discoverability
index does not represent that corpus: three index rows cover 90 closeouts plus
external intake. Its header still describes a manual seed and a proposed
validator extension even though `audit_trail.py --emit-index` was delivered.
The 2026-07-28 closeout explicitly left full population optional. This confirms
charter defect D3 with current measurements.

Relevant audited closeouts include AI Portal architecture and reconciliation,
AI-BBS build and agency, onboarding, report audit and publication mode, identity
and session authentication, second-opinion authorization, external memory,
AIF-086 M0/M1, and the Sidecar correction. These are not one system today; they
are evidence inputs to the integration model.

## 6. Existing prior art cross-walk

The table classifies what already exists before proposing anything new.

| Prior art | Empirical state | What it already contributes | Integration need |
| --- | --- | --- | --- |
| Tier 1 seed, Tier 0, recall graph, and AIF-082 onboarding lane | Tracked; Tier 1 is the mandatory entry; AIF-082 measured and corrected the earlier entry path | Cold-start invariants, stopping test, trigger retrieval, measured onboarding cost | Make onboarding acceptance a named component, not only three implementation rows. |
| `AI_ASSIMILATION_BOOK_V1.md` | Tracked, retained Tier 2 doctrine, cited by `AI_PORTAL.md` for authority order | Authority doctrine and continuation guidance | Add to the integration map as doctrine; do not make it a front door. |
| `AI_ASSIMILATION_PORTAL_V1.md` and `AI_BABY_BOOTSTRAP_CARD.md` | Tracked, explicitly demoted from entry and retained by trigger | Historical onboarding lineage and valid depth-on-demand material | Cross-walk them as superseded entry surfaces, not active competing portals. |
| `AI_ROLES_TAXONOMY_V1.md` | Tracked, source-defined, proof record exists | Separates agent members, local Ollama service, and hosted GPTbase advisor | Add an actor-role component and bind it to identity, agency, memory, and trespass requirements. |
| `AGENCY_MODEL_V1.md` | Tracked, source-defined with explicit gaps | Four legs: identity, authority, authentication, accountability; distinguishes capability, access, influence, and agency | Use as foundational prior art for delegated authorization and audit, not a parallel vocabulary. |
| `ENTITY_LIFECYCLE_AND_THE_BRIDGE_V1.md` | Tracked, large design record with open items | Entity declaration, derived lifecycle state, promotion authority, build-up/build-down reconciliation | Use its span method and inert/unclassified caution for orphan discovery; do not duplicate the lifecycle vocabulary. |
| AIF-045 identity/RBAC and session-auth closeouts | Tracked closeouts; implementation described as in-engine proven | Member identity, owner grants, eligibility, expiry, revocation, authenticated sessions, acting principal | Add identity and authorization as explicit components in the cross-walk; separate implemented root grants from unimplemented delegation chains. |
| Second-opinion authorization boundary | Tracked audited closeout | Current task role controls scope; quoted prior instructions are evidence, not authority | Incorporate as the first concrete trespass/role-boundary case. |
| `AI_RUN_TRACEABILITY_LANE_V1.md` and `AI_RUN_TRACEABILITY_CONTRACT_V1.md` | Lane tracked; contract exists locally but is untracked | Owner/committer/author/planner/attestor separation; run and change provenance | Resolve the local-only contract before claiming clone-verifiable traceability. |
| AI report audit v1 and v2 spec | v1 mandatory and green; v2 tracked candidate and explicitly rejected by current v1 validator | Report identity, scope, project, Git provenance; proposed richer authorship model | Decide whether v2 is adopted, revised, or superseded; do not describe it as live. |
| `AI_EVIDENCE_LAYER_VERSIONING_LANE_V1.md` | Tracked and marked fixed for its original proof gap | Versioned evidence and registry-citation validation | Apply its clone-verifiability rule to canonical tools and AIF-086 artifacts. |
| `EXTERNAL_AGENT_MEMORY_LANE_V1.md` | Tracked, design-intended | Working, episodic, prospective, semantic, procedural, and evidence memory; event-sourced continuity | Extend existing closeouts, intake, proofs, and Pseudo-Chat rather than create a parallel store. |
| Pseudo-Chat return lane, AIF-076 boundary note, and M7 milestone | Tracked | Durable packet return, umbrella-term decomposition, loopback reachability and authentication boundary | Keep packet handoff, BBS transport, worklog, and future duplex distinct. M7 is not an authenticated payload exchange. |
| AI-BBS AIF-052/054/055/057/075/083 | Tracked lane/runbook/closeouts and source claims; runtime evidence exists for several milestones | Board store, daemon, token auth, guestbook, worklog, attribution, RBAC, local transport | Reconcile stale outstanding lists and source gaps: CLI chokepoint, CLOSE attribution, REPLY board permission, read scaling, body capacity, per-session identity. |
| Git Hot Potato, session coordinator, and worktree isolation | Design note plus active tracked coordinator and design-intended worktree lane | Advisory coordination, atomic AIF allocation, shared-index protection, physical isolation design | Model coordination as non-authoritative and select one current path per function. |
| Operational report generators and portal report registry | Four tracked tools and five tracked HTML outputs | Local AI Portal, BBS, access, rulings, and dev-status projections | Move operational views under AI Operations; retain Reports for reviewed public-interest work; adopt fail-closed allow-list publication. |
| DOCSCAN documentation toolchain | 141 local-only scripts; local manifest and version file claim several tools are runtime-proven | Existing file census, authority classification, script subdivision, conflict and disposition proposals | Reconcile rather than rebuild. Its `C:\dottalkpp` staging model is superseded, and none of its claimed toolchain is tracked. |
| HELP/CMDHELPCHK canonical tool lineage | Tracked contracts and SelfDoc registries point at mixed tracked/untracked implementations | Canonical scanner, metadata bridge, chore harvest, message exporter, source-comment escrow | Clone-verifiability is broken for four of five sampled canonical entry points. This is a high-priority integration defect, not cleanup. |
| Top-level maintenance text fragments | Ten of eleven top-level `.txt` files are untracked; most have no other filename reference | Origin prompts, operating snippets, JIT teaching thesis, security/onboarding fragments | Route through governed intake and attribution. Do not leave them as accidental authority or discard them without review. |
| Sidecar `SCAR-20260803-001` | 11 recoverable files with hashes and original paths | Mixed scratch, security proof, documentation-tool, runtime-test, educational, launcher, snapshot, and backup material | Keep in the discovery evidence set. Several entries require lane review before any aging disposition. |

## 7. Canonical-but-local-only defects

Current contracts or registries name these entry points as canonical or active,
but Git does not track them:

| Path | Exists locally | Tracked | Authority references observed |
| --- | --- | --- | ---: |
| `dottalkpp/tools/help/cmdhelpchk_v2_scan.py` | yes | no | 9 |
| `dottalkpp/tools/help/cmdhelpchk_v2_metadata_bridge.py` | yes | no | 1 |
| `dottalkpp/tools/help/cmdhelpchk_v2_chore_harvest.py` | yes | no | 1 |
| `dottalkpp/docs/tools/source_comment_escrow_v2_2.ps1` | yes | no | 2 |
| `dottalkpp/tools/help/generate_runtime_message_catalog_seed_v1.py` | yes | yes | 4 |

The tracked compatibility launcher
`tools/help/cmdhelpchk_v2_scan.py` delegates to the first untracked path. A
clone therefore receives a launcher whose canonical implementation is absent.
The active canonical-path contract also directs future edits to that missing
clone path.

This repeats the exact AIF-062 evidence failure one layer lower: a registry or
contract points at something present only on this machine. The claim is locally
true and repository-false.

The local `dottalkpp/docs/doc_versions.json` also marks eight documentation
tools `runtime-proven`; all eight exist and all eight are untracked. The local
tool manifest still calls `C:\dottalkpp` the clean staging area, which conflicts
with the active repository-role contract naming `C:\x64base` as publication
staging. The toolchain is valuable prior art with stale governance and no clone
delivery, not a folder to move wholesale.

## 8. Cross-walk additions for owner review

These are candidate component identities. They are not canonical until owner
review and M2 schema selection.

| Candidate ID | Component | Why the M0 cross-walk needs it |
| --- | --- | --- |
| `ai.doctrine.assimilation` | AI Assimilation Book | Load-bearing Tier 2 authority doctrine is not represented by the current Tier 1 row. |
| `ai.onboarding.acceptance` | Onboarding cost and acceptance | Tier artifacts exist, but the measured acceptance lifecycle and owner are not a component. |
| `ai.actor.roles` | AI roles taxonomy | Advisor, local model, and acting agent boundaries are otherwise implicit. |
| `ai.agency.model` | Agency model | Identity, authority, authentication, and accountability supply the vocabulary used by BBS and trespass work. |
| `ai.entity.lifecycle` | Entity lifecycle and bridge | Discovery, proof promotion, inert work, and declared-vs-derived state are integration dependencies. |
| `ai.security.identity` | DotTalk++ identity and session authorization | The runtime authority root for actors and grants is absent from the M0 component table. |
| `ai.security.scope_boundary` | Review/development and trespass boundary | The second-opinion incident is the existing concrete scope-crossing case. |
| `ai.traceability.contract` | AI run and change attribution | The run registry row alone does not represent the contract, contribution roles, or local-only gap. |
| `ai.evidence.versioning` | Clone-verifiable evidence | It supplies the exact rule needed for canonical-but-untracked work. |
| `ai.coordination.gitlock` | Git index coordination lineage | Distinguishes the historical advisory design from session coordination and future worktree isolation. |
| `ai.tooling.docscan` | Documentation discovery and authority scanner family | Existing prior art can inform an integration inventory generator after governance and tracking repair. |

## 9. Main integration defects after discovery

| ID | Defect | Impact | Needed correction |
| --- | --- | --- | --- |
| `M1D-01` | Canonical HELP/SelfDoc tool paths are untracked. | A clone cannot execute the tracked launcher or reproduce declared canonical behavior. | Separate exact-path lane: establish lineage, test representative tools, then track, supersede, or correct the authority pointers. |
| `M1D-02` | The local DOCSCAN toolchain claims runtime proof while all 141 `dottalkpp/docs/tools` files are untracked and governance names obsolete staging. | Valuable discovery machinery is both invisible to clones and unsafe to adopt literally. | Curate the small proven spine, update repository roles, and preserve the remaining family as historical/candidate evidence pending review. |
| `M1D-03` | The report audit sees 90 closeouts while the report index exposes three entries. | Auditability exists without usable discovery. | Generate a complete projection or redefine the index as curated external intake only; do not claim both. |
| `M1D-04` | The M0 cross-walk omits mature actor, agency, identity, lifecycle, onboarding-acceptance, evidence-versioning, and tool-lineage prior art. | M2 could invent parallel terms or architecture over existing systems. | Review and adopt the candidate additions before schema design. |
| `M1D-05` | Pseudo-Chat is used for packet handoff, BBS transport, worklog, governance dialogue, and unbuilt duplex chat. | Milestones can sound more complete than the evidence. | Require component identity on every record and reserve `duplex_chat` for concurrent authenticated exchange proof. |
| `M1D-06` | Portal `Reports` still means internal operational HTML; public generation excludes `private` but does not require explicit `public`. | Naming conflicts with the academic public Reports goal, and `internal` can be emitted in public mode. | Move local views under AI Operations and enforce an artifact allow-list plus sensitivity review. |
| `M1D-07` | Agency, identity, proof-promotion, second-opinion, and trespass records use overlapping but disconnected authorization language. | Delegation design could duplicate existing grant machinery or fail to distinguish fact promotion from prose. | Build one source-of-record matrix over AIF-045, AIF-050, AIF-060, the entity bridge, second-opinion incident, and the trespass candidate. |
| `M1D-08` | Raw top-level notes preserve owner directions and teaching ideas without intake identity, owner, status, or supersession. | Useful needs and constraints can be lost, while stale snippets can be mistaken for current instruction. | Classify through an intake ledger; distill durable rules and retain origin evidence with attribution. |
| `M1D-09` | The Sidecar batch mixes genuine disposable material with security, tooling, education, and runtime-test prior art. | Aging alone could destroy useful evidence or hide unmet integration work. | Maintain the hold and review per item against the owning lane before any aging decision. |
| `M1D-10` | AIF-086's intake-queue row described the pre-reentry next gate after this assessment and the visibility prototype changed the measured state. | The queue projection was stale even though the closeout and canonical artifacts were current. | Correct the queue in the M1 closeout slice, preserving the earlier projection in Git history rather than silently rewriting the event. |
| `M1D-11` | Classical scope-calibration and prior-art rules already existed but were not applied proactively at M1 entry or scan intake. | The process failure was avoidable with available repository access. | Enforce `R-08` through `R-11` and make original-outcome traceability a phase-transition check. |
| `M1D-12` | `build_reports.py` writes static HTML and the Portal registry tells operators to regenerate it manually. The local browser displayed a July 28 page with 15 lanes while the repository held a July 31 page with 16; neither included AIF-086. | The surface that appears current can disagree with both canonical registries and another generated copy. | Make the normal local AI Operations surface dynamic under `F-07` through `F-09`; retain static HTML only as a dated export or reviewed publication. |

## 10. Sidecar batch reclassification for review

No status below authorizes restoration or deletion.

| Intake item | Discovery classification | Owning review needed | Candidate disposition after review |
| --- | --- | --- | --- |
| `docs/! echo owner-can-shell.dts` | AIF-045 host-shell grant/revoke regression fragment | Identity and proof registry | Restore into a governed proof lane or retain as origin evidence. No auto-delete. |
| `docs/cmake_presets.txt` | One-line build invocation | Build documentation | Distill only if it names a still-supported preset; otherwise historical scratch. |
| `docs/encapsulation.txt` | Working invocation for the tracked source-object scanner | Source-object location lane | Incorporate into scanner usage documentation or retain as scratch evidence. |
| `tools/Mermaid.txt` | Rendering recipe whose named inputs are absent | Diagram/tooling lane | Historical candidate unless inputs or a successor resolve. |
| `docs/dottalk_case_review_v1_reports.zip` | Snapshot package with seven case-review outputs | Case library and report provenance | Compare hashes and lineage with current case reports before archival classification. |
| `dottalkpp/docs/code_generation.txt` | Entry recipe into the local DOCSCAN toolchain; one named initializer is missing | Documentation toolchain | Keep with `M1D-02`; do not age independently from the tool family. |
| `dottalkpp/docs/cs101.txt` | Generic AI-generated CS 101 index with no source or curriculum mapping | LabTalk curriculum | Educational intake review; likely source material rather than canonical lesson. |
| `dottalkpp/docs/date_implementation_dev.txt` | Substantial MCC/date/string/runtime shakedown stored with the wrong extension | MCC/date/runtime proof lanes | Evaluate as a DotScript regression candidate and recover only with a proof wrapper. |
| `dottalkpp/docs/start_iss.ps1` | One-line local website launcher pointer | Website/local tooling | Compare with current launchers and retain as historical if superseded. |
| `dottalkpp/docs/tools/catalog_reader_adapter_dbarea_api_resolution_v1.ps1` | Empty predecessor beside a non-empty `_v1_1` sibling | Documentation tool lineage | Deletion candidate only after the sibling and references are proven. |
| `src/core/dbf_create.cpp.bak` | Ignored source backup | Source lane | Disposable candidate after confirming the active source and Git contain every needed change. |

## 11. Needs derived from the discovery

The integration project needs these capabilities before M2 architecture can be
considered adequately bounded:

1. **Complete artifact identity.** Every incorporated component resolves an
   owner, lifecycle, canonical source, evidence state, sensitivity, freshness
   owner, and clone-visible path or explicit local-only state.
2. **Prior-art coverage.** Discovery compares proposed architecture with AIF,
   closeouts, contracts, registries, runtime source, tool manifests, and
   preserved intake before a new component or vocabulary is accepted.
3. **Source-of-record matrix.** Identity/RBAC, grants, contribution attribution,
   proof promotion, coordination, BBS transport, and publication authority have
   one relationship map without ownership transfer.
4. **Generated discoverability.** Report and component indexes expose measured
   coverage, generation time, inputs, and omissions.
5. **Fail-closed publication.** Internal operational views remain local unless
   an exact artifact revision is reviewed and allowed.
6. **Tool lineage and delivery.** A canonical tool cannot be declared complete
   when its implementation is untracked or its wrapper fails in a clone.
7. **Governed orphan intake.** Unknown work receives discovery fields and owner
   review before Sidecar, archive, restoration, or deletion candidacy.
8. **Traceable recursive re-entry.** New evidence may reopen phases, while
   avoidable omissions remain named process defects and trigger revalidation.
9. **Educational congruence.** The D10 failure and correction become the worked
   case for why needs assessment precedes solution refinement.
10. **Dynamic local operations.** Local AI operational pages read current
    canonical state per request or through an automatically invalidated bounded
    cache, expose observation time, and fail visibly when freshness is unknown.

## 12. M1 requirement coverage

| Requirement | Discovery evidence | State |
| --- | --- | --- |
| `R-01` | Four-surface census resumed read-only after D10. | satisfied for correction pass |
| `R-02` | Prior-art and Sidecar tables record purpose, maturity, owner/lifecycle, authority, evidence, and integration need. | candidate for owner review |
| `R-03` | Existing prior art and defects are cross-walked to implemented, partial, missing, conflicting, superseded, and unknown states. | candidate for owner review |
| `R-04` | Unknown work is separated from disposable work; no disposition is authorized. | satisfied |
| `R-05` | Charter and M1 closeout record trigger, reopened gate, stale artifacts, exit evidence, and lesson. | satisfied |
| `R-06` | Sidecar is treated as preservation only and remains part of discovery. | satisfied |
| `R-07` | Further Sidecar disposition is paused. | satisfied |
| `R-08` | Recursion is explicitly recovery, not an excuse for a weak first pass. | satisfied |
| `R-09` | Classical non-mutating discovery steps were executed without requiring the owner to enumerate them. | satisfied for correction pass |
| `R-10` | D10 is classified as avoidable omission, not emergent evidence. | satisfied |
| `R-11` | The output is traced back to the original AIF-086 integration and cross-walk objective. | satisfied |

## 13. Owner review gate

M1 should not advance until the owner rules on these questions:

1. Does this census cover the intended discovery surfaces and distinguish
   prior art from housekeeping correctly?
2. Should the candidate component additions in section 8 enter the maintained
   cross-walk?
3. Should the canonical-but-untracked HELP/SelfDoc tools be handled as the
   first corrective implementation lane before M2?
4. Should `ai_report_index.yaml` become a complete generated catalog, or remain
   a curated external-intake index with a more accurate name and contract?
5. Does the Sidecar item assessment preserve the right work for lane review?
6. Is the public posture still default-local for AI operational material, with
   public **Reports** reserved for reviewed academic/public-interest work?

The owner has separately ruled that local operational pages must be dynamic.
That requirement is recorded in `F-07` through `F-09`; M2 still must select the
architecture, cache boundary, source adapter, and failure behavior.

Until those rulings, no further Sidecar curation, tool-family movement,
cross-walk promotion, report publication, runtime change, or M2 architecture is
claimed.
