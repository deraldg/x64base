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

std::string current_alias_or_area_name(xbase::DbArea& A) {
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

std::string primary_field(xbase::DbArea& A) {
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



