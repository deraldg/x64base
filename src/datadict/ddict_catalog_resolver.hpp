#pragma once
// DD096Z-D2ZI guarded resolver source patch.
// Compatibility bridge for legacy compact DD* names and x64 DATA_DICTIONARY_* names.

#include <string>
#include <vector>

namespace dottalk::datadict {

struct DDictCatalogBinding {
    const char* legacy_name;
    const char* x64_name;
    const char* family;
};

const std::vector<DDictCatalogBinding>& ddict_catalog_bindings();

std::string ddict_resolve_to_x64_catalog_name(const std::string& token);
std::string ddict_resolve_to_legacy_catalog_name(const std::string& token);
bool ddict_is_known_catalog_name(const std::string& token);

} // namespace dottalk::datadict
