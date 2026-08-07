# SelfDoc Collection Imperfection Policy v0

Status: POLICY / PLAN_ONLY  
Safety class: PLAN_ONLY  
Mutation authorization: CLOSED

## 1. Purpose

SelfDoc exists to make DotTalk++ easier to observe, classify, review, and maintain.

SelfDoc is not an oracle. It is an observability and classification system.

Its job is to surface likely states, likely drift, likely defects, and likely maintenance work with evidence, confidence, and review gates.

This policy prevents SelfDoc from treating every finding as a source defect and prevents report-only classification from becoming unreviewed mutation.

## 2. Core doctrine

```text
SelfDoc reports are evidence, not verdicts.
```

A SelfDoc finding may represent any of the following:

```text
real source defect
classifier vocabulary gap
capture/parser limitation
stale inventory
source mutation since last scan
intentional architecture exception
policy decision pending
human-review item
```

A report may recommend review or future action. It does not authorize source mutation by itself.

## 3. Collection imperfection rule

SelfDoc collection systems are allowed to be imperfect.

The system must distinguish between source defects, classifier limitations, capture/parser limitations, stale evidence, policy gaps, and intentional architecture exceptions.

Misclassification is treated as normal maintenance input when it is visible, classified, repeatable, and non-mutating.

The unacceptable states are:

```text
silent drift
unexplained mutation
unreviewed repair
tools that collapse uncertainty into false certainty
```

## 4. Required uncertainty lanes

SelfDoc reports should classify uncertain findings into explicit lanes:

```text
CONFIRMED
LIKELY
STALE_EVIDENCE
CLASSIFIER_REVIEW
CAPTURE_REVIEW
POLICY_REVIEW
SOURCE_REVIEW
INTENTIONAL_EXCEPTION
DO_NOT_REPAIR
```

The lane is part of the finding. It should not be hidden in prose only.

## 5. Required evidence fields

Where practical, every SelfDoc report should carry:

```text
status
confidence
evidence hash
source timestamp/hash basis
recommended next action
mutation authorization state
```

For source-contract reports, this usually means:

```text
source path
header hash
capture hash
capture strategy
marker position
source read status
classification lane
confidence
repair authorization state
```

## 6. Mutation authorization rule

```text
NO_AUTO_REPAIR_FROM_CLASSIFICATION_ONLY
```

A classifier may recommend. It cannot authorize source mutation by itself.

Source edits require a separate, explicit approval step after:

```text
evidence review
classification review
policy review when needed
patch proposal review
mutation authorization
```

A report-only or plan-only tool must not quietly become a mutation tool.

## 7. Capture/parser findings

Capture/parser limitations are first-class SelfDoc findings.

If a report says a contract is malformed, SelfDoc must be able to distinguish:

```text
source header is actually malformed
scanner captured too much
scanner captured too little
marker was not treated as payload start
preamble was treated as contract payload
inventory hash is stale
source changed after inventory
```

Capture/parser findings should generally route to:

```text
CAPTURE_REVIEW
CLASSIFIER_REVIEW
STALE_EVIDENCE
```

not directly to source repair.

## 8. Stale evidence rule

A mismatch between an inventory hash and the current source hash is not automatically a source defect.

It may mean:

```text
the source changed since the report was generated
the capture algorithm changed
the report was generated from stale output
line endings or decoding changed
the inventory was not refreshed after a probe update
```

Hash mismatch should route to:

```text
STALE_EVIDENCE
```

until explained.

## 9. Intentional architecture exception rule

DotTalk++ has architecture-bearing files that are not ordinary command surfaces.

Examples include:

```text
shell.cpp
shell_commands.cpp
helpdata_cmdhelp_bridge.cpp
xexpr/function.hpp
```

SelfDoc must model these as architecture roles rather than forcing them into simple command-contract repair lanes.

Possible lanes include:

```text
selfdoc.cli_shell_contract
selfdoc.command_registry_contract
selfdoc.help_metadata_engine_contract
selfdoc.function_contract
selfdoc.api_contract
```

## 10. Confidence scale

Reports should prefer explicit confidence over binary pass/fail.

Recommended confidence values:

```text
HIGH
MEDIUM
LOW
NONE
```

Use `NONE` when the tool could not read required evidence.

## 11. Recommended next-action vocabulary

Recommended next actions should be concrete and non-mutating unless mutation is explicitly authorized.

Examples:

```text
rerun inventory
refresh evidence
review classifier vocabulary
review capture boundary
classify as intentional exception
prepare patch proposal
hold for policy decision
do not repair
```

Avoid vague outcomes such as:

```text
fix it
bad
broken
needs cleanup
```

unless paired with evidence and a review lane.

## 12. Current SelfDoc application

The capture-hotfix validation showed why this policy is needed.

Batch 0 initially looked like a source repair pool. Later evidence showed:

```text
source_repair_needed: 0
classifier_capture_fix_likely: 9
inventory_refresh_needed: 1
```

The correct conclusion was not source repair. The correct conclusion was capture/classifier review plus stale-evidence handling.

That is the intended SelfDoc behavior.

## 13. Current operating rule

Do not chase perfect classification before the system is useful.

Build repeatable classification with reviewable uncertainty.

For v1.1, the goal is not to make every remaining field or shape-review item disappear before proceeding. The goal is stable buckets, confidence levels, clear evidence, and mutation gates.

## 14. Non-mutation guarantees for this policy

This policy does not authorize:

```text
source edits
DBF writes
HELP DATA rebuilds
CMDHELPCHK changes
source contract repairs
file moves
file deletes
v1.1 default promotion
selfdoc runner creation
```

## 15. Acceptance criteria

This policy is accepted when:

```text
1. SelfDoc reports are treated as evidence, not verdicts.
2. Misclassification is treated as maintenance signal, not failure.
3. Capture/parser limitations are separate from source defects.
4. Stale evidence is a first-class lane.
5. Intentional architecture exceptions are modeled explicitly.
6. No classifier-only report can authorize source mutation.
7. Future probes include status, confidence, evidence basis, next action, and mutation authorization state where practical.
```

## 16. AUTOLOG candidate

```text
Date: 2026-05-16
Subsystem: SelfDoc / operating doctrine
Files touched:
  selfdoc\SELFDOC_COLLECTION_IMPERFECTION_POLICY_v0.md
Generated reports:
  dottalkpp\docs\generated\reports\selfdoc_collection_imperfection_policy_v0.md
Intent: Add an explicit policy that SelfDoc reports are evidence, not verdicts, and that collection/capture/classification imperfections must be visible and review-gated rather than converted into automatic source repair
Change: Added a PLAN_ONLY policy artifact defining uncertainty lanes, evidence fields, stale-evidence handling, capture/parser review lanes, intentional architecture exceptions, and NO_AUTO_REPAIR_FROM_CLASSIFICATION_ONLY
Behavior preserved: No source edits; no DBF writes; no HELP DATA rebuild; no CMDHELPCHK modification; no source contract repairs; no file moves/deletes; no v1.1 default promotion; no runner creation
Tests: Policy file generated and scope reviewed
Result: SelfDoc collection imperfection doctrine ready for review
Risks: Policy-only artifact; future probes still need to adopt the lanes/fields consistently
Next recommended action: Continue with capture-hotfix validation/fix work, using the new uncertainty lanes and mutation gates
```

