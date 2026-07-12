# AI Assimilation Portal v1

Status: seed portal.
Audience: any future AI agent, human maintainer, or second-opinion reviewer.
Purpose: provide a durable entry point if prior AI chat history, OpenAI-hosted
content, or model-specific memory is unavailable.

## Start Here

If you are a new AI agent, do not begin by rewriting code or summarizing the
entire tree. Begin by reading these files in order:

1. `docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`
2. `docs/agents/AI_BABY_BOOTSTRAP_CARD.md`
3. `docs/agents/CURRENT_TARGET.md`
4. `DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`
5. `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md`
6. `docs/contracts/README.md`
7. `docs/contracts/CONTRACT_LIFECYCLE_V1.md`

Then inspect only the files required by the user's current request.

## Prime Directive

```text
Do not rely on lost chat history.
Do not rely on model memory.
Use repo-local evidence.
Keep uncertainty explicit.
Preserve existing work.
Promote only with honest evidence.
```

## What This Portal Is

This portal is a durable assimilation map. It explains where a new AI should
look, how to classify what it finds, and how to continue DotTalk++ / LabTalk work
without needing prior access to OpenAI conversations.

It is not a complete manual. It is the front door.

## What To Prove Before Acting

Before changing files, identify:

| Question | Required answer |
| --- | --- |
| What is the user asking now? | Current objective in one sentence. |
| What lane owns the work? | Runtime, HELP, contracts, SelfDoc, MDO/manualgen, LabTalk, AI Friendly, GUI, data dictionary, maintenance, or other. |
| What files are source of truth? | Exact paths. |
| What files are generated/candidate output? | Exact paths, if any. |
| Does this mutate protected systems? | DBF/CDX/LMDB, HELP, metadata, source, generated catalogs, publications, runtime fixtures, backups, archives. |
| What proof is needed? | Build, runtime transcript, report, test, CMDHELPCHK, SelfDoc, manualgen validation, or explicit review note. |

## Assimilation Path

Use this path for first contact:

```text
orient -> read authority docs -> inspect current target -> classify lane
-> read local evidence -> propose or patch narrowly -> verify -> close out
```

Do not bulk-import old notes. Do not assume untracked files are disposable. Do
not treat generated reports as verdicts.

## Emergency Recovery Use Case

If all hosted AI content disappears, this repo should still preserve enough
context for another AI to continue:

- project doctrine,
- current target,
- build/runtime path,
- safety rules,
- contract lifecycle,
- AI Friendly lane,
- LabTalk campus model,
- proof/report conventions,
- command surfaces such as `MAINT AI`.

## Runtime Surface

The native inspection surface is:

```text
MAINT AI
MAINT AI DASHBOARD
MAINT AI ASSIMILATE
MAINT AI VISIBILITY
```

These are read-only visibility commands. They do not import chat, mutate queues,
edit HELP, run scanners, or publish manuals.

## Next File

Read:

```text
docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md
```
