---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: <AIPR-YYYYMMDD-NNN>
  recorded_at_utc: <YYYY-MM-DDTHH:MM:SSZ>
  agent:
    provider: <provider-or-not_exposed>
    product: <AI-product-or-tool>
    model: <model-or-not_exposed>
    access_mode: <local_write | local_read_only | hosted_proposal | external_patch | human_operated_tool | automation>
  session:
    id: <opaque-session-id-or-not_exposed>
    chat_reference: <safe-product-task-reference-or-not_exposed>
  project:
    id: <project-id-from-labtalk/registries/projects.yaml>
    root: <registered-project-root>
  git:
    branch: <branch-or-not_applicable>
    baseline_commit: <full-commit-sha-or-not_applicable>
  authorization:
    requested_by: <maintainer | human-operator | automation-owner>
    scope: <concise-authorized-scope>
  report:
    path: <repo-relative-path-to-this-closeout>
    kind: session_closeout
---

# Session Closeout -- <topic> (AIF-NNN)

**The `(AIF-NNN)` in the title is required** (AIF-082, 6.13). It is the only
machine-readable statement of which lane a closeout belongs to. Measured
2026-07-31: 76 of 83 existing closeouts omit it, which makes the whole set
unattributable and defeats every downstream check, including the AIF-006
Session Log audit. If a session genuinely spans several lanes, name the owning
one here and list the rest in the body. If it belongs to no lane, write
`(no lane)` rather than leaving it blank.

Date: <YYYY-MM-DD>.
Owning lifecycle: <DotTalk++ SDLC | LabTalk SDLC | maintenance | PLDC>.
SDLC lane: <intake | design | implementation | proof | review | promotion | maintenance | publication>.
Truth state: <observed | source-defined | runtime-proven | mixed>.
Proof state: <none | report | transcript | build | git-verified>.

Copy this file to `SESSION_CLOSEOUT_<topic>_<YYYY-MM-DD>.md` and fill it in.
Delete this instruction line and any sections that do not apply. Keep it honest:
report only states actually reached.

The `ai_report_audit` envelope is mandatory for every new AI-authored closeout.
Use `not_exposed` or `not_applicable` instead of inventing identity, chat, model,
or git values. See `labtalk/ai_portal/AI_REPORT_AUDIT_CONTRACT_V1.md`.

## One-line summary

<What the session accomplished, in one sentence.>

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
|  |  |  |

## Verified (proof performed this session)

<Runtime transcripts, tests, readbacks, or git-state checks. Name the evidence.
"A zero exit code is not proof; a green readback is not proof either." Say what
you actually confirmed, and how.>

## AI-facing docs updated (AIF-006 gate)

<Which of CURRENT_TARGET.md / AI_README.md / dashboard / intake queue you
updated, or "no lane state changed this session" with the reason.>

## Published

<Staging promotion and GitHub commits, by stage. Name commits/branches. Or
"not promoted" / "not published".>

## Handoff left (AIF-082 gate, ratified 2026-07-31)

<Path to the handoff this session left in `docs/agents/`, and one line on what it
covers. A closeout records what happened; a handoff records how to work here.

Or state "no handoff owed" with the reason -- a session that only read, or only
repeated known work, has nothing durable to hand off and should say so rather
than manufacture a file.

Rules: commit it, aim it at the next agent, cite `file:line`, assert no
perishable facts (say "measure it"), keep it roughly Tier-1 sized. See
`AI_PORTAL.md` -> "Leave a Handoff as well".>

## Still open — for the next session

<Bugs found but not fixed, deferred lanes, housekeeping, next gate. This is the
most valuable section for continuity — it is what the next session reads first.>

## Provenance pointers

<Links to the reports, contracts, READMEs, and manifests this session produced
or relied on.>
