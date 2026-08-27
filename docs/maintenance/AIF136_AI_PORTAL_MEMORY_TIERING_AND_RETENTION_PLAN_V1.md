# AIF-136 -- AI Portal Memory Tiering and Retention Plan V1

Status: M4 cognitive pilot locally implemented and verified; commit pending; no artifact moved or deleted.

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
| M1 | **IMPLEMENTED LOCALLY.** Read-only inventory generator, typed schema, contract validator, hierarchical counts, and generated Markdown/JSON reports. | G1 local PASS: deterministic output, alias exclusion, deferred hashing, tracked/ignored/untracked/external posture, schema failure fixtures, and stale-report detection tested. Review/commit remains owed. |
| M2 | **IMPLEMENTED LOCALLY.** Derived classification and lineage pass over Portal documents and the generated current LMDB population. | G2 local PASS: every M1 candidate has an authority, sensitivity, tier proposal, and recovery posture; unknowns remain Q5; lineage and recovery matches remain candidate-only. Review/commit remains owed. |
| M3 | **APPROVED.** Owner approved the exact three-body in-place cognitive pilot at `2026-08-27T00:10:00Z`. | G3 PASS: exact manifest approved; no wildcard or physical action; rollback named. |
| M4 | **IMPLEMENTED LOCALLY.** Three exact owner-confirmed C3 overrides, bounded history summary, explicit recall trigger, and repeatable exclusion/retrieval proof. | G4 local PASS: ordinary onboarding excludes the bodies; history recall resolves every exact path and hash through the bounded summary; sources remain in place. Review/commit remains owed. |
| M5 | Separately authorized reconstructible-data reclaim pilot. | G5: rebuild succeeds before and after reclaim; live environments and source containers remain untouched. |
| M6 | Recurring drift, freshness, widow/orphan, and storage-budget checks. | G6: known-bad fixtures fail; clean fixtures pass; alerts do not mutate storage. |

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

Local verification ran the M1 tests plus ten focused M2 tests, both
standard-library contract validators, report generation, and stale-report
checks. The generated inventory is the authority for current counts, byte
distributions, Git posture, and the Portal-facing hierarchy. The generated M2
report is the authority for the current proposed classifications, exact-hash
duplicate groups, conservative filename families, and unverified LMDB recovery
input candidates. These results remain working-tree evidence until a scoped
commit makes them durable.

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

This slice did not create a long-term store, movement manifest, or deletion
authorization. No DBF, CDX, CNX, LMDB, backup, archive, website file, or
publication surface was mutated.
