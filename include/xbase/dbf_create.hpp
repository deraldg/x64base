// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

#include <cstdint>
#include <string>
#include <vector>

namespace xbase::dbf_create {

enum class Flavor {
    MSDOS,
    FOX26,
    VFP,
    X64
};

struct FieldSpec {
    // Authoritative/logical field name.
    // For x64, this is the name written to X64M metadata when available.
    std::string  name;
    char         type{};
    std::uint32_t len{};
    std::uint8_t dec{};

    // Optional physical DBF/VFP descriptor token.
    // Empty means "derive from name using legacy truncation."
    //
    // x64 callers use this to preserve long authoritative names while writing
    // unique 10-byte fallback descriptor tokens.
    std::string  descriptor_name;
};

std::string flavor_name(Flavor flavor);

bool supports_type_now(char code, Flavor flavor) noexcept;

bool create_dbf(const std::string& path,
                const std::vector<FieldSpec>& fields,
                Flavor flavor,
                std::string& err);

// Identity-explicit overload (AIF-110). For X64, `tableName` seeds the X64M
// authoritative table identity INSTEAD of the path stem. Required whenever the
// create path and the table's final identity differ -- the founding case is
// FIELDMGR APPEND's temp-file rewrite, where the stem-derived default stamped
// "STUDENTS.__fldtmp" into the renamed file's metadata (hex-verified
// 2026-08-12). Empty tableName falls back to the path stem; non-X64 flavors
// ignore it (their formats carry no name authority block).
bool create_dbf(const std::string& path,
                const std::string& tableName,
                const std::vector<FieldSpec>& fields,
                Flavor flavor,
                std::string& err);

} // namespace xbase::dbf_create
