#pragma once
// include/cli/build_vectors_report.hpp
//
// Runtime access + reporting for the build-vector authority (AIF-044 M4).
// The compiled constexpr values (dottalk::build::*) are the truth; this exposes them
// as a runtime struct for bindings/reporting and prints ABOUT BUILD / BUILD VECTORS,
// with a short fingerprint so two binaries built with different capacities are
// distinguishable in logs.

#include "dottalk/build_vectors.hpp"

#include <cstdint>
#include <cstdio>
#include <ostream>
#include <string>

namespace dottalk::build {

struct BuildVectors {
    std::uint64_t max_rows;
    std::uint32_t max_fields;
    std::uint32_t max_areas;
    std::uint32_t legacy_max_index_slots;
    std::uint64_t x64_max_record_bytes;
    std::uint64_t x64_record_advisory_bytes;
    std::uint16_t x64_table_name_default;
    std::uint16_t x64_table_name_max;
    std::uint16_t x64_field_name_default;
    std::uint16_t x64_field_name_max;
    std::uint32_t table_buffer_max_changes;
    char          prompt_char;
};

inline const BuildVectors& build_vectors() noexcept {
    static const BuildVectors v{
        max_rows,
        static_cast<std::uint32_t>(max_fields),
        static_cast<std::uint32_t>(max_areas),
        static_cast<std::uint32_t>(legacy_max_index_slots),
        x64::max_record_bytes,
        x64::record_advisory_bytes,
        x64::table_name_default,
        x64::table_name_max,
        x64::field_name_default,
        x64::field_name_max,
        static_cast<std::uint32_t>(table_buffer::max_changes),
        ui::prompt_char_default
    };
    return v;
}

// Deterministic 8-hex-char fingerprint of the capacity set (FNV-1a over key vectors).
inline std::string build_vector_fingerprint() {
    std::uint64_t h = 1469598103934665603ull;
    const auto mix = [&](std::uint64_t x) { h ^= x; h *= 1099511628211ull; };
    const BuildVectors& v = build_vectors();
    mix(v.max_areas); mix(v.max_fields); mix(v.max_rows);
    mix(v.x64_max_record_bytes); mix(v.x64_field_name_max); mix(v.table_buffer_max_changes);
    mix(static_cast<std::uint64_t>(static_cast<unsigned char>(v.prompt_char)));
    char buf[9];
    std::snprintf(buf, sizeof(buf), "%08llx",
                  static_cast<unsigned long long>(h & 0xffffffffull));
    return std::string(buf);
}

inline void print_build_vectors(std::ostream& os) {
    const BuildVectors& v = build_vectors();
    os << "Build vectors\n"
       << "  Maximum work areas      " << v.max_areas << "\n"
       << "  Maximum fields          " << v.max_fields << "\n"
       << "  Maximum rows            " << v.max_rows << "\n"
       << "  Legacy index slots      " << v.legacy_max_index_slots << "\n"
       << "  X64 record hard limit   " << v.x64_max_record_bytes << " bytes\n"
       << "  X64 record advisory     " << v.x64_record_advisory_bytes << " bytes\n"
       << "  X64 table names         default " << v.x64_table_name_default
       << ", maximum " << v.x64_table_name_max << "\n"
       << "  X64 field names         default " << v.x64_field_name_default
       << ", maximum " << v.x64_field_name_max << "\n"
       << "  Table-buffer changes    " << v.table_buffer_max_changes << "\n"
       << "  Prompt character        " << v.prompt_char << "\n"
       << "  Fingerprint             " << build_vector_fingerprint() << "\n";
}

} // namespace dottalk::build
