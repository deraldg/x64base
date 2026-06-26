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

std::string current_alias_or_area_name(xbase::DbArea& /*A*/) {
    // Phase 1: single-bucket. Replace with alias/areaNo later when convenient.
    return std::string("AREA");
}

void set_unique_field(xbase::DbArea& A, const std::string& field_name, bool on) {
    const std::string bucket = current_alias_or_area_name(A);
    std::lock_guard<std::mutex> lk(unique_mutex());
    auto& set = unique_store()[bucket];
    const auto key = upcopy(field_name);
    if (on) set.insert(key);
    else    set.erase(key);
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



