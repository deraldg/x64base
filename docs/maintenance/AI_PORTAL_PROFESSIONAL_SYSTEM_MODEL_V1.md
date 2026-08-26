# AI Portal Professional System Model V1 (AIF-132)

Status: source-backed architecture baseline; development tree only.

Owner: `member.derald`

Steward: `member.ai.codex`

## 1. Purpose and boundary

The AI Portal is the governed routing, coordination, evidence, and reporting
surface for AI-assisted work. It is not a second copy of the DotTalk++ runtime,
HELP database, metadata catalog, accepted manual, or public website.

This model normalizes the ad hoc identifiers and names already in use, lists the
schemas that participate in the Portal, and defines the seams between source
authority, governance state, derived reports, and publication projections.

Authoritative diagrams:

- PFD: `labtalk/diagrams/ai_portal_professional_pfd_v1.mmd`
- schema DFD/crosswalk: `labtalk/diagrams/ai_portal_schema_crosswalk_dfd_v1.mmd`
- feed contract: `docs/contracts/DOTTALK_PORTAL_FEED_CONTRACT_V1.md`
- feed/status inventory: `labtalk/registries/portal_feeds.yaml` and
  `labtalk/reports/portal/portal_feed_status_latest.md`

## 2. Normalized hierarchy and identifier model

These identifiers occupy different dimensions. They must be related by fields,
not collapsed into one overloaded `ticket` string.

| Level | Canonical identity | Meaning | Parent/link |
| --- | --- | --- | --- |
| Project | `project.<domain>.<name>` | Durable program with its own lifecycle | root; registered in `projects.yaml` |
| AIF lane | `AIF-NNN` | Governed work track or intake promoted into a lane | `project_id`; atomic claim file owns the number |
| Lifecycle | `PDLC` or `SDLC` | Method and scale applied to the work | orthogonal classification on project/lane |
| Milestone/gate | lane-defined `M<n>` or named gate | Evidence checkpoint inside a lane | `lane_id` |
| Ruling | global `R<n>` | Doctrine or an owner decision | `lane_id`; one flat global sequence |
| Run | `<provider>-YYYYMMDD-NNN` | One bounded execution/session | many-to-many with lanes through `SYSRUNLANE` |
| Work item | `task.<domain>...` or another namespaced key | Operational unit that can be assigned and closed | `lane_id`, optional project and run |
| Proof | `proof.<domain>...` | Evidence record with truth/proof state | `lane_id`, source, observed time |
| Report | `AIPR-YYYYMMDD-NNN` | Durable AI-authored closeout/report identity | run, project, baseline, authorization |

### Vocabulary rulings

- `AIF-NNN` is the canonical lane/intake identity, not a generic ticket number.
- `R<n>` is a globally allocated doctrine/ruling identity. It is never restarted
  within an AIF lane. Doctrine and lane rulings share the same number space; the
  `kind` field distinguishes them.
- `ticket` is a presentation alias for an external or legacy work-item reference.
  New internal records use `work_item_id` or `task_id`. If a legacy task carries
  `ticket: AIF-048`, that value is a cross-reference to the owning lane, not the
  identity of the task row.
- PDLC means Programming Development Life Cycle and covers a program/feature and
  the deliverable that exposes it. SDLC governs a subsystem or system. PDLC work
  may nest inside an SDLC; neither acronym is an identifier allocator.
- The retired PLDC acronym is not a third lifecycle. Its scope was merged into
  PDLC by the maintained lifecycle doctrine.
- New documentation-push state uses named processes such as
  `development_closeout` and `publication_ascent`. Phase numbers remain historical
  aliases, not the primary state machine.

## 3. Process flow (PFD)

The professional flow is:

1. Classify the request and identify the project.
2. Reuse or atomically allocate an AIF lane.
3. Select the smallest sufficient PDLC/SDLC mode and change class.
4. Record owner, steward, run, work item, and authority chain.
5. Implement only in the authoritative development tree.
6. Capture typed proofs and owner rulings; R numbers come from the global
   allocator.
7. Close the development slice with a report-audit envelope and Session Log row.
8. Derive Portal status and reports from maintained stores.
9. Stop at `development_closeout` unless publication ascent is separately
   authorized.

The PFD makes review and publication explicit decision points. A green source or
documentation gate does not imply promotion, deployment, or public availability.

## 4. Schema catalog

### 4.1 Runtime DBF schemas registered with Portal CRUD

The live registry is `tools/dbf/schema_registry.py`. C++ schema headers and
reviewed `.dtschema` files are the upstream definitions; drift tests reparse
those authorities.

| Domain | Tables | Authority | Mutation posture |
| --- | --- | --- | --- |
| Identity/RBAC | `SYSUSER`, `SYSMEMBER`, `SYSROLE`, `SYSPERM`, `SYSROLEPERM`, `SYSMEMROLE`, `SYSOVERRIDE`, `SYSASSIGN`, `SYSGRANT` | `include/identity/identity_schema.hpp` | governed CRUD; crosswalk and close policies vary |
| BBS/Pseudo-Chat | `SYSBOARD`, `SYSTHREAD`, `SYSPOST` | `include/bbs/bbs_schema.hpp` | read-only through generic Portal CRUD; daemon owns writes |
| Rulings | `SYSRULING` | `include/portal/ruling_schema.hpp` | append-only decision state |
| Portal tracking | `SYSLANE`, `SYSRUN`, `SYSRUNLANE`, `SYSPROOF`, `SYSTASK` | `include/portal/tracking_schema.hpp` | governed CRUD; runs are append-only |
| SelfDoc catalog | `SYSCMD` | `dottalkpp/data/schemas/metadata/syscmd_catalog.dtschema` | read-only projection owned by metadata pipeline |

That is 19 registered table schemas: 9 identity, 3 BBS, 6 Portal, and 1
SelfDoc catalog. Registration does not by itself assert that every table is
seeded, current, or the sole active authority; runtime status must be measured.

### 4.2 Typed YAML/JSON schemas

| Schema id | Store | Purpose |
| --- | --- | --- |
| `ai-report-audit-v1` | closeout front matter; `ai_report_audit.yaml` policy | report identity, agent, run, project, baseline, authorization |
| `ai-report-index-v1` | `ai_report_index.yaml` | generated report discovery index |
| `ai-runs-v1` | `runs.d/*.yaml` -> `ai_runs.yaml` | attributed run records and lane links |
| `labtalk.ai_portal.tasks.v1` | `ai_portal_tasks.yaml` | operational work-item projection |
| `portal-recall-graph-v1` | `portal_recall_graph.yaml` | trigger/node/edge retrieval graph |
| `dottalk.portal.feed.v1` | `portal_feeds.yaml` | authority-to-consumer feed seam |
| `dottalk.portal.assertions.v1` | `portal_assertions.yaml` | typed evidence-anchored routing assertions |
| `dottalk.fullstack.current.v1` | `current_fullstack_doc_push.yaml` | maintained current documentation-run pointer |
| `dottalk.portal.status.v1` | generated Portal status JSON | combined feed/assertion/current-run projection |
| `labtalk-database-ecology-v1` | `database_ecology.yaml` | database artifact classification and custody |

`projects.yaml`, `proofs.yaml`, `portal.yaml`, and the AIF/R Markdown registers
remain important maintained stores even where they do not declare a formal
top-level schema id. Professional hardening should add explicit schemas or
validated contracts without silently changing their current authority.

### 4.3 Documentation and publication schemas

| Store | Record type | Authority rule |
| --- | --- | --- |
| AIF intake queue | lane/intake row | canonical human-readable AIF register |
| AIF claim files | atomic number claim | allocator ledger, not descriptive state |
| R register | doctrine/ruling row | global R allocator of record |
| lane documents | objective, milestones, gates, rulings | argument and lifecycle context |
| closeouts | audited session report | durable execution record |
| dashboard Session Log | derived/readable closeout index | visibility surface, not source behavior |
| HELP DBFs | topics, sections, lines, arguments, provenance | documentation database authority |
| metadata DBFs | command/function/source catalogs | metacollect/self-documentation authority |
| accepted manual | manifest plus reader artifact | reviewed development manual authority |
| website JSON/MDX | public projection | publication consumer, never upstream authority |

## 5. DFD and seam crosswalk

| Producer/source authority | Contracted seam | Portal store/view | Downstream consumer | Direction |
| --- | --- | --- | --- | --- |
| Source usage contracts | HELP/metadata pipelines | HELP and metadata DBFs | manualgen, audit, Portal reports | source -> derived |
| HELP DBFs | `feed.dottalk.help_store` | feed registry/status | manual and Portal readers | source -> Portal |
| metacollect + metadata DBFs | `feed.dottalk.metadata_metacollect` | feed registry/status | comparison/audit tools | source -> Portal |
| accepted manual manifest/artifact | `feed.dottalk.manual_accepted` | feed registry/status | publication ascent | source -> Portal -> publish |
| AIF queue + claim files | lane identity crosswalk | `SYSLANE` / task projection | dashboard and reports | governance -> derived |
| run fragments + report envelopes | run/report crosswalk | `SYSRUN`, `SYSRUNLANE` / report index | attribution and closeouts | governance -> derived |
| R register/ruling sheets | global ruling identity | `SYSRULING` / rulings report | gates and readers | governance -> derived |
| proofs registry | proof identity | `SYSPROOF` / proof reports | gates, dashboard, publication review | evidence -> derived |
| current-run pointer + assertions | typed validation | generated Portal feed status | local Portal | state -> derived |
| Portal current-work projection | publication boundary | website JSON/MDX | x64base.com readers | Portal -> public projection |

No arrow points from the website, dashboard, or generated report back into source
authority. Corrections travel to the owning source/registry and the view is then
regenerated.

## 6. Hardening controls

1. Require typed identifiers and explicit foreign-key fields; do not infer a
   relationship because two prose fields happen to contain the same token.
2. Allocate AIF and R identities only through their allocators and collision
   gates.
3. Separate current state from history. Use append-only transitions for runs and
   rulings where the schema declares them.
4. Put perishable state behind measurement timestamps and expiry.
5. Keep `table = state, Markdown = argument`: machine-answerable status belongs
   in a typed store; rationale belongs in a cited lane/ruling/closeout.
6. Generate reports and public projections. Do not hand-edit derived outputs.
7. Preserve evidence state, platform, retention, sensitivity, and publication
   boundary on every feed.
8. Treat development closeout and publication ascent as separate authorization
   domains.
9. Validate crosswalk completeness: every active lane should resolve to a
   project, claim, run or explicit no-run state, work item where applicable,
   proof/next gate, and closeout when closed.
10. Keep Claude-owned `appgui`, multi-workplaces, and `minidb` outside this AIF-132
    documentation slice.

## 7. Current findings and normalization backlog

- The public/current-work projection still uses the field name `ticket` for a
  mixture of AIF lanes and other work references. Keep it for compatibility,
  but generate it from a typed `lane_id` or `external_ticket_id` field.
- `ai_portal_tasks.yaml` contains perishable counts and an older documentation
  run. The maintained current-run pointer now supplies the current routing fact;
  the task registry should eventually consume it rather than duplicate it.
- `SYSTEM_SCHEMA_MAP_AND_NORMALIZATION_V1.md` is valuable prior art but contains
  2026-08-04 status claims that have since changed. This model supersedes it for
  current topology while preserving it as the historical discovery record.
- The DBF registry includes schemas with different owners and mutation policies.
  A single generic "database" label is insufficient; every access path must use
  the registered per-table policy.
- The D:\dev website projection was inspected read-only. Its
  `public/artifacts/current-work-v1.json` still exposes `ticket` and names the AI
  Portal intake/lane/proof records as its system of record. No website file was
  changed and no publication state was inferred from its presence on disk.

## 8. Acceptance test for the professional model

For any displayed item, the Portal should answer these questions without a
full-tree prose search:

1. Which project and AIF lane own it?
2. Is it PDLC, SDLC, or a nested combination?
3. Which run and member performed the work under whose authorization?
4. Which globally identified rulings govern it?
5. What work item, proof state, current gate, and next gate apply?
6. Which store is authoritative and which views are derived?
7. Is the claim development-only, staged, deployed, or publicly verified?

If any answer is missing, the record is incomplete; if two stores answer it
differently, the seam is not normalized.
