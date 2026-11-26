// @dottalk.file v1
// subsystem: xbase
// layer: header
// owns: x64 memo slot kind predicate
// project: project.x64base.runtime
// lane: x64-memo-slot-predicate-one-owner
// owner: member.derald
// status: supported

#pragma once
// THE ONE OWNER of "is this field an x64 memo slot, and which kind?".
//
// TWO CONVENTIONS LIVE ON ONE FORMAT, and until this header existed, ten copies
// of one predicate each answered privately:
//
//   M(8)  -- X64_MEMO_FIELD_LEN     -- a raw little-endian uint64 OBJECT ID.
//            The decoder reads the eight bytes and hands callers
//            std::to_string(object_id), or "" when the id is 0; the sidecar
//            store resolves that id to a payload.
//   M(16) -- X64_MEMO_REF_TOKEN_LEN -- a 16-hex MemoRef TOKEN, written and read
//            like a character field. cmd_workspace.cpp mints these for the
//            WORKSPACES catalog's SNAPSHOT column. NO object id is involved and
//            no store is consulted, so a __fldbak copy of such a table carries
//            tokens that resolve against nothing.
//
// WHY ONE OWNER RATHER THAN TEN AGREEING COPIES. This predicate decides three
// different things in three different layers: what a field READ returns
// (loadFieldsFromBuffer, decodeFieldFromBuffer), whether a consumer may treat
// that string as an object id, and whether a field WRITE lays down eight raw
// bytes or text. A disagreement across that boundary is silent data corruption,
// not untidy code. The ten copies agreed only because the copy-paste was
// faithful, and nothing kept them agreeing.
//
// ASK THE WIDTH, NOT ONLY THE TYPE. cmd_use.cpp's attach path tests the type
// alone, so the engine opens a real MemoStore for an M(16) table and every
// consumer then refuses to read it. One inconsistency, not two designs.
//
// R149. tools/staging/check_memo_slot_predicate.py fails staging if a second
// definition of this shape appears anywhere under include/ or src/.

#include <cstdint>
#include <string>

// SELF-SUFFICIENT, DELIBERATELY. xbase.hpp carries FieldDef, DbArea and the
// memo width constants; DBF_VERSION_64 lives in xbase_64.hpp. The first build
// of this header compiled in every TU that happened to include xbase_64.hpp
// FIRST and failed in src/cli/expr/rhs_eval.cpp, which does not include it at
// all -- a header that depends on its includer's include order is a trap that
// fires on whichever file is edited next, not on the one that introduced it.
#include "xbase.hpp"
#include "xbase_64.hpp"

namespace xbase {

enum class X64MemoSlotKind {
    None,          // not an x64 memo field at all (legacy flavour, or not type M)
    ObjectId8,     // M(8)  -- raw little-endian uint64 object id
    RefToken16,    // M(16) -- 16-hex MemoRef token, character-like
    UnknownWidth,  // type M on an x64 table at a width NO convention claims
};

// THE PREDICATE. `is_x64` is the caller's already-computed flavour test, so the
// decoder's hot loops pay for it once per record rather than once per field.
inline X64MemoSlotKind x64_memo_slot_kind(const FieldDef& f, bool is_x64) noexcept
{
    if (!is_x64) return X64MemoSlotKind::None;
    if (f.type != 'M' && f.type != 'm') return X64MemoSlotKind::None;

    if (f.length == X64_MEMO_FIELD_LEN)     return X64MemoSlotKind::ObjectId8;
    if (f.length == X64_MEMO_REF_TOKEN_LEN) return X64MemoSlotKind::RefToken16;

    // UNKNOWN IS NOT NONE. A memo field at an unclaimed width is a thing this
    // engine must REFUSE to decode, which is a different answer from "that is
    // not a memo field". Collapsing the two is what let PACK run on a table it
    // could not read.
    return X64MemoSlotKind::UnknownWidth;
}

inline X64MemoSlotKind x64_memo_slot_kind(const DbArea& area, int field1)
{
    if (field1 < 1 || field1 > area.fieldCount()) return X64MemoSlotKind::None;

    const bool is_x64 = (area.versionByte() == DBF_VERSION_64);
    return x64_memo_slot_kind(area.fields()[static_cast<std::size_t>(field1 - 1)], is_x64);
}

// BEHAVIOUR-PRESERVING NAME for the question the consumers have always asked.
// An object-id slot is the only kind that resolves to a payload, so
// `is_x64_memo_field` has always meant ObjectId8 specifically.
inline bool is_x64_memo_field(const DbArea& area, int field1)
{
    return x64_memo_slot_kind(area, field1) == X64MemoSlotKind::ObjectId8;
}

inline bool is_x64_memo_field(const FieldDef& f, bool is_x64) noexcept
{
    return x64_memo_slot_kind(f, is_x64) == X64MemoSlotKind::ObjectId8;
}

// A memo field on an x64 table that the OBJECT-ID scanner cannot decode: the
// token convention, or a width nothing claims. This is what PACK and MEMO GC
// refuse on; they were spelling it `type == 'M' && length != 8` inline.
inline bool is_undecodable_x64_memo_field(const DbArea& area, int field1)
{
    const X64MemoSlotKind k = x64_memo_slot_kind(area, field1);
    return k == X64MemoSlotKind::RefToken16 || k == X64MemoSlotKind::UnknownWidth;
}

inline bool is_undecodable_x64_memo_field(const FieldDef& f, bool is_x64) noexcept
{
    const X64MemoSlotKind k = x64_memo_slot_kind(f, is_x64);
    return k == X64MemoSlotKind::RefToken16 || k == X64MemoSlotKind::UnknownWidth;
}

// THE ONE PARSER for an object-id slot's text form.
//
// MEASURED 2026-10-20, and worth writing down because it looks like a hole: the
// eight copies this replaces had THREE different bodies -- this one, one that
// swallowed the parse failure, and one in the help layer that TRIMMED first.
// None of the differences was reachable. Both read paths that feed this
// (DbArea::get via loadFieldsFromBuffer, and DbArea::decodeFieldFromBuffer)
// normalise an object-id slot to std::to_string(object_id) or "", and every
// call site guards with is_x64_memo_field first. So the only inputs possible
// here are "" or a pure decimal: no sign, no padding, no base ambiguity.
//
// DO NOT "FIX" THIS BY ADDING A TRIM and believe a hole was closed. If a padded
// value ever reaches here, the decoder changed and THAT is the defect.
inline std::uint64_t parse_u64_or_zero(const std::string& s, bool& ok) noexcept
{
    ok = true;

    if (s.empty()) return 0;

    try {
        std::size_t used = 0;
        const unsigned long long v = std::stoull(s, &used, 10);
        if (used != s.size()) {
            ok = false;
            return 0;
        }
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        ok = false;
        return 0;
    }
}

inline std::uint64_t parse_u64_or_zero(const std::string& s) noexcept
{
    bool ok = true;
    return parse_u64_or_zero(s, ok);
}

}  // namespace xbase
