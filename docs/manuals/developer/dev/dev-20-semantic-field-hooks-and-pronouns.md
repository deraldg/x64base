# DEV-20 Semantic Field Hooks and PRONOUNS Design

```yaml
page_id: DEV-20
title: Semantic Field Hooks and PRONOUNS Design
status: DESIGN_LANE_NOT_RUNTIME_CLAIM
last_verified: 2026-07-08
```

## Purpose

This chapter records a proposed x64base field-extension lane for semantic field
hooks such as `PRONOUNS`. It is not a claim that the runtime currently supports
a first-class `P` or `G` DBF field type.

The design belongs beside the current field validation work:

- `include/xbase.hpp` currently exposes the runtime `xbase::FieldDef` as name,
  storage type, length, and decimals.
- `include/datatype_index.hpp` already has a semantic-resolution layer that can
  derive semantic type from DBF code, width, and decimals.
- `MULTIREP`, `REPLACE`, and `CALCWRITE` are the primary mutation surfaces that
  must stay strict and type-aware.
- `FIELDS`, `STRUCT`, `FIELDMGR`, SelfDoc, HELP, and CMDHELPCHK are the public
  inspection and documentation surfaces.

## Design Boundary

Do not add a new core DBF storage byte casually.

The safe starting point is:

```text
storage type: C
semantic role: PRONOUNS
metadata source: x64 field metadata / DDICT / FIELDMGR
runtime behavior: validator + normalizer + optional relationship hook
classic fallback: ordinary C field
```

This keeps classic DBF and VFP compatibility intact while allowing x64 DBF_64
metadata to carry richer field semantics.

## PRONOUNS Field Requirements

A PRONOUNS semantic field should support:

- empty value when not collected,
- normalized common sets such as `he/him`, `she/her`, and `they/them`,
- custom free text where the policy allows it,
- optional display formatting,
- SelfDoc/HELP text that states whether the field is free text, normalized, or
  restricted,
- import/export behavior that round-trips as character data when the target
  format lacks semantic metadata.

## SEX and PRONOUNS Relationship Options

The project should treat `SEX` and `PRONOUNS` as separate facts unless a schema
or metadata rule says otherwise.

Recommended progression:

1. Independent fields: `SEX` and `PRONOUNS` coexist with no runtime coupling.
2. Advisory relation: metadata says `PRONOUNS` is related to `SEX`, but the
   runtime only suggests or warns.
3. Default-on-empty: changing `SEX` may populate `PRONOUNS` only when PRONOUNS
   is empty and the policy allows conventional defaults.
4. Strict validation: only for a dataset or application that explicitly opts in.
5. Composite semantic field: future x64-only design, not a compatibility
   baseline.

Changing `PRONOUNS` should not automatically rewrite `SEX`.

## Strategy / Registry Shape

The attached proposal points toward a Strategy + Registry design. A compatible
x64base version should avoid replacing `xbase::FieldDef` directly. Instead,
layer semantic behavior beside it:

```text
xbase::FieldDef
  -> field semantic resolver
  -> optional field behavior strategy
  -> validation / normalization / display policy
  -> mutation surface integration
```

Candidate strategy responsibilities:

- `name()`
- `validate(value)`
- `normalize(value)`
- `format_for_display(value)`
- `on_related_field_changed(related_field, new_value, current_value)`

Candidate registry responsibilities:

- register semantic handlers,
- resolve handlers from x64 metadata or DDICT/FIELDMGR rows,
- expose handler identity to SelfDoc and HELP,
- keep classic/VFP fallback as normal character storage.

## Mutation-Surface Gate

Any implementation must prove behavior across:

- `REPLACE`,
- `MULTIREP`,
- `CALCWRITE`,
- table buffering on/off,
- stale/dirty field reporting,
- CSV import/export,
- DBF flavor downgrade/export,
- `FIELDS` and `STRUCT`,
- SelfDoc/manual generation.

The mutator rule is strict: no semantic-field hook may silently coerce or
truncate a value after validation has failed.

## Documentation Gate

Before a public website or manual claims PRONOUNS support, the lane needs:

- source location for the handler or metadata resolver,
- HELP topic,
- FIELDMGR/STRUCT readback,
- mutation proof,
- import/export proof,
- fallback behavior proof for classic/VFP targets,
- SelfDoc or manualgen extraction row.

Until then, website/manual language should say `planned semantic field hook` or
`design lane`, not `implemented field type`.

## Domain Note

Domain notes such as `dottalk.com`, `dottalkpp.com`, and `derald.com` belong in
the website/domain-governance lane. Do not publish ownership claims from WHOIS
or parking-page observations unless they are verified by the project owner.

