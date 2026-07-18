# Reference Identity Authority Contract V1

Status: active governance contract  
Authority map: `selfdoc/reference_identity_authority_v1.json`  
Validator: `tools/selfdoc/validate_reference_identity_authority.py`  
Run: `DOCFLUSH-20260716-001`

## Purpose

This contract gives commands, subcommands, functions, arguments, and entry
variants stable identities while preserving the different authority roles of
runtime reflection, source catalogs, reference headers, usage contracts, HELP,
metacollect, joined inventories, and CMDHELPCHK.

It is an identity and provenance contract. It does not rebuild HELP, change
runtime registration, rewrite source contracts, or load metadata candidates.

## Authority Order

```text
Runtime execution proves reachability and behavior.
Source registries and catalogs define accepted tokens and canonical entities.
Source usage/function contracts define documentary semantics.
Reference headers define curated and compatibility-facing names.
HELP explains reviewed projections.
Metacollect organizes candidate rows.
Joined inventories preserve cross-layer evidence.
CMDHELPCHK validates agreement.
```

No downstream layer may silently replace a stronger authority. Disagreement
produces a review row carrying both values and their evidence.

## Canonical Entity Keys

All identity components are trimmed, converted to uppercase, and have internal
whitespace collapsed to one ASCII space. Spaces are not removed from canonical
names. Compact forms such as `SETORDER` remain entry variants of `SET ORDER`.

| Entity | Stable identity |
| --- | --- |
| command | `CMD:{canonical_name}` |
| subcommand | `SUBCMD:{parent_command}::{name}` |
| function | `FN:{canonical_name}` |
| argument | `ARG:{owner_kind}:{owner_name}:{kind}:{arg_name}` |
| entry variant | `ENTRY:{kind}:{token}->{canonical_command}` |

Entity namespaces are mandatory. A command and function with the same display
name are different identities.

## Command Identity

The source command catalog or accepted command-family contract defines the
canonical command name. The static/extension registry defines accepted input
tokens and handlers. Runtime proves whether a token reaches an implementation.

Reference-header names are curated documentation or compatibility evidence;
their presence alone does not prove runtime registration. CMDHELP builds a HELP
projection and cannot create a new runtime command by writing a row.

## Function Identity

The function catalog defines the canonical function name and curated
documentation. Builtin runtime specifications prove callable registration and
runtime arity. If `FunctionDoc` and builtin arity differ, both values are
retained and validation reports the mismatch.

`FUNC_ID` remains a metadata projection. The stable logical identity is
`FN:{canonical_name}`.

## Argument Identity

Arguments are owned entities. `ARG_NAME` alone is never globally unique.

The collision-safe key includes:

```text
owner_kind + owner_name + argument kind + argument name
```

For command arguments, usage contracts define names, shapes, requiredness, and
repeatability; runtime parser behavior and tests prove acceptance. Function
arity belongs to function runtime specifications and is not inferred from
command usage syntax.

Current `ARG_<OWNER>_<NAME>` values remain legacy metadata projection ids. They
do not include argument kind. The current candidate has no collisions, but
future writers must detect collisions before emitting or loading a legacy id.
Changing the live `ARG_ID` format requires a separate schema/promotion gate.

## Subcommands and Entry Variants

A subcommand is keyed by its canonical parent plus subcommand name. An entry
variant is a relationship from an accepted token to a canonical command and
must retain its kind: alias, shortcut, or reexpression.

Aliases are not duplicate canonical commands. Reexpressions such as compact SET
forms do not authorize collapsing canonical spaces.

## Field-Level Rules

- `implemented` and `dispatch_reachable`: runtime proof;
- canonical name and handler mapping: source catalog/registry definition;
- aliases and entry variants: source mapping, runtime validated;
- syntax, examples, summary, notes, and warnings: source contracts/catalogs;
- function min/max arity: builtin runtime specs, catalog agreement required;
- command argument required/repeatable/value shape: source usage contract,
  runtime/test validation when available;
- display name and locale: metadata/HELP projection, never identity;
- HELP topic/text: HELP authority, linked to but not defining runtime identity;
- generated ids: deterministic projection of the canonical logical key;
- provenance: every merged value carries source, authority class, and evidence
  hash or path.

The machine-readable authority map gives the precise order for each field
group.

## Merge and Conflict Rules

1. Normalize keys, not documentary payload.
2. Preserve every contributing authority and evidence path.
3. Do not use “last writer wins.”
4. Do not infer runtime reachability from a ref header or HELP row.
5. Do not infer canonical identity from a generated metadata id.
6. Emit `REVIEW_AUTHORITY_CONFLICT` when authoritative values disagree.
7. Emit `STALE_EVIDENCE` when a recorded input hash changes.
8. Require explicit alias/reexpression review before merging lexical names.

## Current Evidence Checkpoint

The accepted DOCFLUSH candidates currently contain:

- 331 joined reference identities, with zero duplicates and zero normalization
  violations;
- 65 function candidates, with zero canonical-name or `FUNC_ID` duplicates;
- 221 standard argument candidates, with zero logical-key duplicates, zero
  legacy `ARG_ID` duplicates, and zero cross-shape legacy-id collisions.

These counts are evidence, not timeless schema guarantees.

## Change Procedure

1. Update source/runtime authority first.
2. Refresh comments/usage evidence when applicable.
3. Rebuild HELP only through its protected gate.
4. Reharvest metadata candidates.
5. Run the identity authority validator.
6. Review conflict rows before any metadata or manual promotion.

This contract does not authorize any of those mutations.
