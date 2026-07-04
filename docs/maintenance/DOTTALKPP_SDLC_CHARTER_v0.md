# DotTalk++ SDLC Charter v0

Status: draft charter
Created: 2026-07-04
Scope: DotTalk++ runtime, x64base integration, maintenance, proof, and release

## Purpose

DotTalk++ is large enough to have its own SDLC.

LabTalk can teach DotTalk++ and package labs around it, but DotTalk++ owns its
runtime correctness, build shape, command behavior, storage boundaries,
metadata, HELP/CMDHELP/CMDHELPCHK, tests, and maintenance surfaces.

## Decision

Use this split:

```text
DotTalk++ SDLC: engine/runtime/system correctness.
LabTalk SDLC: laboratory campus truth and learning material.
PLDC: product/lab/package delivery over both.
```

PLDC is useful, but it should not replace SDLC. A product or lab package can be
well-designed and still depend on unproven runtime behavior. The SDLC gate must
win when those disagree.

## Ownership Boundary

| Area | Owner |
|---|---|
| x64base storage/data engine | DotTalk++ / x64base SDLC |
| DBF/x64/VFP formats, memo, indexes, locks, buffers | DotTalk++ SDLC |
| CLI commands and command registry | DotTalk++ SDLC |
| DotScript and runtime scripts | DotTalk++ SDLC for behavior; LabTalk for lesson packaging |
| HELP, CMDHELP, CMDHELPCHK | DotTalk++ SDLC and maintenance SDLC |
| MAINT, BBOX, DDICT, MANUAL | DotTalk++ SDLC and lane-specific maintenance SDLC |
| GUI/TUI/browser frontends | DotTalk++ SDLC for runtime contract; PLDC for product delivery |
| LabTalk labs, cases, portal, proof registry | LabTalk SDLC |
| Case-study publication and public pages | LabTalk SDLC plus PLDC publication gate |

## SDLC Lanes

### 1. Requirements and Boundary

Every DotTalk++ change should state:

- command, subsystem, or file family affected,
- read/write/mutation risk,
- compatibility risk,
- expected user-visible behavior,
- HELP/CMDHELP impact,
- test or proof path.

### 2. Design

Design artifacts may be lightweight, but must identify:

- source modules,
- data structures,
- runtime state touched,
- external process/network/filesystem behavior,
- fallback behavior,
- error and message contracts.

### 3. Implementation

Implementation belongs in the correct subsystem:

- `src/xbase`, `include/xbase*` for data/storage behavior,
- `src/xindex`, `include/xindex` for indexing,
- `src/cli` for command surfaces,
- `src/maintenance` for native maintenance support,
- `tools` for report-only or guarded external tools,
- `docs/maintenance` for SDLC reports and gates.

### 4. Verification

Use the smallest proof that exercises the behavior, not only the existence of a
command or file.

Proof types:

- compile/build proof,
- targeted smoke test,
- DTS transcript,
- command output capture,
- fixture readback,
- HELP/CMDHELP readback,
- CMDHELPCHK validation,
- source/report scan,
- before/after fixture diff for mutating behavior.

### 5. Documentation and Metadata

Documentation follows behavior.

Required checks:

- HELP/CMDHELP wording does not outrun runtime behavior,
- CMDHELPCHK gaps are passed or classified,
- contract/source comments are harvested or recorded as next work,
- manuals or LabTalk pages do not promote unverified behavior.

### 6. Release and Promotion

Promotion levels:

| Level | Meaning |
|---|---|
| `source_defined` | Code or contract exists. |
| `runtime_observed` | Runtime proof exists. |
| `help_documented` | HELP/CMDHELP exposes the behavior accurately. |
| `validated` | CMDHELPCHK, smoke, or another validator checked it. |
| `professional_ready` | Safe for normal DotTalk++ runtime use. |
| `lab_ready` | Safe for LabTalk to package in a lab. |

LabTalk may only package a DotTalk++ behavior as `real` after DotTalk++ SDLC has
at least `runtime_observed` proof, and preferably `validated` for student use.

## DotTalk++ vs PLDC

Use DotTalk++ SDLC when the question is:

- Does the command work?
- Is the data safe?
- Does the build pass?
- Are indexes, buffers, filters, relations, and metadata correct?
- Do HELP and validation agree with runtime behavior?

Use PLDC when the question is:

- What product, lab, class, workshop, board, dashboard, or release package are
  we giving a user?
- Who is the audience?
- What setup and support do they need?
- What proof and cleanup should travel with the package?
- Is the public/story/teaching wrapper ready?

## First DotTalk++ SDLC Backlog

1. Keep `docs/maintenance/MAINTENANCE_CHARTER_v1.md` as the maintenance SDLC
   doctrine and this charter as the broader runtime SDLC entry point.
2. Add a DotTalk++ SDLC status report that summarizes build, command, HELP,
   CMDHELPCHK, case/runtime proof, and known red paths.
3. Define release profiles: `ENGINE`, `PROFESSIONAL`, `EDUCATIONAL`,
   `DEV_ONLY`, and `MAINTENANCE`.
4. Classify high-risk command families: mutation, filesystem, external process,
   network, import/export, indexing, and metadata repair.
5. Give LabTalk a stable reference rule: LabTalk can teach only what DotTalk++
   SDLC has proven or what LabTalk labels as simulated/planned.

## Non-Negotiables

- Runtime behavior belongs to DotTalk++ SDLC, even when LabTalk teaches it.
- A portal button is not runtime proof.
- A case study is not runtime proof.
- A successful command listing is not behavioral proof.
- Publication is not authority.
- PLDC cannot promote a behavior past its SDLC evidence.

