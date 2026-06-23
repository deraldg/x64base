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

// Phase 22B/22C boundary:
// - Read-only provider.
// - No runtime catalog writeback.
// - Compiled/static message rows remain fallback.
MessageCatalogStatus active_message_catalog_status();
std::string format_message_catalog(const std::string& locale,
                                   const std::string& symbol,
                                   const std::unordered_map<std::string, std::string>& vars = {});


// MSG-022S1 BEGIN shared routing proof lane declarations
bool message_routing_proof_enabled();
void set_message_routing_proof_enabled(bool enabled);
// MSG-022S1 END shared routing proof lane declarations
} // namespace dottalk::helpdata
