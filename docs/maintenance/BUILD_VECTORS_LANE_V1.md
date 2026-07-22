# BUILD_VECTORS Lane V1

**Status:** approved / design — not started.
**Parent project:** `project.x64base.runtime`.
**AIF:** AIF-044.
**Freshness:** 2026-07-21.

Centralize engine-capacity constants into a single **generated build-vector authority** driven
by CMake, ending the current configuration drift where the same limit is hard-coded in several
places and a declared CMake option does not actually control the compiled engine.

Build vectors are high-level engine-capacity decisions: selected at configuration, validated
together, compiled into every affected target, exposed to runtime reporting, and mirrored to
tooling as JSON.

---

## 1. Motivation — verified configuration drift

Ground-truthed against source on 2026-07-21 (this is *config drift*, not just stale docs):

| Claim | Verified location | Finding |
|---|---|---|
| `MAX_FIELDS` hard-coded | `include/xbase.hpp:28` | `constexpr int MAX_FIELDS = 256;` — comment: *"was 128; doubled — table-buffer kMaxFields already 256"* (admits the duplication) |
| `MAX_INDEX`, `MAX_AREA` | `include/xbase.hpp:29–30` | `MAX_INDEX = 5`, `MAX_AREA = 512` (comment "was 256; doubled") |
| Duplicate field cap | `include/cli/table_state.hpp:20–21` | `kMaxFields = 256`, `kWords = (kMaxFields+63)/64` sizes fixed bit arrays; **must** equal `xbase::MAX_FIELDS`, nothing enforces it |
| Table-buffer change cap | `include/cli/table_state.hpp:42` | `kMaxChanges = 10000` |
| x64 name defaults/ceilings | `include/xbase_64.hpp:144–147` | defaults `128`, ceilings `256` (`X64_TABLE_NAME_LENGTH`, `X64_FIELD_NAME_LENGTH`, `*_MAX`) |
| **CMake option is inert** | `CMakeLists.txt:92,193,197,350` vs `xbase.hpp:30` | `DOTTALK_MAX_AREA` (profile default 256 DEV / 128 PROD) is passed as a compile define, but `xbase.hpp`'s `MAX_AREA = 512` never consults it. **The build summary reports `DOTTALK_MAX_AREA : 256` while the compiled engine is 512.** The option does not control the engine. |
| Record ceilings (16 MiB / 64 KiB) | *not located in xbase.hpp during spot-check* | inventory-pass action: find the exact symbols before cataloging |

The inert `DOTTALK_MAX_AREA` is the sharpest evidence: a declared, reported option that the
compiled engine silently ignores.

---

## 2. Governing rule

> **Format geometry is fixed. Engine acceptance and creation policy are vectored.**

Format/compatibility constants stay source-owned and MUST NOT become options (changing them
produces incompatible files, not a differently-sized engine): `DBF_VERSION_64 = 0x64`, `X64M`
magic, packed x64 structure layouts + sizes, descriptor terminator `0x0D`, the classic 10-byte
visible field-name fallback, legacy memo-reference widths, metadata version numbers, flag-bit
assignments.

Vectored = the largest value this **compiled build** agrees to accept/create/navigate. Distinct
from the on-disk format's representable range.

---

## 3. Architecture — one generated authority

```text
config/
  build_vectors.cmake      # cache vars, maintained defaults, range+relationship validation, summary
  build_vectors.hpp.in     # typed C++ constants via configure_file(); no independent numeric defaults
build/<preset>/generated/dottalk/
  build_vectors.hpp        # THE compiled authority; never hand-edited
  build_vectors.json       # same values for packaging, diagnostics, website, AI Portal, tests
include/
  xbase.hpp                # includes generated header; keeps compat aliases
  xbase_64.hpp             # owns x64 format structures; derives x64 *policy* from generated values
```

CMake owns selectable build inputs; `xbase_64.hpp` owns x64 **format** structures/helpers (do NOT
make it the source of build values). The generated include dir must be added **`PUBLIC`** on the
`xbase` lib so `dottalkpp`, tests, and bindings inherit it; `configure_file()` runs before any
target compiles. The compiled `BuildVectors` struct is the runtime truth; the JSON is a
same-configure-step mirror (so it cannot disagree with the binary).

### Generated C++ surface (typed, namespaced — not scattered macros)

```cpp
namespace dottalk::build {
  inline constexpr std::size_t   max_areas  = /* configured */;
  inline constexpr std::size_t   max_fields = /* configured */;
  inline constexpr std::uint64_t max_rows   = /* configured */;
  inline constexpr std::size_t   legacy_max_index_slots = /* configured */;
  namespace x64 {
    inline constexpr std::uint64_t max_record_bytes      = /* configured */;
    inline constexpr std::uint64_t record_advisory_bytes = /* configured */;
    inline constexpr std::uint16_t table_name_default    = /* configured */;
    inline constexpr std::uint16_t table_name_max        = /* configured */;
    inline constexpr std::uint16_t field_name_default    = /* configured */;
    inline constexpr std::uint16_t field_name_max        = /* configured */;
  }
  namespace table_buffer { inline constexpr std::size_t max_changes = /* configured */; }
}
```

Compatibility aliases (temporary, avoid a big-bang rewrite):

```cpp
constexpr int MAX_FIELDS = static_cast<int>(dottalk::build::max_fields);
constexpr int MAX_AREA   = static_cast<int>(dottalk::build::max_areas);
constexpr int MAX_INDEX  = static_cast<int>(dottalk::build::legacy_max_index_slots);
// table_state.hpp:
constexpr std::size_t kMaxFields = dottalk::build::max_fields;
constexpr std::size_t kWords     = (kMaxFields + 63) / 64;
```

---

## 4. Initial vector catalog (immediate target)

Current values verified above; preserve them exactly in the first cut.

| CMake option | Preserve | Meaning |
|---|---:|---|
| `DOTTALK_MAX_AREAS` | `512` | Max simultaneously addressable work areas (**512, not the inert 256/128**) |
| `DOTTALK_MAX_FIELDS` | `256` | Max fields the compiled engine accepts |
| `DOTTALK_MAX_ROWS` | `9223372036854775807` | Max row count engine policy accepts (see §5) |
| `DOTTALK_LEGACY_MAX_INDEX_SLOTS` | `5` | Legacy per-area index-slot capacity |
| `DOTTALK_X64_MAX_RECORD_BYTES` | `16777216` | Hard x64 fixed-record ceiling (locate symbol) |
| `DOTTALK_X64_RECORD_ADVISORY_BYTES` | `65536` | Advisory move-to-memo point (locate symbol) |
| `DOTTALK_X64_TABLE_NAME_DEFAULT` | `128` | x64 metadata default |
| `DOTTALK_X64_TABLE_NAME_MAX` | `256` | Greatest table name accepted |
| `DOTTALK_X64_FIELD_NAME_DEFAULT` | `128` | x64 metadata default |
| `DOTTALK_X64_FIELD_NAME_MAX` | `256` | Greatest field name accepted |
| `DOTTALK_TABLE_BUFFER_MAX_CHANGES` | `10000` | Max buffered changes per area |

Deferred second inventory pass: relation depth/count, tuple projection/traversal, browser column,
expression nesting/stack, command/argument, memo page/block, LMDB map-size defaults, max keys/tags
per container, import/export batch sizes, and any fixed arrays derived from field/area/index counts.

---

## 5. `MAX_ROWS` — precise definition

The x64 format field is `uint64_t record_count` (fixed format fact — stays a full-range format
capability). The **build vector** means: the largest record count this compiled engine will open,
create, navigate, or mutate.

```text
effective row ceiling = min( format-representable max,
                             configured engine max,
                             platform/addressing constraints,
                             operation-specific constraints )
```

v32 is bounded by its physical format; v64 may carry a wider count; a constrained educational/
embedded build may reject very large tables; a rejection must report both the table's row count and
the compiled ceiling. **Keep the present signed-64-bit acceptance limit initially** so migration
neither widens nor narrows behavior. **CMake caveat:** `9223372036854775807` cannot be a CMake
integer — carry it as a string and emit a `std::uint64_t` literal in the generated header, guarded
by `static_assert`.

---

## 6. Validation — two levels

**CMake (rejects bad user input):** `MAX_AREAS>=1`, `MAX_FIELDS>=1`, `MAX_ROWS>=1`,
`FIELD_NAME_DEFAULT<=FIELD_NAME_MAX`, `TABLE_NAME_DEFAULT<=TABLE_NAME_MAX`, name maxima `<=` uint16
metadata capacity, `RECORD_ADVISORY_BYTES<=MAX_RECORD_BYTES`, and `MAX_FIELDS`/`MAX_AREAS`/
`MAX_INDEX_SLOTS` must fit their index/area/state representations.

**C++ (rejects an impossible generated contract):**

```cpp
static_assert(dottalk::build::max_fields > 0);
static_assert(dottalk::build::max_fields <= std::numeric_limits<std::uint32_t>::max());
```

---

## 7. Runtime availability + reporting

```cpp
struct BuildVectors {
    std::uint64_t max_rows; std::uint32_t max_fields; std::uint32_t max_areas;
    std::uint32_t legacy_max_index_slots;
    std::uint64_t x64_max_record_bytes; std::uint64_t x64_record_advisory_bytes;
    std::uint16_t x64_table_name_default; std::uint16_t x64_table_name_max;
    std::uint16_t x64_field_name_default; std::uint16_t x64_field_name_max;
    std::uint32_t table_buffer_max_changes;
};
const BuildVectors& build_vectors() noexcept;
```

Surface via `ABOUT BUILD` / `BUILD INFO` / `BUILD VECTORS` (fits the engine's "make state visible"
design). Bindings expose a read-only object; diagnostic logs include a short build-vector
fingerprint so two binaries with different capacities are distinguishable.

---

## 8. Migration sequence

1. **Vector inventory.** Classify every hard-coded limit: format-fixed / build vector / runtime
   setting / file-owned metadata / temporary guardrail. (Locate the 16 MiB + 64 KiB record symbols.)
2. **Add `config/build_vectors.cmake`** with current effective values — no behavior change.
3. **Generate `build_vectors.hpp`**; add its include dir `PUBLIC` to `xbase` and consumers.
4. **Replace duplicate field/area constants first** — `xbase.hpp`, `table_state.hpp`, field managers,
   browser builders, validators, area containers derive from the generated constants.
5. **Introduce explicit `MAX_ROWS` policy** — replace the direct `int64_t::max()` check with
   `dottalk::build::max_rows`.
6. **Move x64 policy limits** — structures stay in `xbase_64.hpp`; naming/record-size policy derive
   from generated values.
7. **Add configure-time + runtime reporting.**
8. **Vector matrix test** — default build, lower-limit canary, enlarged field/area build,
   invalid-configuration rejection tests.
9. **Regenerate docs from the manifest** — never hand-repeat numeric values in prose.

Immediate target: the generated authority + `MAX_FIELDS`, `MAX_AREA`, `MAX_ROWS`, and the x64 name
vectors (they expose the drift most clearly and touch several subsystems at once).

---

## 9. Migration-safety gates (non-negotiable)

1. **GATE #1 — preserve 512.** The first cut MUST reproduce current *compiled* behavior
   (`MAX_AREAS=512`). Wiring `MAX_AREA` to the existing inert profile value (256/128) would silently
   *narrow* capacity 512→256. Prove `ABOUT`/`BUILD VECTORS` still reports 512 before anything ships.
2. **Case-ghost.** New `config/*.cmake` + generated paths must use correct casing; the lowercase
   `src/CMakelists.txt` ghost is a live hazard on this exact kind of change and will break Linux CI.
3. **Promotion-sensitive.** This alters the compiled engine — stays on the dev branch behind the
   gated promotion, with the "preserve 512" proof shown green before it reaches `C:\x64base`.

---

## 10. Milestones

- **M0** — vector inventory + classification (incl. locating record-ceiling symbols).
- **M1** — `config/build_vectors.cmake` + `build_vectors.hpp.in` + generated header/json authority,
  preserving current values (GATE #1).
- **M2** — replace duplicate field/area constants; `static_assert` at fixed-array consumers.
- **M3** — explicit `MAX_ROWS` policy; x64 name/record policy derives from generated values.
- **M4** — runtime `BuildVectors` + `BUILD VECTORS` reporting + fingerprint.
- **M5** — vector matrix test (default / canary / enlarged / invalid-rejection).
- **M6** — regenerate docs/website/portal capacity facts from the JSON manifest.

Origin: external AI design proposal (2026-07-21), ground-truthed and endorsed; preserved here as the
lane's design authority.
