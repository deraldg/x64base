# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-10-22T13:43:08Z
    lane        : AIF-082 (6.1)

Read this before acting. It is a generated current-state projection;
verify it with the generator's --check mode before relying on it.

## Tree

    branch        : development
    HEAD          : 70326db07  (2026-10-21)
    upstream      : 70326db07
    unpushed      : 0 commit(s) ahead of upstream

## Declared target

    updated       : 2026-07-31T18:50:00Z
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_AIF171_PHASE8_REPAIR_PLAN_2026-10-15.md
    commits behind HEAD : not committed

## Staleness warnings

- The newest closeout by date, SESSION_CLOSEOUT_AIF171_PHASE8_REPAIR_PLAN_2026-10-15.md, is on disk but in no commit. A clone cannot see it; whoever wrote it has not landed it.
- Closeout(s) on disk but not tracked -- a session's record that never landed: SESSION_CLOSEOUT_AIF171_PHASE8_M4_PLAN_2026-10-15.md, SESSION_CLOSEOUT_AIF171_PHASE8_M4_APPLY_M5_REMEASURE_2026-10-15.md, SESSION_CLOSEOUT_AIF171_PHASE8_M3_APPLY_2026-10-15.md, SESSION_CLOSEOUT_AIF171_PHASE8_M2_PLAN_2026-10-15.md (+13 more).

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-172 | x64-memo-slot-predicate-one-owner | member.ai.claude.cowork | yes |
| AIF-171 | guarded-help-store-refresh | member.ai.codex | yes |
| AIF-170 | ddict-data-repair | member.ai.codex | yes |
| AIF-169 | cascade_differential | member.ai.claude.cowork | yes |
| AIF-168 | Engine performance: per-row cost reduction + parallel read-only scans | member.ai.claude.cowork | yes |
| AIF-167 | Pinocchio Phase 3: relational shakedown (REL/ENUM + SQLsel + transactional DML via indexes) | member.ai.claude.cowork | yes |
| AIF-166 | partner-amicus-standing | member.derald | yes |
| AIF-165 | Regression summary must distinguish graded PASS from transcript-only execution; add validators for the workspace family exposed as not graded by REGRESSION ALL | member.ai.codex | yes |
| AIF-164 | x64-field-type-parity | member.derald | yes |
| AIF-163 | memo-sidecar-reclamation | member.derald | yes |
| AIF-162 | record-lock-lifetime | member.derald | yes |
| AIF-161 | negative-claim-decay | member.derald | yes |
| ... | 91 older claims omitted | | |

## Sessions, lineage, asides

    live   : 2026-07-31_cowork_bbs_agency_legs  (member.ai.claude.cowork)  [stale, reapable]
    live   : AIPR-20260729-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260818-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260821-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260826-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : DECLARED-CAPABILITY-VALIDATOR-20260730  (member.ai.claude.cowork)  [stale, reapable]
    live   : DOCFLUSH-20261013-002  (member.ai.codex)  [stale, reapable]

Aside chains -- a run's claims in order (its horizontal structure);
parent + born_utc from the durable lineage ledger, '-' until a run wakes.

| run | member | parent | born_utc | asides |
| --- | --- | --- | --- | --- |
| AIFGEN-20261020-131238 | member.ai.claude.cowork | - | - | AIF-172 |
| CODEX-20261013-HELP-REFRESH-001 | member.ai.codex | - | - | AIF-171 |
| CODEX-20261012-DDICT-REPAIR-001 | member.ai.codex | - | - | AIF-170 |
| AIPR-20260920-001 | member.ai.claude.cowork | - | - | AIF-167 -> AIF-168 -> AIF-169 |
| AIFGEN-20260916-090054 | member.derald | - | - | AIF-166 |
| CODEX-20260915-AIF165-REGGRADE-001 | member.ai.codex | - | - | AIF-165 |
| AIFGEN-20260914-194836 | member.derald | - | - | AIF-164 |
| AIFGEN-20260914-105334 | member.derald | - | - | AIF-163 |
| ... | | | | 60 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
