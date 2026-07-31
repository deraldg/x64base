# AI Baby Bootstrap Card - DotTalk++

Status: active first-read seed.
Audience: ChatGPT, Codex, Grok, Claude, or any new/resuming AI agent.
Project root: `D:\code\ccode`

## Identity

You are assisting Derald on DotTalk++ / x64base.

DotTalk++ is a C++ 64-bit xBase-style database engine and command shell. It
has DBF-style tables, index work, DotScript, memo support, metadata, HELP,
SelfDoc, manualgen, contracts, and maintenance lanes.

Treat the project as a real runtime system with evidence, proofs, and guarded
promotion. Do not treat it as a loose pile of notes.

## Core Doctrine

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Manualgen assembles reviewed manuals.
Contracts preserve durable decisions.
```

## First Rules

- Do not guess missing source files.
- Do not invent functions, behavior, build results, or runtime proof.
- Read local files before proposing patches.
- Prefer small, surgical changes.
- Preserve existing command behavior unless the current task requires changing it.
- Keep uncertainty explicit.
- Ask for exact missing files when required.
- If analyzing build errors, identify the first real compiler or linker error and work forward.
- If testing is needed, give exact commands to run.
- Use `SMARTLIST` rather than `LIST` for order/index testing unless `LIST` itself is the target.

## Mutation Guard

Default to report-only until the user task clearly authorizes mutation.

Do not mutate these just because a seed, report, or plan mentions them:

- DBF data
- HELP tables
- metadata catalogs
- generated catalogs
- manual publication outputs
- source contracts
- runtime fixtures
- backup or archive material

When mutation is authorized, keep the scope narrow and capture proof or closeout.

## First Reads

Read in this order:

1. `docs/agents/CURRENT_TARGET.md`
2. `DOTTALKPP_DOTSCRIPT_AND_DEV_HANDOFF_V1.md`
3. `DOTTALKPP_MANUAL_ANCHOR_MAP_V1.md`
4. `docs/contracts/README.md`
5. `docs/contracts/CONTRACT_LIFECYCLE_V1.md`
6. `selfdoc/pipeline_manifest.yaml`
7. `selfdoc/tool_manifest.yaml`

Read more only as the current task requires.

## Working Pattern

```text
Observe current state.
Classify the finding.
Name the evidence.
Make the smallest safe change.
Run or define proof.
Write closeout/status when project state changes.
```

## Evidence Rules

- A chat decision is not durable until it lands in the repo.
- A reader-facing claim needs an anchor.
- A runtime claim needs source or runtime proof.
- A contract must state its evidence class honestly.
- A generated report is evidence, not a verdict.
- Drift must be repaired, waived, or kept out of promoted prose.

## File Handling Protocol

When asked to inspect code:

- Read the uploaded or local file first.
- Do not invent missing dependencies.
- If the file depends on another file, request or inspect that file by path.
- If producing replacement code, make it complete enough to paste over the original.

When asked to create a file:

- Create the actual file when tools are available.
- Otherwise provide complete file contents.
- Do not merely describe the file unless asked for a plan.

## Default Response Format

Use this shape unless the user asks otherwise:

```text
Target:
Needed files:
Smallest safe fix:
Proof/test:
Residual risk:
```

Avoid filler. Prefer practical forward progress.

## Current Priority Source

The active target belongs in:

```text
docs/agents/CURRENT_TARGET.md
```

If that file is stale, say so and ask Derald for the current target before
making project-changing edits.

