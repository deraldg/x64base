# AI Systems Integration SDLC -- M2 component/edge model v1 (candidate)

Status: **M2 architecture candidate; owner acceptance gates M2 exit; no runtime schema or generator selected**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Run: `AIPR-20260805-001` (candidate; needs registration in `ai_runs.yaml`)
Owning lifecycle: **AI Systems Integration SDLC**
SDLC lane: `M2 Architecture`
Operating mode: `maintenance`
Change class: `C3`
Build target: `documentation_only`
Owner and final authority: `member.derald`
Steward and author: `member.ai.claude.cowork`
Depends on: M1 accepted 2026-08-05 (recorded in
`AI_SYSTEMS_INTEGRATION_STEWARD_ASSIGNMENT_AND_M1_CONTINUATION_2026-08-05_V1.md`)

## 1. Gate trace (R-11) and bound

M2 entry is authorized by the owner's M1 acceptance (2026-08-05). This is the M2
**required result**: a canonical component/edge model and a source-of-record
matrix (charter phase table). It satisfies the crosswalk's "M2 machine-graph
requirements" list (stable IDs, lifecycles, authority class + system-of-record
pointer, typed edges, supersession-without-deletion).

It does NOT: select or declare a canonical registry file, choose a schema, write
a generator or validator (all M3), change runtime, or dispose of anything. Nodes
and node attributes are carried by reference from
`AI_SYSTEMS_CROSSWALK_V1.md` so this model cannot silently diverge from the
accepted map. The new content here is the source-of-record matrix, the typed
edge set, and the added `ai.capability.egress` node.

## 2. Node set

23 nodes: the 22 crosswalk components (attributes -- stable ID, label, owning and
incorporating lifecycle, authority class, state -- authoritative in
`AI_SYSTEMS_CROSSWALK_V1.md`) plus `ai.capability.egress` (added by the
2026-08-05 discovery re-entry).

Node -> single canonical system of record (SoR). "not a SoR" means the node is a
projection/transport/coordination surface that MUST resolve to another node's
record (A-03, A-05).

| Stable ID | Canonical system of record | Authority class |
| --- | --- | --- |
| `ai.curation.friendly` | `docs/ai-friendly/AI_FRIENDLY_WORKFLOW_V1.md` | routing doctrine |
| `ai.portal.core` | `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md` | architecture/policy |
| `ai.state.tier0` | generated; derives-from registries + source | derived working state (not a SoR) |
| `ai.seed.tier1` | `labtalk/ai_portal/AI_TIER1_SEED_V1.md` | onboarding doctrine |
| `ai.graph.recall` | `labtalk/registries/portal_recall_graph.yaml` | retrieval index (not a content SoR) |
| `ai.work.aif_queue` | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | prospective record (drift-prone; not authoritative state) |
| `ai.work.aif_claims` | `coordination/aif/AIF-*.claim` | allocation record |
| `ai.coordination.sessions` | `tools/coordination/session_coordinator.py` state | coordination, not authorization |
| `ai.coordination.worktrees` | `docs/maintenance/AI_WORKTREE_LANE_ISOLATION_LANE_V1.md` | coordination design |
| `ai.provenance.runs` | `labtalk/registries/ai_runs.yaml` | durable run provenance |
| `ai.provenance.closeouts` | `docs/maintenance/SESSION_CLOSEOUT_*.md` | episodic governed record |
| `ai.evidence.proofs` | `labtalk/registries/proofs.yaml`, `labtalk/proofs/runs/` | evidence |
| `ai.intake.external` | `docs/maintenance/external_ai_intake/` | source material, not authority |
| `ai.audit.reports` | `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md` | compliance record |
| `ai.memory.external` | `docs/maintenance/EXTERNAL_AGENT_MEMORY_LANE_V1.md` | architecture proposal |
| `ai.transport.bbs` | `src/bbs/`, `src/cli/cmd_bbs.cpp` (+ `data/metadata/bbs/`) | transport, not authority |
| `ai.handoff.worklog` | `docs/ai-friendly/AI_BBS_WORKLOG_HANDOFF_LANE_V1.md` | convenience handoff |
| `ai.pattern.pseudo_chat` | none by design; resolves to decomposed components | pattern, never SoR |
| `ai.projection.operations` | none; derives-from provenance/evidence/claims | derived projection (not a SoR) |
| `ai.public.reports` | **OPEN**: no publication manifest yet (D2) | reviewed publication |
| `ai.public.website` | website source + publication contract | publication, not dev authority |
| `ai.education.labtalk` | LabTalk registries + curriculum | reviewed educational consumer |
| `ai.capability.egress` | `src/cli/cmd_net.cpp` (`host.network.egress`) | capability boundary, not authority |

## 3. Typed edge set

Edge types (directional): `incorporates`, `derives_from`, `projects`,
`transports`, `coordinates`, `audits`, `gates`, `teaches`, `supersedes`.

- `incorporates`: the AI Systems Integration SDLC incorporates every node above.
  Incorporation transfers no ownership (A-02).
- `derives_from`:
  - `ai.state.tier0` -> owned registries + source.
  - `ai.projection.operations` -> `ai.provenance.closeouts`, `ai.provenance.runs`,
    `ai.work.aif_claims`, `ai.evidence.proofs`.
  - `ai.graph.recall` -> `ai.seed.tier1` + doctrine seeds (index, not content SoR).
- `projects`:
  - `ai.public.website` projects reviewed `ai.public.reports` + educational cases.
  - `ai.projection.operations` projects current operational state (F-07/F-08:
    request-time or auto-invalidated cache; visible stale/error state).
- `transports`:
  - `ai.transport.bbs` transports `ai.handoff.worklog`, guest `ai.intake.external`,
    and `ai.pattern.pseudo_chat` exchanges. Transport is evidence, not state (P-02).
- `coordinates`:
  - `ai.coordination.sessions` and `ai.coordination.worktrees` coordinate actors
    and files; they never authorize (A-05).
- `audits`:
  - `ai.audit.reports` audits `ai.provenance.runs`, `ai.provenance.closeouts`,
    and `ai.intake.external`.
- `gates`:
  - `ai.capability.egress` gates outbound network use (for example model pulls);
    loopback stays open. OPEN/CLOSE require `host.network.egress` and resolve to
    the trespass/delegation chain (T-01..T-06). Relates to S-09.
- `teaches`:
  - `ai.education.labtalk` teaches from real `ai.provenance.*` and `ai.evidence.*`
    evidence (F-06). Teaching acquires no ownership (A-02).
- `supersedes`:
  - correction edges preserve the prior record and name the later ruling (A-06);
    for example the 2026-08-05 steward record supersedes the prior steward state.

## 4. Source-of-record findings (M2 exit-gate check)

M2 exit gate: every projection resolves to a canonical record and no duplicate
system of record exists. Findings:

- Every projection/transport/coordination node resolves to a canonical record or
  is explicitly "not a SoR" and points at one. PASS for 21 of 23 nodes.
- **Open item O-1**: `ai.public.reports` has no canonical record yet (a
  publication manifest). Tracks D2/D4; must be created before public separation
  (M6). Blocks a clean M2 exit only for the publication subgraph.
- **Open item O-2**: `ai.pattern.pseudo_chat` intentionally has no SoR; every
  Pseudo-Chat record MUST name the decomposed component that carried it (N-05,
  reconciliation obligation 6). This is a rule, not a gap.
- Carried identity debts, not resolved here: D8 (`AIF-064` dual meaning) and D9
  (fast-start 20-vs-19 field count). They remain blocked from silent adoption.

## 5. Requirement trace (F-05)

- Single owning lifecycle per node: A-01 (via crosswalk attributes).
- Projection names its canonical source, never a SoR: A-03, F-01, F-02.
- Coordination/transport/teaching are non-authoritative: A-02, A-05, P-02.
- Egress node ties to delegated authorization: T-01..T-06; and S-09.
- Document classes map onto nodes: D-01..D-05 (operational_projection vs
  audit_record vs public_report vs whitepaper vs educational_case).
- Supersession without deletion: A-06.

## 6. What M2 still needs for owner acceptance

1. Owner ruling on O-1 (create a `public_report` publication manifest as the SoR
   for `ai.public.reports`, or defer to M6 with the gap recorded).
2. Owner confirmation that the edge types and single-SoR assignments match intent.
3. Then M3 Design may select the machine-graph schema, generator, and validators
   (still separate; not proposed here).

This model selects no file as the canonical registry and writes to no runtime.
