// DD096Z-D2ZK DDICT call-site bridge helpers.

#include "ddict_callsite_bridge.hpp"
#include "ddict_catalog_resolver.hpp"

namespace dottalk::datadict {

std::string ddict_bridge_x64_owner_token(const std::string& token) {
    return ddict_resolve_to_x64_catalog_name(token);
}

std::string ddict_bridge_legacy_owner_token(const std::string& token) {
    return ddict_resolve_to_legacy_catalog_name(token);
}

bool ddict_bridge_token_is_catalog_surface(const std::string& token) {
    return ddict_is_known_catalog_name(token);
}

} // namespace dottalk::datadict
