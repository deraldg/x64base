# SELFDOC_EXTERNAL_TOOL_INTAKE_POLICY_v0

Status: DRAFT  
Safety class: PLAN_ONLY / REPORT_ONLY  
Project root: `D:\code\ccode`

## Purpose

This policy explains two things:

- where `metacollect` fits in the DotTalk++ / x64base documentation workflow
- how an external program should be documented inside SelfDoc

Core doctrine:

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
External tools may assist, but they are not authority by default.
```

## Where `metacollect` fits

`metacollect` belongs in the metadata collection / proposal lane.

It is not:

- the live metadata DBF authority
- a HELP rebuild tool
- a `CMDHELPCHK` replacement
- a manual publisher

It is:

- a read-only source/catalog scanner
- a normalizer for future metadata rows
- a comparison tool between source evidence and persisted metadata
- a seed-artifact generator for controlled import review

## `metacollect` workflow role

The intended workflow is:

1. Source contracts, command catalogs, function catalogs, and runtime metadata exist.
2. `metacollect` scans those inputs without mutating them.
3. `metacollect` emits report or import-candidate artifacts such as:
   - fact CSVs
   - compare CSVs
   - canonical import CSVs for lanes like `SYSCMD`, `SYSFUNC`, `SYSARGS`
4. Human review decides whether a candidate should be promoted into live metadata.
5. DotScript/native import scripts perform the actual DBF/CDX/LMDB mutation later, under explicit authorization.

So in the larger family:

```text
source/runtime/help
  -> metacollect (read-only normalize/compare/propose)
  -> reviewed import candidates
  -> live metadata DBFs
  -> SelfDoc / manualgen / diagram promotion lanes
```

## What SelfDoc should do with `metacollect`

SelfDoc should treat `metacollect` as a documented helper tool with:

- a clear safety class
- declared inputs
- declared outputs
- rerun expectations
- known scope limits

SelfDoc should preserve:

- which source roots were scanned
- which filters were applied
- whether keyword arguments were included
- whether dev-only commands were excluded
- which CSVs were produced

## How to document an external program in SelfDoc

An external program should enter SelfDoc in four layers.

### Layer 1: Tool identity

Document the program in a tool manifest entry, at first as a candidate.

Minimum fields:

- tool id
- physical path or install path
- owner lane
- safety class
- lifecycle class
- role
- default status

For example, an external helper should begin life as one of:

- `PROBE`
- `CANDIDATE`
- `PROMOTION_SUPPORT`

not `CANONICAL`.

### Layer 2: Boundary declaration

State exactly what the tool may read and write.

Required boundary questions:

- Does it read source?
- Does it read DBFs?
- Does it read generated docs?
- Does it write reports only?
- Does it write candidate CSVs?
- Does it patch source?
- Does it mutate DBF/CDX/LMDB state?

If mutation is possible, the tool is not implicitly safe. It must stay non-default until explicitly authorized.

### Layer 3: Evidence outputs

SelfDoc should capture the outputs the tool creates.

Typical outputs:

- markdown report
- csv
- json
- patch proposal
- diagram candidate
- import candidate

Each output should be classed as:

- `GENERATED`
- `EVIDENCE`
- `CANDIDATE`

not canonical truth.

### Layer 4: Promotion rule

The tool needs a promotion gate:

- review completed
- outputs repeatable
- authority boundaries understood
- no accidental mutation
- report home stable

Only after that should it move from candidate to promoted support tooling.

## External program doctrine

External programs should usually land in one of these roles:

- report-only probe
- projection writer
- candidate importer/exporter
- maintenance cookbook helper

They should not become:

- direct replacements for runtime commands
- hidden schema authorities
- silent DBF mutation tools
- undocumented build dependencies

## Canonical pattern for external programs

For DotTalk++ / x64base, the preferred pattern is:

1. inventory the program in `selfdoc/tool_manifest_candidate...`
2. record its workflow step in `selfdoc/pipeline_manifest_candidate...`
3. classify it as `READ_ONLY`, `REPORT_ONLY`, or `PLAN_ONLY` unless explicit mutation is intended
4. store outputs under a stable report or candidate home
5. keep runtime/native authority separate

## Applying that rule to `metacollect`

`metacollect` should be documented as:

- lifecycle: promoted helper or promoted support tool
- safety class: `REPORT_ONLY` plus candidate CSV writer
- authority: noncanonical proposal lane
- outputs:
  - facts
  - compare reports
  - import candidates
- non-authority:
  - does not replace live metadata DBFs
  - does not replace HELP
  - does not replace `CMDHELPCHK`

## Beta/dev rule

Developer-only or unfinished command families may be excluded from canonical `metacollect` exports even if runtime registration exists.

Current example:

- `BETA`

That exclusion is a metadata-export policy decision, not proof that the runtime command does not exist.

## Summary

If the program is external, SelfDoc should first describe it as a governed helper, not as truth.

If the program is `metacollect`, its job is to harvest, compare, and propose.

If the output must change live metadata, that happens later through a reviewed promotion step, not inside SelfDoc discovery.
