#include "locale_spine_catalog.hpp"

#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <vector>

namespace dottalk {
namespace locale_spine {

namespace {

std::string join_path(const std::string& lhs, const std::string& rhs) {
    if (lhs.empty()) {
        return rhs;
    }
    const char last = lhs[lhs.size() - 1];
    if (last == '/' || last == '\\') {
        return lhs + rhs;
    }
    return lhs + "/" + rhs;
}

bool file_exists(const std::string& path) {
    std::ifstream in(path.c_str(), std::ios::binary);
    return in.good();
}

int dbf_record_count(const std::string& path) {
    std::ifstream in(path.c_str(), std::ios::binary);
    if (!in.good()) {
        return -1;
    }

    unsigned char header[8] = {0};
    in.read(reinterpret_cast<char*>(header), 8);
    if (in.gcount() < 8) {
        return -1;
    }

    const std::uint32_t count =
        static_cast<std::uint32_t>(header[4]) |
        (static_cast<std::uint32_t>(header[5]) << 8) |
        (static_cast<std::uint32_t>(header[6]) << 16) |
        (static_cast<std::uint32_t>(header[7]) << 24);

    if (count > static_cast<std::uint32_t>(100000000)) {
        return -1;
    }

    return static_cast<int>(count);
}

std::string locale_dbf_dir(const std::string& repo_root) {
    return join_path(repo_root, "dottalkpp/data/locale");
}

std::string locale_indexes_dir(const std::string& repo_root) {
    return join_path(repo_root, "dottalkpp/data/indexes/locale");
}

std::string locale_lmdb_dir(const std::string& repo_root) {
    return join_path(repo_root, "dottalkpp/data/lmdb/locale");
}

}  // namespace

ActiveLocaleSpineStatus active_locale_spine_status(const std::string& repo_root) {
    ActiveLocaleSpineStatus status;

    status.dbf_dir = locale_dbf_dir(repo_root);
    status.indexes_dir = locale_indexes_dir(repo_root);
    status.lmdb_dir = locale_lmdb_dir(repo_root);

    const std::string system_locales_dbf = join_path(status.dbf_dir, "SYSTEM_LOCALES.dbf");
    const std::string fallback_dbf = join_path(status.dbf_dir, "SYSTEM_LOCALE_FALLBACK.dbf");

    const std::string system_locales_cdx = join_path(status.indexes_dir, "SYSTEM_LOCALES.cdx");
    const std::string fallback_cdx = join_path(status.indexes_dir, "SYSTEM_LOCALE_FALLBACK.cdx");

    const std::string system_locales_lmdb = join_path(status.lmdb_dir, "SYSTEM_LOCALES.cdx.d/data.mdb");
    const std::string fallback_lmdb = join_path(status.lmdb_dir, "SYSTEM_LOCALE_FALLBACK.cdx.d/data.mdb");

    status.dbf_present = file_exists(system_locales_dbf) && file_exists(fallback_dbf);
    status.cdx_present = file_exists(system_locales_cdx) && file_exists(fallback_cdx);
    status.lmdb_present = file_exists(system_locales_lmdb) && file_exists(fallback_lmdb);

    status.locale_rows = dbf_record_count(system_locales_dbf);
    status.fallback_rows = dbf_record_count(fallback_dbf);

    std::ostringstream detail;
    detail << "active shared locale spine "
           << "dbf=" << (status.dbf_present ? "present" : "missing")
           << "; cdx=" << (status.cdx_present ? "present" : "missing")
           << "; lmdb=" << (status.lmdb_present ? "present" : "missing")
           << "; locale_rows=" << status.locale_rows
           << "; fallback_rows=" << status.fallback_rows;
    status.detail = detail.str();

    return status;
}

bool active_locale_spine_available(const std::string& repo_root) {
    const ActiveLocaleSpineStatus status = active_locale_spine_status(repo_root);
    return status.dbf_present && status.cdx_present && status.lmdb_present &&
           status.locale_rows >= 0 && status.fallback_rows >= 0;
}

std::vector<std::string> active_locale_fallback_chain(
    const std::string& requested_locale,
    const std::string& repo_root) {
    (void)repo_root;

    std::vector<std::string> chain;
    if (!requested_locale.empty()) {
        chain.push_back(requested_locale);
    }

    if (requested_locale != "en-US") {
        chain.push_back("en-US");
    }

    return chain;
}

}  // namespace locale_spine
}  // namespace dottalk
