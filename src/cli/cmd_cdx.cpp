// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_cdx.cpp
// CDX utility command (CREATE/INFO/TAGS/ADDTAG/DROPTAG)
//
// Behavior change requested:
//   - If invoked with no arguments (". cdx"), print help/options and return.
//     (Do NOT default to INFO.)
//
// Policy enforced:
//   - CREATE: refuse if file exists.
//   - INFO/TAGS/ADDTAG/DROPTAG: require existing file (no implicit creation).
//   - ADDTAG: additionally requires an open table, and refuses a name that is not
//     one of its fields. See the block at the ADDTAG branch for why this is at
//     definition time rather than at build time.
//   - Default path (no path arg):
//       1) if area has active CDX in orderstate: use it
//       2) else <current_dbf_basename>.cdx resolved via INDEXES slot
//
// Notes:
//   - Tag build data (RUN1) persistence is handled by cdx backend; this command
//     is only for container header + tag directory management.

// @dottalk.usage v1
// owner: DOT|CDX
// command: CDX
// category: index
// status: supported
// noargs: usage
// effect: mixed
// mutates: index-metadata filesystem
// usage-access: CDX USAGE
// summary:
//   Manage CDX index container metadata: create containers, inspect header/tag
//   directories, add tags, and drop tags.
//
// usage:
//   CDX USAGE
//   CDX INFO [<path.cdx>]
//   CDX TAGS [<path.cdx>]
//   CDX CREATE [<path.cdx>]
//   CDX ADDTAG <name> [<path.cdx>]
//   CDX DROPTAG <name> [<path.cdx>]
//
// notes:
//   CDX with no arguments shows usage and does not default to INFO.
//   If no path is supplied, CDX first uses the active CDX path from order state when available.
//   Otherwise CDX derives <current_dbf_basename>.cdx through the INDEXES path slot.
//   CREATE refuses to overwrite an existing file.
//   INFO and TAGS are read-only inspection operations and require an existing file.
//   ADDTAG and DROPTAG mutate the CDX container tag directory and require an existing file.
//   ADDTAG requires an OPEN TABLE and refuses a <name> that does not resolve to one of its
//     fields, through the same standard resolver REPLACE uses (xfg::resolve_field_index_std):
//     a CDX tag IS a field name, and BUILDLMDB builds each tag FROM the field of that name.
//     Before 2026-08-29 any string was accepted here and the miss was swallowed at BUILD time
//     without a message, leaving a container carrying a tag nothing would ever fill.
//   DROPTAG is deliberately NOT field-checked: removing a tag whose field is gone is exactly
//     when you need it, so requiring the field to exist would fence off the repair.
//   CDX manages container header/tag metadata; backend tag build data persistence is owned elsewhere.
//
// risk:
//   reads_index_file: INFO TAGS ADDTAG DROPTAG
//   creates_index_file: CREATE
//   overwrites_index_file: no, CREATE refuses existing target
//   mutates_index_metadata: ADDTAG DROPTAG
//   requires_open_table: ADDTAG
//   validates_field_name: ADDTAG (xfg::resolve_field_index_std, as REPLACE does)
//   mutates_table_data: no
//   default_path_uses_order_state: yes
//   default_path_uses_indexes_slot: yes
//
// related:
//   CNX
//   INDEX
//   SET CDX
//   SET ORDER
//   REINDEX
//

#include "xbase.hpp"
#include "xbase/ramfs.hpp"
#include "cdx/cdx.hpp"
#include "cli/command_output.hpp"
#include "cli/path_resolver.hpp"
#include "cli/order_state.hpp"
#include "help/helpdata_messages.hpp"
#include "xbase_field_getters.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <sstream>
#include <string>
#include <system_error>
#include <vector>

namespace fs = std::filesystem;
using cdxfile::CDXHandle;

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
    // A CDX container under a mounted ramfs root lives only in RAM (AIF-043),
    // so a plain disk fs::exists would wrongly report it missing. Consult the
    // ramfs registry first for virtual paths, then fall back to disk.
    if (xbase::ramfs::is_virtual(p.string())) {
        return xbase::ramfs::exists(p.string());
    }
    std::error_code ec;
    return fs::exists(p, ec);
}

static fs::path resolve_cdx_token(const std::string& tok)
{
    fs::path p = dottalk::paths::resolve_index(tok);
    if (!p.has_extension()) p.replace_extension(".cdx");
    return p;
}

static fs::path default_cdx_path(xbase::DbArea& area)
{
    // 1) If a CDX is currently active in orderstate, reuse its path directly.
    if (orderstate::hasOrder(area) && orderstate::isCnx(area)) {
        const std::string active = orderstate::orderName(area);
        if (!active.empty()) return fs::path(active);
    }

    // 2) Otherwise, if a table is open, use dbfBasename/logicalName/name-stem.
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

    fs::path p = resolve_cdx_token(stem);
    if (!p.has_extension()) p.replace_extension(".cdx");
    return p;
}

// Parse optional path (first token from remainder). If none, use default policy.
static bool resolve_target_path(xbase::DbArea& area,
                                std::istringstream& args,
                                fs::path& out)
{
    std::string rest;
    std::getline(args, rest);
    rest = trim_copy(rest);

    if (rest.empty()) {
        out = default_cdx_path(area);
        return !out.empty();
    }

    // first token = path-ish
    std::string first = rest;
    auto sp = first.find_first_of(" \t");
    if (sp != std::string::npos) first = trim_copy(first.substr(0, sp));

    fs::path p = resolve_cdx_token(first);
    if (!p.has_extension()) p.replace_extension(".cdx");
    out = p;
    return true;
}

static void print_help()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CdxUsageText);
}

} // namespace

// ---- command ----
void cmd_CDX(xbase::DbArea& area, std::istringstream& args)
{
    std::string sub;
    args >> sub;

    // NEW: ". cdx" (no args) prints options/help and returns.
    if (sub.empty()) {
        print_help();
        return;
    }

    std::string SUB = up_copy(sub);

    if (SUB == "USAGE" || SUB == "HELP" || SUB == "?" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        print_help();
        return;
    }

    // ---------------- CREATE ----------------
    if (SUB == "CREATE") {
        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CDX CREATE", dottalk::helpdata::MessageId::CdxCreateUnableResolvePathText);
            return;
        }
        if (file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CDX CREATE", dottalk::helpdata::MessageId::CdxCreateFileExistsText,
                {{"path", target.string()}});
            return;
        }

        CDXHandle* h = nullptr;
        if (!cdxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CDX CREATE", dottalk::helpdata::MessageId::CdxCreateOpenFailedText);
            return;
        }
        cdxfile::CDXHeader hdr{};
        (void)cdxfile::read_header(h, hdr);
        cdxfile::close(h);

        cli::cmdout::print_prefixed_message(
            "CDX", dottalk::helpdata::MessageId::CdxCreatedText,
            {{"path", target.string()}});
        return;
    }

    // ---------------- INFO / TAGS ----------------
    if (SUB == "INFO" || SUB == "TAGS") {
        fs::path target;
        (void)resolve_target_path(area, args, target);

        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CDX", dottalk::helpdata::MessageId::CdxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        CDXHandle* h = nullptr;
        if (!cdxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CDX", dottalk::helpdata::MessageId::CdxUnableOpenText,
                {{"path", target.string()}});
            return;
        }

        if (SUB == "INFO") {
            cdxfile::CDXHeader hdr{};
            if (!cdxfile::read_header(h, hdr)) {
                cli::cmdout::print_prefixed_message(
                    "CDX INFO", dottalk::helpdata::MessageId::CdxInfoInvalidHeaderText);
                cdxfile::close(h);
                return;
            }

            std::vector<cdxfile::TagInfo> tags;
            (void)cdxfile::read_tagdir(h, tags);

            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CdxInfoFileLineText,
                {{"path", target.string()}});
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CdxInfoTagsLineText,
                {{"count", std::to_string(tags.size())}});
            for (const auto& t : tags) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CdxInfoTagLineText,
                    {
                        {"tag_id", std::to_string(t.tag_id)},
                        {"name", t.name},
                        {"root_off", std::to_string(t.root_page_off)},
                        {"recs", std::to_string(t.stats_rec)}
                    });
            }
            cdxfile::close(h);
            return;
        }

        // TAGS
        std::vector<cdxfile::TagInfo> tags;
        if (!cdxfile::read_tagdir(h, tags)) {
            cli::cmdout::print_prefixed_message(
                "CDX TAGS", dottalk::helpdata::MessageId::CdxTagsReadFailedText);
            cdxfile::close(h);
            return;
        }
        if (tags.empty()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::CdxNoTagsText);
        } else {
            for (const auto& t : tags) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::CdxTagLineText,
                    {{"tag_id", std::to_string(t.tag_id)}, {"name", t.name}});
            }
        }
        cdxfile::close(h);
        return;
    }

    // ---------------- ADDTAG <name> ----------------
    if (SUB == "ADDTAG") {
        std::string name;
        args >> name;
        if (name.empty()) {
            cli::cmdout::print_prefixed_message(
                "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagMissingNameText);
            return;
        }

        // ------------------------------------------------------------------
        // THE TAG NAME IS A FIELD NAME, SO CHECK IT HERE (AIF-078, 2026-08-29).
        //
        // ADDTAG used to accept ANY string. cmd_buildlmdb.cpp:465-481 --
        // headed "Build one tag from a field name" -- then walked area.fields()
        // looking for a match and gave up on a miss with
        //
        //     if (fld < 1) return false;
        //
        // and NOT ONE WORD PRINTED. Only the total is reported, so a container
        // could carry a tag that nothing would ever fill and BUILDLMDB would
        // still say "done OK=1 tags rebuilt" on the strength of a DIFFERENT
        // tag. Definition time is where a typo is still fixable; build time is
        // too late, the bad tag is already in the container's directory.
        //
        // REPLACE ALREADY HAD THIS RIGHT AND IS THE MODEL. It resolves through
        // xfg::resolve_field_index_std and refuses on -1 (cmd_replace.cpp:822,
        // ReplaceFieldNotFoundText). That resolver is the engine's STANDARD
        // one: it trims, authoritative x64 logical names win, and the 10-byte
        // DBF descriptor token is accepted as an alias when it maps uniquely
        // (include/xbase_field_getters.hpp:117-176). BUILDLMDB's hand-rolled
        // textio::ieq(Fs[i].name, tag) does none of that.
        //
        // SO THERE WERE THREE DECLARATIONS OF WHAT A FIELD NAME IS -- the
        // standard resolver, BUILDLMDB's loop, and ADDTAG's nothing-at-all --
        // and they did not agree. Calling the shared resolver here makes CDX
        // agree with REPLACE rather than adding a fourth opinion. BUILDLMDB's
        // loop is still its own and is NOT changed here: a container written
        // by an older binary, or by hand, can still carry a dead tag, and that
        // is a separate change with its own proof.
        //
        // AN OPEN TABLE IS NOW REQUIRED (owner ruling 2026-08-29). ADDTAG could
        // previously define a tag on a container named by an explicit path with
        // no table open at all. Validating only when the path happens to match
        // the current area would have put the check on every path EXCEPT the
        // one most likely to carry a typo -- a guard that cannot fire, which is
        // the shape this lane keeps finding. BUILDLMDB already requires an open
        // table, so a tag defined without one could not have been built in that
        // session anyway.
        // ------------------------------------------------------------------
        if (!area.isOpen()) {
            cli::cmdout::print_prefixed_message(
                "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagNoFileOpenText);
            return;
        }
        if (xfg::resolve_field_index_std(area, name) < 0) {
            cli::cmdout::print_prefixed_message(
                "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagFieldNotFoundText,
                {{"name", name}});
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagUnableResolvePathText);
            return;
        }
        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CDX", dottalk::helpdata::MessageId::CdxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        CDXHandle* h = nullptr;
        if (!cdxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagOpenFailedText);
            return;
        }

        const std::string up = up_copy(name);
        if (!cdxfile::add_tag(h, up)) {
            cli::cmdout::print_prefixed_message(
                "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagAlreadyExistsText);
            cdxfile::close(h);
            return;
        }

        cdxfile::close(h);
        cli::cmdout::print_prefixed_message(
            "CDX ADDTAG", dottalk::helpdata::MessageId::CdxAddTagAddedText,
            {{"tag", up}});
        return;
    }

    // ---------------- DROPTAG <name> ----------------
    if (SUB == "DROPTAG") {
        std::string name;
        args >> name;
        if (name.empty()) {
            cli::cmdout::print_prefixed_message(
                "CDX DROPTAG", dottalk::helpdata::MessageId::CdxDropTagMissingNameText);
            return;
        }

        fs::path target;
        if (!resolve_target_path(area, args, target)) {
            cli::cmdout::print_prefixed_message(
                "CDX DROPTAG", dottalk::helpdata::MessageId::CdxDropTagUnableResolvePathText);
            return;
        }
        if (!file_exists(target)) {
            cli::cmdout::print_prefixed_message(
                "CDX", dottalk::helpdata::MessageId::CdxFileNotFoundText,
                {{"path", target.string()}});
            return;
        }

        CDXHandle* h = nullptr;
        if (!cdxfile::open(target.string(), h)) {
            cli::cmdout::print_prefixed_message(
                "CDX DROPTAG", dottalk::helpdata::MessageId::CdxDropTagOpenFailedText);
            return;
        }

        const std::string up = up_copy(name);
        if (!cdxfile::drop_tag(h, up)) {
            cli::cmdout::print_prefixed_message(
                "CDX DROPTAG", dottalk::helpdata::MessageId::CdxDropTagNotFoundText);
            cdxfile::close(h);
            return;
        }

        cdxfile::close(h);
        cli::cmdout::print_prefixed_message(
            "CDX DROPTAG", dottalk::helpdata::MessageId::CdxDropTagRemovedText,
            {{"tag", up}});
        return;
    }

    cli::cmdout::print_prefixed_message(
        "CDX", dottalk::helpdata::MessageId::CdxUnknownSubcommandText,
        {{"subcommand", sub}});
}
