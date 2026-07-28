---
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260719-BF2
  recorded_at_utc: 2026-07-26T05:25:45Z
  agent:
    provider: not_exposed
    product: not_exposed
    model: not_exposed
    access_mode: human_operated_tool
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:/code/ccode
  git:
    branch: development
    baseline_commit: 156980512
  authorization:
    requested_by: maintainer
    scope: >
      Envelope reconstructed 2026-07-28 during AI-portal audit backfill
      (AIPR-20260728-002). AI-authored, human-committed (introducing commit
      156980512, 2026-07-26); original session/agent identity was not recorded and is
      marked not_exposed; access_mode human_operated_tool per
      AI_REPORT_AUDIT_CONTRACT_V1.md.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_FIELDTYPE_CODEC_2026-07-19.md
    kind: session_closeout
---

# Session Closeout — FIELDTYPE codec architecture, M1–M5 (2026-07-19)

```yaml
ai_report_audit:
  schema: ai-report-audit-v1
  report_id: AIPR-20260719-007
  recorded_at_utc: 2026-07-20T06:24:03Z
  agent:
    provider: not_exposed
    product: Cowork (Claude)
    model: not_exposed
    access_mode: local_write
  session:
    id: not_exposed
    chat_reference: not_exposed
  project:
    id: project.x64base.runtime
    root: D:\code\ccode
  git:
    branch: homegrown-cnx-20251112-branch
    baseline_commit: 8ee746dee21c14b02eaf0398034b15634132a33f
  authorization:
    requested_by: maintainer
    scope: >
      Investigate field types from the trinity headers and build the field-type
      codec architecture so the binary VFP types are real (not a fixed-width-text
      facade), with the built-in-type handling as the model for custom field types.
      Milestones M1 (codec seam + I int32), M2 (B/Y/T binary codecs + boundary
      test), M3 (date blank/numeric coercion), M4 (worked custom type), M4b
      (single-registration model), M5 (VFP binary interop, both directions).
      Original changes only in D:\code\ccode on the existing branch; no branch
      created or switched; not applied to C:\x64base or GitHub.
  report:
    path: docs/maintenance/SESSION_CLOSEOUT_FIELDTYPE_CODEC_2026-07-19.md
    kind: session_closeout
```

Owning lifecycle: DotTalk++ SDLC.
SDLC lane: implementation + proof.
Truth state: source-defined + runtime-proven (M1–M5).
Proof state: unit test (green) + live shakedowns + independent third-party VFP reader/writer.

## One-line summary

Turned the field-type layer from "every field is fixed-width text" into a real
codec registry: `I`/`B`/`Y`/`T` now store true VFP binary, a worked custom type
(`X` pronoun) plugs in through a single registration with zero switch edits, and
VFP interop is proven both directions by an independent spec-based reader/writer —
all dev-only and uncommitted.

## Background — what the investigation found

From the trinity headers (`xbase.hpp` neutral `FieldDef`, `xbase_vfp.hpp` VFP
descriptor, `xbase_64.hpp` x64 metadata) down to storage, the engine stored
**every field as fixed-width text** (`record_view.cpp` load/store). The four VFP
"binary" types were a facade: `I` was a 4-byte field holding 4 ASCII chars (max
9999) — the confirmed root of the `SID I` truncation (AIF-017) — and `B`/`Y`/`T`
were ASCII, not IEEE-754 / int64-scaled currency / julian+time. Design directive:
make the binary types real, and make the way we handle field types **the model for
custom field types**.

## Changed (development, D:\code\ccode)

| Area | Files | Note |
| --- | --- | --- |
| Codec registry (NEW) | `include/xbase/field_codec.hpp`, `src/xbase/field_codec.cpp` | `Codec{decode,encode,name}` + `codec_for`/`register_codec`; text default (byte-exact to legacy) + `I` int32; M2 `B`/`Y`/`T`; M4 `X` pronoun; M4b `FieldTypeMeta` + `register_field_type` + `field_type_registered/_fixed_width/_formats/_display_name` + format bits |
| Storage seams | `src/xbase/record_view.cpp` **and** `src/cli/record_view.cpp` | load/store dispatch through `codec_for(f.type)` (the `.obj` in the exe shadows the lib copy — both edited) |
| REPLACE pipeline | `src/cli/cmd_replace.cpp` | locale-safe integer format (`std::to_string`); `std::to_chars` fixed for fractional (M5 precision fix); blank-date clear; **canonicalize-on-validate** (D/L/N/F/T write the normalized form back); `T` validation; generic `default` arm validates any registered custom type through its codec; `#include <locale>`, `field_codec.hpp` |
| CREATE chain (M4b) | `src/cli/cmd_create.cpp` | registry fallback: accepts a registered type + checks format eligibility + takes width from the registry for codes the static catalog does not own; `field_codec.hpp` |
| Tests (NEW) | `src/tests/test_field_codec.cpp`, `src/tests/CMakeLists.txt` | `dottalkpp_field_codec_test`: I/B/Y/T/X boundary round-trips, JDN anchor, `register_codec` runtime custom type |
| VFP interop (NEW) | `src/tests/vfp_field_interop.py`, `dottalkpp/data/scripts/fieldtype/vfp_types_make.dts` | independent spec-based VFP reader (shares no engine code) + M5 fixture |
| Docs | `docs/maintenance/FIELD_TYPE_CODEC_LANE_V1.md`, `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-030 M1–M5, AIF-028 resolved, AIF-031 new) | document-as-you-go per AIF-024 |

Touched-then-reverted (net no change): `include/datatype_index.hpp`,
`src/xbase/dbf_create.cpp`, `src/core/dbf_create.cpp` — `X` was added to the static
catalog + `supports_type_now` for M4, then **removed** in M4b once the registry
became the single source (the five-gate deletion). Left byte-identical to baseline.

## Milestones — all proven (dev)

- **M1** — codec seam + text default + `I` int32. Live: `REPLACE SID WITH 50000000`
  → `? SID` = `50000000` (was `5000`). AIF-017 retired.
- **M2** — `B` (IEEE-754), `Y` (int64/10⁴ currency, exact decimal parse), `T`
  (JDN + ms datetime) + `T` write validation. `dottalkpp_field_codec_test` 1/1,
  incl. known-JDN anchor (1970-01-01 = 2440588) and a caught `i32_encode`
  strictness gap (`"12x"`).
- **M3** — blank date clears; validation canonicalizes the stored value (was
  computing and discarding it). AIF-028 date-numeric retired; date8 is the norm.
- **M4** — worked custom type `X` = pronoun (depth-8 stack of set-codes ↔
  "she/her; they/them"). CREATE→REPLACE→read live; `register_codec('~')` runtime
  test proves registration is the extension point.
- **M4b** — single-registration model. Registry carries codec + fixed width +
  format eligibility + display name; CREATE/validation chain consults it; the
  **five hardcoded `X` gates were deleted**; `X` now lives in one file
  (`field_codec.cpp`). Re-proven live after the deletions.
- **M5** — VFP interop, **both directions**. (a) Engine `CREATE VFP` writes a
  genuine VFP file (v`0x30` + 263-byte DBC backlink → header len 456); an
  independent spec-based reader read every binary field exactly. (b) Engine `USE`d
  an externally-authored VFP file and read every field exactly. Datetime epoch
  matches VFP (`JDN(2000-01-01)` = 2451545).

## Defects found + fixed (all via the proof work)

- **AIF-017** — `I` 4-byte-text truncation → real int32 codec (M1).
- **AIF-028** — x64 date REPLACE rejected numeric/blank literals: numeric was the
  locale bug below; blank now clears (M3).
- **AIF-031 (new)** — `cmd_replace` numeric formatting: (i) integral values went
  through a locale-grouping `ostringstream` (`50000000`→`"50,000,000"`), failing
  int32/YYYYMMDD parsing — fixed to `std::to_string`; (ii) fractional values used
  the default 6-sig-fig ostream precision, truncating `3.140625`→`"3.14062"` and
  `1234.5678`→`"1234.57"` and corrupting the stored double/currency — fixed to
  `std::to_chars(..., chars_format::fixed)`. The precision half was caught only
  because the independent VFP reader disagreed by four decimals.
- `i32_encode` accepted trailing garbage (`"12x"`→12); now rejects.

## Verified (proof performed this session)

- **`dottalkpp_field_codec_test` green (1/1)** after each relevant build — I/B/Y/T
  boundary round-trips (INT32 min/max, near-INT64-max currency, 4dp truncation,
  invalid-input rejection), `X` pronoun stack, `register_codec` runtime type,
  known-JDN/ms anchors.
- **Live shakedowns (maintainer, MSVC Release):** `REPLACE SID WITH 50000000` round
  trips; `X` CREATE→REPLACE→read (`she/her; they/them`, case-normalization,
  `foo/bar` rejection, `STRUCT` X 8); M4b re-proof with the five gates removed.
- **M5 independent interop:** `src/tests/vfp_field_interop.py` (no engine code)
  decoded the engine-written `VFPTYPES.dbf` exactly (`I`=50000000, `B`=3.140625,
  `Y`=1234.5678, `T`=2000-01-01 12:00, + INT32_MIN / -99.9999 / 1970 row); the
  engine `USE`d an externally-written `EXTVFP.dbf` and read it exactly
  (`I`=424242, `B`=2.71875, `Y`=777.7777, `T`=2024-07-04 09:00).
- Not proof: no real VFP.exe was used (unavailable); interop is proven against the
  documented VFP on-disk spec via an independent reader/writer, which is the
  practical gate. CALCWRITE was not wired for custom (`X`) types (REPLACE is the
  proven write path).

## Published

**Not promoted.** All changes are original edits on the existing
`homegrown-cnx-20251112-branch` in `D:\code\ccode`; no commit, no `C:\x64base`
staging, no GitHub push, no website change. The M1–M5 vertical is a clean, proven
promotion candidate — the maintainer's deliberate step.

## Still open — for the next session

- **AIF-031 numeric-formatting sweep** (intake task #100): audit other CLI/engine
  numeric formatters for the same two hazards (locale grouping + fixed-precision
  truncation); prefer `std::to_string` / `to_chars` / `imbue(classic())`.
- **Website "VFP binary-compatible" claim**: only after the capacity/spec page is
  updated to reflect the now-real binary types + the interop proof.
- **Custom-type reach**: CALCWRITE support for registered custom types; the
  pronoun function/command layer (`PSUBJ`/`POBJ`/`PPOSS` grammatical accessors,
  `PUSH`/`POP` stack ops) — deliberately left above the codec so storage stays pure.
- **profile_smoke `data\data` path doubling** (task #99, pre-existing, separate).
- **Promotion** of the M1–M5 vertical (maintainer's call).

## Provenance pointers

- Lane: `docs/maintenance/FIELD_TYPE_CODEC_LANE_V1.md`
- Intake: `docs/ai-friendly/AI_INTERACTION_INTAKE_QUEUE_V1.md` (AIF-030, AIF-028, AIF-031)
- Predecessor: `docs/maintenance/SESSION_CLOSEOUT_RECNO64_M1_M4_2026-07-19.md` (AIPR-20260719-006)
- Proof artifacts: `src/tests/test_field_codec.cpp`, `src/tests/vfp_field_interop.py`, `dottalkpp/data/scripts/fieldtype/vfp_types_make.dts`
```
