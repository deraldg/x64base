# AI Portal Hardening Lane v1

Status: **Alpha/Experimental — active plan**
Date: 2026-07-12
Scope: Laboratory Campus AI onboarding, task context assembly, guarded
execution, x64base curation, and DotTalk++ teaching integration

## Product Identity

The AI Portal is a machine-facing fast-start system for AI development
partners entering the x64base environment. It is not a student-facing portal
for access to an AI service. Laboratory Campus teaching may study or consume
its reviewed artifacts, but that is separate from the portal's primary role.

Seeds carry durable orientation, authority, workflow, contracts, runtime
learning, safety, task recipes, and proof expectations. The near-term design
problem is to connect those seeds simply and transparently into the smallest
sufficient task packet.

## Mission

Build an AI-facing entrance to the Laboratory Campus that can rapidly collect
the project-specific context needed to perform a series of related tasks.

The portal is not merely a documentation index, chatbot, search box, or command
launcher. It is a proof-aware context compiler over the ecosystem.

The lane remains **Alpha/Experimental** through all current gates. Public and
internal summaries must preserve that label and must not imply production
autonomy, complete memory, or permission to bypass existing authority and
mutation controls.

## Desired Operating Loop

```text
current task
-> identify owning project and lane
-> traverse curated synapses
-> rank artifacts by authority
-> detect missing, stale, or contradictory evidence
-> assemble a bounded task context packet
-> expose permitted actions and proof requirements
-> execute only through approved adapters
-> record results and feed findings back into the campus
```

## Architectural Boundary

Keep the existing Tkinter application as a small, replaceable campus frontend.
Place graph validation, task recipes, packet compilation, risk evaluation, and
execution policy in a headless core that can also serve:

- portal command-line checks;
- DotTalk++ commands;
- future web or workbench interfaces;
- tests and deterministic report generation;
- x64base import/export pipelines.

The frontend must not become the only implementation of portal semantics.

## Core Records

The lane will introduce explicit records for:

| Record | Responsibility |
| --- | --- |
| project | Project identity, ownership, repository, lanes, and authority role. |
| artifact | Source, document, schema, proof, lesson, command, dataset, or publication node. |
| edge | Typed directional jump between two stable IDs. |
| task recipe | Required starting nodes, evidence classes, limits, risks, and completion proof. |
| context packet | Versioned selection of task-relevant artifacts and explanations. |
| proof | Evidence state, source, result, freshness, and promotion status. |
| run | Guarded execution request, authorization, transcript, result, and hashes. |

Initial registries remain portable YAML. x64base becomes the canonical curation
store only after import, export, recovery, and deterministic round-trip proof
exist.

## Synapse Contract

Every jump must be directional, typed, and explainable. Initial edge types:

```text
defines
proves
documents
teaches
requires
derives_from
publishes
mutates
owned_by
supersedes
contradicts
```

An edge must identify its source ID, target ID, relationship, evidence state,
and optional reason. A label or path alone is not a synapse.

## Task Context Packet Contract

Every generated packet must state:

- packet ID, version, task, and owning lane;
- selected nodes and the jump path used to reach them;
- exact source locations, hashes, freshness, and authority class;
- why each artifact was included;
- contradictions, missing proof, and unresolved references;
- context budget and intentionally excluded material;
- mutation and sensitivity classification;
- permitted actions and approval requirements;
- expected completion proof and closeout shape.

Packets are working context, not a new source of runtime truth.

## Delivery Gates

### APH-0 — Preserve and Stabilize

Outcome: the current portal lane is safely preserved and starts reproducibly.

Required work:

- preserve the current untracked and modified portal assets before refactoring;
- resolve or classify all broken portal paths;
- remove stale orientation claims;
- make the supported Python environment explicit;
- establish portal unit-test and fixture locations;
- record the Campus Launcher versus AI Portal Core boundary.

Promotion proof:

- portal audit reports zero unexplained missing paths;
- supported startup succeeds from a clean checkout;
- baseline registry-loading and audit tests pass.

### APH-1 — Typed Registry Graph

Outcome: current registries become a validated graph rather than flat display
metadata.

Required work:

- define node, edge, task-recipe, proof, and packet schemas;
- enforce stable IDs and referential integrity;
- validate authority, ownership, status, path roots, and freshness metadata;
- report orphan, duplicate, circular, contradictory, and unresolved records;
- retain portable repo-relative paths where the owning boundary permits them.

Promotion proof:

- strict validation passes on the curated seed graph;
- intentionally broken fixtures fail with specific diagnostics;
- every seed jump can explain why its target is relevant.

### APH-2 — Task Context Compiler

Outcome: the portal can prepare deterministic, bounded frontal memory for a
specific task without executing it.

First recipes:

1. review an x64base engine feature;
2. explain a schema or data structure;
3. build or review a DotTalk++ lesson;
4. investigate documentation and runtime drift.

Promotion proof:

- repeated compilation over unchanged inputs produces equivalent packets;
- every included claim has an evidence anchor;
- missing required evidence blocks readiness instead of being silently omitted;
- packet size and artifact count remain within recipe limits.

This is the first useful AI Portal MVP.

### APH-3 — Guarded Execution

Outcome: prepared work can run only through explicit, reviewed capabilities.

Required work:

- separate prepare, approve, execute, and verify states;
- make read-only the default capability;
- replace free-form runnable registry commands with named adapters;
- classify filesystem, database, HELP, metadata, publication, and external
  effects;
- enforce allowed roots, timeouts, cancellation, output bounds, and redaction;
- hash transcripts and retain the authorization decision with each run.

Promotion proof:

- unreviewed registry content cannot grant execution authority;
- traversal and path-escape fixtures are rejected;
- protected mutations require explicit approval;
- failed and timed-out process trees terminate cleanly and leave a transcript.

### APH-4 — Task-Centered Portal Experience

Outcome: the primary user journey begins with work to perform, not a shelf to
browse.

Required work:

- add task selection and task-goal intake;
- show typed jumps and why each artifact was selected;
- expose authority, proof, freshness, risk, and missing-context status;
- support packet preview and export;
- run collection and proof work outside the UI thread with progress and cancel;
- preserve ordinary campus browsing as a secondary view.

Promotion proof:

- a new user can prepare each seed task without knowing repository paths;
- long work does not freeze the portal;
- the UI and command-line compiler produce equivalent packet content.

### APH-5 — x64base Self-Hosting

Outcome: x64base stores and curates the portal graph, packets, proofs, and run
history for the project that it documents.

Required work:

- define x64base schemas for the core records;
- import existing YAML without losing stable IDs or provenance;
- export deterministic YAML/JSON bootstrap views;
- prove backup, recovery, validation, and degraded read-only startup;
- keep the database authoritative only after round-trip gates pass.

Promotion proof:

- import/export round trips are deterministic;
- the portal can recover from portable exports;
- x64base-backed and exported graph validation agree;
- a damaged or unavailable curation database does not erase orientation.

### APH-6 — Teaching and Evaluation Loop

Outcome: building and operating the portal becomes part of the Laboratory
Campus curriculum and its effectiveness is measured.

Required work:

- create DotTalk++ lessons for graph records, evidence states, packet assembly,
  execution boundaries, and proof readback;
- measure cold-start task success, unsupported claims, context cost, stale-node
  rate, readiness failures, and time to first correct action;
- route discovered drift through contracts, HELP, SelfDoc, MDO, manuals, and
  public summaries;
- keep student-facing claims proof-backed or explicitly simulated.

Promotion proof:

- each major portal capability has a runnable or inspectable lesson;
- representative AI tasks improve against the static-reading-list baseline;
- evaluation results are reproducible and visible in the campus proof lane.

## Planning Baseline

| Target | Expected range |
| --- | --- |
| Context-packet MVP through APH-2 | 3–5 weeks |
| Hardened local portal through APH-4 | 6–9 weeks |
| Full lane through APH-6 | 10–15 weeks |

These are planning ranges, not evidence. The lane uses the following schedule
controls:

- finish and review one gate before widening the next;
- produce a runnable, inspectable, or generated artifact at least weekly;
- split any gate that spends two weeks without a reviewable increment;
- defer optional UI polish before deferring validation or safety;
- keep the MVP usable even if x64base self-hosting takes longer than expected.

## Definition of Done

The lane is complete when:

- task-specific packets can cold-start representative AI work;
- every jump resolves and explains its relevance;
- every technical claim identifies its authority and evidence;
- missing or contradictory truth is visible before action;
- registry content cannot silently grant mutation authority;
- x64base can curate and deterministically export the portal model;
- portal capabilities are teachable through DotTalk++ and proof artifacts;
- public material remains a reviewed derivative of source and runtime truth.

## Immediate Work Queue

1. Preserve the current lane state and establish baseline tests.
2. Define the v1 node and edge schema.
3. Convert a narrow engine-feature path into the first typed graph fixture.
4. Compile the first read-only context packet.
5. Compare that packet with the existing static assimilation reading path.
