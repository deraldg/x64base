# AI Friendly Dashboard v1

Status: seed dashboard.
Purpose: User-visible status surface for AI-assisted DotTalk++ / LabTalk work.

## Current Visibility Contract

The user should be able to see:

- what AI is working on,
- what evidence it read,
- what files or systems it touched,
- whether mutation was performed or only proposed,
- where each useful interaction was routed,
- what still needs review, proof, or promotion.

## Current Lane State

| Area | Status | Anchor |
| --- | --- | --- |
| Lane manifest | seeded | `docs/ai-friendly/AI_FRIENDLY_LANE_MANIFEST_V1.md` |
| Workflow | seeded | `docs/ai-friendly/AI_FRIENDLY_WORKFLOW_V1.md` |
| Intake queue | seeded | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` |
| Dashboard | seeded | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` |
| Assimilation portal | seeded | `docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md` |
| Assimilation book | seeded | `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md` |
| LabTalk portal integration | active seed | `labtalk/registries/portal.yaml` |
| AI Portal hardening lane | Alpha/Experimental — active | `labtalk/ai_portal/AI_PORTAL_HARDENING_LANE_V1.md` |
| Generated report integration | not started | future report under `docs/ai-friendly/reports` |

## User Status Buckets

| Bucket | Meaning | Current items |
| --- | --- | --- |
| captured | Useful AI-assisted material has been noticed. | Seed rows AIF-001 through AIF-004. |
| classified | Material has candidate tags and a route. | Seed rows AIF-001 through AIF-004. |
| distilled | Raw interaction has been reduced to a durable artifact. | Manifest, workflow, intake queue, dashboard. |
| anchored | Item points to source, proof, contract, report, or design-intent evidence. | AIF-001, AIF-002, AIF-003. |
| routed | Item has a destination lane. | AIF-001 through AIF-004. |
| promoted | Item has moved into its destination lane with evidence. | Existing agent card and contract lifecycle were already promoted before this lane. |
| review-needed | Human review or stronger evidence is needed. | AIF-004 after first review. |
| rejected | Item is explicitly not part of the system. | none yet. |
| superseded | Item has been replaced by a stronger artifact. | none yet. |

## Authority Levels

Use this table when reading any AI Friendly item:

| Level | User meaning |
| --- | --- |
| chat-only | Conversation material only; not durable. |
| captured | Saved or referenced for possible review. |
| draft | Written in repo, not yet reviewed or proven. |
| design-intended | Accepted as a design direction, not runtime-proven. |
| source-defined | Current source declares or implements it. |
| runtime-proven | A command, test, transcript, or smoke run proves it. |
| HELP-documented | HELP/CMDHELP exposes it to users. |
| CMDHELPCHK-validated | Validation has checked the HELP/contract surface. |
| publication-ready | SelfDoc/manualgen can publish it with evidence. |
| student-ready | LabTalk can present it to learners. |
| rejected | Reviewed and excluded. |
| superseded | Replaced by a newer or stronger artifact. |

## Current AI Work Log

| Date | Work | Mutation | Evidence read | Result |
| --- | --- | --- | --- | --- |
| 2026-07-04 | Seed AI Friendly lane | docs only | LabTalk docs, contract lifecycle, agent bootstrap card, SelfDoc lab docs | Created lane manifest, workflow, intake queue. |
| 2026-07-04 | Add user visibility surface | docs only | AI Friendly seed docs | Created dashboard and linked it from README. |
| 2026-07-04 | Add new-AI assimilation portal/book | docs and MAINT visibility | AI Friendly docs, agent bootstrap card, DotScript handoff | Created durable onboarding path for new or second-opinion AI. |

## Items Needing User Review

| ID | Item | Review question | Suggested outcome |
| --- | --- | --- | --- |
| AIF-004 | AI Friendly lane proposal | Does this lane shape match the intended operating model? | Mark design-intended after review, then add a contract registry row only if it becomes a durable constraint. |

## Items Needing Proof

| Item | Needed proof | Route |
| --- | --- | --- |
| AI Portal hardening APH-0 | Baseline tests, reproducible startup, and zero unexplained missing paths | `labtalk/ai_portal` |
| Future generated AI Friendly inventory report | Read-only scanner/report run | `docs/ai-friendly/reports` |
| Future assimilation smoke | Runtime check for `MAINT AI ASSIMILATE` after MAINT integration | `src/cli/cmd_maint.cpp` |

## Drift Risks

| Risk | Mitigation |
| --- | --- |
| AI Friendly becomes a duplicate documentation shelf. | Route to existing lanes first. |
| Raw chat is treated as authority. | Keep chat material as source material until distilled and anchored. |
| Useful interactions are hoarded instead of curated. | Capture only material with reuse value. |
| Claims outrun source/runtime proof. | Use authority levels and proof gates before promotion. |

## Next Practical Step

Create a small read-only seed inventory report that scans known AI/project notes
and classifies only a few high-value candidates. Do not bulk-import old chat or
scratch material.
