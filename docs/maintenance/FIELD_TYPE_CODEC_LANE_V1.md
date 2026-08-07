# FIELDTYPE -- Field-type codec architecture (lane v1)

Status: **design done; M1-M5 proven (both interop directions)** (dev). Optional
spec/website update pending. Not promoted.
Owning lifecycle: DotTalk++ SDLC.
Truth state: source-defined (verified against `D:\code\ccode`, 2026-07-20).

## Why this lane exists

Investigation (2026-07-20) traced the field-type path from the trinity headers
(`xbase.hpp` neutral `FieldDef`, `xbase_vfp.hpp` `VfpField` descriptor,
`xbase_64.hpp` x64 metadata) down to storage and found:

**The engine stores every field as fixed-width text.** `record_view.cpp`
`loadFieldsFromBuffer` decodes each field (except x64 memo) as raw bytes +
`rtrim` (`:142`); `storeFieldsToBuffer` encodes by copying the text, space-padded,
**truncated to `f.length`** (`:188`). There is no binary encode/decode anywhere.

Consequence -- the four "modern" VFP binary types are a facade:

| Type | Created width (`cmd_create.cpp`) | Real VFP encoding | x64base today |
| --- | --- | --- | --- |
| `I` Integer | 4 bytes | 4-byte little-endian int32 (+/-2.1 B) | **4 ASCII chars -> max 9999** |
| `B` Double | 8 bytes | 8-byte IEEE-754 | 8 ASCII chars |
| `Y` Currency | 8 bytes | 8-byte int64 scaled 10^4 | 8 ASCII chars |
| `T` DateTime | 8 bytes | 4-byte julian + 4-byte time | 8 ASCII chars, **no write validation** (`default:` in `cmd_replace.cpp:527`) |

This is the confirmed root cause of the `SID I` truncation (AIF-017): `SID I` is a
4-byte field, `50000000` stored as text truncates to `5000`, hence the `N(8)`
workaround. Write-validation exists for I/B/Y (`cmd_replace.cpp:500-525`) but the
value that passes validation is then stored as text that doesn't fit.

Secondary: `D` date coercion (`cmd_replace.cpp:362`) rejects blank/empty dates and
mishandles bare-numeric literals (AIF-028).

## Design -- a codec registry (this IS the custom-field-type model)

Per maintainer directive, the way we handle built-in field types must **be the
extensibility model for custom field types**. So field-type handling becomes a
**registry of codecs keyed by type char**, not a hardcoded switch. A built-in type
and a user-defined custom type are the same kind of thing: a `Codec`.

```cpp
// include/xbase/field_codec.hpp
namespace xbase::fieldcodec {
struct Codec {
    // Decode f.length raw on-disk bytes into the engine's text value.
    std::string (*decode)(const char* bytes, std::size_t len, const FieldDef& f);
    // Encode text into exactly f.length bytes at out (caller pre-fills the field
    // region). Return false + *err on an invalid value.
    bool (*encode)(const std::string& text, const FieldDef& f, char* out,
                   std::string* err);
    const char* name;   // "int32", "double", "currency", "datetime", "text", ...
};
const Codec& codec_for(char type);        // built-in or registered; text fallback
void         register_codec(char t, Codec);  // custom field types plug in here
}
```

The two storage seams (`loadFieldsFromBuffer`, `storeFieldsToBuffer`) dispatch
through `codec_for(f.type)` instead of the inline text copy. The x64-memo path
stays special (it needs the object-id/sidecar lifecycle) -- everything else,
including future custom types, is a `Codec`.

**Custom-type contract** (the payoff): a custom field type is registered with a
type char, a width, and a `Codec`. `CREATE`/validation/storage/round-trip all work
through the same registry with no engine edits -- the "planned custom field types"
lane the website already advertises becomes real.

## Milestones

- **M1 -- codec seam + text default + `I` int32. PROVEN (2026-07-19).** New
  `field_codec` module; the text codec reproduces today's fixed-width behavior
  byte-for-byte (C/N/F/D/L/M unchanged); the `I` codec encodes/decodes 4-byte
  little-endian int32 (all-spaces = blank guard for append-blank). Both storage
  seams wired (`src/xbase/record_view.cpp` **and** `src/cli/record_view.cpp` -- the
  `.obj` in the exe shadows the lib copy). Proof, run live:
  `CREATE X64 T1 (SID I)` -> `APPEND` -> `REPLACE SID WITH 50000000` -> `GO TOP` ->
  `? SID` => `50000000` (not `5000`) -- **AIF-017 retired.**

  Shakedown also surfaced a real upstream defect, now fixed: `REPLACE`'s numeric
  RHS was formatted through a `std::ostringstream` **without** imbuing the classic
  locale, so the process/global locale injected thousands separators
  (`50000000` -> `"50,000,000"`), which then failed `parse_i32_strict` (and, for
  `D`, `YYYYMMDD` -- the same mechanism was AIF-028's date-numeric symptom). Fix
  (`cmd_replace.cpp`): integral values go through `std::to_string` (fixed "C"
  locale) and the fractional path imbues `std::locale::classic()`, matching the
  precedent already set in `rhs_eval.cpp` `scalar_to_string`. `cmd_calcwrite.cpp`
  was already type-aware and unaffected. AIF-028's date-numeric coercion is
  retired by this same fix; AIF-028's blank-date acceptance remains an M3 item.
- **M2 -- `B` double, `Y` currency, `T` datetime codecs. PROVEN (2026-07-19).**
  `B` = 8-byte IEEE-754 double (explicit little-endian; canonical decimal text,
  classic locale). `Y` = 8-byte int64 scaled 10^4 with an **exact** decimal parse
  (no float rounding -- round-trips to INT64_MAX). `T` = 8-byte datetime =
  4-byte Julian Day Number + 4-byte milliseconds, canonical text `YYYYMMDDHHMMSS`
  (also accepts `YYYYMMDD` = midnight); added the missing `T` write-validation
  case (`normalize_datetime_value` in `cmd_replace.cpp`). Proof:
  `src/tests/test_field_codec.cpp` (`dottalkpp_field_codec_test`, 1/1 pass) --
  boundary round-trips (INT32 min/max, near-INT64-max currency, 4dp truncation,
  invalid-input rejection for all four) **and** a known-value anchor: 1970-01-01
  encodes JDN `2440588` and 14:30:00 encodes `52,200,000` ms (VFP-consistent, not
  merely self-consistent). The test also caught + fixed an M1 strictness gap:
  `i32_encode` accepted trailing garbage (`"12x"`->12 via lenient `stoll`) -- now
  rejects when `stoll`'s consumed length != input length.
- **M3 -- `D` date-blank + numeric-literal coercion fix. PROVEN (2026-07-19).**
  The canonical stored date is **date8** (8-digit `YYYYMMDD`, per maintainer:
  "normally stored date value is date8 or an 8-digit char field from the .32
  days"). Fixes: (a) a blank/all-space value now **clears** the date instead of
  erroring -- the AIF-028 remainder (`normalize_date_value`); (b) validation now
  **canonicalizes what it stores** -- `validate_field_value_for_store` was
  computing the normalized form and *discarding* it, storing raw text truncated to
  the field width; it now writes the canonical form back into `stored_value`
  (`D`->date8/blank, `L`->`T`/`F`, `N`/`F`->validated, `T`->compact stamp). Proof, run
  live: `REPLACE DOB WITH 19560214` => `19560214`; `REPLACE DOB WITH "        "` =>
  blank; `REPLACE FLAG WITH TRUE` => `T`. Note: an **unquoted** slashed date
  (`02/14/1956`) is read by the expression evaluator as division (`2/14/1956`~=0)
  and never reaches the date normalizer -- expected, since date8 is the normal
  input form; quoted `"02/14/1956"` does canonicalize to `19560214`.
- **M4 -- worked custom field type end-to-end. PROVEN (2026-07-19).** Demo type
  **`X` = pronoun / form of address**: a depth-8 *stack* of pronoun-set codes
  (1 byte each) stored as fixed-width binary, canonical text `"she/her; they/them"`
  (each set shown "subject/object"; `ask` and `it` collapse to a single token).
  Codec in `field_codec.cpp` (`pronoun_encode`/`pronoun_decode`); REPLACE validates
  **through the codec itself** (`cmd_replace.cpp` case `'X'` round-trips encode->decode
  so the type's own `Codec` is the single source of truth). Proof, run live:
  `CREATE X64 PEOPLE (NAME C(12), PN X)` -> `REPLACE PN WITH "she/her; they/them"` ->
  `? PN` => `she/her; they/them`; `"THEY/THEM"` => `they/them` (case-normalized);
  `"ze/zir; ask"` round-trips; `"foo/bar"` => `REPLACE: unknown pronoun set 'foo/bar'.`;
  `STRUCT` shows `PN  X  8`. The `register_codec` unit test additionally installs a
  brand-new runtime type char (`~`) and round-trips it, proving registration -- not a
  hardcoded switch -- is the extension point.

  **Friction found -- feeds M4b.** Adding `X` required editing **five** hardcoded
  gates: the `kTypeIndex` catalog (`datatype_index.hpp`), *two* `supports_type_now`
  copies (`core/` + `xbase/dbf_create.cpp`), the `cmd_create` width switch, and the
  `cmd_replace` validation. Per maintainer directive ("a custom type must register
  its code in a validated data/field-type chain, so extensive coding isn't needed"),
  that friction is the target of **M4b**: make the field-type registry the single
  registration point and have the validation chain *consult* it, then delete the five
  `X` edits -- if `X` still works from one registration, the model is truly proven.

- **M4b -- single-registration model (registry-fed validation chain). PROVEN
  (2026-07-19).** The field-type registry now carries, per code, everything the
  CREATE/validation chain needs: `register_field_type(type, Codec, FieldTypeMeta{
  fixed_width, formats, display_name})` (`field_codec.hpp/.cpp`), queried by
  `field_type_registered / _fixed_width / _formats / _display_name`. The CREATE
  chain consults the registry for any code the static catalog doesn't own:
  `cmd_create` accepts a registered type + checks format eligibility, and takes its
  width from the registry; `cmd_replace`'s `default` arm validates+canonicalizes
  **any** registered custom type through its own codec (no per-type case). The five
  hardcoded `X` gates were then **deleted** -- `kTypeIndex` catalog, both
  `supports_type_now` copies, the `cmd_create` width switch, and the `cmd_replace`
  `case 'X'`. `X` now lives in **one file** (`field_codec.cpp`: codec + metadata).
  Proof, run live after the deletions: `CREATE X64 PEOPLE (NAME C(12), PN X)` ->
  `REPLACE PN WITH "she/her; they/them"` -> `? PN` => `she/her; they/them`;
  `"foo/bar"` => clean rejection; `STRUCT` => `PN X 8`. A new custom field type now
  needs exactly one `register_field_type` call and zero switch edits.
- **M5 -- VFP interop. READ DIRECTION PROVEN (2026-07-19).** `CREATE VFP` writes a
  genuine VFP file (version `0x30`, field descriptors, the 263-byte DBC backlink
  area -> header length 456 for a 5-field table). An **independent, spec-based**
  reader that reuses none of the engine's code -- `src/tests/vfp_field_interop.py`,
  decoding straight from the documented VFP byte layout -- read back every binary
  field the engine wrote, exactly: `I`=50000000, `B`=3.140625, `Y`=1234.5678,
  `T`=2000-01-01 12:00 (and a second row incl. `I`=INT32_MIN, `Y`=-99.9999,
  `T`=1970-01-01). Fixture: `dottalkpp/data/scripts/fieldtype/vfp_types_make.dts`.
  The datetime epoch matches VFP (`JDN(2000-01-01)`=2451545). **Defect the gate
  caught + fixed:** `cmd_replace`'s *fractional* K_Number formatting used the
  default 6-sig-fig ostream precision, silently truncating `3.140625`->`"3.14062"`
  and `1234.5678`->`"1234.57"` before the codec saw them -- corrupting the stored
  double/currency. Fixed with `std::to_chars(..., chars_format::fixed)` (shortest
  round-trip, exact, locale-independent). **REVERSE DIRECTION PROVEN
  (2026-07-19):** an externally-authored VFP file (`EXTVFP.dbf`, written entirely
  outside the engine with the spec header + 263-byte backlink) was opened with
  `USE` and read exactly -- `I`=424242, `B`=2.71875, `Y`=777.7777,
  `T`=2024-07-04 09:00. So the round-trip holds both ways: the engine writes VFP
  binary an independent reader decodes, and reads VFP binary an independent writer
  produced. Remaining (optional, non-code): capacity/website spec update before any
  public "VFP binary-compatible" claim.

## Non-goals / honesty

Classic C/N/F/D/L/M text behavior is unchanged (that path is fine). This lane makes
the *binary* types real and makes the type system extensible; it is dev-only until
built + proven, and VFP binary round-trip (M5) is the interop gate before any
"VFP binary-compatible" claim on the website.
