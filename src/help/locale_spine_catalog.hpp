#pragma once

#include <string>
#include <vector>

namespace dottalk {
namespace locale_spine {

struct ActiveLocaleSpineStatus {
    bool dbf_present = false;
    bool cdx_present = false;
    bool lmdb_present = false;
    int locale_rows = -1;
    int fallback_rows = -1;
    std::string dbf_dir;
    std::string indexes_dir;
    std::string lmdb_dir;
    std::string detail;
};

ActiveLocaleSpineStatus active_locale_spine_status(const std::string& repo_root = std::string());

bool active_locale_spine_available(const std::string& repo_root = std::string());

std::vector<std::string> active_locale_fallback_chain(
    const std::string& requested_locale,
    const std::string& repo_root = std::string());

}  // namespace locale_spine
}  // namespace dottalk
