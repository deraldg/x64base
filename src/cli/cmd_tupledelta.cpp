// cmd_tupledelta.cpp
//
// DotTalk++ tuple delta command skeleton.
//
// Purpose:
//   Compare two tuple streams and report INSERT / DELETE / UPDATE changes.
//
// Command surface:
//   TUPLEDELTA <baseline-stream> <current-stream>
//
// Notes:
//   - REC_ID / PRIMARY UNIQUE should be the identity key.
//   - Field-level diffing is intentionally stubbed.
//   - Stream loading is intentionally abstracted until tuple stream storage
//     format is finalized.

#include "xbase.hpp"
#include "cli/table_state.hpp"

#include <cstdint>
#include <iostream>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

namespace {

struct TupleRow {
    std::string key;                 // REC_ID / PRIMARY UNIQUE value
    std::vector<std::string> fields; // full tuple payload
};

using TupleMap = std::unordered_map<std::string, TupleRow>;

enum class DeltaKind {
    Insert,
    Delete,
    Update
};

struct TupleDelta {
    DeltaKind kind;
    std::string key;
    TupleRow before;
    TupleRow after;
};

static std::string trim(const std::string& s) {
    const auto first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) {
        return {};
    }

    const auto last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

static bool same_tuple_payload(const TupleRow& a, const TupleRow& b) {
    return a.fields == b.fields;
}

// ---------------------------------------------------------------------
// Stub: replace this when tuple stream storage is finalized.
//
// Expected future sources:
//   - named in-memory tuple stream
//   - .tup file
//   - SMARTLIST TO TUPLE <name>
//   - browser snapshot
// ---------------------------------------------------------------------
static bool load_tuple_stream(const std::string& stream_name, TupleMap& out) {
    out.clear();

    std::cerr << "TUPLEDELTA: tuple stream loader not implemented yet: "
              << stream_name << "\n";

    return false;
}

static std::vector<TupleDelta> compute_delta(
    const TupleMap& baseline,
    const TupleMap& current
) {
    std::vector<TupleDelta> deltas;

    for (const auto& [key, before_row] : baseline) {
        const auto it = current.find(key);

        if (it == current.end()) {
            TupleDelta d;
            d.kind = DeltaKind::Delete;
            d.key = key;
            d.before = before_row;
            deltas.push_back(std::move(d));
            continue;
        }

        const TupleRow& after_row = it->second;
        if (!same_tuple_payload(before_row, after_row)) {
            TupleDelta d;
            d.kind = DeltaKind::Update;
            d.key = key;
            d.before = before_row;
            d.after = after_row;
            deltas.push_back(std::move(d));
        }
    }

    for (const auto& [key, after_row] : current) {
        if (baseline.find(key) == baseline.end()) {
            TupleDelta d;
            d.kind = DeltaKind::Insert;
            d.key = key;
            d.after = after_row;
            deltas.push_back(std::move(d));
        }
    }

    return deltas;
}

static void print_delta(const TupleDelta& d) {
    switch (d.kind) {
        case DeltaKind::Insert:
            std::cout << "+ INSERT " << d.key << "\n";
            break;

        case DeltaKind::Delete:
            std::cout << "- DELETE " << d.key << "\n";
            break;

        case DeltaKind::Update:
            std::cout << "~ UPDATE " << d.key << "\n";
            break;
    }
}

} // namespace

void cmd_TUPLEDELTA(xbase::DbArea&, std::istringstream& ss) {
    std::string baseline_name;
    std::string current_name;

    ss >> baseline_name >> current_name;

    baseline_name = trim(baseline_name);
    current_name = trim(current_name);

    if (baseline_name.empty() || current_name.empty()) {
        std::cout << "Usage: TUPLEDELTA <baseline-stream> <current-stream>\n";
        return;
    }

    TupleMap baseline;
    TupleMap current;

    if (!load_tuple_stream(baseline_name, baseline)) {
        return;
    }

    if (!load_tuple_stream(current_name, current)) {
        return;
    }

    const auto deltas = compute_delta(baseline, current);

    std::cout << "TUPLEDELTA: "
              << baseline_name << " -> " << current_name << "\n";

    if (deltas.empty()) {
        std::cout << "No tuple changes.\n";
        return;
    }

    for (const auto& d : deltas) {
        print_delta(d);
    }
}