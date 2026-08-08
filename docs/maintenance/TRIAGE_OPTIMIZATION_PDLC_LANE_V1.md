# Triage Program (Consolidation) -- PDLC Charter and Plan of Record

**Status:** `proposed` (charter drafted; awaiting AIF claim)
**Owner:** `member.derald` - **Steward/author:** `member.ai.claude.cowork`
**Intake:** AIF-NNN (claim pending -- maintainer runs `session_coordinator.py claim-aif`; do NOT reuse AIF-052)
**Parent project:** `project.ai_friendly.agent_memory` (the AI Frontal Memory Project)
**Serves:** the Frontal_Mem persistent-memory thesis (`labtalk/ai_portal/FRONTAL_MEM_POINTER_V1.md`,
`trigger.persistent_memory`).
**M0 seed (built this session):** `tools/memory/consolidate.py` (value function + hybrid
propose/confirm) and `tools/memory/promote.py` (attributed Lane 1 renderer), tested 17/17.

---

## 1. Lane identity and lifecycle placement

The triage program is the **consolidation engine** of the Frontal Memory Project: it decides
which of a session's short-term working memories are promoted to long-term store and which
decay. This is framed as an **optimization project** because, per the thesis, the quality of the
whole system reduces to the quality of this one decision, repeated -- "a perfect store with a
poor value function is a warehouse of trivia." Optimizing the value function IS the work.

Lifecycle: each milestone runs as a full **PDLC** (analyze -> design -> code -> test/debug ->
document -> maintain). Engine-bound milestones (durable write, decay/reinforce) are
maintainer/host handoffs; Python host-tool milestones are testable in-sandbox.

## 2. Rulings ledger (owner rulings binding on this lane)

| # | Ruling |
|---|---|
| R1 | **Human-side memory locus.** The model is stateless; long-term memory is the owner-controlled store (thesis SS1.5). The triage program promotes INTO that store; it never becomes the memory. |
| R2 | **Hybrid promotion.** Agent proposes, owner confirms; confirmations train the autonomous share (thesis 4.5). Nothing reaches durable store without passing the value gate. |
| R3 | **Normalize on collect.** Atomic / deduped / linked by default; costed rollups (grandfather) only when a full rebuild is too dear. |
| R4 | **Forgetting is a feature.** The goal is selective forgetting with reliable recall of what mattered, not total memory. Over-promotion is the graver sin in a small trusted store (thesis 4.4); the promote threshold is tuned to that asymmetry, not fixed. |
| R5 | **No wheel reinvention.** Consume the built M0 core (`consolidate.py`/`promote.py`); a named, verified gap is the only license for new machinery. |
| R6 | **Provenance is mandatory.** Every promoted memory is attributed (`current_member()`, AIF-075); never author 0. |
| R7 | **The gate runs on the work too.** AI agencies are team-member entities; the value gate also runs on an agent's own actions -- unreasoned deferral is demotion (thesis 4.6). |
| R8 | **Measure, do not assert.** The claim that retention cuts time-to-context and mistake rate must be instrumented before it is believed (thesis Section 7). |

## 3. Standing disciplines (enforced per phase)

1. Definition of done per phase: tests authored + run; recall wiring where a durable artifact is
   left; ASCII only, no em-dashes; closeout with `ai_report_audit` envelope; intake row updated;
   this lane doc updated.
2. Delivery: engine-bound work is a maintainer/host handoff with recorded command/exit/artifact
   evidence (sandbox cannot build or run the engine); host-tool work ships tested.
3. Attributed writes only (AIF-075); fresh AIF per engine-touching milestone.
4. Verification proportional to change class (host-tool: unit tests; engine write: datarun +
   oracle-style assertion).

## 4. Phase register (summary; each phase its own PDLC)

| Phase | One line | Gate |
|---|---|---|
| M0 | **DONE.** Value-function core: five signals (acted-on, costly-to-learn, re-referenced, contradiction, novelty), hybrid propose/confirm, normalize-on-collect, cost-asymmetry bias. `consolidate.py`/`promote.py`, 17/17 tests, reproduces the hand-triage. | **G0 CLOSED** (tests + hand-triage acceptance) |
| M1 | **Lane 1 write adapter** (engine-bound): attributed durable write via `current_member`/`post_new`; first-class post `kind` for the source-lane marker; confirm UX. **Assigned to Grok** (`GROK_PUSH_L1_WRITE_ADAPTER_V1.md`). | G1 (datarun: post exists, real author_id, source marker; on decline nothing written) |
| M2 | **Autonomous-share growth**: owner confirmations become a training signal; raise the autonomous promote fraction as measured agreement rises; owner still gates the high-stakes (thesis 4.5). | G2 (agreement rate measured; autonomous share moves only on evidence) |
| M3 | **Decay-and-reinforce** on the recall graph: node/edge strength decays with disuse, reinforces on recall; unused links fade (thesis 5.3 -- currently design-only). | G3 (strength updates observed; a stale link demoted; working sets trend toward used paths) |
| M4 | **Grandfather-father-son retention**: session -> weekly -> month/quarter rollups; atoms age out only once the coarser rollup that supersedes them exists; forgetting is demotion, not raw deletion. | G4 (rollup exists, atoms demoted + marked; no raw deletion) |
| M5 | **Instrumentation + evaluation**: measure time-to-context and mistake-rate before/after (thesis Section 7 "measure, not assert"). | G5 (baseline captured; delta reported) |

## 5. Open questions (placed where they block)

| Question | Blocks | Proposed default |
|---|---|---|
| OQ-1 value-function weighting (domain-specific, moving target) | M2 | start from the M0 static weights; tune against measured re-reference and owner-confirm agreement, never speculatively |
| OQ-2 confirm UX (interactive `PSEUDO PROMOTE ... CONFIRM` vs `board.governance`) | M1 | Grok chooses in the Lane 1 spec; governance route is auditable and reuses SYSGRANT |
| OQ-3 privacy / scope (some things must not be remembered; no cross-member/project leak) | M2 | promote only within the acting project; never cross the member/project boundary without owner confirm |
| OQ-4 drift / reconsolidation (scheduled sleep revisiting OLD memories) | M4 | a periodic reconsolidation pass adjacent to M4; revisit stale semantic memory, not just new |

## 6. Registration state

- `coordination/aif/AIF-NNN.claim` -- **pending**; maintainer claims a fresh AIF and applies with this charter.
- Intake row -- to add to `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` on claim.
- `labtalk/registries/projects.yaml` -- parent `project.ai_friendly.agent_memory` already registered (root `D:/code/ccode`).
- Recall wiring -- node `mechanism.triage_optimization`, reached via `trigger.persistent_memory`.

## 7. Provenance

Distilled from the Frontal_Mem thesis (SS1-8) and this session's build: the M0 value-function
core (`consolidate.py`, 9 tests), the Lane 1 renderer (`promote.py`, 8 tests, full
propose->confirm->render pipeline), the hand-triage acceptance loop (the tool reproduces the
closeout's by-hand decisions), and the coworker/lifecycle doctrine reinforced into the glossary.
Evidence tier at charter time: M0 is `runtime_observed` (tests pass in-sandbox); M1-M5 are
`source_defined` / `design`.
