# Subcommand identity contract lane (AIF-067)

- **Lane**: AIF-067
- **Run**: DOCFLUSH-20260722-001
- **Member**: member.ai.claude.cowork
- **Owner**: member.derald
- **Status**: source_defined
- **Opened**: 2026-07-27
- **Siblings**: AIF-065 (LMDB mapsize override), AIF-066 (locale spine / HELP preview drift)

---

## 1. The gap in one sentence

DotTalk++ has no way to **declare** a subcommand, so a command handled inline in a
parent's dispatcher is invisible to the entire documentation chain: no contract, no
`SYSCMD` or `SYSSUBCMD` row, no HELP topic, and no way for a guard to notice.

## 2. How it surfaced -- four times, from three directions

| # | Symptom | Where it was found |
|---|---|---|
| 1 | `SET LANGUAGE` and `SET LOCALE` stranded as orphaned locale-preview fixture topics | AIF-066, `help_guard_v1` `LOCALE_DRIFT/ORPHANED_TOPIC` |
| 2 | `REL ENUM`, `SET VAR`, `SET VAR!` listed in `dotref.hpp` resolving through no path | `stack_audit_v1` `DOTREF_COV/SUBCOMMAND_ONLY` |
| 3 | `ERRORSTOP` and `INDEXTXN` dispatch correctly but are undiscoverable | measured here, section 3 |
| 4 | `SYSSUBCMD.dbf` seeded with scratch and left to rot | measured here, section 4 |

None of the four was found by the mechanism that should have found it. Each was found
sideways, by a guard built for a different purpose.

## 3. MEASURED: the ladder and its own usage text disagree

`cmd_set.cpp` dispatches its options as a flat `if (opt == "X")` ladder. `SET USAGE`
(`cmd_set.cpp:669`) calls `print_set_usage()`, which renders
`MessageId::SetUsageText` -- a hand-typed ~40-line string literal at
`src/help/helpdata_messages.cpp:9613`.

```
ladder options : 33      listed in SET USAGE : 30

IN LADDER, NOT LISTED : ERRORSTOP, INDEXTXN, SETCASE, SETNEAR
IN LISTED, NOT LADDER : (none)
```

`SETCASE` and `SETNEAR` are benign -- alias spellings of `CASE` and `NEAR`, both listed
under their canonical names. **`ERRORSTOP` and `INDEXTXN` are the real finding: two
working options a user cannot discover from the product itself.**

The aggravating factor is *where* that list lives: a **message-catalog entry**, so it
is translatable.

**Corrected 2026-07-27 -- the localization cost is PROSPECTIVE, not incurred.** An
earlier draft of this document asserted that "every locale replicates this drift".
That was stated as measured and was not measured. Checking:

```
MessageId::SetUsageText rows:  en-US  1     (de, es, fr, it: none)
helpdata_messages.cpp totals:  en-US  1054  .  de/es/fr/it  290 each
```

`SetUsageText` has not been translated. The drift therefore exists exactly ONCE
today. This is consistent with AIF-066's measurement of the messaging spine at 6.6%
coverage -- essential operator messages first, which this is not.

That strengthens rather than weakens the case for generating it: the right moment to
make a string derived is BEFORE four translators copy its errors, not after. Left
alone, the next locale pass converts a single-site defect into a five-site one, and
translated drift is far harder to retire than English drift because retiring it
invalidates paid work.

The general lesson is the one this run keeps re-learning: an aggravating factor is a
claim too, and "it must be worse across the locales" is exactly the kind of plausible
inference that gets written down as a finding without anyone running the grep.

## 4. MEASURED: the metadata layer already anticipated this, then went stale

`dottalkpp/data/metadata/SYSSUBCMD.dbf` exists with a considered 21-field schema:

```
SUB_ID PARENT SUB_NAME QUAL_NAME DISP_STYL IMPL_STAT VIS_TIER OWNER REG_RING
LIFE_PH SRC_AUTH SRC_FILE HANDLER PUB_SURF DISP_REACH OUT_ROUTE MSG_CAT
ACTIVE VER_AT NOTES
```

Field widths reconcile exactly (`sum(widths) + 1 == reclen == 982`) once the two X64
phantom descriptors are excluded, so the table is structurally sound.

Its **contents** are not. 12 rows:

- 3 blank rows
- the same three rows three times over -- `SET PATH`, `SET ORDER`, `REL ENUM`
- one of those batches marked `ACTIVE=F`

That is shape-test scratch, not a seed. And `REL ENUM` is one of the exact entries
`stack_audit` independently flagged as unresolvable, which means **the table already
contained the answer to a question a later guard had to rediscover from source.**

Separately, `dottalkpp/data/scripts/metadata/SYSSUBCMD_SEED_CANDIDATES_v1.csv` holds
37 harvested candidates in a **10-field** schema
(`SUBCMD_ID,PARENT_CMD,CAN_NAME,TOKEN,HANDLER,OWNER,ACTIVE,SRC_FILE,HELP_TOPIC,NOTES`)
against the table's **21-field** schema. Different field names, different arity. The
CSV cannot load into the table it was harvested for. Nothing ever tried, so nothing
ever said so.

## 5. The shape, for the third time

AIF-065: `BUILDLMDB` writes a mapsize; the attach paths overwrite it. Nothing compares.
AIF-066: `SOURCE_HASH` is written into `HELP_TOPIC_LOCALE`; nothing reads it.
AIF-067: three representations of the SET subcommand surface -- **the ladder, the usage
text, and the table** -- and no two of them are ever compared.

The recurring failure is not carelessness. It is that each pair was authored by a
different mechanism at a different time, and the codebase has no habit of making a
derived artifact *derived*. Where a thing is typed twice, it drifts.

## 6. DECIDED (member.derald, 2026-07-27): contract is authority, table is generated

Three options were considered and two rejected.

- **Rejected -- parent `USAGE` argument alone.** Already implemented, already drifted
  (section 3). Listing subcommands in prose does not give them identity, and a
  hand-maintained list is the defect, not the fix.
- **Rejected -- a `has_subcommands` boolean.** A flag asserts a list exists without
  saying what is on it, and **nothing can verify a bool**. It is the one design that
  cannot detect the error it is meant to prevent.
- **Rejected -- table as authority, hand-seeded.** This is what was attempted, and
  section 4 is the result.

**Adopted: `@dottalk.subusage v1`, a contract block placed adjacent to the ladder arm
it documents.**

### 6.1 Why a block and not a file

AIF-066's remedy for `AREA51` was *give it a file* -- correct, because `AREA51` was an
inline **top-level** command and a file was the identity it lacked.

The subcommand case is different and must not copy that answer. `SET LANGUAGE`'s
implementation genuinely belongs inside `cmd_set`'s dispatcher; a `cmd_set_language.cpp`
would be a fiction invented to satisfy the tooling. So identity comes from a **field**,
not a filename:

```
parent: SET
sub:    LANGUAGE
        -> QUAL_NAME "SET LANGUAGE"
```

`QUAL_NAME` is the key HELP, `SYSCMD` and `dotref` already index on -- and it is
already a column in the live 21-field schema, alongside `DISP_STYL: routed`. The
schema was designed for this model before the model was written down.

### 6.2 Placement rule

The block sits **immediately above its ladder arm**, in the parent's source file. This
is the whole point: contract and dispatch land in the **same diff hunk**, so drift
between them is visible to a reviewer without tooling. None of the rejected options
have that property.

### 6.3 Authority chain

```
@dottalk.subusage blocks   (source, hand-authored, the only authority)
        |
        v
SYSSUBCMD                  (generated -- never typed)
        |
        v
SET USAGE / HELP topics    (rendered -- true by construction)
```

`SET USAGE` keeps its message-catalog entry for framing prose. The **option list** is
no longer part of the translated string, which is what stops localization from
replicating drift.

## 7. Acceptance test

The lane is not done because code was written. It is done when the guard catches the
defect that opened it:

1. `stack_audit_v1` gains `SUBCMD_COV`, a three-way comparison of ladder arms vs
   `@dottalk.subusage` contracts vs live `SYSSUBCMD` rows.
2. Run against the tree **as it stands today**, it must report `ERRORSTOP` and
   `INDEXTXN` as ladder-present / usage-absent. A check that passes on the broken
   tree has proved nothing.
3. `SET USAGE` must then list both, without either name being typed into
   `helpdata_messages.cpp`.
4. `DOTREF_COV/SUBCOMMAND_ONLY` must fall to 0 as its three entries acquire contracts.

## 8. Honesty bounds

- The 33-vs-30 drift is **measured** from source, by parsing the ladder and the literal.
  It is not yet **runtime-observed**: `SET USAGE` has not been run against the new
  binary and diffed. Owed before promotion.
- The claim that `SETCASE`/`SETNEAR` are benign aliases rests on reading
  `cmd_set.cpp:1294,1305` (`opt == "CASE" || opt == "SETCASE"`). Confirmed by source,
  not by execution.
- `SYSSUBCMD`'s 12 rows were read directly from the DBF with field widths reconciled
  against `reclen`. The interpretation "3 blank + 3 batches of 3" is a reading of that
  dump; the *intent* behind those rows is inferred and no authoring record was found.
- Per `lesson.career.a_documented_option_is_not_an_honoured_option` (AIF-065): this
  lane documents options as *claims* until `SET USAGE` is executed and compared. The
  same lesson applies to its own remedy.

## 9. Owed

- Reconcile or retire `SYSSUBCMD_SEED_CANDIDATES_v1.csv` -- it cannot load as written.
- Decide whether `BUILD` and `ERROR` compound parents (harvest section 2) adopt the
  same contract or stay concatenated commands.
- `SET VAR` vs `SET VAR!` -- the `!` variant needs a naming rule before it can carry a
  `sub:` value.
## 9a. PLANTED FIXTURE -- `cmd_area51.cpp` is deliberately NOT harvested

**Do not "fix" this. Decided by member.derald, 2026-07-27.**

`stack_audit_v1` currently reports, and should keep reporting:

```
[WARN] SRCFILE_DRIFT/UNCOLLECTED: 1 tracked source file(s) absent from SRCFILE:
       src/cli/cmd_area51.cpp
```

That is true and the guard is right. `cmd_area51.cpp` was added on 2026-07-27
(AIF-066 follow-on) and the SRC* comment catalog has not been reharvested since.
The obvious next move is to run the reload driver and clear it. **We are not going
to.**

It is being held back on purpose as a **live fixture for the next full-stack pass**:
a real, tracked, contract-bearing source file that the catalog does not know about.
The optimized first-class pass now being designed should discover it without being
told, from its own traversal. Seeding the catalog first would remove the only
unplanted piece of evidence available to test that pass against.

WHY THIS NOTE EXISTS AT ALL
    A deliberate open finding and an ignored one look identical in a report. Left
    unlabelled, the next session reads a WARN with an obvious remedy, applies the
    remedy, and destroys the fixture -- correctly, by its own lights, because
    nothing told it otherwise. This project has already paid that bill once
    (AIF-061: a shipped WAL still labelled "intentionally no-op placeholders";
    a partner surveyed the header, reasonably believed it, and reported that no
    WAL existed). An intention that lives only in a chat transcript is not an
    intention the codebase has.

PASS/FAIL PREDICATE FOR THE NEXT PASS
    PASS -- the new pass independently reports `src/cli/cmd_area51.cpp` as present
            in the repository and absent from SRCFILE, without this note being fed
            to it as an input.
    FAIL -- it reports full coverage, or reports the gap only after being told
            where to look. Either means it is confirming a catalog rather than
            auditing a tree, which is the failure mode the whole run exists to
            close.

    On PASS, harvest it, delete this section, and record the catch as evidence.
    Until then the WARN stays and the baseline carries it.

## 10. `app_` is a reserved name, not an existing convention (corrected)

Recorded because the first reading was wrong and the wrong reading was acted on.

`git ls-files` shows `src/cli/app_army.cpp`, `app_erp.cpp`, `app_paxon.cpp`, which
looked like an established `app_` convention that a `cmd_ -> app_` rename could
extend. Reading the files says otherwise. Each is **184 bytes**: a `@dottalk.file`
banner and a single `#include`. No function, no registration, no code. Their headers
say so explicitly --

```
// role: Declares a LabTalk placeholder/stub application surface for army
```

-- and `src/CMakeLists.txt:226-230` removes all three from non-LabTalk builds.

So there is no working `app_` exemplar to copy, and equally no bad pattern being
propagated. A `cmd_ -> app_` rename would be **establishing** the convention. That
is a better position than inheriting a broken one, but it means the first renamed
file defines the shape for the rest and should be chosen deliberately.

Owed before any rename:

- Decide what `app_` MEANS as distinct from `cmd_`. The `@dottalk.usage`
  `category:` vocabulary currently has 23 values (`diagnostics`, `index`,
  `navigation`, `workspace`, `script`, ...) and no `app`. If an app is a category,
  it may not need a filename prefix at all; if it is a different KIND of thing, the
  prefix is right and the category should follow it.
- Confirm how an `app_` TU is expected to reach the prompt. `edu_` self-registers
  from a static initializer (`edu_case.cpp:202`), and `src/cli/` is picked up by
  `GLOB_RECURSE ... CONFIGURE_DEPENDS`, so a self-registering TU placed there is
  automatic. `src/edu/` instead has a CMake path rule (line 218) that STRIPS
  non-essential TUs from non-LabTalk builds. A self-registering TU that gets
  stripped silently loses its command -- which is the `SIMPLEBROWSER` /
  `SMARTBROWSER` failure mode arriving by a different road. Keep `app_*` under
  `src/cli/`, or add the rule deliberately and prove it.
- The browsers were not classified. No `registry().add` was found in
  `src/cli/browse/browse_cmd.cpp` or `src/browser/*.cpp`, so their command
  structure resolves some other way and should be traced before deciding whether
  they are apps, a third category, or their own subsystem.
