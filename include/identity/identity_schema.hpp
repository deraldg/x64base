#pragma once
// include/identity/identity_schema.hpp
// DBF schema for the identity / RBAC catalog (AIF-045 2b-ii, APH-5 self-hosting).
//
// PURE DATA. Declares the nine SYS* identity tables that persist the nine
// InMemoryIdentityStore vectors, one table per vector. No database access here —
// the writer/loader (identity_dbf_store.*) consumes these specs.
//
// Storage convention (DOTTALKPP_DBF_PATH_POLICY): identity tables are SYSTEM
// catalogs, so they live under data/metadata/identity/ alongside the other SYS*
// runtime catalogs — not in the data/dbf fixture dirs, not in a profile home.
//
// Round-trip invariant (Contract v1 §Invariant 5): the authoritative 64-bit IDs
// AND the portable string keys are both persisted, so a x64base -> reload ->
// x64base pass preserves identity exactly. 64-bit IDs are stored as N(20,0)
// decimal text (DBF 'I' is only int32); optional IDs use 0 = unset, matching the
// StrongId convention. Enums persist as small N codes, bools as 'L'.

#include "xbase/dbf_create.hpp"

#include <string>
#include <vector>

namespace dottalk::identity::schema {

using xbase::dbf_create::FieldSpec;

// data/metadata/identity/ subdirectory (joined onto the resolved metadata root).
inline constexpr const char* kIdentityDir = "identity";

struct Table {
    const char*            name;    // logical table name -> <name>.dbf
    std::vector<FieldSpec> fields;
};

// Field-width conventions kept in one place.
namespace w {
inline constexpr std::uint32_t ID   = 20;  // 64-bit id / timestamp as decimal text
inline constexpr std::uint32_t KEY  = 64;  // portable string key (user.derald, ...)
inline constexpr std::uint32_t NAME = 48;
inline constexpr std::uint32_t CLS  = 24;  // resource_class / action / kind
inline constexpr std::uint32_t TEXT = 160; // reason / description
} // namespace w

inline FieldSpec N(const char* n, std::uint32_t len) { return FieldSpec{n, 'N', len, 0, ""}; }
inline FieldSpec C(const char* n, std::uint32_t len) { return FieldSpec{n, 'C', len, 0, ""}; }
inline FieldSpec L(const char* n)                    { return FieldSpec{n, 'L', 1,  0, ""}; }

// ---- one function per table (names <= 10 chars, classic-browsable) ----

inline Table sysuser() {
    return {"SYSUSER", {
        N("ID", w::ID), C("UKEY", w::KEY), C("LOGIN", 32), C("DISPLAY", w::KEY),
        N("AUTHKIND", 2), C("CRED", w::KEY), N("STATUS", 2), C("PROFHOME", 32),
        N("VFROM", w::ID), N("VTHRU", w::ID), N("ROWVER", w::ID),
    }};
}

inline Table sysmember() {
    return {"SYSMEMBER", {
        N("ID", w::ID), N("USERID", w::ID), C("MKEY", w::KEY), N("KIND", 2),
        N("DEFROLE", w::ID), N("DEFPSET", w::ID), N("STATUS", 2),
        N("VFROM", w::ID), N("VTHRU", w::ID), N("ROWVER", w::ID),
    }};
}

inline Table sysrole() {
    return {"SYSROLE", {
        N("ID", w::ID), C("RKEY", w::NAME), C("RNAME", w::NAME),
        C("RKIND", w::CLS), C("DESCR", 128), N("STATUS", 2),
    }};
}

inline Table sysperm() {
    return {"SYSPERM", {
        N("ID", w::ID), C("PKEY", w::NAME), C("RESCLASS", w::CLS), C("PACTION", w::CLS),
        N("RISK", 2), L("REQAPPR"), N("STATUS", 2),
    }};
}

inline Table sysroleperm() {
    return {"SYSROLEPERM", {
        N("ROLEID", w::ID), N("PERMID", w::ID),
    }};
}

inline Table sysmemrole() {
    return {"SYSMEMROLE", {
        N("MEMBERID", w::ID), N("ROLEID", w::ID), N("ORGSCOPE", w::ID), N("WORKSCOPE", w::ID),
    }};
}

inline Table sysoverride() {
    return {"SYSOVERRIDE", {
        N("MEMBERID", w::ID), N("PERMID", w::ID), N("EFFECT", 2),
        N("ORGSCOPE", w::ID), N("WORKSCOPE", w::ID),
    }};
}

inline Table sysassign() {
    return {"SYSASSIGN", {
        N("ID", w::ID), N("MEMBERID", w::ID), N("ORGUNIT", w::ID), N("WORK", w::ID),
        N("ROLE", w::ID), N("PSET", w::ID), N("REPORTSTO", w::ID), C("AKIND", w::CLS),
        N("STATUS", 2), N("VFROM", w::ID), N("VTHRU", w::ID), N("ROWVER", w::ID),
    }};
}

inline Table sysgrant() {
    return {"SYSGRANT", {
        N("ID", w::ID), N("REQBY", w::ID), N("GRANTTO", w::ID), N("ROLEASN", w::ID),
        N("WORK", w::ID), C("RESSCOPE", w::NAME), C("ACTSCOPE", w::NAME), N("RISK", 2),
        N("GRANTAT", w::ID), N("EXPAT", w::ID), N("STATUS", 2),
        C("REASON", w::TEXT), C("SRCREPORT", w::NAME),
    }};
}

// All nine tables. Order is load-safe (referenced catalogs before crosswalks).
inline std::vector<Table> all_tables() {
    return {
        sysuser(), sysmember(), sysrole(), sysperm(),
        sysroleperm(), sysmemrole(), sysoverride(), sysassign(), sysgrant(),
    };
}

} // namespace dottalk::identity::schema
