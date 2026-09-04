// @dottalk.file v1
// subsystem: include
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// xbase_vfp.hpp
// FoxPro / Visual FoxPro extensions - include only where needed

#pragma once

#include "xbase.hpp"

#include <cstddef>
#include <cstdint>
#include <cstring>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace xbase {

// ------------------------------------------------------------------------
// VFP-specific field extras (not baked into FieldDef)
// ------------------------------------------------------------------------
struct VfpFieldExtras {
    bool        nullable      {false};
    bool        binary        {false};
    // Flag 0x01. The `_NullFlags` column is a SYSTEM field and must be kept out of
    // the user field vector; nothing decoded this before AIF-091 M1.
    bool        system        {false};
    bool        autoincrement {false};
    uint32_t    next_autoinc  {0};
    uint8_t     step_autoinc  {0};
    std::string long_name     {};
};

// ------------------------------------------------------------------------
// DBF level / flavor detection
// ------------------------------------------------------------------------
enum class DbfLevel : uint8_t {
    ClassicNoMemo   = 0x03,
    ClassicWithMemo = 0x83,
    Fox26Memo       = 0xF5,
    VfpBase         = 0x30,
    VfpAutoInc      = 0x31,
    VfpVar          = 0x32
};

inline std::string versionHex(uint8_t version)
{
    std::ostringstream oss;
    oss << "0x"
        << std::uppercase
        << std::hex
        << std::setw(2)
        << std::setfill('0')
        << static_cast<unsigned int>(version);
    return oss.str();
}

inline DbfLevel detectDbfLevel(uint8_t version) {
    switch (version) {
        case 0x03: return DbfLevel::ClassicNoMemo;
        case 0x83: return DbfLevel::ClassicWithMemo;
        case 0xF5: return DbfLevel::Fox26Memo;
        case 0x30: return DbfLevel::VfpBase;
        case 0x31: return DbfLevel::VfpAutoInc;
        case 0x32: return DbfLevel::VfpVar;
        default:
            throw std::runtime_error("Unsupported DBF version: " + versionHex(version));
    }
}

inline bool isVfp(DbfLevel lvl) noexcept {
    return lvl == DbfLevel::VfpBase ||
           lvl == DbfLevel::VfpAutoInc ||
           lvl == DbfLevel::VfpVar;
}

inline bool isClassicLike(DbfLevel lvl) noexcept {
    return lvl == DbfLevel::ClassicNoMemo ||
           lvl == DbfLevel::ClassicWithMemo ||
           lvl == DbfLevel::Fox26Memo;
}

// ------------------------------------------------------------------------
// VFP header (32 bytes)
// ------------------------------------------------------------------------
#pragma pack(push, 1)
struct VfpHeader {
    uint8_t     version;
    uint8_t     yy;
    uint8_t     mm;
    uint8_t     dd;
    uint32_t    num_recs;
    uint16_t    header_size;
    uint16_t    record_size;
    uint8_t     reserved1[2];
    uint8_t     in_transaction;
    uint8_t     encrypted;
    uint8_t     reserved2[12];
    uint8_t     table_flags;
    uint8_t     codepage;
    uint16_t    reserved3;
};
#pragma pack(pop)

static_assert(sizeof(VfpHeader) == 32, "VfpHeader must be 32 bytes");

// ------------------------------------------------------------------------
// VFP field descriptor (32 bytes)
//
// CORRECTED 2026-09-04, AIF-091 M1. This struct used to place `flags` at BYTE 23
// and carried `workarea` at 20 -- which is the dBASE III field descriptor
// (work-area id at 20, SET FIELDS flag at 23), not the VFP one. Microsoft's table
// file structure is unambiguous:
//
//     18      Field flags: 0x01 system, 0x02 can store null, 0x04 binary,
//             0x0C autoincrementing
//     19-22   Autoincrement NEXT value
//     23      Autoincrement STEP value
//     24-31   Reserved
//
// So `ex.nullable = (vf.flags & 0x02)` was reading bit 1 of the AUTOINCREMENT STEP
// BYTE, and the real flags byte was swallowed inside `reserved1`. It has never
// decoded a nullable field. It never reported one either, which is why nothing
// caught it: measured 2026-09-04, every VFP- and x64-flavor table in this tree
// carries ZERO at byte 18 AND ZERO at byte 23, so the wrong byte and the right
// byte give the same answer on every file we own. The first genuinely nullable
// table to arrive would have been read as non-nullable IN SILENCE.
//
// Same shape as AIF-123: a default that never changed on any path anyone ran, so
// nothing could go red. The static_asserts below are what stop it drifting back --
// they state the documented layout as a compile-time claim rather than a comment.
//
// Source: Microsoft, "Table File Structure", VFP field subrecord layout; and
// Hentzen et al., Hacker's Guide to VFP, s1c2 ("bit 0 of byte 18").
// ------------------------------------------------------------------------
#pragma pack(push, 1)
struct VfpField {
    char        name[11];       // 0-10
    char        type;           // 11
    uint32_t    displacement;   // 12-15
    uint8_t     length;         // 16
    uint8_t     decimals;       // 17
    uint8_t     flags;          // 18  <- THE FIELD FLAGS. Byte 18, not 23.
    uint32_t    autoinc_next;   // 19-22
    uint8_t     autoinc_step;   // 23
    uint8_t     reserved[8];    // 24-31
};
#pragma pack(pop)

static_assert(sizeof(VfpField) == 32, "VfpField must be 32 bytes");
static_assert(offsetof(VfpField, type)         == 11, "VFP descriptor: type at byte 11");
static_assert(offsetof(VfpField, displacement) == 12, "VFP descriptor: displacement at 12");
static_assert(offsetof(VfpField, length)       == 16, "VFP descriptor: length at byte 16");
static_assert(offsetof(VfpField, decimals)     == 17, "VFP descriptor: decimals at byte 17");
static_assert(offsetof(VfpField, flags)        == 18, "VFP descriptor: FIELD FLAGS at byte 18");
static_assert(offsetof(VfpField, autoinc_next) == 19, "VFP descriptor: autoinc next at 19");
static_assert(offsetof(VfpField, autoinc_step) == 23, "VFP descriptor: autoinc step at 23");
static_assert(offsetof(VfpField, reserved)     == 24, "VFP descriptor: reserved at 24");

// The classic descriptor's `reserved` block STARTS AT THE SAME BYTE, which is what
// lets an x64 table carry field flags without changing its parse shape: the flags
// byte is already in the file, inherited, and simply was not being read.
static_assert(offsetof(FieldRec, reserved) == 18,
              "classic descriptor: reserved[0] must BE byte 18 (the VFP flags byte)");

// ------------------------------------------------------------------------
// DOES THIS FLAVOR'S FIELD DESCRIPTOR CARRY FIELD FLAGS AT BYTE 18?
//
// VFP lineage does, and X64 (0x64) inherits the descriptor shape, so it does too.
// CLASSIC FLAVORS DO NOT and must not be read that way: in dBASE III the same
// region is a work-area id and a SET FIELDS flag, so reading byte 18 as flags
// there would invent nullability out of unrelated bytes.
// ------------------------------------------------------------------------
inline bool descriptor_carries_field_flags(uint8_t version) noexcept
{
    return version == 0x30 || version == 0x31 || version == 0x32 || version == 0x64;
}

// ------------------------------------------------------------------------
// ONE PLACE THAT READS THE FLAGS BYTE.
//
// AUTOINCREMENT IS CHECKED FIRST AND IT IS NOT OPTIONAL. Microsoft lists 0x0C for
// "column is autoincrementing", and 0x0C is 0x04|0x08 -- so an autoincrementing
// field ALSO has the 0x04 bit set, and a naive `& 0x04` reports it as a BINARY
// column. Decoding autoinc first and excluding it from binary is the difference
// between reading the table and reading a plausible fiction.
// ------------------------------------------------------------------------
inline VfpFieldExtras decode_field_flags(uint8_t flags) noexcept
{
    VfpFieldExtras ex;
    ex.autoincrement = ((flags & 0x0C) == 0x0C);
    ex.nullable      = (flags & 0x02) != 0;
    ex.binary        = !ex.autoincrement && ((flags & 0x04) != 0);
    ex.system        = (flags & 0x01) != 0;
    return ex;
}

// ------------------------------------------------------------------------
// Version-aware loader helpers
// ------------------------------------------------------------------------
namespace vfp_loader {

// Peek version without consuming stream position.
inline uint8_t peekVersion(std::istream& fp) {
    const std::streampos pos = fp.tellg();
    uint8_t ver = 0;
    fp.read(reinterpret_cast<char*>(&ver), 1);
    if (!fp) throw std::runtime_error("Cannot peek DBF version byte");
    fp.clear();
    fp.seekg(pos);
    return ver;
}

// Read header and map to DbArea's encapsulated state.
inline void readHeader(DbArea& area, std::istream& fp) {
    const uint8_t ver = peekVersion(fp);
    area.setVersionByte(ver);
    area.setKind(detect_area_kind_from_version(ver));

    if (ver == 0x03 || ver == 0x83 || ver == 0xF5) {
        HeaderRec h{};
        fp.read(reinterpret_cast<char*>(&h), sizeof(h));
        if (!fp) throw std::runtime_error("Classic/Fox26 header read failed");
        area.setHeader(h);
        area.setVersionByte(h.version);
        area.setKind(detect_area_kind_from_version(h.version));
        return;
    }

    if (ver == 0x30 || ver == 0x31 || ver == 0x32) {
        VfpHeader vh{};
        fp.read(reinterpret_cast<char*>(&vh), sizeof(vh));
        if (!fp) throw std::runtime_error("VFP header read failed");

        area.setVersionByte(vh.version);
        area.setKind(detect_area_kind_from_version(vh.version));
        area.setLastUpdated(vh.yy, vh.mm, vh.dd);
        area.setRecordCount(static_cast<int32_t>(vh.num_recs));
        area.setDataStart(static_cast<std::uint64_t>(vh.header_size));
        area.setRecordLength(static_cast<std::uint64_t>(vh.record_size));
        return;
    }

    throw std::runtime_error("Unsupported DBF version: " + versionHex(ver));
}

// Read field descriptors until the 0x0D terminator.
inline void readFields(DbArea& area,
                       std::istream& fp,
                       std::vector<VfpFieldExtras>& extras)
{
    extras.clear();
    area.clearFields();

    const bool is_vfp = (area.versionByte() == 0x30 ||
                         area.versionByte() == 0x31 ||
                         area.versionByte() == 0x32);

    while (true) {
        const std::streampos pos = fp.tellg();

        uint8_t marker = 0;
        fp.read(reinterpret_cast<char*>(&marker), 1);
        if (!fp) {
            throw std::runtime_error("Truncated DBF header while reading fields");
        }

        if (marker == HEADER_TERM_BYTE) {
            break;
        }

        fp.clear();
        fp.seekg(pos);

        if (is_vfp) {
            VfpField vf{};
            fp.read(reinterpret_cast<char*>(&vf), sizeof(vf));
            if (!fp) {
                throw std::runtime_error("Truncated VFP field descriptor");
            }

            FieldDef fd;
            fd.name     = std::string(vf.name, strnlen(vf.name, 11));
            fd.type     = vf.type;
            fd.length   = vf.length;
            fd.decimals = vf.decimals;
            area.addField(std::move(fd));

            FieldRec fr{};
            std::memset(&fr, 0, sizeof(fr));
            const std::string& nm = area.fields().back().name;
            if (!nm.empty()) {
                const size_t copy_n = (nm.size() > 10) ? 10 : nm.size();
                std::memcpy(fr.field_name, nm.data(), copy_n);
            }
            fr.field_type         = area.fields().back().type;
            fr.field_data_address = 0;
            fr.field_length       = static_cast<std::uint8_t>(area.fields().back().length);
            fr.decimal_places     = area.fields().back().decimals;
            area.addRawField(std::move(fr));

            VfpFieldExtras ex = decode_field_flags(vf.flags);
            ex.next_autoinc  = vf.autoinc_next;
            ex.step_autoinc  = vf.autoinc_step;
            extras.push_back(std::move(ex));
        } else {
            FieldRec fr{};
            fp.read(reinterpret_cast<char*>(&fr), sizeof(fr));
            if (!fp) {
                throw std::runtime_error("Truncated classic field descriptor");
            }

            area.addRawField(fr);

            FieldDef fd;
            fd.name     = std::string(fr.field_name, strnlen(fr.field_name, 11));
            fd.type     = fr.field_type;
            fd.length   = fr.field_length;
            fd.decimals = fr.decimal_places;
            area.addField(std::move(fd));

            // X64 INHERITS THE DESCRIPTOR, so its flags byte is already in the
            // file at 18 -- which is exactly where the classic descriptor's
            // `reserved` block begins (static_assert above). Read it for the
            // flavors that carry it and leave the genuinely classic ones alone.
            if (descriptor_carries_field_flags(area.versionByte()))
                extras.push_back(decode_field_flags(fr.reserved[0]));
            else
                extras.push_back(VfpFieldExtras{});
        }
    }

    if (is_vfp) {
        fp.seekg(263, std::ios::cur);
        if (!fp) {
            throw std::runtime_error("Failed to skip VFP backlink block");
        }
    }
}

} // namespace vfp_loader

} // namespace xbase
