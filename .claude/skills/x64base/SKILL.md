---
name: x64base
description: Source-of-truth map and measurement traps for the x64base / DotTalk++ tree -- which table is authoritative when several look like it, how to prove a command worked, and the search mistakes that produce confident wrong answers. Use when reading engine metadata, the help surfaces, or the glossaries, or when verifying that a mutation landed.
---

# x64base -- what CLAUDE.md does not carry

**This file deliberately does not restate `CLAUDE.md` or `AI_TIER1_SEED_V1.md`.**
Both are already in front of you. Repo roles, the portal walk, git rules, build and
run, closeout, commit coordination: read them there. AIF-082 6.8 -- two shims that
restate will diverge, and have.

**No counts here, only the command that measures them.** Every figure this file
could have asserted has already moved once. Measure.

## 1. Which source is authoritative when several look like it

Several obvious-looking tables are decoys. Each one below cost a wrong conclusion,
and one of them reached a second lane's review before it was caught.

| You want | Use | NOT |
| --- | --- | --- |
| command surface | `SYSCMD` (`CMD_ID, CAN_NAME, TYPE, VIS, HANDLER, ACTIVE`) | -- |
| command prose | `dottalkpp/data/help/HELP_ARTIFACTS.dbf`, and `docs/manuals/command_reference/command_reference_guide_v1.csv` (`summary, usage, effect, mutates, examples`) | **`SYSHELP` -- vestigial. A conclusion drawn from it was wrong by two orders of magnitude.** |
| house coined vocabulary | `labtalk/ai_portal/AI_GLOSSARY_V1.md` | `docs/glossary/*.csv` |
| reader terminology, aliases, legacy wording | `docs/glossary/glossary_master_v0.csv`, `alias_map_v0.csv`, `legacy_terms_v0.csv` | `AI_GLOSSARY_V1.md` |

**The two glossaries are different instruments, not versions of each other.** The
first records terms the house MINTED -- doctrine. The second is a reader's
dictionary: what a word means, what to say instead, what has been retired. They do
not overlap. Both are projected to the site by
`tools/fullstack_docs/glossary_sync.py` (`emit` / `check`); `check` is a drift gate.

Measure rather than cite:

    $py12 = Join-Path (git rev-parse --show-toplevel) '.venv312\Scripts\python.exe'
    & $py12 -c "import sys;sys.path.insert(0,'tools/fullstack_docs');import dbfread;t=dbfread.read('dottalkpp/data/help/HELP_ARTIFACTS.dbf');print(t.live)"

## 2. Reading a DBF

`t = dbfread.read(path)`, then **`t.live`**. Not `t.records` (does not exist) and
not `len(t)` (raises). A `hasattr(t,'records')` fallback once printed `rows=0` for
a populated table and the zero was believed.

**Parsing a header by hand: take the offset from the constant, never by probing
for an alignment that looks right.** x64 field descriptors begin at
`xbase_64.hpp`'s `LARGE_HEADER_SIZE`, which is `32 + sizeof(LargeHeaderExtension)`
= **96**. A probe that tried 32, 68, 76, 128 and 256 locked onto a false
alignment at 128 and produced a clean, plausible, correctly-typed 21-field table
-- with the first field, `WS_ID`, silently missing. **In a fixed-width format a
wrong offset does not look wrong**; it looks like a table with one fewer column.
The tell was arithmetic: catalog v2 has 22 columns and the parse found 21.
Reconcile the count against something that knows it before quoting the schema.

## 3. Proving a command worked

The catalog already declares what state each command touches: the `mutates` column
of `command_reference_guide_v1.csv`. Use it to choose the readback.

| declares | the check that proves it |
| --- | --- |
| `table-data` | read the field back |
| `cursor`, `record-pointer` | check `RECNO` and `EOF` |
| `index`, `order-state` | `SEEK` a known key -- an unordered area reports not-found for rows that exist |
| `memo` | re-read the memo |
| `table-buffer`, `stale-state` | **a write may be buffered; navigation discards it silently.** Confirm commit state |
| `none` | nothing to prove |

A success message is not durability. The vocabulary is semi-structured -- a real
head and a free-text tail -- so an unmapped token means "no rule", never "no risk".

## 4. Search traps that produce confident wrong answers

- **A query shaped by the object you already have cannot find an object with a
  different schema.** Grepping a CSV's column names to check whether a prose file
  exists will "prove" absence. Vary the query form before concluding a thing is
  not there.
- **A caveat is not a control.** Flagging data as stale and then reasoning from it
  is the same error as not flagging it. If `origin/main` is behind, fetch or stop.
- **`git grep` is indexed and fast; a filesystem `grep -r` over this tree is not**
  and will hit the timeout. Bound every filesystem search, and exclude
  `node_modules` in the site repo.
- **Tool-dependent coverage.** Ripgrep honours `.gitignore`; `find | xargs grep`
  does not. Two sweeps of "the tree" can return different populations. Name the
  tool when you report a count.
- **A workspace's state lives in THREE roots, not one.** DBF, INDEXES and LMDB are
  separate path slots and they move as a set (R131). A posture's `index=` resolves
  against IDXROOT, never beside the `.dbf`. So an `ls` of the DBF directory answers
  a different question than the posture asks -- answering it anyway produced
  "twelve declared index files, zero of them exist" about a workspace whose
  indexes were all present and attaching. Two lines settle it:

        do x64
        workspace open dbf

  The first prints every slot it resolved. The second prints `[index: ...,
  attached]` per area. A count that disagrees with those is counting something
  else.
- **A SELECTOR IS A SILENT FILTER, AND ZERO IS ITS FAVOURITE ANSWER.** Ten memo
  helpers gate on `(f.type == 'M') && f.length == xbase::X64_MEMO_FIELD_LEN`, and
  that constant is **8** -- the uint64 object-id slot. `WORKSPACES.SNAPSHOT` is
  **M(16)**, a 16-hex MemoRef token, so every one of those helpers takes its "no
  memo fields here" branch. The reachability scanner then returned `orphan objects
  0 / reclaimable 0 / status OK` for a 3.1 MB store **it had never read a field
  of**, and PACK silently took its no-memo path on the one table whose memo field
  is the point of the table. **Before believing a zero, check that the selector
  matched anything at all.** Two widths, two conventions, one predicate.
- **Ask whether the shape you are testing can even be built.** `cmd_create.cpp`
  hard-codes memo width -- 8 for x64, 10 for legacy -- and **discards the width
  the caller asked for**, so no `.dts` can construct an M(16) table; the only
  producer in the tree is `cmd_workspace.cpp`. That is *why* the trap above
  survived: nothing reachable from a script can make the thing the predicates
  mishandle. When a fixture cannot be built, the absence of a test is structural,
  not an oversight -- say so instead of promising a spec that cannot exist.
- **A PIPELINE'S EXIT STATUS IS THE LAST COMMAND'S.** `cp A B 2>&1 | head -2 &&
  echo "write SUCCEEDED"` prints SUCCEEDED when `cp` fails -- the `&&` is reading
  `head`. In the same line, `ls` without `-a` hid the dotfile that would have
  disproved the claim. **Two instrument defects in one line, in opposite
  directions.** Test the command's own `$?`, and name the artifact you expect to
  see. (Corrected by that probe: `.claude/` **is** writable from the remote shell
  -- `cp` exit 0 -- so an earlier note saying remote writes there are blocked is
  wrong for the shell, whatever is true of `device_commit_files`.)
- **Take a line number from `grep -n`, never by counting inside a `sed -n 'A,Bp'`
  window.** Four citations in one document were off by one to three lines that
  way. Nothing downstream catches it: `check_cited_paths.py` resolves PATHS, never
  LINES (OI-046), so it prints a green on a document whose line numbers are all
  wrong. The only check that works is to print each cited line back and compare it
  to the claim it supports.

## 5. The engine's prose states defaults, and a default forbids nothing

A help sentence of the form **"X is chosen by Y"** licenses a default. It is not a
constraint, and it is never the validity authority. Read past it to the function
whose job is to answer that question.

    WORKSPACE help:  "Without CNX/INX/CDX, index files are chosen by DBF flavor:
                      true x64/v128 CDX, classic VFP/v32 CNX."
    the authority:   valid_index_types_for() in src/cli/cmd_use.cpp, which returns
                     "CDX, CNX" for an x64 area and "CNX, INX" for a classic one

Taking the first for the second turns a sanctioned file into a reported defect.
CNX on x64 is accepted by owner ruling (AIF-099); CNX and CDX are two different
index technologies with two different openers, not a right and a wrong spelling of
one thing. The leading clause is the tell -- **"Without ..."** is there because the
explicit keyword form exists, and `WORKSPACE OPEN <target> CNX` is in the contract.

The shape generalizes well past indexes. Before calling anything non-conforming,
find the function that owns the valid set and read what it returns.

## 6. Leaving a note when you touch another lane's work

`GOOD_NEIGHBOR_POLICY_V1.md` governs; this is only the field that gets omitted.
A note states what changed, whose area, **what authorization you were acting
under -- or `AUTHORIZATION: NONE`** -- and how to verify or undo. The authorization
line is what makes it a record rather than a courtesy, and `NONE` is the honest
entry, not a missing one.

Durability ladder, from the protocol: a quip is a sticky note between live
sessions and is ephemeral by design; `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`
survives a fresh clone; `BBS SYSPOST` is the attributable, DBF-backed rung. A quip
to a session that is not checked in reaches nobody -- the tool says so; believe it.

## 7. Run IDs collide

`claim-aif` is atomic (`O_EXCL`). `checkin` is a bare write with no existence
check, so a date-plus-`001` run id silently overwrites another session's record.
Check the board and `coordination/aif/*.claim` before choosing one.
