# OI-019 half (2) -- triage of the untracked DotScript corpus

**SUPERSEDED IN PART, 2026-09-07 -- read RESOLUTION at the end first.** The
counts in the body are the 2026-09-04 reading and are kept verbatim as the record
of what was believed then. They have since moved, and two of this sheet's own
methods were wrong in ways the resolution names.

    status      : mechanical triage, REPORT-ONLY; the ruling is the owner's
    raised      : 2026-09-04 (OI-019, half 2)
    owner       : member.derald   prepared by: member.ai.claude.cowork
    inventory   : docs/maintenance/OI019_UNTRACKED_DTS_INVENTORY_V1.csv
    measured    : 2026-09-04, this tree, at 4311b886f

Half (1) of OI-019 is closed: every one of the 75 specs registered in
`kRegressionSpecs` is tracked. This sheet is the other half, and it is
deliberately a CLASSIFICATION rather than a recommendation to `git add`. The
question each file poses is "intended, scratch, or generated", and that is a
judgment about intent that measurement cannot settle.

## The measurement

`dottalkpp/data/scripts` holds **350 `.dts` on disk, 144 tracked, 206 untracked
and NONE gitignored** -- 533 KB of omission rather than policy. No untracked file
is byte-identical to a tracked one, so none of this is a stale duplicate of
something already shipped.

Each untracked file was scored on ONE signal: does anything else in the tree name
it. That signal is not intent, but it is the only evidence in the tree, and it
sorts the corpus into four tiers of decreasing obligation.

| tier | meaning | files | size |
| --- | --- | --- | --- |
| A | cited by TRACKED ENGINE SOURCE (`.cpp`/`.hpp`) | 6 | 6.1 KB |
| B | cited by tracked docs, tests or tools, not by source | 51 | 107.6 KB |
| C | cited only by OTHER UNTRACKED files | 132 | 384.2 KB |
| D | cited by nothing in the tree | 17 | 35.5 KB |

Full per-file inventory, with the citing files: the CSV named in the header.

## METHOD WARNING -- read this before trusting any count here

**Substring matching produced a phantom and it looked exactly like a finding.**
The first pass matched basenames with fixed strings and no boundary, which
reported SEVEN tier-A files. The seventh was `regression.dts`, "cited" by four
tracked engine sources -- and every one of those citations is a substring of
`rel_join_enum_regression.dts`, which is tracked and unrelated. Requiring the
match to start at a filename boundary dropped it. Short names are the whole
hazard here: `x64.dts` matches inside `mcc_build_x64.dts`, and a corpus of 206
names contains many such prefixes.

That is the SECOND measurement error of this shape in one sitting. The first,
recorded in OI-019 itself, was a doubled path separator that reported six
untracked default-suite specs -- the same count the stale row asserted, naming a
different six. Both were caught only by re-deriving the number a second way.
**Every tier below is a machine's reading of names in text. Spot-check before
acting on it.**

## Tier A -- six files, and they are not one problem

Two are RUNTIME WIDOWS, and this is the OI-013 shape pointed at the shipping
binary rather than at documentation:

- `dottalkpp/data/scripts/x32.dts` <!-- cite-check:ignore --> and
  `dottalkpp/data/scripts/x64.dts` <!-- cite-check:ignore --> are named by
  `src/tv/foxtalk_menu.cpp:40-41`, which builds two `TMenuItem`s labelled "Load
  x32 Environment" and "Load x64 Environment" -- each label naming its script in
  parentheses, each item carrying the command string `DO X32` / `DO X64`.
  Neither file is in the repository. A fresh clone therefore ships a
  menu whose entries cannot resolve. Both are trivial -- two and three `SET PATH`
  lines -- which is precisely why they were never noticed.

Two are genuine complements to tracked code:

- `dottalkpp/data/scripts/limits/limits_record_advisory_shakedown.dts` <!-- cite-check:ignore -->
  is named by `src/tests/test_x64_record_limit.cpp:17` as the script that
  complements that unit test.
- `dottalkpp/data/scripts/pinocchio/wal_phaseA_proof.dts` <!-- cite-check:ignore -->
  is named by `src/cli/cmd_regression.cpp:420` as the BASIS of a registered
  regression entry.

Two are explicitly SUPERSEDED, and tracking them would be the wrong move:

- `dottalkpp/data/scripts/commit_rollback_test.dts` <!-- cite-check:ignore --> and
  `dottalkpp/data/scripts/suites/commit_rollback_test.dts` <!-- cite-check:ignore -->
  appear only in `src/cli/cmd_regression.cpp:417`, in a NOTE saying the
  `WAL_COMMIT_ROLLBACK` entry replaces "the legacy commit_rollback_test.dts,
  which assumed an already-open `students` table, did not self-bootstrap
  (regression doctrine violation), and silently no-op'd when run standalone."
  The citation is an epitaph, not a dependency.

**So tier A is 4 to track and 2 to delete**, and reading the citation rather than
counting it is what separates them. A gate that only counted would have filed all
six the same way.

## Tier B -- 51 files, the judgment tier

Cited by tracked prose and tooling: 38 citations from `docs/`, 15 from `tests/`,
8 from `dottalkpp/`, 7 from `DOTSCRIPT_README_TESTING.md`, 5 from `tools/`. These
are the files a reader is TOLD to run and a fresh clone does not have. No
compile breaks and no menu misfires, so the cost is a reader following an
instruction that cannot be carried out -- the same class as OI-013's contract
registry listing contracts whose text is absent.

This tier is where the intended/scratch question actually bites, and it should be
walked with the citing document open. A file cited by an accepted manual is a
different obligation from one cited by a 2026-05 autolog.

## Tiers C and D -- 149 files, 420 KB, the likely scratch

Tier C is self-referential: 132 files cited only by other untracked files. Tier D
is cited by nothing at all. Their distribution is the tell -- 55 sit loose at the
top level of `scripts/`, then `canaries` 25, `legacy` 23, `suites` 11. Filenames
in this group include forms no build would ever resolve, such as one literally
named `CREATE TABLE command_avatars.dts`, which is a pasted fragment saved as a
file.

**Recommendation, offered as one:** tiers C and D are the right place to STOP
rather than to start. Nothing in the tree depends on them, so the cost of leaving
them untracked is zero today, and the cost of bulk-adding 420 KB of unexamined
scratch is a corpus nobody can later distinguish from the real suite. If they are
to be resolved, the cheap and honest move is a `.gitignore` rule that makes the
omission POLICY rather than accident, so the next audit stops re-finding them.
That is a decision, not a cleanup.

## What is owed

1. Track the four tier-A files, ideally with `x32.dts` and `x64.dts` treated as
   the urgent pair -- a shipping menu points at them.
2. Rule on the two superseded `commit_rollback_test.dts` copies: delete, or keep
   and say why in the NOTE that already names them.
3. Walk tier B against its citing documents. 51 files, and the answer differs
   per citing artifact.
4. Decide C and D as a class: ignore-by-policy, or leave and stop counting them.

Only step 1 is mechanical. The rest is the ruling this sheet exists to inform.

---

## RESOLUTION 2026-09-07 -- half (2) is ruled and actioned

Owner rulings taken this session, in response to the three questions this sheet
left open. Re-measured from scratch first, because this row's own METHOD WARNING
says a wrong measurement that agrees with a stale headline is the most expensive
kind, and the 2026-09-04 numbers were three days and two authoring sessions old.

### The re-measurement

| | 2026-08-24 | 2026-09-04 | 2026-09-07 |
| --- | --- | --- | --- |
| `.dts` on disk | 332 | 350 | **366** |
| tracked | 87 | 144 | **154** |
| untracked | 245 | 206 | **212** |
| gitignored | 0 | 0 | **0** |
| untracked bytes | -- | 533 KB | **557 KB** |

Tracked-but-missing-from-disk: **zero**. The registration side is sound; this
was only ever an omission of the targets.

### Two method corrections, and both inflated a tier

**1. THE SHEET'S OWN INVENTORY WAS BEING COUNTED AS A CITATION.**
`OI019_UNTRACKED_DTS_INVENTORY_V1.csv` is tracked and names every untracked
script. A citation walk that reads it therefore reports "cited by a tracked
file" for the entire corpus. First pass this session returned **tier B = 196**
on that basis. Excluding this sheet, its inventory, and `OPEN_ITEMS.md` brings
it to 54. **Bookkeeping ABOUT a set is not a citation OF it**, and a ledger that
counts itself will always report that everything is load-bearing.

**2. SUBSTRING MATCHING MADE FOUR PHANTOM TIER-A ENTRIES.**
Matching a bare basename found `x64.dts` inside `mcc_build_x64.dts`,
`regression.dts` inside `cascade_env_regression.dts`, and `test.dts` inside
`commit_rollback_test.dts`. That reported **tier A = 8**. Requiring the name to
stand alone -- a left boundary that permits `/` and `\` and quotes but not
filename characters -- gives **tier A = 5 names / 6 files**, which is what the
2026-09-04 pass found by hand. Same family as the doubled-separator bug this
sheet already records: **the path arithmetic is where these measurements break,
every time.**

### Tier A -- DONE

Read, not counted. The four tracked and the two retired divide on what the
citing line actually SAYS, not on how many lines mention them:

| file | citing line | disposition |
| --- | --- | --- |
| `x64.dts` | `src/tv/foxtalk_menu.cpp:40` -- live `TMenuItem` shipping `DO X64` | **tracked** |
| `x32.dts` | `src/tv/foxtalk_menu.cpp:41` -- live `TMenuItem` shipping `DO X32` | **tracked** |
| `limits/limits_record_advisory_shakedown.dts` | `src/tests/test_x64_record_limit.cpp:17` -- "Complements ..." | **tracked** |
| `pinocchio/wal_phaseA_proof.dts` | `cmd_regression.cpp:502` -- "the self-contained basis is ..." | **tracked** |
| `commit_rollback_test.dts` | `cmd_regression.cpp:499` -- "this entry REPLACES the legacy ..." | **retired** |
| `suites/commit_rollback_test.dts` | same note | **retired** |

`foxtalk_menu.cpp` is in the build (`src/tv/CMakeLists.txt:20`), so the urgent
finding is confirmed: **a fresh clone shipped a menu with two items that could
not resolve.** That is now closed.

The two retirements were verified before moving, not inferred from the note:
both open with `select students` against a table they do not create, and both
have the terminal verb commented out (`* commit`), so run standalone they
measure nothing. They were never tracked, so nothing left the repository; they
sit in `dottalkpp/data/scripts/_to_delete/` for the owner's removal, since the
device bridge cannot delete. The note at `cmd_regression.cpp:499` now says it is
an epitaph and dates the retirement.

### Tier B -- RULED: track all 53 (131 KB)

Owner ruling 2026-09-07. The argument that closed half (1) applies unchanged:
tracked prose names them, so either they are in the repository or the citation
is a lie. Nine are named by tracked TEST-PROCEDURE documents
(`tests/README_TESTING.md`, `DOTSCRIPT_README_TESTING.md`,
`docs/WORKFLOW_RUNBOOK_v1.md`), which means a clean clone could not follow its
own documented procedures.

### Tier C/D -- RULED: leave untracked, and this is the record of why

Owner ruling 2026-09-07. **153 files, 420 KB, named by no tracked file.**
Deliberately untracked scratch: one-off canaries, superseded metadata seeds,
and experiments, many with spaces in the filename. `.gitignore` is NOT changed
-- this paragraph is the policy, so the next measurement reads 153 uncited
`.dts` as a decision rather than re-finding it as an omission.

**A future walk should expect this number to be non-zero and should not file it
as a finding.** What WOULD be a finding is a tier C/D file acquiring a tracked
citation, which moves it to tier B by definition.

### One hazard this triage surfaced and did not resolve

Eleven untracked scripts share a basename with a file already tracked
elsewhere. Five are byte-identical; **six are forks -- same name, different
content**:

    dottalkpp/data/scripts/SYSTEM_METADATA_BOOLEAN_FIX.dts   vs tests/manual/dotscript/quarantine/
    dottalkpp/data/scripts/SYSTEM_METADATA_SEED_v1.dts       vs tests/manual/dotscript/metadata/legacy/
    dottalkpp/data/scripts/SYSTEM_METADATA_SEED_v2.dts       vs tests/manual/dotscript/metadata/
    dottalkpp/data/scripts/SYSTEM_METADATA_VALIDATE_v0.dts   vs tests/manual/dotscript/metadata/
    dottalkpp/data/scripts/legacy/version.dts                vs dottalkpp/data/tests/version.dts
    dottalkpp/data/scripts/cases/date_implementation_dev.dts vs tests/manual/dotscript/legacy/  (cite-check:ignore -- tier C/D, untracked by ruling)

Five of the six are tier B and are now tracked under the ruling above, which
makes the ambiguity VISIBLE in git rather than latent on one machine. It does
not make it safe: `DO <name>` resolves through the SCRIPTS path slot, so which
copy runs depends on a runtime setting. **Two files with the same name and
different content, reachable by one unqualified verb, is a defect waiting for a
day when the answer matters.** Owner ruling owed; recommend an OI of its own
rather than folding it into this one.

### Status

Half (1): closed `1f61c22e4`. Half (2): closed here. The inventory CSV remains
the **2026-09-04** snapshot and is not regenerated -- it is a dated record, and
this section is the authority for what changed after it.
