// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// File: src/cli/unique_registry.cpp
// Purpose: Runtime registry for SET UNIQUE-style field tracking during
//          validation and mutation flows.
// Boundary: This is process-local shell state, not persistent schema
//           metadata; storage/backfill policy belongs elsewhere.

#include "cli/unique_registry.hpp"
#include "xbase.hpp"

#include <mutex>
#include <cctype>
#include <unordered_map>
#include <unordered_set>

namespace {
static std::unordered_map<std::string, std::unordered_set<std::string>>& unique_store() {
    static std::unordered_map<std::string, std::unordered_set<std::string>> store;
    return store;
}

static std::mutex& unique_mutex() {
    static std::mutex mu;
    return mu;
}

static std::string upcopy(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}
} // anonymous

namespace unique_reg {

std::string current_alias_or_area_name(const xbase::DbArea& A) {
    // Phase 2 (AIF-074 P1.1): bucket by table identity so per-table
    // declarations do not collide and match the dtschema KEY <table> identity
    // (the header's own Phase-1 note asked for this). Falls back to the
    // Phase-1 single bucket when no table identity is available.
    try {
        const std::string n = upcopy(A.name());
        if (!n.empty()) return n;
    } catch (...) {}
    return std::string("AREA");
}

static std::unordered_map<std::string, std::string>& primary_store() {
    static std::unordered_map<std::string, std::string> store;
    return store;
}

void set_unique_field(xbase::DbArea& A, const std::string& field_name, bool on) {
    const std::string bucket = current_alias_or_area_name(A);
    std::lock_guard<std::mutex> lk(unique_mutex());
    auto& set = unique_store()[bucket];
    const auto key = upcopy(field_name);
    if (on) {
        set.insert(key);
    } else {
        set.erase(key);
        // Dropping uniqueness on the primary field drops the primary too.
        auto pit = primary_store().find(bucket);
        if (pit != primary_store().end() && pit->second == key) {
            primary_store().erase(pit);
        }
    }
}

void set_primary_field(xbase::DbArea& A, const std::string& field_name) {
    const std::string bucket = current_alias_or_area_name(A);
    const auto key = upcopy(field_name);
    std::lock_guard<std::mutex> lk(unique_mutex());
    unique_store()[bucket].insert(key);   // PRIMARY implies UNIQUE
    primary_store()[bucket] = key;        // one primary per table; last set wins
}

std::string primary_field(const xbase::DbArea& A) {
    // THE FILE IS THE AUTHORITY (AIF-156). The x64 header is self-describing --
    // it already carries the table's logical name, its field names and the
    // authoritative field lengths -- so the key designation lives there too,
    // in X64FieldMetaEntry.flags, and it is read back at open.
    //
    // Before this, the answer came only from the map below, which this file's
    // own boundary comment calls "process-local shell state, not persistent
    // schema metadata". That meant SET UNIQUE FIELD <f> PRIMARY was forgotten
    // at exit: reopen the table in a fresh session without redeclaring, and a
    // REPLACE overwrote the key in silence on the very build where the
    // regression arms read green. A refusal standing on a fact that evaporates
    // is not an enforced key.
    try {
        const int f = A.primaryFieldIndex();
        if (f >= 1 && f <= static_cast<int>(A.fields().size())) {
            return upcopy(A.fields()[static_cast<std::size_t>(f - 1)].name);
        }
    } catch (...) {
        // fall through to the cache
    }

    // The map is now a CACHE, not the authority, and it is consulted only when
    // the file designates nothing. It survives because it still answers for
    // in-session state on a table that could not be stamped; it must never
    // again be the only place an answer lives.
    const std::string bucket = current_alias_or_area_name(A);
    std::lock_guard<std::mutex> lk(unique_mutex());
    const auto it = primary_store().find(bucket);
    return it == primary_store().end() ? std::string() : it->second;
}

bool is_unique_field(xbase::DbArea& A, const std::string& field_name) {
    const std::string bucket = current_alias_or_area_name(A);
    std::lock_guard<std::mutex> lk(unique_mutex());
    const auto it = unique_store().find(bucket);
    if (it == unique_store().end()) return false;
    return it->second.count(upcopy(field_name)) != 0;
}

std::vector<std::string> list_unique_fields(xbase::DbArea& A) {
    const std::string bucket = current_alias_or_area_name(A);
    std::vector<std::string> out;
    std::lock_guard<std::mutex> lk(unique_mutex());
    const auto it = unique_store().find(bucket);
    if (it == unique_store().end()) return out;
    out.reserve(it->second.size());
    for (const auto& f : it->second) out.push_back(f);
    return out;
}

const std::unordered_map<std::string, std::unordered_set<std::string>>& snapshot() {
    return unique_store();
}

} // namespace unique_reg



