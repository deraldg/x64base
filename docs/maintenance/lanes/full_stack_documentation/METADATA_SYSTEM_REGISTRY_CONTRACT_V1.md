# Metadata System Registry Contract V1

Status: active governance contract  
Registry: `selfdoc/metadata_system_registry_v1.json`  
Validator: `tools/selfdoc/validate_metadata_system_registry.py`  
Authority root: `D:\code\ccode`

## Purpose

The metadata system registry identifies stable collectors, harvesters,
reflection layers, validators, candidate emitters, readers, and protected
mutators without collapsing their authority boundaries into a generic
“metadata” category.

Registration is descriptive. It does not execute a system, accept its output,
authorize mutation, or promote candidate data.

## Authority Rule

```text
Runtime proves.
Source defines.
HELP explains.
Metadata organizes.
CMDHELPCHK validates.
SelfDoc preserves provenance.
Manualgen assembles reviewed views.
Publication exposes reviewed snapshots.
```

A registered system may own one stage or evidence type. It does not acquire the
authority of its dependencies or consumers.

## Required Registry Fields

Every system row must declare:

- stable `system_id` and human-readable `name`;
- one or more canonical repository entrypoints;
- role, authority domain, and authority class;
- mutation class and protected targets;
- lifecycle and owning lane;
- authoritative inputs and produced outputs/evidence;
- dependencies and overlapping systems;
- SHA-256 of the primary entrypoint;
- last verified run id and date;
- SelfDoc tool-manifest mapping, when present;
- default execution and promotion authorization states.

## Mutation Classes

| Class | Meaning |
| --- | --- |
| `READ_ONLY` | Reads state and writes nothing. |
| `REPORT_ONLY` | Writes bounded reports/evidence only. |
| `CANDIDATE_WRITER` | Writes isolated, non-promoted candidate artifacts. |
| `IN_MEMORY_ONLY` | Builds runtime state without persistent output. |
| `PROJECTION_WRITER` | Writes a derived, non-authoritative projection. |
| `PROTECTED_HELP_MUTATOR` | Writes protected HELP data under a separate gate. |
| `PROTECTED_STORAGE_MUTATOR` | Writes protected storage/index metadata under a separate gate. |
| `HELPER_ONLY` | Returns metadata to its caller; the caller owns persistence. |

Protected mutators must name protected targets. No registry row may enable
default execution or claim promotion authority.

## Lifecycle Classes

- `ACTIVE`: current stable system;
- `SUPPORTING`: current downstream adapter, joiner, or projection helper;
- `PROTOTYPE`: bounded system still under contract or stabilization review;
- `HISTORICAL`: retained evidence or superseded implementation;
- `UTILITY`: narrow application helper without pipeline authority.

Historical rows remain registered so older evidence can be interpreted. They
must not be treated as current defaults.

## Source Hash Rule

`source_sha256` is the SHA-256 of the first path in
`canonical_entrypoints`. Validator failure indicates registry drift, not
automatic source fault. Hash drift routes to `STALE_EVIDENCE` review.

## Dependency and Overlap Rule

Dependencies and overlaps use registry system ids. A dependency describes an
input or execution relationship. An overlap describes systems that observe or
represent some of the same facts but have different roles.

No overlap may be resolved by silently selecting one authority. The owning
contract must define the role split.

## SelfDoc Integration

`selfdoc/tool_manifest.yaml` remains the reviewed operational tool subset.
`selfdoc/pipeline_manifest.yaml` remains the reviewed pipeline subset. Both
point to this cross-domain registry.

The system registry is broader: it includes native runtime components,
protected mutators, supporting readers, and historical tools that should never
be made default merely because they are inventoried.

## Validation

The validator checks:

- schema, required fields, and enum values;
- unique and well-formed ids;
- canonical entrypoint existence and primary hash;
- dependency/overlap referential integrity;
- protected-target declarations for mutators;
- default-execution and promotion gates;
- SelfDoc tool-manifest mappings;
- source inventory path and hash.

The validator prints findings and optionally JSON to standard output. It does
not rewrite the registry or any protected artifact.

## Change Procedure

1. Mine or review the implementation and authority boundary.
2. Add or revise the registry row with current source hash.
3. Run the validator and focused unit tests.
4. Record the change in the active documentation run.
5. Review execution or promotion separately if either is desired.

Registry validation is never a substitute for runtime proof, regression tests,
HELP validation, COMMENTS review, or a protected mutation gate.
