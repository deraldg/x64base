# x64base AI Portal

Status: **Alpha/Experimental**
Audience: AI development partners and maintainers
Published location: repository root as `AI_PORTAL.md`

This is the fast-start entrance for ChatGPT, Codex, Gemini, Grok, Copilot, and
other AI systems asked to review or change x64base.

It is not a student portal for accessing an AI service. It prepares an AI to
work as a development partner using repo-local authority, contracts, runtime
evidence, safety gates, and task recipes.

## Mandatory Start

Read these in order before proposing changes:

1. [`labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`](labtalk/ai_portal/DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md)
2. [`labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md`](labtalk/ai_portal/SDLC_FAST_START_SEED_V1.md)
3. [`labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`](labtalk/ai_portal/SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md)
4. [`labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`](labtalk/ai_portal/DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md) when DotTalk++ or DotScript is involved
5. [`labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md`](labtalk/ai_portal/EXTERNAL_AI_CHANGE_PACKAGE_V1.md) when work will return as a patch or package
6. [`labtalk/ai_portal/README.md`](labtalk/ai_portal/README.md) for the complete Alpha/Experimental lane

Then inspect only the contracts, source, tests, HELP, and proof material needed
for the assigned task.

## Authority

```text
D:\code\ccode
  authoritative development source and runtime work
        |
        | reviewed, relevant files only
        v
C:\x64base
  curated Git publication staging
        |
        | commit and push
        v
github.com/deraldg/x64base
  public snapshot used by outside AI systems
```

GitHub is the public baseline, not authority over unpublished development work.
An outside AI must identify the exact public commit on which its proposal is
based.

## Source Mutation Rule

Before changing source code, report:

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
Proof/test plan:
```

If the request conflicts with an active contract, stop and describe the
conflict. Do not rewrite the contract merely to make a patch convenient.

## Outside-AI Delivery Rule

Hosted AI systems do not modify `D:\code\ccode` directly. Return a reviewable
change package tied to the stated commit. The package must contain:

1. a unified patch;
2. a manifest of changed and new files;
3. contracts and source usage blocks read;
4. behavioral effects, mutations, and risks;
5. build and test instructions;
6. expected runtime proof;
7. unresolved questions, drift, or conflicts.

The manifest must preserve the owning lifecycle, SDLC lane, truth state, proof
state, risk class, next gate, and status. PLDC or publication work cannot bypass
the underlying DotTalk++, maintenance, or LabTalk SDLC gate.

Do not include binaries, build directories, generated runtime data, unrelated
formatting, cleanup, or branch operations.

## Local Integration Rule

Returned packages are reviewed and applied selectively in `D:\code\ccode`.
They are compiled and tested there first. Only proven, relevant files are
promoted to `C:\x64base`, verified again in staged form, committed, and pushed.
Full or long-running builds are handed to the maintainer as exact PowerShell
commands under the mandatory operator-handoff rule; they are not launched or
babysat by an AI partner unless explicitly authorized for the current task.

Website work is separate. When verified behavior changes public documentation,
update and build `D:\dev\x64base-site`, then commit and publish that repository
with a reference to the supporting x64base source commit.

## Required Closeout

Report each state separately:

- patch reviewed;
- development files changed;
- development build/test result;
- files promoted to `C:\x64base`;
- staged verification result;
- x64base commit and pushed branch;
- website files changed and build result;
- website commit and pushed branch.

Never claim a later state merely because an earlier one succeeded.
