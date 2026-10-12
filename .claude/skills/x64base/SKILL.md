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

## 5. Leaving a note when you touch another lane's work

`GOOD_NEIGHBOR_POLICY_V1.md` governs; this is only the field that gets omitted.
A note states what changed, whose area, **what authorization you were acting
under -- or `AUTHORIZATION: NONE`** -- and how to verify or undo. The authorization
line is what makes it a record rather than a courtesy, and `NONE` is the honest
entry, not a missing one.

Durability ladder, from the protocol: a quip is a sticky note between live
sessions and is ephemeral by design; `docs/ai-friendly/PSEUDO_CHAT_BOARD.md`
survives a fresh clone; `BBS SYSPOST` is the attributable, DBF-backed rung. A quip
to a session that is not checked in reaches nobody -- the tool says so; believe it.

## 6. Run IDs collide

`claim-aif` is atomic (`O_EXCL`). `checkin` is a bare write with no existence
check, so a date-plus-`001` run id silently overwrites another session's record.
Check the board and `coordination/aif/*.claim` before choosing one.
