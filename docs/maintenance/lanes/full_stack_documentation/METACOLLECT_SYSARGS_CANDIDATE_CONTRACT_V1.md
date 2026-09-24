# Metacollect SYSARGS Candidate Contract V1

Status: active source-defined candidate contract
Owner: metadata / full-stack documentation
Physical schema: NONE EXISTS -- see "Physical Schema Is Absent" below
Sibling contract: `METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md`
Validator: `tools/fullstack_docs/validate_sysargs_candidate.py`

## Purpose

This contract defines the report-only `metacollect` projection from
`@dottalk.usage v1` source contracts into a reviewable `SYSARGS` import
candidate. It does not authorize a metadata load, index rebuild, HELP
mutation, or manual publication.

**It exists because the SYSCMD contract's uniqueness clause covered the
artifact that was never at risk.** Gate 5 has checked unique `CMD_ID` and
unique `CAN_NAME` on every run since 2026-07-16, and both have always passed.
Nothing checked `ARG_ID`, and it has not been unique since at least
2026-08-05. Written 2026-09-24, from the finding in
`FINDING_ARG_ID_COLLAPSES_KEYWORD_AND_PLACEHOLDER_AND_THE_UNIQUENESS_CLAUSE_STOPS_AT_SYSCMD.md`.

## Output Shape

The candidate uses the emitted field order exactly:

```text
ARG_ID,OWNER_KND,OWNER_NAM,ARG_NAME,DEF_LOCALE,REGION_ID,ARG_KIND,VAL_SHAPE,REQUIRED,REPEAT,SRC_AUTH,SRC_FILE,ACTIVE,VER_AT,NOTES
```

`ARG_ID` is the deterministic projection `ARG_` + symbol(`OWNER_NAM`) + `_` +
`ARG_NAME`. Verified on all 1,180 rows of the 2026-09-24 candidate: zero
projection violations.

### Physical Schema Is Absent, And That Is Stated Rather Than Invented

`dottalkpp/data/schemas/metadata/` holds `syscmd_catalog.dtschema` and
`sysmsg_catalog.dtschema` and **no SYSARGS schema at all**. So this contract
declares no field widths: there is no reviewed authority to declare them from,
and inventing widths from one emit would create a second authority that the
first load would contradict. Observed maxima on 2026-09-24, as a FLOOR for
whoever writes the schema, not as a rule:

    ARG_ID 41   OWNER_NAM 15   ARG_NAME 32   SRC_FILE 32   NOTES 639

NOTES at 639 characters is the one that decides a memo field.

*(Noted in passing: both existing `.dtschema` files are UNTRACKED. The SYSCMD
contract names `syscmd_catalog.dtschema` as its physical schema authority and
that file is not in git. Not this contract's business to fix, but a reader
should know before treating it as reviewed.)*

## Reserved Values

Each of these is read off the emitter, not off one emit. Widening a set is a
change to this contract and to `metacollect.cpp` together.

    OWNER_KND   {command}
    ARG_KIND    {keyword, placeholder}
    SRC_AUTH    {usage_contract_v1}
    ACTIVE      true
    REQUIRED    {true, false}
    REPEAT      {true, false}
    VAL_SHAPE   keyword rows     -> literal, always
                placeholder rows -> expression, field-name, file-path,
                                    integer, locale-code, name, path,
                                    predicate, table-ref, value
                (metacollect.cpp infer_shape_from_placeholder; the keyword
                 branch assigns "literal" unconditionally)

`VAL_SHAPE` must agree with `ARG_KIND` in both directions: no keyword row
carries a placeholder shape, no placeholder row carries `literal`. Verified
on all 1,180 rows: zero violations in either direction.

## Authority And Merge Rules

1. Rows derive ONLY from `@dottalk.usage v1` source contracts. `SRC_AUTH` is
   `usage_contract_v1` on every row and `SRC_FILE` names the file the contract
   was mined from. Every `SRC_FILE` in the 2026-09-24 candidate exists in the
   tree.
2. Every `OWNER_NAM` must have a row in the SYSCMD candidate from the SAME
   emit. Verified: 151 owners, 231 SYSCMD rows, **zero orphan owners**. This is
   the SYSARGS counterpart of SYSCMD's static-registry backing clause, and it
   is the "would an import orphan anything" question one level down.
3. Rows are grouped by `OWNER_NAM` in non-decreasing order. The order WITHIN an
   owner is the emitter's aggregation order and is NOT sorted by `ARG_NAME`;
   98 of 151 owners are unsorted within themselves. Do not gate a sort that the
   emitter does not perform -- byte-identity across re-emissions is what makes
   the order citable, not alphabetization.
4. Repeated runs over unchanged source must be byte-identical. Proven
   2026-09-24: two emits from the same binary, and emits from three separate
   binaries (host MSVC twice, g++ 11.4 once), all byte-identical.

## THE CLAUSE THIS CONTRACT WAS WRITTEN FOR

**`ARG_ID` must be unique across the candidate.**

It is not, today, and the validator is expected to FAIL saying so:

    2026-08-05    959 rows,   950 distinct ARG_ID,   9 collisions
    2026-08-26   1066 rows,  1054 distinct ARG_ID,  12 collisions
    2026-09-24   1180 rows,  1166 distinct ARG_ID,  14 collisions

    SYSARGSCHK FAIL rows=1180 findings=14

Run against all three archived candidates, the validator reports those counts
and **nothing else** -- every other clause above passes on seven weeks of
emitted data. The one thing that fails is the one defect.

The cause is two lines apart in the emitter: the row is aggregated on
`command|arg_kind|arg_name` and the id is written as `ARG_<command>_<arg_name>`.
Three components in the key, two in the id. A command whose own usage text uses
one word in both roles -- `SET PATH` the literal and `<path>` the placeholder,
`USER ... KEY` and `<key>` -- emits two legitimate, DIFFERENT rows under one id.

**Do not loosen this clause to make a gate green.** A red Gate 5 on SYSARGS is
this contract working. It goes green when either remedy lands:

1. include `arg_kind` in the emitted id so the id matches the aggregation key
   (`metacollect.cpp`, one line) -- this renames rows, so it is a candidate
   schema change and this contract must be revised with it; or
2. the usage text itself stops using one word in two roles, which is a source
   change and unlikely to be worth it.

Until then the fourteen are a KNOWN, MEASURED, NAMED state, which is a
different thing from an unchecked one.

## Validation And Promotion Boundary

    python tools/fullstack_docs/validate_sysargs_candidate.py <candidate.csv> \
        --repo-root . --syscmd-candidate <SYSCMD_IMPORT_candidate_v1.csv>

Unit tests: `tools/fullstack_docs/tests/test_validate_sysargs_candidate.py`,
8 cases, including the real `ARG_SET_PATH` pair as a regression.

Any load into `dottalkpp/data/metadata/SYSARGS.dbf`, and any associated
CDX/LMDB work, requires a separate reviewed mutation gate with backup,
before/after readback, rollback evidence, and explicit maintainer authority.
The live table holds 249 rows against a candidate of 1,180 -- 21% -- so the
first real load is a large one, and it is the load that would hit the
collisions.
