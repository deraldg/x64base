// src/cli/cmd_setorder.cpp
// FoxPro-style SET ORDER command with CNX/CDX-aware activation.
//
// Supported forms:
//   SET ORDER
//   SET ORDER 0
//   SET ORDER PHYSICAL | NATURAL | PHYS
//   SET ORDER <tag>
//   SET ORDER TAG <tag>
//   SET ORDER TAG <tag> IN <alias>
//   SET ORDER <container> <tag> [ASC|DESC|ASCEND|DESCEND|--asc|--desc]
//
// Notes:
// - For bare tag forms, an already-attached compatible container is preferred.
// - If no suitable container is attached, fallback is flavor-aware:
//     classic xBase/VFP -> <table>.cnx
//     true x64/v128 -> <table>.cdx
// - For IN <alias>, target area is modified without changing the selected area.
// - Numeric tag-number orders remain reserved/minimal for now.
//
// Policy:
// - classic xBase/VFP: CNX is the tag-container path.
// - true x64/v128: CDX (LMDB-backed) is the tag-container path.
// - INX remains valid for SET INDEX attachment, but tag activation via
//   SET ORDER is intentionally not handled here.
//
// CDX policy:
// - Public CDX container resolves under INDEXES.
// - LMDB backend resolves under LMDB.
// - This command validates both paths before attempting backend activation.

// @dottalk.usage v1
// owner: DOT|SET ORDER
// command: SET ORDER
// category: index
// status: supported
// noargs: report
// effect: configure
// mutates: order-state index-backend cursor
// usage-access: SET ORDER USAGE
// summary:
//   FoxPro-style SET ORDER command with CNX and CDX-aware tag activation.
//
// usage:
//   SET ORDER
//   SET ORDER USAGE
//   SET ORDER 0
//   SET ORDER PHYSICAL
//   SET ORDER NATURAL
//   SET ORDER PHYS
//   SET ORDER <tag>
//   SET ORDER TAG <tag>
//   SET ORDER TAG <tag> IN <alias>
//   SET ORDER <container> <tag>
//   SET ORDER <container> <tag> ASC
//   SET ORDER <container> <tag> DESC
//   SETORDER
//   SETORDER USAGE
//   SETORDER <tag>
//
// notes:
//   SET ORDER with no arguments reports the active order or physical order.
//   SET ORDER 0, PHYSICAL, NATURAL, and PHYS clear active order.
//   Bare tag forms prefer an already-attached compatible container.
//   If no suitable container is attached, fallback is flavor-aware.
//   Classic xBase/VFP tables default to CNX.
//   True x64/v128 tables default to CDX.
//   IN <alias> modifies the target area without changing the selected area.
//   INX activation is intentionally not handled by SET ORDER.
//
// risk:
//   mutates_order_state: yes
//   mutates_index_backend: yes
//   mutates_cursor: yes
//   mutates_table_data: no
//
// related:
//   SET INDEX
//   SET CDX
//   SET CNX
//   INDEX
//   REINDEX
//

#include <sstream>
#include <string>
#include <filesystem>
#include <cctype>
#include <limits>
#include <vector>
#include <algorithm>

#include "xbase.hpp"
#include "xbase/ramfs.hpp"
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

// An index container under a mounted ramfs root lives only in RAM (AIF-043),
// so a plain disk fs::exists would wrongly report it missing and block SET ORDER.
// Consult the ramfs registry first for virtual paths, then fall back to disk.
static bool container_exists(const std::string& path)
{
    if (xbase::ramfs::is_virtual(path)) return xbase::ramfs::exists(path);
    std::error_code ec;
    return fs::exists(path, ec);
}

static std::string msg(MessageId id,
                       const std::unordered_map<std::string, std::string>& vars = {})
{
    return cli::cmdout::message_text(id, vars);
}
} // namespace

// ---------- helpers ----------------------------------------------------------

static inline std::string up_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static inline std::string low_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

static inline bool ieq(const std::string& a, const char* b) {
    if (!b) return false;
    std::size_t n = 0;
    while (b[n] != '\0') ++n;
    if (a.size() != n) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        if (std::tolower(static_cast<unsigned char>(a[i])) !=
            std::tolower(static_cast<unsigned char>(b[i]))) {
            return false;
        }
    }
    return true;
}

static inline bool is_integer(const std::string& s, int& outVal) {
    if (s.empty()) return false;
    std::size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    if (i >= s.size()) return false;
    for (; i < s.size(); ++i) {
        if (!std::isdigit(static_cast<unsigned char>(s[i]))) return false;
    }
    try {
        long long v = std::stoll(s);
        if (v < std::numeric_limits<int>::min() ||
            v > std::numeric_limits<int>::max()) return false;
        outVal = static_cast<int>(v);
        return true;
    } catch (...) {
        return false;
    }
}

static inline bool ends_with_ci(const std::string& s, const std::string& suffix) {
    if (s.size() < suffix.size()) return false;
    return up_copy(s.substr(s.size() - suffix.size())) == up_copy(suffix);
}

static inline bool contains_path_sep(const std::string& s) {
    return (s.find('/') != std::string::npos) || (s.find('\\') != std::string::npos);
}

static inline bool looks_absolute(const std::string& s) {
    return (s.size() > 2 && std::isalpha(static_cast<unsigned char>(s[0])) && s[1] == ':') ||
           (!s.empty() && (s[0] == '/' || s[0] == '\\'));
}

static bool is_direction_token(const std::string& s) {
    const std::string u = up_copy(s);
    return u == "ASC" || u == "DESC" || u == "ASCEND" || u == "DESCEND" ||
           u == "--ASC" || u == "--DESC";
}

static bool parse_direction_token(const std::string& s, bool& ascending) {
    const std::string u = up_copy(s);
    if (u == "ASC" || u == "ASCEND" || u == "--ASC") {
        ascending = true;
        return true;
    }
    if (u == "DESC" || u == "DESCEND" || u == "--DESC") {
        ascending = false;
        return true;
    }
    return false;
}

static inline bool looks_like_container_token(const std::string& s) {
    if (s.empty()) return false;
    if (contains_path_sep(s) || looks_absolute(s)) return true;
    if (ends_with_ci(s, ".CDX") || ends_with_ci(s, ".CNX") ||
        ends_with_ci(s, ".INX") || ends_with_ci(s, ".CDX.D")) {
        return true;
    }
    return false;
}

static inline bool is_v32_area(const xbase::DbArea& area) {
    return area.kind() == xbase::AreaKind::V32;
}

static inline bool is_x64_cdx_area(const xbase::DbArea& area) {
    return area.versionByte() == xbase::DBF_VERSION_64 ||
           area.kind() == xbase::AreaKind::V128;
}

static inline bool is_classic_tag_area(const xbase::DbArea& area) {
    return is_v32_area(area) ||
           (area.kind() == xbase::AreaKind::V64 &&
            area.versionByte() != xbase::DBF_VERSION_64);
}

static fs::path resolve_index_path(const xbase::DbArea& area,
                                   const std::string& token,
                                   const std::string& defaultExt)
{
    if (token.empty()) {
        const std::string stem = !area.dbfBasename().empty() ? area.dbfBasename()
                                                             : area.logicalName();
        fs::path p = dottalk::paths::resolve_index(stem);
        if (!p.has_extension()) p.replace_extension(defaultExt);
        return p;
    }

    if (ends_with_ci(token, ".CDX.D")) {
        std::string s = token;
        s.erase(s.size() - 2); // strip trailing ".d"
        fs::path p = (contains_path_sep(s) || looks_absolute(s))
                   ? fs::path(s)
                   : dottalk::paths::resolve_index(s);
        return p;
    }

    fs::path p = dottalk::paths::resolve_index(token);
    if (!p.has_extension()) p.replace_extension(defaultExt);
    return p;
}

static int resolve_area_index_by_name(xbase::XBaseEngine& eng, const std::string& tokRaw) {
    std::string tok = textio::trim(tokRaw);
    if (tok.empty()) return -1;

    int n = 0;
    if (is_integer(tok, n)) {
        if (n >= 0 && n < xbase::MAX_AREA) return n;
        return -1;
    }

    const std::string want = up_copy(tok);
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        xbase::DbArea& A = eng.area(i);
        if (!A.isOpen()) continue;

        std::string name = A.name();
        std::replace(name.begin(), name.end(), '\\', '/');
        auto slash = name.find_last_of('/');
        if (slash != std::string::npos) name.erase(0, slash + 1);
        auto dot = name.find_last_of('.');
        if (dot != std::string::npos) name.erase(dot);
        name = up_copy(name);

        if (name == want) return i;
    }
    return -1;
}

extern "C" xbase::XBaseEngine* shell_engine();

static void clear_order_and_close_indexes(xbase::DbArea& area) {
    orderstate::clearOrder(area);
    xindex::ensure_manager(area).close();
}

static void position_to_first_after_order_change(xbase::DbArea& area)
{
    try {
        auto& im = xindex::ensure_manager(area);

        if (!im.hasBackend()) {
            cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET ORDER");
            return;
        }

        auto cur = im.scan(xindex::Key{}, xindex::Key{});
        if (!cur) {
            cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET ORDER");
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

        cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET ORDER");
    } catch (...) {
        try {
            cli::nav::go_endpoint(area, cli::nav::Endpoint::Top, "SET ORDER");
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
        err = msg(MessageId::SetOrderUnableOpenCdxContainerText);
        return false;
    }

    std::vector<cdxfile::TagInfo> tags;
    if (!cdxfile::read_tagdir(h, tags)) {
        cdxfile::close(h);
        err = msg(MessageId::SetOrderUnableReadCdxTagDirectoryText);
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
    err = msg(MessageId::SetOrderTagNotFoundInContainerText,
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

static bool attached_container_is_tag_container(const xbase::DbArea& area) {
    if (!orderstate::hasOrder(area)) return false;
    return orderstate::isCdx(area) || orderstate::isCnx(area);
}

static std::string preferred_attached_container_for_flavor(const xbase::DbArea& area) {
    if (!attached_container_is_tag_container(area)) return std::string{};

    const std::string name = orderstate::orderName(area);
    if (name.empty()) return std::string{};

    const bool isCdx = orderstate::isCdx(area);
    const bool isCnx = orderstate::isCnx(area);

    if (is_classic_tag_area(area) && isCnx) return name;
    if (is_x64_cdx_area(area) && isCdx) return name;

    return std::string{};
}

static std::string default_container_for_flavor(const xbase::DbArea& area) {
    if (is_classic_tag_area(area)) {
        return resolve_index_path(area, "", ".cnx").string();
    }
    if (is_x64_cdx_area(area)) {
        return resolve_index_path(area, "", ".cdx").string();
    }
    return resolve_index_path(area, "", ".cdx").string();
}

static bool validate_explicit_container_for_flavor(const xbase::DbArea& area,
                                                   const std::string& container,
                                                   std::string& err)
{
    err.clear();

    const bool isCdx = ends_with_ci(container, ".CDX");
    const bool isCnx = ends_with_ci(container, ".CNX");
    const bool isInx = ends_with_ci(container, ".INX");

    if (!isCdx && !isCnx && !isInx) {
        err = msg(MessageId::SetOrderUnsupportedIndexContainerText,
                  {{"container", container}});
        return false;
    }

    if (is_classic_tag_area(area)) {
        if (isCdx) {
            err = msg(MessageId::SetOrderV32UsesCnxNotCdxText);
            return false;
        }
        return true;
    }

    if (is_x64_cdx_area(area)) {
        if (!isCdx) {
            err = msg(MessageId::SetOrderV64RequiresCdxText);
            return false;
        }
        return true;
    }

    return true;
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

    // A .cdx under a mounted ramfs root is a native CDX-V64 served from RAM
    // (AIF-043): it has no on-disk container and no LMDB env sidecar. Consult
    // the RAM registry for existence and skip the LMDB env gate entirely; the
    // native backend (openCdx virtual branch) owns the RAM path.
    const bool virtual_cdx = xbase::ramfs::is_virtual(container);

    if (!container_exists(container)) {
        err = msg(MessageId::SetOrderOpenCdxContainerNotFoundText,
                  {{"container", container_path.string()}});
        return false;
    }

    if (!virtual_cdx && (!fs::exists(env_path) || !fs::is_directory(env_path))) {
        err = msg(MessageId::SetOrderOpenCdxEnvMissingText,
                  {{"env", env_path.string()}});
        return false;
    }

    // Critical fix: always release any current backend/handles first.
    xindex::ensure_manager(area).close();
    orderstate::clearOrder(area);

    orderstate::setOrder(area, container);
    orderstate::setActiveTag(area, tag);
    orderstate::setAscending(area, ascending);

    if (!xindex::ensure_manager(area).openCdx(container, tag, &err)) {
        if (err.empty()) {
            err = msg(MessageId::SetOrderOpenCdxBackendOpenFailedText,
                      {{"container", container_path.string()},
                       {"env", env_path.string()}});
        } else {
            err = msg(MessageId::SetOrderOpenCdxBackendOpenFailedDetailText,
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

    if (!container_exists(container)) {
        err = msg(MessageId::SetOrderOpenCnxContainerNotFoundText,
                  {{"container", container}});
        return false;
    }

    // Critical fix: always release any current backend/handles first.
    xindex::ensure_manager(area).close();
    orderstate::clearOrder(area);

    orderstate::setOrder(area, container);
    orderstate::setActiveTag(area, tag);
    orderstate::setAscending(area, ascending);

    if (!xindex::ensure_manager(area).openCnx(container, tag, &err)) {
        if (err.empty()) err = msg(MessageId::SetOrderOpenCnxBackendOpenFailedText);
        orderstate::clearOrder(area);
        xindex::ensure_manager(area).close();
        return false;
    }

    position_to_first_after_order_change(area);
    return true;
}


static void print_setorder_usage()
{
    cli::cmdout::print_message(MessageId::SetOrderUsageText);
}

static bool is_setorder_usage_request(const std::vector<std::string>& toks)
{
    if (toks.size() != 1) return false;
    const std::string u = up_copy(toks[0]);
    return u == "USAGE" || u == "HELP" || u == "?";
}

// ---------- command implementation -------------------------------------------

void cmd_SETORDER(xbase::DbArea& currentArea, std::istringstream& args)
{
    std::vector<std::string> toks;
    for (std::string t; args >> t; ) toks.push_back(t);

    if (is_setorder_usage_request(toks)) {
        print_setorder_usage();
        return;
    }

    if (toks.empty()) {
        if (!orderstate::hasOrder(currentArea)) {
            cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderNonePhysicalText);
            return;
        }

        const std::string name = orderstate::orderName(currentArea);
        const bool asc = orderstate::isAscending(currentArea);
        const std::string tag = orderstate::activeTag(currentArea);

        std::string typeStr = "unknown";
        if (orderstate::isCnx(currentArea)) typeStr = "CNX";
        else if (orderstate::isCdx(currentArea)) typeStr = "CDX";
        else if (ends_with_ci(name, ".INX")) typeStr = "INX";

        std::string tag_clause;
        if (!tag.empty()) {
            tag_clause = msg(MessageId::SetOrderTagClauseText, {{"tag", tag}});
        }
        cli::cmdout::print_prefixed_message(
            "SET ORDER",
            MessageId::SetOrderStatusText,
            {{"type", typeStr},
             {"name", name},
             {"tag_clause", tag_clause},
             {"direction", asc ? "ASC" : "DESC"}});
        return;
    }

    std::size_t i = 0;
    if (i < toks.size() && ieq(toks[i], "TO")) ++i;
    if (i >= toks.size()) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderMissingTargetText);
        return;
    }

    xbase::DbArea* target = &currentArea;
    if (toks.size() >= 2) {
        for (std::size_t k = i; k + 1 < toks.size(); ++k) {
            if (ieq(toks[k], "IN")) {
                auto* eng = shell_engine();
                if (!eng) {
                    cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderEngineUnavailableText);
                    return;
                }
                int areaIdx = resolve_area_index_by_name(*eng, toks[k + 1]);
                if (areaIdx < 0) {
                    cli::cmdout::print_prefixed_message(
                        "SET ORDER",
                        MessageId::SetOrderUnknownAreaAliasText,
                        {{"alias", toks[k + 1]}});
                    return;
                }
                target = &eng->area(areaIdx);
                toks.erase(toks.begin() + static_cast<std::ptrdiff_t>(k),
                           toks.begin() + static_cast<std::ptrdiff_t>(k + 2));
                break;
            }
        }
    }

    if (!target->isOpen()) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderNoTableOpenTargetAreaText);
        return;
    }

    i = 0;
    if (i < toks.size() && ieq(toks[i], "TO")) ++i;
    if (i >= toks.size()) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderMissingTargetText);
        return;
    }

    {
        int n = 0;
        if (is_integer(toks[i], n)) {
            if (n == 0) {
                clear_order_and_close_indexes(*target);
                cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderClearedPhysicalText);
                return;
            }
            cli::cmdout::print_prefixed_message(
                "SET ORDER",
                MessageId::SetOrderNumericNotImplementedText,
                {{"number", std::to_string(n)}});
            return;
        }

        const std::string u = up_copy(toks[i]);
        if (u == "PHYSICAL" || u == "NATURAL" || u == "PHYS") {
            clear_order_and_close_indexes(*target);
            cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderClearedPhysicalText);
            return;
        }
    }

    bool ascending = true;
    if (!toks.empty() && is_direction_token(toks.back())) {
        parse_direction_token(toks.back(), ascending);
        toks.pop_back();
    }

    i = 0;
    if (i < toks.size() && ieq(toks[i], "TO")) ++i;
    if (i >= toks.size()) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderMissingTargetText);
        return;
    }

    std::string container;
    std::string tag;

    if (ieq(toks[i], "TAG")) {
        if (i + 1 >= toks.size()) {
            cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderMissingTagNameAfterTagText);
            return;
        }
        tag = up_copy(toks[i + 1]);

        container = preferred_attached_container_for_flavor(*target);
        if (container.empty()) {
            container = default_container_for_flavor(*target);
        }
    }
    else if (i + 1 == toks.size()) {
        if (looks_like_container_token(toks[i])) {
            cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderExpectsTagNotContainerText);
            cli::cmdout::print_message(MessageId::SetOrderUseTitleText);
            cli::cmdout::print_line("  SET INDEX TO " + toks[i]);
            cli::cmdout::print_line("  SET ORDER TO TAG <tag>");
            return;
        }

        tag = up_copy(toks[i]);

        container = preferred_attached_container_for_flavor(*target);
        if (container.empty()) {
            container = default_container_for_flavor(*target);
        }
    }
    else {
        const std::string first = toks[i];
        const std::string second = toks[i + 1];

        const std::string defaultExt = is_classic_tag_area(*target) ? ".cnx" : ".cdx";
        container = resolve_index_path(*target, first, defaultExt).string();
        tag = up_copy(second);

        std::string flavorErr;
        if (!validate_explicit_container_for_flavor(*target, container, flavorErr)) {
            cli::cmdout::print_line("SET ORDER: " + flavorErr);
            return;
        }
    }

    if (container.empty()) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderUnableResolveContainerText);
        return;
    }

    if (tag.empty()) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderMissingTagText);
        return;
    }

    if (!container_exists(container)) {
        cli::cmdout::print_prefixed_message(
            "SET ORDER",
            MessageId::SetOrderFileNotFoundText,
            {{"path", container}});
        return;
    }

    const bool isCdx = ends_with_ci(container, ".CDX");
    const bool isCnx = ends_with_ci(container, ".CNX");
    const bool isInx = ends_with_ci(container, ".INX");

    if (isInx) {
        cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderInxNotImplementedText);
        cli::cmdout::print_line("Use SET INDEX TO <file>.inx for single-order attachment.");
        return;
    }

    std::string err;
    bool ok = false;

    if (isCdx) {
        if (!cdx_has_tag(container, tag, err)) {
            cli::cmdout::print_line("SET ORDER: " + err);
            return;
        }

        ok = activate_cdx_on_area(*target, container, tag, ascending, err);
    } else if (isCnx) {
        if (!cnx_has_tag(*target, tag)) {
            cli::cmdout::print_prefixed_message(
                "SET ORDER",
                MessageId::SetOrderTagNotAvailableForCnxText,
                {{"tag", tag}});
            return;
        }

        ok = activate_cnx_on_area(*target, container, tag, ascending, err);
    } else {
        cli::cmdout::print_prefixed_message(
            "SET ORDER",
            MessageId::SetOrderUnsupportedIndexContainerText,
            {{"container", container}});
        return;
    }

    if (!ok) {
        if (err.empty()) {
            cli::cmdout::print_prefixed_message("SET ORDER", MessageId::SetOrderUnableActivateOrderText);
        } else {
            cli::cmdout::print_line("SET ORDER: " + err);
        }
        return;
    }

    cli::cmdout::print_prefixed_message(
        "SET ORDER",
        MessageId::SetOrderActivatedText,
        {{"kind", isCnx ? "CNX" : "CDX"},
         {"tag", tag},
         {"direction", orderstate::isAscending(*target) ? "ASC" : "DESC"}});
}
