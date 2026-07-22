// xbase_64.hpp
// x64 dialect expansion layer.
//
// Metadata authority phase:
// - xbase.hpp remains neutral and stores only resolved runtime truth.
// - xbase_vfp.hpp remains the classic/VFP descriptor bridge.
// - xbase_64.hpp owns x64 extension structures, x64 vector metadata,
//   fallback descriptor policy, and name resolution.
// - 10-byte DBF/VFP descriptor names remain compatibility fallback tokens.
// - Optional X64M metadata blocks may carry authoritative table/field names.
// - Missing metadata falls back to descriptor tokens; invalid x64 structural
//   headers still fail rather than pretending to be x32.

#pragma once

#include "xbase_vfp.hpp"

#include <cstdint>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace xbase {

// -----------------------------------------------------------------------------
// X64 VERSION BYTE
// -----------------------------------------------------------------------------
constexpr uint8_t DBF_VERSION_64 = 0x64;

// -----------------------------------------------------------------------------
// X64 LARGE HEADER EXTENSION (64 bytes)
// -----------------------------------------------------------------------------
#pragma pack(push, 1)
struct LargeHeaderExtension {
    uint64_t record_count;     // total records (64-bit)
    uint64_t data_start_64;    // data section offset
    uint64_t record_size_64;   // bytes per record
    uint64_t autoq_next;       // next autoincrement / sequence value
    uint32_t table_flags;      // x64 table capability flags
    uint32_t reserved32;       // reserved
    uint64_t reserved[3];      // reserved, future use
};
#pragma pack(pop)

static_assert(sizeof(LargeHeaderExtension) == 64,
              "LargeHeaderExtension must be exactly 64 bytes");

// Base 32-byte header + 64-byte x64 extension. Field descriptors still begin
// immediately after this prelude in the current compatibility geometry.
constexpr uint16_t LARGE_HEADER_SIZE =
    32 + static_cast<uint16_t>(sizeof(LargeHeaderExtension));

// -----------------------------------------------------------------------------
// OPTIONAL X64 METADATA LOCATOR / VECTOR METADATA BLOCK
//
// X64MetaLocator is reserved for a later locator geometry. The current metadata
// authority phase stores X64M immediately after the descriptor terminator and
// before record data, with data_start_64/header_size pointing after X64M.
// -----------------------------------------------------------------------------
#pragma pack(push, 1)
struct X64MetaLocator {
    uint64_t meta_offset;   // absolute file offset of metadata block
    uint32_t meta_length;   // metadata block length in bytes
    uint16_t meta_version;  // metadata sub-format version
    uint16_t meta_flags;    // reserved
};
#pragma pack(pop)

static_assert(sizeof(X64MetaLocator) == 16,
              "X64MetaLocator must be exactly 16 bytes");

#pragma pack(push, 1)
struct X64MetaHeader {
    char     magic[4];            // "X64M"
    uint16_t version;             // metadata version
    uint16_t flags;               // policy / reserved

    uint32_t total_length;        // total metadata block length in bytes

    uint32_t table_name_offset;   // relative to string_pool_offset
    uint16_t table_name_length;   // bytes
    uint16_t reserved0;

    uint32_t field_entry_offset;  // relative to metadata block start
    uint32_t field_count;         // number of X64FieldNameEntry records

    uint32_t string_pool_offset;  // relative to metadata block start
    uint32_t string_pool_length;  // bytes

    uint32_t checksum;            // optional; zero if unused
    uint32_t reserved1;
};
#pragma pack(pop)

static_assert(sizeof(X64MetaHeader) == 44,
              "X64MetaHeader must be exactly 44 bytes");

#pragma pack(push, 1)
struct X64FieldNameEntry {
    uint32_t field_index;   // 1-based field index
    uint32_t name_offset;   // relative to string_pool_offset
    uint16_t name_length;   // bytes
    uint16_t flags;         // reserved / policy
};
#pragma pack(pop)

static_assert(sizeof(X64FieldNameEntry) == 12,
              "X64FieldNameEntry must be exactly 12 bytes");

#pragma pack(push, 1)
struct X64FieldMetaEntry {
    uint32_t field_index;   // 1-based field index
    uint32_t name_offset;   // relative to string_pool_offset
    uint16_t name_length;   // bytes
    uint16_t flags;         // reserved / policy
    uint32_t field_length;  // authoritative runtime field length in bytes
};
#pragma pack(pop)

static_assert(sizeof(X64FieldMetaEntry) == 16,
              "X64FieldMetaEntry must be exactly 16 bytes");

// -----------------------------------------------------------------------------
// X64 TABLE FLAGS
// -----------------------------------------------------------------------------
constexpr uint32_t DBF64_FLAG_HAS_MEMO              = 0x00000001;
constexpr uint32_t DBF64_FLAG_HAS_RECID_PK          = 0x00000002;
constexpr uint32_t DBF64_FLAG_STRICT_FALLBACK_NAMES = 0x00000004;
constexpr uint32_t DBF64_FLAG_HAS_META_BLOCK        = 0x00000008;

constexpr uint32_t DBF64_KNOWN_TABLE_FLAGS =
    DBF64_FLAG_HAS_MEMO |
    DBF64_FLAG_HAS_RECID_PK |
    DBF64_FLAG_STRICT_FALLBACK_NAMES |
    DBF64_FLAG_HAS_META_BLOCK;

// -----------------------------------------------------------------------------
// X64 NAMING / VECTOR CONTRACT
// -----------------------------------------------------------------------------
constexpr uint16_t X64_TABLE_NAME_LENGTH      = 128;   // maintained default
constexpr uint16_t X64_FIELD_NAME_LENGTH      = 128;   // maintained default
constexpr uint16_t X64_TABLE_NAME_LENGTH_MAX  = 256;   // ceiling (was 128; doubled)
constexpr uint16_t X64_FIELD_NAME_LENGTH_MAX  = 256;   // ceiling (was 128; doubled)
constexpr uint16_t X64_FALLBACK_FIELD_TOKEN_BYTES = 10; // DBF/VFP fallback token

// -----------------------------------------------------------------------------
// Policy helpers
// -----------------------------------------------------------------------------
inline bool x64_table_name_fits(std::size_t bytes) noexcept {
    return bytes <= X64_TABLE_NAME_LENGTH_MAX;   // allow up to the ceiling
}

inline bool x64_field_name_fits(std::size_t bytes) noexcept {
    return bytes <= X64_FIELD_NAME_LENGTH_MAX;   // allow up to the ceiling
}

inline std::string x64_fallback_field_token(const std::string& name)
{
    if (name.size() <= X64_FALLBACK_FIELD_TOKEN_BYTES) return name;
    return name.substr(0, X64_FALLBACK_FIELD_TOKEN_BYTES);
}

inline std::string x64_descriptor_field_token(const std::string& name)
{
    return x64_fallback_field_token(name);
}

inline bool x64_has_name_vector_metadata(uint32_t table_flags) noexcept
{
    return (table_flags & DBF64_FLAG_HAS_META_BLOCK) != 0;
}

inline uint16_t x64_effective_table_name_length(uint32_t table_flags) noexcept
{
    (void)table_flags;
    return X64_TABLE_NAME_LENGTH;
}

inline uint16_t x64_effective_field_name_length(uint32_t table_flags) noexcept
{
    (void)table_flags;
    return X64_FIELD_NAME_LENGTH;
}

inline bool x64_should_use_descriptor_name_fallback(uint32_t table_flags) noexcept
{
    return !x64_has_name_vector_metadata(table_flags);
}

inline std::uint16_t x64_compatible_u16_mirror(std::uint64_t value) noexcept
{
    return (value > static_cast<std::uint64_t>(std::numeric_limits<std::uint16_t>::max()))
        ? std::numeric_limits<std::uint16_t>::max()
        : static_cast<std::uint16_t>(value);
}

inline bool x64_compatible_u16_matches(std::uint16_t mirror, std::uint64_t wide) noexcept
{
    if (mirror == 0) {
        return true;
    }

    if (wide <= static_cast<std::uint64_t>(std::numeric_limits<std::uint16_t>::max())) {
        return mirror == static_cast<std::uint16_t>(wide);
    }

    return mirror == std::numeric_limits<std::uint16_t>::max();
}

inline std::string x64_resolve_field_name_or_fallback(uint32_t table_flags,
                                                      const std::string& metadata_name,
                                                      const std::string& fallback_name)
{
    if (x64_has_name_vector_metadata(table_flags) && !metadata_name.empty() &&
        x64_field_name_fits(metadata_name.size())) {
        return metadata_name;
    }
    return fallback_name;
}

// -----------------------------------------------------------------------------
// X64M metadata helpers
// -----------------------------------------------------------------------------
inline std::vector<char> x64_build_name_metadata(const std::string& table_name,
                                                 const std::vector<std::string>& field_names,
                                                 const std::vector<std::uint32_t>& field_lengths = {})
{
    struct PendingFieldMeta {
        uint32_t field_index{};
        std::string name;
        uint32_t field_length{};
    };

    const bool use_table_name = !table_name.empty() && x64_table_name_fits(table_name.size());

    std::vector<PendingFieldMeta> pending;
    pending.reserve(field_names.size());

    for (std::size_t i = 0; i < field_names.size(); ++i) {
        const std::string& name = field_names[i];
        if (name.empty()) continue;
        if (!x64_field_name_fits(name.size())) continue;

        const std::uint32_t len =
            (i < field_lengths.size()) ? field_lengths[i] : 0u;

        pending.push_back(PendingFieldMeta{static_cast<uint32_t>(i + 1), name, len});
    }

    if (!use_table_name && pending.empty()) {
        return {};
    }

    const uint32_t entry_offset = static_cast<uint32_t>(sizeof(X64MetaHeader));
    const uint32_t field_count = static_cast<uint32_t>(pending.size());
    const uint32_t string_pool_offset =
        entry_offset + field_count * static_cast<uint32_t>(sizeof(X64FieldMetaEntry));

    std::vector<char> string_pool;
    string_pool.reserve((use_table_name ? table_name.size() : 0) + field_names.size() * 16);

    uint32_t table_name_offset = 0;
    uint16_t table_name_length = 0;
    if (use_table_name) {
        table_name_offset = static_cast<uint32_t>(string_pool.size());
        table_name_length = static_cast<uint16_t>(table_name.size());
        string_pool.insert(string_pool.end(), table_name.begin(), table_name.end());
    }

    std::vector<X64FieldMetaEntry> entries;
    entries.reserve(pending.size());

    for (const auto& p : pending) {
        X64FieldMetaEntry e{};
        e.field_index = p.field_index;
        e.name_offset = static_cast<uint32_t>(string_pool.size());
        e.name_length = static_cast<uint16_t>(p.name.size());
        e.flags = 0;
        e.field_length = p.field_length;
        string_pool.insert(string_pool.end(), p.name.begin(), p.name.end());
        entries.push_back(e);
    }

    const uint32_t total_length =
        string_pool_offset + static_cast<uint32_t>(string_pool.size());

    X64MetaHeader mh{};
    mh.magic[0] = 'X';
    mh.magic[1] = '6';
    mh.magic[2] = '4';
    mh.magic[3] = 'M';
    mh.version = 2;
    mh.flags = 0;
    mh.total_length = total_length;
    mh.table_name_offset = table_name_offset;
    mh.table_name_length = table_name_length;
    mh.reserved0 = 0;
    mh.field_entry_offset = entry_offset;
    mh.field_count = field_count;
    mh.string_pool_offset = string_pool_offset;
    mh.string_pool_length = static_cast<uint32_t>(string_pool.size());
    mh.checksum = 0;
    mh.reserved1 = 0;

    std::vector<char> out(total_length, 0);
    std::memcpy(out.data(), &mh, sizeof(mh));
    if (!entries.empty()) {
        std::memcpy(out.data() + entry_offset,
                    entries.data(),
                    entries.size() * sizeof(X64FieldMetaEntry));
    }
    if (!string_pool.empty()) {
        std::memcpy(out.data() + string_pool_offset,
                    string_pool.data(),
                    string_pool.size());
    }

    return out;
}

inline void x64_apply_name_metadata(DbArea& area,
                                    const std::vector<char>& block,
                                    std::string* why = nullptr)
{
    auto fail = [&](const char* msg) {
        if (why) *why = msg;
        throw std::runtime_error(std::string("Invalid x64 metadata block: ") + msg);
    };

    if (block.size() < sizeof(X64MetaHeader)) {
        fail("block shorter than X64MetaHeader");
    }

    X64MetaHeader mh{};
    std::memcpy(&mh, block.data(), sizeof(mh));

    if (std::memcmp(mh.magic, "X64M", 4) != 0) {
        fail("missing X64M magic");
    }
    if (mh.version != 1 && mh.version != 2) {
        fail("unsupported X64M version");
    }
    if (mh.total_length > block.size()) {
        fail("total_length exceeds available block bytes");
    }
    if (mh.string_pool_offset > mh.total_length ||
        mh.string_pool_length > mh.total_length - mh.string_pool_offset) {
        fail("string pool is out of range");
    }
    if (mh.field_entry_offset > mh.total_length) {
        fail("field entry offset is out of range");
    }
    const std::size_t entry_size =
        (mh.version == 1) ? sizeof(X64FieldNameEntry) : sizeof(X64FieldMetaEntry);
    const uint64_t entries_bytes =
        static_cast<uint64_t>(mh.field_count) * static_cast<uint64_t>(entry_size);
    if (entries_bytes > mh.total_length - mh.field_entry_offset) {
        fail("field entries exceed metadata block");
    }

    auto read_string = [&](uint32_t off, uint32_t len) -> std::string {
        if (len == 0) return {};
        if (off > mh.string_pool_length || len > mh.string_pool_length - off) {
            fail("string reference is out of range");
        }
        const char* base = block.data() + mh.string_pool_offset + off;
        return std::string(base, base + len);
    };

    if (mh.table_name_length != 0) {
        std::string table = read_string(mh.table_name_offset, mh.table_name_length);
        if (!table.empty() && x64_table_name_fits(table.size())) {
            area.setLogicalName(std::move(table));
        }
    }

    for (uint32_t i = 0; i < mh.field_count; ++i) {
        uint32_t field_index = 0;
        uint32_t name_offset = 0;
        uint16_t name_length = 0;
        uint32_t field_length = 0;

        const std::size_t pos = static_cast<std::size_t>(mh.field_entry_offset) +
                                static_cast<std::size_t>(i) * entry_size;

        if (mh.version == 1) {
            X64FieldNameEntry e{};
            std::memcpy(&e, block.data() + pos, sizeof(e));
            field_index = e.field_index;
            name_offset = e.name_offset;
            name_length = e.name_length;
        } else {
            X64FieldMetaEntry e{};
            std::memcpy(&e, block.data() + pos, sizeof(e));
            field_index = e.field_index;
            name_offset = e.name_offset;
            name_length = e.name_length;
            field_length = e.field_length;
        }

        if (field_index == 0 || field_index > static_cast<uint32_t>(area.fieldCount())) {
            fail("field entry index is out of range");
        }

        std::string name = read_string(name_offset, name_length);
        if (!name.empty() && x64_field_name_fits(name.size())) {
            area.setFieldName(static_cast<int>(field_index), std::move(name));
        }

        if (field_length != 0) {
            area.setFieldLength(static_cast<int>(field_index), field_length);
        }
    }

    if (why) why->clear();
}

// -----------------------------------------------------------------------------
// 0x64 LOADER
// -----------------------------------------------------------------------------
namespace x64_loader {

inline bool validate_large_header_extension(const VfpHeader& vh,
                                            const LargeHeaderExtension& ext,
                                            std::string* why = nullptr)
{
    auto fail = [&](const char* msg) {
        if (why) {
            *why = msg;
        }
        return false;
    };

    if (vh.version != DBF_VERSION_64) {
        return fail("x64 compatible header version byte is not 0x64");
    }

    // x64 extension values are authoritative. Do not silently fall back to
    // the compatible 16-bit header values, because that masks damaged or
    // diminished x64 metadata.
    if (ext.data_start_64 < LARGE_HEADER_SIZE) {
        return fail("x64 data_start_64 is before the field descriptor area");
    }

    if (ext.record_size_64 == 0) {
        return fail("x64 record_size_64 is zero");
    }

    // The compatible VFP-style header should mirror the x64 extension geometry
    // when those compatible fields are populated.
    if (!x64_compatible_u16_matches(vh.header_size, ext.data_start_64)) {
        return fail("x64 data_start_64 disagrees with compatible header_size");
    }

    if (!x64_compatible_u16_matches(vh.record_size, ext.record_size_64)) {
        return fail("x64 record_size_64 disagrees with compatible record_size");
    }

    if ((ext.table_flags & ~DBF64_KNOWN_TABLE_FLAGS) != 0) {
        return fail("x64 table_flags contain unknown bits");
    }

    return true;
}

inline LargeHeaderExtension read_extension_at_start(std::istream& fp)
{
    fp.clear();
    fp.seekg(static_cast<std::streamoff>(sizeof(VfpHeader)), std::ios::beg);
    LargeHeaderExtension ext{};
    fp.read(reinterpret_cast<char*>(&ext), sizeof(ext));
    if (!fp) {
        throw std::runtime_error("Truncated x64 64-byte extension");
    }
    return ext;
}

inline void readHeader(DbArea& area, std::istream& fp) {
    const uint8_t ver = vfp_loader::peekVersion(fp);
    if (ver != DBF_VERSION_64) {
        throw std::runtime_error("Not an xbase_64 file (expected 0x64)");
    }

    area.setVersionByte(ver);
    area.setKind(detect_area_kind_from_version(ver));

    VfpHeader vh{};
    fp.read(reinterpret_cast<char*>(&vh), sizeof(vh));
    if (!fp) {
        throw std::runtime_error("Failed to read base 32-byte x64 header");
    }

    area.setVersionByte(vh.version);
    area.setKind(detect_area_kind_from_version(vh.version));
    area.setLastUpdated(vh.yy, vh.mm, vh.dd);

    LargeHeaderExtension ext{};
    fp.read(reinterpret_cast<char*>(&ext), sizeof(ext));
    if (!fp) {
        throw std::runtime_error("Truncated x64 64-byte extension");
    }

    std::string why;
    if (!validate_large_header_extension(vh, ext, &why)) {
        throw std::runtime_error("Invalid x64 header extension: " + why);
    }

    // x64 record_count is authoritative. Preserve the full 64-bit value in
    // DbArea and let the legacy 32-bit mirror clamp only where required.
    area.setRecordCount64(ext.record_count);

    area.setDataStart(ext.data_start_64);
    area.setRecordLength(ext.record_size_64);
    area.setAutoQNext64(ext.autoq_next);
    area.setTableFlags(ext.table_flags);
}

inline void readFields(DbArea& area,
                       std::istream& fp,
                       std::vector<VfpFieldExtras>& extras)
{
    const LargeHeaderExtension ext = read_extension_at_start(fp);

    fp.clear();
    fp.seekg(LARGE_HEADER_SIZE, std::ios::beg);
    if (!fp) {
        throw std::runtime_error("Failed to seek to x64 field descriptor area");
    }

    // Descriptors remain the compatibility fallback source and are still read
    // exactly like classic/VFP descriptors until the 0x0D terminator.
    vfp_loader::readFields(area, fp, extras);

    if (!x64_has_name_vector_metadata(ext.table_flags)) {
        return;
    }

    const std::streampos pos_after_descriptors = fp.tellg();
    if (pos_after_descriptors < std::streampos(0)) {
        throw std::runtime_error("Failed to locate x64 metadata start");
    }

    const auto meta_start = static_cast<std::uint64_t>(pos_after_descriptors);
    if (ext.data_start_64 <= meta_start) {
        throw std::runtime_error("x64 metadata flag set but no metadata bytes before data_start_64");
    }

    const std::uint64_t meta_len64 = ext.data_start_64 - meta_start;
    if (meta_len64 > static_cast<std::uint64_t>(std::numeric_limits<std::uint32_t>::max())) {
        throw std::runtime_error("x64 metadata block is too large");
    }

    std::vector<char> block(static_cast<std::size_t>(meta_len64));
    fp.read(block.data(), static_cast<std::streamsize>(block.size()));
    if (!fp) {
        throw std::runtime_error("Failed to read x64 metadata block");
    }

    x64_apply_name_metadata(area, block);
}

} // namespace x64_loader

} // namespace xbase
