// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// ============================================================================
// File: src/cli/helpdata_cmdhelp_bridge.cpp
// Purpose: CLI-side bridge from existing CMDHELP/command docs into HELP DATA v2.
// ============================================================================
#include "helpdata_cmdhelp_bridge.hpp"

#include "../help/helpdata_artifacts.hpp"
#include "../help/helpdata_export_dbf.hpp"
#include "../help/helpdata_source_miner.hpp"

#if __has_include("command_catalog.hpp")
  #include "command_catalog.hpp"
  #define DOTTALK_HELPDATA_HAS_COMMAND_CATALOG 1
#else
  #define DOTTALK_HELPDATA_HAS_COMMAND_CATALOG 0
#endif

#include <algorithm>
#include <vector>
#include <sstream>
#include <set>
#include <map>
#include <fstream>
#include <filesystem>
#include <cctype>
#include <iterator>
#include <string>
#include <utility>

namespace cmdhelp {
namespace hd = dottalk::helpdata;
namespace fs = std::filesystem;

namespace {

static std::string canonicalize_set_family_command_local(const std::string& command);

static hd::SourceKind source_for_catalog(const std::string& catalog)
{
    const std::string cat = hd::upper(catalog);
    if (cat == "FOX") return hd::SourceKind::FoxRef;
    if (cat == "ED")  return hd::SourceKind::EdRef;
    return hd::SourceKind::DotRef;
}

static std::string canonical_artifact_command_name(const std::string& command)
{
    return canonicalize_set_family_command_local(command);
}

static hd::Artifact make_command_status_artifact(const CommandInfo& command)
{
    const std::string catalog = hd::upper(command.catalog.empty() ? std::string("DOT") : command.catalog);
    const std::string name = canonical_artifact_command_name(command.name);

    std::string text = "implemented=";
    text += command.implemented ? "yes" : "no";
    text += "; supported=";
    text += command.supported ? "yes" : "no";

    return hd::make_artifact(catalog,
                             name,
                             { hd::OwnerKind::Command, name },
                             hd::ArtifactKind::Status,
                             hd::SourceKind::Registry,
                             hd::Confidence::Reflected,
                             hd::Severity::Info,
                             "COMMAND_STATUS",
                             text,
                             0);
}

static void append_legacy_catalog_artifacts(const CommandInfo& command,
                                            std::vector<hd::Artifact>& out,
                                            HelpDataV2Counts& counts)
{
    const std::string catalog = hd::upper(command.catalog.empty() ? std::string("DOT") : command.catalog);
    const std::string name = canonical_artifact_command_name(command.name);
    const hd::SourceKind source = source_for_catalog(catalog);

    if (!command.verbose.empty()) {
        out.push_back(hd::make_artifact(catalog,
                                        name,
                                        { hd::OwnerKind::Command, name },
                                        hd::ArtifactKind::Summary,
                                        source,
                                        hd::Confidence::Catalog,
                                        hd::Severity::Info,
                                        "LEGACY_SUMMARY",
                                        command.verbose,
                                        0));
        ++counts.legacy_catalog_rows;
    }

    if (!command.usage.empty()) {
        out.push_back(hd::make_artifact(catalog,
                                        name,
                                        { hd::OwnerKind::Command, name },
                                        hd::ArtifactKind::Syntax,
                                        source,
                                        hd::Confidence::Catalog,
                                        hd::Severity::Info,
                                        "LEGACY_USAGE",
                                        command.usage,
                                        1));
        ++counts.legacy_catalog_rows;
    }
}

#if DOTTALK_HELPDATA_HAS_COMMAND_CATALOG
static void append_command_doc_artifacts(const CommandInfo& command,
                                         std::vector<hd::Artifact>& out,
                                         HelpDataV2Counts& counts)
{
    const std::string catalog = hd::upper(command.catalog.empty() ? std::string("DOT") : command.catalog);
    const std::string name = canonical_artifact_command_name(command.name);
    const dottalk::doc::CommandDoc* doc = dottalk::doc::get(name);
    if (!doc) return;

    auto add = [&](hd::ArtifactKind kind,
                   hd::Severity severity,
                   const std::string& row_name,
                   const std::string& text,
                   int ordinal) {
        if (text.empty()) return;
        out.push_back(hd::make_artifact(catalog,
                                        name,
                                        { hd::OwnerKind::Command, name },
                                        kind,
                                        hd::SourceKind::CuratedDoc,
                                        hd::Confidence::Curated,
                                        severity,
                                        row_name,
                                        text,
                                        ordinal));
        ++counts.curated_doc_rows;
    };

    add(hd::ArtifactKind::Summary, hd::Severity::Info, "SUMMARY", doc->summary, 0);

    int ordinal = 1;
    for (const auto& syntax : doc->syntax) {
        add(hd::ArtifactKind::Syntax, hd::Severity::Info, "SYNTAX", syntax, ordinal++);
    }

    ordinal = 1;
    for (const auto& sample : doc->samples) {
        add(hd::ArtifactKind::Example, hd::Severity::Info, "SAMPLE", sample, ordinal++);
    }

    ordinal = 1;
    for (const auto& note : doc->notes) {
        add(hd::ArtifactKind::Note, hd::Severity::Info, "NOTE", note, ordinal++);
    }

    ordinal = 1;
    for (const auto& warning : doc->warnings) {
        add(hd::ArtifactKind::Warning, hd::Severity::Warning, "WARNING", warning, ordinal++);
    }
}
#else
static void append_command_doc_artifacts(const CommandInfo&,
                                         std::vector<hd::Artifact>&,
                                         HelpDataV2Counts&)
{
}
#endif


static std::string trim_copy_local(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static std::string lower_copy_local(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return s;
}

static bool starts_with_local(const std::string& s, const std::string& prefix)
{
    return s.size() >= prefix.size() && s.compare(0, prefix.size(), prefix) == 0;
}

static std::string strip_contract_comment_prefix(std::string line)
{
    line = trim_copy_local(std::move(line));
    if (starts_with_local(line, "//")) {
        line = line.substr(2);
        if (!line.empty() && line.front() == ' ') {
            line.erase(line.begin());
        }
    }
    return line;
}


static bool is_compact_set_family_command_local(const std::string& command)
{
    const std::string u = hd::upper(trim_copy_local(command));
    static const std::map<std::string, std::string> compact_to_canonical = {
        {"SETCASE", "SET CASE"},
        {"SETCDX", "SET CDX"},
        {"SETCNX", "SET CNX"},
        {"SETFILTER", "SET FILTER"},
        {"SETINDEX", "SET INDEX"},
        {"SETLMDB", "SET LMDB"},
        {"SETNEAR", "SET NEAR"},
        {"SETORDER", "SET ORDER"},
        {"SETPATH", "SET PATH"},
        {"SETUNIQUE", "SET UNIQUE"},
        {"SET_UNIQUE", "SET UNIQUE"}
    };
    return compact_to_canonical.count(u) > 0;
}

static std::string canonicalize_set_family_command_local(const std::string& command)
{
    const std::string u = hd::upper(trim_copy_local(command));
    static const std::map<std::string, std::string> compact_to_canonical = {
        {"SETCASE", "SET CASE"},
        {"SETCDX", "SET CDX"},
        {"SETCNX", "SET CNX"},
        {"SETFILTER", "SET FILTER"},
        {"SETINDEX", "SET INDEX"},
        {"SETLMDB", "SET LMDB"},
        {"SETNEAR", "SET NEAR"},
        {"SETORDER", "SET ORDER"},
        {"SETPATH", "SET PATH"},
        {"SETUNIQUE", "SET UNIQUE"},
        {"SET_UNIQUE", "SET UNIQUE"}
    };
    auto it = compact_to_canonical.find(u);
    return it == compact_to_canonical.end() ? u : it->second;
}

static void add_set_family_alias_if_needed_local(const std::string& original,
                                                 std::vector<std::string>& aliases)
{
    const std::string u = hd::upper(trim_copy_local(original));
    if (!is_compact_set_family_command_local(u)) {
        return;
    }
    if (std::find(aliases.begin(), aliases.end(), u) == aliases.end()) {
        aliases.push_back(u);
    }
}

static bool source_file_extension_supported(const fs::path& p)
{
    std::string ext = hd::upper(p.extension().string());
    return ext == ".CPP" || ext == ".CXX" || ext == ".CC" ||
           ext == ".HPP" || ext == ".H" || ext == ".HH";
}

struct UsageContractDoc {
    std::string owner;
    std::string command;
    std::vector<std::string> summary;
    // `syntax:` IS A SECTION AND THIS READER USED TO BE THE ONLY ONE THAT DID
    // NOT KNOW IT. helpdata_source_miner.cpp lists SYNTAX among its section
    // names (miner:1134); this file's list stopped at `related`, so when the
    // miner's contract family was retired on 2026-09-13 the one `syntax:` line
    // in the tree stopped reaching the store. Measured the same day: 1 syntax:
    // line, in 1 file -- cmd_maint.cpp:25.
    //
    // TEACHING THE READER RATHER THAN REWRITING THE FILE IS DELIBERATE. In
    // cmd_maint.cpp the `syntax:` line is the verb GRAMMAR and the `usage:`
    // lines beneath it enumerate the individual forms; folding one into the
    // other would put a 187-character compound line among the single forms and
    // lose a distinction the author drew on purpose.
    std::vector<std::string> syntax;
    std::vector<std::string> usage;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> aliases;
    std::vector<std::string> related;
};

static void add_contract_line(UsageContractDoc& doc,
                              const std::string& section,
                              const std::string& value)
{
    const std::string clean = trim_copy_local(value);
    if (clean.empty()) {
        return;
    }

    if (section == "summary") {
        doc.summary.push_back(clean);
    } else if (section == "syntax") {
        doc.syntax.push_back(clean);
    } else if (section == "usage") {
        doc.usage.push_back(clean);
    } else if (section == "examples" || section == "example") {
        doc.examples.push_back(clean);
    } else if (section == "notes" || section == "note") {
        doc.notes.push_back(clean);
    } else if (section == "aliases" || section == "alias") {
        doc.aliases.push_back(hd::upper(clean));
    } else if (section == "related") {
        doc.related.push_back(clean);
    }
}

static UsageContractDoc parse_usage_contract_block(const std::vector<std::string>& lines,
                                                   std::size_t marker_index)
{
    UsageContractDoc doc;
    std::string section;

    // A CONTRACT DOES NOT HAVE TO LIVE IN A COMMENT, AND THIS READER ASSUMED
    // IT DID. The loop below broke at the first line not starting with "//",
    // so a contract written inside a RAW STRING yielded nothing but its own
    // marker line.
    //
    // There is exactly ONE such contract in the tree, counted 2026-09-13, and
    // it is a good design rather than an oddity: cmd_lmdb.cpp:96 opens
    // R"DTUSAGE( ... )DTUSAGE" and puts the contract INSIDE THE TEXT THE
    // COMMAND ACTUALLY PRINTS, so the contract and the runtime usage are the
    // same bytes and cannot drift from each other. Moving it into comments to
    // suit this reader would force that text to be duplicated -- a new drift
    // surface, to remove one.
    //
    // helpdata_source_miner.cpp has always handled this (its raw-string branch
    // at miner:1102). Retiring the miner's contract family therefore dropped
    // this one command's usage and notes from the store, which is how it was
    // found: `contract_inventory.py drift` reported DOT|LMDB source-only.
    //
    // THE TWO FORMS END DIFFERENTLY, which is the whole of the change: the
    // comment form ends at the first non-comment line; the raw-string form ends
    // at its closing delimiter, a line that begins with ')' and carries the
    // quote -- )DTUSAGE" here. Both still end at @dottalk.end and at a second
    // marker, below.
    const bool comment_form =
        starts_with_local(trim_copy_local(lines[marker_index]), "//");

    for (std::size_t i = marker_index; i < lines.size(); ++i) {
        std::string raw = trim_copy_local(lines[i]);

        if (i != marker_index) {
            if (comment_form) {
                if (!starts_with_local(raw, "//")) {
                    break;
                }
            } else if (!raw.empty() && raw.front() == ')' &&
                       raw.find('"') != std::string::npos) {
                break;
            }
        }

        std::string line = strip_contract_comment_prefix(std::move(raw));
        if (line.empty()) {
            continue;
        }

        const std::string lineU = hd::upper(line);
        if (lineU == "@DOTTALK.USAGE V1") {
            // A SECOND MARKER ENDS THIS BLOCK. IT USED TO BE SKIPPED, AND THAT
            // MADE ONE FILE'S CONTRACTS EAT EACH OTHER.
            //
            // `continue` here meant a block ran to @dottalk.end or to the first
            // non-// line -- and 196 of the 210 contract-bearing files in this
            // tree carry NO @dottalk.end (counted 2026-09-13), so in an unbroken
            // comment run every contract absorbed the ones after it and took the
            // LAST `command:` it saw as its key.
            //
            // Measured on the store REBUILT 2026-09-13 after the other fixes
            // landed: src/tv/cmd_recordview.cpp holds RECORDVIEW, RECORD and
            // BROWSETV in one run with no terminator, and the store held THREE
            // nested cumulative copies under UI|BROWSETV -- 8 USAGE rows where
            // the command declares one -- while UI|RECORD and UI|RECORDVIEW had
            // ZERO rows each. Published documentation said BROWSETV accepts
            // `RECORD <field> WITH <value>`. It does not.
            //
            // THIS FIX WAS WRITTEN ONCE BEFORE AND LOST. The patch that added it
            // was rebased away by a later patch built from a stale copy of this
            // file, and only the rebuilt store caught it -- the SUMMARY count
            // per command is the cheap detector: one contract, one summary, so
            // any command with two is either this defect or two files declaring
            // the same name. Check that count after any change here.
            //
            // helpdata_source_miner.cpp's extractor has always broken here. This
            // is the bridge agreeing with it. Terminating the 196 contracts is
            // the other half and is a source change, not this one.
            if (i != marker_index) {
                break;
            }
            continue;
        }
        if (lineU == "@DOTTALK.END" || lineU == "@DOTTALK.CONTRACT.END") {
            break;
        }
        // ANY @dottalk. TOKEN ENDS THE CONTRACT, not just the two end markers.
        // A contract whose last section is `related:` and which is followed by
        // an @dottalk.location v1 block used to ABSORB that block: ABOUT
        // published 8 RELATED entries where its source declares 2, the extra
        // six being `@dottalk.location v1`, `id:`, `home:`, `canonical-path:`,
        // `project:`, `role:` -- documentation asserting that a command is
        // related to its own file path. Measured 2026-09-13: 3 contracts,
        // 18 lines (DOT|ABOUT and DOT|HELP in RELATED, DOT|BBOX in NOTE).
        //
        // Stopping HERE rather than filtering those keys downstream is what
        // lets the unrecognized-key rule below be permissive, which is where
        // 534 wrongly-dropped prose lines come back.
        if (lineU.rfind("@DOTTALK.", 0) == 0) {
            break;
        }

        // A COLON IS NOT A KEY, AND TREATING IT AS ONE SILENTLY ATE 906 LINES.
        //
        // This tested `line.find(':')` -- ANY colon, anywhere -- so a prose line
        // inside a section became a key: value pair, matched no known key, and
        // fell through to the section.clear() below. Everything after it in that
        // section was then dropped until the next section header.
        //
        // Measured 2026-09-13 over the whole tree: 60 sections killed early,
        // 906 contract prose lines dropped, 49 of 223 commands affected -- 21%
        // of the contract prose in the tree. The single line that did the most
        // damage is cmd_workspace.cpp:133, the FIRST note of the biggest command
        // in the tree:
        //
        //     WORKSPACE with no arguments is a report: it lists current open
        //     work areas.
        //
        // One colon in ordinary English, and DOT|WORKSPACE published ZERO notes
        // while the store showed 157 -- all of them from the other writer. Its
        // usage section died the same way at :109 ("...which it is on line
        // one:"), which is why it stored 34 of 55 usage lines.
        //
        // THE TEST IS NOW STRUCTURAL: a key is a single unspaced token. That is
        // exactly what separates `notes:` from a sentence that happens to
        // contain a colon, and it is the rule a reader already applies by eye.
        // Lines that DO look like keys and are not section names still clear the
        // section -- `id:`, `home:`, `canonical-path:` from an adjacent
        // @dottalk.location block are meant to be dropped, and still are.
        //
        // helpdata_source_miner.cpp never had this defect: on an unrecognized
        // key it falls through and APPENDS rather than clearing. That is the
        // one axis on which the miner was the better reader.
        const auto colon = line.find(':');
        const bool colon_is_a_key = [&] {
            if (colon == std::string::npos || colon == 0 || colon > 24) return false;
            const std::string head = trim_copy_local(line.substr(0, colon));
            if (head.empty() || head.size() != colon) return false;   // no leading space
            // A KEY'S COLON IS FOLLOWED BY NOTHING OR WHITESPACE. Verified over
            // the whole tree 2026-09-13: every contract key is written with a
            // space or an end-of-line after its colon, none `status:supported`.
            // This is what keeps a line that merely BEGINS with a URL --
            // `http://...` -- from reading as the key `http`.
            if (colon + 1 < line.size() &&
                !std::isspace(static_cast<unsigned char>(line[colon + 1]))) return false;
            if (!std::isalpha(static_cast<unsigned char>(head.front()))) return false;
            for (const char ch : head) {
                const unsigned char u = static_cast<unsigned char>(ch);
                if (!std::isalnum(u) && ch != '_' && ch != '-') return false;
            }
            return true;
        }();
        if (colon_is_a_key) {
            const std::string key = lower_copy_local(trim_copy_local(line.substr(0, colon)));
            const std::string value = trim_copy_local(line.substr(colon + 1));

            if (key == "owner") {
                doc.owner = value;
                section.clear();
                continue;
            }
            if (key == "command") {
                doc.command = value;
                section.clear();
                continue;
            }

            if (key == "summary" || key == "syntax" || key == "usage" ||
                key == "examples" || key == "example" ||
                key == "notes" || key == "note" ||
                key == "aliases" || key == "alias" ||
                key == "related") {
                section = key;
                add_contract_line(doc, section, value);
                continue;
            }

            // ENVELOPE KEYS CLOSE THE SECTION; ANYTHING ELSE IS PROSE.
            //
            // This used to clear the section for EVERY unrecognized key, which
            // is fine for `risk:` and fatal for a note that happens to open
            // with a word and a colon. English does that constantly --
            // "DESKTOP: no windows, no focus, no z-order", "noise: this is the
            // one part of R131 that can change...", "provenance: MDO-377G" --
            // and each one silently killed the rest of its section.
            //
            // Measured 2026-09-13 with the structural key test above already in
            // place: 372 prose lines still dropped across 8 commands, 314 of
            // them DOT|WORKSPACE alone. Naming the envelope explicitly and
            // treating everything else as prose recovers them, and it is what
            // helpdata_source_miner.cpp has always done -- on an unrecognized
            // key it falls through and appends.
            //
            // The location-block bleed this used to prevent is now prevented
            // upstream, at the @dottalk. break, which is the correct place: the
            // block is not part of the contract at all.
            static const std::set<std::string> envelope = {
                "catalog", "category", "status", "noargs", "effect", "mutates",
                "usage-access", "usage_access", "risk", "lane", "project",
                "subsystem", "layer", "owns"
            };
            if (envelope.count(key) > 0) {
                section.clear();
                continue;
            }
            // Not a key we know: fall through and keep it as section prose.
        }

        add_contract_line(doc, section, line);
    }

    return doc;
}

static std::vector<std::string> read_text_lines_best_effort(const fs::path& path)
{
    std::ifstream in(path, std::ios::binary);
    std::vector<std::string> lines;
    if (!in) {
        return lines;
    }

    std::string line;
    while (std::getline(in, line)) {
        if (!line.empty() && line.back() == '\r') {
            line.pop_back();
        }
        lines.push_back(std::move(line));
    }
    return lines;
}

static void append_usage_contract_artifacts_for_doc(const UsageContractDoc& doc,
                                                    std::vector<hd::Artifact>& out,
                                                    HelpDataV2Counts& counts)
{
    std::string catalog = "DOT";
    std::string raw_name = hd::upper(trim_copy_local(doc.command));
    std::vector<std::string> aliases = doc.aliases;

    if (!doc.owner.empty()) {
        const std::string ownerU = hd::upper(trim_copy_local(doc.owner));
        const auto bar = ownerU.find('|');
        if (bar != std::string::npos) {
            catalog = ownerU.substr(0, bar);
            if (raw_name.empty()) {
                raw_name = ownerU.substr(bar + 1);
            }
        } else if (raw_name.empty()) {
            raw_name = ownerU;
        }
    }

    add_set_family_alias_if_needed_local(raw_name, aliases);
    std::string name = canonicalize_set_family_command_local(raw_name);

    if (name.empty()) {
        return;
    }

    auto add = [&](hd::ArtifactKind kind,
                   const std::string& role,
                   const std::string& text,
                   int ordinal) {
        const std::string clean = trim_copy_local(text);
        if (clean.empty()) return;

        out.push_back(hd::make_artifact(catalog,
                                        name,
                                        { hd::OwnerKind::Command, name },
                                        kind,
                                        hd::SourceKind::UsageContract,
                                        hd::Confidence::Curated,
                                        hd::Severity::Info,
                                        role,
                                        clean,
                                        ordinal));
        ++counts.usage_contract_rows;
    };

    int alias_ordinal = 1;
    for (const auto& alias : aliases) {
        add(hd::ArtifactKind::Alias,
            "USAGE_CONTRACT_ALIAS",
            alias,
            alias_ordinal++);
    }

    if (!doc.summary.empty()) {
        std::string combined;
        for (const auto& s : doc.summary) {
            if (!combined.empty()) combined += " ";
            combined += s;
        }
        add(hd::ArtifactKind::Summary, "USAGE_CONTRACT_SUMMARY", combined, 0);
    }

    int ordinal = 1;
    for (const auto& s : doc.syntax) {
        add(hd::ArtifactKind::Syntax, "USAGE_CONTRACT_SYNTAX", s, ordinal++);
    }

    ordinal = 1;
    for (const auto& s : doc.usage) {
        add(hd::ArtifactKind::Usage, "USAGE_CONTRACT", s, ordinal++);
    }

    ordinal = 1;
    for (const auto& s : doc.examples) {
        add(hd::ArtifactKind::Example, "USAGE_CONTRACT_EXAMPLE", s, ordinal++);
    }

    ordinal = 1;
    for (const auto& s : doc.notes) {
        add(hd::ArtifactKind::Note, "USAGE_CONTRACT_NOTE", s, ordinal++);
    }

    ordinal = 1;
    for (const auto& s : doc.related) {
        add(hd::ArtifactKind::Related, "USAGE_CONTRACT_RELATED", s, ordinal++);
    }
}

static void append_direct_usage_contract_artifacts(const std::vector<std::string>& source_roots,
                                                   std::vector<hd::Artifact>& out,
                                                   HelpDataV2Counts& counts)
{
    std::set<std::string> files_with_contract;

    for (const auto& root_raw : source_roots) {
        if (root_raw.empty()) {
            continue;
        }

        fs::path root(root_raw);
        std::error_code ec;
        if (!fs::exists(root, ec)) {
            continue;
        }

        if (fs::is_regular_file(root, ec)) {
            if (!source_file_extension_supported(root)) {
                continue;
            }

            const auto lines = read_text_lines_best_effort(root);
            for (std::size_t i = 0; i < lines.size(); ++i) {
                if (lines[i].find("@dottalk.usage v1") == std::string::npos) {
                    continue;
                }

                UsageContractDoc doc = parse_usage_contract_block(lines, i);
                const int before = counts.usage_contract_rows;
                append_usage_contract_artifacts_for_doc(doc, out, counts);
                if (counts.usage_contract_rows > before) {
                    files_with_contract.insert(root.lexically_normal().string());
                }
            }
            continue;
        }

        if (!fs::is_directory(root, ec)) {
            continue;
        }

        for (fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec), end;
             !ec && it != end;
             it.increment(ec)) {
            if (ec) {
                break;
            }

            const fs::path p = it->path();
            if (!it->is_regular_file(ec) || ec) {
                ec.clear();
                continue;
            }

            if (!source_file_extension_supported(p)) {
                continue;
            }

            const auto lines = read_text_lines_best_effort(p);
            if (lines.empty()) {
                continue;
            }

            for (std::size_t i = 0; i < lines.size(); ++i) {
                if (lines[i].find("@dottalk.usage v1") == std::string::npos) {
                    continue;
                }

                UsageContractDoc doc = parse_usage_contract_block(lines, i);
                const int before = counts.usage_contract_rows;
                append_usage_contract_artifacts_for_doc(doc, out, counts);
                if (counts.usage_contract_rows > before) {
                    files_with_contract.insert(p.lexically_normal().string());
                }
            }
        }
    }

    counts.usage_contract_files = static_cast<int>(files_with_contract.size());
}


static void assign_ids(std::vector<hd::Artifact>& artifacts)
{
    int id = 1;
    for (auto& artifact : artifacts) {
        artifact.id = id++;
    }
}

static void copy_mine_counts(const hd::SourceMineResult& mined,
                             HelpDataV2Counts& counts)
{
    counts.mined_source_rows = static_cast<int>(mined.artifacts.size());
    counts.source_files_seen = mined.counts.files_seen;
    counts.source_files_scanned = mined.counts.files_scanned;
    counts.source_files_skipped = mined.counts.files_skipped;
    counts.source_command_contexts = mined.counts.command_contexts;
    counts.source_command_identity_facts = mined.counts.command_identity_facts;
    counts.source_argument_candidates = mined.counts.argument_candidates;
    counts.source_syntax_candidates = mined.counts.syntax_candidates;
    counts.source_message_candidates = mined.counts.message_candidates;
    counts.source_message_symbol_candidates = mined.counts.message_symbol_candidates;
    counts.source_artifact_cap_hit = (mined.counts.artifacts > 0 &&
                                      mined.counts.artifacts == counts.mined_source_rows &&
                                      counts.mined_source_rows >= 1000) ? 1 : 0;
}

} // namespace

std::vector<hd::Artifact>
collect_helpdata_v2_artifacts(const std::vector<CommandInfo>& commands,
                              const std::vector<std::string>& source_roots,
                              HelpDataV2Counts* counts_out)
{
    HelpDataV2Counts counts;
    std::vector<hd::Artifact> artifacts;

    artifacts.reserve(commands.size() * 4);

    for (const auto& command : commands) {
        artifacts.push_back(make_command_status_artifact(command));
        ++counts.command_status_rows;

        append_legacy_catalog_artifacts(command, artifacts, counts);
        append_command_doc_artifacts(command, artifacts, counts);
    }

    std::vector<hd::Artifact> standard_messages = hd::artifacts_from_standard_messages();
    counts.standard_message_rows = static_cast<int>(standard_messages.size());
    artifacts.insert(artifacts.end(),
                     std::make_move_iterator(standard_messages.begin()),
                     std::make_move_iterator(standard_messages.end()));

    hd::SourceMineResult mined = hd::mine_source_roots(source_roots);
    copy_mine_counts(mined, counts);
    artifacts.insert(artifacts.end(),
                     std::make_move_iterator(mined.artifacts.begin()),
                     std::make_move_iterator(mined.artifacts.end()));

    // Contract supplement: if the heuristic miner skips a small command file
    // or stops at a safety cap, @dottalk.usage v1 remains authoritative.
    append_direct_usage_contract_artifacts(source_roots, artifacts, counts);

    assign_ids(artifacts);
    counts.total_artifact_rows = static_cast<int>(artifacts.size());

    if (counts_out) {
        *counts_out = counts;
    }
    return artifacts;
}

HelpDataV2Counts export_helpdata_v2_dbfs(const std::string& out_dir,
                                         const std::vector<CommandInfo>& commands,
                                         const std::vector<std::string>& source_roots)
{
    HelpDataV2Counts counts;
    std::vector<hd::Artifact> artifacts = collect_helpdata_v2_artifacts(commands, source_roots, &counts);
    const hd::ExportCounts exported = hd::export_artifacts_dbf(out_dir, artifacts);
    counts.exported_artifact_rows = exported.artifacts;
    return counts;
}

} // namespace cmdhelp
