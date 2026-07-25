// @dottalk.file v1
// path: include/bbs/bbs_schema.hpp
// subsystem: bbs
// layer: header
// owns: 
// project: project.x64base.runtime
// status: supported
// provenance: prov://include/bbs/bbs_schema.hpp

// bbs_schema.hpp — DBF table definitions for the AI-BBS / pseudo-chat board (M1).
//
// Mirrors include/identity/identity_schema.hpp conventions:
//   - table/field names <= 10 chars, classic-browsable: 10 is the classic DBF physical
//     descriptor limit (11-byte name slot). x64 defaults logical names to 128 via X64M
//     metadata, but physical names are kept <=10 for compatibility with external xBase
//     systems (ODBC / dBASE / FoxPro readers) that lack that flexibility. Full logical
//     names remain available through X64M; plan_x64_unique_fallback keeps the two in sync.
//   - 64-bit ids stored as N(20,0) decimal text (DBF 'I' is int32 only); 0 = unset
//   - enums as small N codes; bools as 'L'
//   - stored under data/metadata/bbs/ (its OWN dir — not folded into identity all_tables())
//
// M1 scope: local board only. No server, no egress, no crypto dependency.
#pragma once

#include <string>
#include <vector>
#include "xbase/dbf_create.hpp"   // xbase::dbf_create::FieldSpec

namespace dottalk::bbs::schema {

using xbase::dbf_create::FieldSpec;

// data/metadata/bbs/ subdirectory (joined onto the resolved metadata root).
inline constexpr const char* kBbsDir = "bbs";

struct Table {
    const char*            name;    // logical table name -> <name>.dbf
    std::vector<FieldSpec> fields;
};

// Field-width conventions (kept parallel to identity::schema::w).
namespace w {
inline constexpr std::uint32_t ID    = 20;   // 64-bit id / epoch stamp as decimal text
inline constexpr std::uint32_t KEY   = 64;   // board.governance, run id, perm/role key
inline constexpr std::uint32_t NAME  = 48;
inline constexpr std::uint32_t SUBJ  = 160;  // thread subject / short text
inline constexpr std::uint32_t BODY  = 240;  // M1 post body (C field; memo upgrade deferred)
} // namespace w

inline FieldSpec N(const char* n, std::uint32_t len) { return FieldSpec{n, 'N', len, 0, ""}; }
inline FieldSpec C(const char* n, std::uint32_t len) { return FieldSpec{n, 'C', len, 0, ""}; }
inline FieldSpec L(const char* n)                    { return FieldSpec{n, 'L', 1,  0, ""}; }

// Boards / rooms. KIND: 0=governance 1=chat 2=notice. STATUS: 0=active 1=archived.
inline Table sysboard() {
    return {"SYSBOARD", {
        N("ID", w::ID), C("BKEY", w::KEY), C("NAME", w::NAME), N("KIND", 2),
        C("POSTPERM", w::KEY), N("STATUS", 2),
        N("VFROM", w::ID), N("VTHRU", w::ID), N("ROWVER", w::ID),
    }};
}

// Threads. STATE: 0=open 1=answered 2=closed. OPENEDBY = member id (0=unknown).
inline Table systhread() {
    return {"SYSTHREAD", {
        N("ID", w::ID), N("BOARDID", w::ID), C("SUBJECT", w::SUBJ),
        N("OPENEDBY", w::ID), N("OPENAT", w::ID), N("STATE", 2), N("LASTPOST", w::ID),
    }};
}

// Posts. KIND: 0=post 1=reply 2=agent_prompt 3=agent_reply 4=system.
// STATUS: 0=posted 1=redacted. REFGRANT = SYSGRANT id (0=none). RUNID = ai_runs ref (may be empty).
inline Table syspost() {
    return {"SYSPOST", {
        N("ID", w::ID), N("BOARDID", w::ID), N("THREADID", w::ID),
        N("AUTHORID", w::ID), N("AUTHKIND", 2), N("KIND", 2),
        C("BODY", w::BODY), N("REFGRANT", w::ID), C("RUNID", w::NAME),
        N("POSTAT", w::ID), N("STATUS", 2),
    }};
}

// Load-safe order: boards, threads, then posts.
inline std::vector<Table> all_tables() {
    return { sysboard(), systhread(), syspost() };
}

} // namespace dottalk::bbs::schema
