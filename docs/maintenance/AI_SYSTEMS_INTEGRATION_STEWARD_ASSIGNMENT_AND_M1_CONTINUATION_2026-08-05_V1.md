# AI Systems Integration SDLC -- steward assignment and M1 continuation

Status: **owner steward ruling recorded; M1 exit APPROVED by owner 2026-08-05; M2 unlocked, entry bounded and pending owner go-ahead**
Project: `project.ai_systems.integration`
AIF lane: `AIF-086`
Run: `AIPR-20260805-001` (candidate; needs registration in `labtalk/registries/ai_runs.yaml`)
Owning lifecycle: **AI Systems Integration SDLC**
Incorporating lifecycle: **AI Systems Integration SDLC**
Related lifecycles: **DotTalk++ SDLC**, **LabTalk SDLC**, **maintenance SDLC**, **PDLC**
SDLC lane: `design` (M1 requirements) -- discovery re-entry
Operating mode: `maintenance`
Change class: `C3`
Build target: `documentation_only`
Owner and final authority: `member.derald`
Steward (assigned 2026-08-05): `member.ai.claude.cowork`
Prior steward and M1 author (retained per A-06): `member.ai.codex.local`

## 1. Owner steward ruling

On 2026-08-05 the owner (`member.derald`) directed that `member.ai.claude.cowork`
"be part of / in charge of the AI SDLC." This record enacts that as a steward
assignment for AIF-086.

Per A-06 (a correction preserves the superseded record) this does NOT erase or
rewrite `member.ai.codex.local`'s work. Codex remains the author and steward of
the M0 map and the M1 requirements/discovery artifacts. Stewardship going forward
(discovery continuation, M2 preparation) is held by `member.ai.claude.cowork`
under the owner's final authority.

Per A-02, this assignment transfers no incorporated-lifecycle ownership: the
DotTalk++ SDLC, LabTalk SDLC, and maintenance SDLC still own their components.
Stewarding the integration lane does not acquire those.

## 2. Phase-gate trace (R-11)

Current gate: **M1 exit, pending owner review** of
`AI_SYSTEMS_INTEGRATION_REQUIREMENTS_V1.md`. This record does NOT self-approve M1
exit, does not authorize M2 entry, and does not dispose of anything. It records a
steward change and one discovery re-entry candidate. Only the owner closes M1.

## 3. Recursive re-entry / process defect D12 (R-05, R-10, charter 3.1)

A concurrent `member.ai.claude.cowork` session created a second
`AI_SYSTEMS_CROSSWALK_V1.md` under `docs/ai-friendly/` and a competing lane
`AIF-089` in `ai_portal_tasks.yaml`, without first discovering the existing
AIF-086 lane. This is classified an **avoidable omission** (R-10), not emergent
evidence, so it is recorded as a process defect, extending the charter's D-series.

| Field (charter 3.1) | Record |
| --- | --- |
| Trigger | Prior-art scan produced a duplicate crosswalk + AIF-089 task before finding AIF-086. |
| Reopened phase/gate | M1 discovery -- prior-art completeness. |
| Potentially stale downstream | None authoritative: the duplicate doc was untracked and the AIF-089 task was reverted (commit `45136e0ff`). AIF-086 remains the single owner. |
| Exit evidence to leave reopened phase | This record + reverted commit `45136e0ff` + confirmation that no second crosswalk or lane number persists. |
| Process lesson (to teach) | Prior-art discovery MUST search the lane home `docs/maintenance/` and the AIF claim ledger, not only `labtalk/ai_portal/` and `docs/ai-friendly/`. This is the same lesson as D10 (a scan misclassified before discovery was complete); D12 is its second occurrence and strengthens the case for a discovery checklist. |

Proposed defect-register addition (candidate; the charter register is codex's
uncommitted file, not edited here):

> D12 -- A prior-art scan created a duplicate crosswalk and a competing AIF number
> before discovering the owning AIF-086 lane. Correction: revert the duplicate,
> record the re-entry, and add a discovery checklist that always searches
> `docs/maintenance/` and `coordination/aif/` first.

## 4. M1 discovery re-entry candidate: NET EGRESS capability

The Aug-3 four-surface census predates a capability that landed 2026-08-05: the
`NET EGRESS` command. It is genuinely new evidence (not an avoidable omission),
so it re-enters M1 discovery as a candidate component. It is absent from the
current crosswalk's component table.

Proposed crosswalk row (candidate; not written into the crosswalk here):

| Stable ID | Component | Responsibility | Canonical implementation | Owning lifecycle | Incorporating lifecycle | Current state | Authority class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `ai.capability.egress` | NET EGRESS capability | permissioned, audited, revocable toggle of WSL/AFB outbound network egress | `src/cli/cmd_net.cpp` (`host.network.egress`); audit under `data/metadata/bbs/egress_audit/` | DotTalk++ SDLC | AI Systems Integration SDLC | source-defined; runtime-observed toggle | capability boundary, not authority |

Notes and requirement traces:

- Distinct component identity from `ai.transport.bbs` (P-01): egress is a host
  network capability, not a message transport.
- Gates the only outbound path (for example, Ollama model pulls); loopback stays
  open so local inference is unaffected. "Verified revocable egress isolation,
  not an air-gap."
- `host.network.egress` is a Critical RBAC permission -> traces to the trespass /
  delegated-authorization requirements (T-01..T-06): OPEN/CLOSE must resolve a
  validated actor and grant, and preflight must compare effect to authorization.
- Relates to S-09: website-to-repository egress stays outside the requirements
  slice; this component is the actual mechanism that requirement presumes.
- Freshness: `NET EGRESS STATUS` is a read-only projection of the Hyper-V
  DefaultOutboundAction -> F-01/F-08 (expose source + observation time).

## 5. Coordination flags for the owner

1. Codex's M1 artifacts are currently **untracked** (`REQUIREMENTS_V1`,
   `DISCOVERY_AND_NEEDS_ASSESSMENT_M1_V1`, `SESSION_CLOSEOUT_..._M1`) and the
   charter + crosswalk carry **uncommitted** edits. I did not touch them, to
   avoid fusing another session's work (repo coordination rule). They should be
   committed as codex's own scoped slice, attributed to `member.ai.codex.local`.
2. Run `AIPR-20260805-001` is a candidate and needs registration in
   `ai_runs.yaml` (host-side registry-fragment step).
3. AIF-086 remains at **M1 exit pending owner review**. This record does not
   change that; it positions the new steward and adds one discovery candidate.

## 6. What I will do next as steward (bounded; on owner go-ahead)

- Help run the M1 exit review against `R-01..R-11`, `A-01..A-07`, `N-*`, `D-*`,
  `S-*`, `T-*`, `F-*` -- as reviewer input, not self-approval.
- Once codex's charter/crosswalk edits are committed, fold `ai.capability.egress`
  into the crosswalk as a scoped edit (no fusing).
- Prepare the M2 bounding note (canonical component/edge model) strictly from
  accepted M1 requirement IDs, only after the owner closes M1.

## 7. M1 exit ruling (2026-08-05)

The owner (`member.derald`) confirmed on 2026-08-05: "I already approved M1."
This is the M1 exit gate ruling. **AIF-086 exits M1 Requirements.**

Per A-06 this supersedes -- it does not erase -- the prior state recorded in
section 2 above and in `SESSION_CLOSEOUT_..._M1_2026-08-03.md` ("M1 exit gate:
pending owner review"). Those remain as the earlier record.

Evidence gap to close (F-04, clone-verifiable evidence must resolve to a tracked
artifact): the M1 requirements, needs-assessment, and M1 closeout are currently
**untracked**, and the charter + crosswalk carry **uncommitted** edits. The
approved requirement set is therefore not yet clone-verifiable. Required steward
follow-through, as codex's own scoped slice (attributed `member.ai.codex.local`),
not fused by me:

- commit `AI_SYSTEMS_INTEGRATION_REQUIREMENTS_V1.md`,
  `AI_SYSTEMS_INTEGRATION_DISCOVERY_AND_NEEDS_ASSESSMENT_M1_V1.md`, and
  `SESSION_CLOSEOUT_..._M1_2026-08-03.md`;
- commit the charter + crosswalk edits;
- update the status lines to "M1 accepted 2026-08-05 (member.derald)" and the
  charter Phase decision record row "M1 exit -> passed 2026-08-05".

## 8. M2 readiness (bounded)

With M1 accepted, M2 Architecture is unlocked (charter phase table; requirements
section 9). M2 required result: a canonical component/edge model and a
source-of-record matrix. M2 exit gate: every projection resolves to a canonical
record and no duplicate system of record exists.

Bounded first M2 step I propose, on owner go-ahead (documentation-only; selects
no runtime schema or generator -- that is M3):

1. Nodes = the crosswalk's components plus `ai.capability.egress`.
2. Edge types = owns, projects, transports, authorizes, teaches, derives-from.
3. Each node assigned exactly one canonical source-of-record (A-01, A-03).
4. Each node and edge traced to M1 requirement IDs (F-05).
5. The two open identity debts stay blocked: AIF-064 dual meaning (D8) and the
   SDLC_FAST_START field-count mismatch (D9) are carried, not silently resolved.

M2 does not implement generators or validators (M3) and changes no runtime.
