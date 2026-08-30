// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/order_banner.hpp
// DotTalk++ -- AREA banner formatter -- header-only
//
// Wire-up: build an AreaFacts struct from your DbArea + order_state and
// print the returned strings in AREA (or anywhere you show state).
//
// READ THIS BEFORE INCLUDING THIS HEADER.  It is a DUPLICATE of
// area_banner.hpp + area_banner.cpp: same namespace, same AreaFacts, same
// order_phrase() and format_banner(), same bodies.  Neither copy has a caller
// today -- nothing in the tree constructs an AreaFacts -- but area_banner.cpp
// is compiled into the binary by the source glob, so ITS definitions are in
// every link.
//
// MEASURED 2026-08-30, not assumed: linking a TU that includes THIS header
// against area_banner.o SUCCEEDS and prints no diagnostic.  These definitions
// are inline and land as WEAK symbols; area_banner.cpp's land as STRONG, and
// the linker silently keeps the strong ones (`nm -C`: W here, T there).  So
// including this header does not get you this header's code -- IT GETS YOU
// area_banner.cpp's.  Identical bodies make that invisible right now.  It
// stops being invisible the moment someone edits one file and not the other:
// the edit is discarded at link time with nothing said.  If you fix a bug
// here, fix it in area_banner.cpp or your fix does not run.
//
// The honest resolution is to delete one of the two, which is an owner's call
// and has not been made.  AIF-148 residue pass, 2026-08-30.

#pragma once
#include <string>
#include "order_path_resolver.hpp" // for IndexKind and via_phrase()

namespace dottalk { namespace order {

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
    std::string tag;          // e.g., "LNAME" for CNX; empty for pure INX-ASC
    bool        asc {true};   // ASC/DESC flag

    // Container info (if any)
    IndexKind   kind { IndexKind::NONE };
    std::string index_rel;    // pretty path relative to data_root (or empty)
};

struct AreaBanner {
    std::string line1;  // "Current area: N"
    std::string line2;  // "  File: <file>  Recs: <n>  Recno: <n>"
    std::string line3;  // "  Order: <...>" (or "NATURAL")
    std::string line4;  // "  Active tag  : <name| (none)>" (omitted for NATURAL)
};

inline std::string order_phrase(const AreaFacts& f){
    if (!f.has_order || f.kind==IndexKind::NONE)
        return "NATURAL";
    // CNX with tag name
    if (f.kind==IndexKind::CNX) {
        const std::string dir = f.asc ? "ASC" : "DESC";
        return f.tag + " (" + dir + ") " + via_phrase(f.kind, f.index_rel);
    }
    // INX/IDX (legacy) -- show direction and optional tag
    const std::string dir = f.asc ? "ASCEND" : "DESCEND";
    if (!f.tag.empty()) {
        return dir + " " + via_phrase(f.kind, f.index_rel) + "  Tag: " + f.tag;
    }
    return dir + " " + via_phrase(f.kind, f.index_rel);
}

inline AreaBanner format_banner(int area_number, const AreaFacts& f){
    AreaBanner b;
    b.line1 = "Current area: " + std::to_string(area_number);
    b.line2 = "  File: " + f.file_rel + "  Recs: " + std::to_string(f.recs) + "  Recno: " + std::to_string(f.recno);
    const auto ord = order_phrase(f);
    b.line3 = "  Order: " + ord;
    if (ord=="NATURAL") {
        b.line4.clear(); // omit for natural
    } else {
        b.line4 = "  Active tag  : " + (f.tag.empty() ? std::string("(none)") : f.tag);
    }
    return b;
}

}} // namespace dottalk::order
