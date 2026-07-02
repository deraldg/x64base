// src/cli/cmd_cnx.cpp
// CNX utility command (CREATE/INFO/TAGS/ADDTAG/DROPTAG/WALK)
//
// Behavior:
//   - ". cnx" with no args prints help/options and returns.
//   - CREATE: refuse if file exists.
//   - INFO/TAGS/ADDTAG/DROPTAG/WALK: require existing file.
//   - Default path (no path arg):
//       1) if area has active CNX in orderstate: use it
//       2) else <current_dbf_basename>.cnx resolved via INDEXES slot
//
// WALK notes:
//   - Read-only diagnostic
//   - Uses root_page_off from the CNX tag directory
//   - Prints RUN1 header/body summary
//   - Follows plausible child offsets recursively with loop/depth protection
//   - Does NOT modify CNX or replace backend traversal

// @dottalk.usage v1
// owner: DOT|CNX
// command: CNX
// category: index
// status: supported
// noargs: usage
// effect: mixed
// mutates: index-metadata filesystem
// usage-access: CNX USAGE
// summary:
//   Manage CNX index container metadata: create containers, inspect header/tag
//   directories, add/drop tags, and walk/trace RUN1 tag structures.
//
// usage:
//   CNX USAGE
//   CNX INFO [<path.cnx>]
//   CNX TAGS [<path.cnx>]
//   CNX CREATE [<path.cnx>]
//   CNX ADDTAG <name> [<path.cnx>]
//   CNX DROPTAG <name> [<path.cnx>]
//   CNX WALK <tag> [<path.cnx>]
//   CNX TRACE <tag> [<path.cnx>]
//
// notes:
//   CNX with no arguments shows usage.
//   If no path is supplied, CNX first uses the active CNX path from order state when available.
//   Otherwise CNX derives <current_dbf_basename>.cnx through the INDEXES path slot.
//   CREATE refuses to overwrite an existing file.
//   INFO, TAGS, WALK, and TRACE are read-only inspection/diagnostic operations and require an existing file.
//   WALK/TRACE use root_page_off from the CNX tag directory and follow plausible child offsets with loop/depth protection.
//   ADDTAG and DROPTAG mutate the CNX container tag directory and require an existing file.
//
// risk:
//   reads_index_file: INFO TAGS WALK TRACE ADDTAG DROPTAG
//   creates_index_file: CREATE
//   overwrites_index_file: no, CREATE refuses existing target
//   mutates_index_metadata: ADDTAG DROPTAG
//   mutates_table_data: no
//   diagnostic_tree_walk: WALK TRACE
//   default_path_uses_order_state: yes
//   default_path_uses_indexes_slot: yes
//
// related:
//   CDX
//   INDEX
//   SET CNX
//   SET ORDER
//   REINDEX
//

#include "xbase.hpp"
#include "cnx/cnx.hpp"
#include "cli/command_output.hpp"
#include "cli/path_resolver.hpp"
#include "cli/order_state.hpp"
#include "help/helpdata_messages.hpp"

#include <algorithm>
#include <cctype>
#include <cstdio>
#include <cstring>
#include <filesystem>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <system_error>
#include <unordered_set>
#include <vector>

namespace fs = std::filesystem;
using cnxfile::CNXHandle;

namespace {

static inline std::string trim_copy(std::string s)
{
    auto issp = [](unsigned char c){ return std::isspace(c)!=0; };
    while (!s.empty() && issp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && issp((unsigned char)s.back()))  s.pop_back();
    return s;
}

static inline std::string up_copy(std::string s)
{
    for (auto& c : s) c = (char)std::toupper((unsigned char)c);
    return s;
}

static inline bool file_exists(const fs::path& p)
{
    std::error_code ec;
    return fs::exists(p, ec);
}

static fs::path resolve_cnx_token(const std::string& tok)
{
    fs::path p = dottalk::paths::resolve_index(tok);
    if (!p.has_extension()) p.replace_extension(".cnx");
    return p;
}

static fs::path default_cnx_path(xbase::DbArea& area)
{
    if (orderstate::hasOrder(area) && orderstate::isCnx(area)) {
        const std::string active = orderstate::orderName(area);
        if (!active.empty()) return fs::path(active);
    }

    std::string stem;
    if (area.isOpen()) {
        stem = area.dbfBasename();
        if (stem.empty()) stem = area.logicalName();
        if (stem.empty()) {
            fs::path n(area.name());
            stem = n.stem().string();
        }
        if (stem.empty()) stem = "table";
    } else {
        stem = "table";
    }

    fs::path p = resolve_cnx_token(stem);
    if (!p.has_extension()) p.replace_extension(".cnx");
    return p;
}

static bool resolve_target_path(xbase::DbArea& area,
                                std::istringstream& args,
                                fs::path& out)
{
    std::string rest;
    std::getline(args, rest);
    rest = trim_copy(rest);

    if (rest.empty()) {
        out = default_cnx_path(area);
        return !out.empty();
    }

    std::string first = rest;
    auto sp = first.find_first_of(" 	");
    if (sp != std::string::npos) first = trim_copy(first.substr(0, sp));

    fs::path p = resolve_cnx_token(first);
    if (!p.has_extension()) p.replace_extension(".cnx");
    out = p;
    return true;
}

static void print_help()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CnxUsageText);
}

static std::uint32_t rd_u32_le(const unsigned char* p)
{
    return static_cast<std::uint32_t>(p[0])
         | (static_cast<std::uint32_t>(p[1]) << 8)
         | (static_cast<std::uint32_t>(p[2]) << 16)
         | (static_cast<std::uint32_t>(p[3]) << 24);
}

static std::string hex_ascii_summary(const std::vector<unsigned char>& buf,
                                     std::size_t start,
                                     std::size_t n)
{
    std::ostringstream os;
    if (start >= buf.size()) {
        os << "hex=  ascii=\"\"";
        return os.str();
    }

    const std::size_t end = std::min(start + n, buf.size());

    os << "hex=";
    for (std::size_t i = start; i < end; ++i) {
        if (i > start) os << ' ';
        char tmp[4];
        std::snprintf(tmp, sizeof(tmp), "%02X", static_cast<unsigned>(buf[i]));
        os << tmp;
    }

    os << "  ascii=\"";
    for (std::size_t i = start; i < end; ++i) {
        const unsigned char c = buf[i];
        os << (std::isprint(c) ? static_cast<char>(c) : '.');
    }
    os << '"';
    return os.str();
}

struct Run1Header {
    char magic[4]{};
    std::uint32_t version{0};
    std::uint32_t tag_id{0};
    std::uint32_t flags{0};
    std::uint32_t reserved0{0};
    std::uint32_t rec_count{0};
    std::uint32_t reserved1{0};
    std::uint32_t run_bytes{0};
};

static bool parse_run1_header(const std::vector<unsigned char>& buf, Run1Header& h)
{
    if (buf.size() < 32) return false;
    std::memcpy(h.magic, buf.data(), 4);
    if (std::memcmp(h.magic, "RUN1", 4) != 0) return false;

    h.version   = rd_u32_le(buf.data() + 4);
    h.tag_id    = rd_u32_le(buf.data() + 8);
    h.flags     = rd_u32_le(buf.data() + 12);
    h.reserved0 = rd_u32_le(buf.data() + 16);
    h.rec_count = rd_u32_le(buf.data() + 20);
    h.reserved1 = rd_u32_le(buf.data() + 24);
    h.run_bytes = rd_u32_le(buf.data() + 28);
    return true;
}

static std::string indent_of(int depth)
{
    return std::string(static_cast<std::size_t>(depth) * 2u, ' ');
}

static std::vector<std::uint64_t> collect_plausible_child_offsets(const std::vector<unsigned char>& buf,
                                                                  const Run1Header& h,
                                                                  std::optional<std::uint32_t> page_sz_opt)
{
    std::vector<std::uint64_t> out;
    const std::size_t scan_end = std::min<std::size_t>(buf.size(), h.run_bytes);

    const std::uint32_t page_sz = page_sz_opt.value_or(16);

    for (std::size_t off = 32; off + 4 <= scan_end; off += 4) {
        const std::uint32_t v = rd_u32_le(buf.data() + off);

        if (v > h.rec_count && v >= 64 && (v % page_sz == 0 || v % 16 == 0)) {
            if (out.empty() || out.back() != v) {
                out.push_back(v);
            }
        }
    }
    return out;
}

static void walk_run1_node(CNXHandle* h,
                           std::uint64_t off,
                           int depth,
                           int max_depth,
                           std::unordered_set<std::uint64_t>& visited,
                           std::optional<std::uint32_t> page_sz_opt)
{
    const std::string ind = indent_of(depth);

    if (depth > max_depth) {
        std::cout << ind << "(max depth reached at off=" << off << ")\n";
        return;
    }

    if (visited.find(off) != visited.end()) {
        std::cout << ind << "(already visited off=" << off << ")\n";
        return;
    }
    visited.insert(off);

    std::vector<unsigned char> buf(256);
    if (!cnxfile::read_at(h, off, buf.data(), buf.size())) {
        std::cout << ind << "READ FAILED off=" << off << "\n";
        return;
    }

    Run1Header hdr{};
    if (!parse_run1_header(buf, hdr)) {
        std::cout << ind << "NODE off=" << off << "  "
                  << hex_ascii_summary(buf, 0, 32) << "\n";
        return;
    }

    std::cout << ind << "RUN1 NODE off=" << off
              << " ver=" << hdr.version
              << " tag_id=" << hdr.tag_id
              << " flags=" << hdr.flags
              << " recs=" << hdr.rec_count
              << " run_bytes=" << hdr.run_bytes
              << "\n";

    std::cout << ind << "  BODY first_u32=";
    bool first = true;
    for (std::size_t pos = 32; pos + 4 <= buf.size() && pos < 64; pos += 4) {
        const std::uint32_t v = rd_u32_le(buf.data() + pos);
        if (!first) std::cout << ",";
        std::cout << v;
        first = false;
    }
    std::cout << "\n";

    const auto kids = collect_plausible_child_offsets(buf, hdr, page_sz_opt);

    if (kids.empty()) {
        std::cout << ind << "  plausible_children=(none)\n";
        return;
    }

    std::cout << ind << "  plausible_children=";
    for (std::size_t i = 0; i < kids.size(); ++i) {
        if (i) std::cout << ",";
        std::cout << kids[i];
    }
    std::cout << "\n";

    const std::size_t limit = std::min<std::size_t>(kids.size(), 3);
    for (std::size_t i = 0; i < limit; ++i) {
        walk_run1_node(h, kids[i], depth + 1, max_depth, visited, page_sz_opt);
    }
}

static bool walk_tag_run1(const fs::path& target, const std::string& tag_name_upper)
{
    CNXHandle* h = nullptr;
    if (!cnxfile::open(target.string(), h) || !h) {
        cli::cmdout::print_prefixed_message(
            "CNX WALK", dottalk::helpdata::MessageId::CnxWalkUnableOpenText,
            {{"path", target.string()}});
        return false;
    }

    std::vector<cnxfile::TagInfo> tags;
    if (!cnxfile::read_tagdir(h, tags)) {
        cli::cmdout::print_prefixed_message(
            "CNX WALK", dottalk::helpdata::MessageId::CnxWalkReadTagDirectoryFailedText);
        cnxfile::close(h);
        return false;
    }

    const cnxfile::TagInfo* found = nullptr;
    for (const auto& t : tags) {
        if (up_copy(t.name) == tag_name_upper) {
            found = &t;
            break;
        }
    }

    if (!found) {
        cli::cmdout::print_prefixed_message(
            "CNX WALK", dottalk::helpdata::MessageId::CnxWalkTagNotFoundText,
            {{"tag", tag_name_upper}});
        cnxfile::close(h);
        return false;
    }

    cli::cmdout::print_prefixed_message(
        "CNX WALK", dottalk::helpdata::MessageId::CnxWalkFileSummaryText,
        {
            {"path", target.string()},
            {"tag", found->name},
            {"root_off", std::to_string(found->root_page_off)},
            {"stats_rec", std::to_string(found->stats_rec)}
        });

    const auto psz = cnxfile::page_size(h);
    if (psz) {
        cli::cmdout::print_prefixed_message(
            "CNX WALK", dottalk::helpdata::MessageId::CnxWalkPageSizeText,
            {{"size", std::to_string(*psz)}});
    }

    if (found->root_page_off == 0) {
        cli::cmdout::print_prefixed_message(
            "CNX WALK", dottalk::helpdata::MessageId::CnxWalkRootZeroText);
        cnxfile::close(h);
        return false;
    }

    std::unordered_set<std::uint64_t> visited;
    walk_run1_node(h, found->root_page_off, 0, 4, visited, psz);

    cnxfile::close(h);
    return true;
}

} // namespace

// ---- command ----
void cmd_CNX(xbase::DbArea& area, std::istringstream& args)
{
    std::string sub;
    args >> sub;

    if (sub.empty()) {
        print_help();
        return;
    }

    std::string SUB = up_copy(sub);

    if (SUB == "USAGE" || SUB == "HELP" || SUB == "?" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        print_help();
        return;
    }

    if (SUB == "CREATE") {
        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CNX CREATE", dottalk::helpdata::MessageId::CnxCreateUnableResolvePathText);
            return;
        }
        if (file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CNX CREATE", dottalk::helpdata::MessageId::CnxCreateFileExistsText,
                {{"path", target.string()}});
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CNX CREATE", dottalk::helpdata::MessageId::CnxCreateOpenFailedText);
            return;
        }
        cnxfile::CNXHeader hdr{};
        (void)cnxfile::read_header(h, hdr);
        cnxfile::close(h);

        cli::cmdout::print_prefixed_message(
            "CNX", dottalk::helpdata::MessageId::CnxCreatedText,
            {{"path", target.string()}});
        return;
    }

    if (SUB == "INFO" || SUB == "TAGS") {
        fs::path target;
        (void)resolve_target_path(area, args, target);

        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CNX", dottalk::helpdata::MessageId::CnxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CNX", dottalk::helpdata::MessageId::CnxUnableOpenText,
                {{"path", target.string()}});
            return;
        }

        if (SUB == "INFO") {
            cnxfile::CNXHeader hdr{};
            if (!cnxfile::read_header(h, hdr)) {
                cli::cmdout::print_prefixed_message(
                    "CNX INFO", dottalk::helpdata::MessageId::CnxInfoInvalidHeaderText);
                cnxfile::close(h);
                return;
            }

            std::vector<cnxfile::TagInfo> tags;
            (void)cnxfile::read_tagdir(h, tags);

            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CnxInfoFileLineText,
                {{"path", target.string()}});
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CnxInfoTagsLineText,
                {{"count", std::to_string(tags.size())}});
            for (const auto& t : tags) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CnxInfoTagLineText,
                    {
                        {"tag_id", std::to_string(t.tag_id)},
                        {"name", t.name},
                        {"root_off", std::to_string(t.root_page_off)},
                        {"recs", std::to_string(t.stats_rec)}
                    });
            }
            cnxfile::close(h);
            return;
        }

        std::vector<cnxfile::TagInfo> tags;
        if (!cnxfile::read_tagdir(h, tags)) {
            cli::cmdout::print_prefixed_message(
                "CNX TAGS", dottalk::helpdata::MessageId::CnxTagsReadFailedText);
            cnxfile::close(h);
            return;
        }
        if (tags.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::CnxNoTagsText);
        } else {
            for (const auto& t : tags) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CnxTagLineText,
                    {{"tag_id", std::to_string(t.tag_id)}, {"name", t.name}});
            }
        }
        cnxfile::close(h);
        return;
    }

    if (SUB == "WALK" || SUB == "TRACE") {
        std::string tag;
        args >> tag;
        if (tag.empty()) {
            cli::cmdout::print_prefixed_message(
                "CNX WALK", dottalk::helpdata::MessageId::CnxWalkMissingTagText);
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CNX WALK", dottalk::helpdata::MessageId::CnxWalkUnableResolvePathText);
            return;
        }
        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CNX", dottalk::helpdata::MessageId::CnxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        (void)walk_tag_run1(target, up_copy(tag));
        return;
    }

    if (SUB == "ADDTAG") {
        std::string name;
        args >> name;
        if (name.empty()) {
            cli::cmdout::print_prefixed_message(
                "CNX ADDTAG", dottalk::helpdata::MessageId::CnxAddTagMissingNameText);
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CNX ADDTAG", dottalk::helpdata::MessageId::CnxAddTagUnableResolvePathText);
            return;
        }
        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CNX", dottalk::helpdata::MessageId::CnxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CNX ADDTAG", dottalk::helpdata::MessageId::CnxAddTagOpenFailedText);
            return;
        }

        const std::string up = up_copy(name);
        if (!cnxfile::add_tag(h, up)) {
            cli::cmdout::print_prefixed_message(
                "CNX ADDTAG", dottalk::helpdata::MessageId::CnxAddTagAlreadyExistsText);
            cnxfile::close(h);
            return;
        }

        cnxfile::close(h);
        cli::cmdout::print_prefixed_message(
            "CNX ADDTAG", dottalk::helpdata::MessageId::CnxAddTagAddedText,
            {{"tag", up}});
        return;
    }

    if (SUB == "DROPTAG") {
        std::string name;
        args >> name;
        if (name.empty()) {
            cli::cmdout::print_prefixed_message(
                "CNX DROPTAG", dottalk::helpdata::MessageId::CnxDropTagMissingNameText);
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CNX DROPTAG", dottalk::helpdata::MessageId::CnxDropTagUnableResolvePathText);
            return;
        }
        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CNX", dottalk::helpdata::MessageId::CnxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CNX DROPTAG", dottalk::helpdata::MessageId::CnxDropTagOpenFailedText);
            return;
        }

        const std::string up = up_copy(name);
        if (!cnxfile::drop_tag(h, up)) {
            cli::cmdout::print_prefixed_message(
                "CNX DROPTAG", dottalk::helpdata::MessageId::CnxDropTagNotFoundText);
            cnxfile::close(h);
            return;
        }

        cnxfile::close(h);
        cli::cmdout::print_prefixed_message(
            "CNX DROPTAG", dottalk::helpdata::MessageId::CnxDropTagRemovedText,
            {{"tag", up}});
        return;
    }

    cli::cmdout::print_prefixed_message(
        "CNX", dottalk::helpdata::MessageId::CnxUnknownSubcommandText,
        {{"subcommand", sub}});
}
