# AIF-136 M3 Memory Pilot Ruling Packet V1

Status: APPROVED

Owner: `member.derald`

Steward: `member.ai.codex`

Manifest: `labtalk/registries/aif136_memory_pilot_manifest_v1.json`

Validator: `labtalk/ai_portal/validate_memory_pilot_manifest.py`

## Decision requested

Approve, revise, or reject a three-body cognitive-demotion pilot. Approval
would authorize M4 to change Portal classification and recall behavior from W2
warm recall to C3 cold-on-demand. It would not authorize moving or deleting a
file, changing Git history, publishing content, or reclaiming storage.

## Why this pilot

The three bodies are tracked, hashed, development-only reviewed derivatives.
They are dated history or early design, not current onboarding authority. They
are small enough to verify exactly and meaningful enough to prove that the
Portal can retain useful history without loading the full body during ordinary
onboarding.

| Exact body | M1 identity | Proposed change | Why retained |
| --- | --- | --- | --- |
| `labtalk/ai_portal/AI_PORTAL_REONBOARDING_ASSESSMENT_2026-07-29.md` | `memory.file.9a79a9a9f3af3b95d0f4` | W2 -> C3 | Cold-start acceptance-test and synchronization-drift history. |
| `labtalk/ai_portal/AI_ONBOARDING_TRUTH_REVIEW_2026-08-05_V1.md` | `memory.file.35c21a34db10fadf5c73` | W2 -> C3 | Incident history explaining why current onboarding controls exist. |
| `labtalk/ai_portal/SEED_CONNECTION_PROTOTYPE_NOTE_V1.md` | `memory.file.db8df9b3fb28e94a3d3b` | W2 -> C3 | Design lineage for bounded intent-driven recall. |

The exact expected SHA-256 and byte size for each body live in the manifest and
must match both the live file and the M1 inventory before M4 can begin.

## Proposed retained state

- The Git-tracked source path remains the stored body. There is no second copy.
- `trigger.portal_history` reaches this packet and, in M4, a bounded summary for
  each selected body.
- Normal onboarding loads the summary and authority warning, not the body.
- An explicit history request retrieves the tracked body on demand.
- Current seeds, source, contracts, registries, and runtime evidence remain the
  authority for current behavior.

This in-place pilot deliberately tests cognitive tiering before choosing or
creating a separate physical cold store. A separate store would add custody,
copy, and restore risks without helping prove the first mechanism.

## M4 acceptance proof if approved

1. Revalidate the exact manifest against the current M1 inventory and live
   SHA-256 values.
2. Add explicit, generated classification overrides for only the three memory
   IDs; wildcard selection is forbidden.
3. Add a bounded Portal history summary reachable from
   `trigger.portal_history`.
4. Prove ordinary onboarding does not load the three full bodies.
5. Prove an explicit history query resolves each exact path and hash.
6. Re-run recall, widow/orphan, inventory, classification, and manifest gates.
7. Record measured results. A failed proof returns the classification to W2.

## Rollback

Remove only the three classification overrides and the history-summary
projection. The source bodies never leave their tracked paths, so rollback does
not require data restoration.

## Explicit exclusions

- No F0 seed, F1 frontal record, active claim, or governance authority.
- No private `D:\code\Frontal_Mem` Q5 body.
- No DBF, CDX, CNX, LMDB, backup, archive, generated catalog, or website file.
- No source move, copy, deletion, publication, Git-history rewrite, or storage
  reclamation.
- No supersession declaration. The packet records related lineage only.

## Owner ruling

Current state: `approved`.

Owner decision: approved in the active Codex task on 2026-08-27 at
`2026-08-27T00:10:00Z` in response to the exact instruction, "Approve the
AIF-136 M3 pilot."

Approval requires an explicit owner response after reviewing these exact three
targets. The steward must then record `decision: approved` and a decision UTC in
the manifest before M4. Authoring this packet does not self-approve it.
