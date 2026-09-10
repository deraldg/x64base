// @dottalk.file v1
// subsystem: cli
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// File: src/cli/workareas.hpp
// Purpose: Lightweight wrappers around engine-owned work areas for shell and
//          runtime access.
// Boundary: Ownership stays in xbase::XBaseEngine; this header exposes
//           navigation and lookup conveniences without redefining lifecycle.

#pragma once

#include <cstddef>
#include <memory>
#include <string>
#include <vector>
// <iostream> IS NO LONGER USED BY THIS HEADER and is kept deliberately.
// WorkAreaSet::print() and workareas::print() were the only consumers and were
// removed 2026-09-11 (see the note on the class). This header is included by
// hundreds of translation units, an unknown number of which have been getting
// <iostream> transitively; dropping it is a separate change with its own blast
// radius, not a tidy-up to ride along with a behaviour fix.
#include <iostream>

#include "xbase.hpp"

namespace workareas {

// Engine bridge
extern xbase::XBaseEngine* shell_engine();

// --------------------------------------------------
// STUBS (future expansion points)
// --------------------------------------------------
class MemoManager {};
class OrderContext {};

// --------------------------------------------------
// WorkArea (wraps engine-owned DbArea)
// --------------------------------------------------
class WorkArea {
public:
    WorkArea(std::size_t slot0, xbase::DbArea* db)
        : slot0_(slot0), db_(db) {}

    xbase::DbArea& db() { return *db_; }
    const xbase::DbArea& db() const { return *db_; }

    xbase::DbArea* get() { return db_; }
    const xbase::DbArea* get() const { return db_; }

    xbase::DbArea* operator->() { return db_; }
    const xbase::DbArea* operator->() const { return db_; }

    bool isOpen() const {
        return db_ && db_->isOpen();
    }

    bool is_open() const {
        return isOpen();
    }

    std::string name() const {
        return isOpen() ? db_->name() : "";
    }

    // THE ALIAS. What this INSTANCE answers to -- DbArea::name() is
    // _logical_name, which USE may have derived as <stem>2 when the stem was
    // already held. Correct here, and deliberately NOT the same string as
    // file_name() below.
    std::string label() const {
        return name();
    }

    // THE FILE. Absolute path, because that is the only field that can tell
    // two open areas apart once two workspaces hold different files sharing a
    // basename -- measured 2026-09-10, twelve such pairs in one session across
    // an x64 and an x32 workspace.
    //
    // UNTIL 2026-09-11 THIS RETURNED name(), THE ALIAS. Its only consumers are
    // in cmd_wsreport.cpp, one of which prints it under the literal label
    // `FILE`, so the report answered "which file" with a name that is not a
    // file and that both same-named areas share. A caller wanting the short
    // form takes the basename of this; a caller wanting the alias calls
    // label(). They must not collapse back into one function.
    std::string file_name() const {
        return isOpen() ? db_->filename() : std::string();
    }

    std::size_t slot() const { return slot0_; }

private:
    std::size_t slot0_;
    xbase::DbArea* db_;
};

// --------------------------------------------------
// WorkAreaSet (mirrors engine slots)
// --------------------------------------------------
class WorkAreaSet {
public:
    WorkAreaSet()
        : areas_(xbase::MAX_AREA)
    {
        rebind_if_needed();
    }

    std::size_t count() const { return areas_.size(); }

    WorkArea* at(std::size_t i) {
        rebind_if_needed();
        if (i >= areas_.size()) return nullptr;
        return areas_[i].get();
    }

    const WorkArea* at(std::size_t i) const {
        rebind_if_needed();
        if (i >= areas_.size()) return nullptr;
        return areas_[i].get();
    }

    WorkArea* current() {
        rebind_if_needed();
        auto* eng = shell_engine();
        if (!eng) return nullptr;
        return at(static_cast<std::size_t>(eng->currentArea()));
    }

    const WorkArea* current() const {
        rebind_if_needed();
        auto* eng = shell_engine();
        if (!eng) return nullptr;
        return at(static_cast<std::size_t>(eng->currentArea()));
    }

    std::size_t current_slot() const {
        rebind_if_needed();
        auto* eng = shell_engine();
        if (!eng) return 0;
        return static_cast<std::size_t>(eng->currentArea());
    }

    // print() LIVED HERE AND HAD ZERO CALLERS. Removed 2026-09-11.
    //
    // It emitted `Slot Cur Name` over every open slot with a `*` on the engine
    // current area. Nothing in the tree ever called it -- not WSREPORT, not
    // AREA, not STATUS -- and the only surviving mentions of that format were
    // COMMENTS citing it as what this class does. A dead formatter that a
    // header describes as canonical is worse than no formatter: it teaches a
    // shape nobody emits, and the next reader builds against it.
    //
    // It is not replaced here. The report it looked like it should feed wants
    // a WORKSPACE COLUMN, and this class is flat by design -- no workspace
    // dimension, one engine, MAX_AREA slots. That join is published once, by
    // cli::workdesk::observe(), and belongs to the caller.

private:
    void rebind_if_needed() const {
        auto* eng = shell_engine();
        if (!eng) return;
        if (bound_engine_ == eng && areas_bound_) return;

        auto* self = const_cast<WorkAreaSet*>(this);
        for (std::size_t i = 0; i < self->areas_.size(); ++i) {
            if (auto* area = eng->areaPtr(static_cast<int>(i))) {
                self->areas_[i] = std::make_unique<WorkArea>(i, area);
            } else {
                self->areas_[i].reset();
            }
        }
        self->bound_engine_ = eng;
        self->areas_bound_ = true;
    }

    std::vector<std::unique_ptr<WorkArea>> areas_;
    xbase::XBaseEngine* bound_engine_{nullptr};
    bool areas_bound_{false};
};

// --------------------------------------------------
// GLOBAL ACCESS
// --------------------------------------------------
inline WorkAreaSet& global() {
    static WorkAreaSet g;
    return g;
}

inline std::size_t count() {
    return global().count();
}

inline WorkArea* at(std::size_t i) {
    return global().at(i);
}

inline const WorkArea* at_const(std::size_t i) {
    return global().at(i);
}

inline WorkArea* current() {
    return global().current();
}

inline const WorkArea* current_const() {
    return global().current();
}

inline std::size_t current_slot() {
    return global().current_slot();
}

// ---- DbArea bridge ----
inline xbase::DbArea* db(std::size_t i) {
    auto* wa = at(i);
    return wa ? wa->get() : nullptr;
}

inline const xbase::DbArea* db_const(std::size_t i) {
    auto* wa = at(i);
    return wa ? wa->get() : nullptr;
}

inline xbase::DbArea* current_db() {
    auto* wa = current();
    return wa ? wa->get() : nullptr;
}

inline const xbase::DbArea* current_db_const() {
    auto* wa = current_const();
    return wa ? wa->get() : nullptr;
}

inline const char* name(std::size_t i) {
    static thread_local std::string buf;
    auto* wa = at(i);
    buf = wa ? wa->label() : "";
    return buf.c_str();
}

inline std::vector<WorkArea*> all() {
    std::vector<WorkArea*> v;
    auto& g = global();
    for (std::size_t i = 0; i < g.count(); ++i) {
        v.push_back(g.at(i));
    }
    return v;
}

inline std::size_t open_count() {
    std::size_t n = 0;
    for (auto* wa : all()) {
        if (wa && wa->is_open()) ++n;
    }
    return n;
}

// WHICH SLOTS ARE OPEN, rendered as runs. `{}`, `{5}`, `{0..16}`,
// `{0..19,50..54}`.
//
// UNTIL 2026-09-11 THIS PRINTED `{front..back}` AND WAS A RANGE OVER A SET.
// Open slots {0,3} rendered as `{0..3}` -- four areas claimed, two open. It
// needed no second workspace to be wrong: `USE <t> IN 3` with area 0 already
// open produces exactly that, which is the arrangement USE_ARGS U_T4 sets up
// on purpose. Two workspaces only made it routine.
//
// THE CONTRACT WAS NEVER LOST, ONLY THE CODE THAT MET IT. The four-line
// example above is copied from src/workspace/workarea_utils.hpp:17-21, which
// still DECLARES this function; its definition moved here and left the
// documentation behind (src/workspace/workarea_utils.cpp:15 records the move).
// The implementation that inherited the name did not inherit the spec.
//
// Eight call sites in four verbs -- STATUS, GPS, AREA, WSREPORT. Nothing in
// the .dts corpus or cmd_regression.cpp asserts the token, checked before
// changing the rendering.
//
// STILL FLAT, DELIBERATELY. These are ENGINE slots with no workspace
// dimension, so `{0..12,13..25}` says two runs and not two workspaces. The
// caller that wants ownership asks cli::workdesk::observe(). What is fixed
// here is the arithmetic, not the model.
inline std::string occupied_desc() {
    std::vector<std::size_t> slots;

    for (auto* wa : all()) {
        if (wa && wa->is_open()) {
            slots.push_back(wa->slot());
        }
    }

    if (slots.empty()) return "{}";

    // all() walks 0..count()-1, so `slots` is ascending and a run is a plain
    // forward scan. Do not sort here -- a sort would hide a future change that
    // made all() unordered, which is the ordering trap observe() already had
    // to answer for handles().
    std::string out = "{";
    for (std::size_t i = 0; i < slots.size(); ) {
        std::size_t j = i;
        while (j + 1 < slots.size() && slots[j + 1] == slots[j] + 1) ++j;

        if (i != 0) out += ",";
        out += std::to_string(slots[i]);
        if (j > i) {
            out += "..";
            out += std::to_string(slots[j]);
        }
        i = j + 1;
    }
    out += "}";
    return out;
}

} // namespace workareas
