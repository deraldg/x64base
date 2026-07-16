# External AI Change Package Contract v1

Status: **Active handoff contract**
Audience: hosted AI engines, maintainers, and the local integration workbench

## Purpose

ChatGPT, Gemini, Grok, Copilot, and other AI systems may review the public
x64base snapshot and propose changes. Their output returns to the maintainer as
a package for review against the authoritative development tree.

An outside AI proposal is never considered compiled, integrated, or proven
merely because the AI produced complete-looking files.

## Required Request Inputs

Every request to an outside AI should provide:

```text
Repository URL:
Public branch:
Exact baseline commit SHA:
AI Portal entry URL:
Target files or subsystem:
Objective:
Owning lifecycle:
SDLC lane:
Truth state:
Proof state:
Risk class:
Next gate:
Allowed scope:
Excluded scope:
Expected proof:
```

If the AI cannot read the repository or linked portal files, attach the portal
entry, mandatory seeds, relevant contracts, and target files. The AI must list
what it actually received and read.

## Required Package Contents

Preferred archive layout:

```text
x64base-ai-change-package/
  MANIFEST.md
  changes.patch
  new-files/
  TEST_PLAN.md
  NOTES.md
```

`MANIFEST.md` must identify:

- the complete `ai_report_audit` envelope from
  `AI_REPORT_AUDIT_CONTRACT_V1.md`, including AI provider/product/model,
  access mode, opaque session/chat reference, registered project ID and root,
  authorization scope, and report path;
- AI engine and session date;
- repository URL, branch, and exact baseline commit;
- objective and owning subsystem;
- owning lifecycle, SDLC lane, truth state, proof state, risk class, next gate,
  and status;
- changed, added, and deleted files;
- contracts and source annotations read;
- mutation and compatibility effects;
- files intentionally excluded;
- unresolved questions or conflicts.

The external AI must self-identify honestly. If the host does not expose the
model or session identifier, use `not_exposed`; do not guess. Do not place raw
chat transcripts, credentials, cookies, access tokens, or private account data
in the package.

`changes.patch` should be a unified diff relative to the stated baseline.
Complete replacement files belong under `new-files/` only when a unified patch
cannot represent them clearly.

`TEST_PLAN.md` must separate:

- checks the outside AI actually performed;
- checks it recommends but could not perform;
- expected local build/runtime results;
- fixtures and mutation safety;
- rollback or non-promotion conditions.

## Package Rejection Conditions

Reject or return the package for correction when:

- it omits the baseline commit;
- it changes files outside the requested scope without justification;
- it ignores applicable contracts;
- it includes binaries, build output, databases, indexes, secrets, or local
  machine state;
- it claims compilation or runtime proof that was not actually performed;
- it relies on a public snapshot older than the relevant development work and
  does not acknowledge the gap;
- it rewrites large files when a narrow patch would suffice;
- it creates or assumes a new branch as part of the proposal.

## Local Intake Procedure

The local workbench should:

1. preserve the received archive unchanged as intake evidence;
2. verify the manifest and baseline commit;
3. inspect the patch before applying it;
4. compare the public baseline with current `D:\code\ccode` target files;
5. enter the correct SDLC and identify the current lane and next gate;
6. complete the source-mutation contract preflight;
7. apply or manually reconcile only the intended hunks;
8. compile and test in development;
9. keep failed or superseded proposals out of publication staging;
10. promote only the proven relevant result to `C:\x64base`;
11. record development, staging, GitHub, and website states separately.

## Copyable Outside-AI Request

```text
Repository: https://github.com/deraldg/x64base
Branch: main
Baseline commit: <exact SHA>
Start here: https://github.com/deraldg/x64base/blob/main/AI_PORTAL.md

Read every mandatory seed and applicable contract before proposing source
changes.

Target: <file or subsystem>
Objective: <requested change>
Owning lifecycle / SDLC lane: <lifecycle and current gate>
Allowed scope: <paths>
Excluded scope: unrelated cleanup, binaries, generated runtime data, branch operations

Return a package containing MANIFEST.md, changes.patch, TEST_PLAN.md, NOTES.md,
and any genuinely new text source files. State exactly what you read, what you
tested, what you could not test, and every unresolved contract conflict.
```

## Boundary

This contract standardizes intake. It does not authorize the outside AI to
write to local development, approve its own patch, mutate maintained data,
publish, commit, push, or change contracts.
