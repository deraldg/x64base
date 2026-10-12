# AIF-136 -- AI Portal Memory Tiering and Retention Plan V1

Status: IMPLEMENTATION COMPLETE IN DEVELOPMENT; owner review-needed. M1-M6 are
durable and verified for AIF-136 scope. No bulk reclaim or publication is
authorized.

Owner: `member.derald`

Steward: `member.ai.codex`

Run: `CODEX-20260826-014`

Parent project: `project.ai_friendly.agent_memory`

Claim: `coordination/aif/AIF-136.claim`

## 1. Purpose

Keep AI onboarding small, current, and dependable while preserving older or
heavier knowledge in an owner-controlled long-term store that can be recalled
when needed.

The Portal is frontal memory. It selects, summarizes, and routes. It is not a
warehouse and does not become a second copy of source, HELP, metadata, proof,
manual, database, or archive authority.

This plan governs two different operations:

1. cognitive tiering -- what enters an AI's bounded working context; and
2. physical retention -- where bytes live and when they may be reclaimed.

Cognitive demotion does not authorize a file move. A file move does not
authorize deletion. Deletion always requires a separate owner-approved action
with a verified recovery or reconstruction path.

## 2. Relationship to existing lanes

| Lane or artifact | Relationship to AIF-136 |
| --- | --- |
| AIF-073 | Supplies the external-agent memory-class architecture. |
| AIF-098 | Owns the held Frontal_Mem Lane 1 write-adapter implementation, not this retention lifecycle. |
| AIF-112 | Owns document control and check-in/check-out. AIF-136 consumes its inventory and custody concepts but does not replace it. |
| AIF-132 | Supplies Portal feed, authority, lineage, sensitivity, and publication-boundary fields. |
| AIF-163 | Owns memo-sidecar orphan reclamation. It does not authorize AIF-136 LMDB reconstruction or reclaim work, and the two physical-storage populations must remain separate. |
| `TRIAGE_OPTIMIZATION_PDLC_LANE_V1.md` | Supplies the value function and human-confirmed promotion model. AIF-136 applies it to document and storage lifecycle. |
| `SYNAPSE_CONCEPT_V1.md` | Supplies the rule that durable knowledge must be reachable by intent, not merely filed. |
| `LMDB_MAPSIZE_OVERRIDE_LANE_V1.md` | Supplies the source-backed rule that LMDB environments are derived and rebuildable; physical reclamation remains separately approved. |

## 3. Measured opening baseline

Measured 2026-08-26 in `D:\code\ccode`. These values are a dated observation,
not hand-maintained Portal status:

| Surface | Observation |
| --- | --- |
| Core AI Portal working set | 195 files; about 2.07 MiB. |
| Portal plus `docs/ai-friendly` | 343 files; about 3.12 MiB. |
| `D:\code\Frontal_Mem` | 13 files; about 0.10 MiB. |
| Historical memory-retention output packet | 53 files; about 0.93 MiB. |
| `.git` | about 2.85 GiB; repository machinery, not Portal memory. |
| `build` | about 2.58 GiB; generally regenerable build output. |
| `docs` LMDB payload | The opening coarse probe found 152 non-sparse 1-GiB files. The M1 inventory supersedes that probe with the full current population and size distribution in `labtalk/reports/portal/memory_storage_inventory_latest.md`. |

None of the measured `docs/**/data.mdb` files is tracked by Git. The inspected
messaging specimen is ignored by the `docs/**/backups/` rule. Directory totals
that traverse `tmp/vroot` must not be treated as unique physical usage because
that tree contains WSL reparse-point aliases.

The opening finding is therefore: Portal prose is not the storage problem.
Repeated derived LMDB environments are the first physical-storage population
to classify, while oversized onboarding sets and stale authority copies are the
first cognitive population to classify. Current counts and sizes belong to the
generated M1 inventory, not this charter.

## 4. Memory and storage tiers

| Tier | Name | Purpose | Typical contents | Default loading |
| --- | --- | --- | --- | --- |
| F0 | Bootstrap | Safe action invariants and maintained pointers. | Tier-1 seed and vendor shims. | Always read; hard byte ceiling. |
| F1 | Frontal | Current task posture and smallest sufficient working set. | Current target, active claims, current run pointers, glossary routes, authority map. | Loaded by task intent. |
| W2 | Warm recall | Recent or frequently reused knowledge. | Current contracts, accepted decisions, recent closeouts, active proofs. | One or two recall hops. |
| C3 | Cold memory | Valuable but infrequently needed history. | Superseded specifications, complete evidence packets, historical closeouts, rollback records. | Metadata and summary first; body on demand. |
| R4 | Reconstructible | Outputs reproducible from a smaller authority. | Builds, caches, generated reports, derived LMDB environments. | Never onboarded; rebuild on demand. |
| Q5 | Quarantine | Unclassified, conflicting, sensitive, or recovery-unproven material. | Unknown backups, divergent copies, documents with unclear authority. | Owner review only. |

Storage tier is independent of authority. An authoritative artifact can be cold.
A frontal artifact can be derivative if it is clearly labeled and points to its
authority. No tier changes evidence state or publication state.

## 5. Record model

Every inventory record must carry enough information to retrieve, evaluate,
and restore the artifact without trusting its filename:

| Field | Meaning |
| --- | --- |
| `memory_id` | Stable namespaced identity for the record. |
| `title` | Human-readable label. |
| `project_id` | Owning project. |
| `lane_ids` | Owning or related AIF lanes; never overloaded into `ticket`. |
| `artifact_kind` | Contract, plan, closeout, proof, source, database, generated output, backup, or other typed kind. |
| `authority_class` | Authority, evidence, reviewed derivative, generated projection, or unknown. |
| `evidence_state` | Planned, source-evidenced, or runtime-proven. |
| `storage_tier` | F0, F1, W2, C3, R4, or Q5. |
| `source_uri` | Current exact path or external URI. |
| `stored_uri` | Long-term location when different from the source. |
| `sha256` | Content identity for a stored immutable artifact. |
| `size_bytes` | Measured logical size. Physical allocation is recorded separately when material. |
| `created_at` | Known creation time and its source. |
| `last_verified_at` | Time the path, hash, or reconstruction procedure was last checked. |
| `supersedes` / `superseded_by` | Explicit lineage; absence must not be inferred from dates alone. |
| `retention_policy` | Keep, review-after, reconstructible, legal hold, or owner-ruling-required. |
| `sensitivity` | Public, development-only, private, secret, or unknown. |
| `retrieval_trigger` | Portal recall trigger that makes the memory reachable. |
| `recovery_method` | Restore or rebuild procedure plus proof reference. |
| `portal_summary` | One or two paragraphs suitable for bounded recall. |

The future machine-readable schema and generated inventory belong to M1. This
document is the plan of record, not a hand-maintained inventory.

## 6. Standing rules proposed for owner adoption

1. Pointer over copy. Frontal memory carries a summary, identity, authority,
   trigger, and exact location; it does not duplicate the body.
2. Reachable before demoted. An item cannot leave F1/W2 until a recall trigger
   reaches its summary and storage record.
3. Restore before reclaim. No physical source is removed until retrieval or
   reconstruction has succeeded from the proposed retained state.
4. Authority before age. Newer does not mean authoritative, and older does not
   mean disposable.
5. Derived is not automatically deletable. Reconstructibility must be proven
   for the exact population and dependencies before an execute step.
6. Owner confirms destructive transitions. Agents may inventory, classify, and
   propose; physical deletion or irreversible relocation requires an explicit
   owner-approved manifest.
7. No perishable literals in F0. Counts and sizes are generated observations
   behind pointers, never copied into always-read onboarding text.
8. One inventory, many projections. The Portal, website inspector, reports, and
   maintenance views consume the same typed record set.
9. Reparse points are boundaries. Size scanners do not recurse into a name
   surrogate unless alias traversal is explicitly requested and labeled.
10. Unknown means quarantine. Missing authority, sensitivity, hash, or recovery
    evidence prevents automatic demotion or reclamation.

These rules are proposed by AIF-136. Recording them does not self-approve them;
owner rulings will promote, revise, or reject them.

## 7. Lifecycle

```text
discover
-> measure without following aliases
-> classify authority and sensitivity
-> identify duplicates and supersession
-> propose a cognitive/storage tier
-> owner confirms protected transitions
-> copy or move into the approved store
-> verify hash and retrieval/rebuild
-> update Portal summary and recall synapse
-> re-run onboarding and widow/orphan gates
-> separately authorize any source reclamation
```

At every transition the original remains in place until the destination and
recovery method are verified. A failed verification returns the record to Q5
and makes no destructive change.

## 8. Phases and gates

| Phase | Deliverable | Gate |
| --- | --- | --- |
| M0 | This charter, AIF claim, measured opening baseline, and proposed rules. | G0: owner reviews scope and rules; no storage mutation. |
| M1 | **COMMITTED; CURRENT REPORTS REFRESHED.** Read-only inventory generator, typed schema, contract validator, hierarchical counts, and generated Markdown/JSON reports. | G1 PASS: deterministic output, alias exclusion, deferred hashing, tracked/ignored/untracked/external posture, schema failure fixtures, stale-report detection, and the unified deep check are green. |
| M2 | **COMMITTED; CURRENT REPORTS REFRESHED.** Derived classification and lineage pass over Portal documents and the generated current LMDB population. | G2 PASS: every M1 candidate has an authority, sensitivity, tier proposal, and recovery posture; unknowns remain Q5; lineage and recovery matches remain candidate-only. |
| M3 | **APPROVED.** Owner approved the exact three-body in-place cognitive pilot at `2026-08-27T00:10:00Z`. | G3 PASS: exact manifest approved; no wildcard or physical action; rollback named. |
| M4 | **COMMITTED AND VERIFIED.** Three exact owner-confirmed C3 overrides, bounded history summary, explicit recall trigger, and repeatable exclusion/retrieval proof. | G4 PASS: ordinary onboarding excludes the bodies; history recall resolves every exact path and hash through the clone-visible bounded summary; sources remain in place. |
| M5 | **M5-A AND THE ONE EXACT M5-B PILOT APPROVED, VERIFIED, AND DURABLE.** M5-A proved reconstruction from the retained DBF plus CDX metadata container. After a separately approved restore drill, M5-B manifest `AIF136-M5B-001` removed only its listed `data.mdb` and `lock.mdb`, reclaimed 16,384 logical bytes, preserved the empty target directory, and left the retained DBF, CDX, and every other protected environment unchanged. | G5 PASS: ruling packet, exact manifest, fail-closed executors, focused tests, transcript, and machine-readable proofs ship together. Recheck on 2026-10-12 confirmed the local target directory is present and empty, removed payloads remain absent, retained local DBF/CDX match their approved hashes, and the transcript hash matches its proof. The evidence is clone-visible; the retained DBF/CDX are development data at the manifest paths, not Git payloads. This pilot authorizes no other target or bulk reclaim. |
| M6 | **IMPLEMENTED AND VERIFIED.** One ordered command refreshes or checks Tier 0, its self-declared byte budget, mandatory tracked onboarding, identifier/feed projections, the truth audit, history summary, M3/M4 proof, and optionally the slower M1/M2 storage census. | G6 PASS for AIF-136 scope: the Portal suite is 97/97; Tier 0 stale detection was proven red before regeneration; the history target is clone-visible; M3/M4 recall checks pass; and current inventory/classification checks pass. Recurrence is event-triggered at cold start, restart, Portal mutation, and closeout through the maintained README command, not a background time scheduler. The aggregate recall gate still reports two untracked DDICT resources owned by the separate DDICT integration slice; they do not reopen AIF-136. |

M5 must use a new execution authorization even if M0-M4 are accepted. The
existing `prune_lmdb_archives.ps1` defaults to dry-run and is evidence of prior
art, not authorization to execute it against the newly measured population.

## 9. First inventory slices

The read-only M1 inventory should report these populations separately:

1. Portal F0/F1 bodies and recall targets.
2. `docs/ai-friendly` governance and onboarding documents.
3. closeouts, proofs, run artifacts, and external-AI intake packages.
4. `D:\code\Frontal_Mem` and explicitly linked external memory bodies.
5. ignored `docs/**/data.mdb` files, grouped by lane, package, and environment.
6. build/cache outputs and reparse-point aliases, excluded from document counts.

The first report must not hash all 152 GiB blindly. It should identify file
identity, allocation, path grouping, timestamps, Git posture, container/source
dependencies, and cheap duplicate candidates first. Full hashing is a scheduled
follow-up only where it changes a retention decision.

## 10. Acceptance test

AIF-136 is ready for an execution ruling when the system can answer, for any
candidate artifact:

1. Why is this knowledge worth keeping?
2. Which artifact is authoritative?
3. Which project, AIF lane, run, and ruling own it?
4. Which cognitive and physical tiers apply?
5. What summary and trigger make it reachable without loading the body?
6. What exact bytes will move or be reclaimed?
7. How was retrieval or reconstruction proven?
8. What requires owner approval, and where is that approval recorded?

If any answer is missing, the artifact remains in place and is classified Q5.

## 11. Current boundary

M1 and M2 created these development-tree artifacts:

- `labtalk/ai_portal/build_memory_storage_inventory.py`
- `labtalk/ai_portal/schemas/portal_memory_inventory_v1.schema.json`
- `labtalk/ai_portal/tests/test_build_memory_storage_inventory.py`
- `labtalk/reports/portal/memory_storage_inventory_latest.json`
- `labtalk/reports/portal/memory_storage_inventory_latest.md`
- `labtalk/ai_portal/build_memory_storage_classification.py`
- `labtalk/ai_portal/schemas/portal_memory_classification_v1.schema.json`
- `labtalk/ai_portal/tests/test_build_memory_storage_classification.py`
- `labtalk/reports/portal/memory_storage_classification_latest.json`
- `labtalk/reports/portal/memory_storage_classification_latest.md`
- `docs/maintenance/AIF136_M3_MEMORY_PILOT_RULING_PACKET_V1.md`
- `labtalk/registries/aif136_memory_pilot_manifest_v1.json`
- `labtalk/ai_portal/schemas/portal_memory_pilot_manifest_v1.schema.json`
- `labtalk/ai_portal/validate_memory_pilot_manifest.py`
- `labtalk/ai_portal/tests/test_validate_memory_pilot_manifest.py`
- `labtalk/ai_portal/build_portal_history_summary.py`
- `labtalk/ai_portal/PORTAL_HISTORY_SUMMARY_V1.md`
- `labtalk/ai_portal/tests/test_build_portal_history_summary.py`
- `labtalk/ai_portal/verify_memory_pilot_recall.py`
- `labtalk/ai_portal/tests/test_verify_memory_pilot_recall.py`
- `docs/maintenance/AIF136_M4_COGNITIVE_DEMOTION_PROOF_V1.md`

The implementation and its focused tests landed in development at `5d09988bd`;
the charter and M3/M4 proof landed at `3d79836b7`. The generated inventory is
the authority for current counts, byte distributions, Git posture, and the
Portal-facing hierarchy. The generated M2 report is the authority for the
current proposed classifications, exact-hash duplicate groups, conservative
filename families, and unverified LMDB recovery input candidates. Generated
reports remain perishable projections and must pass the refresh/check workflow
before their values are treated as current.

M3 adds a three-item exact manifest for cognitive demotion only. Its validator
matches every memory ID, path, size, and SHA-256 against M1 and the live tracked
body, rejects physical mutation, and requires an explicit owner decision and
timestamp before `approved` is valid. The proposed retained store is the
existing Git-tracked source path; M3 creates no copy and selects no physical
cold-store technology.

M4 applies the approved manifest as three exact owner-confirmed C3 overrides,
generates the bounded history summary, and proves the selected bodies are absent
from ordinary onboarding while their paths and hashes remain reachable through
`trigger.portal_history`. No source body changed location or content.

M6 adds `labtalk/ai_portal/refresh_portal_state.py`. Its default path checks or
refreshes the fast control plane. `--include-storage` adds the slower read-only
M1/M2 scan. The order is part of the contract: the generated history summary is
written before M1 inventories `labtalk/ai_portal`; otherwise the refresh makes
its own inventory stale later in the same pass. The Portal truth audit was also
separated from the optional Tk GUI import so headless maintenance can run on the
project Python. The same fast path delegates the F0 size limit to
`tools/staging/check_seed_budget.py` and clone visibility of mandatory onboarding
to `labtalk/ai_portal/check_mandatory_tracked.py`; the orchestrator deliberately
does not duplicate either tool's maintained threshold or path set.

The 2026-10-12 truthfulness repair closes one false-green in that orchestration.
The Tier 0 step previously had no check arguments, so `--check` merely printed a
fresh projection and returned success without comparing it with
`TIER0_STATE.md`. The generator normalizes transport line endings and the
deliberately volatile `generated_utc` value, then compares every semantic state
line. A different HEAD, upstream, target, closeout, warning, claim, session,
lineage row, or aside chain makes the check fail with exit 3. Focused tests
prove current and stale paths, and the aggregate runner explicitly requires the
new `--check` argument.

The storage inventory excludes `.git` from its maintained workspace summaries.
Repository bookkeeping is not Portal memory, and staging a refreshed report
mutates `.git/index`; including it made the report invalidate itself before an
immediate check. The dated opening baseline above preserves the useful Git-size
observation without turning Git index churn into a false Portal freshness
failure. A focused test changes `.git/index` and proves the inventory remains
identical.

The M6 automation slice did not create a long-term store, movement manifest, or
deletion authorization. Its checks do not mutate DBF, CDX, CNX, LMDB, backup,
archive, website, or publication surfaces. The earlier M5-B action remains
bounded exclusively by manifest `AIF136-M5B-001` and its owner ruling.

M5-B and M6 completion add these durable artifacts:

- `docs/maintenance/AIF136_M5B_RECLAIM_PILOT_RULING_PACKET_V1.md`
- `docs/maintenance/AIF136_M5B_RESTORE_DRILL_PROOF_V1.md`
- `docs/maintenance/AIF136_M5B_RECLAIM_EXECUTION_PROOF_V1.md`
- `labtalk/registries/aif136_m5b_reclaim_manifest_v1.json`
- `labtalk/ai_portal/run_aif136_m5b_restore_drill.py`
- `labtalk/ai_portal/run_aif136_m5b_reclaim.py`
- `labtalk/ai_portal/tests/test_run_aif136_m5b_restore_drill.py`
- `labtalk/ai_portal/tests/test_run_aif136_m5b_reclaim.py`
- `labtalk/proofs/runs/20260915_aif136_m5b_restore_drill.txt`
- `labtalk/proofs/runs/20260915_aif136_m5b_restore_drill.json`
- `labtalk/proofs/runs/20260915_aif136_m5b_reclaim.json`
- `labtalk/ai_portal/PORTAL_HISTORY_SUMMARY_V1.md`
- `labtalk/ai_portal/refresh_portal_state.py`
- `labtalk/ai_portal/tests/test_refresh_portal_state.py`

Completion means the bounded lifecycle, pilot, proof, recall route, and
maintenance command are durable in `development`. It does not approve another
reclaim candidate, convert the one pilot into a wildcard policy, promote files
to `C:\x64base`, publish the website, or push a branch.

The M5-B evidence and recovery procedure are durable in Git. The exact retained
DBF and CDX inputs remain local development data, untracked at their manifest
paths. A fresh clone can inspect the approval and proof but cannot rebuild this
specific environment until those exact inputs are restored from the retained
data store. That boundary is deliberate and must not be abbreviated to
"clone-reproducible."
