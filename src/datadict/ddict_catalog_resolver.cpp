// DD096Z-D2ZI guarded resolver source patch.
// Compatibility bridge for legacy compact DD* names and x64 DATA_DICTIONARY_* names.

#include "ddict_catalog_resolver.hpp"

#include <algorithm>
#include <cctype>

namespace dottalk::datadict {

namespace {
std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(), [](unsigned char c) {
        return static_cast<char>(std::toupper(c));
    });
    return s;
}
}

const std::vector<DDictCatalogBinding>& ddict_catalog_bindings() {
    static const std::vector<DDictCatalogBinding> kBindings = {
        {"DDRUN",    "DATA_DICTIONARY_RUNS",              "run records"},
        {"DDOBJECT", "DATA_DICTIONARY_OBJECTS",           "catalog objects"},
        {"DDATTR",   "DATA_DICTIONARY_OBJECT_ATTRIBUTES", "object attributes"},
        {"DDEDGE",   "DATA_DICTIONARY_RELATION_EDGES",    "relation edges"},
        {"DDEVID",   "DATA_DICTIONARY_EVIDENCE_RECORDS",  "evidence records"},
        {"DDGATE",   "DATA_DICTIONARY_GATE_RECORDS",      "gate records"},
    };
    return kBindings;
}

std::string ddict_resolve_to_x64_catalog_name(const std::string& token) {
    const std::string u = upper_copy(token);
    if (u == "DDICT") {
        return "DATA_DICTIONARY_OBJECTS";
    }
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return b.x64_name;
        }
    }
    return token;
}

std::string ddict_resolve_to_legacy_catalog_name(const std::string& token) {
    const std::string u = upper_copy(token);
    if (u == "DDICT") {
        return "DDOBJECT";
    }
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return b.legacy_name;
        }
    }
    return token;
}

bool ddict_is_known_catalog_name(const std::string& token) {
    const std::string u = upper_copy(token);
    if (u == "DDICT") {
        return true;
    }
    for (const auto& b : ddict_catalog_bindings()) {
        if (u == b.legacy_name || u == b.x64_name) {
            return true;
        }
    }
    return false;
}

} // namespace dottalk::datadict
