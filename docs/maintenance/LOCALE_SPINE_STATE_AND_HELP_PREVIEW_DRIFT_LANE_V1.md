# Locale Spine: Messaging Mature, HELP Preview Fixture Stranded, Manuals Greenfield v1

Date: 2026-07-27
Status: **survey — measurements below are runtime/on-disk facts; one defect confirmed in source; drift itself NOT yet proven**
AI Friendly route: **AIF-066**
Run: `COWORK-20260726-001`   Member: `member.ai.claude.cowork`   Owner: `member.derald`
Mutation: documentation only. No table, source, HELP or index change.

Companion policy note: [`LANGUAGE_REGION_DOCUMENTATION_BOUNDARY_v1`](LANGUAGE_REGION_DOCUMENTATION_BOUNDARY_v1.md).
That note sets the *intended* boundary. This one records what is actually built,
where the two agree, and where they don't.

## Summary

There are **two** locale efforts in the tree, at very different maturities, and
they are not two halves of one attempt:

| Surface | State | Evidence |
| --- | --- | --- |
| Messaging spine | **mature, matches doctrine** | 1006 messages, 264 translated rows across 4 languages |
| HELP locale preview | **mechanism live, fixture stranded** | contract-bound reader in `cmdhelp.cpp`; data unchanged since 2026-06-11 |
| Manual localization | **greenfield, zero implementation** | `manual_assembly_manifest.yaml`: `exists: false`, `status: greenfield` |

The HELP work is **not** a leftover from an abandoned manuals attempt. It is the
opposite order: the boundary note names manuals as the highest-value target, and
implementation went HELP-first — plausibly because HELP already had the
topic/section/line table structure a locale companion could hang from.

## 1. Messaging spine — working as designed

```text
dottalkpp/data/locale/SYSTEM_LOCALES.dbf            5 rows   2026-06-03
    en-US  DEFAULT_ACTIVE   es / fr / de / it  ACTIVE   all LTR
dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf    5 rows   2026-06-03
dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf     1006 rows   2026-07-07
dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf 1270 rows   2026-07-07

SYSTEM_MESSAGE_TEXT locale distribution:
    en-US 1006  ·  de 66  ·  es 66  ·  fr 66  ·  it 66      (264 translated)
```

**66 of 1006 messages localised, 6.6%, in each of four languages.** That is a
faithful implementation of the boundary note's Priority 2 — "localize only
essential runtime/operator messages first" — rather than a stalled translation
project. Selected by `SET LANGUAGE` / `SET LOCALE` (`cmd_set.cpp:599,679`),
maintained by `MSGMGR SEED PRIORITY{A,B,C} APPLY`, consumed by
`src/help/message_catalog.cpp`.

Doctrine and data agree here. No action needed.

## 2. HELP locale preview — the mechanism is real and deliberately scoped

`src/cli/cmdhelp.cpp` carries its own contract:

```text
@dottalk.locale-preview-contract v1  PHASE23T_CMDHELP_LOCALE_PREVIEW_SOURCE_CONTRACT
    CMDHELP <topic> PREVIEW LOCALE <locale>
    CMDHELP <topic> LOCALE <locale>
    Locale preview is explicit-only and does not change normal CMDHELP behavior.
    Preview falls back to canonical/source HELP text when locale rows are
    missing or blocked.
    Rows with DRAFT_PLACEHOLDER or NEEDS_REVIEW fall back to source/default text.
```

`open_help_locale_area()` reads `HELP_TOPIC_LOCALE.dbf` (line 1820) and
`HELP_LINE_LOCALE.dbf` (line 1851). `help_guard_v1.py` watches all four
companions as its `LOCALE_SET` check. This is wired, contracted and guarded.

### The fixture

```text
HELP_TOPIC        714  <-  HELP_TOPIC_LOCALE      25    = 5 topics x 5 locales
HELP_SECTION    14637  <-  HELP_SECTION_LOCALE    25
HELP_LINE       29197  <-  HELP_LINE_LOCALE       75    = 5 x 5 x 3
HELP_ARTIFACTS  14637  <-  HELP_ARTIFACT_LOCALE   25
```

The five topics are `AREA`, `ABOUT`, `CMDHELP`, `SET LANGUAGE`, `SET LOCALE` —
the locale machinery documenting itself. `LOCALIZED_TITLE` values are literally
`AREA`, `[es draft] AREA`, `[fr draft] AREA`, `[de draft] AREA`,
`[it draft] AREA`. `TRANSL_STATUS` carries `SOURCE_CANON` and `DRAFT_PLACEH`.

**Those placeholders are not unfinished translation.** Under the contract above,
a `DRAFT_PLACEHOLDER` row is *supposed* to fall back to source — so a
placeholder that falls back correctly IS the test. 25 rows is a fixture proving
the fallback path end to end, and reading it as abandoned work is a mistake.

## 3. CONFIRMED DEFECT — the drift column is written and never read

`HELP_TOPIC_LOCALE` has 13 columns. `HelpTopicLocaleView`
(`cmdhelp.cpp:1434`) has **six**, and the reader fetches exactly those:

```text
table columns (13):  RUN_ID  TOPIC_LOCALE_ID  TOPICKEY  COMMAND  LOCALE_ID
                     TEXT_DIR  SOURCE_TITLE  LOCALIZED_TITLE  SOURCE_HASH
                     TRANSL_STATUS  REVIEW_STATUS  FALLBACK_APPLIED  CREATED_AT

reader fetches (6):  TOPICKEY  LOCALE_ID  SOURCE_TITLE  LOCALIZED_TITLE
                     TRANSL_STATUS  REVIEW_STATUS
```

`SOURCE_HASH` is **not fetched**, and the string does not appear anywhere under
`src/` or `include/`. The schema carries a source hash whose only conceivable
purpose is detecting that the underlying HELP text has changed since the locale
row was generated — and nothing compares it.

### Why that is worse than an ordinary gap

The failure is **indistinguishable from correct behaviour at the prompt**:

- a `DRAFT_PLACEHOLDER` row falls back to source text — by design, correctly
- a **stale** row, whose source has since changed, also falls back to source
  text — because nothing checks the hash

Both render the same. The mechanism that makes the feature safe is the same
mechanism that conceals its own staleness. There is no output difference to
notice, so drift can accumulate indefinitely without a symptom.

This is the same shape as AIF-065 and the source-set membership split: **two
things that never compare themselves.** Here the comparison was even designed
for — the column exists — and simply never wired up.

## 4. Drift is LIKELY but NOT PROVEN

```text
HELP_TOPIC_LOCALE.dbf     2026-06-11 14:07     (RUN_ID PHASE23J-F7C54B7D07BB2118)
HELP_SECTION_LOCALE.dbf   2026-06-11 14:07
HELP_LINE_LOCALE.dbf      2026-06-11 14:07
HELP_ARTIFACT_LOCALE.dbf  2026-06-11 14:07

HELP_TOPIC.dbf            2026-07-22 23:58     <- core rebuilt 6 weeks later
HELP_LINE.dbf             2026-07-22 23:58
```

The HELP core was regenerated on 2026-07-22; the locale companions were not.
Six weeks of potential drift on five topics.

**That is circumstantial.** Mtimes prove the core was rewritten, not that the
five fixture topics' text actually changed. Confirming it requires comparing
each locale row's stored `SOURCE_HASH` against a hash of the current
`HELP_TOPIC` / `HELP_LINE` content for those five topics. Recorded here as
**unproven** rather than asserted, per
`lesson.career.a_script_never_run_is_not_evidence`.

If they have drifted, the fixture no longer proves what it was built to prove.

## 5. Doctrine vs implementation — the priority inversion

`LANGUAGE_REGION_DOCUMENTATION_BOUNDARY_v1` is explicit that manuals and
educational documentation are the strongest near-term multilingual investment
(Priority 3), ahead of broad runtime translation, with region/culture formatting
deferred (Priority 4).

What is built:

| Priority | Doctrine | Built |
| --- | --- | --- |
| 1 | English authoritative for source, contracts, identifiers | yes |
| 2 | messaging/locale spine, essential operator messages | **yes — 66 msgs x 4 langs** |
| 3 | manuals and educational docs first; selected HELP material | **HELP only; manuals none** |
| 4 | region/culture formatting deferred | correctly deferred |

`manualgen` has exactly one locale reference, in
`tools/manualgen/manual_assembly_manifest.yaml`:

```yaml
source_of_record: "HRESULT catalog + message catalog + locale spine"
binding: {generator: "assembler:message-catalog", exists: false}
status: greenfield
```

`exists: false`. The locale spine is *named* as a source of record for a manual
section that has not been built. So the highest-stated-value surface has zero
coverage while the lower-priority one has a working preview.

That is not necessarily wrong — HELP already had the table structure to hang a
locale companion from, and manuals did not — but the divergence should be a
decision on the record rather than an accident.

## 6. What is owed

1. **Wire `SOURCE_HASH`, or drop it.** Either the reader compares it and reports
   drift, or a guard does, or the column is removed so it stops implying a
   protection that does not exist. A written-but-never-read integrity column is
   worse than no column: it looks like the problem is handled.
2. **Prove or disprove the drift** on the five fixture topics before extending
   anything. Two hashes and a comparison.
3. **Locate `PHASE23J`.** `PHASE23T` names the cmdhelp contract; `PHASE23J`
   names the data run that produced the fixture. No document referencing
   `PHASE23J` was found under `docs/`, `tools/` or
   `dottalkpp/data/scripts/`. Absence of evidence, not evidence of absence —
   but worth resolving before the fixture is regenerated by someone guessing at
   its intent.
4. **Decide the manuals question deliberately.** The HELP locale schema
   (source/localized pair + translation status + review status + fallback flag)
   is a proven pattern. If multilingual manuals are still the goal, that pattern
   is the thing to carry across — but nothing carries it today.

## 7. Method note

Everything in sections 1-3 is measured: row counts and locale distributions read
directly from the DBF files, mtimes from the filesystem, contract text and reader
columns from source. Section 4 is explicitly marked unproven. Section 5 is
document-vs-artifact comparison.

One correction worth recording: during this survey a shell probe printed
`[none above = no runtime reader]` unconditionally, immediately below a grep that
had in fact found two readers. The label was hard-coded, not conditional. Had it
been trusted, the entire finding would have inverted — "abandoned tables" instead
of "live mechanism with a stranded fixture." Diagnostic output that asserts a
conclusion the command did not compute is its own small instance of the pattern
this lane documents.

## Files

```text
src/cli/cmdhelp.cpp:30-43,1434,1602,1784,1820,1851   locale preview contract + reader
src/cli/cmd_set.cpp:599,679                          SET LANGUAGE / SET LOCALE
src/help/message_catalog.cpp                         message catalog consumer
dottalkpp/data/locale/SYSTEM_LOCALES.dbf             5 locales
dottalkpp/data/locale/SYSTEM_LOCALE_FALLBACK.dbf     5 fallback rules
dottalkpp/data/messaging/SYSTEM_MESSAGES.dbf         1006
dottalkpp/data/messaging/SYSTEM_MESSAGE_TEXT.dbf     1270 (264 translated)
dottalkpp/data/help/HELP_*_LOCALE.dbf                25/25/75/25 fixture, PHASE23J
tools/fullstack_docs/help_guard_v1.py                LOCALE_SET check
tools/manualgen/manual_assembly_manifest.yaml:205-209 greenfield, exists:false
docs/maintenance/LANGUAGE_REGION_DOCUMENTATION_BOUNDARY_v1.md   policy note
```
