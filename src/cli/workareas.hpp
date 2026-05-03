#pragma once

#include <cstddef>
#include <memory>
#include <string>
#include <vector>
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

    std::string label() const {
        return name();
    }

    std::string file_name() const {
        return name();
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
        auto* eng = shell_engine();
        for (std::size_t i = 0; i < areas_.size(); ++i) {
            areas_[i] =
                std::make_unique<WorkArea>(i, &eng->area(static_cast<int>(i)));
        }
    }

    std::size_t count() const { return areas_.size(); }

    WorkArea* at(std::size_t i) {
        if (i >= areas_.size()) return nullptr;
        return areas_[i].get();
    }

    const WorkArea* at(std::size_t i) const {
        if (i >= areas_.size()) return nullptr;
        return areas_[i].get();
    }

    WorkArea* current() {
        auto* eng = shell_engine();
        return at(static_cast<std::size_t>(eng->currentArea()));
    }

    const WorkArea* current() const {
        auto* eng = shell_engine();
        return at(static_cast<std::size_t>(eng->currentArea()));
    }

    std::size_t current_slot() const {
        auto* eng = shell_engine();
        return static_cast<std::size_t>(eng->currentArea());
    }

    void print(std::ostream& os) const {
        os << "Slot Cur Name\n";

        const std::size_t cur = current_slot();

        for (std::size_t i = 0; i < areas_.size(); ++i) {
            const auto* wa = areas_[i].get();
            if (!wa || !wa->isOpen()) continue;

            os << i << " "
               << (i == cur ? "*" : " ")
               << " "
               << wa->label() << "\n";
        }
    }

private:
    std::vector<std::unique_ptr<WorkArea>> areas_;
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

inline std::string occupied_desc() {
    std::vector<std::size_t> slots;

    for (auto* wa : all()) {
        if (wa && wa->is_open()) {
            slots.push_back(wa->slot());
        }
    }

    if (slots.empty()) return "{}";

    std::string out = "{";
    out += std::to_string(slots.front());
    if (slots.size() > 1) {
        out += "..";
        out += std::to_string(slots.back());
    }
    out += "}";
    return out;
}

inline void print(std::ostream& os) {
    global().print(os);
}

} // namespace workareas