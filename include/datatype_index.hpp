// datatype_index.hpp
// Central type catalog / mapping index for DotTalk++
//
// Purpose:
//   - Provide one authoritative place for DBF/Fox/VFP/X64/SQL type knowledge
//   - Keep storage type, semantic type, and external mapping separate
//   - Allow gradual integration into CREATE / USE / STRUCT / importsql / tuptalk
//
// Notes:
//   - Header-only by design
//   - Declarative first; runtime policy can be layered on later
//   - Conservative defaults: unsupported mappings are explicit
//   - Classic xBase is the common base
//   - VFP types are an extension slice
//   - X64 is the modern superset runtime (classic + selected VFP + X64/SQL extensions)

#pragma once

#include <array>
#include <cctype>
#include <cstdint>
#include <string_view>

namespace dottalk::types {

// -----------------------------------------------------------------------------
// Engine/file families
// -----------------------------------------------------------------------------
enum class EngineFormat : std::uint8_t {
    Unknown = 0,
    MSDOS_DBASE,
    FOX26,
    VFP,
    X64,
    SQL,
    TUPTALK
};

// -----------------------------------------------------------------------------
// Physical storage family
// -----------------------------------------------------------------------------
enum class StorageFamily : std::uint8_t {
    Unknown = 0,

    // Classic / DBF-family
    FixedText,
    FixedNumericAscii,
    DateYYYYMMDD,
    LogicalAscii,
    MemoPointer,

    // VFP / extended binary
    Integer32Binary,
    Currency64Binary,
    DateTimeBinary,
    DoubleBinary,
    VarChar,
    VarBinary,
    Blob,
    General,
    Picture,

    // X64 / SQL-native extension families
    Integer64Binary,
    Integer16Binary,
    Integer8Binary,
    Real32Binary,
    FixedWideText,
    VarWideText,
    Clob,
    TimeOnly,
    TimestampBinary,
    UuidBinary,
    JsonText,
    XmlText
};

// -----------------------------------------------------------------------------
// Logical semantic type
// -----------------------------------------------------------------------------
enum class SemanticType : std::uint8_t {
    Unknown = 0,

    // Classic/core
    Character,
    Numeric,
    Integer,
    Decimal,
    Date,
    DateTime,
    Logical,
    Memo,
    Currency,
    DoubleFloat,
    Binary,
    Blob,
    General,
    Picture,
    AutoIncrement,

    // X64 / SQL-native extension semantics
    BigInt,
    SmallInt,
    TinyInt,
    RealFloat,
    WideCharacter,
    Clob,
    Time,
    Timestamp,
    Uuid,
    Json,
    Xml
};

// -----------------------------------------------------------------------------
// Support state
// -----------------------------------------------------------------------------
enum class SupportLevel : std::uint8_t {
    None = 0,
    Planned,
    ParseOnly,
    ReadWrite
};

// -----------------------------------------------------------------------------
// Per-type capability flags
// -----------------------------------------------------------------------------
enum TypeFlags : std::uint32_t {
    TF_NONE            = 0,
    TF_HAS_WIDTH       = 1u << 0,
    TF_HAS_DECIMALS    = 1u << 1,
    TF_IS_BINARY       = 1u << 2,
    TF_IS_MEMO         = 1u << 3,
    TF_IS_VARIABLE     = 1u << 4,
    TF_IS_NUMERIC      = 1u << 5,
    TF_IS_TEXTUAL      = 1u << 6,
    TF_IS_TEMPORAL     = 1u << 7,
    TF_CAN_INDEX       = 1u << 8,
    TF_SQL_FRIENDLY    = 1u << 9,
    TF_TUPLE_FRIENDLY  = 1u << 10,
    TF_VFP_ONLY        = 1u << 11,
    TF_CLASSIC_ONLY    = 1u << 12,
    TF_X64_ONLY        = 1u << 13,
    TF_SQL_ONLY        = 1u << 14,
    TF_UNICODE_TEXT    = 1u << 15,
    TF_SEMISTRUCTURED  = 1u << 16
};

constexpr inline bool has_flag(std::uint32_t value, std::uint32_t flag) noexcept {
    return (value & flag) != 0;
}

// -----------------------------------------------------------------------------
// Canonical type record
// -----------------------------------------------------------------------------
struct TypeInfo {
    char            dbf_code;         // physical DBF/Fox/VFP type code; 0 if N/A
    std::string_view short_name;      // "C", "N", "DATE", "BIGINT", ...
    std::string_view display_name;    // "Character", "Numeric", ...
    StorageFamily   storage_family;
    SemanticType    semantic_type;
    std::uint32_t   flags;

    SupportLevel    msdos_support;
    SupportLevel    fox26_support;
    SupportLevel    vfp_support;
    SupportLevel    x64_support;
    SupportLevel    sql_support;
    SupportLevel    tuptalk_support;

    std::string_view default_sql_type;
    std::string_view notes;
};

// -----------------------------------------------------------------------------
// Canonical index
//
// Policy:
//   - Classic/core types are broadly supported and inherited by X64
//   - VFP types remain VFP-specific in origin, but selected ones may participate
//     in X64 as planned/readwrite as maturity grows
//   - SQL-only modern types are cataloged honestly with dbf_code == 0
//   - SQL-only modern types are treated as X64 extensions, not legacy DBF types
// -----------------------------------------------------------------------------
constexpr inline std::array<TypeInfo, 27> kTypeIndex{{
    // -------------------------------------------------------------------------
    // Classic / common core
    // -------------------------------------------------------------------------
    {
        'C', "C", "Character",
        StorageFamily::FixedText, SemanticType::Character,
        TF_HAS_WIDTH | TF_IS_TEXTUAL | TF_CAN_INDEX | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY,
        SupportLevel::ReadWrite,  // msdos
        SupportLevel::ReadWrite,  // fox26
        SupportLevel::ReadWrite,  // vfp
        SupportLevel::ReadWrite,  // x64
        SupportLevel::ReadWrite,  // sql
        SupportLevel::ReadWrite,  // tuptalk
        "VARCHAR",
        "Classic fixed-length character field."
    },
    {
        'N', "N", "Numeric",
        StorageFamily::FixedNumericAscii, SemanticType::Numeric,
        TF_HAS_WIDTH | TF_HAS_DECIMALS | TF_IS_NUMERIC | TF_CAN_INDEX | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        "DECIMAL",
        "ASCII numeric storage; decimals determine integer vs decimal usage."
    },
    {
        'D', "D", "Date",
        StorageFamily::DateYYYYMMDD, SemanticType::Date,
        TF_IS_TEMPORAL | TF_CAN_INDEX | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        "DATE",
        "Stored as YYYYMMDD in DBF family formats."
    },
    {
        'L', "L", "Logical",
        StorageFamily::LogicalAscii, SemanticType::Logical,
        TF_CAN_INDEX | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        "BOOLEAN",
        "Logical true/false/? style field."
    },
    {
        'M', "M", "Memo",
        StorageFamily::MemoPointer, SemanticType::Memo,
        TF_IS_MEMO | TF_IS_TEXTUAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        SupportLevel::ReadWrite,
        "TEXT",
        "Memo pointer into DBT/FPT/DTX-style sidecar."
    },
    {
        'F', "F", "Float",
        StorageFamily::FixedNumericAscii, SemanticType::DoubleFloat,
        TF_HAS_WIDTH | TF_HAS_DECIMALS | TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "FLOAT",
        "Rare in classic xBase usage; treat carefully."
    },

    // -------------------------------------------------------------------------
    // VFP-origin extension slice
    // -------------------------------------------------------------------------
    {
        'I', "I", "Integer",
        StorageFamily::Integer32Binary, SemanticType::Integer,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "INTEGER",
        "Visual FoxPro 32-bit integer."
    },
    {
        'Y', "Y", "Currency",
        StorageFamily::Currency64Binary, SemanticType::Currency,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "DECIMAL(19,4)",
        "Visual FoxPro scaled 64-bit currency."
    },
    {
        'T', "T", "DateTime",
        StorageFamily::DateTimeBinary, SemanticType::DateTime,
        TF_IS_TEMPORAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "DATETIME",
        "Visual FoxPro datetime."
    },
    {
        'B', "B", "Double",
        StorageFamily::DoubleBinary, SemanticType::DoubleFloat,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "DOUBLE",
        "Visual FoxPro binary double."
    },
    {
        'V', "V", "VarChar",
        StorageFamily::VarChar, SemanticType::Character,
        TF_HAS_WIDTH | TF_IS_TEXTUAL | TF_IS_VARIABLE | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "VARCHAR",
        "Visual FoxPro varchar."
    },
    {
        'Q', "Q", "VarBinary",
        StorageFamily::VarBinary, SemanticType::Binary,
        TF_HAS_WIDTH | TF_IS_BINARY | TF_IS_VARIABLE | TF_SQL_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "VARBINARY",
        "Visual FoxPro varbinary."
    },
    {
        'W', "W", "Blob",
        StorageFamily::Blob, SemanticType::Blob,
        TF_IS_BINARY | TF_IS_MEMO | TF_SQL_FRIENDLY | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "BLOB",
        "Visual FoxPro blob/generalized binary memo-style storage."
    },
    {
        'G', "G", "General",
        StorageFamily::General, SemanticType::General,
        TF_IS_MEMO | TF_VFP_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::Planned,
        SupportLevel::ParseOnly,
        SupportLevel::Planned,
        "BLOB",
        "Visual FoxPro general field; often OLE/object-like payload."
    },

    // -------------------------------------------------------------------------
    // SQL/X64-only extension slice
    // -------------------------------------------------------------------------
    {
        0, "BIGINT", "BigInt",
        StorageFamily::Integer64Binary, SemanticType::BigInt,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "BIGINT",
        "SQL 64-bit integer; x64-native extension."
    },
    {
        0, "SMALLINT", "SmallInt",
        StorageFamily::Integer16Binary, SemanticType::SmallInt,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "SMALLINT",
        "SQL 16-bit integer; x64-native extension."
    },
    {
        0, "TINYINT", "TinyInt",
        StorageFamily::Integer8Binary, SemanticType::TinyInt,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "TINYINT",
        "SQL 8-bit integer; x64-native extension."
    },
    {
        0, "REAL", "Real",
        StorageFamily::Real32Binary, SemanticType::RealFloat,
        TF_IS_NUMERIC | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "REAL",
        "SQL single-precision floating point; x64-native extension."
    },
    {
        0, "CHAR", "Char",
        StorageFamily::FixedText, SemanticType::Character,
        TF_HAS_WIDTH | TF_IS_TEXTUAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "CHAR",
        "SQL fixed-width text; distinct from legacy DBF C semantics."
    },
    {
        0, "NCHAR", "NChar",
        StorageFamily::FixedWideText, SemanticType::WideCharacter,
        TF_HAS_WIDTH | TF_IS_TEXTUAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY |
            TF_X64_ONLY | TF_SQL_ONLY | TF_UNICODE_TEXT,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "NCHAR",
        "SQL fixed-width Unicode text; x64-native extension."
    },
    {
        0, "NVARCHAR", "NVarChar",
        StorageFamily::VarWideText, SemanticType::WideCharacter,
        TF_HAS_WIDTH | TF_IS_TEXTUAL | TF_IS_VARIABLE | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY |
            TF_X64_ONLY | TF_SQL_ONLY | TF_UNICODE_TEXT,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "NVARCHAR",
        "SQL variable-width Unicode text; x64-native extension."
    },
    {
        0, "CLOB", "Clob",
        StorageFamily::Clob, SemanticType::Clob,
        TF_IS_TEXTUAL | TF_IS_MEMO | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY |
            TF_X64_ONLY | TF_SQL_ONLY | TF_UNICODE_TEXT,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "CLOB",
        "SQL large character object; x64-native extension."
    },
    {
        0, "TIME", "Time",
        StorageFamily::TimeOnly, SemanticType::Time,
        TF_IS_TEMPORAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "TIME",
        "SQL time-of-day only; x64-native extension."
    },
    {
        0, "TIMESTAMP", "Timestamp",
        StorageFamily::TimestampBinary, SemanticType::Timestamp,
        TF_IS_TEMPORAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "TIMESTAMP",
        "SQL timestamp; distinct from legacy/VFP DATETIME naming."
    },
    {
        0, "UUID", "Uuid",
        StorageFamily::UuidBinary, SemanticType::Uuid,
        TF_IS_BINARY | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY | TF_X64_ONLY | TF_SQL_ONLY,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "UUID",
        "SQL UUID/GUID; x64-native extension."
    },
    {
        0, "JSON", "Json",
        StorageFamily::JsonText, SemanticType::Json,
        TF_IS_TEXTUAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY |
            TF_X64_ONLY | TF_SQL_ONLY | TF_SEMISTRUCTURED,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "JSON",
        "SQL/modern semistructured JSON payload; x64-native extension."
    },
    {
        0, "XML", "Xml",
        StorageFamily::XmlText, SemanticType::Xml,
        TF_IS_TEXTUAL | TF_SQL_FRIENDLY | TF_TUPLE_FRIENDLY |
            TF_X64_ONLY | TF_SQL_ONLY | TF_SEMISTRUCTURED,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::None,
        SupportLevel::Planned,
        SupportLevel::ReadWrite,
        SupportLevel::Planned,
        "XML",
        "SQL/modern XML payload; x64-native extension."
    }
}};

// -----------------------------------------------------------------------------
// Lookup helpers
// -----------------------------------------------------------------------------
constexpr inline char up_char(char c) noexcept {
    return (c >= 'a' && c <= 'z') ? static_cast<char>(c - 'a' + 'A') : c;
}

constexpr inline const TypeInfo* find_by_code(char dbf_code) noexcept {
    const char key = up_char(dbf_code);
    for (const auto& t : kTypeIndex) {
        if (t.dbf_code != 0 && t.dbf_code == key) return &t;
    }
    return nullptr;
}

constexpr inline const TypeInfo* find_by_semantic(SemanticType st) noexcept {
    for (const auto& t : kTypeIndex) {
        if (t.semantic_type == st) return &t;
    }
    return nullptr;
}

inline const TypeInfo* find_by_sql_name(std::string_view sql_name) noexcept {
    auto upper_eq = [](std::string_view a, std::string_view b) -> bool {
        if (a.size() != b.size()) return false;
        for (std::size_t i = 0; i < a.size(); ++i) {
            const unsigned char ca = static_cast<unsigned char>(a[i]);
            const unsigned char cb = static_cast<unsigned char>(b[i]);
            if (std::toupper(ca) != std::toupper(cb)) return false;
        }
        return true;
    };

    for (const auto& t : kTypeIndex) {
        if (upper_eq(t.default_sql_type, sql_name) || upper_eq(t.short_name, sql_name)) {
            return &t;
        }
    }
    return nullptr;
}

// -----------------------------------------------------------------------------
// Support matrix helpers
// -----------------------------------------------------------------------------
constexpr inline SupportLevel support_for(const TypeInfo& t, EngineFormat fmt) noexcept {
    switch (fmt) {
        case EngineFormat::MSDOS_DBASE: return t.msdos_support;
        case EngineFormat::FOX26:       return t.fox26_support;
        case EngineFormat::VFP:         return t.vfp_support;
        case EngineFormat::X64:         return t.x64_support;
        case EngineFormat::SQL:         return t.sql_support;
        case EngineFormat::TUPTALK:     return t.tuptalk_support;
        default:                        return SupportLevel::None;
    }
}

constexpr inline bool is_supported(const TypeInfo& t, EngineFormat fmt) noexcept {
    return support_for(t, fmt) != SupportLevel::None;
}

constexpr inline bool is_readwrite(const TypeInfo& t, EngineFormat fmt) noexcept {
    return support_for(t, fmt) == SupportLevel::ReadWrite;
}

// -----------------------------------------------------------------------------
// Derived semantic helpers
// -----------------------------------------------------------------------------
constexpr inline bool is_numeric_semantic(SemanticType st) noexcept {
    return st == SemanticType::Numeric ||
           st == SemanticType::Integer ||
           st == SemanticType::Decimal ||
           st == SemanticType::Currency ||
           st == SemanticType::DoubleFloat ||
           st == SemanticType::AutoIncrement ||
           st == SemanticType::BigInt ||
           st == SemanticType::SmallInt ||
           st == SemanticType::TinyInt ||
           st == SemanticType::RealFloat;
}

constexpr inline bool is_text_semantic(SemanticType st) noexcept {
    return st == SemanticType::Character ||
           st == SemanticType::Memo ||
           st == SemanticType::WideCharacter ||
           st == SemanticType::Clob ||
           st == SemanticType::Json ||
           st == SemanticType::Xml;
}

constexpr inline bool is_temporal_semantic(SemanticType st) noexcept {
    return st == SemanticType::Date ||
           st == SemanticType::DateTime ||
           st == SemanticType::Time ||
           st == SemanticType::Timestamp;
}

constexpr inline SemanticType derive_semantic_type(char dbf_code,
                                                   std::uint8_t width,
                                                   std::uint8_t decimals) noexcept
{
    (void)width;

    const TypeInfo* t = find_by_code(dbf_code);
    if (!t) return SemanticType::Unknown;

    if (t->dbf_code == 'N') {
        if (decimals == 0) return SemanticType::Integer;
        return SemanticType::Decimal;
    }

    return t->semantic_type;
}

// -----------------------------------------------------------------------------
// SQL mapping helper
// Conservative, string-view only. Precise formatting can be layered later.
// -----------------------------------------------------------------------------
constexpr inline std::string_view sql_type_for(char dbf_code,
                                               std::uint8_t width,
                                               std::uint8_t decimals) noexcept
{
    (void)width;

    const TypeInfo* t = find_by_code(dbf_code);
    if (!t) return "UNKNOWN";

    if (up_char(dbf_code) == 'N') {
        return (decimals == 0) ? "INTEGER" : "DECIMAL";
    }

    return t->default_sql_type;
}

// -----------------------------------------------------------------------------
// CREATE validation helper
// Useful for CREATE / schema import / conversion planning
//
// Note:
//   This remains DBF-code driven.
//   SQL-only types (dbf_code == 0) should be validated through a separate
//   SQL-name path, not through legacy DBF field-code validation.
// -----------------------------------------------------------------------------
struct ValidationResult {
    bool            ok;
    const TypeInfo* type;
    const char*     reason;
};

constexpr inline ValidationResult validate_type_for_format(char dbf_code,
                                                           EngineFormat fmt) noexcept
{
    const TypeInfo* t = find_by_code(dbf_code);
    if (!t) {
        return { false, nullptr, "Unknown field type code." };
    }

    if (!is_supported(*t, fmt)) {
        return { false, t, "Field type is not supported for this engine format." };
    }

    return { true, t, nullptr };
}

// Optional helper for SQL-name-driven validation
inline ValidationResult validate_sql_type_for_format(std::string_view sql_name,
                                                     EngineFormat fmt) noexcept
{
    const TypeInfo* t = find_by_sql_name(sql_name);
    if (!t) {
        return { false, nullptr, "Unknown SQL type name." };
    }

    if (!is_supported(*t, fmt)) {
        return { false, t, "SQL type is not supported for this engine format." };
    }

    return { true, t, nullptr };
}

// -----------------------------------------------------------------------------
// Open hook surface
// These are intentionally small and non-invasive.
// The app can start using them without a runtime registry object.
// -----------------------------------------------------------------------------
struct ResolvedFieldType {
    char            dbf_code;
    SemanticType    semantic_type;
    StorageFamily   storage_family;
    std::uint8_t    width;
    std::uint8_t    decimals;
    const TypeInfo* info;
};

constexpr inline ResolvedFieldType resolve_field_type(char dbf_code,
                                                      std::uint8_t width,
                                                      std::uint8_t decimals) noexcept
{
    const TypeInfo* t = find_by_code(dbf_code);
    return {
        up_char(dbf_code),
        derive_semantic_type(dbf_code, width, decimals),
        t ? t->storage_family : StorageFamily::Unknown,
        width,
        decimals,
        t
    };
}

// -----------------------------------------------------------------------------
// Suggested integration points
//
// CREATE:
//   validate_type_for_format(type, format)
//   validate_sql_type_for_format(sql_type_name, format)
//
// USE/open:
//   resolve_field_type(field.type, field.length, field.decimals)
//
// STRUCT/FIELDS:
//   info->display_name / semantic_type
//
// importsql:
//   find_by_sql_name(...) or validate_sql_type_for_format(...)
//
// tuptalk:
//   resolve_field_type(...).semantic_type
// -----------------------------------------------------------------------------

} // namespace dottalk::types