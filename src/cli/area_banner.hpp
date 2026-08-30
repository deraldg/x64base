// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/area_banner.hpp
// DotTalk++ -- AREA banner formatter (declaration)

#pragma once
#include <string>
#include <cstdint>


// Must pull in IndexKind and via_phrase()
#include "order_path_resolver.hpp"  // defines dottalk::order::IndexKind and helpers

namespace dottalk { namespace order {

// Facts the banner needs (populate from DbArea + order_state)
struct AreaFacts {
    // Required
    std::string file_rel;     // e.g., "dbf/students.dbf"
    uint32_t    recs {0};
    uint32_t    recno {0};

    // Order info
    //
    // AIF-148 WARNING TO WHOEVER WIRES THIS UP.  This formatter has NO CALLER
    // -- nothing in the tree constructs an AreaFacts -- so has_order is a
    // contract nobody has filled yet, and order_phrase() below is correct or
    // wrong depending entirely on how the first caller fills it.
    //
    // FILL IT FROM orderstate::isNaturalOrder(), INVERTED.  Do NOT fill it
    // from orderstate::hasOrder(), whose name matches this field's name and
    // whose meaning does not: hasOrder() answers IS A CONTAINER ATTACHED, and
    // WORKSPACE OPEN attaches a .cdx to every table while selecting no tag.
    // Filling this field from the identically-named function is the exact
    // mistake AIF-148 was, and the matching names are the whole trap.
    //
    //     f.has_order = !orderstate::isNaturalOrder(area);   // correct
    //     f.has_order =  orderstate::hasOrder(area);         // the defect
    bool        has_order {false};
    std::string tag;          // "LNAME" if CNX; optional for INX/IDX
    bool        asc {true};   // ASC/DESC

    // Container info (if any)
    dottalk::order::IndexKind kind { dottalk::order::IndexKind::NONE };
    std::string index_rel;    // pretty path relative to data_root (or empty)
};

struct AreaBanner {
    std::string line1;  // "Current area: N"
    std::string line2;  // "  File: <file>  Recs: <n>  Recno: <n>"
    std::string line3;  // "  Order: <...>" or "  Order: NATURAL"
    std::string line4;  // "  Active tag  : ..." (empty for NATURAL)
};

// Build the user-facing order phrase (e.g., "LNAME (ASC) via CNX [indexes/students.cnx]")
std::string order_phrase(const AreaFacts& f);

// Format all AREA lines in a stable way
AreaBanner format_banner(int area_number, const AreaFacts& f);

}} // namespace dottalk::order
