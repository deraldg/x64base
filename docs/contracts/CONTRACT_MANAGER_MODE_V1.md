# DotTalk++ Contract Manager Mode v1

Status: source-defined first wave.

## Purpose

Define the appropriate manager surface for the contracts lane across `MAINT`,
`BBOX`, `DDICT`, `CMDHELPCHK`, SelfDoc, and future runtime commands.

## Recommendation

The primary manager mode should be:

```text
MAINT CONTRACTS
```

This keeps contract governance inside the existing read-only maintenance control
surface without prematurely creating another top-level runtime command.

## Surface Roles

| Surface | Role |
| --- | --- |
| `MAINT CONTRACTS` | Primary manager/inspector for contract lane status, scans, registry, intake, drift, and gates |
| `BBOX CONTRACTS` | Educational explanation of contracts as data-in/process/information-out lane |
| `DDICT` | Later table-backed metadata/query surface if contracts become catalog rows |
| `CMDHELPCHK` | Validator for command usage/HELP alignment, especially usage contracts |
| `CMDHELP`/`HELP` | User-facing explanation after command contracts are promoted |
| SelfDoc/manualgen | Provenance and publication path for contract evidence |
| future `CONTRACTS` | Optional alias or dedicated command only after `MAINT CONTRACTS` proves useful |

## Why MAINT Owns The Manager Mode

Contracts are governance/control artifacts. They touch source, usage, HELP,
metadata, database safety, GUI behavior, build policy, and publication evidence.
That makes them a maintenance lane rather than a data dictionary lane or an
educational lane.

`MAINT` is already the native read-only SDLC/maintenance inspection surface.
Adding `MAINT CONTRACTS` fits its purpose:

- inspect lanes,
- report status,
- expose boundaries,
- point to cookbooks,
- avoid mutation.

## Why BBOX Does Not Own It

`BBOX` should teach and explain:

```text
contract data in
  -> classify/register/validate/promote
  -> registry, reports, drift queues out
```

It should not be the operational manager. It is the conceptual model and
education surface.

Recommended BBOX form:

```text
BBOX CONTRACTS
```

## Why DDICT Does Not Own It First

`DDICT` is the data dictionary inspector. It is appropriate later if contracts
become table-backed metadata with entities, attributes, relationships, evidence,
and registry rows.

But the first contracts lane is broader than the data dictionary:

- source contracts,
- usage contracts,
- GUI contracts,
- safety contracts,
- build contracts,
- governance contracts,
- historical/superseded contracts.

Those should not be forced into DDICT before the contract model stabilizes.

DDICT can later expose:

```text
DDICT CONTRACTS
DDICT EVIDENCE CONTRACT <id>
DDICT REL CONTRACT <id>
```

Only after the catalog shape is accepted.

## Initial MAINT CONTRACTS Forms

Recommended first read-only command family:

```text
MAINT CONTRACTS
MAINT CONTRACTS USAGE
MAINT CONTRACTS STATUS
MAINT CONTRACTS SCAN
MAINT CONTRACTS REGISTRY
MAINT CONTRACTS INTAKE
MAINT CONTRACTS DRIFT
MAINT CONTRACTS GATES
```

Initial behavior:

- `MAINT CONTRACTS` defaults to `STATUS`.
- `SCAN` reports counts from `tools/contracts/contract_scan.py` or a native
  equivalent later.
- `REGISTRY` points to active registry and summary counts.
- `INTAKE` points to queued contract candidates.
- `DRIFT` reports discovered-but-unregistered and registered-but-undiscovered
  candidates once the scanner supports it.
- `GATES` lists promotion gates and next lane actions.

All first-wave forms are read-only.

## Mutation Policy

No first-wave manager command should mutate:

- source files,
- DBFs,
- HELP/CMDHELP,
- contract registry,
- intake queue,
- manual publications,
- metadata catalogs,
- build files.

Future mutation, if any, must use explicit guarded forms such as:

```text
MAINT CONTRACTS PLAN
MAINT CONTRACTS APPLY <approved-plan>
```

Those are deferred.

## Eventual Dedicated Command

A top-level command may be justified later:

```text
CONTRACTS
CONTRACTS STATUS
CONTRACTS SCAN
CONTRACTS DRIFT
```

Do not start there. Begin with `MAINT CONTRACTS` and optionally make
`CONTRACTS` an alias once the behavior is stable.

## Acceptance Criteria

The manager mode is minimally correct when:

- `MAINT CONTRACTS` is documented as the primary manager surface,
- `BBOX CONTRACTS` is documented as educational,
- DDICT is reserved for later table-backed catalog/query behavior,
- the contracts lane scanner has a read-only runtime-facing path,
- all first-wave forms are status/report-only.

## First Runtime Proof

The first source-defined implementation lives in:

- `src/cli/cmd_maint.cpp`
- `src/cli/cmd_bbox.cpp`

Implemented first-wave surfaces:

- `MAINT CONTRACTS`
- `MAINT CONTRACTS USAGE`
- `MAINT CONTRACTS STATUS`
- `MAINT CONTRACTS SCAN`
- `MAINT CONTRACTS REGISTRY`
- `MAINT CONTRACTS INTAKE`
- `MAINT CONTRACTS DRIFT`
- `MAINT CONTRACTS GATES`
- `BBOX CONTRACTS`

These are read-only report/explanation surfaces.
