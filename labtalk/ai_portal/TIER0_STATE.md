# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-08-26T22:56:32Z
    lane        : AIF-082 (6.1)

Read this before acting. It is the only current-state source that
cannot drift, because nothing here is written by hand.

## Tree

    branch        : development
    HEAD          : 6c3809eed  (2026-08-26)
    upstream      : 372c5834f
    unpushed      : 3 commit(s) ahead of upstream

## Declared target

    updated       : unknown
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_R128_ADDITIVE_WORKSPACES_2026-08-26.md
    commits behind HEAD : ?

## Staleness warnings

- 3 commit(s) are unpushed and invisible to a clone.

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-136 | AI Portal frontal-memory tiering, document consolidation, long-term storage, retrieval, and governed retention lifecycle | member.ai.codex | yes |
| AIF-135 | Align claim-aif and next_aif on monotonic high-water allocation over the canonical intake-and-claims identity universe; prove gaps are never reused and preserve atomic collision handling | member.ai.codex | yes |
| AIF-134 | ERROR CLEAR/STATUS/TEST are registered as multi-word keys with no bare ERROR router, so shell_dispatch cannot reach them -- the AIF-131 defect unfixed in a sibling family, while dotref publishes all three as supported | member.ai.claude.cowork | yes |
| AIF-133 | FIELDMGR scratch tables keep the .dbf extension, so every directory scan opened a restructure backup as a work area -- and it sorted first, taking area 0 | member.ai.claude.cowork | yes |
| AIF-132 | AI Portal typed feed contract, advisory validator, and documentation-push crosswalk | member.ai.codex | yes |
| AIF-131 | dotref documents BUILD VECTORS / BUILD INFO as supported; shell_dispatch keys on the first token so they can never be typed | member.ai.claude.cowork | yes |
| AIF-130 | AI_README says a sandbox cannot build; measured false 2026-08-12, uncorrected for 13 days | member.ai.claude.cowork | yes |
| AIF-129 | contract-subblock-vocabularies-uncontrolled | member.ai.claude.cowork | yes |
| AIF-128 | refcheck-guard-tests-the-union-not-the-authority | member.ai.claude.cowork | yes |
| AIF-127 | x64-reader-false-terminator-at-thirteen-rows | member.ai.claude.cowork | yes |
| AIF-126 | help-store-shared-msg-unreachable-by-key | member.ai.claude.cowork | yes |
| AIF-125 | agent-navigation-index-over-system-metadata | member.ai.claude.cowork | yes |
| ... | 56 older claims omitted | | |

## Sessions, lineage, asides

    live   : 2026-07-31_cowork_bbs_agency_legs  (member.ai.claude.cowork)  [stale, reapable]
    live   : AIPR-20260729-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260816-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260818-001  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260821-002  (member.ai.claude.cowork)  [stale, reapable]
    live   : COWORK-20260826-001  (member.ai.claude.cowork)
    live   : DECLARED-CAPABILITY-VALIDATOR-20260730  (member.ai.claude.cowork)  [stale, reapable]

Aside chains -- a run's claims in order (its horizontal structure);
parent + born_utc from the durable lineage ledger, '-' until a run wakes.

| run | member | parent | born_utc | asides |
| --- | --- | --- | --- | --- |
| CODEX-20260826-014 | member.ai.codex | - | - | AIF-135 -> AIF-136 |
| COWORK-20260826-002 | member.ai.claude.cowork | - | - | AIF-134 |
| COWORK-20260825-001 | member.ai.claude.cowork | - | - | AIF-128 -> AIF-129 -> AIF-130 -> AIF-131 -> AIF-133 |
| CODEX-20260826-001 | member.ai.codex | - | - | AIF-132 |
| COWORK-20260824-001 | member.ai.claude.cowork | - | - | AIF-123 -> AIF-124 -> AIF-125 -> AIF-126 -> AIF-127 |
| COWORK-20260822-001 | member.ai.claude.cowork | - | - | AIF-121 -> AIF-122 |
| COWORK-20260817-001 | member.ai.claude.cowork | - | - | AIF-119 -> AIF-120 |
| COWORK-20260816-001 | member.ai.claude.cowork | - | - | AIF-118 |
| ... | | | | 38 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
