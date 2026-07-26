# Session Record -- Claude Cowork, 2026-07-26 (v1)

Lane: full_stack_documentation (bottom half: source -> contracts -> metadata)
Related run: `DOCFLUSH-20260722-001` (AIF-048)
Related mission: `METACOLLECT-238-20260717-001` (separate, report-only)
Agent: member.ai.claude.cowork
Maintainer: member.derald
Authority root: `D:\code\ccode`
Status: **report/candidate only -- no metadata table was mutated in this session**

## Purpose

Full record of one working session on the lower half of the full-stack
documentation vertical: what was fixed, what was found, what was produced, and
**what I got wrong**. The mistakes section is not a formality -- three of them
would have destroyed data or corrupted canonical lanes if executed, and the
pattern behind them is worth institutional memory.

---

## 1. Work completed

### 1.1 BOM regression repair (build-blocking) -- DONE, VERIFIED

MSVC failed (`C3872` / `C2014` / `C2143`) on the xbase/memo/xindex modules.

Root cause: the AIF-062 `@dottalk.file` banner backfill prepended an 8-line
banner **above** files that already began with a UTF-8 BOM, relocating the BOM
to ~line 10. A BOM at offset 0 is fine; a BOM mid-file breaks MSVC. GCC/clang
tolerate it silently, so a WSL build would have produced a false green.

Fixed:
- stripped the stray BOM bytes from **29 headers/sources** (see 1.2 for the list scope)
- `tools/fullstack_docs/source_census.py`: read with `utf-8-sig` in BOTH the
  `--write` and `--upgrade` paths, so a banner can never again strand a BOM
- `tools/staging/prepush_gate.py`: added `embedded_bom_offenders()` -- HARD block
  (exit 2) on any staged C/C++ blob carrying `EF BB BF` after byte 0

Verified end-to-end on MSVC (the compiler that actually failed):
```
cmake --build build --target dottalkpp --config Release   -> clean
  xbase.lib / memo.lib / xindex.lib all rebuilt clean
./datarun.ps1 -CommandLines 'USER LIST'                    -> runs, 6 members
dottalk++ v0.6 (2026-07-24)  build Jul 26 2026 09:35:34
```

### 1.2 Working-tree triage -- DONE

Untracked count went **12,400 -> ~8,500**. Two commits, both gate-PASS:

- `73fe092c5` gitignore triage v1 -- backup trees, manualgen logs +
  `MDO-*/PIP-*_STATUS.md`, `data/ram/` cache, `mcc/*.DBF`, stray root `import*.py`
  (~2,284 untracked hidden, zero collision with tracked files)
- `65c8dd422` gitignore triage v2 -- generated report/candidate CSVs +
  `indexes/**/*.cdx.meta` (~1,927 hidden; 3 deliberately-tracked report CSVs stay)

Moved to `D:\code\ccode.sidecar` (nothing deleted, all reversible):
- 91 chat-fragment `.txt`, accidental `import*.py`, 2 temp dirs
- 25 one-off root `.ps1` (`begin_mdo_*`, `gather_*`, `rollback_mdo_*`, ...)
- 120 **uncited** probe `.dts` -- see 3.4 for how "uncited" was established
- 3 byte-identical `(1)` duplicate copies

Deliberately NOT ignored, and the reasons recorded in `.gitignore` itself:
`dottalkpp/data` DBF/index tables (84 tracked fixtures -- a track-the-source-tables
policy), `.patch` / `.dts` (AIPortal intake deliverables), and the mixed
`indexes/` `.cdx`/`.cnx` binaries (36 tracked / 75 untracked -- per-file call deferred).

### 1.3 M1 source-contract harvest -- BUILT (but see 4.2)

Added two additive read-only flags to `tools/fullstack_docs/source_census.py`
(`--emit-syssrc`, `--emit-syscmddoc`, plus `--csv-bom`). Default census output
is byte-identical -- verified. Produces 1034 file rows and 243 contract rows.

Genuinely new vs. everything already in the tree:
- **`FLD_PROV`** -- per-field authored-vs-derived provenance, computed by
  regenerating `derive_block()` and comparing. Nothing else records this.
- anomaly detection (dialects, mention-only false positives, bad identities)

### 1.4 SRC* catalog reharvest -- CANDIDATE PRODUCED

Ran the canonical `tools/comments/reharvest_source_comment_catalog.py` into
`DOCFLUSH-20260722-001/comments_reharvest/fullstack_20260726_contracts_v3`.
`CANDIDATE_ONLY / NOT_LOADED`, zero DBF writes. Authorization package written:
`RELOAD_AUTHORIZATION_PACKAGE_V1.md` (includes the 6 PATH_REMOVED adjudication).

### 1.5 METACOLLECT current audit -- RUN, REPORT-ONLY

Rebuilt the `metacollect` target (`build\metacollect-docflush`, flag
`DOTTALK_BUILD_METACOLLECT=ON`) and ran it read-only into the mission's own
directory `audit_20260726/` -- NOT into the DOCFLUSH run, per the handoff's
explicit boundary.

---

## 2. CSV encoding policy (decided from engine behavior)

Canonical = **UTF-8, no BOM**. Evidence, not preference:

- every existing canonical import file is BOM-less (SYSCMD/SYSARGS/SYSFUNC/SYSMSG)
- the engine WRITES BOM-less CSV (no BOM emitter anywhere in `src/`)
- the engine READS a BOM tolerantly: `strip_import_utf8_bom()` clears it from
  column 0 of the HEADER record only (`cmd_import.cpp:146` passes `true`; data
  rows pass `false`) -- correct, since a BOM can only occur at file start
- `csv::read_record()` DOES support quoted multi-line cells; `csv::escape()` uses
  RFC-4180 quote doubling, compatible with Python's writer

So BOM is opt-in (`--csv-bom`) for Excel review copies only. Rationale is written
into `write_csv()` so it is not re-litigated.

**Untested path flagged:** SYSCMDDOC/SRCUSAGE carry ~798 quoted multi-line cells.
`csv::read_record` supports them, but **no previously loaded metadata CSV
exercises that path**. Smoke-test IMPORT on a scratch table before any reload.

---

## 3. Findings worth keeping

### 3.1 The metadata lane is inverted, in both directions

| table | live rows | its CSV |
|---|---:|---:|
| SYSCMD | 203 | 40 |
| SYSARGS | **0** | 215 |
| SYSFUNC | **0** | 64 |
| SYSMSG | **0** | 1006 |
| SYSSUBCMD | 12 | -- |

SYSCMD's table is AHEAD of its CSV; SYSARGS/SYSFUNC/SYSMSG have CSVs with data
and **empty canonical tables**. Backlog Phase 2 ("seed canonical rows") is
genuinely unstarted for three of five lanes.

### 3.2 The dotref generator reads a stale CSV, not the canonical table

`generate_dotref_from_metadata_v1.py` defaults to `SYSCMD_IMPORT_v1.csv`
(40 rows, stale since 2026-05-20) and reported **14.9%** coverage. Measured
against the live 203-row table it is **78.4%** (200/255). The tool was measuring
a snapshot and calling it the lane -- a doctrine violation (metadata table is the
canonical authoring lane).

Regenerating dotref would rewrite **93 of 200** syntax strings, flip **0**
`supported` flags, and cannot truncate (`USAGE`/`VERBOSE` are memo fields;
`COMMAND` is C(24) vs max name length 15). The rewrites are improvements:
`SET ORDER` goes from one guessed form to the three real ones mined from SYSARGS.
CAVEAT: that syntax comes from the SYSARGS **CSV**, whose canonical table is empty.

### 3.3 The SRC* catalog predates the banner backfill

Reharvest delta vs live: **902 COMMENT_METADATA_CHANGED, 141 PATH_ADDED,
6 PATH_REMOVED**. Of the 902, **494 gained a header banner (F->T)** and 480 of
those gained exactly 9 lines with `owner: member.derald` -- the `@dottalk.file v1`
signature. **Zero files lost a banner** (stale in the safe direction).

### 3.4 PATH_REMOVED adjudication -- 4 moves, 2 real removals

| removed path | verdict |
|---|---|
| `include/dottalkForm.h` | CASE RENAME -> `include/DottalkForm.h` (Windows case-insensitivity hid it) |
| `src/cli/table_state.hpp` | MOVED -> `include/cli/table_state.hpp` |
| `src/cli/table_write.hpp` | MOVED -> `include/cli/table_write.hpp` |
| `src/core/dbf_create.cpp` | MOVED -> `src/xbase/dbf_create.cpp` |
| `src/cli/nav_select.cpp` | DELETED in `9922505e9`; header + callers survive |
| `src/cli/cmd_vuse.cpp` | **NEVER TRACKED** -- untracked scratch present at harvest time |

That last one matters beyond itself: **the harvester scans the filesystem, not
the git index**, so any scratch file sitting in the tree becomes a catalog row.
Worth deciding whether that is intended.

### 3.5 Banner estate is 99.4% machine-derived

`FLD_PROV` across 1034 files: **1028 carry ZERO authored fields.** Only 6 have a
hand-set `layer`. `subsystem` 0 authored / 1034 derived; `project`, `owner`,
`status` 1 distinct value each; `owns` empty in 1032; `lane` empty in 1011.

Consequence: `status: supported` is asserted on **every** file including the 10
test-layer ones. Loading that into a queryable table converts a backfill default
into apparent authority.

By contrast the command contracts ARE real: `USAGE_TXT` 100% filled (max 1053
chars), `CATEGORY`/`MUTATES`/`SUMMARY` 99.6%, `NOTES` 97.9%, `RISK` 84.8%.

### 3.6 Contract-space quality defects (surfaced, not corrected)

- `src/cli/cmd_ddict.cpp` uses a **non-canonical block-comment dialect**
  (`/* */` with `surface:`/`forms:` instead of `command:`/`usage:`, plus
  `profiles:`/`read_mode:`, and a real `status: source_contract_review_candidate`)
- **6 mention-only false positives** (`helpdata_source_miner.cpp`,
  `metacollect.cpp`, `helpdata_cmdhelp_bridge.{cpp,hpp}`, `ext_policy.hpp`,
  `helpdata_messages.cpp`) merely reference the marker in code/prose --
  **the census `commands (@usage): 230` is inflated; the true count is 227**
- `DOTSCRIPT` declares a contract **twice in the same file**
- `NONE` used as a command name in 3 `src/edu/` files
- `ASCEND/DESCEND` and `ERP / EDU_ERP` are compound strings, not identities

### 3.7 METACOLLECT: frozen 238 confirmed, and 10 actionable rows

Current audit reproduces the baseline **exactly**: 238 issues =
**175 `METADATA_ONLY` commands + 63 `SOURCE_ONLY` functions**. No drift since
2026-07-17. `SYSFUNC`/`SYSARGS`/`SYSMSG` still warn zero rows.

The candidate is a strict **superset** of live SYSCMD (213 vs 203, **0 dropped**).
The 10 additions -- implemented, handler-resolved, absent from the table:

`BBS`, `NET`, `VDISK`, `USER`, `BUILDVECTORS`, `STOP_ON_ERROR`,
`DEFCMD`, `UNDEFCMD`, `DEFFN`, `UNDEFFN`

### 3.8 Cross-tool convergence: recent lanes don't reach metadata

`BBS`, `NET`, `VDISK` are missing from SYSCMD **and** the BBS/security files are
missing from SRCFILE. Two independent tools, same blind spot: **AIF-052 (BBS) and
AIF-053 (security/NET) never propagated to the metadata layer.**

### 3.9 CMDHELP is a compile-time consumer of dotref

`cmdhelp.hpp` includes `dotref.hpp`/`foxref.hpp` directly, so the catalogs are
baked into the binary. `collect_commands()` merges registry + foxref + dotref +
edref, mapping `it.syntax -> usage`, `it.summary -> verbose`,
`it.supported -> SUPPORTED`. Regenerating dotref therefore rewrites CMDHELP's
usage text at the source. `CMDHELP BUILD LEGACY` emits `commands.dbf`/`cmd_args.dbf`;
`BUILD V2` emits `help_topic/section/line/artifacts.dbf`.

---

## 4. MISTAKES -- what I got wrong

### 4.1 Proposed a destructive SYSCMD import built on a false premise (MOST SERIOUS)

I read the generator's "14.9% coverage", concluded SYSCMD was under-seeded, and
staged a full `ERASE SYSCMD CONFIRM` + `CREATE` + `IMPORT` of a 216-row CSV.

Wrong because:
1. the 14.9% came from the **stale 40-row CSV**, not the live 203-row table;
   true coverage was 78.4%
2. my 216-row CSV **omitted 15 rows that exist live** -- `BUILDLMDB`, `SETPATH`,
   `PREDHELP`, `WHERECACHE`, `STUDENTECHO`, `STUDENTHELLO`, and the whole
   `SET CASE/CDX/CNX/FILTER/INDEX/NEAR/ORDER/RELATION/UNIQUE` family
3. those 15 were precisely the rows I had earlier proposed "holding for review" --
   i.e. the maintainer had already decided them and I would have deleted the decisions

Caught only because I checked the live DBF header before running it. Had I
trusted the tool's own number, I would have destroyed maintainer decisions in a
canonical table.

Mitigation: staged script overwritten with an inert WITHDRAWN header documenting
all of the above; `SYSCMD_IMPORT_v2.csv` flagged for deletion.

**Lesson: a coverage metric is only as canonical as its input. Verify which
artifact a tool actually reads before acting on its number.**

### 4.2 Designed two tables that already existed

I wrote `SOURCE_CONTRACT_COLLECTION_DESIGN_v1.md` proposing `SYSSRC` (file grain)
and `SYSCMDDOC` (contract grain). Both already exist:

| I proposed | already exists | rows |
|---|---|---|
| `SYSSRC` | `SRCFILE.dbf` | 1032 -- already has `HASH C(64)` + `UPDATED D(8)`, the exact drift key I "designed" |
| `SYSCMDDOC` | `SRCUSAGE.dbf` | 243 -- same grain, same fields |
| (missed entirely) | `SRCBLOCK.dbf` | 706 |

I designed against `dottalkpp/data/metadata/` without ever listing
`dottalkpp/data/comments/`. Doc is now marked SUPERSEDED IN PART with the
correction at the top rather than quietly rewritten.

### 4.3 Reimplemented metacollect in Python -- and did it worse

`report_syscmd_seed_gap_v1.py` emits `CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE` --
byte-for-byte what `metacollect --syscmd-import-out` already produces. Measured
side by side:

| | metacollect | my Python |
|---|---:|---:|
| candidate rows | 213 | 176 |
| live rows dropped | **0** | **15** |
| TYPE classes | `command` + `syntax-command` | `command` only |

Of my 176, only 158 agreed. **18 were false positives** -- `COMMANDSHELP`, `EXIT`,
`FOXTALK`, `GENERIC`, `LMDB`, `LMDBDUMP`, `SCAN_BUFFER`, `LOOP_BUFFER`, `BETA`,
`CANARY`, `AVERAGE`, `BROWSETV`, `EXPFUNCS`, `REL_LIST` -- aliases, internal
buffers and dev surfaces the contract explicitly excludes.

I also violated its documented merge rules: I inferred aliases from shared
handlers (`ARCTICTALK` -> `cmd_FOXTALK`), but rule 5 states **"a shared handler
alone never proves an alias"**. And I filed `SETORDER` vs `SET ORDER` as an
unresolved "spelling fork" when rule 4 already handles compact matching.

### 4.4 Nearly swept `.dts` files as junk without understanding them

In the cleanup pass I classified 146 `.dts` as sidecar candidates. The maintainer
had to point out that `.dts` are valid DotTalk++ scripts. I had in fact excluded
`.dts` from `.gitignore` and run a citation check first -- but the framing was
careless and the correction was warranted. Final action kept the 12 doc-cited
proofs and 11 test-dir smokes, and moved only 120 verified-orphan probes (no
reference in any tracked doc, code, or runner) -- all reversible.

### 4.5 Reported a broken provenance metric

First `FLD_PROV` implementation compared only the hardcoded constants, so
`subsystem` was always scored "authored" and I reported "1034 files carry an
authored field (0 fully derived)" -- meaningless. Corrected to regenerate
`derive_block()` and compare per field, giving the real answer: **1028 of 1034
carry zero authored fields.** The first number was noise presented as a finding.

### 4.6 Misjudged an Excel failure

Told the user their CSVs were fine and implied Excel was at fault. The files were
structurally clean (verified: no NULs, no control chars, valid UTF-8, no ragged
rows), but the user's own suggestion -- an access/permissions issue -- was the
better hypothesis, and I should have reached for Mark-of-the-Web before
explaining the data.

### 4.7 Process errors

- gave a PowerShell command with a bare filename when the script was in the
  scratch outputs folder, not the repo -- wasted a cycle
- misread `git status --short` line counts as file counts; `--short` folds an
  entire untracked directory into one line, so 1,590 lines != 1,590 files
- initially estimated the SRCFILE gap at "14 files" by comparing against
  `git ls-files`; the real delta was 141 added / 6 removed / 902 changed, because
  the reharvest scans a wider root set (1,044 files incl. `bindings/`)

### 4.8 The pattern

Four of these (4.1, 4.2, 4.3, 4.4) share one root cause: **I acted on a local
reading without first surveying what the project already had.** The repo is
mature and its C++ tooling is more careful than a fresh Python approximation.
Python earned its place here only for one-off cross-checks -- which is exactly
what caught the stale-CSV problem in 4.1.

**Standing guidance for the next agent: before writing a tool, grep for an
existing one. Before trusting a number, check which artifact produced it.
Before erasing anything, read the live table header.**

---

## 5. Artifacts produced (all report/candidate)

```
docs/maintenance/lanes/full_stack_documentation/
  SESSION_RECORD_CLAUDE_COWORK_2026-07-26_V1.md          <- this file
  runs/DOCFLUSH-20260722-001/comments_reharvest/fullstack_20260726_contracts_v3/
    README.md                                   1044 scanned / 244 contracts
    source_comment_reharvest_delta_v1.csv       1050 delta rows
    candidate_source_comment_metadata_import_v2/*.csv    8 candidate tables
    RELOAD_AUTHORIZATION_PACKAGE_V1.md          preconditions/rollback/verify

docs/maintenance/lanes/metadata/missions/METACOLLECT-238-20260717-001/audit_20260726/
    metacollect_compare_20260726.csv            238 issues (175 cmd / 63 fn)
    metacollect_warnings_20260726.txt
    SYSCMD_CANDIDATE_20260726.csv               213 rows
    SYSFUNC_CANDIDATE_20260726.csv               65 rows
    SYSARGS_CANDIDATE_20260726.csv              248 rows

dottalkpp/docs/authority/
    SOURCE_CONTRACT_COLLECTION_DESIGN_v1.md     SUPERSEDED IN PART (see 4.2)

tools/fullstack_docs/source_census.py           +--emit-syssrc/--emit-syscmddoc/--csv-bom
tools/staging/prepush_gate.py                   +embedded-BOM hard block
dottalkpp/data/scripts/metadata/
    SYSCMD_NATIVE_CREATE_IMPORT_v2.RUN_METADATA_REVIEWED.dts   INERT/WITHDRAWN
```

Committed: `73fe092c5`, `65c8dd422` (both `.gitignore` only, gate PASS).
Everything else is uncommitted working-tree state.

---

## 6. Open decisions for the maintainer

1. **`status` semantics** -- re-author per file, or accept the derived default?
   Reloading SRCFILE promotes 1028 files' worth of backfill defaults into
   catalog authority (3.5).
2. **SRC* reload timing** -- inside DOCFLUSH-20260722-001, or open the next
   vertical? Gates 2 and 3 were computed from the pre-backfill catalog, so their
   results (212 aligned commands; 459 legacy commands / 575 topics) go stale on
   reload and should be re-run before Gates 6-7 publication.
3. **The 10 metacollect additions** (3.7) -- seed now or disposition inside the
   METACOLLECT-238 mission workstreams?
4. **Refresh `SYSCMD_IMPORT_v1.csv` from the live table** (export, not import),
   or point the generator at the DBF directly? Either fixes 3.2.
5. **`cmd_vuse.cpp` class of problem** -- should the reharvester scan the git
   index instead of the filesystem (3.4)?
6. **`cmd_ddict.cpp` dialect** -- canonicalize to `command:`/`usage:`, or record
   the block dialect as a supported alternate?
7. **SET-family seam** -- dotref carries `SET ORDER`/`SET CDX`/... as top-level
   commands, SYSSUBCMD models them as subcommands (16 spelling forks), and
   cmdhelp compensates with `canonical_set_family_query()`. If dotref
   regeneration and SYSSUBCMD seeding both proceed, they meet here.
8. **Two helper files** left in the repo root by the cleanup passes
   (`move_to_sidecar_first_pass.ps1`, `quarantine_files.txt`,
   `sidecar_oneoff_ps1.txt`, `sidecar_dts_uncited.txt`, `sidecar_step3_dupes.txt`)
   -- sidecar or delete.

## 7. Boundaries respected

- No metadata/COMMENTS/HELP/manual/website table was written.
- METACOLLECT output went to the mission directory, not the DOCFLUSH run --
  the handoff states its 238 findings "must not be silently absorbed into this run".
- Sidecar moves are moves, never deletes; every list is retained.
- Both commits were `.gitignore`-only and passed the prepush gate
  (source/docs/config only, no embedded BOM, no AIF collision).
