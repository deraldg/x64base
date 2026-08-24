# DEV-15 SelfDoc Pipeline

```yaml
page_id: DEV-15
title: SelfDoc Pipeline
status: DRAFT_PATCHED
last_verified: 2026-07-08
```

## Corrected pipeline

```text
source usage contracts / command registration / shared messages
  -> CMDHELP BUILD LEGACY (when dotref changes)
  -> CMDHELP BUILD . d:\code\ccode\src
  -> HELP DATA + legacy command catalogs
  -> META semantic catalogs where seeded
  -> CMDHELPCHK validation
  -> source / command / CMake verification sidecars
  -> runtime proof classification
  -> evidence binder
  -> diagrams / metadata crosswalks
  -> Developer Manual
  -> User Manual and Student Manual derivations
  -> Website derivations
```

This is still an assembly pipeline, not a truth-authority inversion.

The governing doctrine remains:

- runtime proves
- source defines
- HELP explains
- metadata organizes
- CMDHELPCHK validates
- SelfDoc preserves provenance
- manualgen assembles

## Pipeline manifests and policy homes

Current SelfDoc control artifacts already in-tree:

```text
selfdoc/pipeline_manifest.yaml
selfdoc/tool_manifest.yaml
selfdoc/SELFDOC_ARTIFACT_LIFECYCLE_POLICY_v0.md
selfdoc/SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0.md
```

These matter because SelfDoc is no longer just a loose idea. It has explicit
manifest and policy files that describe:

- pipeline stages
- helper-tool roles
- lifecycle classes
- safety classes
- non-mutation guards

## Manifested report-only doctrine

The current `selfdoc/pipeline_manifest.yaml` declares the metadata collection
pipeline as:

- active
- report-only
- default

Its reviewed stages include:

- `metacollect_facts_scan`
- `metacollect_compare_scan`
- `metacollect_sysfunc_candidate_export`
- `metacollect_sysargs_candidate_export`

And its non-mutation guards explicitly include:

- no DBF writes
- no HELP rebuild
- no CMDHELPCHK changes
- no source repairs
- no live metadata promotion
- review before import

That is the correct posture for SelfDoc.

## SelfDoc mission

SelfDoc exists to keep DotTalk++ from becoming three different realities: what source says, what HELP says, and what runtime does.

The current system extends that rule upward:

- source/runtime own behavior truth
- HELP and reference layers explain and reflect that truth
- META organizes semantic crosswalks where seeded
- manuals and website prose derive from the same evidence spine

The website is not an authority override for runtime/manual truth. It is an
attached publication lane that should harvest from the same evidence stack.

## Verified operator sequence

Verified on 2026-07-07:

```text
CMDHELP BUILD LEGACY
CMDHELP BUILD . d:\code\ccode\src
CMDHELPCHK
```

Observed result:

- legacy compatibility layer refreshed
- current HELP DATA incorporated `REGISTRY`, `DOTREF`, `FOXREF`, `EDREF`,
  `SHARED_MSG`, `SOURCE_MINER`, and `USAGE_CONTRACT`
- structural validation passed
- external metadata helpers remained outside live HELP/META authority

## Lifecycle and safety classes

The current SelfDoc artifact policy defines these lifecycle classes:

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

And these safety classes:

```text
READ_ONLY
REPORT_ONLY
PLAN_ONLY
PROJECTION_WRITER
PATCH_WRITER
MUTATION_TOOL
```

Current SelfDoc build work is intentionally constrained to the safe/reporting
end of that range. This is the project's defense against documentation lanes
quietly mutating runtime truth.

## Authority rule

Within the SelfDoc pipeline, authority flows in this order:

1. runtime behavior
2. source implementation and source usage contract
3. HELP/reflection/reference output
4. META semantic organization where seeded
5. manual and website prose

If upper layers disagree with lower layers, the upper layer is wrong until it is
repaired.

## External tool intake rule

SelfDoc now has an explicit rule for external programs.

External tools:

- may assist
- may harvest
- may compare
- may emit candidate CSVs or reports
- are not authority by default

`metacollect` is the model case:

- it is a read-only source/catalog scanner
- it normalizes future metadata candidates
- it emits facts, compare reports, and import candidates
- it does not replace live metadata DBFs
- it does not rebuild HELP
- it does not replace `CMDHELPCHK`
- it does not publish manuals

So the larger family is:

```text
source/runtime/help
  -> metacollect (read-only normalize/compare/propose)
  -> reviewed import candidates
  -> live metadata DBFs
  -> SelfDoc / manualgen / diagram promotion lanes
```

This is the right shape because it keeps proposal tooling separate from live
authoritative mutation.

## Practical consequences

When working in SelfDoc:

- inventory first
- classify second
- promote third
- automate fourth
- mutate only after explicit review

That rule is already written into the artifact lifecycle policy and should stay
visible in the manual because it governs how we grow the system without losing
authority discipline.

## MANUALCHK relationship

MANUALCHK is planned. CMDHELPCHK validates command/help/reflection congruence. MANUALCHK should later validate manual/evidence congruence.

## Current bridge to manualgen

SelfDoc does not replace manualgen and manualgen does not replace SelfDoc.

Current relationship:

- SelfDoc preserves provenance, manifests, probes, and evidence governance
- manualgen consumes reviewed evidence to assemble manual inventories,
  validation reports, manifests, and publication workspaces

The manual/website layer should therefore consume from SelfDoc-governed
evidence, not invent a parallel prose-only truth.
