# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-09-04T19:52:02Z
    lane        : AIF-082 (6.1)

Read this before acting. It is the only current-state source that
cannot drift, because nothing here is written by hand.

## Tree

    branch        : development
    HEAD          : 68e80d359  (2026-09-04)
    upstream      : 8df02addf
    unpushed      : 13 commit(s) ahead of upstream

## Declared target

    updated       : unknown
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_SQLSEL_USER_MANUAL_2026-09-03.md
    commits behind HEAD : 15

## Staleness warnings

- The newest closeout is 15 commit(s) behind HEAD. Work has landed that no closeout describes; read `git log` as well.
- 13 commit(s) are unpushed and invisible to a clone.

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-152 | null-semantics | member.derald | yes |
| AIF-151 | triggers-pdlc | member.derald | yes |
| AIF-150 | atomic lock race proof and SQLsel P4.3 LEFT JOIN | member.ai.codex.local | yes |
| AIF-149 | set-relation-crossing-workspaces | member.ai.claude.cowork | yes |
| AIF-148 | hasorder-conflates-container-with-active-order | member.ai.claude.cowork | yes |
| AIF-147 | relation-traversal-surface-asymmetry | member.ai.claude.cowork | yes |
| AIF-145 | path-resolution-ladder-divergence | member.ai.claude.cowork | yes |
| AIF-144 | identity-authority-fragmentation | member.ai.claude.cowork | yes |
| AIF-143 | duplicate-settings-struct | member.ai.claude.cowork | yes |
| AIF-142 | deleted-row-absent-from-order | member.ai.claude.cowork | yes |
| AIF-141 | x64-name-vector-silent-drop | member.ai.claude.cowork | yes |
| AIF-140 | load-alias-collision | member.ai.claude.cowork | yes |
| ... | 71 older claims omitted | | |

## Sessions, lineage, asides

    live   : 2026-07-31_cowork_bbs_agency_legs  (member.ai.claude.cowork)  [stale, reapable]
    live   : AIPR-20260729-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260816-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260818-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260821-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260826-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : DECLARED-CAPABILITY-VALIDATOR-20260730  (member.ai.claude.cowork)  [stale, reapable]

Aside chains -- a run's claims in order (its horizontal structure);
parent + born_utc from the durable lineage ledger, '-' until a run wakes.

| run | member | parent | born_utc | asides |
| --- | --- | --- | --- | --- |
| AIFGEN-20260904-124821 | member.derald | - | - | AIF-152 |
| AIFGEN-20260904-064818 | member.derald | - | - | AIF-151 |
| CODEX-20260903-007 | member.ai.codex.local | - | - | AIF-150 |
| COWORK-20260830-001 | member.ai.claude.cowork | - | - | AIF-149 |
| COWORK-20260829-001 | member.ai.claude.cowork | - | - | AIF-148 |
| COWORK-20260827-001 | member.ai.claude.cowork | - | - | AIF-137 -> AIF-138 -> AIF-139 -> AIF-140 -> AIF-141 -> AIF-142 ... |
| CODEX-20260826-014 | member.ai.codex | - | - | AIF-135 -> AIF-136 |
| COWORK-20260826-002 | member.ai.claude.cowork | - | - | AIF-134 |
| ... | | | | 44 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
