# AI Report Audit Contract v1

Status: **active — mandatory for new AI-authored closeouts and change packages**.

## Purpose

Make the actor, originating task, owning project, authorization, and repository
state recoverable without treating hosted chat history as project authority.

The durable report is the record. A chat or thread identifier is a provenance
pointer to the interaction that produced it.

## When the envelope is required

Include the `ai_report_audit` YAML front matter in every new AI-authored:

- `SESSION_CLOSEOUT_*.md` file;
- external AI `MANIFEST.md` change package;
- report that changes AI Portal lane state, contracts, registries, proofs,
  promotion state, or publication state.

An AI that mutates an AI Portal-owned artifact must create an audited closeout
in the same changeset. Self-identification is therefore a condition of an AI
Portal update, not an optional annotation added after publication.

Read-only orientation that produces no durable report does not create an audit
record. A human-authored report may use `human_operated_tool` when an automated
tool produced the file under direct human operation.

## Required envelope

```yaml
---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-YYYYMMDD-NNN
  recorded_at_utc: YYYY-MM-DDTHH:MM:SSZ
  agent:
    provider: OpenAI
    product: Codex
    model: not_exposed
    access_mode: local_write
  session:
    id: opaque-provider-session-id
    chat_reference: product-task:opaque-provider-session-id
  project:
    id: project.ai_friendly
    root: D:/code/ccode
  git:
    branch: current-branch
    baseline_commit: full-commit-sha
  authorization:
    requested_by: maintainer
    scope: concise mutation authority granted by the request
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_TOPIC_YYYY-MM-DD.md
    kind: session_closeout
---
```

Project IDs come from `labtalk/registries/projects.yaml`. The declared project
root must match that registry record.

## Honest identity rules

- Never invent a provider session ID, model name, URL, commit, or reviewer.
- Use `not_exposed` when the host does not expose a value.
- Use `not_applicable` only when a field genuinely does not apply.
- Record the AI product separately from the underlying model.
- Record whether the agent had local write access, read-only access, or could
  only return an external proposal.
- A report cannot approve itself. Human review and promotion remain separate
  stages.

## Chat privacy and authority

Store an opaque task/thread ID and, when safe and stable, a link or product
reference. Do not copy raw conversation text, credentials, cookies, access
tokens, private account identifiers, or unrelated personal data into the repo.

The chat reference explains where the work originated. It does not outrank the
repository, contracts, source, HELP, runtime evidence, or human review.

## Enforcement

`labtalk/registries/ai_report_audit.yaml` owns the machine-readable policy.
Historical closeouts are explicitly grandfathered by path. Every closeout not
on that list must pass:

```powershell
python .\labtalk\ai_portal\audit_trail.py
```

The validator checks required fields, report-ID uniqueness, project registry
membership, project-root agreement, report-path agreement, and access-mode
vocabulary. The LabTalk Portal truth audit includes the same findings.
