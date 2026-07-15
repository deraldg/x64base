// include/snx/snx.hpp
#pragma once
//
// SNX container format
// --------------------
// Purpose:
//   - Future custom compound index family (peer to CNX/CDX)
//   - Keep one canonical on-disk format
//   - Avoid embedded INX payload/document duplication
//
// Design rules:
//   - Single canonical header
//   - Optional table bind block
//   - Tag directory is authoritative
//   - Each tag points to a root block/page/chain
//   - 64-bit offsets throughout
//   - Raw I/O helpers included for future page/block work

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace snxfile {

static constexpr std::uint32_t SNX_MAGIC             = 0x31584E53; // "SNX1" little-end
static constexpr std::uint32_t SNX_VERSION           = 1;
static constexpr std::uint32_t SNX_DEFAULT_PAGE_SIZE = 4096;

enum : std::uint32_t {
    SNX_HDRF_DIRTY     = 0x0001,
    SNX_HDRF_HAS_BIND  = 0x0002,
};

enum : std::uint32_t {
    SNX_TAGF_ASCENDING = 0x0001,
    SNX_TAGF_UNIQUE    = 0x0002,
    SNX_TAGF_FILTERED  = 0x0004,
    SNX_TAGF_BINARY    = 0x0008,
};

enum class KeyType : std::uint32_t {
    Unknown = 0,
    Character,
    Numeric,
    Date,
    DateTime,
    Logical,
    Integer,
    Binary,
};

struct SNXHeader {
    std::uint32_t magic       = SNX_MAGIC;
    std::uint32_t version     = SNX_VERSION;
    std::uint32_t page_size   = SNX_DEFAULT_PAGE_SIZE;
    std::uint32_t flags       = 0;

    std::uint64_t tagdir_offset    = 0;
    std::uint32_t tag_count        = 0;
    std::uint32_t active_tag_hint  = 0; // 0-based; advisory only

    std::uint64_t bind_offset      = 0; // 0 if absent
    std::uint64_t reserved1        = 0;
    std::uint64_t reserved2        = 0;
};

struct TagDirEntry {
    char          name[32]         = {0};

    std::uint32_t tag_id           = 0;
    std::uint32_t flags            = 0;
    std::uint32_t collation_id     = 0;
    std::uint32_t reserved0        = 0;

    std::uint64_t expr_hash64      = 0;
    std::uint64_t for_hash64       = 0;

    std::uint32_t key_type         = 0; // KeyType
    std::uint32_t key_len          = 0;

    std::uint64_t root_block_off   = 0; // root page/block/chain head
    std::uint64_t stats_rec_count  = 0;
    std::uint64_t updated_ts       = 0;
};

struct TagInfo {
    std::string   name;
    std::uint32_t tag_id           = 0;
    std::uint32_t flags            = 0;
    std::uint32_t collation_id     = 0;

    std::uint64_t expr_hash64      = 0;
    std::uint64_t for_hash64       = 0;

    std::uint32_t key_type         = 0;
    std::uint32_t key_len          = 0;

    std::uint64_t root_block_off   = 0;
    std::uint64_t stats_rec_count  = 0;
    std::uint64_t updated_ts       = 0;
};

struct TableBind {
    std::uint8_t  table_uuid[16]{};
    std::uint64_t schema_hash64    = 0;
    std::uint32_t record_len       = 0;
    std::uint32_t field_count      = 0;
    char          table_basename[40]{};
    std::uint64_t build_dbftime    = 0;
    std::uint8_t  _pad[64]{};
};

struct TableProbe {
    std::uint8_t  table_uuid[16]{};
    std::uint64_t schema_hash64    = 0;
    std::uint32_t record_len       = 0;
    std::uint32_t field_count      = 0;
    std::string   table_basename_upper;
    std::uint64_t dbf_mtime        = 0;
};

enum class BindPolicy {
    STRICT,
    WARN,
    LOOSE
};

struct BindCheck {
    bool ok = false;
    bool warn = false;
    std::string message;
};

struct SNXHandle; // opaque

// ---- open / close / header -----------------------------------------------

bool open(const std::string& path, SNXHandle*& out);
void close(SNXHandle*& h);

bool read_header(SNXHandle* h, SNXHeader& hdr);
bool flush_header(SNXHandle* h, const SNXHeader& hdr);
bool set_dirty(SNXHandle* h, bool dirty);

std::optional<std::uint32_t> page_size(SNXHandle* h);

// ---- table bind -----------------------------------------------------------

bool read_table_bind(SNXHandle* h, TableBind& out);
bool write_table_bind(SNXHandle* h, const TableBind& in);

// ---- tag directory --------------------------------------------------------

bool read_tagdir(SNXHandle* h, std::vector<TagInfo>& out);
bool write_tagdir(SNXHandle* h, const std::vector<TagInfo>& tags);

bool add_tag(SNXHandle* h, const std::string& tag_name_upper);
bool drop_tag(SNXHandle* h, const std::string& tag_name_upper);

// ---- attach validation ----------------------------------------------------

BindCheck validate_table_bind(const TableBind& bind,
                              const TableProbe& probe,
                              BindPolicy policy);

// ---- minimal raw I/O helpers ---------------------------------------------

bool append_bytes(SNXHandle* h,
                  const void* data,
                  std::size_t len,
                  std::uint64_t& out_off);

bool read_at(SNXHandle* h,
             std::uint64_t off,
             void* buf,
             std::size_t len);

bool write_at(SNXHandle* h,
              std::uint64_t off,
              const void* buf,
              std::size_t len);

} // namespace snxfile