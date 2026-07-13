# AI Portal Hardening Lane

Status: **Alpha/Experimental — active lane**
Started: 2026-07-12
Owner: Laboratory Campus / AI Friendly / DotTalk++ integration

## Purpose

This lane turns the current LabTalk registry browser and static AI assimilation
documents into a task-oriented AI Portal.

The AI Portal is **for AI to access the development environment as a partner**.
It is not a student portal for accessing an AI service. Its first job is to give
a new or resumed AI a fast, accurate start using durable project seeds rather
than chat memory.

The portal should prepare an AI for a specific series of project tasks by
following curated, typed jumps between projects and artifacts, selecting the
smallest sufficient evidence set, and producing an inspectable task context
packet.

The working metaphor is **frontal memory**. The implementation must remain
explicit and reproducible:

```text
task request
-> typed project and artifact jumps
-> authority and proof checks
-> bounded task context packet
-> guarded action plan
-> proof readback
-> SelfDoc / MDO / Laboratory Campus feedback
```

## First Reads

1. `DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`
2. `SDLC_FAST_START_SEED_V1.md`
3. `SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`
4. `DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`
5. `SEED_CONNECTION_PROTOTYPE_NOTE_V1.md`
6. `../diagrams/DOTTALKPP_SHELL_DISPATCH_AND_LOOP_CAPTURE_V1.md`
7. `EXTERNAL_AI_CHANGE_PACKAGE_V1.md`
8. `AI_PORTAL_HARDENING_LANE_V1.md`
9. `../portal/README.md`
10. `../LABTALK_PORTAL_CONCEPT_v0.md`
11. `../../AI_README.md`
12. `../../docs/ai-friendly/AI_ASSIMILATION_PORTAL_V1.md`
13. `../../docs/ai-friendly/AI_ASSIMILATION_BOOK_V1.md`
14. `../docs/co-development/recursive_coproject_model_v1.md`
15. `../registries/ai_portal.yaml`

## Delivery Posture

The lane is organized around usable increments rather than one long portal
rewrite.

- First usable target: task recipes plus deterministic context packets.
- Near-term prototype: connect task intent to the smallest required set of
  seeds, explain every connection, and expose missing or conflicting context.
- Hardened target: guarded execution and a task-centered portal interface.
- Full intent target: x64base-backed curation and a DotTalk++ teaching loop.
- If a gate runs for more than two weeks without a reviewable artifact, split
  or reduce that gate before continuing.

The planning baseline is substantially shorter than seven months. Dates remain
estimates; proof and safe integration determine promotion.

## Mandatory Public Status

The AI Portal lane is **Alpha/Experimental**. Portal, manual, website, and
generated-summary references must retain that label until graph validation,
context sufficiency, guarded execution, recovery, and evaluation gates are
complete. The portal must not be presented as production autonomous memory or
as an independent source of project truth.

Student and teaching systems may later consume reviewed AI Portal artifacts,
but student access to AI is not the purpose or primary interface of this lane.

## Authority Boundary

This lane organizes and packages truth. It does not manufacture truth.

```text
Source defines.
Runtime proves.
HELP explains.
Metadata organizes.
SelfDoc preserves provenance.
MDO assembles reviewed documentation.
The AI Portal selects and explains task-relevant context.
```

Raw AI conversation, portal prose, generated packets, and public website copy
remain derivative material unless promoted through the existing evidence and
review lanes.

For x64base source and publication work, the mandatory location chain is:

```text
D:\code\ccode -> C:\x64base -> github.com/deraldg/x64base
development      clean staging  public snapshot
authority
```

The current development branch is discovered from the workspace. A new AI chat
must not create or switch branches without an explicit maintainer instruction.
The full cold-start and closeout rules are registered in
`DEVELOPMENT_FLOW_AUTHORITY_SEEDS_V1.md`.

Every task must also enter through `SDLC_FAST_START_SEED_V1.md`, declare its
owning lifecycle and current SDLC lane, and preserve truth, proof, risk, gate,
and closeout state through implementation and publication.

An AI is not DotScript-ready merely because it knows xBase or has read a
language summary. Before AI-authored `.dts` execution, the portal requires the
runtime-learning, syntax-evidence, bootstrap, safety-classification, and
transcript-review gates in `DOTTALKPP_DOTSCRIPT_READINESS_SEEDS_V1.md`.

Before source-code mutation, an AI must complete the contract preflight in
`SOURCE_MUTATION_CONTRACT_GATE_SEED_V1.md`: read the contract shelf, registry,
lifecycle, subsystem contracts, and applicable source usage/contract blocks;
then identify constraints and drift before applying a patch.

## Tracking

Milestones and their current state are registered in:

```text
labtalk/registries/ai_portal.yaml
```

The LabTalk portal exposes that registry as the `AI Portal Work` section.
