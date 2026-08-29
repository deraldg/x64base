# Tier 0 -- generated state projection

    GENERATED FILE. Do not edit; edits are overwritten.
    generator   : labtalk/ai_portal/generate_tier0_state.py
    generated_utc : 2026-08-29T21:19:52Z
    lane        : AIF-082 (6.1)

Read this before acting. It is the only current-state source that
cannot drift, because nothing here is written by hand.

## Tree

    branch        : development
    HEAD          : af6e9ea03  (2026-08-29)
    upstream      : c7c94e186
    unpushed      : 12 commit(s) ahead of upstream

## Declared target

    updated       : unknown
    section       : NEXT TARGET -- owner ruling 2026-07-31: no single controlling lane

## Newest closeout

    file          : SESSION_CLOSEOUT_PATH_LADDERS_AND_TRAVERSAL_SURFACES_2026-08-28.md
    commits behind HEAD : 63

## Staleness warnings

- The newest closeout is 63 commit(s) behind HEAD. Work has landed that no closeout describes; read `git log` as well.
- 12 commit(s) are unpushed and invisible to a clone.

## Claimed lanes (newest first)

| AIF | lane | steward | intake row |
| --- | --- | --- | --- |
| AIF-148 | hasorder-conflates-container-with-active-order | member.ai.claude.cowork | yes |
| AIF-147 | relation-traversal-surface-asymmetry | member.ai.claude.cowork | yes |
| AIF-145 | path-resolution-ladder-divergence | member.ai.claude.cowork | yes |
| AIF-144 | identity-authority-fragmentation | member.ai.claude.cowork | yes |
| AIF-143 | duplicate-settings-struct | member.ai.claude.cowork | yes |
| AIF-142 | deleted-row-absent-from-order | member.ai.claude.cowork | yes |
| AIF-141 | x64-name-vector-silent-drop | member.ai.claude.cowork | yes |
| AIF-140 | load-alias-collision | member.ai.claude.cowork | yes |
| AIF-139 | R112's migration gate is unassertable: sec 6a admits first-wins-plus-warning only as an instrumented phase whose counter must reach a measured zero, but ambiguity_count() has no DTS-visible reader -- cmd_workspace.cpp only PRINTS it -- and rel_name_ambiguity_regression.dts, which calls itself the tripwire for AIF-078 stage 4, runs WORKSPACE REGISTRY between two FORMULA markers with nothing checking. The comment at cmd_workspace.cpp:4736 claims the count is 'a FIELD of the registry, assertable by a spec' and no such reader exists. The tripwire fired on 2026-08-27 and no spec in the suite would have caught it | member.ai.claude.cowork | yes |
| AIF-138 | Engine::_current cannot express 'nothing selected': slot 0 means area 0, the startup position (shell.cpp:528 selectArea(0)), and 'no engine' (workareas.hpp:120 'if (!eng) return 0'). Absent is spelled with a present value (R6), and the no-engine fallback is the AIF-118 shape sitting in the accessor infer_parent_from_workarea() calls. Predates multi-workspace; R129 sec 6.1 makes an empty workspace a legal position and so makes it reachable | member.ai.claude.cowork | yes |
| AIF-137 | The relation STORE is partitioned by workspace (AIF-078 I1.2) but the relation PARENT is not -- current_parent_override() is one global string and current_parent_name()/refresh_from_parent_name() resolve through the unscoped find_open_area_by_name_ci, so a refresh standing in one workspace reads another workspace's area; measured live 2026-08-27 with an EMPTY relation store, so it needs no SET RELATION to occur | member.ai.claude.cowork | yes |
| AIF-136 | AI Portal frontal-memory tiering, document consolidation, long-term storage, retrieval, and governed retention lifecycle | member.ai.codex | yes |
| ... | 67 older claims omitted | | |

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
| COWORK-20260829-001 | member.ai.claude.cowork | - | - | AIF-148 |
| COWORK-20260827-001 | member.ai.claude.cowork | - | - | AIF-137 -> AIF-138 -> AIF-139 -> AIF-140 -> AIF-141 -> AIF-142 ... |
| CODEX-20260826-014 | member.ai.codex | - | - | AIF-135 -> AIF-136 |
| COWORK-20260826-002 | member.ai.claude.cowork | - | - | AIF-134 |
| COWORK-20260825-001 | member.ai.claude.cowork | - | - | AIF-128 -> AIF-129 -> AIF-130 -> AIF-131 -> AIF-133 |
| CODEX-20260826-001 | member.ai.codex | - | - | AIF-132 |
| COWORK-20260824-001 | member.ai.claude.cowork | - | - | AIF-123 -> AIF-124 -> AIF-125 -> AIF-126 -> AIF-127 |
| COWORK-20260822-001 | member.ai.claude.cowork | - | - | AIF-121 -> AIF-122 |
| ... | | | | 40 older run(s) omitted |

Perishable detail lives in the artifacts these point at. Do not
restate anything above; regenerate it.
