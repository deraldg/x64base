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
#include "xindex/attach.hpp"
#include "textio.hpp"
#include "cli/command_output.hpp"
#include "cli/order_state.hpp"
#include "cli/cmd_setpath.hpp"
#include "help/helpdata_messages.hpp"

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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::LmdbUsageText);
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
        cli::cmdout::print_prefixed_message(
            "LMDB", dottalk::helpdata::MessageId::LmdbActionNoTableOpenText,
            {{"action", sub}});
        return;
    }

    if (sub == "INFO") {
        const auto* im = xindex::manager_if_attached(db);
        if (!im || !im->hasBackend() || !im->isCdx()) {
            cli::cmdout::print_prefixed_message("LMDB INFO", dottalk::helpdata::MessageId::LmdbInfoNoneText);
            return;
        }
        cli::cmdout::print_message(dottalk::helpdata::MessageId::LmdbInfoTitleText);
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::LmdbInfoContainerLineText,
            {{"path", im->containerPath()}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::LmdbInfoTagLineText,
            {{"tag", (im->activeTag().empty() ? "(none)" : im->activeTag())}});
        return;
    }

    if (sub == "OPEN") {
        std::string tok;
        iss >> tok;
        tok = trim_copy(tok);
        if (tok.empty()) {
            cli::cmdout::print_prefixed_message("LMDB OPEN", dottalk::helpdata::MessageId::LmdbOpenMissingPathText);
            return;
        }

        std::string err;
        const std::string cdx_path = resolve_container_token(tok);
        if (cdx_path.empty()) {
            cli::cmdout::print_prefixed_message("LMDB OPEN", dottalk::helpdata::MessageId::LmdbOpenInvalidPathText);
            return;
        }

        if (!xindex::ensure_manager(db).openCdx(cdx_path, {}, &err)) {
            cli::cmdout::print_prefixed_message(
                "LMDB", dottalk::helpdata::MessageId::LmdbOpenFailedText,
                {{"detail", (err.empty() ? "openCdx failed" : err)}});
            return;
        }

        // Keep legacy orderstate coherent until it's removed.
        orderstate::setOrder(db, cdx_path);

        cli::cmdout::print_prefixed_message(
            "LMDB", dottalk::helpdata::MessageId::LmdbOpenText,
            {{"path", cdx_path}});
        return;
    }

    if (sub == "USE") {
        std::string tag;
        iss >> tag;
        tag = upper_copy(trim_copy(tag));
        if (tag.empty()) {
            cli::cmdout::print_prefixed_message("LMDB USE", dottalk::helpdata::MessageId::LmdbUseMissingTagText);
            return;
        }

        std::string err;
        if (!xindex::ensure_manager(db).setTag(tag, &err)) {
            cli::cmdout::print_prefixed_message(
                "LMDB", dottalk::helpdata::MessageId::LmdbUseFailedText,
                {{"detail", (err.empty() ? "setTag failed" : err)}});
            return;
        }

        orderstate::setActiveTag(db, tag);

        cli::cmdout::print_prefixed_message(
            "LMDB", dottalk::helpdata::MessageId::LmdbUseText,
            {{"tag", tag}});
        return;
    }

    if (sub == "SEEK") {
        std::string key;
        std::getline(iss, key);
        key = trim_copy(key);
        if (key.empty()) {
            cli::cmdout::print_prefixed_message("LMDB SEEK", dottalk::helpdata::MessageId::LmdbSeekMissingKeyText);
            return;
        }

        std::uint64_t recno = 0;
        std::string err;
        if (!xindex::ensure_manager(db).lmdbSeekUserKey(key, recno, err)) {
            cli::cmdout::print_prefixed_message(
                "LMDB", dottalk::helpdata::MessageId::LmdbSeekFailedText,
                {{"detail", (err.empty() ? "not found" : err)}});
            return;
        }

        cli::cmdout::print_prefixed_message(
            "LMDB", dottalk::helpdata::MessageId::LmdbSeekRecnoText,
            {{"recno", std::to_string(recno)}});
        return;
    }

    if (sub == "DUMP") {
        int maxn = 25;
        if (iss >> maxn) {
            if (maxn < 0) maxn = 0;
            if (maxn > 100000) maxn = 100000;
        }

        const auto* im = xindex::manager_if_attached(db);
        if (!im || !im->hasBackend() || !im->isCdx()) {
            cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbDumpNoneText);
            return;
        }
        if (im->activeTag().empty()) {
            cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbDumpNoTagSelectedText);
            return;
        }

        auto cur = xindex::ensure_manager(db).scan(xindex::Key{}, xindex::Key{});
        if (!cur) {
            cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbDumpCursorOpenFailedText);
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

        cli::cmdout::print_prefixed_message(
            "LMDB", dottalk::helpdata::MessageId::LmdbDumpPrintedText,
            {{"count", std::to_string(printed)}});
        return;
    }

    if (sub == "SCAN") {
        std::string low, high;
        iss >> low >> high;
        low = upper_copy(trim_copy(low));
        high = upper_copy(trim_copy(high));

        if (low.empty() || high.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::LmdbScanUsageText);
            return;
        }

        const auto* im = xindex::manager_if_attached(db);
        if (!im || !im->hasBackend() || !im->isCdx()) {
            cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbScanNoneText);
            return;
        }
        if (im->activeTag().empty()) {
            cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbScanNoTagSelectedText);
            return;
        }

        xindex::Key lo(low.begin(), low.end());
        xindex::Key hi(high.begin(), high.end());

        auto cur = xindex::ensure_manager(db).scan(lo, hi);
        if (!cur) {
            cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbScanCursorOpenFailedText);
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

        cli::cmdout::print_prefixed_message(
            "LMDB", dottalk::helpdata::MessageId::LmdbScanShownText,
            {{"count", std::to_string(shown)}});
        return;
    }

    if (sub == "CLOSE") {
        xindex::ensure_manager(db).close();
        try { orderstate::clearOrder(db); } catch (...) {}
        cli::cmdout::print_prefixed_message("LMDB", dottalk::helpdata::MessageId::LmdbCloseText);
        return;
    }

    lmdb_help();
}
