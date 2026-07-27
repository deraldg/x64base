# Session Record -- Claude Cowork, 2026-07-26 (v2) -- HANDOFF

Lane: `full_stack_documentation` (bottom half: source -> contracts -> metadata)
Run: `COWORK-20260726-001`   Agent: `member.ai.claude.cowork`   Maintainer: `member.derald`
Branch: `development`   HEAD at close: **`32747e423`** (2026-07-26 22:33 -0700, pushed)
Continues: `SESSION_RECORD_CLAUDE_COWORK_2026-07-26_V1.md`

> **V1's status line is SUPERSEDED.** V1 says "no metadata table was mutated in
> this session." That was true when written. It is no longer: this half of the
> session performed an authorised destructive reload of all eight SRC* tables
> and refreshed the tracked SYSCMD CSV. See section 2.

**READ THIS FIRST IF YOU ARE PICKING UP THE LANE.** Section 6 is the next
action. Section 7 is what will bite you.

---

## 1. Where the chain actually stands

The vertical is: source contracts -> SRC* catalog -> metadata -> dotref -> HELP
-> manual -> website.

```text
Gate 1  SRC* catalog          CLOSED   reloaded, matches the repo, drift 0
Gate 2  contracts/census      PASS     1035/1035 banners, 100%
Gate 3  HELP                  BLOCKED  needs CMDHELPCHK transcript (external evidence)
Gate 4  manual                STALE    passes, but on a 2026-07-23 assembly
Gate 5  website               NO GUARD spec only
Gate 6  --                    PARTIAL
Gate 7  live readback         NO GUARD spec only
```

`stack_audit_v1`: **FAIL 0 / WARN 18**, baseline ratcheted 21 -> 19 -> 18 across
the session. Baselines ratchet DOWN only; never raise one to make a run pass.

**Gate 1 is the headline.** Before this session every gate above it had passed
on a catalog that predated the AIF-062 banner backfill. Those passes were not
wrong so much as meaningless. The catalog now matches `git ls-files`, so Gates
2-4 are measuring something real for the first time.

---

## 2. What changed (7 commits, all pushed)

```text
72a847ec4  feat(date)    UTC clock -- zone arg, UDATE/UTIME/UNOW aliases
bc37dcc3e  docs(pdlc)    four migration proofs registered, empirical lane corrected
64c9d68d7  docs(aif-065) BUILDLMDB size ladder documented but not honoured
456f4ebf1  fix(docs-chain) one source-set rule -- git ls-files over src/include/bindings
3f4e0be45  chore(gate1)  ratchet baseline 21 -> 19 after SRC* reload
492ac73f0  fix(syscmd)   remove fabricated LOAD row; export mirror
32747e423  chore(syscmd) refresh tracked CSV from live table (40 -> 203); baseline 19 -> 18
```

### 2.1 Destructive operations performed

- **SRC* reload.** All eight COMMENTS tables dropped and rebuilt from the v5
  tracked-membership candidate. Final: SRCFILE 1035, SRCBLOCK 1279, SRCLINE
  30085, SRCUSAGE 244, SRCCLASS 1279, SRCDISP 20, SRCALIAS 9, MEMO_LINES 1530 --
  each verified against the candidate manifest by the driver, not by eye.
  Backup: `..\ccode.sidecar\comments_reload_backup_20260726-215408` (26 MB).
- **SYSCMD tracked CSV replaced**, 40 rows -> 203, exported FROM the live table.
  Backup: `..\ccode.sidecar\SYSCMD_IMPORT_v1.csv.<stamp>.bak`.
- **~87 GB reclaimed**: 37.4 GB of LMDB archives pruned, ~47 GB of sidecar
  backup deleted, plus a partial.

### 2.2 The membership rule (settled -- do not relitigate silently)

**The SRC* catalog documents the REPOSITORY, not the working tree.**
Membership = `git ls-files` over `{src, include, bindings}`.

Chosen by the maintainer 2026-07-26. Three tools were disagreeing:
`reharvest_source_comment_catalog.py` walked the filesystem over three roots
while `stack_audit_v1.py` and `source_census.py` used git over two. Every
`SRCFILE_DRIFT` finding was an artifact of that disagreement. All three now
share the rule and the extension set. `--allow-untracked` exists as an escape
hatch and should stay unused.

Ten never-committed files under `src/tests/`, `include/reference/`,
`src/reference/` and `src/cli/cmd_transaction.cpp` are consequently **excluded**
from the catalog. That is deliberate. Commit them if they should be documented.

---

## 3. Defects found and documented (not silently patched)

Three, and they are the same defect: **something declared in one place, not
honoured in another, with no check comparing the two.**

| | Defect | State |
|---|---|---|
| **AIF-065** | `BUILDLMDB`'s size ladder (TINY..HUGE, MAPSIZE) is parsed, floored, echoed -- then overridden by hardcoded 1 GiB in `cdx_backend.cpp:189` and `lmdb_backend.cpp:80`. The whole ladder is cosmetic. | documented, **fix NOT applied** |
| census `SRC_DIRS` | Declared at the top of `source_census.py`, but the git path hardcoded `("src","include")` past it. Widening the constant did nothing; it kept reporting 1034/1034 = 100%. | **fixed** in `456f4ebf1` |
| `LOAD` phantom | `SYSCMD_IMPORT_v{1,2}.csv` asserted a top-level `LOAD` command with `HANDLER cmd_LOAD`. No such function exists. `LOAD` is only a subcommand (`BETA LOAD`, `REL LOAD`, ...) and a reserved word. | **fixed** in `492ac73f0` |

### 3.1 AIF-065 -- what is owed before the fix

Full analysis: `docs/maintenance/LMDB_MAPSIZE_OVERRIDE_LANE_V1.md`.
Lesson: `lesson.career.a_documented_option_is_not_an_honoured_option`.

**The effect is measured. The cause is INFERRED.** Recorded at
`source_defined`, and it must not be promoted to `runtime_observed` until this
runs and the transcript is preserved:

```text
USE <small table> / SELECT <area> / BUILDLMDB CLEAN TINY YES
    -> stat data.mdb    expect      33,554,432
force an index attach (SET ORDER TO <tag>)
    -> stat data.mdb    33,554,432 = mechanism wrong
                        1,073,741,824 = mechanism right
```

The proposed fix is to **delete** both reader-side `mdb_env_set_mapsize` calls
so LMDB adopts the meta-page size -- **confirm that adoption rule against the
linked LMDB version first.** If it differs, the fix is larger (persist the size
in the CDX container). Needs a rebuild plus a `BUILDLMDB CLEAN` pass per lane
before existing envs shrink. Its own slice; do not fold into a reload.

### 3.2 Consequence already recorded

The **x64base-vs-SQLite benchmark storage axis is blocked**. Index footprint is
currently a function of attach history, not data -- a 30,124-row table and a
9-row table both occupy 1,073,741,824 bytes. Recorded in the PDLC empirical
lane. Latency, row-count and correctness axes are unaffected.

---

## 4. Also corrected: the PDLC round-trip claim

`DBF -> CSV -> DBF` is now recorded as **STRUCTURE-lossless**, not lossless.
`EXPORT` emits `L` fields lowercase (`t`) where the DBF stores `T`. Both parse
on `IMPORT`, so no content is lost, but the intermediate CSV is not the DBF's
bytes. Consequences: a text diff of two exports is not a data diff; checksum
identity across a CSV hop fails on intact data; external readers may not accept
both spellings.

**Owed:** extend the round-trip proof to compare VALUES across every field type.
`L` surfaced first; `D`, `N` with decimals and `M` are next, and memo is where a
surprise is most likely given the quoted-newline issue already routed around by
`MEMO_LINES_IMPORT_v2_ONE_PHYSICAL_ROW.csv`.

---

## 5. New tooling (all committed)

```text
tools/fullstack_docs/reload_src_comments.ps1     parameterised Gate 1 reload driver
tools/fullstack_docs/prune_lmdb_archives.ps1     archive reclaim, -Keep N per table
tools/fullstack_docs/export_syscmd_mirror.ps1    table -> CSV refresh with guards
dottalkpp/data/scripts/metadata/SYSCMD_EXPORT_MIRROR_v1.dts
```

Two conventions worth keeping, both learned the hard way:

- **Expected values are READ, never typed.** The reload driver reads row counts
  from the candidate manifest; the export driver reads the count from the DBF
  header. Invented expectations make a correct run look broken and a broken run
  look correct.
- **Guards acknowledge by name.** `-AcceptCsvOnly LOAD` names the one row being
  dropped. No blanket overrides.

---

## 6. NEXT ACTIONS, in order

### 6.1 Immediate hygiene (5 minutes)

```powershell
cd D:\code\ccode
Remove-Item reload-src-comments-v3.ps1                             # superseded
Remove-Item commit-fullstack-guards-and-conversion-proofs.ps1      # spent
```

### 6.2 Make the audit prove its own inputs -- DO THIS FIRST

`stack_audit_v1`'s `CSV_VS_TABLE` check reads lane CSVs. **It does not verify
they are tracked.** Discovered at session close:

```text
SYSCMD_IMPORT_v1.csv   untracked until 32747e423  (tonight)
SYSCMD_IMPORT_v2.csv   untracked until 492ac73f0  (tonight)
SYSMSG_IMPORT_v1.csv   STILL UNTRACKED -- 1,006 rows
```

The guard has been comparing canonical tables against files no clone has. This
is the **AIF-062 shape** -- evidence invisible outside this machine -- and the
registry validator was built for exactly it, then never pointed at the audit's
own inputs.

Add a finding code (`UNTRACKED_INPUT`) that fires when any lane CSV is not in
`git ls-files`. A guard that silently reads untracked evidence can pass on one
machine and mean nothing on another. Cheap, and it must land before the seeding
below, or the seeding inherits the same blind spot.

### 6.3 Seed the three empty lanes

```text
SYSARGS   table EMPTY,  CSV 215 rows   (tracked)
SYSFUNC   table EMPTY,  CSV  64 rows   (tracked)
SYSMSG    table EMPTY,  CSV 1006 rows  (UNTRACKED -- fix 6.2 first)
```

**The direction reverses from this session.** SYSCMD was table -> CSV with the
table as authority. These are CSV -> table into EMPTY tables, so the CSV is the
only candidate source and nothing can be overwritten. Safer in that respect --
but `LOAD` proves these seed CSVs contain fabrications, so run the same handler-
resolution check before importing:

> read every tracked source file into one blob; assert each row's HANDLER
> appears as an identifier. Of 216 SYSCMD rows, exactly one failed.

Note the check catches **fabrication, not misclassification**. All 27 remaining
seed-gap candidates in `SYSCMD_IMPORT_v2.csv` pass it -- so would `LOAD` have,
had someone named a real function. Adjudicate against the command registry.

### 6.4 Then, and only then, up the chain

```text
dotref regen (93 syntax rewrites, 0 supported-flag flips, measured earlier)
  -> CMDHELP BUILD
  -> CMDHELPCHK          <- produces Gate 3's owed transcript
  -> manualgen           <- refreshes Gate 4's stale assembly
  -> Gates 5 and 7 guards (specs exist, no implementation)
```

`DOTREF_COV` sits at 78.4% -- 55 dotref entries with no SYSCMD row. Some of
those 55 likely overlap the 27 seed-gap candidates, so 6.3 may move this number
on its own. Check before treating it as separate work.

---

## 7. Traps -- read before touching this lane

1. **`SYSCMD_IMPORT_v2.csv` has 215 rows and the table has 203. It is NOT a
   superset.** It lacks 15 deliberate maintainer entries: the nine `SET`
   compounds plus `BUILDLMDB`, `SETPATH`, `PREDHELP`, `WHERECACHE`,
   `STUDENTECHO`, `STUDENTHELLO`. A wholesale import destroys them. An earlier
   generator read the 40-row snapshot, reported 14.9% coverage against a true
   78.4%, and acting on that number would have erased exactly these rows.

2. **DBF path protocol.** `SETPATH DBF <dir>` then **bare** table names. Slashed
   relative paths resolve against the DATA root, not the DBF slot.

3. **`.dts` files are real DotTalk++ scripts.** Use `&&` for comments in
   single-token lines; free-text commands (`POST`, `CHAT`) must be comment-free.
   Run with `./datarun.ps1 -CommandLines 'DOTSCRIPT <abs path>'` -- there is no
   `-Script` parameter and `--script` binds positionally to `-CommandLines`.

4. **Never back up `dottalkpp\data\lmdb`.** It is derived; `BUILDLMDB CLEAN YES`
   rebuilds it in seconds. A recursive copy also drags in `backups\`, which
   compounds. This filled the disk mid-reload. The reload driver now hard-aborts
   above 500 MB.

5. **`.cdx` files looking old is CORRECT.** They are 488-776 byte declaration
   shells; the keys live in the LMDB envs, rebuilt every reload. Verify by size,
   not timestamp. To inspect tags: open the table, `SELECT` its area, `CDX INFO`
   -- `STRUCT` reports tags only when the index is open.

6. **`EXPORT` grammar is narrow:** `EXPORT [TO] <file> [CSV|PIPE]`. No
   `DELIMITER`, no `QUOTES`, no `SCHEMA`, no `REJECTS`. Those options in the old
   `tests/conversion/` scripts are why none of them could run. Write to `tmp/`;
   `_drops/` does not exist.

7. **Ten `CONTRACT_QA` warnings are arguably not defects.** `SET` declared in 12
   places is what a command family looks like; `ASCEND/DESCEND` and
   `TEXT/EDIT/COBOL` are multi-command files. These need a **contract convention
   for families**, not fixes. Until one exists they sit in the baseline as
   permanent noise -- which trains people to ignore the check, the worst outcome
   for a guard.

8. **`BANNER_CENSUS` 1031/1035 derived-only is honest.** Backfilled defaults
   correctly labelled as not-authority. Do not "fix" it by authoring fake
   provenance.

---

## 8. What I got wrong this half

Kept because the pattern matters more than the individual errors.

- **Backed up 47 GB of regenerable LMDB to protect a reload that regenerates
  it**, and the recursive copy included the archive pile. Filled the disk,
  aborted the reload mid-backup. "Back up everything to be safe" is a reflex,
  and it is wrong when the thing copied is rebuilt by the very next step.
- **Nearly filed a second false finding.** June-dated `.cdx` files against
  new DBFs looked like stale indexes. Checked the byte sizes first; they are
  declaration shells. One check away from repeating the Gate 4 mistake.
- **Built a guard that asked the wrong question.** The export "lost rows" check
  guarded against something structurally impossible -- the row count is checked
  against the DBF header. It fired anyway and caught a fabricated CSV row.
  Right alarm, wrong reason; rewritten as CSV-only-phantom adjudication.
- **Predicted the prepush gate would classify a CSV as a data fixture. It did
  not** -- the classifier keys on path, and `dottalkpp/data/scripts/` reads as
  scripts. A genuine fixture dropped there would pass unremarked.

The through-line, and the reason section 6.2 comes first: **every real defect
this session came from two things that never compared themselves.** The
harvester and the guard. The BUILDLMDB writer and its readers. The census
constant and the census query. The CSV and the table. None was visible to
reading a single file carefully; all were visible the moment something measured
both sides.

---

## 9. Registry state at close

```text
census gate    PASS   1035/1035 = 100%
registry gate  PASS   104 verifiable, 0 missing, 0 untracked, 3 external
AIF collision  PASS   64 intake rows, 64 distinct, AIF-065 claimed + reconciled
stack audit    FAIL 0 / WARN 18   (baseline current)
help guard     FAIL 0 / WARN 3    (CMDHELPCHK evidence owed)
manual guard   FAIL 0 / WARN 4    (assembly stale, 2026-07-23)
```

Working tree carries ~1,034 untracked paths, mostly generated candidates and
run artifacts. Not triaged here; not blocking.

`coordination/aif/AIF-065.claim` is live. Release it with
`session_coordinator.py release-aif` only if the lane is abandoned -- it is not.
