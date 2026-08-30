// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

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
    std::uint32_t max_relation_depth;
    std::uint32_t max_workspace_depth;
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
        static_cast<std::uint32_t>(max_relation_depth),
        static_cast<std::uint32_t>(max_workspace_depth),
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
    // ADDED 2026-08-30 with the depth vectors. They are capacity vectors, so they
    // belong in the capacity fingerprint -- and adding them CHANGES IT, which is
    // the point: a build whose traversal caps differ is a different build.
    //
    // AT THE DEFAULTS (24 / 32): 3b276bee -> 9e8c58e6. The second value is
    // OBSERVED, from BUILDVECTORS on the built binary. The first is derived from
    // the same model that reproduces the second exactly, which is what makes it
    // trustworthy rather than merely arithmetic.
    //
    // THE PREDICTION FOR THIS LINE WAS WRONG ONCE AND THE ERROR IS RECORDED
    // RATHER THAN QUIETLY REPLACED: it said 45f7a2c6, computed by appending the
    // two new mixes AFTER the prompt_char mix. THE CODE APPENDS THEM BEFORE IT.
    // FNV-1a is order-dependent, so a model of a hash that gets the ORDER wrong
    // agrees with the code on every value and on nothing else -- and the only
    // thing that could catch it was running the binary. Whoever changes this
    // function next: the mix ORDER is part of the contract, and a fingerprint
    // predicted from source is a prediction until BUILDVECTORS says otherwise.
    //
    // These two are mixed here, immediately after table_buffer_max_changes and
    // BEFORE prompt_char, so the existing mixes keep their relative order.
    mix(v.max_relation_depth); mix(v.max_workspace_depth);
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
       << "  Relation depth cap      " << v.max_relation_depth << "\n"
       << "  Workspace depth cap     " << v.max_workspace_depth << "\n"
       << "  Prompt character        " << v.prompt_char << "\n"
       << "  Fingerprint             " << build_vector_fingerprint() << "\n";
}

} // namespace dottalk::build
