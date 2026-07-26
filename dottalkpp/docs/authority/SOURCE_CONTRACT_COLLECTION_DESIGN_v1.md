# Source Contract Collection -- Design Proposal v1

> ## SUPERSEDED IN PART -- READ THIS FIRST (correction, 2026-07-26)
>
> The two tables proposed below (`SYSSRC`, `SYSCMDDOC`) **ALREADY EXIST** as
> `SRCFILE` and `SRCUSAGE` in the COMMENTS lane (`dottalkpp\data\comments\`),
> built by the DOCFLUSH-20260722-001 / AIF-048 Gate 1 work. This proposal was
> written without checking that lane. Do NOT create new tables.
>
> | proposed here | already exists | rows | verdict |
> |---|---|---|---|
> | `SYSSRC` | `SRCFILE.dbf` | 1032 | duplicate -- SRCFILE already has `HASH C(64)` + `UPDATED D(8)`, i.e. the drift key this doc proposed |
> | `SYSCMDDOC` | `SRCUSAGE.dbf` | 243 | duplicate -- same grain, same fields (OWNER/COMMAND/CATEGORY/STATUS/NOARGS/EFFECT/MUTATES/USGACC/SUMMARY/USAGE M/EXAMPLES M/NOTES M/RELATED) |
> | (not proposed) | `SRCBLOCK.dbf` | 706 | comment-block inventory, finer grain than either |
>
> Canonical collector: `tools/comments/reharvest_source_comment_catalog.py`
> (with `tools/comments/upsert_source_comment_contract.py` for single-contract
> updates). The M1 harvester built below is therefore a **cross-check /
> second opinion**, not the collection path. Refresh via the canonical tool.
>
> **What survives from this proposal** (genuinely absent from the SRC* family):
>
> 1. `FLD_PROV` -- authored-vs-derived provenance per banner field. `SRCFILE`
>    records detected values (`DET_KIND`/`DET_OWNER`/`DET_CMD`/`STATUS`) but does
>    not mark which are hand-authored vs backfill defaults. Finding 1 below
>    (1028/1034 files are pure backfill) is not visible in any existing table.
> 2. The anomaly set in Finding 3 (mention-only false positives, block dialect,
>    duplicate/`NONE` command names).
> 3. The staleness measurement below.
>
> ### THE ACTUAL HOLE (this is the answer to "we are not collecting new additions")
>
> `SRCFILE` holds 1032 rows; the tree now has 1034 tracked source files, and the
> sets do not merely differ by 2 -- they differ by **14 uncollected + 12 phantom**:
>
> **Uncollected (in tree, absent from SRCFILE)** -- note these are whole recent lanes:
> ```
> include/DottalkForm.h              src/bbs/bbs_server.cpp
> include/bbs/bbs_schema.hpp         src/bbs/bbs_store.cpp
> include/bbs/bbs_server.hpp         src/cli/cmd_bbs.cpp
> include/bbs/bbs_store.hpp          src/cli/cmd_net.cpp
> include/cli/build_vectors_report.hpp   src/security/token_crypto.cpp
> include/security/token_crypto.hpp  (+2 more)
> include/selfdoc/event_record.hpp
> ```
> The AIF-052 (BBS) and AIF-053 (security/NET) lanes are entirely absent from the
> source-contract catalog.
>
> **Phantom (in SRCFILE, no longer tracked)** -- 12 rows including
> `include/dottalkForm.h` (a CASE-ONLY rename of `include/DottalkForm.h`),
> `src/cli/cmd_transaction.cpp`, `src/module.cpp`, and 5 `src/tests/test_*.cpp`.
>
> So the catalog is stale in both directions. The repair is a reharvest + reload
> through the canonical tool, followed by wiring the drift check into the
> prepush gate (M4 below still stands, retargeted at SRCFILE.HASH).

Status: proposal / SUPERSEDED IN PART -- see correction above
Subsystem: metadata / selfdoc / help
Owner: member.derald   authored_by: member.ai.claude.cowork
Date: 2026-07-26
Mutation authority: none from this document alone

## Problem Statement

Three distinct holes, currently conflated:

1. **No file-grain table.** 804 non-command source files carry `@dottalk.file`
   banners. `tools/fullstack_docs/source_census.py` computes the set
   (`non_command = census \ commands`) but persists it nowhere.

2. **Command contract data is discarded.** `@dottalk.usage` carries 14 sub-fields;
   `SYSCMD` stores 6 columns. Uncollected today: `category`, `effect`, `mutates`,
   `risk`, `related`, `examples`, `notes`, `summary`, `noargs`, `usage-access`.

3. **Collection is one-shot, not a cycle.** The AIF-062 backfill WROTE banners once.
   Nothing reads them back, so edits and new files drift silently. This is the root
   cause of "we are not collecting the new additions."

## Measured Baseline (2026-07-26)

```
total tracked source (src/ + include/)   1034
  carrying @dottalk.file                 1034   (100.0%)
  carrying @dottalk.usage (commands)      230
  non_command (file-grain only)           804
live SYSCMD.dbf rows                      203
dotref.hpp entries                        255
```

### Banner field entropy -- the boilerplate problem

| field | distinct values | note |
|---|---|---|
| subsystem | 44 | real signal |
| layer | 6 | real signal (header 478 / helper 313 / command 230 / test 10) |
| owns | 3 | EMPTY in 1032 of 1034 |
| lane | 6 | EMPTY in 1011 of 1034 |
| project | 1 | zero information |
| owner | 1 | zero information |
| status | 1 | zero information -- asserts "supported" for ALL files incl. tests |

`derive_block()` hardcodes `project`, `owner`, `status`. These are DERIVED
DEFAULTS masquerading as authored facts.

### Contract field text lengths (drives C vs Memo)

| field | max chars | storage |
|---|---|---|
| usage | 1197 | Memo |
| notes | 1016 | Memo |
| risk | 472 | Memo |
| summary | 325 | Memo |
| examples | 284 | Memo |
| related | 119 | C(128) |
| mutates | 104 | C(128) |
| category | 27 | C(32) |
| effect | 31 | C(32) |

## Design Decision: Separate Tables, Not Schema Extension

**Grain differs, and the data proves it.** 8 files declare multiple commands:

```
src/cli/cmd_defcmd.cpp -> DEFCMD, UNDEFCMD
src/cli/cmd_deffn.cpp  -> DEFFN,  UNDEFFN
src/cli/cmd_if.cpp     -> IF,     ENDIF
src/cli/cmd_loop.cpp   -> LOOP,   ENDLOOP
src/cli/cmd_loop.hpp   -> ENDWHILE, ENDUNTIL
src/cli/cmd_until.cpp  -> UNTIL,  UNTIL_BUFFER
```

File:command is 1:N. Folding file facts into SYSCMD duplicates file rows per
command and corrupts the identity grain. Three tables, each at one grain:

### A. `SYSSRC` -- one row per source file (1034 rows)

```
FILE_ID    C(64)   stable key: path with / -> _  (e.g. SRC_CLI_CMD_IF_CPP)
PATH       C(160)  repo-relative, forward slashes
STEM       C(64)
EXT        C(8)
SUBSYSTEM  C(24)
LAYER      C(16)   header|helper|command|test|engine-core|glue
PROJECT    C(32)
LANE       C(16)   AIF-NNN or empty
OWNER      C(32)
STATUS     C(16)   supported|candidate|draft|retired
IS_CMD     L       carries @dottalk.usage
CMD_COUNT  N(3)    commands declared (0 for non-command files)
BANNER_V   C(8)    banner schema version (v1)
SRC_HASH   C(40)   SHA1 of the banner block ONLY -- drift key
HARVEST_AT C(19)   ISO timestamp of last harvest
FLD_PROV   M       per-field provenance: authored vs derived
```

`SRC_HASH` over the banner block (not the whole file) is the mechanism that
closes hole #3: body edits do not create false drift; banner edits do.

`FLD_PROV` addresses the boilerplate problem -- it records which fields were
hand-authored vs filled by `derive_block()`, so a future audit can tell real
`status: supported` from a default.

### B. `SYSCMDDOC` -- one row per command, the @dottalk.usage payload

```
CMD_ID     C(32)   FK -> SYSCMD.CMD_ID
CAN_NAME   C(80)
FILE_ID    C(64)   FK -> SYSSRC.FILE_ID
CATEGORY   C(32)
EFFECT     C(32)
NOARGS     C(32)
MUTATES    C(128)
RELATED    C(128)
USAGE_ACC  C(128)
SUMMARY    M
USAGE_TXT  M
EXAMPLES   M
RISK       M
NOTES      M
SRC_HASH   C(40)
HARVEST_AT C(19)
```

Kept SEPARATE from SYSCMD deliberately: identity is narrow, stable and queried
constantly; prose is bulky and churns with every comment edit. Mixing them forces
an identity-table rewrite on every doc tweak.

### C. `SYSCMD` -- unchanged spine (+ deferred Phase 1A fields)

SYSCMD stays the identity lane. Backlog Phase 1A specifies 13 minimum fields;
live table has 6. The missing `SRC_FILE` is the natural join to `SYSSRC.FILE_ID`
and should be added when the Phase 1A widening happens -- NOT as part of this
change (see "Do Not Bundle" below).

## The Repair: Make Collection a Cycle

Current state is write-once:

```
backfill --write  ->  banners in source  ->  (nothing reads them back)
```

Target:

```
source banners --[harvest]--> CSV --[import]--> SYSSRC / SYSCMDDOC
       ^                                              |
       |                                        [drift report]
       +---------- reconcile / re-author <-----------+
```

### Milestones

- **M1 harvest (read-only).** Extend `source_census.py` with `--emit-syssrc CSV`
  and `--emit-syscmddoc CSV`. No table writes. Pure function of the tree.
- **M2 seed.** Create both tables via the established
  `*_NATIVE_CREATE_IMPORT_*.RUN_METADATA_REVIEWED.dts` pattern.
  NOTE: correct DBF path is `dottalkpp\data\metadata`, NOT `data\dbf\metadata`
  (the v1 SYSCMD script has this wrong and would create a divergent table).
- **M3 drift report.** Compare `SRC_HASH` per file: source-only (new file),
  table-only (deleted), hash-mismatch (edited banner). Report, do not mutate.
- **M4 gate.** Wire the drift report into `tools/staging/prepush_gate.py` as a
  WARN lane (exit 3, ack-able) alongside the BOM and AIF gates -- so a banner edit
  without a metadata refresh is visible at the commit chokepoint. WARN, not HARD:
  banner edits are legitimate; going stale silently is what we are preventing.

## Do Not Bundle

Keep these separate from this change:

- widening SYSCMD to the full Phase 1A 13-field schema
- the dotref.hpp regeneration (93 syntax rewrites)
- SYSSUBCMD seeding / the 16 SET-family spelling forks
- refreshing the stale `SYSCMD_IMPORT_v1.csv` (40 rows) from the live 203-row table

Each is independently reviewable. Bundling them makes the diff unreadable and
couples a schema decision to a content decision.

## M1 Harvest -- BUILT and RUN (2026-07-26)

Implemented as additive read-only flags on `tools/fullstack_docs/source_census.py`:

```
python tools/fullstack_docs/source_census.py --root . \
    --emit-syssrc     <path>/SYSSRC_IMPORT_v1.csv \
    --emit-syscmddoc  <path>/SYSCMDDOC_IMPORT_v1.csv
```

Default census output is byte-for-byte unchanged (verified). No table writes.

Result: **1034 SYSSRC rows** (227 command-bearing, 807 non-command) and
**243 SYSCMDDOC rows** (236 distinct commands).

### Finding 1 -- the banner estate is 99.4% machine-derived

`FLD_PROV` compares every field against what `derive_block()` would regenerate:

| field | authored | derived | empty |
|---|---:|---:|---:|
| subsystem | 0 | 1034 | 0 |
| layer | **6** | 1028 | 0 |
| owns | 0 | 2 | 1032 |
| project | 0 | 1034 | 0 |
| lane | 0 | 23 | 1011 |
| owner | 0 | 1034 | 0 |
| status | 0 | 1034 | 0 |

**1028 of 1034 files carry ZERO authored banner fields.** The `@dottalk.file`
estate is backfill output, not collected knowledge. `SYSSRC` is still worth
building -- it is the file inventory and the drift spine -- but STATUS / OWNER /
PROJECT must NOT be treated as authority until authored. `FLD_PROV` keeps that
distinction visible in the table instead of laundering defaults into fact.

### Finding 2 -- the command contracts ARE rich (this is the real asset)

`@dottalk.usage` is hand-authored and dense:

| column | fill | max len |
|---|---:|---:|
| USAGE_TXT | 100.0% | 1053 |
| CATEGORY / MUTATES / SUMMARY | 99.6% | 104 / 304 |
| EFFECT / USAGE_ACC | 99.2% | 39 / 45 |
| NOTES | 97.9% | 955 |
| RISK | 84.8% | 426 |
| RELATED | 83.1% | 274 |
| EXAMPLES | 31.7% | 258 |

This is the material SYSCMD's 6 columns were discarding.

### Finding 3 -- anomalies surfaced (reported, NOT auto-corrected)

- **1 non-canonical dialect**: `src/cli/cmd_ddict.cpp` uses a block comment
  (`/* ... */`) with `surface:`/`forms:` instead of `command:`/`usage:`, plus
  `profiles:`/`read_mode:`. Harvester now reads both dialects and records which
  in `SYSCMDDOC.DIALECT`. Canonicalization is a maintainer decision.
- **6 mention-only false positives**: `helpdata_source_miner.cpp`,
  `metacollect.cpp`, `helpdata_cmdhelp_bridge.{cpp,hpp}`, `ext_policy.hpp`,
  `helpdata_messages.cpp` merely reference the marker in code/prose. **The census
  `commands (@usage): 230` count is inflated by these.** True count is 227 files.
- **6 duplicate command names**: `HELP`, `IDX`, `PSHELL`, `STRUCT` declared in two
  files each; `DOTSCRIPT` declared TWICE IN THE SAME FILE; `NONE` used as a
  command name in 3 `src/edu/` files (placeholder leaking into contract space).
- **Non-identity names**: `ASCEND/DESCEND` and `ERP / EDU_ERP` are compound
  strings, not canonical command identities.

### Finding 4 -- bidirectional gap vs live SYSCMD

```
contracts with NO SYSCMD row : 35   <- source documents them; table does not
SYSCMD rows with NO contract :  2
```

The 35 include `BBS`, `DEFCMD`, `DEFFN`, `BUILDVECTORS`, `BETA`, `FOXREF`,
`GENERIC`. These overlap the 55 dotref entries lacking SYSCMD rows -- the same
gap seen from a third angle.

## Open Questions for the Maintainer

1. **`status` semantics.** Should `status` be re-authored per file (test files are
   not "supported"), or is a `layer`-derived default acceptable? Current uniform
   `supported` is inaccurate for the 10 test-layer files at minimum.
2. **`SYSSRC` scope.** `src/` + `include/` only (1034 files), or extend to
   `tools/` and `dottalkpp/tools/` (python tooling also carries banners)?
3. **Retired files.** When a source file is deleted, does its `SYSSRC` row get
   deleted or marked `STATUS: retired` for historical traceability?
