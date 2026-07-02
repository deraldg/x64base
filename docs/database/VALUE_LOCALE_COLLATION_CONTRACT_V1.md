# DotTalk++ Value, Locale, and Collation Contract v1

Status: draft blocking contract.

Related:

- `../LANGUAGE_AND_REGION_SEAMS_v1.md`
- `DATABASE_SAFETY_CONTRACT_V1.md`
- `../gui/WINDOWED_APP_CONTRACT_V1.md`
- `../ui/CORE_UI_PRINCIPLES_V1.md`

## Purpose

DotTalk++ must not treat language, region, locale, encoding, and collation as a
late display feature. These concepts affect whether values are read correctly,
whether indexes are valid, whether searches find the right records, and whether
users trust what a GUI shows.

This contract defines the minimum rules for values before the database and GUI
lanes mature further.

## Core Rule

Stored bytes, logical values, displayed text, parsed input, and comparison keys
are different things.

No UI lane may collapse them into one string contract.

```text
physical bytes
  -> decoded field value
  -> typed logical value
  -> displayed text

typed user input
  -> parsed logical value
  -> encoded stored value

logical value
  -> collation/search key
  -> index key
```

The display locale may change how a value is shown. It must not silently change
the stored value or the index key.

## Required Terms

| Term | Meaning |
| --- | --- |
| Physical bytes | The exact bytes in DBF, memo, index, script, or metadata files |
| Encoding profile | How text bytes are decoded and encoded, such as CP437, CP1252, UTF-8, or unknown |
| Field dialect | xBase/DBF variant and field type behavior used by the table |
| Logical value | Typed value after decoding/parsing: text, numeric, date, logical, memo, blob, blank, null |
| Display value | User-facing text produced from a logical value and display locale |
| Parse locale | Locale used to interpret user/import text, such as decimal and date forms |
| UI language | Language used for menus, labels, messages, and help |
| Display locale | Locale used for formatting numbers, dates, currency, and sort previews |
| Collation profile | Rules for comparison, case folding, accent handling, trimming, blanks, and nulls |
| Index identity | The full expression, encoding, collation, and value policy that makes an index valid |

## Required Context Objects

The exact code shape may evolve, but the concepts must exist.

### Table Value Context

Every opened table should eventually expose:

- table path and dialect,
- DBF code page byte or detected encoding profile,
- memo encoding policy,
- default collation profile,
- date interpretation policy,
- numeric precision policy,
- blank/null policy,
- warnings for unknown or guessed behavior.

### Session Locale Context

Every UI session should carry:

- UI language,
- display locale,
- input parse locale,
- import/export locale,
- fallback locale chain,
- explicit user overrides.

The default can be `en-US`, but the context must still exist.

### Field Display Policy

Every field display should be derivable from:

- field name,
- field type,
- width and decimals,
- logical type override if metadata supplies one,
- display format,
- display locale,
- validation rules,
- null/blank behavior.

### Index Collation Identity

Every index/tag should be identifiable by:

- source table identity,
- key expression text,
- expression evaluator version,
- field encoding profile,
- collation profile,
- case folding rules,
- accent/diacritic policy,
- whitespace/trimming policy,
- blank/null ordering,
- numeric/date conversion rules,
- descending/ascending flags,
- filter/for expression identity.

An index built under one identity must not be silently reused under another.

## Hard Rules

- UI language, display locale, and table encoding are separate settings.
- Unknown encoding is a warning state, not a pretend UTF-8 success.
- Opening a table must not rewrite bytes to match the current UI locale.
- Display formatting must be reversible only when explicitly used as an input format.
- Import parsing must declare its parse locale or use a visible default.
- Indexes must carry enough identity to detect stale or incompatible collation.
- Seek/search behavior must declare whether it uses binary, legacy xBase, or Unicode collation.
- Case-insensitive search must not assume ASCII-only behavior unless the profile says so.
- Accent-insensitive search must be an explicit collation feature.
- Ambiguous dates must be rejected or parsed through an explicit policy.
- Numeric parsing must not depend on the OS process locale implicitly.
- Command output may be localized, but command IDs and status codes stay canonical.

## Value Behavior Matrix

| Value family | Storage issue | Display issue | Compare/index issue |
| --- | --- | --- | --- |
| Character | code page, padding, trimming | font fallback, mojibake warnings | binary vs language collation, case/accent rules |
| Memo | memo pointer validity, block size, encoding | large text preview, line endings | full-text search later, not normal DBF key by default |
| Numeric | width, decimals, overflow, blank numeric fields | decimal/thousands separators | numeric compare, not lexical compare |
| Currency | scale and rounding policy | currency symbol and grouping | exact scaled compare |
| Date | DBF date bytes, blank dates | locale display format | chronological compare |
| DateTime | timezone and epoch policy by dialect | timezone display | instant vs local-time compare |
| Logical | T/F/Y/N/? variants | localized yes/no labels | canonical tri-state ordering if nullable |
| Blob | memo/file pointer, binary integrity | preview policy | not comparable unless explicit |
| Null/blank | dialect-specific support | visible blank/null distinction | null ordering and filter semantics |

## UI Requirements

All first-class UI lanes should be able to show or inspect:

- table encoding and dialect,
- active display locale,
- active parse locale,
- active collation profile,
- warnings about guessed encoding or unknown dialect,
- whether indexes are valid for the active value/collation policy.

The windowed GUI should eventually surface this in a Structure/Properties view,
not only in logs.

## Search and Index Requirements

Searching a field and seeking through an index must not be treated as the same
operation unless their comparison policies match.

Minimum policies:

- binary byte comparison,
- decoded text exact comparison,
- legacy xBase comparison,
- Unicode case-sensitive comparison,
- Unicode case-insensitive comparison,
- optional accent-insensitive comparison.

If a search cannot use an index safely, the UI and command result should say so
and fall back to scan only when requested or clearly safe.

## Compatibility Modes

DotTalk++ needs both compatibility and modern behavior.

| Mode | Purpose |
| --- | --- |
| Legacy xBase | Preserve old application behavior and index compatibility |
| Strict legacy | Reject behavior not representable in old DBF/xBase forms |
| DotTalk++ modern | Allow stronger metadata, Unicode, explicit collation, and richer validation |
| Import repair | Read dirty data with warnings and repair/export tools |

The mode must be explicit in service/session state.

## Test Corpus Requirements

Add fixtures before relying on locale-sensitive behavior:

- CP437 text with box/legacy characters,
- CP1252 text with accents and smart punctuation,
- UTF-8 metadata or import text,
- mixed-case names with accents,
- Turkish dotted/dotless I case behavior,
- German sharp-s case behavior,
- Spanish/Swedish style sort expectations where practical,
- `en-US` and `de-DE` numeric parse/display examples,
- ambiguous date strings such as `01/02/2026`,
- blank dates and blank numeric fields,
- stale index built under a different collation identity,
- corrupt or unknown code page byte.

## Near-Term Implementation Tasks

1. Add value/context structs in a neutral runtime or GUI-core header.
2. Attach table encoding/dialect warnings to `OpenTableResult`.
3. Extend `TableSnapshot` with optional table value context metadata.
4. Add status codes for unknown encoding, guessed encoding, and collation mismatch.
5. Record collation identity in future index metadata and LMDB-backed index lanes.
6. Add Python mirror constants so the preview GUI can display the same concepts.
7. Add fixtures and smoke tests for encoding, display, and index compatibility.

## Non-Goals For v1

- Full translation of every UI string.
- Full ICU integration decision.
- Complete Unicode collation implementation.
- Automatic conversion of legacy DBF data.
- Live editing of locale-sensitive fields.

The immediate goal is to make the seams explicit so implementation cannot drift
into implicit process-locale behavior.
