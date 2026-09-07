// @dottalk.file v1
// subsystem: xbase
// layer: helper
// owns: durable PRIMARY designation in the x64 metadata block
// project: project.x64base.runtime
// lane: AIF-156
// owner: member.derald
// status: supported

// File: src/xbase/x64_field_meta.cpp
// Purpose: THE X64 METADATA BLOCK'S FIRST WRITER.
//
// The block has only ever been BUILT, at CREATE, by
// x64_build_name_metadata() called from dbf_create.cpp. Nothing has ever
// rewritten one. That absence is the reason the PRIMARY key designation lived
// in a process-local std::unordered_map in unique_registry.cpp -- whose own
// boundary comment calls it "not persistent schema metadata" -- and therefore
// did not survive a close. A refusal built on a fact that evaporates at exit is
// not an enforced key.
//
// The x64 header is SELF-DESCRIBING: it already carries the table's logical
// name, its field names and the authoritative field lengths. The key
// designation belongs in the same place, for the same reason.
//
// Boundary: this unit owns the bytes. WHICH field should be primary, and what
// happens to a write that targets it, are command policy and live above the
// engine.
// Notes: ASCII only.

#include "xbase.hpp"
#include "xbase_64.hpp"

#include <cstddef>
#include <cstring>
#include <string>
#include <vector>

namespace xbase {

namespace {

// Byte offset of X64FieldMetaEntry::flags within the entry.
constexpr std::size_t kEntryFlagsOffset = offsetof(X64FieldMetaEntry, flags);

void set_err(std::string* err, const char* text) { if (err) *err = text; }

} // namespace

int DbArea::primaryFieldIndex() const noexcept
{
    const int n = static_cast<int>(_fields.size());
    for (int f = 1; f <= n; ++f) {
        if (x64_field_is_primary(_fields[static_cast<std::size_t>(f - 1)].x64_flags)) {
            return f;
        }
    }
    return 0;
}

bool DbArea::setFieldPrimaryDurable(int field1, bool make_primary, std::string* err)
{
    if (err) err->clear();

    if (!isOpen()) {
        set_err(err, "no table is open");
        return false;
    }
    if (_dbf_version_byte != DBF_VERSION_64) {
        set_err(err, "only an x64 table can carry a durable PRIMARY designation; "
                     "this table's header has nowhere to record one");
        return false;
    }
    if (_x64_meta_start == 0 || _x64_meta_len < sizeof(X64MetaHeader)) {
        set_err(err, "this x64 table has no metadata block, so there is no entry "
                     "to stamp; the designation cannot be made durable here");
        return false;
    }

    const int nfields = static_cast<int>(_fields.size());
    if (make_primary && (field1 < 1 || field1 > nfields)) {
        set_err(err, "field index is out of range");
        return false;
    }

    // ---- Read the metadata header -----------------------------------------
    X64MetaHeader mh{};
    io().clear();
    io().seekg(static_cast<std::streamoff>(_x64_meta_start), std::ios::beg);
    io().read(reinterpret_cast<char*>(&mh), sizeof(mh));
    if (!io()) {
        io().clear();
        set_err(err, "could not read the x64 metadata header");
        return false;
    }

    if (mh.magic[0] != 'X' || mh.magic[1] != '6' ||
        mh.magic[2] != '4' || mh.magic[3] != 'M') {
        set_err(err, "the x64 metadata block does not carry the X64M magic");
        return false;
    }

    // VERSION 1 IS LEFT ALONE ON PURPOSE. X64FieldNameEntry has a flags word
    // too, and it has never been written as anything but zero. Giving it a
    // meaning now would be inventing a claim about tables produced by a format
    // version that never made one.
    if (mh.version != 2) {
        set_err(err, "this table's metadata block predates per-field flags; "
                     "its entries cannot carry a PRIMARY designation");
        return false;
    }

    const std::uint64_t entries_base = _x64_meta_start + mh.field_entry_offset;
    const std::uint64_t entries_bytes =
        static_cast<std::uint64_t>(mh.field_count) * sizeof(X64FieldMetaEntry);
    if (mh.field_entry_offset > _x64_meta_len ||
        entries_bytes > _x64_meta_len - mh.field_entry_offset) {
        set_err(err, "the x64 metadata field entries run past the end of the block");
        return false;
    }

    // ---- Pass 1: read every entry's index and flags ------------------------
    //
    // AN ENTRY EXISTS ONLY FOR A FIELD WHOSE NAME WAS RECORDED. The builder
    // skips empty names and names that do not fit, so a field can be perfectly
    // real and still have no entry to stamp. That is a refusal with a reason,
    // not a silent no-op.
    struct Slot { std::uint32_t index; std::uint16_t flags; std::uint64_t flags_pos; };
    std::vector<Slot> slots;
    slots.reserve(mh.field_count);

    for (std::uint32_t i = 0; i < mh.field_count; ++i) {
        const std::uint64_t pos = entries_base + static_cast<std::uint64_t>(i) * sizeof(X64FieldMetaEntry);
        X64FieldMetaEntry e{};
        io().clear();
        io().seekg(static_cast<std::streamoff>(pos), std::ios::beg);
        io().read(reinterpret_cast<char*>(&e), sizeof(e));
        if (!io()) {
            io().clear();
            set_err(err, "could not read an x64 metadata field entry");
            return false;
        }
        slots.push_back(Slot{e.field_index, e.flags, pos + kEntryFlagsOffset});
    }

    bool target_found = !make_primary;
    for (const Slot& s : slots) {
        if (make_primary && static_cast<int>(s.index) == field1) target_found = true;
    }
    if (!target_found) {
        set_err(err, "that field has no entry in this table's metadata block, so "
                     "there is nowhere durable to record the designation");
        return false;
    }

    // ---- Pass 2: write only the entries whose flags actually change --------
    //
    // Clearing every other field first is not tidiness: a table has at most one
    // primary key, so a second stamp must MOVE the designation. Leaving the old
    // bit standing would produce a table with two, and primaryFieldIndex()
    // would then answer with whichever came first.
    for (const Slot& s : slots) {
        const bool want_primary =
            make_primary && static_cast<int>(s.index) == field1;
        std::uint16_t next = s.flags;
        if (want_primary) next |= X64_FIELD_FLAG_PRIMARY;
        else              next = static_cast<std::uint16_t>(next & ~X64_FIELD_FLAG_PRIMARY);

        if (next == s.flags) continue;

        io().clear();
        io().seekp(static_cast<std::streamoff>(s.flags_pos), std::ios::beg);
        io().write(reinterpret_cast<const char*>(&next), sizeof(next));
        if (!io()) {
            io().clear();
            set_err(err, "could not write an x64 metadata field entry");
            return false;
        }
    }

    // ---- The table-level summary bit ---------------------------------------
    //
    // DBF64_FLAG_HAS_RECID_PK has been declared and never set since the format
    // was defined. It earns its place here because a per-field bit cannot raise
    // a question an old reader can see: a binary that predates
    // X64_FIELD_FLAG_PRIMARY reads it as zero and enforces nothing, in silence.
    // The table flag is at least comparable against DBF64_KNOWN_TABLE_FLAGS, so
    // a table can announce a capability its reader does not have.
    //
    // Patched in place at its own offsetof, exactly as the append path patches
    // record_count -- so dialect tail bytes are never rewritten.
    {
        const std::streamoff flags_pos =
            static_cast<std::streamoff>(sizeof(VfpHeader)) +
            static_cast<std::streamoff>(offsetof(LargeHeaderExtension, table_flags));

        std::uint32_t tf = 0;
        io().clear();
        io().seekg(flags_pos, std::ios::beg);
        io().read(reinterpret_cast<char*>(&tf), sizeof(tf));
        if (!io()) {
            io().clear();
            set_err(err, "could not read the x64 table flags");
            return false;
        }

        const std::uint32_t next_tf = make_primary
            ? (tf | DBF64_FLAG_HAS_RECID_PK)
            : static_cast<std::uint32_t>(tf & ~DBF64_FLAG_HAS_RECID_PK);

        if (next_tf != tf) {
            io().clear();
            io().seekp(flags_pos, std::ios::beg);
            io().write(reinterpret_cast<const char*>(&next_tf), sizeof(next_tf));
            if (!io()) {
                io().clear();
                set_err(err, "could not write the x64 table flags");
                return false;
            }
        }
        _x64_table_flags = next_tf;
    }

    io().flush();
    if (!io()) {
        io().clear();
        set_err(err, "the metadata patch did not reach the file");
        return false;
    }
    io().clear();

    // ---- Bring the in-memory picture into line -----------------------------
    //
    // Last, and only after the bytes are down. An in-memory designation that
    // outlives a failed write is the same defect this whole change exists to
    // remove, one layer up.
    for (int f = 1; f <= nfields; ++f) {
        std::uint16_t cur = _fields[static_cast<std::size_t>(f - 1)].x64_flags;
        if (make_primary && f == field1) cur |= X64_FIELD_FLAG_PRIMARY;
        else cur = static_cast<std::uint16_t>(cur & ~X64_FIELD_FLAG_PRIMARY);
        _fields[static_cast<std::size_t>(f - 1)].x64_flags = cur;
    }

    return true;
}

} // namespace xbase
