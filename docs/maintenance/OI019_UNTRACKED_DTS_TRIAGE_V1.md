# OI-019 half (2) -- triage of the untracked DotScript corpus

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
