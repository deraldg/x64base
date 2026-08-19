// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/tuple_stream.hpp
#pragma once

#include <cstddef>
#include <limits>
#include <string>
#include <vector>

#include "tuple_types.hpp"

namespace dottalk {

// Minimal stream interface for Super Browser -- and, since AIF-120 R66/R67, the
// runtime contract of the UIDEF `grid` kind. A GUI grid binds this directly; it
// does not drive the SMARTBROWSER pager, which owns stdin and runs a loop.
// A one-shot command is called; a REPL is not.
class TupleStream {
public:
    virtual ~TupleStream() = default;

    virtual void top() = 0;
    virtual void bottom() = 0;

    // RECNO64: a movement is a signed 64-bit delta, not a `long`. Widening this
    // is a no-op on gcc and a real change under MSVC, which is the point.
    virtual void skip(RecordDelta n) = 0;

    // BETA-6.1 freezes "TOP/BOTTOM/SKIP/GOTO semantics for tuple iteration", and
    // this interface had no GOTO -- DbTupleStream carried goto_pos/goto_recno
    // outside it, so a second implementation was not required to provide either.
    // Positioning by record identity is part of iterating, so it belongs here.
    virtual bool goto_record(RecordNo recno) = 0;

    virtual std::vector<TupleRow> next_page(std::size_t max_rows) = 0;
    virtual std::string status_line() const = 0;

    // Capacity, reported rather than assumed. This is IIndexBackend's shape
    // (RECNO64 M4-4): the wide value is the default, a narrower backing overrides
    // it, and a caller ASKS instead of a cast truncating. "One engine API, three
    // capacities" -- a stream over a classic 32-bit table is not broken, it is
    // narrower, and it says so.
    virtual RecordNo max_record_number() const {
        return std::numeric_limits<RecordNo>::max();
    }
    bool record_number_fits(RecordNo r) const {
        return r <= max_record_number();
    }
};

} // namespace dottalk
