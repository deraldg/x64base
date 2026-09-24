# Finding: ARG_ID collapses keyword and placeholder, and the uniqueness clause stops at SYSCMD

    Found     : 2026-09-24, DOCFLUSH-20260924-001 Gate 5, while accounting for
                SYSARGS +114 -- not while looking for this.
    Evidence  : source-evidenced (metacollect.cpp) + runtime-proven on Linux
                (g++ 11.4 emit, byte-identical to the host MSVC emit) and on
                three archived candidate CSVs from 08-05, 08-26 and 09-24.
    Lane      : full_stack_documentation / AIF-068.
    Status    : OPEN. Not fixed -- Gate 5 binds, it does not mutate.

## The measurement

`SYSARGS_IMPORT_candidate_v1.csv` has more ROWS than distinct `ARG_ID`s, and has
had for at least seven weeks:

    2026-08-05    959 rows    950 distinct ARG_ID     9 collisions
    2026-08-26   1066 rows   1054 distinct ARG_ID    12 collisions
    2026-09-24   1180 rows   1166 distinct ARG_ID    14 collisions

All 14 pairs carry DIFFERENT content -- they are not duplicate rows:

    ARG_KIND    differs in 14 of 14
    VAL_SHAPE   differs in 14 of 14
    NOTES       differs in 11 of 14

    ARG_BBS_SUBJECT     ARG_CODASYL_SET    ARG_ERASE_TABLE   ARG_FIELDMGR_NAME
    ARG_FIELDMGR_TYPE   ARG_IDX_TAG        ARG_RETRO_STYLE   ARG_SET_FILE
    ARG_SET_PATH        ARG_SQLSEL_SELECT  ARG_SQLSEL_VALUES ARG_USER_KEY
    ARG_USER_SECRET     ARG_WORKSPACE_FILE

`ARG_SET_PATH`, both rows in full:

    keyword     literal   usage=SET PATH <slot> <path>
    placeholder path      usage=SET DEVICE TO FILE <path> ; usage=SET PATH <slot> <path>

## The cause is two lines apart

    src/meta/metacollect.cpp:1084
        const auto aggregate_key = contract.command + "|" + arg_kind + "|" + arg_name;
    src/meta/metacollect.cpp:1087
        agg.row.arg_id = "ARG_" + sanitize_symbol(contract.command) + "_" + arg_name;

**The aggregation key has three components and the identifier it emits has
two.** The emitter knows the keyword/placeholder distinction, uses it to keep
the rows correctly apart in its own map, and then drops it from the name it
writes out. Any command whose own usage text uses one word in both roles --
`SET PATH` the literal and `<path>` the placeholder, `USER ... KEY` and `<key>`
-- produces two legitimate rows under one id.

## The flag that makes it reachable

`metacollect.cpp:1081-1083` drops keyword tokens unless
`--sysargs-include-keywords` is given. **That flag is in the standard emit** the
recipe book records, so the defect is created by the documented flag set rather
than by an unusual invocation. Without the flag there are no keyword rows and no
collisions -- which is why a spot check that omitted it would have reported the
table clean.

## Why nobody has hit it

Nothing imports SYSARGS. Live `SYSARGS.dbf` holds 249 rows against a candidate
of 1180 -- 21%. The collision is latent until the first keyed load, and on that
day 14 rows collide and one of each pair wins silently. A silent winner is worse
than a hard failure, because the table afterwards looks complete.

## The gate gap, and it is the proxy shape again

`METACOLLECT_SYSCMD_CANDIDATE_CONTRACT_V1.md` requires unique `CMD_ID` and
unique `CAN_NAME`. Gate 5 checks both, every run, and both pass -- **and SYSCMD
was never the table at risk.** The clause that exists is on the artifact that
does not need it. There is no SYSARGS counterpart, so seven weeks of candidates
carried a non-unique primary key past a gate whose whole subject is uniqueness.

This is the proxy family (recipe book Part 8a): a check that cannot answer the
question put to it, and reads as coverage because it is green.

## Remedy, either half of which closes it

1. Include `arg_kind` in the emitted id (`ARG_<command>_<kind>_<arg_name>`, or
   suffix only the placeholder form) so the id matches the aggregation key.
   One line, `metacollect.cpp:1087` -- but it renames rows, so it is a
   candidate-schema change and needs the contract updated with it.
2. Give the contract a SYSARGS clause -- `ARG_ID` unique, checked at Gate 5 --
   which makes the defect fail loudly today without changing any id.

**(2) first, (1) as the fix**, because (2) is what stops the next seven weeks.

## Verify

    cut -d, -f1 SYSARGS_IMPORT_candidate_v1.csv | sort | uniq -d
    grep -n "aggregate_key\|arg_id = " src/meta/metacollect.cpp
