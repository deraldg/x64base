#pragma once
// DD096Z-D2ZK DDICT call-site bridge helpers.
// These helpers are intentionally small wrappers around the D2ZI resolver.

#include <string>

namespace dottalk::datadict {

std::string ddict_bridge_x64_owner_token(const std::string& token);
std::string ddict_bridge_legacy_owner_token(const std::string& token);
bool ddict_bridge_token_is_catalog_surface(const std::string& token);

} // namespace dottalk::datadict
