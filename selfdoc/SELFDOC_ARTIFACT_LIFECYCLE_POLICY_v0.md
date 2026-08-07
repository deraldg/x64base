# SELFDOC_ARTIFACT_LIFECYCLE_POLICY_v0

Status: PLAN_ONLY  
Safety class: REPORT_ONLY / PLAN_ONLY  
Project root: `D:\code\ccode`  
Runtime/data/docs subtree: `dottalkpp\`  
Date: 2026-05-14

## Purpose

This policy defines how SelfDoc classifies project artifacts before cleanup, promotion, deletion, archival, or automation.

Core doctrine:

```text
Misc is not the enemy.
Unclassified misc is the enemy.
```

Build doctrine:

```text
Inventory first.
Classify second.
Promote third.
Automate fourth.
Mutate only after explicit review.
```

This policy does not move files, delete files, write DBFs, repair source contracts, rebuild HELP DATA, regenerate diagrams, or modify CMDHELPCHK.

## Baseline

Completed SelfDoc phases:

```text
SelfDoc tooling bootstrap: GREEN
Source contract inventory: GREEN
Source contract inventory review: GREEN
Source contract classifier tuning: GREEN
Source contract extension vocabulary v1.1: GREEN
Source contract classifier update draft v1.1: GREEN
```

Current confirmed source-contract baseline:

```text
Records reviewed: 899
Previous broad escrow candidates: 899
Actionable missing command/help usage contracts: 2
Accepted existing command contracts after v1.1 draft: 102
Existing command contracts needing shape review after v1.1 draft: 73
Remaining distinct unrecognized fields after v1.1 draft: 70
```

The two actionable missing command/help usage-contract candidates remain:

```text
src\cli\cmdhelp.cpp
src\cli\shell_commands.cpp
```

No mutation is authorized by this policy.

## Artifact lifecycle classes

SelfDoc adopts these lifecycle classes:

```text
CANONICAL
GENERATED
EVIDENCE
PROBE
CANDIDATE
PROMOTED
ATTIC
TRANSIENT
NOISE
QUARANTINE
```

Each artifact should eventually have one lifecycle class, a lane, a safety class, and a recommended next action.

## Class rules

### CANONICAL

Source-of-truth artifacts such as source files, include files, human-authored docs, schema definitions, metadata table definitions, and curated HELP/reflection catalogs.

Rules:

```text
Never silently mutate.
Change only by explicit handoff or reviewed patch.
Generated reports do not override canonical artifacts.
```

### GENERATED

Reproducible outputs such as generated reports, diagrams, patches, and evidence files.

Rules:

```text
May be overwritten by reruns only when the generator is known.
Must declare generator or report source.
Must not be mistaken for canonical truth.
```

### EVIDENCE

Runtime/probe proof snapshots that support decisions.

Rules:

```text
Keep when tied to a decision.
Expire when obsolete and not referenced.
Must identify date, command/probe, and decision supported when practical.
```

### PROBE

Exploratory script or report used to inspect the system.

Rules:

```text
Read-only or report-only by default.
Cannot become a dependency until promoted.
Must declare safety class, inputs, and outputs.
```

### CANDIDATE

Reusable artifact not yet stable.

Rules:

```text
May be refined.
Must declare intended lane and safety class.
Must not be treated as active pipeline dependency.
```

### PROMOTED

Governed tool, pipeline, or document.

Rules:

```text
Must be registered in manifest.
Must declare inputs, outputs, safety class, and rerun policy.
Must have known failure behavior.
```

### ATTIC

Preserved history that is not active.

Rules:

```text
Kept for reference.
Not part of active pipeline.
Must not be imported or executed by promoted tools unless explicitly restored.
```

### TRANSIENT

Temporary development byproduct.

Rules:

```text
Allowed to pass through controlled tmp/out lanes.
May expire.
Should not be referenced as durable evidence unless promoted.
```

### NOISE

Ignored material without continuing value.

Rules:

```text
Do not chase manually.
Only promote if repeated patterns reveal value.
Must not distract from build lanes.
```

### QUARANTINE

Suspicious, unsafe, malformed, or ambiguous artifact.

Rules:

```text
Review before promotion, deletion, or mutation.
Prefer quarantine over guessing.
Do not execute quarantined scripts.
```

## Safety classes

```text
READ_ONLY          Reads files/state only; writes nothing.
REPORT_ONLY        Reads files/state and writes approved reports.
PLAN_ONLY          Writes planning/control artifacts only.
PROJECTION_WRITER  Writes derived non-canonical projections.
PATCH_WRITER       Writes patch proposals but does not apply them.
MUTATION_TOOL      Mutates source/data/runtime state; forbidden until explicitly approved.
```

Current allowed classes for SelfDoc build work:

```text
READ_ONLY
REPORT_ONLY
PLAN_ONLY
```

## Approved roots and lanes

Project root:

```text
D:\code\ccode
```

Source/tooling lanes:

```text
src\
include\
selfdoc\
```

Runtime/data/docs subtree:

```text
dottalkpp\
```

Generated output homes:

```text
dottalkpp\docs\generated\reports
dottalkpp\docs\generated\diagrams
dottalkpp\docs\generated\patches
dottalkpp\docs\generated\evidence
```

SelfDoc active and inactive lanes:

```text
selfdoc\probes
selfdoc\attic
```

## Promotion and retention rules

A probe may be promoted only when:

```text
It has stable inputs.
It has stable outputs.
It declares safety class.
It is deterministic enough for review.
It has known failure behavior.
It has a reviewed sample output.
It is registered in a manifest.
It does not exceed its safety class.
```

A generated artifact may become evidence when it supports a decision or closure record and has enough provenance context.

A candidate may become canonical only through explicit human review and a patch/handoff.

An artifact may move to attic only after it is superseded, not part of active pipeline, and the move is planned and reviewed.

No automatic deletes are authorized by this policy.

## Classification outputs

Future lifecycle inventory reports should produce at least:

```text
path
lifecycle_class
lane
safety_class
owner_or_subsystem
generator_or_origin
active_status
recommended_action
reason
risk
```

Recommended actions:

```text
KEEP
PROMOTE_REVIEW
ATTIC_REVIEW
EXPIRE_REVIEW
QUARANTINE_REVIEW
CLASSIFY_MANUALLY
IGNORE
```

No recommendation should directly delete, move, or mutate.

## Decision gates

### Gate A -- Source Contract Classifier Stable

Open when v1.1 source contract probe is run and reviewed.

Allows shape review planning. Does not allow source repairs.

### Gate B -- Shape Review Complete

Open when remaining shape-review items are classified.

Allows repair patch planning. Does not allow automatic source edits.

### Gate C -- Artifact Lifecycle Policy Active

Open when this policy exists and first lifecycle inventory is run.

Allows misc classification and retention planning. Does not allow deleting or moving files.

### Gate D -- Crosswalk Reports Stable

Open when source contracts, help artifacts, and metadata presence reports can be combined.

Allows CMDHELPCHK v2 probe. Does not allow runtime CMDHELPCHK implementation.

### Gate E -- CMDHELPCHK v2 Probe Reviewed

Open when cmdhelpchk_v2_probe_report is useful and false positives are understood.

Allows runtime CMDHELPCHK v2 implementation handoff.

## Current next build order

```text
1. Promote v1.1 source-contract classifier into repeatable report-only probe mode.
2. Produce source contract shape-review plan.
3. Produce first artifact lifecycle inventory.
4. Produce help_artifacts summary probe after safe access method is agreed.
5. Produce metadata catalog presence probe.
6. Produce command help crosswalk probe.
7. Produce CMDHELPCHK v2 probe.
8. Only then plan repair patches.
```

## What this policy does not authorize

```text
source edits
DBF writes
HELP DATA rebuilds
CMDHELPCHK changes
source contract repairs
file moves
file deletes
diagram regeneration
data-root cleanup
automatic promotion of loose scripts
automatic attic moves
automatic quarantine moves
```

## Acceptance criteria

```text
selfdoc\SELFDOC_ARTIFACT_LIFECYCLE_POLICY_v0.md exists.
It defines lifecycle classes.
It defines safety classes.
It defines roots and output homes.
It defines promotion/retention rules.
It defines decision gates.
It preserves no-mutation boundaries.
It gives the next build order.
```

## AUTOLOG candidate

```text
Date: 2026-05-14
Subsystem: SelfDoc / artifact lifecycle policy
Files touched:
  selfdoc\SELFDOC_ARTIFACT_LIFECYCLE_POLICY_v0.md
Intent: Define lifecycle classes and retention/promotion rules before building more SelfDoc probes
Change: Added PLAN_ONLY policy covering canonical, generated, evidence, probe, candidate, promoted, attic, transient, noise, and quarantine artifact classes
Behavior preserved: No source edits; no DBF writes; no HELP DATA rebuild; no CMDHELPCHK changes; no file moves; no deletes
Tests: Policy file created and reviewed for scope boundaries
Result: Artifact lifecycle policy ready for review
Risks: Policy-only artifact; lifecycle inventory probe not implemented yet
Next recommended action: Implement source_contract_inventory_probe_v1_1 or first artifact lifecycle inventory, depending on preferred gate order
```
