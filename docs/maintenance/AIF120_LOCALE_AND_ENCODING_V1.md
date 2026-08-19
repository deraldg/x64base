---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260819-COWORK-041
  recorded_at_utc: 2026-08-19T13:35:00Z
  agent:
    provider: Anthropic
    product: Claude (Cowork)
    model: claude-opus-5
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
    run_id: COWORK-20260818-001
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 564747371
  authorization:
    requested_by: maintainer (member.derald), in-session -- "as we build are we
      respecting international languages?" and then "look for existing are in dottalkpp
      in messaging - set locale".
  report:
    path: docs/maintenance/AIF120_LOCALE_AND_ENCODING_V1.md
    kind: ruling
---

# AIF-120 -- R33: the design table could not hold the languages x64base already ships

Status: **ruling, review-needed.** Owner: member.derald.
Author: member.ai.claude.cowork, run `COWORK-20260818-001`. Date: 2026-08-19.

## 0. A correction I owe before anything else

Asked whether this work respects international languages, I answered: **"no, we are
not respecting them, and it fails hard rather than degrading."** That was accurate
about the design table and **wrong about x64base**, and I said it without looking.

The maintainer then pointed at `dottalkpp` messaging and `SET LOCALE`. What is
already in this tree:

| | |
| --- | --- |
| `SET LOCALE TO <locale\|DEFAULT>`, `SET LANGUAGE TO`, `SET LOCALE CHECK`, `SET LOCALE REPORT` | `src/cli/cmd_set.cpp` |
| `message_catalog::text(Code)`, `text(Code, locale)`, `available_locales()`, `is_supported_locale()`, `normalize_locale()` | `src/cli/message_catalog.hpp` |
| **1,324 messages** | `SYSTEM_MESSAGES_IMPORT_v1.csv` |
| **4,756 localised texts across five locales** -- en-US 1,323, de 319, es 319, fr 319, it 319 | `SYSTEM_MESSAGE_TEXT_IMPORT_v1.csv` |
| an authority model governing all of it | `dottalkpp/docs/authority/help_message_reference_authority_model_v1.md` |

The catalog's design is worth stating because the DSL should adopt it rather than
invent one: **identity is locale-free** (`MSGID`, `SYMBOL`, `ENUMNAME`), **text is
keyed by identity plus locale** (`LOCALE`, and composite keys `MSGLOCALE` =
`0000000015|en-US`, `SYMBOLLOC` = `SYMBOL|en-US`), and each text carries a
`TXTHASH` so a translation can be told it has gone stale.

So x64base respects international languages. **The UI DSL does not, and until
today could not.**

## 1. R33.1 -- the codepage byte, read and written

The reader decoded every byte as `latin1` and never looked at header byte 29, the
language driver. The writer **declared** cp1252 in that byte and **encoded**
latin1, which is a different encoding across 0x80-0x9F.

The consequence was not degradation. A euro sign and a curly quote -- both ordinary
in the German and French text the catalog already ships -- raised
`UnicodeEncodeError` and the row was never written.

Now: seventeen language drivers map to codecs on read; the writer takes an
`encoding`, declares it in byte 29 and encodes with it. Measured round trip,
written and read back:

| text | codepage | byte 29 | before |
| --- | --- | --- | --- |
| `Prenom` with an acute e | cp1252 | 0x03 | worked |
| a euro sign | cp1252 | 0x03 | **threw** |
| `"quoted"` (curly) | cp1252 | 0x03 | **threw** |
| `Imie` with ogonek | cp1250 | 0xc8 | **threw** |
| `Onoma` in Greek | cp1253 | 0xcb | **threw** |
| Japanese | cp932 | 0x7b | **threw** |
| Arabic | cp1256 | 0x7e | **threw** |

## 2. R33.2 -- a DBF carries ONE codepage, and that is the real ceiling

This is a constraint of the container, not a defect to engineer around. A document
cannot hold Japanese and Greek at once, because byte 29 holds one value.

So the failure is reported as what it is:

```
cannot store 'Japanese text' (U+540D) in a cp1252 table: a DBF declares one
codepage in header byte 29 and every value must fit it
```

rather than as a codec error naming latin1, which told the caller nothing they
could act on.

**The owner's weighing:** one codepage per document is entirely workable for a
per-locale document set and fatal for one document in many languages. Section 4 of
this ruling is why that may not matter.

## 3. R33.3 -- binary columns were being decoded as text

Chasing the encoding work turned up an unrelated defect. The reader treated every
non-memo column as characters, and VFP has binary column types: `I` (4-byte
integer), `Y` (currency, int64 scaled by 10,000), `B` (double), `T` (datetime),
`W`, `G`, and the `0` null-flags column.

Across the corpus: **79 binary columns** -- 46 `I`, 20 `Y`, 3 `B`, and the rest.
Every one was being decoded as text and would have produced silent nonsense for any
caller that read it.

Now unpacked properly. Text-field decode failures across 279 files fall from
**15 to 1**, and the remaining fallbacks are `OBJCODE` (174) and `OLE` (14), which
are binary by design and correctly excluded from the count.

**No measurement in this lane is affected.** `STUDENTS.dbf` and `ACCOUNTS.DBF`
declare `N` and `C` throughout, and R30 and R31's corpus figures are byte-identical
after the change -- 363 inherited members, 2,687 rows, 274 unresolved. Checked, not
assumed.

## 4. R33.4 -- the caption should be a reference, not a literal

This is the proposal, and it is the owner's call.

`PROPS` carries `Caption = "STUDENTS"`. A literal, in one language, in the
document's one codepage. The catalog next door holds the same kind of text keyed by
`(symbol, locale)` with five locales already populated.

> **R33.4 (proposed).** A caption may name a **message symbol** rather than carry
> literal text -- `Caption = @FORM_STUDENTS_TITLE` -- resolved by the target through
> the existing catalog for the active locale.

What that buys, beyond the obvious:

- **One document renders in five locales**, using the mechanism `SET LOCALE`
  already drives.
- **R33.2's ceiling largely dissolves.** If captions are symbols, the table holds
  ASCII identifiers and the *catalog* holds the prose. A single-codepage container
  stops being a limit on which languages a form can display.
- **It follows R25.5 and R28.2**: a load-bearing value gets a named key, and
  meaning does not travel in a channel a reader may discard.

Not implemented. It touches the contract's section 7, the importer, every consumer,
and the catalog's own authority model -- and the authority model is owned
elsewhere, so it is a conversation before it is a commit.

## 5. Still open

- **Nothing measures how the DSL would map to the catalog.** How many distinct
  captions a form set contains, and whether they would collide as symbols, is not
  measured.
- **Text direction.** The contract defines `FLOW = row` as "children left to right".
  That is a hard-coded direction and wrong in an RTL locale. Untouched.
- **R25's width law assumes a fixed per-character advance**, which is wrong for
  double-width CJK and for Arabic shaping. The mechanism survives; the constants do
  not travel, which R25 section 8 already said for a different reason.
- **`TAG2` in one `.FRX`** still falls back to latin1 and is not classified.

## 6. Handoff to the maintainer -- PowerShell, run in `D:\code\ccode`

Run after the R32 commit.

```powershell
cd D:\code\ccode
git add docs/maintenance/AIF120_LOCALE_AND_ENCODING_V1.md
# NOTE added 2026-08-19 by R42: this block staged tools/uidef/read_vfp_binary.py (cite-check:ignore),
# which is gitignored by design. `git add` on an ignored path is a SILENT no-op, so R33's
# reader fix never reached the repository and every gate still passed. The reader that
# ships is tools/vfp/read_vfp_binary.py, promoted by R42. The dead line is removed.
git add tools/uidef/uidef.py
git add docs/maintenance/AIF120_LANE_STATUS_AND_FIXTURES_V1.md
git diff --cached --stat
git commit -m "AIF-120: R33 -- codepage honoured on read and write, binary column types unpacked; the DSL bypasses x64base's own locale catalog"
```
