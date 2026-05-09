// File: src/cli/cmd_lmdb.cpp
//
// LMDB command (per-area, no global LMDB env).
//
// Design:
//   DbArea -> IndexManager -> CdxBackend -> MDB_env*
//
// This command is intentionally a thin wrapper over DbArea::indexManager().
// It does not touch LMDB_UTIL or any shared singleton state.
//
// @dottalk.usage v1
// owner: DOT|LMDB
// command: LMDB
// category: index
// status: developer
// noargs: usage
// effect: mixed
// mutates: index-backend order-state cursor
// usage-access: LMDB USAGE
// summary:
//   Inspect and control the per-area LMDB backed CDX index backend through the
//   current DbArea IndexManager.
//
// usage:
//   LMDB USAGE
//   LMDB INFO
//   LMDB OPEN <container.cdx>
//   LMDB OPEN <envdir.cdx.d>
//   LMDB OPEN <stem>
//   LMDB USE <tag>
//   LMDB SEEK <key>
//   LMDB DUMP
//   LMDB DUMP <max>
//   LMDB SCAN <low> <high>
//   LMDB CLOSE
//
// notes:
//   LMDB is a thin wrapper over the current area IndexManager and CDX backend.
//   LMDB does not use LMDB_UTIL or any shared global LMDB environment.
//   Bare stems are resolved through the INDEXES path slot.
//   OPEN attaches the CDX container and updates legacy order state.
//   USE selects an active tag and updates legacy active-tag state.
//   SEEK searches the selected tag and reports the matching record number.
//   DUMP and SCAN inspect the selected tag.
//   CLOSE closes the current area index manager and clears order state.
//   LMDB mutates index/order session state but not table records.
//
// risk:
//   opens_lmdb_backend: LMDB OPEN
//   closes_lmdb_backend: LMDB CLOSE
//   mutates_order_state: OPEN USE CLOSE
//   reads_index_data: INFO SEEK DUMP SCAN
//   mutates_table_data: no
//   global_lmdb_state: no
//
// related:
//   CDX
//   CNX
//   SET INDEX
//   SET ORDER
//   LMDBDUMP
//   LMDB_UTIL
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "textio.hpp"
#include "cli/order_state.hpp"
#include "cli/cmd_setpath.hpp"

namespace fs = std::filesystem;

namespace {


static constexpr const char* DT_USAGE_LMDB = R"DTUSAGE(
@dottalk.usage v1
owner: DOT|LMDB
command: LMDB
category: index
status: developer
summary: Per-area LMDB/CDX backend inspection and control command.
usage:
  LMDB command (per-area):
  LMDB INFO
  LMDB OPEN <container.cdx>
  LMDB OPEN <envdir.cdx.d>
  LMDB OPEN <stem>
  LMDB USE <TAG>
  LMDB SEEK <key>
  LMDB DUMP [<max>]
  LMDB SCAN <low> <high>
  LMDB CLOSE
notes:
  LMDB is a thin wrapper over the current area IndexManager/CDX backend.
  Bare stems are resolved through the INDEXES path slot.
  Runtime status and error output is intentionally separate from this usage contract.
related:
  SET INDEX
  SET ORDER
  CDX
  CNX
)DTUSAGE";

inline std::string trim_copy(const std::string& s) { return textio::trim(s); }

inline std::string upper_copy(std::string s) {
    for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

inline bool ends_with_ci(const std::string& s, const char* suffix) {
    const std::string suf(suffix);
    if (s.size() < suf.size()) return false;
    for (size_t i = 0; i < suf.size(); ++i) {
        const char a = static_cast<char>(std::tolower(static_cast<unsigned char>(s[s.size() - suf.size() + i])));
        const char b = static_cast<char>(std::tolower(static_cast<unsigned char>(suf[i])));
        if (a != b) return false;
    }
    return true;
}

inline bool has_path_sep(const std::string& s) {
    return s.find('/') != std::string::npos || s.find('\\') != std::string::npos;
}

inline bool looks_absolute(const std::string& s) {
    if (s.size() >= 2 && std::isalpha(static_cast<unsigned char>(s[0])) && s[1] == ':') return true;
    if (!s.empty() && (s[0] == '/' || s[0] == '\\')) return true;
    return false;
}

static std::string container_from_envdir(const std::string& env_dir) {
    // ".../STUDENTS.cdx.d" -> ".../STUDENTS.cdx"
    if (ends_with_ci(env_dir, ".cdx.d") && env_dir.size() >= 2) {
        return env_dir.substr(0, env_dir.size() - 2);
    }
    // ".../STUDENTS.cdx" -> itself
    return env_dir;
}

static std::string resolve_container_token(const std::string& token) {
    // Accept:
    //   - container.cdx
    //   - envdir.cdx.d
    //   - stem (students)
    //   - relative paths like indexes\students.cdx.d
    // Uses INDEXES slot when token is a bare stem/container name without separators.
    const fs::path idx = dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES);

    std::string t = trim_copy(token);
    if (t.empty()) return {};

    // envdir -> container. Keep this helper wired in because it is also
    // the canonical readable conversion for diagnostics/reporting:
    //   .../STUDENTS.cdx.d -> .../STUDENTS.cdx
    if (ends_with_ci(t, ".cdx.d")) t = container_from_envdir(t);

    // bare stem or file
    if (!has_path_sep(t) && !looks_absolute(t)) {
        if (ends_with_ci(t, ".cdx")) return (idx / t).string();
        return (idx / (upper_copy(t) + ".cdx")).string();
    }

    // path-like token: accept as given (relative to CWD is fine)
    if (!ends_with_ci(t, ".cdx") && !ends_with_ci(t, ".cdx.d")) {
        // If a directory path was passed, treat it as "<dir>/<UPPER(stem)>.cdx"
        // but we keep this conservative: append ".cdx" if it has no extension.
        fs::path p(t);
        if (p.extension().empty()) p += ".cdx";
        return p.string();
    }

    return t;
}

static void lmdb_help() {
    std::cout
        << "Usage:\n"
        << "  LMDB USAGE\n"
        << "  LMDB INFO\n"
        << "  LMDB OPEN <container.cdx>\n"
        << "  LMDB OPEN <envdir.cdx.d>\n"
        << "  LMDB OPEN <stem>\n"
        << "  LMDB USE <tag>\n"
        << "  LMDB SEEK <key>\n"
        << "  LMDB DUMP\n"
        << "  LMDB DUMP <max>\n"
        << "  LMDB SCAN <low> <high>\n"
        << "  LMDB CLOSE\n"
        << "Notes:\n"
        << "  - LMDB is per-area and uses the current DbArea IndexManager/CDX backend.\n"
        << "  - Bare stems resolve through the INDEXES path slot.\n"
        << "  - LMDB_UTIL is deprecated and disabled.\n";
}

static std::string key_bytes_to_text(const xindex::Key& kb) {
    std::string s;
    s.reserve(kb.size());
    for (auto b : kb) {
        const char c = static_cast<char>(b);
        if (c == '\0') break;
        s.push_back(c);
    }
    while (!s.empty() && (s.back() == ' ' || s.back() == '\0')) s.pop_back();
    return s;
}

} // namespace

void cmd_LMDB(xbase::DbArea& db, std::istringstream& iss) {
    std::string sub;
    iss >> sub;
    sub = upper_copy(sub);

    if (sub.empty() || sub == "USAGE" || sub == "HELP" || sub == "?") {
        lmdb_help();
        return;
    }

    if (!db.isOpen() && sub != "INFO" && sub != "CLOSE") {
        std::cout << "* LMDB " << sub << ": no table open in current area\n";
        return;
    }

    if (sub == "INFO") {
        const auto* im = db.indexManagerPtr();
        if (!im || !im->hasBackend() || !im->isCdx()) {
            std::cout << "* LMDB INFO: (none)\n";
            return;
        }
        std::cout << "* LMDB INFO\n";
        std::cout << "  container: " << im->containerPath() << "\n";
        std::cout << "  tag      : " << (im->activeTag().empty() ? "(none)" : im->activeTag()) << "\n";
        return;
    }

    if (sub == "OPEN") {
        std::string tok;
        iss >> tok;
        tok = trim_copy(tok);
        if (tok.empty()) {
            std::cout << "* LMDB OPEN: missing path\n";
            return;
        }

        std::string err;
        const std::string cdx_path = resolve_container_token(tok);
        if (cdx_path.empty()) {
            std::cout << "* LMDB OPEN: invalid path\n";
            return;
        }

        if (!db.indexManager().openCdx(cdx_path, {}, &err)) {
            std::cout << "* LMDB OPEN failed: " << (err.empty() ? "openCdx failed" : err) << "\n";
            return;
        }

        // Keep legacy orderstate coherent until it's removed.
        orderstate::setOrder(db, cdx_path);

        std::cout << "* LMDB OPEN: " << cdx_path << "\n";
        return;
    }

    if (sub == "USE") {
        std::string tag;
        iss >> tag;
        tag = upper_copy(trim_copy(tag));
        if (tag.empty()) {
            std::cout << "* LMDB USE: missing TAG\n";
            return;
        }

        std::string err;
        if (!db.indexManager().setTag(tag, &err)) {
            std::cout << "* LMDB USE failed: " << (err.empty() ? "setTag failed" : err) << "\n";
            return;
        }

        orderstate::setActiveTag(db, tag);

        std::cout << "* LMDB USE: " << tag << "\n";
        return;
    }

    if (sub == "SEEK") {
        std::string key;
        std::getline(iss, key);
        key = trim_copy(key);
        if (key.empty()) {
            std::cout << "* LMDB SEEK: missing key\n";
            return;
        }

        std::uint32_t recno = 0;
        std::string err;
        if (!db.indexManager().lmdbSeekUserKey(key, recno, err)) {
            std::cout << "* LMDB SEEK failed: " << (err.empty() ? "not found" : err) << "\n";
            return;
        }

        std::cout << "* LMDB SEEK: recno=" << recno << "\n";
        return;
    }

    if (sub == "DUMP") {
        int maxn = 25;
        if (iss >> maxn) {
            if (maxn < 0) maxn = 0;
            if (maxn > 100000) maxn = 100000;
        }

        const auto* im = db.indexManagerPtr();
        if (!im || !im->hasBackend() || !im->isCdx()) {
            std::cout << "* LMDB DUMP: (none)\n";
            return;
        }
        if (im->activeTag().empty()) {
            std::cout << "* LMDB DUMP: no TAG selected. Try: LMDB USE <TAG>\n";
            return;
        }

        auto cur = db.indexManager().scan(xindex::Key{}, xindex::Key{});
        if (!cur) {
            std::cout << "* LMDB DUMP: cursor open failed\n";
            return;
        }

        int printed = 0;
        xindex::Key k;
        xindex::RecNo r;

        if (cur->first(k, r)) {
            do {
                std::cout << key_bytes_to_text(k) << " -> " << static_cast<std::uint32_t>(r) << "\n";
                ++printed;
                if (maxn > 0 && printed >= maxn) break;
            } while (cur->next(k, r));
        }

        std::cout << "* LMDB DUMP: printed " << printed << "\n";
        return;
    }

    if (sub == "SCAN") {
        std::string low, high;
        iss >> low >> high;
        low = upper_copy(trim_copy(low));
        high = upper_copy(trim_copy(high));

        if (low.empty() || high.empty()) {
            std::cout << "* LMDB SCAN: usage: LMDB SCAN <low> <high>\n";
            return;
        }

        const auto* im = db.indexManagerPtr();
        if (!im || !im->hasBackend() || !im->isCdx()) {
            std::cout << "* LMDB SCAN: (none)\n";
            return;
        }
        if (im->activeTag().empty()) {
            std::cout << "* LMDB SCAN: no TAG selected. Try: LMDB USE <TAG>\n";
            return;
        }

        xindex::Key lo(low.begin(), low.end());
        xindex::Key hi(high.begin(), high.end());

        auto cur = db.indexManager().scan(lo, hi);
        if (!cur) {
            std::cout << "* LMDB SCAN: cursor open failed\n";
            return;
        }

        int shown = 0;
        xindex::Key k;
        xindex::RecNo r;

        if (cur->first(k, r)) {
            do {
                std::cout << key_bytes_to_text(k) << " -> " << static_cast<std::uint32_t>(r) << "\n";
                ++shown;
                if (shown >= 200) break; // safety
            } while (cur->next(k, r));
        }

        std::cout << "* LMDB SCAN: shown " << shown << "\n";
        return;
    }

    if (sub == "CLOSE") {
        db.indexManager().close();
        try { orderstate::clearOrder(db); } catch (...) {}
        std::cout << "* LMDB CLOSE\n";
        return;
    }

    lmdb_help();
}
