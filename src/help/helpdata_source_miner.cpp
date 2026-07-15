// ============================================================================
// File: src/help/helpdata_source_miner.cpp
// Purpose: Surface-focused source-code mining for HELP DATA v2 usage contracts and candidate artifacts.
// ============================================================================
#include "helpdata_source_miner.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <regex>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <unordered_set>

namespace fs = std::filesystem;

namespace dottalk::helpdata {
namespace {

// Conservative runtime-mining guards. These keep CMDHELP BUILD V2 predictable
// when pointed at an entire production tree. The miner is an evidence collector,
// not a compiler frontend; bounded, repeatable output is more valuable than
// exhaustive noisy harvesting.
static constexpr std::size_t kEffectiveMaxFileBytes = 512u * 1024u;
static constexpr std::size_t kMaxTotalArtifacts = 1000u;
static constexpr std::size_t kMaxArtifactsPerFile = 40u;
static constexpr int kMaxMatchesPerPatternPerFile = 25;
static constexpr int kMaxMessageMatchesPerFile = 8;
static constexpr std::size_t kMaxCommandContextsPerFile = 4u;

static bool total_budget_exhausted(const std::vector<Artifact>& artifacts)
{
    return artifacts.size() >= kMaxTotalArtifacts;
}

static std::string trim(std::string s)
{
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), [&](unsigned char ch) { return !is_space(ch); }));
    while (!s.empty() && is_space(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static std::string normalize_token(std::string s)
{
    s = trim(s);
    std::replace(s.begin(), s.end(), '-', '_');
    return upper(s);
}

static bool is_compact_set_family_command(const std::string& command)
{
    const std::string u = upper(trim(command));
    static const std::unordered_map<std::string, std::string> compact_to_canonical = {
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

static std::string canonicalize_set_family_command(const std::string& command)
{
    const std::string u = upper(trim(command));
    static const std::unordered_map<std::string, std::string> compact_to_canonical = {
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

static void add_set_family_alias_if_needed(const std::string& original,
                                           std::vector<std::string>& aliases)
{
    const std::string u = upper(trim(original));
    if (!is_compact_set_family_command(u)) {
        return;
    }
    if (std::find(aliases.begin(), aliases.end(), u) == aliases.end()) {
        aliases.push_back(u);
    }
}

static bool has_source_extension(const fs::path& path)
{
    const std::string ext = upper(path.extension().string());
    return ext == ".CPP" || ext == ".HPP" || ext == ".H" ||
           ext == ".CC" || ext == ".CXX" || ext == ".C";
}

static bool is_skipped_dir(const fs::path& path)
{
    const std::string name = upper(path.filename().string());

    static const std::unordered_set<std::string> skip = {
        ".GIT", ".HG", ".SVN", ".VS", ".VSCODE",
        "BUILD", "BUILDS", "OUT", "BIN", "OBJ",
        "DEBUG", "RELEASE", "RELWITHDEBINFO", "MINSIZEREL",
        "X64", "X86", "X32",
        "CMAKEFILES", "CMAKEFILESTMP",
        "VCPKG_INSTALLED", "NODE_MODULES",
        "DOCS", "PATCHES", "TESTS", "FIXTURES",
        "MINER_FIXTURE", "HELPDATA_SMOKE_OUT", "BRIDGE_OUT",
        "GENERATED", "AUTOGEN", "TMP", "TEMP"
    };

    return skip.count(name) > 0;
}



static bool is_catalog_authority_file(const fs::path& path)
{
    const std::string stem = upper(path.stem().string());
    static const std::unordered_set<std::string> exact_stems = {
        "FOXREF",
        "DOTREF",
        "EDREF",
        "COMMAND_CATALOG",
        "FUNCTION_CATALOG",
        "FUNCTION_HELP",
        "XEXPR_FUNCTIONS",
        "SHELL_COMMANDS",
        "TABLE_BUFFER"
    };
    return exact_stems.count(stem) > 0;
}

static bool is_command_implementation_surface(const fs::path& path)
{
    const std::string stem = upper(path.stem().string());
    auto starts_with = [](const std::string& value, const std::string& prefix) {
        return value.rfind(prefix, 0) == 0;
    };

    // Prefer command implementation surfaces, not every helper named
    // command_*. Catalog/reflection files are handled separately below.
    if (starts_with(stem, "CMD")) {
        return true;
    }

    return false;
}

static bool is_education_surface(const fs::path& path)
{
    const std::string stem = upper(path.stem().string());
    return stem.rfind("EDU", 0) == 0;
}

static bool is_app_surface(const fs::path& path)
{
    const std::string stem = upper(path.stem().string());
    return stem.rfind("APP", 0) == 0;
}

static bool is_function_surface(const fs::path& path)
{
    const std::string stem = upper(path.stem().string());
    return stem.rfind("FN", 0) == 0 || stem.rfind("FUNCTION", 0) == 0;
}

static bool is_help_surface_source_file(const fs::path& path)
{
    // HELP DATA source mining is intentionally limited to files that usually
    // define user-facing command, education, app/demo, and function surfaces.
    // Curated authority files are allowed through for future function/help
    // generator work, but ordinary prose from those files is not mined as
    // runtime messages.
    const std::string name = upper(path.filename().string());

    if (is_command_implementation_surface(path) ||
        is_education_surface(path) ||
        is_app_surface(path) ||
        is_function_surface(path) ||
        is_catalog_authority_file(path)) {
        return true;
    }

    // Some projects use explicit ref header names.
    return name == "FOXREF.HPP" || name == "DOTREF.HPP" || name == "EDREF.HPP";
}

static bool permits_runtime_message_mining(const fs::path& /*path*/,
                                           const std::vector<std::string>& /*commands*/)
{
    // Command/help source mining should not harvest runtime output strings by
    // default. Runtime messages belong to the later MessageDef/OutputClass
    // subsystem; treating every cout/error string as HELP DATA makes the V2
    // artifact table noisy and causes the artifact cap to hide better signal.
    //
    // Keep message symbol mining enabled below, because stable symbolic IDs are
    // useful evidence. Raw message text mining can be reintroduced later behind
    // an explicit developer mode such as CMDHELP BUILD V2 MESSAGES.
    return false;
}

static bool is_skipped_source_file(const fs::path& path)
{
    const std::string name = upper(path.filename().string());

    if (name == "CMAKECXXCOMPILERID.CPP" ||
        name == "CMAKECXXCOMPILERABI.CPP" ||
        name == "CMAKECXXCOMPILERID.C" ||
        name == "CMAKECXXCOMPILERABI.C") {
        return true;
    }

    if (name.find("_AUTOGEN") != std::string::npos ||
        name.find("MOC_") == 0 ||
        name.find("QRC_") == 0) {
        return true;
    }

    return false;
}

static std::string read_file_limited(const fs::path& path, std::size_t max_bytes, bool& skipped)
{
    skipped = false;
    const std::size_t effective_max = std::min<std::size_t>(max_bytes, kEffectiveMaxFileBytes);
    std::error_code ec;
    const auto size = fs::file_size(path, ec);
    if (ec || size > effective_max) {
        skipped = true;
        return {};
    }

    std::ifstream in(path, std::ios::binary);
    if (!in) {
        skipped = true;
        return {};
    }

    return std::string((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
}

static int line_for_pos(const std::string& text, std::size_t pos)
{
    int line = 1;
    for (std::size_t i = 0; i < pos && i < text.size(); ++i) {
        if (text[i] == '\n') {
            ++line;
        }
    }
    return line;
}

static std::string evidence_for(const fs::path& file,
                                int line,
                                const std::string& pattern,
                                const std::string& extra = {})
{
    std::ostringstream out;
    out << file.generic_string();
    if (line > 0) {
        out << ":" << line;
    }
    out << " pattern=" << pattern;
    if (!extra.empty()) {
        out << " " << extra;
    }
    return out.str();
}

static std::string command_hint_from_path(const fs::path& path)
{
    const std::string stem = path.stem().string();
    if (upper(path.stem().string()) == "TABLE_BUFFER") {
        return "TABLE BUFFER";
    }

    static const std::regex rx(R"(^cmd[_-]([A-Za-z0-9_]+)$)", std::regex::icase);
    std::smatch m;
    if (std::regex_match(stem, m, rx) && m.size() > 1) {
        std::string name = m[1].str();
        std::replace(name.begin(), name.end(), '_', ' ');
        return canonicalize_set_family_command(name);
    }
    return {};
}

static std::vector<std::string> command_contexts_from_source(const std::string& text,
                                                             const fs::path& file)
{
    std::vector<std::string> commands;
    std::set<std::string> seen;

    const std::vector<std::regex> patterns = {
        std::regex(R"(\bregister_?command\s*\(\s*[\"']([A-Za-z][A-Za-z0-9_ ]{0,40})[\"'])"),
        std::regex(R"(\bCommandDoc\s*\{\s*[\"']([A-Za-z][A-Za-z0-9_ ]{0,40})[\"'])"),
        std::regex(R"(\.name\s*=\s*[\"']([A-Za-z][A-Za-z0-9_ ]{0,40})[\"'])")
    };

    for (const auto& rx : patterns) {
        for (auto it = std::sregex_iterator(text.begin(), text.end(), rx); it != std::sregex_iterator(); ++it) {
            const std::string cmd = normalize_token((*it)[1].str());
            if (!cmd.empty() && seen.insert(cmd).second) {
                commands.push_back(cmd);
                if (commands.size() >= kMaxCommandContextsPerFile) {
                    return commands;
                }
            }
        }
    }

    const std::string hint = command_hint_from_path(file);
    if (!hint.empty() && seen.insert(hint).second && commands.size() < kMaxCommandContextsPerFile) {
        commands.push_back(hint);
    }

    return commands;
}

static bool is_likely_argument_token(const std::string& token)
{
    static const std::unordered_set<std::string> allow = {
        "ALL", "REST", "NEXT", "RECORD", "FOR", "WHILE", "FIELDS", "FIELD",
        "TO", "INTO", "IN", "ON", "OFF", "TAG", "INDEX", "ORDER", "ALIAS",
        "ASC", "DESC", "UNIQUE", "VERBOSE", "QUIET", "SILENT", "STATUS",
        "TALK", "ECHO", "CONSOLE", "PRINT", "DEVICE", "ALTERNATE", "PAGING",
        "WRAP", "PATH", "DBF", "CDX", "MEMO", "HELP", "BUILD", "CHECK",
        "V2", "ALLTRIM", "RAW", "EXACT", "SAFETY", "DELETED"
    };

    if (token.empty() || token.size() > 32) {
        return false;
    }
    if (token.rfind("NO", 0) == 0 && token.size() > 2) {
        return true;
    }
    if (token.rfind("SET_", 0) == 0 && token.size() > 4) {
        return true;
    }
    if (token.rfind("OPT_", 0) == 0 && token.size() > 4) {
        return true;
    }
    return allow.count(token) > 0;
}

static bool is_noise_string(const std::string& text)
{
    const std::string t = trim(text);
    if (t.size() < 3) {
        return true;
    }
    if (t == "\\n" || t == "\n" || t == " " || t == ":") {
        return true;
    }
    int alpha = 0;
    for (char ch : t) {
        if (std::isalpha(static_cast<unsigned char>(ch))) {
            ++alpha;
        }
    }
    return alpha < 2;
}

static Severity severity_from_output_call(const std::string& call_name)
{
    const std::string c = upper(call_name);
    if (c.find("FATAL") != std::string::npos) {
        return Severity::Fatal;
    }
    if (c.find("ERR") != std::string::npos || c == "CERR" || c.find("THROW") != std::string::npos) {
        return Severity::Error;
    }
    if (c.find("WARN") != std::string::npos) {
        return Severity::Warning;
    }
    return Severity::Info;
}

static std::string output_class_hint_from_call(const std::string& call_name)
{
    const std::string c = upper(call_name);
    if (c.find("TALK") != std::string::npos) return "OUTPUT_CLASS:TALK";
    if (c.find("ECHO") != std::string::npos) return "OUTPUT_CLASS:ECHO";
    if (c.find("NOTIFY") != std::string::npos || c.find("NOTE") != std::string::npos) return "OUTPUT_CLASS:NOTIFY";
    if (c.find("STATUS") != std::string::npos) return "OUTPUT_CLASS:STATUS";
    if (c.find("DIAG") != std::string::npos || c.find("VERBOSE") != std::string::npos) return "OUTPUT_CLASS:DIAGNOSTIC";
    if (c.find("WARN") != std::string::npos) return "OUTPUT_CLASS:WARNING";
    if (c.find("ERR") != std::string::npos || c == "CERR" || c.find("THROW") != std::string::npos) return "OUTPUT_CLASS:ERROR";
    if (c.find("PROMPT") != std::string::npos) return "OUTPUT_CLASS:PROMPT";
    if (c == "COUT") return "OUTPUT_CLASS:RAW_COUT";
    return "OUTPUT_CLASS:UNCLASSIFIED";
}

static Artifact command_artifact(const SourceMineOptions& options,
                                 const std::string& command,
                                 ArtifactKind kind,
                                 const std::string& name,
                                 const std::string& text,
                                 const std::string& detail,
                                 const std::string& evidence,
                                 Severity severity = Severity::None,
                                 Confidence confidence = Confidence::Heuristic)
{
    return make_artifact(options.default_catalog,
                         command,
                         Owner { OwnerKind::Command, command },
                         kind,
                         SourceKind::SourceMiner,
                         confidence,
                         severity,
                         name,
                         text,
                         0,
                         detail,
                         evidence);
}

static void add_unique(std::vector<Artifact>& artifacts,
                       std::set<std::string>& keys,
                       Artifact artifact)
{
    if (total_budget_exhausted(artifacts)) {
        return;
    }

    const std::string key = artifact.catalog + "|" + artifact.command + "|" +
                            std::string(to_string(artifact.kind)) + "|" + artifact.name + "|" +
                            artifact.text + "|" + artifact.evidence;
    if (keys.insert(key).second) {
        artifacts.push_back(std::move(artifact));
    }
}

static void mine_command_identity(const SourceMineOptions& options,
                                  const fs::path& file,
                                  const std::string& text,
                                  const std::vector<std::string>& commands,
                                  std::vector<Artifact>& artifacts,
                                  std::set<std::string>& unique,
                                  SourceMineCounts& counts)
{
    if (!options.mine_command_identity) {
        return;
    }

    for (const auto& command : commands) {
        const std::string ev = evidence_for(file, 0, "command_context", "source=registration-or-filename");
        add_unique(artifacts, unique,
                   command_artifact(options,
                                    command,
                                    ArtifactKind::SourceFact,
                                    "COMMAND_CONTEXT",
                                    command,
                                    "Mined command context. This identifies ownership for nearby source facts; it is not a curated help entry.",
                                    ev,
                                    Severity::None,
                                    Confidence::Inferred));
        ++counts.command_identity_facts;
    }
    (void)text;
}

static void mine_arguments(const SourceMineOptions& options,
                           const fs::path& file,
                           const std::string& text,
                           const std::vector<std::string>& commands,
                           std::vector<Artifact>& artifacts,
                           std::set<std::string>& unique,
                           SourceMineCounts& counts)
{
    if (!options.mine_arguments || commands.empty()) {
        return;
    }

    struct Pattern {
        const char* name;
        std::regex rx;
        int group;
    };

    const std::vector<Pattern> patterns = {
        { "case_token", std::regex(R"(\bcase\s+(?:Token::|TOK_|TOKEN_)([A-Z][A-Z0-9_]+)\b)"), 1 },
        { "token_ref", std::regex(R"(\b(?:Token::|TOK_|TOKEN_)([A-Z][A-Z0-9_]+)\b)"), 1 },
        { "has_switch", std::regex(R"(\b(?:hasSwitch|hasFlag|seenSwitch|has_kw|is_kw|match_kw)\s*\(\s*[\"']([A-Za-z][A-Za-z0-9_]{1,31})[\"']\s*\))"), 1 },
        { "set_on_off", std::regex(R"(\bSET\s+([A-Z][A-Z0-9_]+)\s+(ON|OFF)\b)"), 1 },
        { "no_toggle", std::regex(R"(\bNO([A-Z][A-Z0-9_]+)\b)"), 1 }
    };

    for (const auto& pat : patterns) {
        int matches_for_pattern = 0;
        for (auto it = std::sregex_iterator(text.begin(), text.end(), pat.rx);
             it != std::sregex_iterator() && matches_for_pattern < kMaxMatchesPerPatternPerFile && !total_budget_exhausted(artifacts);
             ++it, ++matches_for_pattern) {
            std::string token = normalize_token((*it)[pat.group].str());
            if (std::string(pat.name) == "no_toggle") {
                token = "NO" + token;
            }
            if (!is_likely_argument_token(token)) {
                continue;
            }

            const int line = line_for_pos(text, static_cast<std::size_t>(it->position()));
            for (const auto& command : commands) {
                add_unique(artifacts, unique,
                           command_artifact(options,
                                            command,
                                            ArtifactKind::Argument,
                                            token,
                                            token,
                                            "Mined command argument/switch candidate. Promote only after validation against parser behavior or curated command docs.",
                                            evidence_for(file, line, pat.name),
                                            Severity::None,
                                            Confidence::Heuristic));
                ++counts.argument_candidates;
            }
        }
    }
}

static void mine_syntax_strings(const SourceMineOptions& options,
                                const fs::path& file,
                                const std::string& text,
                                const std::vector<std::string>& commands,
                                std::vector<Artifact>& artifacts,
                                std::set<std::string>& unique,
                                SourceMineCounts& counts)
{
    if (!options.mine_syntax_strings || commands.empty()) {
        return;
    }

    const std::regex syntax_assign(R"(\b(?:syntax|usage)\s*(?:=|:)\s*[\"']([^\"'\n]{3,240})[\"'])", std::regex::icase);
    const std::regex syntax_call(R"(\b(?:addSyntax|syntax_form|usage_form)\s*\(\s*[\"']([^\"'\n]{3,240})[\"'])", std::regex::icase);

    const std::vector<std::pair<const char*, std::regex>> patterns = {
        { "syntax_assign", syntax_assign },
        { "syntax_call", syntax_call }
    };

    for (const auto& pat : patterns) {
        int matches_for_pattern = 0;
        for (auto it = std::sregex_iterator(text.begin(), text.end(), pat.second);
             it != std::sregex_iterator() && matches_for_pattern < kMaxMatchesPerPatternPerFile && !total_budget_exhausted(artifacts);
             ++it, ++matches_for_pattern) {
            const std::string value = trim((*it)[1].str());
            if (is_noise_string(value)) {
                continue;
            }
            const int line = line_for_pos(text, static_cast<std::size_t>(it->position()));
            for (const auto& command : commands) {
                add_unique(artifacts, unique,
                           command_artifact(options,
                                            command,
                                            ArtifactKind::Syntax,
                                            "MINED_SYNTAX",
                                            value,
                                            "Mined syntax/usage string candidate. Curated command docs remain authoritative.",
                                            evidence_for(file, line, pat.first),
                                            Severity::None,
                                            Confidence::Heuristic));
                ++counts.syntax_candidates;
            }
        }
    }
}


static std::string decode_cpp_string_literal(std::string s)
{
    std::string out;
    out.reserve(s.size());
    bool esc = false;
    for (char ch : s) {
        if (!esc) {
            if (ch == '\\') {
                esc = true;
            } else {
                out.push_back(ch);
            }
            continue;
        }

        switch (ch) {
            case 'n': out.push_back('\n'); break;
            case 'r': out.push_back('\r'); break;
            case 't': out.push_back('\t'); break;
            case '\\': out.push_back('\\'); break;
            case '"': out.push_back('"'); break;
            case '\'': out.push_back('\''); break;
            default:
                out.push_back(ch);
                break;
        }
        esc = false;
    }
    if (esc) {
        out.push_back('\\');
    }
    return out;
}

static std::vector<std::string> split_text_lines(const std::string& text)
{
    std::vector<std::string> lines;
    std::string line;
    std::istringstream in(text);
    while (std::getline(in, line)) {
        line = trim(line);
        if (!line.empty()) {
            lines.push_back(line);
        }
    }
    return lines;
}

static bool has_usage_or_syntax_prefix(const std::string& line)
{
    const std::string u = upper(trim(line));
    return u.rfind("USAGE:", 0) == 0 ||
           u.rfind("SYNTAX:", 0) == 0 ||
           u == "USAGE" ||
           u == "SYNTAX";
}

static std::string strip_usage_or_syntax_prefix(std::string line)
{
    line = trim(line);
    const std::string u = upper(line);
    auto strip_n = [&](std::size_t n) {
        line = trim(line.substr(n));
    };

    if (u.rfind("USAGE:", 0) == 0) strip_n(6);
    else if (u.rfind("SYNTAX:", 0) == 0) strip_n(7);
    else if (u == "USAGE" || u == "SYNTAX") line.clear();
    return line;
}

static bool looks_like_usage_header(const std::string& line)
{
    const std::string u = upper(trim(line));
    if (has_usage_or_syntax_prefix(u)) {
        return true;
    }
    // Examples: "REL syntax", "LMDB command (per-area):"
    return u.find(" SYNTAX") != std::string::npos ||
           u.find(" COMMAND") != std::string::npos ||
           u.find(" HELP") != std::string::npos;
}

static bool looks_like_command_syntax_line(const std::string& line)
{
    std::string t = strip_usage_or_syntax_prefix(line);
    t = trim(t);
    if (t.empty()) {
        return false;
    }
    if (t.size() < 3 || t.size() > 260) {
        return false;
    }

    // Syntax forms are usually upper-case command names followed by options,
    // placeholders, pipes, brackets, or subcommands.
    if (!std::isupper(static_cast<unsigned char>(t.front()))) {
        return false;
    }

    static const std::regex syntax_start(R"(^[A-Z][A-Z0-9_]*(?:\s+[A-Z][A-Z0-9_]*)?(?:\s|$|\[|<|\||\())");
    if (!std::regex_search(t, syntax_start)) {
        return false;
    }

    // Avoid obvious prose headings that start with a capital word.
    const std::string u = upper(t);
    static const std::unordered_set<std::string> prose_heads = {
        "EXAMPLES", "NOTES", "WARNING", "WARNINGS", "STATUS", "PURPOSE", "ALIASES"
    };
    if (prose_heads.count(u) > 0) {
        return false;
    }

    return true;
}

static std::string command_from_usage_function_name(const std::string& fn)
{
    std::string n = fn;
    const std::string u = upper(n);

    auto strip_prefix = [&](const std::string& prefix) {
        if (upper(n).rfind(prefix, 0) == 0) {
            n = n.substr(prefix.size());
            return true;
        }
        return false;
    };
    auto strip_suffix = [&](const std::string& suffix) {
        const std::string un = upper(n);
        if (un.size() >= suffix.size() && un.compare(un.size() - suffix.size(), suffix.size(), suffix) == 0) {
            n = n.substr(0, n.size() - suffix.size());
            return true;
        }
        return false;
    };

    strip_prefix("HELP_");
    strip_prefix("USAGE_");
    strip_suffix("_HELP");
    strip_suffix("_USAGE");

    if (n.empty() || upper(n) == "HELP" || upper(n) == "USAGE") {
        return {};
    }

    std::replace(n.begin(), n.end(), '_', ' ');
    return normalize_token(n);
}

static std::string command_from_syntax_line(const std::string& line)
{
    std::string t = strip_usage_or_syntax_prefix(line);
    t = trim(t);
    if (t.empty()) {
        return {};
    }

    std::istringstream in(t);
    std::string first;
    std::string second;
    in >> first;
    in >> second;
    first = normalize_token(first);
    second = normalize_token(second);

    if (first.empty()) {
        return {};
    }

    if (first == "SET" && !second.empty()) {
        return "SET " + second;
    }
    if (is_compact_set_family_command(first)) {
        return canonicalize_set_family_command(first);
    }
    if (first == "TABLE" && second == "BUFFER") {
        return "TABLE BUFFER";
    }

    return first;
}

static std::string command_from_file_or_usage(const fs::path& file,
                                              const std::vector<std::string>& commands,
                                              const std::vector<std::string>& lines,
                                              const std::string& function_name = {})
{
    const std::string fn_cmd = command_from_usage_function_name(function_name);
    if (!fn_cmd.empty()) {
        return fn_cmd;
    }

    for (const auto& line : lines) {
        const std::string cmd = command_from_syntax_line(line);
        if (!cmd.empty()) {
            return cmd;
        }
    }

    if (!commands.empty()) {
        return commands.front();
    }

    const std::string hint = command_hint_from_path(file);
    if (!hint.empty()) {
        return hint;
    }

    const std::string stem = upper(file.stem().string());
    if (stem == "TABLE_BUFFER") {
        return "TABLE BUFFER";
    }
    return {};
}

static std::size_t find_matching_brace(const std::string& text, std::size_t open_pos)
{
    if (open_pos >= text.size() || text[open_pos] != '{') {
        return std::string::npos;
    }

    int depth = 0;
    bool in_string = false;
    bool in_char = false;
    bool in_line_comment = false;
    bool in_block_comment = false;
    bool escaped = false;

    for (std::size_t i = open_pos; i < text.size(); ++i) {
        const char ch = text[i];
        const char next = (i + 1 < text.size()) ? text[i + 1] : '\0';

        if (in_line_comment) {
            if (ch == '\n') in_line_comment = false;
            continue;
        }
        if (in_block_comment) {
            if (ch == '*' && next == '/') {
                in_block_comment = false;
                ++i;
            }
            continue;
        }
        if (in_string) {
            if (escaped) {
                escaped = false;
            } else if (ch == '\\') {
                escaped = true;
            } else if (ch == '"') {
                in_string = false;
            }
            continue;
        }
        if (in_char) {
            if (escaped) {
                escaped = false;
            } else if (ch == '\\') {
                escaped = true;
            } else if (ch == '\'') {
                in_char = false;
            }
            continue;
        }

        if (ch == '/' && next == '/') {
            in_line_comment = true;
            ++i;
            continue;
        }
        if (ch == '/' && next == '*') {
            in_block_comment = true;
            ++i;
            continue;
        }
        if (ch == '"') {
            in_string = true;
            continue;
        }
        if (ch == '\'') {
            in_char = true;
            continue;
        }

        if (ch == '{') {
            ++depth;
        } else if (ch == '}') {
            --depth;
            if (depth == 0) {
                return i;
            }
        }
    }

    return std::string::npos;
}

struct LiteralHit {
    std::string text;
    std::size_t position { 0 };
};

static std::vector<LiteralHit> cout_string_literals_in_range(const std::string& text,
                                                             std::size_t begin,
                                                             std::size_t end)
{
    std::vector<LiteralHit> hits;
    if (begin >= text.size() || end <= begin) {
        return hits;
    }
    end = std::min(end, text.size());

    // Intentionally require stream-output syntax. This avoids re-mining catalog
    // initializer prose while still catching local usage/help emitters.
    const std::regex stream_literal("(?:std::)?cout\\s*<<|<<\\s*\"((?:\\\\.|[^\"\\\\])*)\"");
    const std::string slice = text.substr(begin, end - begin);

    for (auto it = std::sregex_iterator(slice.begin(), slice.end(), stream_literal);
         it != std::sregex_iterator(); ++it) {
        hits.push_back(LiteralHit { decode_cpp_string_literal((*it)[1].str()), begin + static_cast<std::size_t>(it->position()) });
    }
    return hits;
}

static void add_usage_lines_as_artifacts(const SourceMineOptions& options,
                                         const fs::path& file,
                                         const std::vector<std::string>& commands,
                                         const std::string& command_hint,
                                         const std::vector<std::string>& lines,
                                         const std::string& evidence,
                                         std::vector<Artifact>& artifacts,
                                         std::set<std::string>& unique,
                                         SourceMineCounts& counts)
{
    if (lines.empty() || total_budget_exhausted(artifacts)) {
        return;
    }

    std::string command = command_hint;
    if (command.empty()) {
        command = command_from_file_or_usage(file, commands, lines);
    }
    if (command.empty()) {
        return;
    }

    int ordinal = 0;
    bool emitted_summary = false;

    for (const auto& raw_line : lines) {
        if (total_budget_exhausted(artifacts)) {
            return;
        }

        std::string line = trim(raw_line);
        if (line.empty()) {
            continue;
        }

        if (has_usage_or_syntax_prefix(line)) {
            const std::string rest = strip_usage_or_syntax_prefix(line);
            if (rest.empty()) {
                if (!emitted_summary) {
                    add_unique(artifacts, unique,
                               command_artifact(options,
                                                command,
                                                ArtifactKind::Summary,
                                                "STRUCTURED_USAGE_HEADER",
                                                upper(command) + " usage",
                                                "Mined from a command-local Usage/Syntax output block. Promote to DOTREF/FOXREF or CommandDoc when curated.",
                                                evidence,
                                                Severity::None,
                                                Confidence::Inferred));
                    emitted_summary = true;
                }
                continue;
            }
            line = rest;
        } else if (!emitted_summary && looks_like_usage_header(line) && !looks_like_command_syntax_line(line)) {
            add_unique(artifacts, unique,
                       command_artifact(options,
                                        command,
                                        ArtifactKind::Summary,
                                        "STRUCTURED_USAGE_HEADER",
                                        line,
                                        "Mined from a command-local *_usage/*_help output block. Promote to DOTREF/FOXREF or CommandDoc when curated.",
                                        evidence,
                                        Severity::None,
                                        Confidence::Inferred));
            emitted_summary = true;
            continue;
        }

        std::string detail;
        const std::size_t hash = line.find('#');
        if (hash != std::string::npos) {
            detail = trim(line.substr(hash + 1));
            line = trim(line.substr(0, hash));
        }

        if (!looks_like_command_syntax_line(line)) {
            continue;
        }

        Artifact artifact = command_artifact(options,
                                             command,
                                             ArtifactKind::Syntax,
                                             "STRUCTURED_USAGE",
                                             line,
                                             detail.empty()
                                                ? "Mined from command-local usage/help output. Curated catalogs remain authoritative."
                                                : detail,
                                             evidence,
                                             Severity::None,
                                             Confidence::Inferred);
        artifact.ordinal = ++ordinal;
        add_unique(artifacts, unique, std::move(artifact));
        ++counts.syntax_candidates;
    }
}


struct UsageContractBlock {
    std::string content;
    std::size_t position { 0 };
};

static std::vector<UsageContractBlock> extract_usage_contract_blocks(const std::string& text)
{
    std::vector<UsageContractBlock> blocks;
    std::size_t pos = 0;
    while ((pos = text.find("@dottalk.usage v1", pos)) != std::string::npos) {
        std::size_t raw_begin = text.rfind("R\"", pos);
        if (raw_begin == std::string::npos) {
            // Fallback: collect a comment/plain-text block until two blank lines.
            std::size_t line_begin = text.rfind('\n', pos);
            line_begin = (line_begin == std::string::npos) ? pos : line_begin + 1;
            std::size_t end = text.find("\n\n", pos);
            if (end == std::string::npos) end = std::min(text.size(), pos + 4096u);
            blocks.push_back(UsageContractBlock { text.substr(line_begin, end - line_begin), line_begin });
            pos = end;
            continue;
        }

        const std::size_t delim_start = raw_begin + 2;
        const std::size_t open = text.find('(', delim_start);
        if (open == std::string::npos || open > pos) {
            pos += 18;
            continue;
        }

        const std::string delim = text.substr(delim_start, open - delim_start);
        const std::string close_token = ")" + delim + "\"";
        const std::size_t close = text.find(close_token, pos);
        if (close == std::string::npos || close <= open) {
            pos += 18;
            continue;
        }

        blocks.push_back(UsageContractBlock { text.substr(open + 1, close - (open + 1)), raw_begin });
        pos = close + close_token.size();
    }
    return blocks;
}

static bool is_contract_section_name(const std::string& s)
{
    const std::string u = upper(trim(s));
    static const std::unordered_set<std::string> names = {
        "USAGE", "SYNTAX", "EXAMPLES", "EXAMPLE", "NOTES", "NOTE",
        "WARNINGS", "WARNING", "RELATED", "ALIASES", "ALIAS", "DETAIL", "DETAILS"
    };
    return names.count(u) > 0;
}

struct ParsedUsageContract {
    std::string owner;
    std::string catalog;
    std::string command;
    std::string category;
    std::string status;
    std::string summary;
    std::vector<std::string> aliases;
    std::unordered_map<std::string, std::vector<std::string>> sections;
};

static void split_owner_into_catalog_command(const std::string& owner,
                                             std::string& catalog,
                                             std::string& command)
{
    const std::string o = trim(owner);
    const std::size_t bar = o.find('|');
    if (bar != std::string::npos) {
        catalog = normalize_token(o.substr(0, bar));
        command = canonicalize_set_family_command(o.substr(bar + 1));
        return;
    }
    command = canonicalize_set_family_command(o);
}

static ParsedUsageContract parse_usage_contract(const std::string& body)
{
    ParsedUsageContract c;
    std::string current_section;
    std::istringstream in(body);
    std::string raw;

    while (std::getline(in, raw)) {
        std::string line = trim(raw);
        if (line.empty()) {
            continue;
        }
        if (line.rfind("//", 0) == 0) {
            line = trim(line.substr(2));
        }
        if (line.empty()) {
            continue;
        }
        if (line.rfind("@dottalk.usage", 0) == 0) {
            continue;
        }

        const std::size_t colon = line.find(':');
        if (colon != std::string::npos) {
            const std::string key = normalize_token(line.substr(0, colon));
            const std::string value = trim(line.substr(colon + 1));

            if (key == "OWNER") {
                c.owner = value;
                std::string raw_owner_command;
                std::string ignored_catalog;
                split_owner_into_catalog_command(value, c.catalog, c.command);
                const std::size_t bar = trim(value).find('|');
                raw_owner_command = (bar == std::string::npos) ? normalize_token(value)
                                                               : normalize_token(trim(value).substr(bar + 1));
                add_set_family_alias_if_needed(raw_owner_command, c.aliases);
                current_section.clear();
                continue;
            }
            if (key == "COMMAND") {
                const std::string raw_command = normalize_token(value);
                c.command = canonicalize_set_family_command(raw_command);
                add_set_family_alias_if_needed(raw_command, c.aliases);
                current_section.clear();
                continue;
            }
            if (key == "CATALOG") {
                c.catalog = normalize_token(value);
                current_section.clear();
                continue;
            }
            if (key == "CATEGORY") {
                c.category = value;
                current_section.clear();
                continue;
            }
            if (key == "STATUS") {
                c.status = value;
                current_section.clear();
                continue;
            }
            if (key == "SUMMARY") {
                c.summary = value;
                current_section.clear();
                continue;
            }
            if (is_contract_section_name(key)) {
                current_section = key;
                if (!value.empty()) {
                    c.sections[current_section].push_back(value);
                }
                continue;
            }
        }

        if (!current_section.empty()) {
            c.sections[current_section].push_back(line);
        }
    }

    if (c.catalog.empty()) {
        c.catalog = "DOT";
    }
    return c;
}

static std::string join_lines(const std::vector<std::string>& lines)
{
    std::ostringstream out;
    for (std::size_t i = 0; i < lines.size(); ++i) {
        if (i) out << "\n";
        out << lines[i];
    }
    return out.str();
}

static Artifact contract_artifact(const ParsedUsageContract& c,
                                  ArtifactKind kind,
                                  const std::string& name,
                                  const std::string& text,
                                  int ordinal,
                                  const std::string& detail,
                                  const std::string& evidence,
                                  Severity severity = Severity::None)
{
    return make_artifact(c.catalog.empty() ? "DOT" : c.catalog,
                         c.command,
                         Owner { OwnerKind::Command, c.command },
                         kind,
                         SourceKind::UsageContract,
                         Confidence::Authoritative,
                         severity,
                         name,
                         text,
                         ordinal,
                         detail,
                         evidence);
}

static void add_contract_section_rows(const ParsedUsageContract& c,
                                      const std::string& section,
                                      ArtifactKind kind,
                                      const std::string& name,
                                      const std::string& evidence,
                                      std::vector<Artifact>& artifacts,
                                      std::set<std::string>& unique,
                                      SourceMineCounts& counts)
{
    auto it = c.sections.find(section);
    if (it == c.sections.end()) {
        return;
    }

    int ordinal = 0;
    for (std::string line : it->second) {
        if (total_budget_exhausted(artifacts)) return;
        line = trim(line);
        if (line.empty()) continue;

        std::string detail;
        const std::size_t hash = line.find('#');
        if (hash != std::string::npos) {
            detail = trim(line.substr(hash + 1));
            line = trim(line.substr(0, hash));
        }

        add_unique(artifacts, unique,
                   contract_artifact(c, kind, name, line, ++ordinal, detail, evidence));
        if (kind == ArtifactKind::Syntax) {
            ++counts.syntax_candidates;
        }
    }
}

static void mine_usage_contracts(const SourceMineOptions& options,
                                 const fs::path& file,
                                 const std::string& text,
                                 const std::vector<std::string>& commands,
                                 std::vector<Artifact>& artifacts,
                                 std::set<std::string>& unique,
                                 SourceMineCounts& counts)
{
    if (!options.mine_syntax_strings || total_budget_exhausted(artifacts)) {
        return;
    }

    for (const auto& block : extract_usage_contract_blocks(text)) {
        if (total_budget_exhausted(artifacts)) return;
        ParsedUsageContract c = parse_usage_contract(block.content);
        if (c.command.empty()) {
            std::vector<std::string> probe;
            auto uit = c.sections.find("USAGE");
            if (uit != c.sections.end()) probe = uit->second;
            auto sit = c.sections.find("SYNTAX");
            if (probe.empty() && sit != c.sections.end()) probe = sit->second;
            c.command = command_from_file_or_usage(file, commands, probe);
        }
        if (!c.command.empty()) {
            const std::string raw_command = normalize_token(c.command);
            c.command = canonicalize_set_family_command(raw_command);
            add_set_family_alias_if_needed(raw_command, c.aliases);
        }
        if (c.command.empty()) {
            continue;
        }
        if (c.catalog.empty()) {
            c.catalog = options.default_catalog;
        }

        const int line_no = line_for_pos(text, block.position);
        const std::string ev = evidence_for(file, line_no, "usage_contract", "version=v1");

        int alias_ordinal = 0;
        for (const auto& alias : c.aliases) {
            add_unique(artifacts, unique,
                       contract_artifact(c,
                                         ArtifactKind::Alias,
                                         "CONTRACT_ALIAS",
                                         alias,
                                         ++alias_ordinal,
                                         "Compatibility compact SET-family verb routes to canonical SET * topic.",
                                         ev));
        }

        std::vector<std::string> usage_payload;
        auto uit = c.sections.find("USAGE");
        if (uit != c.sections.end()) usage_payload.insert(usage_payload.end(), uit->second.begin(), uit->second.end());
        auto sit = c.sections.find("SYNTAX");
        if (sit != c.sections.end()) usage_payload.insert(usage_payload.end(), sit->second.begin(), sit->second.end());

        std::ostringstream detail;
        if (!c.category.empty()) detail << "category=" << c.category << "\n";
        if (!c.status.empty()) detail << "status=" << c.status << "\n";
        if (!usage_payload.empty()) detail << join_lines(usage_payload);

        add_unique(artifacts, unique,
                   contract_artifact(c,
                                     ArtifactKind::Usage,
                                     "USAGE_CONTRACT",
                                     c.summary.empty() ? (upper(c.command) + " usage contract") : c.summary,
                                     0,
                                     detail.str(),
                                     ev));

        if (!c.summary.empty()) {
            add_unique(artifacts, unique,
                       contract_artifact(c,
                                         ArtifactKind::Summary,
                                         "CONTRACT_SUMMARY",
                                         c.summary,
                                         0,
                                         "Command-owned @dottalk.usage v1 summary.",
                                         ev));
        }

        // USAGE lines include title/header plus syntax forms. Keep a USAGE row
        // for human review, and emit syntax rows only for command-shaped lines.
        int usage_ordinal = 0;
        auto usage_it = c.sections.find("USAGE");
        if (usage_it != c.sections.end()) {
            for (std::string line : usage_it->second) {
                if (total_budget_exhausted(artifacts)) return;
                line = trim(line);
                if (line.empty()) continue;
                std::string detail_text;
                const std::size_t hash = line.find('#');
                if (hash != std::string::npos) {
                    detail_text = trim(line.substr(hash + 1));
                    line = trim(line.substr(0, hash));
                }
                add_unique(artifacts, unique,
                           contract_artifact(c,
                                             ArtifactKind::Usage,
                                             "CONTRACT_USAGE_LINE",
                                             line,
                                             ++usage_ordinal,
                                             detail_text,
                                             ev));
                if (looks_like_command_syntax_line(line)) {
                    add_unique(artifacts, unique,
                               contract_artifact(c,
                                                 ArtifactKind::Syntax,
                                                 "CONTRACT_SYNTAX",
                                                 line,
                                                 usage_ordinal,
                                                 detail_text,
                                                 ev));
                    ++counts.syntax_candidates;
                }
            }
        }

        add_contract_section_rows(c, "SYNTAX", ArtifactKind::Syntax, "CONTRACT_SYNTAX", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "EXAMPLE", ArtifactKind::Example, "CONTRACT_EXAMPLE", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "EXAMPLES", ArtifactKind::Example, "CONTRACT_EXAMPLE", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "NOTE", ArtifactKind::Note, "CONTRACT_NOTE", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "NOTES", ArtifactKind::Note, "CONTRACT_NOTE", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "WARNING", ArtifactKind::Warning, "CONTRACT_WARNING", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "WARNINGS", ArtifactKind::Warning, "CONTRACT_WARNING", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "RELATED", ArtifactKind::Related, "CONTRACT_RELATED", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "ALIAS", ArtifactKind::Alias, "CONTRACT_ALIAS", ev, artifacts, unique, counts);
        add_contract_section_rows(c, "ALIASES", ArtifactKind::Alias, "CONTRACT_ALIAS", ev, artifacts, unique, counts);
    }
}

static void mine_usage_help_functions(const SourceMineOptions& options,
                                      const fs::path& file,
                                      const std::string& text,
                                      const std::vector<std::string>& commands,
                                      std::vector<Artifact>& artifacts,
                                      std::set<std::string>& unique,
                                      SourceMineCounts& counts)
{
    if (!options.mine_syntax_strings) {
        return;
    }

    const std::regex fn_rx(R"(\b(?:static\s+)?(?:inline\s+)?void\s+([A-Za-z_][A-Za-z0-9_]*(?:_usage|_help|usage|help))\s*\([^;{}]*\)\s*\{)", std::regex::icase);
    int matches = 0;

    for (auto it = std::sregex_iterator(text.begin(), text.end(), fn_rx);
         it != std::sregex_iterator() && matches < kMaxMatchesPerPatternPerFile && !total_budget_exhausted(artifacts);
         ++it, ++matches) {
        const std::string fn_name = (*it)[1].str();
        const std::size_t open = static_cast<std::size_t>(it->position() + it->length() - 1);
        const std::size_t close = find_matching_brace(text, open);
        if (close == std::string::npos || close <= open) {
            continue;
        }

        std::vector<std::string> lines;
        for (const auto& hit : cout_string_literals_in_range(text, open, close)) {
            for (const auto& line : split_text_lines(hit.text)) {
                lines.push_back(line);
            }
        }
        if (lines.empty()) {
            continue;
        }

        const int line_no = line_for_pos(text, static_cast<std::size_t>(it->position()));
        const std::string cmd = command_from_file_or_usage(file, commands, lines, fn_name);
        add_usage_lines_as_artifacts(options,
                                     file,
                                     commands,
                                     cmd,
                                     lines,
                                     evidence_for(file, line_no, "usage_help_function", "function=" + fn_name),
                                     artifacts,
                                     unique,
                                     counts);
    }
}

static void mine_usage_output_blocks(const SourceMineOptions& options,
                                     const fs::path& file,
                                     const std::string& text,
                                     const std::vector<std::string>& commands,
                                     std::vector<Artifact>& artifacts,
                                     std::set<std::string>& unique,
                                     SourceMineCounts& counts)
{
    if (!options.mine_syntax_strings || total_budget_exhausted(artifacts)) {
        return;
    }

    const std::regex usage_start("(?:std::)?cout\\s*<<\\s*\"((?:\\\\.|[^\"\\\\])*(?:Usage|usage|Syntax|syntax)(?:\\\\.|[^\"\\\\])*)\"");
    int blocks = 0;

    for (auto it = std::sregex_iterator(text.begin(), text.end(), usage_start);
         it != std::sregex_iterator() && blocks < kMaxMatchesPerPatternPerFile && !total_budget_exhausted(artifacts);
         ++it, ++blocks) {
        const std::size_t start = static_cast<std::size_t>(it->position());
        const std::size_t hard_end = std::min<std::size_t>(text.size(), start + 5000u);
        std::size_t end = hard_end;
        const std::size_t ret = text.find("return", start);
        if (ret != std::string::npos && ret < hard_end) {
            end = ret;
        }

        std::vector<std::string> lines;
        for (const auto& hit : cout_string_literals_in_range(text, start, end)) {
            for (const auto& line : split_text_lines(hit.text)) {
                lines.push_back(line);
            }
        }
        if (lines.empty()) {
            continue;
        }

        const int line_no = line_for_pos(text, start);
        const std::string cmd = command_from_file_or_usage(file, commands, lines);
        add_usage_lines_as_artifacts(options,
                                     file,
                                     commands,
                                     cmd,
                                     lines,
                                     evidence_for(file, line_no, "usage_output_block"),
                                     artifacts,
                                     unique,
                                     counts);
    }
}

static void mine_structured_usage_blocks(const SourceMineOptions& options,
                                         const fs::path& file,
                                         const std::string& text,
                                         const std::vector<std::string>& commands,
                                         std::vector<Artifact>& artifacts,
                                         std::set<std::string>& unique,
                                         SourceMineCounts& counts)
{
    mine_usage_help_functions(options, file, text, commands, artifacts, unique, counts);
    mine_usage_output_blocks(options, file, text, commands, artifacts, unique, counts);
}

static void mine_message_strings(const SourceMineOptions& options,
                                 const fs::path& file,
                                 const std::string& text,
                                 const std::vector<std::string>& commands,
                                 std::vector<Artifact>& artifacts,
                                 std::set<std::string>& unique,
                                 SourceMineCounts& counts)
{
    if (!options.mine_message_strings) {
        return;
    }

    struct Pattern {
        const char* name;
        std::regex rx;
        int call_group;
        int text_group;
    };

    const std::vector<Pattern> patterns = {
        { "std_stream", std::regex(R"((?:std::)?(cout|cerr)\s*<<\s*[\"']([^\"'\n]{3,240})[\"'])"), 1, 2 },
        { "router_call", std::regex(R"(\b(out|talk_line|console_note|status_line|notify|warning|error|debug_line|emit_talk|emit_notify|emit_warning|emit_error|emit_diagnostic)\s*\(\s*[\"']([^\"'\n]{3,240})[\"'])"), 1, 2 },
        { "throw_runtime", std::regex(R"(\bthrow\s+std::(?:runtime_error|logic_error|invalid_argument)\s*\(\s*[\"']([^\"'\n]{3,240})[\"'])"), 0, 1 }
    };

    std::vector<std::string> owners = commands;
    if (owners.empty()) {
        owners.push_back("");
    }

    for (const auto& pat : patterns) {
        int matches_for_pattern = 0;
        for (auto it = std::sregex_iterator(text.begin(), text.end(), pat.rx);
             it != std::sregex_iterator() && matches_for_pattern < kMaxMessageMatchesPerFile && !total_budget_exhausted(artifacts);
             ++it, ++matches_for_pattern) {
            const std::string msg = trim((*it)[pat.text_group].str());
            if (is_noise_string(msg)) {
                continue;
            }

            std::string call_name = pat.name;
            if (pat.call_group > 0) {
                call_name = (*it)[pat.call_group].str();
            }

            const Severity severity = severity_from_output_call(call_name);
            const std::string output_hint = output_class_hint_from_call(call_name);
            const int line = line_for_pos(text, static_cast<std::size_t>(it->position()));

            for (const auto& command : owners) {
                Owner owner = command.empty() ? Owner { OwnerKind::Miner, "SOURCE" }
                                              : Owner { OwnerKind::Command, command };
                Artifact artifact = make_artifact(options.default_catalog,
                                                  command,
                                                  owner,
                                                  ArtifactKind::Message,
                                                  SourceKind::SourceMiner,
                                                  Confidence::Heuristic,
                                                  severity,
                                                  output_hint,
                                                  msg,
                                                  0,
                                                  "Mined runtime-output string candidate. This is inventory evidence for later MessageDef/OutputClass adoption; do not treat as authoritative text.",
                                                  evidence_for(file, line, pat.name, "call=" + call_name));
                add_unique(artifacts, unique, std::move(artifact));
                ++counts.message_candidates;
            }
        }
    }
}

static void mine_message_symbols(const SourceMineOptions& options,
                                 const fs::path& file,
                                 const std::string& text,
                                 const std::vector<std::string>& commands,
                                 std::vector<Artifact>& artifacts,
                                 std::set<std::string>& unique,
                                 SourceMineCounts& counts)
{
    if (!options.mine_message_symbols) {
        return;
    }

    const std::regex symbol_rx(R"(\b(DT_[A-Z][A-Z0-9_]{4,80}|MessageId::[A-Za-z][A-Za-z0-9_]{2,80})\b)");
    std::vector<std::string> owners = commands;
    if (owners.empty()) {
        owners.push_back("");
    }

    int matches_for_pattern = 0;
    for (auto it = std::sregex_iterator(text.begin(), text.end(), symbol_rx);
         it != std::sregex_iterator() && matches_for_pattern < kMaxMatchesPerPatternPerFile && !total_budget_exhausted(artifacts);
         ++it, ++matches_for_pattern) {
        const std::string symbol = (*it)[1].str();
        const int line = line_for_pos(text, static_cast<std::size_t>(it->position()));
        for (const auto& command : owners) {
            Owner owner = command.empty() ? Owner { OwnerKind::Miner, "SOURCE" }
                                          : Owner { OwnerKind::Command, command };
            Artifact artifact = make_artifact(options.default_catalog,
                                              command,
                                              owner,
                                              ArtifactKind::SourceFact,
                                              SourceKind::SourceMiner,
                                              Confidence::Inferred,
                                              Severity::None,
                                              "MESSAGE_SYMBOL",
                                              symbol,
                                              0,
                                              "Mined stable runtime message symbol reference.",
                                              evidence_for(file, line, "message_symbol"));
            add_unique(artifacts, unique, std::move(artifact));
            ++counts.message_symbol_candidates;
        }
    }
}

static void mine_one_file(const SourceMineOptions& options,
                          const fs::path& file,
                          std::vector<Artifact>& artifacts,
                          std::set<std::string>& unique,
                          SourceMineCounts& counts)
{
    if (total_budget_exhausted(artifacts)) {
        return;
    }

    const std::size_t file_start_artifacts = artifacts.size();

    bool skipped = false;
    const std::string text = read_file_limited(file, options.max_file_bytes, skipped);
    if (skipped) {
        ++counts.files_skipped;
        return;
    }

    ++counts.files_scanned;
    const std::vector<std::string> commands = command_contexts_from_source(text, file);
    counts.command_contexts += static_cast<int>(commands.size());

    const bool catalog_authority = is_catalog_authority_file(file);
    const bool allow_runtime_messages = permits_runtime_message_mining(file, commands);

    if (!catalog_authority) {
        mine_command_identity(options, file, text, commands, artifacts, unique, counts);
        mine_arguments(options, file, text, commands, artifacts, unique, counts);
        mine_syntax_strings(options, file, text, commands, artifacts, unique, counts);
        mine_usage_contracts(options, file, text, commands, artifacts, unique, counts);
        mine_structured_usage_blocks(options, file, text, commands, artifacts, unique, counts);
    }

    if (allow_runtime_messages) {
        mine_message_strings(options, file, text, commands, artifacts, unique, counts);
    }

    mine_message_symbols(options, file, text, commands, artifacts, unique, counts);

    if (artifacts.size() > file_start_artifacts + kMaxArtifactsPerFile) {
        artifacts.resize(file_start_artifacts + kMaxArtifactsPerFile);
    }
}

} // namespace

SourceMineResult mine_source_roots(const std::vector<std::string>& roots,
                                   const SourceMineOptions& options)
{
    SourceMineResult result;
    std::set<std::string> unique;

    for (const auto& root_text : roots) {
        if (total_budget_exhausted(result.artifacts)) {
            break;
        }
        if (root_text.empty()) {
            continue;
        }

        fs::path root(root_text);
        std::error_code ec;
        if (!fs::exists(root, ec)) {
            continue;
        }

        if (fs::is_regular_file(root, ec)) {
            if (has_source_extension(root)) {
                ++result.counts.files_seen;
                if (is_skipped_source_file(root) || !is_help_surface_source_file(root)) {
                    ++result.counts.files_skipped;
                } else {
                    mine_one_file(options, root, result.artifacts, unique, result.counts);
                }
            }
            continue;
        }

        if (!fs::is_directory(root, ec) || is_skipped_dir(root)) {
            continue;
        }

        fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec);
        fs::recursive_directory_iterator end;

        while (!ec && it != end && !total_budget_exhausted(result.artifacts)) {
            const fs::path p = it->path();

            std::error_code stat_ec;
            if (it->is_directory(stat_ec)) {
                if (is_skipped_dir(p)) {
                    it.disable_recursion_pending();
                }
                it.increment(ec);
                continue;
            }

            if (it->is_regular_file(stat_ec) && has_source_extension(p)) {
                ++result.counts.files_seen;
                if (is_skipped_source_file(p) || !is_help_surface_source_file(p)) {
                    ++result.counts.files_skipped;
                } else {
                    mine_one_file(options, p, result.artifacts, unique, result.counts);
                }
            }

            it.increment(ec);
            if (ec) {
                // Do not let one unreadable/generated subtree abort the entire mine.
                // With skip_permission_denied this should be rare, but clearing here
                // keeps source mining a best-effort evidence pass.
                ec.clear();
            }
        }
    }

    for (std::size_t i = 0; i < result.artifacts.size(); ++i) {
        if (result.artifacts[i].id <= 0) {
            result.artifacts[i].id = static_cast<int>(i + 1);
        }
    }

    result.counts.artifacts = static_cast<int>(result.artifacts.size());
    return result;
}

std::vector<Artifact> mine_source_artifacts(const std::vector<std::string>& roots,
                                            const SourceMineOptions& options)
{
    return mine_source_roots(roots, options).artifacts;
}

} // namespace dottalk::helpdata
