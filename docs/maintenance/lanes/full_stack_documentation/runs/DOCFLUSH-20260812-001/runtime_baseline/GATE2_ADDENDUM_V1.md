# Gate 2 addendum -- re-baseline at HEAD (flush v5)

    Run        : DOCFLUSH-20260812-001
    Recorded   : 2026-08-21
    Session    : COWORK-20260821-002 (member.ai.claude.cowork), sandbox, report-only
    Entry HEAD : cac02a8b5 (2026-08-21 09:16 -0700), branch development
    Supersedes : nothing. GATE2_BASELINE_REVIEW_V1.md stands; this adds nine
                 days of measured movement to it.
    Verdict    : Gate 0 preconditions CLEARED. Gate 2's decisive finding is
                 CLOSED. Gate 3 may open.

---

## 0. Why this file exists

v5 opened 2026-08-12 and stopped at Gate 0, blocked on a metacollect repair and
a stale SYSFUNC. Both cleared within 48 hours -- and neither the run record nor
the handoff was told. The store then moved a SECOND time, again outside a gate.
A resuming agent reading only the Gate 0 envelope and Gate 2 review would have
re-derived all of it and re-issued blockers that no longer exist.

Nothing below is asserted from those documents. Every figure is re-measured at
`cac02a8b5` and says which instrument produced it.

---

## 1. Gate 0 preconditions -- both CLEARED

**Envelope section 3, the metacollect link.** Repaired `d99f4ed9c`
(2026-08-14): `src/common/path_resolver.cpp` and `src/common/path_state.cpp`
added to the `dt_meta` target, at `CMakeLists.txt:742`. The commit body records
that `path_resolver.cpp` alone did NOT link and exposed four further undefined
`dottalk::paths` symbols, all of which `path_state.cpp` terminates -- so the
owner ruling the envelope was waiting on was made and the wider closure was the
one adopted. **Not verified here:** that the target builds. The sandbox cannot
build; the commit says verify by building, and Gate 4 is where that happens.

**Envelope section 3, SYSFUNC.** `b9d267df8` (2026-08-14, authored by
member.derald) added the `FN_FILE` row. Measured in the tree today:

    dottalkpp/data/scripts/metadata/SYSFUNC_IMPORT_v1.csv   75 functions, FN_FILE present
    (tracked; read by tools/fullstack_docs/edref_csv_v1.py and stack_audit_v1.py)

So `FN_COVERAGE`'s `IMPLEMENTED 75 / CATALOG 74` warn has its input. Confirming
the warn is gone requires a run; it is a Gate 4 assertion, not a claim here.

### 1a. A decoy of the same name sits in the repository root

    D:\code\ccode\SYSFUNC_IMPORT_v1.csv                     64 functions, NO FN_FILE
                                                            mtime 2026-06-27, UNTRACKED
                                                            md5 f13e2a58bfa96c5c154cb25e9a07cecb

Two files, one filename, eight weeks apart, and the stale one is the one at the
path a reader reaches first. Nothing in `tools/` or `src/` references the root
copy. The Gate 0 envelope cited `SYSFUNC_IMPORT_v1.csv` bare, without a
directory, which resolves to the decoy.

Recorded, not deleted -- an untracked root file is not this run's to remove.

---

## 2. The store moved AGAIN, on 2026-08-15, outside a gate

    dottalkpp/data/help/{HELP_LINE,HELP_ARTIFACTS,HELP_TOPIC,
                         HELP_SECTION,COMMANDS,CMD_ARGS}.dbf
    all six mtime 2026-08-15 19:49

That is the second ungated rebuild of this run -- the first is the condition the
envelope opened v5 to repair. No Gate 3 package, no Gate 4 validation, no
transcript. There is also no way to attribute the build to a commit, because
**HELP DATA still carries no provenance rows** (v6 hints section 2); the nearest
commit before that mtime is `d4661f4a3` (2026-08-15 12:25) and whether the tree
was clean at build time is not recoverable.

**But it did the job Gate 2 said was owed, and the store proves it.** Read
directly from `HELP_LINE.dbf` with `tools/fullstack_docs/dbfread.py`:

| SOURCE | Gate 2 (2026-08-12) | now (2026-08-15 store) | delta |
| --- | --- | --- | --- |
| USAGE_CONTRACT | 14,914 | 14,914 | 0 |
| SOURCE_MINER | 7,503 | 7,503 | 0 |
| SHARED_MSG | 2,637 | 2,637 | 0 |
| **DOTREF** | **896** | **992** | **+96** |
| CURATED_DOC | 868 | 868 | 0 |
| EDREF | 786 | 786 | 0 |
| FOXREF | 665 | 665 | 0 |
| REGISTRY | 462 | 462 | 0 |
| **total live lines** | **28,731** | **28,827** | **+96** |
| distinct TOPICKEY | 527 | 528 | +1 |

The entire movement is DOTREF, and +96 is the exact figure the 2026-08-12
handoff recorded for the three rewritten dotref entries ("added 96 rows, about
32 each"). Two independent measurements, taken nine days apart by different
instruments, agreeing to the row.

**Gate 2 section 2 is therefore CLOSED.** Its decisive finding was that
`dotref.hpp` was not in the running binary because the contracts slice had never
been committed. The slice landed as `c04ac1bdb`, an engine build followed, and
the 08-15 rebuild carried it into the store. No corrective mutation is owed for
that finding.

`include/dotref.hpp` is clean against HEAD today (`git show HEAD:... | diff
--strip-trailing-cr`), so the condition that produced the finding cannot be
present.

---

## 3. Q1 SETTLED -- the 205-vs-229 gap is not a coverage gap, and the
## envelope's hypothesis is false

The envelope asked whether the harvest is `src/cli`-shaped, which would mean
`src/edu` and four other subsystems were silently unmined. It is not, and they
are not. Measured at HEAD with `git grep -l`:

    literal "@dottalk.usage"        in .cpp   231
      of which "@dottalk.usage v1"  (mined)   209
      of which "@dottalk.usage.voluntary v1"   16
      remainder: the string in ordinary prose   6

The mined marker by directory:

    src/cli 184   src/edu 15   src/tv 4   src/help 2
    src/ext   2   src/meta 1   src/dewey 1              = 209

`src/cli` alone carries **184**, well below the 205 the ad-hoc build reported.
The harvest is tree-shaped; a `src/cli`-shaped harvest could not have reached
205. `src/edu`'s 15 mined files are in, not out.

**The 22-file difference is deliberate and self-labelled.** The 16 voluntary
files were demoted by owner ruling 2026-07-27 (AIF-067,
`tools/fullstack_docs/convert_subcmd_to_voluntary.py`): `command:` became
`documents:` for the SET family and its siblings, because only `command:` is an
identity and nine of them were sitting in live SYSCMD as top-level commands they
are not. Their blocks open with, in their own words:

    // NOT UNDER CONTRACT -- voluntary description, offered not promised.
    // Nothing verifies this block and nothing may fail because of it.

The remaining 6 (`cmd_rpg`, `cmd_trigger`, `cmd_ttestapp`, `cmd_vmware`,
`cmd_vt200`, `shell_commands`) mention the marker in narrative comments and
carry no block.

**Proven against the store, not inferred from source.** Probing 28,827 live
HELP_LINE rows for text that exists only in a voluntary block:

    "Report or set predicate/expression case-sensitivity"   0 rows
    "voluntary description"                                 0 rows
    "NOT UNDER CONTRACT"                                    0 rows
    "mutates_session_settings"                              0 rows

Zero. The miner searches the literal `@dottalk.usage v1`
(`src/help/helpdata_source_miner.cpp:1065`), which cannot match
`@dottalk.usage.voluntary v1`, and the string "voluntary" appears nowhere in
`src/help`. The behaviour matches the ruling exactly.

### 3a. The residual question the ruling leaves open, for AIF-114

The 2026-07-27 decision kept the blocks on the explicit ground that *"the
handler files' prose is BETTER than the ladder's, and deleting good
documentation to satisfy a schema would be the tool wagging the author."*

Measured consequence: that prose reaches no published surface. 14 of the 16 are
`cmd_set*.cpp`, which is `AIF-114 set-family-doc-drift`'s exact subject. Whether
the better prose should be promoted into the ladder's `@dottalk.subusage`
contracts, or should stay a source-reader courtesy, is that lane's ruling and
not this run's. Filed for it rather than acted on.

It is the same shape as `risk:` blocks (v6 hints section 6): a block that is
written, correct, and read by nobody downstream.

---

## 4. Re-measured entry facts

Compare against envelope section 5, which asked to be re-measured rather than
trusted.

| fact | envelope, 2026-08-12 | now, cac02a8b5 |
| --- | --- | --- |
| entry HEAD | 46bd9233f | cac02a8b5 |
| branch | development | development |
| dotref entries | 258 | 261 |
| foxref entries | -- | 175 |
| contract-bearing .cpp (literal) | 229 | 231 |
| mined marker `@dottalk.usage v1` | not measured | 209 |
| non-ASCII inside contract blocks | 0 | not re-measured this pass |
| HELP store | rebuilt ad hoc 08-12, no gate record | rebuilt ad hoc 08-15, no gate record |

`git --no-optional-locks` throughout; no index lock was taken.

---

## 5. Disposition

Gate 0 CLEARED. Gate 2 accepted as amended by section 2. Gate 3 open; the
package is `../help_refresh/HELP_REFRESH_PACKAGE_V1.md`.

Carried forward unchanged: Q2 (foxref and `FILE()`), Q3 (`risk:` blocks not
harvested), the three-separately-authored-descriptions finding, and the website
matrix CLOSING gate in `D:\dev\x64base-site`.

Newly filed: the SYSFUNC root decoy (section 1a) and the voluntary-prose
question for AIF-114 (section 3a).
