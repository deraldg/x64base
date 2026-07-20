#pragma once
// Field-type codec registry (FIELDTYPE lane).
//
// A field-type codec converts between a field's fixed-width on-disk bytes and the
// engine's text value. Every field type — built-in (C/N/F/D/L/M and the binary
// VFP types I/B/Y/T) or custom — is one `Codec`. The registry (`codec_for` /
// `register_codec`) is the single extensibility seam: registering a custom type is
// exactly how a built-in type is defined, so custom field types are first-class.
//
// The two storage seams in `record_view.cpp` (loadFieldsFromBuffer /
// storeFieldsToBuffer) dispatch through `codec_for(field.type)`. The x64-memo path
// stays special (object-id/sidecar lifecycle); everything else is a Codec.

#include <cstddef>
#include <string>

namespace xbase {

struct FieldDef;   // defined in xbase.hpp

namespace fieldcodec {

struct Codec {
    // Decode `len` on-disk bytes at `bytes` into the engine's text value.
    std::string (*decode)(const char* bytes, std::size_t len, const FieldDef& f);

    // Encode `text` into exactly `f.length` bytes at `out`. The caller has already
    // filled the field's byte region with spaces; a text codec may leave that pad,
    // a binary codec overwrites all bytes it owns. Returns false and sets *err on an
    // invalid value (the write path validates first, so this is a backstop).
    bool (*encode)(const std::string& text, const FieldDef& f, char* out,
                   std::string* err);

    const char* name;   // "text", "int32", "double", "currency", "datetime", ...
};

// Codec for a type char: the registered/built-in codec, or the fixed-width text
// codec when none is registered (preserves classic C/N/F/D/L/M behavior).
const Codec& codec_for(char type) noexcept;

// Register or override the codec for a type char (custom field types).
void register_codec(char type, Codec codec);

// ---------------------------------------------------------------------------
// Single-registration field-type model (FIELDTYPE M4b).
//
// A custom field type registers its code ONCE here, with everything the CREATE
// and validation chain needs, so no hand-edited per-type switch is required:
//   - its Codec (bytes <-> text),
//   - a fixed on-disk width (0 = the type takes a CREATE length param),
//   - which engine formats may use it,
//   - a display name for STRUCT/FIELDS.
// The CREATE-side gates consult this registry for any type code the static
// datatype catalog does not own.
// ---------------------------------------------------------------------------
enum FieldFormatBits : unsigned short {
    FT_FMT_MSDOS   = 1u << 0,
    FT_FMT_FOX26   = 1u << 1,
    FT_FMT_VFP     = 1u << 2,
    FT_FMT_X64     = 1u << 3,
    FT_FMT_SQL     = 1u << 4,
    FT_FMT_TUPTALK = 1u << 5,
};

struct FieldTypeMeta {
    unsigned int   fixed_width  = 0;   // 0 => requires a CREATE length param
    unsigned short formats      = 0;   // FieldFormatBits mask of eligible formats
    const char*    display_name = "";
    bool           registered   = false;
};

// Register a field type in one call: codec + metadata (the M4b entry point).
void register_field_type(char type, Codec codec, FieldTypeMeta meta);

// Registry queries used by the CREATE / validation chain.
bool           field_type_registered(char type) noexcept;
unsigned int   field_type_fixed_width(char type) noexcept;
unsigned short field_type_formats(char type) noexcept;
const char*    field_type_display_name(char type) noexcept;

}  // namespace fieldcodec
}  // namespace xbase
