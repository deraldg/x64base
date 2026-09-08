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

// THE FILE FIRST, THEN THE CACHE -- the shape primary_field() has used since
// AIF-156, arriving here one defect late.
//
// AIF-156 moved the primary key designation into the x64 header and taught
// primary_field() to read it back. THIS FUNCTION WAS NOT FOLLOWED, and the two
// halves of the primary key contract then disagreed across a restart:
// field_constraints.cpp reaches primary_field() and refuses the write, while
// append_support.cpp reaches this and mints nothing. A FRESH PROCESS ENFORCED A
// KEY IT WOULD NOT MINT.
//
// MEASURED 2026-09-08 on build Sep 07 2026 18:56:28, PKDURABLE run 2 -- a
// separate process that issues NO declaration, opening a table whose PRIMARY
// flag is stamped in its header:
//
//   PKD_G5_undeclared_SID_minted_by_name:.T.            <- minted by name match
//   PKD_T3_stamped_key_minted_without_a_declaration:.F. <- declared, stamped, BLANK
//   PKD_T4_the_key_could_be_filled_by_hand:.F.          <- and cannot be filled
//
// One row, one APPEND, two numeric fields. The eight graded markers of that
// same run were green, so enforcement demonstrably read the stamp in that same
// process. The row was born with a blank primary key that neither the engine
// nor the user can complete, because the funnel refuses every write to a
// primary key. It has not bitten in the field only because every table in this
// tree with a generated key names it SID, and the undeclared name match covers
// for the missing generation.
//
// THREE OTHER CONSUMERS WERE BLIND FOR THE SAME REASON, and this is why the fix
// belongs here rather than in the generator:
//   - cmd_validate_unique.cpp -- VALIDATE UNIQUE with no FIELD said "no unique
//     fields declared for this table" on a table carrying a stamped key, so the
//     one column that must not hold duplicates was the one column never checked.
//   - cmd_setunique.cpp -- SET UNIQUE with no arguments listed nothing.
//   - cmd_workspace.cpp -- a saved workspace omitted the KEY line entirely, so
//     a restore could not carry the designation either.
//
// THE HEADER IS READ OUTSIDE THE MUTEX, ON PURPOSE. primaryFieldIndex() can
// touch the file, and holding the registry lock across file access invites a
// lock order this file cannot see. The stamped name is resolved first, the
// cache is read under the lock, and the merge happens after.
//
// THE STAMP IS ADDED, NOT SUBSTITUTED. A table can carry a stamped primary AND
// in-session SET UNIQUE FIELD <f> ON declarations that live only in the map;
// both are real and both belong in the answer. The cache stays authoritative
// for what only it knows, and it stops being the ONLY place an answer lives.
std::vector<std::string> list_unique_fields(xbase::DbArea& A) {
    std::string stamped;
    try {
        const int f = A.primaryFieldIndex();
        if (f >= 1 && f <= static_cast<int>(A.fields().size())) {
            stamped = upcopy(A.fields()[static_cast<std::size_t>(f - 1)].name);
        }
    } catch (...) {
        // A table that cannot answer -- VFP, classic, closed -- stamps nothing,
        // and the cache below answers alone exactly as it did before.
    }

    std::vector<std::string> out;

    {
        const std::string bucket = current_alias_or_area_name(A);
        std::lock_guard<std::mutex> lk(unique_mutex());
        const auto it = unique_store().find(bucket);
        if (it != unique_store().end()) {
            out.reserve(it->second.size() + 1);
            for (const auto& f : it->second) out.push_back(f);
        }
    }

    // set_primary_field() also inserts into the cache ("PRIMARY implies
    // UNIQUE"), so in the DECLARING process the stamped name is already here.
    // Without this check that process would see the field twice and mint it
    // twice -- and the planner in append_support.cpp deduplicates by field
    // index precisely because it must not depend on this one being right.
    if (!stamped.empty()) {
        bool already = false;
        for (const auto& f : out) {
            if (f == stamped) { already = true; break; }
        }
        if (!already) out.push_back(stamped);
    }

    return out;
}

const std::unordered_map<std::string, std::unordered_set<std::string>>& snapshot() {
    return unique_store();
}

} // namespace unique_reg



