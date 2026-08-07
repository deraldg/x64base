---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260806-007
  recorded_at_utc: 2026-08-07T06:20:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: claude-cowork:not_exposed
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: c16dd10b7
  authorization:
    requested_by: maintainer
    scope: >
      Owner asked "why is p0 stopping you", which exposed that G0 had been ruled
      against an audience the agent had chosen rather than the audience the
      project brief named. Owner then authorized the missing no-tree probe and
      its documentation.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_X64BASE_AGENT_SKILL_PROBE_C_2026-08-06.md
    kind: session_closeout
---

# Session Closeout -- AIF-090 probe C, G0 made audience-specific (AIF-090)

Date: 2026-08-06.
Owning lifecycle: PLDC.
SDLC lane: intake.
Truth state: mixed -- structural findings verified directly; behavioural findings contaminated.
Proof state: report + web-verified.

## One-line summary

Ran the no-tree probe that P0 had skipped, discovered the harness makes a clean
no-tree probe impossible, and found -- without needing the probe at all -- that
this project does not publish its own contributor governance on the branch it
tells contributors to use.

## Changed (development, D:\code\ccode)

| Area | File | Note |
| --- | --- | --- |
| Evidence | `.../aif090_cold_probes_2026-08-06/PROBE_C_NO_TREE.md` | new; no-tree arm, contamination disclosed in its section 1 |
| Evidence | `.../aif090_cold_probes_2026-08-06/MANIFEST.md` | records the fourth arm that was designed and deliberately NOT run |
| Lane | `docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md` | new section 9a; G0 is now audience-specific |
| Continuity | `docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md` | section 0 |
| Registry | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` | AIF-090 row |
| Registry | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` | Session Log row |

## Verified (proof performed this session)

**Verified directly, no probe required** -- fetched from
`raw.githubusercontent.com` and compared against the working tree:

- `CONTRIBUTING.md` @ `main`: "The public `main` branch is the canonical
  collaboration and release branch." **That sentence is about where a public
  claim becomes current. The file is SILENT on which branch to baseline** -- its
  "Before opening a change" list says "build from a clean checkout" and names no
  branch. An earlier revision of this closeout, the lane, the dashboard, the
  intake row, the handoff and the probe file all quoted it as if it answered the
  baselining question. It does not. Corrected same day, 2026-08-06, in all six.
  The probe flagged this before its author did: "No document I read says in one
  place 'outside contributors, base on `main`'."
- `AI_README.md` @ `main`: "public branch: main" and "The development branch is
  current workspace state and must be discovered locally." No branch-enumeration
  section. No repository-roles table. Calls `C:\x64base` a "clean staging
  mirror".
- `AI_README.md` @ `development`: carries "Remote / hosted agents -- MANDATORY
  branch enumeration" and states that building against `main` without
  enumerating is "a hard onboarding failure (observed 2026-08)". Opens with the
  repository-roles table.
- `AI_PORTAL.md`: 24,693 B on `main`, 53,350 B on `development` (the latter
  measured locally).

**Verified by probe, and contaminated** -- the harness auto-injected `CLAUDE.md`
into the subagent despite an explicit instruction that it had no local access.
The probe detected this itself and disclosed it unprompted, declining to claim a
clean-room result. Its behavioural findings are therefore not trustworthy; its
structural findings are, because they are properties of what is published.

**Deliberately not run:** the fourth arm (no tree, WITH a bundle). Both arms
would have carried the bundle's contents by injection, so the comparison could
not have meant anything. Publishing that number would have been an instance of
the defect class this lane exists to close. Recorded in the manifest rather than
omitted.

## AI-facing docs updated (AIF-006 gate)

Lane section 9a, handoff section 0, intake row, dashboard row.
`CURRENT_TARGET.md` deliberately unchanged.

## Published

Committed to `development`. Not promoted to `C:\x64base`. Not published to the
website -- which is itself relevant to the finding.

## Handoff left (AIF-082 gate)

`docs/agents/HANDOFF_CLAUDE_COWORK_AGENT_SKILL_2026-08-06.md` section 0, updated
a third time in one day. Three updates in a day is the argument for a handoff
being pointer-shaped rather than narrative.

## Still open -- for the next session

1. **The cheapest fix is not a skill and not a bundle.** Publish the
   branch-enumeration rule and the repository-roles table on `main`, where
   `CONTRIBUTING.md` already sends people. That is a promotion decision, not a
   build. It is owner territory: it changes what the public branch says.
2. **The real tension is `AI_README.md` @ `development` versus `AGENTS.md`.**
   The former says baseline on `development`; the latter says never merge
   `development` to `main`. `PROMOTION_PROCESS.md` resolves it ("open PRs
   against `main`") and is also `development`-only, so an outside contributor
   sees neither the instruction nor its resolution.
3. **`WORKFLOW_X64BASE.md` on `main`** calls `C:\x64base` "a mirror only" while
   `AI_PORTAL.md` on the same branch declares that wording stale. Known on
   `development`, invisible from `main`.
4. **A clean no-tree measurement needs a different harness.** Any future probe
   of the distributable case must run somewhere `CLAUDE.md` is not injected, or
   its control is not a control.
5. Carried forward: flip `check_seed_budget.py` to hard after one clean cycle;
   the graph over-links and now says so; 21 untracked `.md` at
   `docs/maintenance` root; the `yes`/`no` vs `true`/`false` editorial call.

## What this session actually established

The lane opened to build a skill that would make onboarding fire automatically.
P0 killed it: agents inside the tree already onboard fine. Probe C then found
that the audience the brief named -- outside agencies -- has a different problem
entirely, and one no skill fixes: **the rules they will be judged against are
not published where they can read them.** An outside agent that follows the only
instructions visible to it commits the failure this project records as hard.

The lane's answer to its own question turned out to be a publication decision,
not a tool.

## Provenance pointers

- Probe package: `docs/maintenance/external_ai_intake/aif090_cold_probes_2026-08-06/`
- Lane: `docs/maintenance/X64BASE_AGENT_SKILL_PLDC_LANE_V1.md` sections 9, 9a, 10
- Prior closeouts this day: `..._LANE_OPEN_...`, `..._P0_...`, `..._D1_D4_...`
