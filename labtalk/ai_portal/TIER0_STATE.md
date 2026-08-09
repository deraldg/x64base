# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-08-09T02:54:32Z
    lane        : AIF-082 (6.1)

Read this before acting. It is the only current-state source that
cannot drift, because nothing here is written by hand.

## Tree

    branch        : development
    HEAD          : 6afd91876  (2026-08-08)
    upstream      : 6afd91876
    unpushed      : 0 commit(s) ahead of upstream

## Declared target

    updated       : unknown
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_PORTAL_MEMORY_SYNAPSE_2026-08-08.md
    commits behind HEAD : 16

## Staleness warnings

- The newest closeout is 16 commit(s) behind HEAD. Work has landed that no closeout describes; read `git log` as well.

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-097 | private-site auth + search | member.derald | yes |
| AIF-096 | coordination-ontology | member.derald | yes |
| AIF-095 | dottalkpp-site | member.derald | yes |
| AIF-094 | pdlc-vocabulary-merge | member.ai.claude.cowork | yes |
| AIF-093 | dottalkpp-text-extension | member.ai.claude.cowork | yes |
| AIF-092 | publication-surface-recovery | member.ai.claude.cowork | yes |
| AIF-091 | dbf-vfp-type-support | member.ai.claude.cowork | yes |
| AIF-090 | x64base-agent-skill | member.ai.claude.cowork | yes |
| AIF-088 | command_catalog_runtime_drift | member.derald | yes |
| AIF-087 | triggers-pdlc | member.derald | yes |
| AIF-086 | ai-systems-integration-sdlc | member.ai.codex.local | yes |
| AIF-083 | bbs-agency-legs | member.ai.claude.cowork | yes |
| ... | 18 older claims omitted | | |

## Sessions, lineage, asides

    live   : 2026-07-31_cowork_bbs_agency_legs  (member.ai.claude.cowork)  [stale, reapable]
    live   : AIPR-20260729-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : DECLARED-CAPABILITY-VALIDATOR-20260730  (member.ai.claude.cowork)  [stale, reapable]

Aside chains -- a run's claims in order (its horizontal structure);
parent + born_utc from the durable lineage ledger, '-' until a run wakes.

| run | member | parent | born_utc | asides |
| --- | --- | --- | --- | --- |
| COWORK-20260808-001 | member.derald | - | - | AIF-097 |
| COWORK-20260807-005 | member.derald | - | - | AIF-095 -> AIF-096 |
| COWORK-20260807-004 | member.ai.claude.cowork | - | - | AIF-094 |
| COWORK-20260807-003 | member.ai.claude.cowork | - | - | AIF-092 -> AIF-093 |
| COWORK-20260807-002 | member.ai.claude.cowork | - | - | AIF-091 |
| COWORK-20260806-001 | member.ai.claude.cowork | - | - | AIF-090 |
| COWORK-20260804-002 | member.derald | - | - | AIF-088 |
| COWORK-20260804-001 | member.derald | - | - | AIF-087 |
| ... | | | | 18 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
