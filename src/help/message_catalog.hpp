// ============================================================================
// File: src/help/message_catalog.hpp
// Purpose: Runtime Messaging catalog provider boundary.
// Phase: MSG-022B candidate; apply only via guarded Phase 22C.
// ============================================================================

#pragma once

#include <string>
#include <unordered_map>
#include <vector>

namespace dottalk::helpdata {

enum class MessageCatalogMode {
    CompiledFallback,
    ActiveDbf,
    Auto
};

struct MessageCatalogStatus {
    MessageCatalogMode mode = MessageCatalogMode::CompiledFallback;
    bool active_catalog_present = false;
    bool active_catalog_loaded = false;
    int message_count = 0;
    int text_row_count = 0;
    std::string active_dbf_dir;
    std::string active_indexes_dir;
    std::string active_lmdb_dir;
    std::string detail;
};

struct MessageCatalogSeedReport {
    bool success = false;
    bool check_only = true;
    bool active_catalog_present = false;
    bool active_catalog_loaded = false;
    bool seed_complete = false;
    int expected_message_rows = 0;
    int expected_text_rows = 0;
    int present_message_rows = 0;
    int present_text_rows = 0;
    int message_rows_before = 0;
    int message_rows_after = 0;
    int text_rows_before = 0;
    int text_rows_after = 0;
    int message_rows_inserted = 0;
    int message_rows_updated = 0;
    int message_rows_unchanged = 0;
    int text_rows_inserted = 0;
    int text_rows_updated = 0;
    int text_rows_unchanged = 0;
    std::string active_dbf_dir;
    std::string active_indexes_dir;
    std::string active_lmdb_dir;
    std::string detail;
    std::vector<std::string> rebuilt_containers;
    std::vector<std::string> errors;
};

// Phase 22B/22C boundary:
// - Read-only provider.
// - No runtime catalog writeback.
// - Compiled/static message rows remain fallback.
MessageCatalogStatus active_message_catalog_status();
std::string format_message_catalog(const std::string& locale,
                                   const std::string& symbol,
                                   const std::unordered_map<std::string, std::string>& vars = {});
MessageCatalogSeedReport check_priority_a_seed();
MessageCatalogSeedReport apply_priority_a_seed();
MessageCatalogSeedReport check_priority_b_seed();
MessageCatalogSeedReport apply_priority_b_seed();
MessageCatalogSeedReport check_priority_c_seed();
MessageCatalogSeedReport apply_priority_c_seed();


// MSG-022S1 BEGIN shared routing proof lane declarations
bool message_routing_proof_enabled();
void set_message_routing_proof_enabled(bool enabled);
// MSG-022S1 END shared routing proof lane declarations
} // namespace dottalk::helpdata
