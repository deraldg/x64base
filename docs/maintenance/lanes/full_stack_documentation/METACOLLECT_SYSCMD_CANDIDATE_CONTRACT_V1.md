# Metacollect SYSCMD Candidate Contract V1

Status: active source-defined candidate contract  
Owner: metadata / full-stack documentation  
Physical schema: `dottalkpp/data/schemas/metadata/syscmd_catalog.dtschema`  
Identity authority: `REFERENCE_IDENTITY_AUTHORITY_CONTRACT_V1.md`

## Purpose

This contract defines the report-only `metacollect` projection from active
static command registrations into a reviewable `SYSCMD` import candidate.
It does not authorize a metadata load, index rebuild, HELP mutation, or manual
publication.

## Output Shape

The candidate uses the reviewed physical field order exactly:

```text
CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE
```

Field lengths and types remain governed by `syscmd_catalog.dtschema`.
`CMD_ID` is the deterministic `CMD_` projection of the canonical command name;
the logical identity remains `CMD:{canonical_name}`.

## Authority And Merge Rules

1. Literal active registrations in the C++ command registry establish the
   dispatch inventory and handler evidence.
2. A source `@dottalk.usage v1` contract may supply the canonical spaced name,
   status, and explicit aliases.
3. Exact registered/contract names remain separate canonical commands even
   when the documentation catalog presents them as one command family.
4. A unique compact match may map a registry token such as `SETORDER` to the
   source-contract canonical name `SET ORDER`.
5. An explicit `aliases:` value maps the alias token to its contract command;
   a shared handler alone never proves an alias.
6. Duplicate registrations resolve deterministically in favor of the central
   `src/cli/shell_commands.cpp` registry and then stable source order.
7. Rows sort by `CAN_NAME`; repeated runs over unchanged source must be
   byte-identical.

## Classification And Exclusions

- `TYPE=syntax-command` is reserved for the reviewed control-flow command set;
  other rows use `TYPE=command`.
- Default rows use `VIS=public`.
- Source-classified developer/canary surfaces are excluded unless
  `--include-dev-commands` is supplied; included developer rows use
  `VIS=developer`.
- Punctuation-only registry tokens are entry variants and do not receive a
  duplicate canonical `SYSCMD` row.
- Dynamic registrations whose name is not a source literal require runtime
  reflection and remain outside this static candidate.
- HELP, generated reference output, old `SYSCMD` rows, and shared handler names
  may be comparison evidence but may not silently create or rename a row.

## Conflict Rule

When two source authorities disagree and neither exact-name, explicit-alias,
nor unique-compact resolution applies, retain the registered token as its own
candidate name and route the disagreement to review. Do not use last-writer
wins and do not infer an alias from handler equality.

## Validation And Promotion Boundary

The candidate must pass the focused validator for schema, field lengths,
allowed values, unique ids, unique canonical names, and static-registry
backing. Determinism is proved by two byte-identical emissions.

Any load into `dottalkpp/data/metadata/SYSCMD.dbf`, and any associated
CDX/LMDB work, requires a separate reviewed mutation gate with backup,
before/after readback, rollback evidence, and explicit maintainer authority.

