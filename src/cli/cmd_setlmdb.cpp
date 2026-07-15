// src/cli/cmd_setlmdb.cpp
//
// SETLMDB: select LMDB-backed ordering (container/tag/asc/desc) per area.
//
// Ownership rule enforced here:
//   DbArea -> IndexManager -> CdxBackend -> LMDB env
// No global LMDB singleton is touched from this command.
//
// Behavior:
//   SETLMDB 0                      -> clear ordering (physical)
//   SETLMDB                        -> report state
//   SETLMDB <stem|cdx|envdir>      -> default tag selection
//   SETLMDB <...> <TAG> [--asc|--desc]
//
// @dottalk.usage v1
// owner: DOT|SET LMDB
// command: SET LMDB
// category: index
// status: developer
// noargs: report
// effect: configure
// mutates: order-state index-backend
// usage-access: SET LMDB USAGE
// summary:
//   Select LMDB-backed CDX ordering per area without touching global LMDB state.
//
// usage:
//   SET LMDB
//   SET LMDB USAGE
//   SET LMDB 0
//   SET LMDB <stem>
//   SET LMDB <container.cdx>
//   SET LMDB <envdir.cdx.d>
//   SET LMDB <stem> <tag>
//   SET LMDB <stem> <tag> --asc
//   SET LMDB <stem> <tag> --desc
//   SETLMDB
//   SETLMDB USAGE
//   SETLMDB 0
//   SETLMDB <stem> <tag>
//
// notes:
//   SET LMDB with no arguments reports current LMDB/order state.
//   SET LMDB 0 clears ordering and closes the current index manager.
//   Bare stems resolve through the INDEXES path slot as <stem>.cdx.
//   .cdx.d environment directory tokens normalize back to the public .cdx container.
//   Default tag is LNAME when no tag is supplied.
//   This command opens the per-area CDX backend and never uses a global LMDB singleton.
//
// risk:
//   mutates_order_state: yes
//   mutates_index_backend: yes
//   mutates_table_data: no
//
// related:
//   LMDB
//   SET INDEX
//   SET ORDER
//   CDX
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"

#include "textio.hpp"
#include "cli/command_output.hpp"
#include "cli/cmd_setpath.hpp"
#include "cli/order_state.hpp"

namespace {

using MessageId = dottalk::helpdata::MessageId;

static inline std::string trim_copy(const std::string& s) { return textio::trim(s); }

static inline std::string upper_copy(std::string s) {
    for (char& c : s) {
        const unsigned char uc = static_cast<unsigned char>(c);
        c = static_cast<char>(std::toupper(uc));
    }
    return s;
}

static inline bool ends_with_ci(const std::string& s, const std::string& suffix) {
    if (s.size() < suffix.size()) return false;
    return upper_copy(s.substr(s.size() - suffix.size())) == upper_copy(suffix);
}

static inline bool contains_path_sep(const std::string& s) {
    return (s.find('/') != std::string::npos) || (s.find('\\') != std::string::npos);
}

static inline bool looks_absolute(const std::string& s) {
    return (s.size() > 2 && std::isalpha(static_cast<unsigned char>(s[0])) && s[1] == ':') ||
           (!s.empty() && (s[0] == '/' || s[0] == '\\'));
}

// Resolve user token to container "<INDEXES>/<STEM>.cdx" (stable contract).
static std::string resolve_container_path(const std::string& token) {
    const std::filesystem::path idx = dottalk::paths::get_slot(dottalk::paths::Slot::INDEXES);

    // If token is already an envdir (<something>.cdx.d), normalize to container by stripping ".d".
    if (ends_with_ci(token, ".cdx.d")) {
        const auto envdir = (contains_path_sep(token) || looks_absolute(token)) ? token : (idx / token).string();
        return envdir.substr(0, envdir.size() - 2);
    }

    // If token is a container "students.cdx"
    if (ends_with_ci(token, ".cdx")) {
        return (contains_path_sep(token) || looks_absolute(token)) ? token : (idx / token).string();
    }

    // Otherwise treat as stem ("students")
    std::string stem = token;
    if (stem.empty()) stem = "students";
    return (idx / (upper_copy(stem) + ".cdx")).string();
}


static void print_setlmdb_usage()
{
    cli::cmdout::print_message(MessageId::SetLmdbUsageText);
}

static bool is_setlmdb_usage_request(const std::string& raw)
{
    std::string t = upper_copy(trim_copy(raw));
    if (t.rfind("SET LMDB ", 0) == 0) {
        t = upper_copy(trim_copy(t.substr(9)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

} // namespace

void cmd_SETLMDB(xbase::DbArea& db, std::istringstream& iss) {
    const std::string raw_args = iss.str();

    std::string tok;
    iss >> tok;
    tok = trim_copy(tok);

    if (is_setlmdb_usage_request(tok) || is_setlmdb_usage_request(raw_args)) {
        print_setlmdb_usage();
        return;
    }

    // Report-only form
    if (tok.empty()) {
        if (!orderstate::hasOrder(db)) {
            cli::cmdout::print_prefixed_message("SET LMDB", MessageId::SetOrderNonePhysicalText);
            return;
        }
        cli::cmdout::print_prefixed_message(
            "SET LMDB",
            MessageId::SetLmdbStatusText,
            {{"container", orderstate::orderName(db)},
             {"tag", orderstate::activeTag(db)},
             {"direction", orderstate::isAscending(db) ? "ASC" : "DESC"}});
        if (const auto* im = xindex::manager_if_attached(db); im && im->hasBackend()) {
            cli::cmdout::print_message(
                MessageId::SetLmdbBackendLineText,
                {{"backend", im->isCdx() ? "CDX/LMDB" : "OTHER"}});
        }
        return;
    }

    if (!db.isOpen()) {
        cli::cmdout::print_prefixed_message("SET LMDB", MessageId::SetIndexNoTableOpenText);
        return;
    }

    // Clear form
    if (tok == "0") {
        orderstate::clearOrder(db);
        xindex::ensure_manager(db).close();
        cli::cmdout::print_prefixed_message("SET LMDB", MessageId::SetOrderClearedPhysicalText);
        return;
    }

    // Parse optional tag + flags
    std::string chosenTag;
    std::string flag;
    iss >> chosenTag;
    iss >> flag;

    bool asc = true;
    if (!flag.empty()) {
        const std::string f = upper_copy(flag);
        if (f == "--DESC") asc = false;
        if (f == "--ASC")  asc = true;
    }

    const std::string container = resolve_container_path(tok);

    if (chosenTag.empty()) chosenTag = "LNAME";
    const std::string tag = upper_copy(chosenTag);

    // Persist per-area order state (legacy contract)
    orderstate::setOrder(db, container);
    orderstate::setActiveTag(db, tag);
    orderstate::setAscending(db, asc);

    // Open per-area backend now (no global LMDB state).
    {
        std::string err;
        if (!xindex::ensure_manager(db).openCdx(container, tag, &err)) {
            cli::cmdout::print_prefixed_message(
                "SET LMDB",
                MessageId::SetLmdbOpenCdxFailedText,
                {{"detail", err.empty() ? "openCdx failed" : err}});
            // keep state consistent
            orderstate::clearOrder(db);
            xindex::ensure_manager(db).close();
            return;
        }
    }

    cli::cmdout::print_prefixed_message(
        "SET LMDB",
        MessageId::SetLmdbUsingText,
        {{"container", container},
         {"tag", tag},
         {"direction", asc ? "ASC" : "DESC"}});
    cli::cmdout::print_message(
        MessageId::SetLmdbEnvdirLineText,
        {{"path", container + ".d"}});
}
