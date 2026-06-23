#include "dt/meta/metacollect.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <ostream>
#include <regex>
#include <sstream>
#include <string_view>
#include <unordered_set>

namespace dt::meta {
namespace {

namespace fs = std::filesystem;

std::string upper_ascii(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return value;
}

std::string lower_ascii(std::string value) {
    for (char& ch : value) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return value;
}

bool has_extension(const fs::path& path, const std::vector<std::string>& extensions) {
    const auto ext = lower_ascii(path.extension().string());
    return std::find(extensions.begin(), extensions.end(), ext) != extensions.end();
}

std::string read_text_file(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return {};
    }

    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

std::string normalize_slashes(std::string value) {
    std::replace(value.begin(), value.end(), '\\', '/');
    return value;
}

std::string path_for_fact(const fs::path& workspace_root, const fs::path& file) {
    std::error_code ec;
    const auto rel = fs::relative(file, workspace_root, ec);
    if (!ec) {
        return normalize_slashes(rel.string());
    }
    return normalize_slashes(file.string());
}

std::vector<std::string> default_extensions() {
    return {".cpp", ".hpp", ".h", ".hh", ".cxx", ".cc"};
}

std::vector<fs::path> default_source_roots(const fs::path& workspace_root) {
    return {
        workspace_root / "src",
        workspace_root / "include",
        workspace_root / "bindings"
    };
}

bool is_ignored_path(const fs::path& path) {
    const auto text = normalize_slashes(path.string());
    return text.find("/build/") != std::string::npos ||
           text.find("/_drops/") != std::string::npos ||
           text.find("/docs/generated/") != std::string::npos ||
           text.find("/.git/") != std::string::npos;
}

void add_fact(std::vector<MetaFact>& facts,
              MetaFactDomain domain,
              MetaFactEvidenceKind kind,
              std::string canonical_name,
              std::string display_name,
              std::string owner,
              std::string source_file,
              std::string evidence_value,
              std::string notes) {
    MetaFact fact;
    fact.domain = domain;
    fact.evidence_kind = kind;
    fact.canonical_name = upper_ascii(std::move(canonical_name));
    fact.display_name = std::move(display_name);
    fact.owner = std::move(owner);
    fact.visibility_tier = "developer";
    fact.implementation_status = "detected";
    fact.source_authority = "source-scan";
    fact.source_file = std::move(source_file);
    fact.public_surface = false;
    fact.active = true;
    fact.evidence_value = std::move(evidence_value);
    fact.notes = std::move(notes);
    facts.push_back(std::move(fact));
}

void extract_doc_literals(std::vector<MetaFact>& facts,
                          const fs::path& workspace_root,
                          const fs::path& file,
                          const std::string& text) {
    const auto rel = path_for_fact(workspace_root, file);

    const std::regex command_doc(
        R"METAREGEX((?:static\s+)?const\s+CommandDoc\s+[A-Za-z0-9_]+\s*=\s*\{\s*"([^"]+)")METAREGEX",
        std::regex_constants::icase);

    const std::regex function_doc(
        R"METAREGEX((?:static\s+)?const\s+FunctionDoc\s+[A-Za-z0-9_]+\s*=\s*\{\s*"([^"]+)")METAREGEX",
        std::regex_constants::icase);

    for (std::sregex_iterator it(text.begin(), text.end(), command_doc), end; it != end; ++it) {
        const auto name = (*it)[1].str();
        add_fact(facts,
                 MetaFactDomain::Command,
                 MetaFactEvidenceKind::SourceCatalog,
                 name,
                 name,
                 "command-catalog",
                 rel,
                 "CommandDoc literal",
                 "Catalog Extraction v1 regex detection.");
    }

    for (std::sregex_iterator it(text.begin(), text.end(), function_doc), end; it != end; ++it) {
        const auto name = (*it)[1].str();
        add_fact(facts,
                 MetaFactDomain::Function,
                 MetaFactEvidenceKind::SourceCatalog,
                 name,
                 name,
                 "function-catalog",
                 rel,
                 "FunctionDoc literal",
                 "Catalog Extraction v1 regex detection.");
    }
}

void extract_handler_symbols(std::vector<MetaFact>& facts,
                             const fs::path& workspace_root,
                             const fs::path& file,
                             const std::string& text) {
    const auto rel = path_for_fact(workspace_root, file);
    const std::regex handler_symbol(R"(\bcmd_([A-Za-z0-9_]+)\b)");

    std::unordered_set<std::string> seen;
    for (std::sregex_iterator it(text.begin(), text.end(), handler_symbol), end; it != end; ++it) {
        auto token = (*it)[1].str();
        if (token.empty()) {
            continue;
        }

        const auto key = upper_ascii(token);
        if (!seen.insert(key).second) {
            continue;
        }

        add_fact(facts,
                 MetaFactDomain::Command,
                 MetaFactEvidenceKind::SourceRegistry,
                 token,
                 token,
                 "handler-symbol",
                 rel,
                 "cmd_ handler/symbol",
                 "Symbol evidence only; not proof of public command registration.");
    }
}

void add_skeleton_marker(std::vector<MetaFact>& facts, const std::string& workspace_root) {
    MetaFact marker;
    marker.domain = MetaFactDomain::RuntimeProof;
    marker.evidence_kind = MetaFactEvidenceKind::GeneratedReport;
    marker.canonical_name = "METACOLLECT_SKELETON";
    marker.display_name = "METACOLLECT skeleton";
    marker.owner = "metadata";
    marker.visibility_tier = "developer";
    marker.implementation_status = "skeleton";
    marker.source_authority = "proposal";
    marker.source_file = workspace_root;
    marker.public_surface = false;
    marker.active = true;
    marker.evidence_value = "read-only skeleton marker";
    marker.notes = "Skeleton marker retained; catalog extraction may add rows after this row.";
    facts.push_back(std::move(marker));
}

std::string csv_bool(bool value) {
    return value ? "true" : "false";
}

} // namespace

const char* to_string(MetaFactDomain domain) noexcept {
    switch (domain) {
    case MetaFactDomain::Command: return "command";
    case MetaFactDomain::Function: return "function";
    case MetaFactDomain::Subcommand: return "subcommand";
    case MetaFactDomain::EntryVariant: return "entry-variant";
    case MetaFactDomain::Argument: return "argument";
    case MetaFactDomain::HelpText: return "help-text";
    case MetaFactDomain::Message: return "message";
    case MetaFactDomain::FieldDictionary: return "field-dictionary";
    case MetaFactDomain::RuntimeProof: return "runtime-proof";
    case MetaFactDomain::Unknown:
    default: return "unknown";
    }
}

const char* to_string(MetaFactEvidenceKind kind) noexcept {
    switch (kind) {
    case MetaFactEvidenceKind::SourceCatalog: return "source-catalog";
    case MetaFactEvidenceKind::SourceRegistry: return "source-registry";
    case MetaFactEvidenceKind::MetadataTable: return "metadata-table";
    case MetaFactEvidenceKind::RuntimeTranscript: return "runtime-transcript";
    case MetaFactEvidenceKind::GeneratedHelp: return "generated-help";
    case MetaFactEvidenceKind::CuratedHelp: return "curated-help";
    case MetaFactEvidenceKind::GeneratedReport: return "generated-report";
    case MetaFactEvidenceKind::Unknown:
    default: return "unknown";
    }
}

CollectResult collect_catalog_facts(const CollectOptions& options) {
    CollectResult result;

    const fs::path workspace_root = options.workspace_root.empty()
        ? fs::current_path()
        : fs::path(options.workspace_root);

    if (options.include_skeleton_marker) {
        add_skeleton_marker(result.facts, workspace_root.string());
    }

    if (!options.include_source_catalogs) {
        return result;
    }

    std::vector<std::string> extensions = options.source_extensions.empty()
        ? default_extensions()
        : options.source_extensions;

    for (auto& ext : extensions) {
        ext = lower_ascii(ext);
        if (!ext.empty() && ext.front() != '.') {
            ext.insert(ext.begin(), '.');
        }
    }

    std::vector<fs::path> roots;
    if (options.source_roots.empty()) {
        roots = default_source_roots(workspace_root);
    } else {
        for (const auto& root : options.source_roots) {
            roots.emplace_back(root);
        }
    }

    for (const auto& root : roots) {
        std::error_code ec;
        if (!fs::exists(root, ec)) {
            result.warnings.push_back("source root not found: " + root.string());
            continue;
        }

        for (fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec), end;
             it != end && !ec;
             it.increment(ec)) {
            if (ec) {
                result.warnings.push_back("directory iteration warning under: " + root.string());
                break;
            }

            if (!it->is_regular_file()) {
                continue;
            }

            const fs::path file = it->path();
            if (is_ignored_path(file) || !has_extension(file, extensions)) {
                continue;
            }

            const auto text = read_text_file(file);
            if (text.empty()) {
                continue;
            }

            extract_doc_literals(result.facts, workspace_root, file, text);
            extract_handler_symbols(result.facts, workspace_root, file, text);
        }
    }

    return result;
}

static void csv_cell(std::ostream& out, const std::string& value) {
    out << '"';
    for (char ch : value) {
        if (ch == '"') {
            out << "\"\"";
        } else {
            out << ch;
        }
    }
    out << '"';
}

void write_metafacts_csv(std::ostream& out, const std::vector<MetaFact>& facts) {
    out << "domain,evidence_kind,canonical_name,display_name,owner,visibility_tier,"
           "implementation_status,source_authority,source_file,handler,"
           "dispatch_reachable,public_surface,self_registered,generated,curated,active,"
           "evidence_value,notes\n";

    for (const auto& fact : facts) {
        csv_cell(out, to_string(fact.domain)); out << ',';
        csv_cell(out, to_string(fact.evidence_kind)); out << ',';
        csv_cell(out, fact.canonical_name); out << ',';
        csv_cell(out, fact.display_name); out << ',';
        csv_cell(out, fact.owner); out << ',';
        csv_cell(out, fact.visibility_tier); out << ',';
        csv_cell(out, fact.implementation_status); out << ',';
        csv_cell(out, fact.source_authority); out << ',';
        csv_cell(out, fact.source_file); out << ',';
        csv_cell(out, fact.handler); out << ',';
        out << csv_bool(fact.dispatch_reachable) << ',';
        out << csv_bool(fact.public_surface) << ',';
        out << csv_bool(fact.self_registered) << ',';
        out << csv_bool(fact.generated) << ',';
        out << csv_bool(fact.curated) << ',';
        out << csv_bool(fact.active) << ',';
        csv_cell(out, fact.evidence_value); out << ',';
        csv_cell(out, fact.notes); out << '\n';
    }
}

} // namespace dt::meta

