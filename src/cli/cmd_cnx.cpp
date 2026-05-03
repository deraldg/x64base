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

#include "xbase.hpp"
#include "cnx/cnx.hpp"
#include "cli/path_resolver.hpp"
#include "cli/order_state.hpp"

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
    std::cout
        << "CNX INFO [<path.cnx>]\n"
        << "CNX TAGS [<path.cnx>]\n"
        << "CNX CREATE [<path.cnx>]\n"
        << "CNX ADDTAG <name> [<path.cnx>]\n"
        << "CNX DROPTAG <name> [<path.cnx>]\n"
        << "CNX WALK <tag> [<path.cnx>]\n";
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
        std::cout << "CNX WALK: unable to open: \"" << target.string() << "\"\n";
        return false;
    }

    std::vector<cnxfile::TagInfo> tags;
    if (!cnxfile::read_tagdir(h, tags)) {
        std::cout << "CNX WALK: failed to read tag directory.\n";
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
        std::cout << "CNX WALK: tag not found: " << tag_name_upper << "\n";
        cnxfile::close(h);
        return false;
    }

    std::cout << "CNX WALK: file=\"" << target.string() << "\""
              << "  tag=" << found->name
              << "  root_off=" << found->root_page_off
              << "  stats_rec=" << found->stats_rec
              << "\n";

    const auto psz = cnxfile::page_size(h);
    if (psz) {
        std::cout << "CNX WALK: page_size=" << *psz << "\n";
    }

    if (found->root_page_off == 0) {
        std::cout << "CNX WALK: root_page_off is 0\n";
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

    if (SUB == "HELP" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        print_help();
        return;
    }

    if (SUB == "CREATE") {
        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            std::cout << "CNX CREATE: unable to resolve path.\n";
            return;
        }
        if (file_exists(target)) {
            std::cout << "CNX CREATE: file already exists: \"" << target.string() << "\"\n";
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            std::cout << "CNX CREATE: open/create failed.\n";
            return;
        }
        cnxfile::CNXHeader hdr{};
        (void)cnxfile::read_header(h, hdr);
        cnxfile::close(h);

        std::cout << "CNX created: \"" << target.string() << "\"\n";
        return;
    }

    if (SUB == "INFO" || SUB == "TAGS") {
        fs::path target;
        (void)resolve_target_path(area, args, target);

        if (!file_exists(target)) {
            std::cout << "CNX: file not found: \"" << target.string() << "\"\n";
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            std::cout << "CNX: unable to open: \"" << target.string() << "\"\n";
            return;
        }

        if (SUB == "INFO") {
            cnxfile::CNXHeader hdr{};
            if (!cnxfile::read_header(h, hdr)) {
                std::cout << "CNX INFO: invalid header.\n";
                cnxfile::close(h);
                return;
            }

            std::vector<cnxfile::TagInfo> tags;
            (void)cnxfile::read_tagdir(h, tags);

            std::cout << "CNX file : " << target.string() << "\n";
            std::cout << "Tags     : " << tags.size() << "\n";
            for (const auto& t : tags) {
                std::cout << "  [" << t.tag_id << "] " << t.name
                          << "  root_off=" << t.root_page_off
                          << "  recs=" << t.stats_rec
                          << "\n";
            }
            cnxfile::close(h);
            return;
        }

        std::vector<cnxfile::TagInfo> tags;
        if (!cnxfile::read_tagdir(h, tags)) {
            std::cout << "CNX TAGS: read failed.\n";
            cnxfile::close(h);
            return;
        }
        if (tags.empty()) {
            std::cout << "(no tags)\n";
        } else {
            for (const auto& t : tags) {
                std::cout << "  [" << t.tag_id << "] " << t.name << "\n";
            }
        }
        cnxfile::close(h);
        return;
    }

    if (SUB == "WALK" || SUB == "TRACE") {
        std::string tag;
        args >> tag;
        if (tag.empty()) {
            std::cout << "CNX WALK: missing <tag>.\n";
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            std::cout << "CNX WALK: unable to resolve path.\n";
            return;
        }
        if (!file_exists(target)) {
            std::cout << "CNX: file not found: \"" << target.string() << "\"\n";
            return;
        }

        (void)walk_tag_run1(target, up_copy(tag));
        return;
    }

    if (SUB == "ADDTAG") {
        std::string name;
        args >> name;
        if (name.empty()) {
            std::cout << "CNX ADDTAG: missing <name>.\n";
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            std::cout << "CNX ADDTAG: unable to resolve path.\n";
            return;
        }
        if (!file_exists(target)) {
            std::cout << "CNX: file not found: \"" << target.string() << "\"\n";
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            std::cout << "CNX ADDTAG: open failed.\n";
            return;
        }

        const std::string up = up_copy(name);
        if (!cnxfile::add_tag(h, up)) {
            std::cout << "CNX ADDTAG: tag already exists.\n";
            cnxfile::close(h);
            return;
        }

        cnxfile::close(h);
        std::cout << "CNX ADDTAG: added '" << up << "'.\n";
        return;
    }

    if (SUB == "DROPTAG") {
        std::string name;
        args >> name;
        if (name.empty()) {
            std::cout << "CNX DROPTAG: missing <name>.\n";
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            std::cout << "CNX DROPTAG: unable to resolve path.\n";
            return;
        }
        if (!file_exists(target)) {
            std::cout << "CNX: file not found: \"" << target.string() << "\"\n";
            return;
        }

        CNXHandle* h = nullptr;
        if (!cnxfile::open(target.string(), h)) {
            std::cout << "CNX DROPTAG: open failed.\n";
            return;
        }

        const std::string up = up_copy(name);
        if (!cnxfile::drop_tag(h, up)) {
            std::cout << "CNX DROPTAG: not found.\n";
            cnxfile::close(h);
            return;
        }

        cnxfile::close(h);
        std::cout << "CNX DROPTAG: removed '" << up << "'.\n";
        return;
    }

    std::cout << "CNX: unknown subcommand: " << sub << "\n";
}
