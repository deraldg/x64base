# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-08-26T15:39:58Z
    lane        : AIF-082 (6.1)

Read this before acting. It is the only current-state source that
cannot drift, because nothing here is written by hand.

## Tree

    branch        : development
    HEAD          : 892245854  (2026-08-26)
    upstream      : a278b511e
    unpushed      : 87 commit(s) ahead of upstream

## Declared target

    updated       : unknown
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_AI_PORTAL_STRUCTURED_ASSERTIONS_2026-08-26.md
    commits behind HEAD : 15

## Staleness warnings

- The newest closeout is 15 commit(s) behind HEAD. Work has landed that no closeout describes; read `git log` as well.
- 87 commit(s) are unpushed and invisible to a clone.

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-133 | FIELDMGR scratch tables keep the .dbf extension, so every directory scan opened a restructure backup as a work area -- and it sorted first, taking area 0 | member.ai.claude.cowork | yes |
| AIF-132 | AI Portal typed feed contract, advisory validator, and documentation-push crosswalk | member.ai.codex | yes |
| AIF-131 | dotref documents BUILD VECTORS / BUILD INFO as supported; shell_dispatch keys on the first token so they can never be typed | member.ai.claude.cowork | yes |
| AIF-130 | AI_README says a sandbox cannot build; measured false 2026-08-12, uncorrected for 13 days | member.ai.claude.cowork | yes |
| AIF-129 | contract-subblock-vocabularies-uncontrolled | member.ai.claude.cowork | yes |
| AIF-128 | refcheck-guard-tests-the-union-not-the-authority | member.ai.claude.cowork | yes |
| AIF-127 | x64-reader-false-terminator-at-thirteen-rows | member.ai.claude.cowork | yes |
| AIF-126 | help-store-shared-msg-unreachable-by-key | member.ai.claude.cowork | yes |
| AIF-125 | agent-navigation-index-over-system-metadata | member.ai.claude.cowork | yes |
| AIF-124 | canonical-workspace-versus-workspace-state | member.ai.claude.cowork | yes |
| AIF-123 | set-deleted-visibility-sweep | member.ai.claude.cowork | yes |
| AIF-122 | build-stamp-rebuild-cost | member.ai.claude.cowork | yes |
| ... | 53 older claims omitted | | |

## Sessions, lineage, asides

    live   : 2026-07-31_cowork_bbs_agency_legs  (member.ai.claude.cowork)  [stale, reapable]
    live   : AIPR-20260729-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : CODEX-20260826-012  (member.ai.openai.codex)
    live   : COWORK-20260816-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260818-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260821-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : DECLARED-CAPABILITY-VALIDATOR-20260730  (member.ai.claude.cowork)  [stale, reapable]

Aside chains -- a run's claims in order (its horizontal structure);
parent + born_utc from the durable lineage ledger, '-' until a run wakes.

| run | member | parent | born_utc | asides |
| --- | --- | --- | --- | --- |
| COWORK-20260825-001 | member.ai.claude.cowork | - | - | AIF-128 -> AIF-129 -> AIF-130 -> AIF-131 -> AIF-133 |
| CODEX-20260826-001 | member.ai.codex | - | - | AIF-132 |
| COWORK-20260824-001 | member.ai.claude.cowork | - | - | AIF-123 -> AIF-124 -> AIF-125 -> AIF-126 -> AIF-127 |
| COWORK-20260822-001 | member.ai.claude.cowork | - | - | AIF-121 -> AIF-122 |
| COWORK-20260817-001 | member.ai.claude.cowork | - | - | AIF-119 -> AIF-120 |
| COWORK-20260816-001 | member.ai.claude.cowork | - | - | AIF-118 |
| COWORK-20260815-001 | member.derald | - | - | AIF-113 -> AIF-114 -> AIF-115 -> AIF-116 -> AIF-117 |
| COWORK-20260814-001 | member.ai.claude.cowork | - | - | AIF-112 |
| ... | | | | 36 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
