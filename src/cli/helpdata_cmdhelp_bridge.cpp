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

static hd::SourceKind source_for_catalog(const std::string& catalog)
{
    const std::string cat = hd::upper(catalog);
    if (cat == "FOX") return hd::SourceKind::FoxRef;
    if (cat == "ED")  return hd::SourceKind::EdRef;
    return hd::SourceKind::DotRef;
}

static hd::Artifact make_command_status_artifact(const CommandInfo& command)
{
    const std::string catalog = hd::upper(command.catalog.empty() ? std::string("DOT") : command.catalog);
    const std::string name = hd::upper(command.name);

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
    const std::string name = hd::upper(command.name);
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
    const std::string name = hd::upper(command.name);
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
    std::vector<std::string> usage;
    std::vector<std::string> examples;
    std::vector<std::string> notes;
    std::vector<std::string> aliases;
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
    } else if (section == "usage") {
        doc.usage.push_back(clean);
    } else if (section == "examples" || section == "example") {
        doc.examples.push_back(clean);
    } else if (section == "notes" || section == "note") {
        doc.notes.push_back(clean);
    } else if (section == "aliases" || section == "alias") {
        doc.aliases.push_back(hd::upper(clean));
    }
}

static UsageContractDoc parse_usage_contract_block(const std::vector<std::string>& lines,
                                                   std::size_t marker_index)
{
    UsageContractDoc doc;
    std::string section;

    for (std::size_t i = marker_index; i < lines.size(); ++i) {
        std::string raw = trim_copy_local(lines[i]);

        if (i != marker_index && !starts_with_local(raw, "//")) {
            break;
        }

        std::string line = strip_contract_comment_prefix(std::move(raw));
        if (line.empty()) {
            continue;
        }

        const std::string lineU = hd::upper(line);
        if (lineU == "@DOTTALK.USAGE V1") {
            continue;
        }

        const auto colon = line.find(':');
        if (colon != std::string::npos) {
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

            if (key == "summary" || key == "usage" ||
                key == "examples" || key == "example" ||
                key == "notes" || key == "note" ||
                key == "aliases" || key == "alias") {
                section = key;
                add_contract_line(doc, section, value);
                continue;
            }

            // Other metadata/risk keys are intentionally not emitted as
            // renderable help rows.
            section.clear();
            continue;
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
