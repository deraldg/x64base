# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-09-10T00:52:16Z
    lane        : AIF-082 (6.1)

Read this before acting. It is the only current-state source that
cannot drift, because nothing here is written by hand.

## Tree

    branch        : development
    HEAD          : be39ae05b  (2026-09-09)
    upstream      : bde66b0a9
    unpushed      : 6 commit(s) ahead of upstream

## Declared target

    updated       : unknown
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_SQLSEL_USER_MANUAL_2026-09-03.md
    commits behind HEAD : 107

## Staleness warnings

- The newest closeout is 107 commit(s) behind HEAD. Work has landed that no closeout describes; read `git log` as well.
- 6 commit(s) are unpushed and invisible to a clone.

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-159 | sqlsel-transactions | member.derald | yes |
| AIF-158 | autoincrement | member.derald | yes |
| AIF-157 | index-sidecar-durability | member.ai.claude.cowork | yes |
| AIF-156 | primary-key-policy | member.ai.claude.cowork | yes |
| AIF-155 | runtime-def-family | member.ai.claude.cowork | yes |
| AIF-154 | metadata-catalogue-pipeline | member.ai.claude.cowork | yes |
| AIF-153 | browsetui-student-app | member.ai.claude.cowork | yes |
| AIF-152 | null-semantics | member.derald | yes |
| AIF-151 | triggers-pdlc | member.derald | yes |
| AIF-150 | atomic lock race proof and SQLsel P4.3 LEFT JOIN | member.ai.codex.local | yes |
| AIF-149 | set-relation-crossing-workspaces | member.ai.claude.cowork | yes |
| AIF-148 | hasorder-conflates-container-with-active-order | member.ai.claude.cowork | yes |
| ... | 78 older claims omitted | | |

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
| AIFGEN-20260909-174200 | member.derald | - | - | AIF-159 |
| AIFGEN-20260907-182435 | member.derald | - | - | AIF-158 |
| COWORK-20260906-001 | member.ai.claude.cowork | - | - | AIF-156 -> AIF-157 |
| COWORK-20260905-002 | member.ai.claude.cowork | - | - | AIF-154 -> AIF-155 |
| COWORK-20260905-001 | member.ai.claude.cowork | - | - | AIF-153 |
| AIFGEN-20260904-124821 | member.derald | - | - | AIF-152 |
| AIFGEN-20260904-064818 | member.derald | - | - | AIF-151 |
| CODEX-20260903-007 | member.ai.codex.local | - | - | AIF-150 |
| ... | | | | 49 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
