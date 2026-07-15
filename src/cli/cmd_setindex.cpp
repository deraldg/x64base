// src/cli/cmd_setindex.cpp
// SET INDEX TO <container>
//
// Flavor-aware decision flow:
// - If user explicitly supplies an extension:
//     classic xBase/VFP accepts .inx / .cnx
//     true x64/v128 accepts .cdx only
// - If user supplies no extension:
//     classic xBase/VFP prefers .cnx, then .inx
//     true x64/v128 prefers .cdx
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
// - SET INDEX TO
//     attach the default container for the open table (current DBF stem)
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

// @dottalk.usage v1
// owner: DOT|SET INDEX
// command: SET INDEX
// category: index
// status: supported
// noargs: usage
// effect: attach
// mutates: order-state index-backend cursor
// usage-access: SET INDEX USAGE
// summary:
//   Flavor-aware SET INDEX command that attaches INX, CNX, or CDX containers and
//   can seed an active tag immediately.
//
// usage:
//   SET INDEX USAGE
//   SET INDEX TO
//   SET INDEX TO <container>
//   SET INDEX TO <container> TAG <tag>
//   SET INDEX TO <container> <tag>
//   SETINDEX USAGE
//   SETINDEX TO
//   SETINDEX TO <container>
//   SETINDEX TO <container> TAG <tag>
//   SETINDEX TO <container> <tag>
//
// notes:
//   SET INDEX requires an open table except for usage.
//   Explicit extensions are validated by table flavor.
//   Classic xBase/VFP tables accept INX or CNX.
//   True x64/v128 tables require CDX.
//   SET INDEX TO with no container uses the current DBF stem.
//   Bare container names resolve through the INDEXES path slot.
//   CDX attachment also requires the LMDB environment to exist.
//   Container attach and tag activation are treated as related but separate decisions.
//   INX is single-order; supplied tag names are accepted but ignored.
//   On hard failure, active index/order state is cleared to avoid stale ordering.
//
// risk:
//   mutates_order_state: yes
//   mutates_index_backend: yes
//   mutates_cursor: when tag activation positions to first ordered record
//   reads_filesystem: yes
//   mutates_table_data: no
//
// related:
//   SET ORDER
//   INDEX
//   REINDEX
//   CDX
//   CNX
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "cli/command_output.hpp"
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"
#include "cdx/cdx.hpp"
#include "textio.hpp"
#include "cli/order_state.hpp"
#include "cli/path_resolver.hpp"
#include "cli/nav_move.hpp"

namespace fs = std::filesystem;

namespace {

using MessageId = dottalk::helpdata::MessageId;

static std::string msg(MessageId id,
                       const std::unordered_map<std::string, std::string>& vars = {})
{
    return cli::cmdout::message_text(id, vars);
}

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

static bool is_v32_area(const xbase::DbArea& A) {
    return A.kind() == xbase::AreaKind::V32;
}

static bool is_x64_cdx_area(const xbase::DbArea& A) {
    return A.versionByte() == xbase::DBF_VERSION_64 ||
           A.kind() == xbase::AreaKind::V128;
}

static bool is_classic_tag_area(const xbase::DbArea& A) {
    return is_v32_area(A) ||
           (A.kind() == xbase::AreaKind::V64 &&
            A.versionByte() != xbase::DBF_VERSION_64);
}


static void print_setindex_usage()
{
    cli::cmdout::print_message(MessageId::SetIndexUsageText);
}

static bool is_setindex_usage_request(const std::string& raw)
{
    std::string t = up_copy(textio::trim(raw));
    if (t.rfind("SET INDEX ", 0) == 0) {
        t = up_copy(textio::trim(t.substr(10)));
    }
    return t.empty() || t == "USAGE" || t == "HELP" || t == "?";
}

static std::string default_index_token_for_area(const xbase::DbArea& A) {
    try {
        const fs::path p(A.filename());
        const std::string stem = p.stem().string();
        if (!stem.empty()) return stem;
    } catch (...) {
    }

    try {
        const std::string base = A.dbfBasename();
        if (!base.empty()) return base;
    } catch (...) {
    }

    return {};
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
        xindex::ensure_manager(A).close();
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
        err = msg(MessageId::SetIndexUnsupportedContainerText,
                  {{"path", p.string()}});
        return false;
    }

    if (is_classic_tag_area(A)) {
        if (ext != ".inx" && ext != ".cnx") {
            err = msg(MessageId::SetIndexV32AcceptsInxOrCnxText);
            return false;
        }
        return true;
    }

    if (is_x64_cdx_area(A)) {
        if (ext != ".cdx") {
            err = msg(MessageId::SetIndexV64RequiresCdxText);
            return false;
        }
        return true;
    }

    err = msg(MessageId::SetIndexUnknownFlavorText);
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
    if (is_classic_tag_area(A)) {
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

        err = msg(MessageId::SetIndexNoValidV32IndexText,
                  {{"token", tok}});
        return false;
    }

    if (is_x64_cdx_area(A)) {
        fs::path cdx = base;
        cdx.replace_extension(".cdx");

        out_path = cdx;
        return true;
    }

    err = msg(MessageId::SetIndexUnknownFlavorText);
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
        err = msg(MessageId::SetIndexMissingFilenameText);
        return false;
    }

    if (up_copy(container_tok) == "TO") {
        if (!(args >> container_tok)) {
            container_tok.clear();
            return true;
        }
    }

    std::string next;
    if (!(args >> next)) {
        return true; // attach only
    }

    if (up_copy(next) == "TAG") {
        if (!(args >> tag_tok)) {
            err = msg(MessageId::SetIndexTagRequiresNameText);
            return false;
        }

        std::string extra;
        if (args >> extra) {
            err = msg(MessageId::SetIndexUnexpectedTrailingTokenText,
                      {{"token", extra}});
            return false;
        }
        return true;
    }

    // Shorthand:
    //   SET INDEX TO students.cnx lname
    tag_tok = next;

    std::string extra;
    if (args >> extra) {
        err = msg(MessageId::SetIndexUnexpectedTrailingTokenText,
                  {{"token", extra}});
        return false;
    }

    return true;
}

// Shared activation helpers copied locally so cmd_setindex.cpp remains
// self-contained and does not depend on file-local statics in cmd_setorder.cpp.

static void position_to_first_after_order_change(xbase::DbArea& area)
{
    try {
        auto& im = xindex::ensure_manager(area);

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
        err = msg(MessageId::SetIndexUnableOpenCdxContainerText);
        return false;
    }

    std::vector<cdxfile::TagInfo> tags;
    if (!cdxfile::read_tagdir(h, tags)) {
        cdxfile::close(h);
        err = msg(MessageId::SetIndexUnableReadCdxTagDirectoryText);
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
    err = msg(MessageId::SetIndexTagNotFoundInContainerText,
              {{"tag", wantedTag}, {"container", container}});
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
        err = msg(MessageId::SetIndexOpenCdxContainerNotFoundText,
                  {{"container", container_path.string()}});
        return false;
    }

    if (!fs::exists(env_path) || !fs::is_directory(env_path)) {
        err = msg(MessageId::SetIndexOpenCdxEnvMissingText,
                  {{"env", env_path.string()}});
        return false;
    }

    xindex::ensure_manager(area).close();
    orderstate::clearOrder(area);

    orderstate::setOrder(area, container);
    orderstate::setActiveTag(area, tag);
    orderstate::setAscending(area, ascending);

    if (!xindex::ensure_manager(area).openCdx(container, tag, &err)) {
        if (err.empty()) {
            err = msg(MessageId::SetIndexOpenCdxBackendOpenFailedText,
                      {{"container", container_path.string()},
                       {"env", env_path.string()}});
        } else {
            err = msg(MessageId::SetIndexOpenCdxBackendOpenFailedDetailText,
                      {{"detail", err},
                       {"container", container_path.string()},
                       {"env", env_path.string()}});
        }
        orderstate::clearOrder(area);
        xindex::ensure_manager(area).close();
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
        err = msg(MessageId::SetIndexOpenCnxContainerNotFoundText,
                  {{"container", container}});
        return false;
    }

    xindex::ensure_manager(area).close();
    orderstate::clearOrder(area);

    orderstate::setOrder(area, container);
    orderstate::setActiveTag(area, tag);
    orderstate::setAscending(area, ascending);

    if (!xindex::ensure_manager(area).openCnx(container, tag, &err)) {
        if (err.empty()) err = msg(MessageId::SetIndexOpenCnxBackendOpenFailedText);
        orderstate::clearOrder(area);
        xindex::ensure_manager(area).close();
        return false;
    }

    position_to_first_after_order_change(area);
    return true;
}

} // namespace

void cmd_SETINDEX(xbase::DbArea& A, std::istringstream& args)
{
    const std::string raw_args = args.str();
    if (is_setindex_usage_request(raw_args)) {
        print_setindex_usage();
        return;
    }

    if (!A.isOpen()) {
        cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexNoTableOpenText);
        return;
    }

    std::string tok;
    std::string tag;
    std::string parse_err;

    if (!parse_setindex_args(args, tok, tag, parse_err)) {
        cli::cmdout::print_line("SET INDEX: " + parse_err);
        print_setindex_usage();
        return;
    }

    if (tok.empty()) {
        tok = default_index_token_for_area(A);
        if (tok.empty()) {
            cli::cmdout::print_line("SET INDEX: " + msg(MessageId::SetIndexMissingFilenameText));
            print_setindex_usage();
            return;
        }
    }

    fs::path p;
    std::string err;

    if (!choose_container_path_for_flavor(A, tok, p, err)) {
        clear_index_state(A);
        cli::cmdout::print_line("SET INDEX: " + err);
        return;
    }

    const std::string ext = lower_copy(p.extension().string());

    if (!fs::exists(p)) {
        clear_index_state(A);
        cli::cmdout::print_prefixed_message(
            "SET INDEX",
            MessageId::SetIndexFileNotFoundText,
            {{"path", p.string()}});
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
                cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexCdxEnvMissingText);
                cli::cmdout::print_message(MessageId::SetIndexContainerLine, {{"path", p.string()}});
                cli::cmdout::print_message(MessageId::SetIndexExpectedEnvLine, {{"path", env.string()}});
                cli::cmdout::print_message(MessageId::SetIndexHintReindexBuildLmdbText);
                return;
            }

            cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexCdxAttachedText);
            cli::cmdout::print_message(MessageId::SetIndexContainerLine, {{"path", p.filename().string()}});
            cli::cmdout::print_message(MessageId::SetIndexLmdbEnvLine, {{"path", env.string()}});
            cli::cmdout::print_message(MessageId::SetIndexUseSetOrderHintText);
            return;
        }

        if (ext == ".cnx") {
            cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexCnxAttachedText);
            cli::cmdout::print_message(MessageId::SetIndexContainerLine, {{"path", p.filename().string()}});
            cli::cmdout::print_message(MessageId::SetIndexUseSetOrderHintText);
            return;
        }

        if (ext == ".inx") {
            cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexInxAttachedText);
            cli::cmdout::print_line("  " + p.filename().string());
            return;
        }

        clear_index_state(A);
        cli::cmdout::print_prefixed_message(
            "SET INDEX",
            MessageId::SetIndexUnsupportedResolvedExtensionText,
            {{"path", p.string()}});
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
            cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexCdxAttachedText);
            cli::cmdout::print_message(MessageId::SetIndexContainerLine, {{"path", p.filename().string()}});
            cli::cmdout::print_message(MessageId::SetIndexTagNotFoundText, {{"tag", tag_up}});
            return;
        }

        ok = activate_cdx_on_area(A, container, tag_up, ascending, err2);

    }
    else if (ext == ".cnx") {

        if (!cnx_has_tag(A, tag_up)) {
            cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexCnxAttachedText);
            cli::cmdout::print_message(MessageId::SetIndexContainerLine, {{"path", p.filename().string()}});
            cli::cmdout::print_message(MessageId::SetIndexTagInvalidForTableText, {{"tag", tag_up}});
            return;
        }

        ok = activate_cnx_on_area(A, container, tag_up, ascending, err2);

    }
    else if (ext == ".inx") {

        cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexInxAttachedText);
        cli::cmdout::print_line("  " + p.filename().string());
        cli::cmdout::print_message(MessageId::SetIndexInxTagIgnoredText);
        return;
    }
    else {
        clear_index_state(A);
        cli::cmdout::print_prefixed_message(
            "SET INDEX",
            MessageId::SetIndexUnsupportedResolvedExtensionText,
            {{"path", p.string()}});
        return;
    }

    if (!ok) {
        clear_index_state(A);
        if (err2.empty()) {
            cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexUnableActivateTagText);
        } else {
            cli::cmdout::print_line("SET INDEX: " + err2);
        }
        return;
    }

    // Success message (mirrors SET ORDER)
    cli::cmdout::print_prefixed_message("SET INDEX", MessageId::SetIndexAttachedActivatedText);
    cli::cmdout::print_message(MessageId::SetIndexContainerLine, {{"path", p.filename().string()}});
    cli::cmdout::print_message(MessageId::SetIndexTagAscLine, {{"tag", tag_up}});
}
