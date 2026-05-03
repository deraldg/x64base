// src/cli/cmd_setindex.cpp
// SET INDEX TO <container>
//
// Flavor-aware decision flow:
// - If user explicitly supplies an extension:
//     v32 accepts .inx / .cnx
//     v64 accepts .cdx only
// - If user supplies no extension:
//     v32 prefers .cnx, then .inx
//     v64 prefers .cdx
//
// CDX notes:
// - CDX public container is attached through order state
// - LMDB env must also exist for usable CDX/LMDB operation
//
// Note:
// Full backend open/close through A.indexManager() requires the header that
// defines xindex::IndexManager, not just the forward declaration from xbase.hpp.
//
// Extended UX:
// - SET INDEX TO <container>
//     attach container only (current behavior preserved)
// - SET INDEX TO <container> TAG <tag>
//     attach container and seed the active tag immediately
// - SET INDEX TO <container> <tag>
//     shorthand form for the same
//
// Behavioral rule:
// - Container attach and tag activation are treated as two related decisions.
// - If container attach succeeds but tag activation cannot be honored, the
//   container should still remain attached.
// - For .inx, trailing TAG / bare tag is accepted but ignored, because INX is
//   effectively a single-order container.

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xindex/index_manager.hpp"
#include "cdx/cdx.hpp"
#include "textio.hpp"
#include "cli/order_state.hpp"
#include "cli/path_resolver.hpp"
#include "cli/nav_move.hpp"

namespace fs = std::filesystem;

namespace {

static std::string up_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::string lower_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s;
}

static bool ends_with_ci(const std::string& s, const char* suffix) {
    const std::string sl = lower_copy(s);
    const std::string su = lower_copy(std::string(suffix));
    if (sl.size() < su.size()) return false;
    return sl.compare(sl.size() - su.size(), su.size(), su) == 0;
}

static bool has_any_sep(const std::string& s) {
    return s.find('/') != std::string::npos || s.find('\\') != std::string::npos;
}

static bool looks_absolute(const std::string& s) {
    return (s.size() > 2 &&
            std::isalpha(static_cast<unsigned char>(s[0])) &&
            s[1] == ':') ||
           (!s.empty() && (s[0] == '/' || s[0] == '\\'));
}

static bool is_supported_index_ext(const fs::path& p) {
    const std::string ext = lower_copy(p.extension().string());
    return ext == ".inx" || ext == ".cnx" || ext == ".cdx";
}

static fs::path resolve_index_token(const std::string& tok) {
    if (ends_with_ci(tok, ".cdx.d")) {
        std::string s = tok;
        s.erase(s.size() - 2); // strip trailing ".d"
        return has_any_sep(s) || looks_absolute(s)
             ? fs::path(s)
             : dottalk::paths::resolve_index(s);
    }
    return dottalk::paths::resolve_index(tok);
}

static bool has_explicit_extension(const fs::path& p) {
    return p.has_extension() && !p.extension().string().empty();
}

static bool is_v64_area(const xbase::DbArea& A) {
    return A.kind() == xbase::AreaKind::V64;
}

static bool is_v32_area(const xbase::DbArea& A) {
    return A.kind() == xbase::AreaKind::V32;
}

// Keep existing attach/reset behavior:
// - bind container into order state
// - default ascending
// - clear active tag
//
// If the caller later supplies a tag, it will be seeded after attach.
static void print_attach_and_seed_orderstate(xbase::DbArea& A, const fs::path& p) {
    orderstate::setOrder(A, p.string());
    orderstate::setAscending(A, true);
    orderstate::setActiveTag(A, "");
}

// Clear any active runtime/backend order state.  This is used on hard SET INDEX
// failure paths so a failed attach attempt cannot leave the previous CDX/CNX/INX
// order active and make later SET ORDER / TOP / LIST tests lie.
static void clear_index_state(xbase::DbArea& A) {
    try {
        A.indexManager().close();
    } catch (...) {
        // Best-effort cleanup only.  SET INDEX diagnostics should still report
        // the original user-facing failure, not a secondary close failure.
    }

    orderstate::clearOrder(A);
}

static bool validate_explicit_ext_for_flavor(const xbase::DbArea& A,
                                             const fs::path& p,
                                             std::string& err)
{
    const std::string ext = lower_copy(p.extension().string());

    if (!is_supported_index_ext(p)) {
        err = "SET INDEX: unsupported index container: " + p.string() + "\n"
              "Supported: .inx, .cnx, .cdx";
        return false;
    }

    if (is_v32_area(A)) {
        if (ext != ".inx" && ext != ".cnx") {
            err = "SET INDEX: v32 tables accept INX or CNX, not CDX.\n"
                  "Use .inx or .cnx for this table.";
            return false;
        }
        return true;
    }

    if (is_v64_area(A)) {
        if (ext != ".cdx") {
            err = "SET INDEX: v64 tables require CDX (LMDB-backed).\n"
                  "Use .cdx for this table.";
            return false;
        }
        return true;
    }

    err = "SET INDEX: unknown/unsupported table flavor for current area.";
    return false;
}

static bool choose_container_path_for_flavor(const xbase::DbArea& A,
                                             const std::string& tok,
                                             fs::path& out_path,
                                             std::string& err)
{
    fs::path base = resolve_index_token(tok);

    // Explicit extension path: respect it, then validate against flavor.
    if (has_explicit_extension(base)) {
        if (!validate_explicit_ext_for_flavor(A, base, err)) {
            return false;
        }

        out_path = base;
        return true;
    }

    // No explicit extension: choose by flavor policy.
    if (is_v32_area(A)) {
        fs::path cnx = base;
        fs::path inx = base;
        cnx.replace_extension(".cnx");
        inx.replace_extension(".inx");

        if (fs::exists(cnx)) {
            out_path = cnx;
            return true;
        }
        if (fs::exists(inx)) {
            out_path = inx;
            return true;
        }

        err = "SET INDEX: no valid v32 index found for '" + tok + "'.\n"
              "Looked for .cnx, then .inx.";
        return false;
    }

    if (is_v64_area(A)) {
        fs::path cdx = base;
        cdx.replace_extension(".cdx");

        out_path = cdx;
        return true;
    }

    err = "SET INDEX: unknown/unsupported table flavor for current area.";
    return false;
}

// Parse:
//   SET INDEX TO <container>
//   SET INDEX TO <container> TAG <tag>
//   SET INDEX TO <container> <tag>
//
// Notes:
// - "TO" is optional from the parser's point of view because callers may route
//   here as either "SET INDEX ..." or "SET INDEX TO ..."
// - Bare trailing token is treated as shorthand for TAG <tag>
// - Extra trailing tokens are rejected for now to keep behavior deterministic
static bool parse_setindex_args(std::istringstream& args,
                                std::string& container_tok,
                                std::string& tag_tok,
                                std::string& err)
{
    container_tok.clear();
    tag_tok.clear();
    err.clear();

    if (!(args >> container_tok)) {
        err = "SET INDEX: missing filename.";
        return false;
    }

    if (up_copy(container_tok) == "TO") {
        if (!(args >> container_tok)) {
            err = "SET INDEX: missing filename.";
            return false;
        }
    }

    std::string next;
    if (!(args >> next)) {
        return true; // attach only
    }

    if (up_copy(next) == "TAG") {
        if (!(args >> tag_tok)) {
            err = "SET INDEX: TAG requires a name.";
            return false;
        }

        std::string extra;
        if (args >> extra) {
            err = "SET INDEX: unexpected trailing token '" + extra + "'.";
            return false;
        }
        return true;
    }

    // Shorthand:
    //   SET INDEX TO students.cnx lname
    tag_tok = next;

    std::string extra;
    if (args >> extra) {
        err = "SET INDEX: unexpected trailing token '" + extra + "'.";
        return false;
    }

    return true;
}

// Shared activation helpers copied locally so cmd_setindex.cpp remains
// self-contained and does not depend on file-local statics in cmd_setorder.cpp.

static void position_to_first_after_order_change(xbase::DbArea& area)
{
    try {
        auto& im = area.indexManager();

        if (!im.hasBackend()) {
            cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET INDEX");
            return;
        }

        auto cur = im.scan(xindex::Key{}, xindex::Key{});
        if (!cur) {
            cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET INDEX");
            return;
        }

        xindex::Key k;
        xindex::RecNo r{0};

        const bool moved = orderstate::isAscending(area) ? cur->first(k, r)
                                                         : cur->last(k, r);
        if (moved) {
            const int recno = static_cast<int>(r);
            if (recno > 0 && recno <= area.recCount()) {
                (void)area.gotoRec(recno);
                (void)area.readCurrent();
                return;
            }
        }

        cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET INDEX");
    } catch (...) {
        try {
            cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET INDEX");
        } catch (...) {
        }
    }
}

static bool cdx_has_tag(const std::string& container,
                        const std::string& wantedTag,
                        std::string& err)
{
    err.clear();

    cdxfile::CDXHandle* h = nullptr;

    if (!cdxfile::open(container, h)) {
        err = "unable to open CDX container.";
        return false;
    }

    std::vector<cdxfile::TagInfo> tags;
    if (!cdxfile::read_tagdir(h, tags)) {
        cdxfile::close(h);
        err = "unable to read CDX tag directory.";
        return false;
    }

    const std::string want = up_copy(wantedTag);

    for (const auto& t : tags) {
        if (up_copy(t.name) == want) {
            cdxfile::close(h);
            return true;
        }
    }

    cdxfile::close(h);
    err = "tag '" + wantedTag + "' not found in " + container;
    return false;
}

static bool cnx_has_tag(const xbase::DbArea& area,
                        const std::string& wantedTag)
{
    const auto& Fs = area.fields();
    const std::string want = up_copy(textio::trim(wantedTag));
    if (want.empty()) return false;

    if (!want.empty() && want[0] == '#') {
        try {
            int idx = std::stoi(want.substr(1));
            return idx >= 1 && idx <= static_cast<int>(Fs.size());
        } catch (...) {
            return false;
        }
    }

    for (const auto& f : Fs) {
        if (up_copy(textio::trim(f.name)) == want) {
            return true;
        }
    }

    return false;
}

static bool activate_cdx_on_area(xbase::DbArea& area,
                                 const std::string& container,
                                 const std::string& tag,
                                 bool ascending,
                                 std::string& err)
{
    err.clear();

    const fs::path container_path(container);
    const fs::path env_path = dottalk::paths::resolve_lmdb_env_for_cdx(container_path);

    if (!fs::exists(container_path)) {
        err = "openCdx: container not found: " + container_path.string();
        return false;
    }

    if (!fs::exists(env_path) || !fs::is_directory(env_path)) {
        err = "openCdx: LMDB env missing: " + env_path.string();
        return false;
    }

    area.indexManager().close();
    orderstate::clearOrder(area);

    orderstate::setOrder(area, container);
    orderstate::setActiveTag(area, tag);
    orderstate::setAscending(area, ascending);

    if (!area.indexManager().openCdx(container, tag, &err)) {
        if (err.empty()) {
            err = "openCdx: backend open() failed"
                  " [container=" + container_path.string() +
                  ", env=" + env_path.string() + "]";
        } else {
            err += " [container=" + container_path.string() +
                   ", env=" + env_path.string() + "]";
        }
        orderstate::clearOrder(area);
        area.indexManager().close();
        return false;
    }

    position_to_first_after_order_change(area);
    return true;
}

static bool activate_cnx_on_area(xbase::DbArea& area,
                                 const std::string& container,
                                 const std::string& tag,
                                 bool ascending,
                                 std::string& err)
{
    err.clear();

    if (!fs::exists(container)) {
        err = "openCnx: container not found: " + container;
        return false;
    }

    area.indexManager().close();
    orderstate::clearOrder(area);

    orderstate::setOrder(area, container);
    orderstate::setActiveTag(area, tag);
    orderstate::setAscending(area, ascending);

    if (!area.indexManager().openCnx(container, tag, &err)) {
        if (err.empty()) err = "openCnx: backend open failed";
        orderstate::clearOrder(area);
        area.indexManager().close();
        return false;
    }

    position_to_first_after_order_change(area);
    return true;
}

} // namespace

void cmd_SETINDEX(xbase::DbArea& A, std::istringstream& args)
{
    if (!A.isOpen()) {
        std::cout << "SET INDEX: no table open.\n";
        return;
    }

    std::string tok;
    std::string tag;
    std::string parse_err;

    if (!parse_setindex_args(args, tok, tag, parse_err)) {
        std::cout << parse_err << "\n";
        return;
    }

    fs::path p;
    std::string err;

    if (!choose_container_path_for_flavor(A, tok, p, err)) {
        clear_index_state(A);
        std::cout << err << "\n";
        return;
    }

    const std::string ext = lower_copy(p.extension().string());

    if (!fs::exists(p)) {
        clear_index_state(A);
        std::cout << "SET INDEX: file not found: " << p.string() << "\n";
        return;
    }

    // Always attach container first (existing behavior)
    print_attach_and_seed_orderstate(A, p);

    // -------------------------------------------------------
    // NO TAG → preserve original behavior
    // -------------------------------------------------------
    if (tag.empty()) {

        if (ext == ".cdx") {
            const fs::path env = dottalk::paths::resolve_lmdb_env_for_cdx(p);

            if (!fs::exists(env)) {
                clear_index_state(A);
                std::cout << "SET INDEX: CDX container found but LMDB env missing\n";
                std::cout << "  Container: " << p.string() << "\n";
                std::cout << "  Expected : " << env.string() << "\n";
                std::cout << "Hint: run REINDEX CDX or BUILDLMDB\n";
                return;
            }

            std::cout << "SET INDEX (CDX attached)\n";
            std::cout << "  Container: " << p.filename().string() << "\n";
            std::cout << "  LMDB env : " << env.string() << "\n";
            std::cout << "Use SET ORDER TO TAG <tag>\n";
            return;
        }

        if (ext == ".cnx") {
            std::cout << "SET INDEX (CNX attached)\n";
            std::cout << "  Container: " << p.filename().string() << "\n";
            std::cout << "Use SET ORDER TO TAG <tag>\n";
            return;
        }

        if (ext == ".inx") {
            std::cout << "SET INDEX (INX attached)\n";
            std::cout << "  " << p.filename().string() << "\n";
            return;
        }

        clear_index_state(A);
        std::cout << "SET INDEX: unsupported resolved extension: " << p.string() << "\n";
        return;
    }

    // -------------------------------------------------------
    // TAG supplied → USE REAL SET ORDER LOGIC
    // -------------------------------------------------------

    std::string container = p.string();
    std::string tag_up = up_copy(tag);
    bool ascending = true;

    std::string err2;
    bool ok = false;

    if (ext == ".cdx") {

        if (!cdx_has_tag(container, tag_up, err2)) {
            std::cout << "SET INDEX (CDX attached)\n";
            std::cout << "  Container: " << p.filename().string() << "\n";
            std::cout << "Tag '" << tag_up << "' not found.\n";
            return;
        }

        ok = activate_cdx_on_area(A, container, tag_up, ascending, err2);

    }
    else if (ext == ".cnx") {

        if (!cnx_has_tag(A, tag_up)) {
            std::cout << "SET INDEX (CNX attached)\n";
            std::cout << "  Container: " << p.filename().string() << "\n";
            std::cout << "Tag '" << tag_up << "' not valid for this table.\n";
            return;
        }

        ok = activate_cnx_on_area(A, container, tag_up, ascending, err2);

    }
    else if (ext == ".inx") {

        std::cout << "SET INDEX (INX attached)\n";
        std::cout << "  " << p.filename().string() << "\n";
        std::cout << "  Note: INX is single-order; tag ignored.\n";
        return;
    }
    else {
        clear_index_state(A);
        std::cout << "SET INDEX: unsupported resolved extension: " << p.string() << "\n";
        return;
    }

    if (!ok) {
        clear_index_state(A);
        std::cout << "SET INDEX: " << (err2.empty() ? "unable to activate tag." : err2) << "\n";
        return;
    }

    // Success message (mirrors SET ORDER)
    std::cout << "SET INDEX: attached + activated\n";
    std::cout << "  Container: " << p.filename().string() << "\n";
    std::cout << "  TAG: '" << tag_up << "' (ASC)\n";
}