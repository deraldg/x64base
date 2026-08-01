// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_rebuild.cpp
// REBUILD [<name-or-path.cnx>]
//
// CNX rebuild (legacy compound index)
//
// Policy:
// - Rebuilds the CNX container once
// - CNX backend itself rebuilds all tags in the container
// - Requires clean TABLE (or explicit COMMIT)
//
// Architecture:
// - Public CNX container resolves via INDEXES
// - CNX remains a legacy/flat structure (no LMDB backend)
//
// Relationship to REINDEX:
// - REINDEX CNX -> calls REBUILD
// - This file is the CNX execution engine / orchestrator

// @dottalk.usage v1
// owner: DOT|REBUILD
// command: REBUILD
// category: index
// status: supported
// noargs: mutate
// effect: rebuild
// mutates: cnx-index table-stale-state
// usage-access: REBUILD USAGE
// summary:
//   Rebuild a CNX container for the current table, using the active CNX or a
//   supplied CNX name/path and clearing TABLE stale state on success.
//
// usage:
//   REBUILD USAGE
//   REBUILD
//   REBUILD <name-or-path.cnx>
//
// notes:
//   REBUILD with no arguments uses the current CNX or defaults to <table>.cnx.
//   REBUILD requires an open table except for REBUILD USAGE.
//   REBUILD prompts to COMMIT dirty TABLE buffers before rebuilding.
//   REBUILD refuses to continue if the table remains dirty after COMMIT.
//   REBUILD opens the CNX tag directory once for reporting.
//   The CNX backend rebuilds all tags in the container in one rebuild call.
//   On success, TABLE STALE is cleared for the current area when table buffering is enabled.
//
// risk:
//   writes_index_file: yes
//   reads_cnx_tagdir: yes
//   may_commit_buffered_table_data: yes when dirty TABLE is accepted
//   clears_stale_state: yes on success
//   mutates_table_data: indirectly through COMMIT prompt only
//   requires_open_table: yes except usage
//
// related:
//   REINDEX
//   CNX
//   COMMIT
//   TABLE
//

#include "xbase.hpp"

#include "cnx/cnx.hpp"
#include "cnx/cnx_backend.hpp"
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"        // ensure_manager
#include "cli/command_output.hpp"
#include "cli/path_resolver.hpp"
#include "cli/order_state.hpp"
#include "cli/table_state.hpp"

#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace fs = std::filesystem;

// Is the attached container the one REBUILD was asked to rebuild?
//
// PATH IDENTITY, NOT STRING IDENTITY. A container reached by two spellings of
// the same path is one container, and this codebase has already been bitten:
// IndexManager::openCnx's own already-open short-circuit compares raw strings
// and misses for exactly that reason (finding F3). Compare normalised forms,
// and fall back to a lexical compare rather than throwing if either path
// cannot be resolved -- a wrong answer here means rebuilding through the wrong
// object, so it fails toward "not the same container", which is the old
// behaviour and is safe.
static bool same_container_path_(const std::string& attached, const fs::path& target)
{
    if (attached.empty()) return false;

    std::error_code ec_a;
    std::error_code ec_b;
    const fs::path a = fs::weakly_canonical(fs::path(attached), ec_a);
    const fs::path b = fs::weakly_canonical(target, ec_b);

    if (!ec_a && !ec_b) return a == b;

    return fs::path(attached).lexically_normal() == target.lexically_normal();
}

extern "C" xbase::XBaseEngine* shell_engine(void);

// forward declare
void cmd_COMMIT(xbase::DbArea& A, std::istringstream& in);

namespace {

static inline std::string up_copy(std::string s)
{
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static int resolve_current_index(xbase::DbArea& A)
{
    if (auto* eng = shell_engine()) {
        for (int i = 0; i < xbase::MAX_AREA; ++i) {
            if (&eng->area(i) == &A) return i;
        }
    }
    return -1;
}

static bool prompt_yes_no(const std::string& prompt, bool default_no = true)
{
    std::cout << prompt;
    std::cout << (default_no ? " (y/N) " : " (Y/n) ");

    std::string line;
    std::getline(std::cin, line);

    if (line.empty()) return !default_no;

    const char c = static_cast<char>(std::toupper(static_cast<unsigned char>(line[0])));
    return c == 'Y';
}

static std::string normalize_field_name(std::string s)
{
    const auto nul = s.find('\0');
    if (nul != std::string::npos) s.resize(nul);

    while (!s.empty() && s.back() == ' ') s.pop_back();

    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static fs::path resolve_cnx_token(const std::string& tok)
{
    fs::path p = dottalk::paths::resolve_index(tok);
    if (!p.has_extension()) p.replace_extension(".cnx");
    return p;
}

static fs::path default_cnx_for_open_table(const xbase::DbArea& A)
{
    if (orderstate::hasOrder(A) && orderstate::isCnx(A)) {
        const std::string active = orderstate::orderName(A);
        if (!active.empty()) return fs::path(active);
    }

    std::string stem = A.dbfBasename();
    if (stem.empty()) stem = A.logicalName();
    if (stem.empty()) stem = "table";

    return resolve_cnx_token(stem);
}

static bool ensure_clean_or_commit(xbase::DbArea& A, int area0, const char* verb)
{
    if (area0 < 0) return true;
    if (!dottalk::table::is_enabled(area0)) return true;
    if (!dottalk::table::is_dirty(area0)) return true;

    std::ostringstream oss;
    oss << verb << ": TABLE has uncommitted changes. Commit now and continue?";
    if (!prompt_yes_no(oss.str(), true)) {
        cli::cmdout::print_prefixed_message(verb, dottalk::helpdata::MessageId::RebuildCanceledDirtyText);
        return false;
    }

    std::istringstream empty;
    cmd_COMMIT(A, empty);

    if (dottalk::table::is_dirty(area0)) {
        cli::cmdout::print_prefixed_message(verb, dottalk::helpdata::MessageId::RebuildStillDirtyText);
        return false;
    }

    return true;
}

static void print_help()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::RebuildUsageText);
}

} // namespace

void cmd_REBUILD(xbase::DbArea& A, std::istringstream& in)
{
    std::string arg;
    if (in >> arg) {
        const std::string up = up_copy(arg);
        if (up == "USAGE" || up == "HELP" || up == "?" ||
            up == "/?" || up == "-H" || up == "--HELP") {
            print_help();
            return;
        }
    }

    const int area0 = resolve_current_index(A);
    if (!ensure_clean_or_commit(A, area0, "REBUILD")) return;

    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildNoTableOpenText);
        return;
    }

    fs::path cnx_path;
    if (!arg.empty()) cnx_path = resolve_cnx_token(arg);
    else              cnx_path = default_cnx_for_open_table(A);

    if (!fs::exists(cnx_path)) {
        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildCnxNotFoundText,
            {{"path", cnx_path.string()}});
        return;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::RebuildReindexBannerText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::RebuildCnxContainerText, {{"path", cnx_path.string()}});

    // Read tagdir once for reporting only.
    cnxfile::CNXHandle* h = nullptr;
    if (!cnxfile::open(cnx_path.string(), h) || !h) {
        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildUnableOpenCnxText);
        return;
    }

    std::vector<cnxfile::TagInfo> tags;
    if (!cnxfile::read_tagdir(h, tags)) {
        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildFailedReadTagdirText);
        cnxfile::close(h);
        return;
    }

    cnxfile::close(h);

    try {
        // XIDX-TXN-02 M2, finding F4. REBUILD used to ALWAYS construct a local
        // throwaway CnxBackend and rebuild through that, leaving the area's
        // ATTACHED backend holding a stale in-memory permutation and a
        // non-empty dirty set. Harmless until M2 gave close() a save(): the
        // next SET ORDER closed the attached backend, save() re-appended the
        // stale permutation, and the correct rebuild was overwritten.
        //
        // Measured 2026-08-01 by the VUREPCNX proof:
        //     [CNX REBUILD] tag=SID recs=4 root=4240   <- correct
        //     [CNX SAVE]    tag=SID recs=4 root=4288   <- stale, over the top
        //
        // The remedy is the same one findings F1 and F3 want at their own
        // seams: REBIND rather than build a second object. Rebuilding through
        // the attached backend leaves ONE OWNER of the state -- rebuild()
        // clears its own dirty set and reloads its own document, so there is
        // nothing stale left to republish.
        //
        // Asked as a CAPABILITY question, not a type question. rebuild() is on
        // IIndexBackend, so this needs no dynamic_cast and stays correct if
        // this container ever gains a different backend. The local instance
        // remains the fallback for the case it was written for: rebuilding a
        // container that is not the one currently attached.
        auto& im = xindex::ensure_manager(A);

        const bool attached_owns_this_container =
            im.hasBackend() && same_container_path_(im.containerPath(), cnx_path);

        if (attached_owns_this_container) {
            im.backend()->rebuild();
        } else {
            xindex::CnxBackend b(A, cnx_path.string(), orderstate::activeTag(A));

            if (!b.open(cnx_path.string())) {
                cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildBackendOpenFailedText);
                return;
            }

            b.rebuild();
            b.close();
        }

        // Report once per tag, but rebuild only happened once.
        for (const auto& t : tags) {
            const std::string tag = normalize_field_name(t.name);
            cli::cmdout::print_message(dottalk::helpdata::MessageId::RebuildTagOkText,
                {{"id", std::to_string(t.tag_id)}, {"tag", tag}});
        }

        if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
            dottalk::table::set_stale(area0, false);
            dottalk::table::clear_stale_fields(area0);
            cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildStaleClearedText);
        }

        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildDoneText,
            {{"ok", std::to_string(tags.size())}});
    }
    catch (const std::exception& e) {
        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildFailDetailText,
            {{"detail", e.what()}});
    }
    catch (...) {
        cli::cmdout::print_prefixed_message("REBUILD", dottalk::helpdata::MessageId::RebuildFailText);
    }
}