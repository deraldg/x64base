# x64base AI Portal

Status: **Alpha/Experimental**
Audience: AI development partners and maintainers
Published location: repository root as `AI_PORTAL.md`

The AI Portal prepares an AI to work with x64base using repository-local
authority, contracts, runtime evidence, safety gates, task recipes, and explicit
proof states. It is not a student AI service, autonomous project authority, or
production agent runtime.

## Canonical Start

`AI_README.md` is the one canonical front door. Begin there.

Its required order is:

1. newest `docs/maintenance/SESSION_CLOSEOUT_*.md`;
2. `docs/agents/CURRENT_TARGET.md`;
3. development-flow authority seeds;
4. local-access checklist when the AI can act locally;
5. SDLC fast start;
6. source-mutation contract gate before source changes;
7. DotScript readiness before authoring or running `.dts`;
8. external-AI package contract when work returns as a proposal.

This file summarizes the portal doctrine. It does not replace that order or turn
the full reference shelf into a mandatory startup queue.

## Authority

```text
D:\code\ccode
  authoritative development source and runtime truth
        |
        | reviewed coherent changes and selected public projection
        v
C:\x64base
  disposable curated publication staging
        |
        | reviewed commit and push
        v
github.com/deraldg/x64base
  public snapshot
```

GitHub is the baseline available to outside AI systems. It is not authority over
unpublished development work. `C:\x64base` is not a backup, second development
tree, or place for original changes.

A public-only change must be reconciled into `D:\code\ccode`, proved there, and
promoted again before it is integrated project work.

## Task Entry

Every task records:

```text
id:
title:
area:
owning_lifecycle:
sdlc_lane:
truth_state:
proof_state:
risk_class:
authority_root:
public_baseline_commit:
source_path:
website_path:
next_gate:
owner:
status:
```

Unknown fields remain unknown. Publication does not convert design intent into
runtime proof.

## Source-Mutation Rule

Before changing authoritative implementation source, report:

```text
Target source files:
Owning subsystem:
Baseline commit:
Owning lifecycle and SDLC lane:
Truth state, proof state, risk class, and next gate:
Contracts read:
Applicable @dottalk.contract / @dottalk.usage blocks:
Constraints and conflicts:
Expected behavior change:
Required source/test/HELP/metadata changes:
Proof plan:
```

If the request conflicts with an active contract, stop before mutation and
surface the conflict. Do not weaken a contract for patch convenience.

## Hosted / Outside AI

An outside AI proposal must identify the exact public baseline and return a
reviewable package containing:

- manifest and scope;
- unified patch or narrowly scoped new text files;
- contracts and source annotations read;
- behavioral, compatibility, mutation, and security effects;
- tests actually performed versus tests only recommended;
- expected local proof and rollback/non-promotion conditions;
- unresolved drift or conflicts.

Outside AI does not claim local compilation, integration, or runtime proof it did
not perform.

## Local-Access AI

Direct file or shell access removes the packaging step, not the gate.

A local-access AI must:

- complete the same authority, SDLC, and contract reads;
- obtain explicit maintainer authorization before mutation;
- make original changes only in authoritative development;
- preserve dirty and untracked maintainer work;
- avoid broad Git staging, branch changes, cleanup, resets, and irreversible
  deletion unless specifically authorized;
- default to report-only for runtime data, HELP/metadata catalogs, generated
  outputs, publications, fixtures, backups, and archives;
- hand long builds to the maintainer unless explicitly authorized;
- report only stages actually reached.

## DotScript Gate

DotScript is the current DotTalk++ command stream, not remembered xBase, SQL, or
an imagined language.

Readiness states are:

```text
UNASSIMILATED
-> ORIENTED
-> SYNTAX_BACKED
-> SANDBOX_PROVEN
-> AUTHORIZED_FOR_TARGET
```

A zero process exit code is not proof. Review the full transcript, bootstrap the
runtime profile explicitly, name source paths, and assert specific data and
behavior.

## Public-State Rule

Public documentation must describe the public target. Development-only behavior
must be labeled as development-only.

Current example: the product/index edition system is implemented and proved in
authoritative development, while public `main` still contains the older preset
surface documented in `BUILDING.md`. That distinction remains until Path A is
published and cold-clone certified.

## Required Closeout

Report these states separately:

1. development files changed;
2. development proof;
3. files promoted to staging;
4. staging proof;
5. commit created;
6. branch/commit pushed;
7. website changes and publication, when applicable.

Never infer a later stage from an earlier success.

### Closeout Updates Startup — AIF-006

When lane state changes, update the AI-facing document that describes it:

| Changed state | Update |
| --- | --- |
| current objective | `docs/agents/CURRENT_TARGET.md` |
| branch, remote, or authority pointer | `AI_README.md` |
| lane state or session log | `docs/ai-friendly/AI_FRIENDLY_DASHBOARD_V1.md` |
| candidate status or identifier | `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` |

A state-changing session also leaves a dated closeout under
`docs/maintenance/` and adds it to the dashboard Session Log.

## Portal Boundary

```text
source defines
runtime proves
HELP explains
metadata organizes
SelfDoc preserves provenance
MDO/manualgen assembles reviewed documentation
website summarizes reviewed truth
AI Portal selects and explains task-relevant context
```

The portal is currently Python/YAML/Markdown and read-oriented. Typed graph
validation, deterministic context compilation, guarded execution, recovery, and
evaluation remain hardening gates. Until those gates pass, all public surfaces
must retain the **Alpha/Experimental** label.
