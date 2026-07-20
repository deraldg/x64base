// ============================================================================
// File: src/meta/metacollect.cpp
// Purpose: Read-only source and metadata fact extraction for metacollect.
// Boundary: Scan source and metadata DBFs only; emit reports; never mutate DBFs.
// ============================================================================

#include "dt/meta/metacollect.hpp"

#include "cli/expr/fn_date.hpp"
#include "cli/expr/fn_numeric.hpp"
#include "cli/expr/fn_string.hpp"
#include "cli/expr/function_catalog.hpp"
#include "datadict/ddict_dbf_reader.hpp"
#include "datadict/ddict_read_helpers.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <map>
#include <ostream>
#include <regex>
#include <sstream>
#include <string_view>
#include <unordered_map>
#include <unordered_set>
#include <utility>

namespace dt::meta {
namespace {

namespace fs = std::filesystem;
using dottalk::datadict::DDictRow;

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

std::string squeeze_ws(std::string value) {
    std::string out;
    out.reserve(value.size());
    bool prev_space = false;
    for (char ch : value) {
        const bool is_space = ch == '\r' || ch == '\n' || ch == '\t' || ch == ' ';
        if (is_space) {
            if (!prev_space && !out.empty()) {
                out.push_back(' ');
            }
            prev_space = true;
        } else {
            out.push_back(ch);
            prev_space = false;
        }
    }
    return dottalk::datadict::trim_copy(out);
}

std::string join_flat(const std::vector<std::string>& items, const char* sep = " | ") {
    std::string out;
    bool first = true;
    for (const auto& item : items) {
        const auto flat = squeeze_ws(item);
        if (flat.empty()) {
            continue;
        }
        if (!first) {
            out += sep;
        }
        out += flat;
        first = false;
    }
    return out;
}

std::string path_for_fact(const fs::path& workspace_root, const fs::path& file) {
    std::error_code ec;
    const auto rel = fs::relative(file, workspace_root, ec);
    if (!ec) {
        return normalize_slashes(rel.string());
    }
    return normalize_slashes(file.string());
}

std::uint32_t dbf_record_count(const fs::path& path) {
    std::ifstream in(path, std::ios::binary);
    if (!in) {
        return 0;
    }

    unsigned char header[8] = {};
    in.read(reinterpret_cast<char*>(header), sizeof(header));
    if (in.gcount() < static_cast<std::streamsize>(sizeof(header))) {
        return 0;
    }

    return static_cast<std::uint32_t>(header[4]) |
           (static_cast<std::uint32_t>(header[5]) << 8U) |
           (static_cast<std::uint32_t>(header[6]) << 16U) |
           (static_cast<std::uint32_t>(header[7]) << 24U);
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

fs::path default_metadata_root(const fs::path& workspace_root) {
    const auto direct = workspace_root / "data" / "metadata";
    if (fs::exists(direct)) {
        return direct;
    }

    const auto runtime = workspace_root / "dottalkpp" / "data" / "metadata";
    if (fs::exists(runtime)) {
        return runtime;
    }

    return direct;
}

bool is_ignored_path(const fs::path& path) {
    const auto text = normalize_slashes(path.string());
    return text.find("/build/") != std::string::npos ||
           text.find("/_drops/") != std::string::npos ||
           text.find("/docs/generated/") != std::string::npos ||
           text.find("/.git/") != std::string::npos;
}

std::vector<SysFuncSeedRow> build_sysfunc_seed_rows() {
    std::unordered_map<std::string, SysFuncSeedRow> by_name;

    const auto docs = dottalk::expr::all_function_docs();
    for (const auto* doc : docs) {
        if (!doc) {
            continue;
        }

        SysFuncSeedRow row;
        row.func_id = "FN_" + upper_ascii(doc->name);
        row.can_name = upper_ascii(doc->name);
        row.disp_name = doc->name;
        row.def_locale = "en-US";
        row.region_id = "GLOBAL";
        row.func_cat = dottalk::expr::to_string(doc->category);
        row.min_args = static_cast<int>(doc->min_args);
        row.max_args = static_cast<int>(doc->max_args);
        row.impl_stat = "implemented";
        row.vis_tier = "core";
        row.owner = "expression_engine";
        row.src_auth = "function_catalog";
        row.src_file = "src/cli/expr/function_catalog.cpp";
        row.handler.clear();
        row.calc_call = true;
        row.pub_surf = true;
        row.self_reg = false;
        row.msg_cat = false;
        row.active = true;

        std::vector<std::string> note_parts;
        if (!doc->summary.empty()) {
            note_parts.push_back("summary=" + squeeze_ws(doc->summary));
        }
        if (!doc->aliases.empty()) {
            note_parts.push_back("aliases=" + join_flat(doc->aliases));
        }
        if (!doc->syntax.empty()) {
            note_parts.push_back("syntax=" + join_flat(doc->syntax));
        }
        if (!doc->examples.empty()) {
            note_parts.push_back("examples=" + join_flat(doc->examples));
        }
        if (!doc->notes.empty()) {
            note_parts.push_back("notes=" + join_flat(doc->notes));
        }
        if (!doc->warnings.empty()) {
            note_parts.push_back("warnings=" + join_flat(doc->warnings));
        }
        row.notes = join_flat(note_parts, " ; ");

        by_name[row.can_name] = std::move(row);
    }

    auto overlay_specs = [&](const dottalk::expr::BuiltinFnSpec* specs,
                             std::size_t count,
                             const char* category,
                             const char* source_file) {
        if (!specs) {
            return;
        }

        for (std::size_t i = 0; i < count; ++i) {
            const auto& spec = specs[i];
            std::string name = spec.name ? spec.name : "";
            if (name.empty()) {
                continue;
            }

            const std::string canonical = upper_ascii(name);
            auto it = by_name.find(canonical);
            if (it == by_name.end()) {
                SysFuncSeedRow row;
                row.func_id = "FN_" + canonical;
                row.can_name = canonical;
                row.disp_name = canonical;
                row.def_locale = "en-US";
                row.region_id = "GLOBAL";
                row.func_cat = category ? category : "";
                row.impl_stat = "implemented";
                row.vis_tier = "core";
                row.owner = "expression_engine";
                row.src_auth = "builtin_registry";
                row.src_file = source_file ? source_file : "";
                row.calc_call = true;
                row.pub_surf = true;
                row.self_reg = false;
                row.msg_cat = false;
                row.active = true;
                row.notes = "runtime builtin spec without curated FunctionDoc row.";
                row.min_args = spec.minArgs;
                row.max_args = spec.maxArgs;
                by_name.emplace(canonical, std::move(row));
            } else {
                it->second.min_args = spec.minArgs;
                it->second.max_args = spec.maxArgs;
                it->second.src_file = source_file ? source_file : it->second.src_file;
                if (it->second.func_cat.empty()) {
                    it->second.func_cat = category ? category : "";
                }
            }
        }
    };

    overlay_specs(dottalk::expr::string_fn_specs(),
                  dottalk::expr::string_fn_specs_count(),
                  "String",
                  "src/cli/expr/fn_string.cpp");
    overlay_specs(dottalk::expr::date_fn_specs(),
                  dottalk::expr::date_fn_specs_count(),
                  "Date",
                  "src/cli/expr/fn_date.cpp");
    overlay_specs(dottalk::expr::numeric_fn_specs(),
                  dottalk::expr::numeric_fn_specs_count(),
                  "Numeric",
                  "src/cli/expr/fn_numeric.cpp");

    std::vector<SysFuncSeedRow> rows;
    rows.reserve(by_name.size());
    for (auto& [name, row] : by_name) {
        (void)name;
        rows.push_back(std::move(row));
    }

    std::sort(rows.begin(), rows.end(),
              [](const SysFuncSeedRow& a, const SysFuncSeedRow& b) {
                  return a.can_name < b.can_name;
              });
    return rows;
}

struct UsageContract {
    std::string owner;
    std::string command;
    std::vector<std::string> aliases;
    std::string category;
    std::string status;
    std::string noargs;
    std::string usage_access;
    std::vector<std::string> usage_lines;
    fs::path source_file;
};

struct UsageToken {
    std::string raw;
    std::string kind;
    bool optional = false;
    bool repeated = false;
};

struct SysArgAggregate {
    SysArgSeedRow row;
    std::unordered_set<std::string> notes;
    int non_usage_variants_seen = 0;
    int required_variants_seen = 0;
};

std::string trim_copy(std::string value) {
    return dottalk::datadict::trim_copy(std::move(value));
}

std::vector<std::string> split_contract_list(std::string value) {
    std::vector<std::string> out;
    std::string current;
    for (char ch : value) {
        if (ch == ',' || ch == ';' || ch == '|') {
            current = trim_copy(std::move(current));
            if (!current.empty()) {
                out.push_back(std::move(current));
            }
            current.clear();
        } else {
            current.push_back(ch);
        }
    }
    current = trim_copy(std::move(current));
    if (!current.empty()) {
        out.push_back(std::move(current));
    }
    return out;
}

bool starts_with_ci(std::string_view text, std::string_view prefix) {
    if (text.size() < prefix.size()) {
        return false;
    }
    for (std::size_t i = 0; i < prefix.size(); ++i) {
        const auto lhs = static_cast<char>(std::toupper(static_cast<unsigned char>(text[i])));
        const auto rhs = static_cast<char>(std::toupper(static_cast<unsigned char>(prefix[i])));
        if (lhs != rhs) {
            return false;
        }
    }
    return true;
}

std::string sanitize_symbol(std::string token) {
    std::string out;
    out.reserve(token.size());
    bool prev_underscore = false;
    for (char ch : token) {
        const unsigned char uch = static_cast<unsigned char>(ch);
        if (std::isalnum(uch)) {
            out.push_back(static_cast<char>(std::toupper(uch)));
            prev_underscore = false;
        } else if (!prev_underscore) {
            out.push_back('_');
            prev_underscore = true;
        }
    }
    while (!out.empty() && out.front() == '_') {
        out.erase(out.begin());
    }
    while (!out.empty() && out.back() == '_') {
        out.pop_back();
    }
    return out;
}

std::string infer_shape_from_placeholder(std::string_view name) {
    const auto token = lower_ascii(sanitize_symbol(std::string(name)));
    if (token.find("csv") != std::string::npos || token.find("file") != std::string::npos) {
        return "file-path";
    }
    if (token.find("path") != std::string::npos) {
        return "path";
    }
    if (token.find("table") != std::string::npos || token.find("dbf") != std::string::npos) {
        return "table-ref";
    }
    if (token.find("field") != std::string::npos) {
        return "field-name";
    }
    if (token.find("expr") != std::string::npos || token.find("value") != std::string::npos) {
        return "expression";
    }
    if (token.find("pred") != std::string::npos || token == "FOR") {
        return "predicate";
    }
    if (token.find("tag") != std::string::npos || token.find("order") != std::string::npos ||
        token.find("index") != std::string::npos) {
        return "name";
    }
    if (token.find("count") != std::string::npos || token == "N" || token == "RECNO" ||
        token.find("offset") != std::string::npos || token.find("row") != std::string::npos) {
        return "integer";
    }
    if (token.find("locale") != std::string::npos || token.find("lang") != std::string::npos) {
        return "locale-code";
    }
    return "value";
}

bool looks_like_usage_mode(const std::string& usage_line) {
    const auto upper = upper_ascii(usage_line);
    return upper.find(" USAGE") != std::string::npos ||
           upper.find(" HELP") != std::string::npos ||
           upper.find(" ?") != std::string::npos;
}

std::string strip_command_prefix(const std::string& usage_line, const std::string& command) {
    const auto trimmed = trim_copy(usage_line);
    const auto upper_trimmed = upper_ascii(trimmed);

    std::vector<std::string> variants;
    variants.push_back(upper_ascii(command));

    auto spaced = upper_ascii(command);
    std::replace(spaced.begin(), spaced.end(), '_', ' ');
    if (std::find(variants.begin(), variants.end(), spaced) == variants.end()) {
        variants.push_back(spaced);
    }

    auto compact = upper_ascii(command);
    compact.erase(std::remove(compact.begin(), compact.end(), '_'), compact.end());
    compact.erase(std::remove(compact.begin(), compact.end(), ' '), compact.end());
    if (std::find(variants.begin(), variants.end(), compact) == variants.end()) {
        variants.push_back(compact);
    }

    std::size_t best = 0;
    for (const auto& variant : variants) {
        if (starts_with_ci(upper_trimmed, variant) && variant.size() > best) {
            best = variant.size();
        }
    }

    if (best == 0) {
        return trimmed;
    }
    return trim_copy(trimmed.substr(best));
}

std::vector<UsageToken> tokenize_usage_syntax(std::string_view text) {
    std::vector<UsageToken> out;
    int optional_depth = 0;

    auto push_word = [&](std::string word, std::size_t& pos) {
        if (word.empty()) {
            return;
        }
        UsageToken tok;
        tok.raw = std::move(word);
        tok.kind = "keyword";
        tok.optional = optional_depth > 0;

        std::size_t look = pos;
        while (look < text.size() && std::isspace(static_cast<unsigned char>(text[look]))) {
            ++look;
        }
        if (look + 2 < text.size() && text.substr(look, 3) == "...") {
            tok.repeated = true;
            pos = look + 3;
        }
        out.push_back(std::move(tok));
    };

    for (std::size_t i = 0; i < text.size();) {
        const char ch = text[i];
        if (ch == '[') {
            ++optional_depth;
            ++i;
            continue;
        }
        if (ch == ']') {
            optional_depth = std::max(0, optional_depth - 1);
            ++i;
            continue;
        }
        if (ch == '<') {
            const auto close = text.find('>', i + 1);
            if (close == std::string_view::npos) {
                break;
            }
            UsageToken tok;
            tok.raw = std::string(text.substr(i, close - i + 1));
            tok.kind = "placeholder";
            tok.optional = optional_depth > 0;
            i = close + 1;
            std::size_t look = i;
            while (look < text.size() && std::isspace(static_cast<unsigned char>(text[look]))) {
                ++look;
            }
            if (look + 2 < text.size() && text.substr(look, 3) == "...") {
                tok.repeated = true;
                i = look + 3;
            }
            out.push_back(std::move(tok));
            continue;
        }
        if (std::isalnum(static_cast<unsigned char>(ch)) || ch == '_' || ch == '?') {
            std::size_t start = i;
            while (i < text.size()) {
                const char part = text[i];
                if (!(std::isalnum(static_cast<unsigned char>(part)) || part == '_' || part == '?')) {
                    break;
                }
                ++i;
            }
            auto word = std::string(text.substr(start, i - start));
            push_word(std::move(word), i);
            continue;
        }
        ++i;
    }

    return out;
}

std::vector<UsageContract> parse_usage_contracts(const fs::path& path) {
    const auto text = read_text_file(path);
    if (text.find("@dottalk.usage v1") == std::string::npos) {
        return {};
    }

    std::vector<UsageContract> contracts;
    std::istringstream in(text);
    std::string line;
    bool in_contract = false;
    std::string current_key;
    UsageContract current;

    auto finish_contract = [&]() {
        if (!in_contract) {
            return;
        }
        if (!current.command.empty() && !current.usage_lines.empty()) {
            contracts.push_back(std::move(current));
        }
        current = UsageContract{};
        current_key.clear();
        in_contract = false;
    };

    while (std::getline(in, line)) {
        auto trimmed = trim_copy(line);
        if (!starts_with_ci(trimmed, "//")) {
            finish_contract();
            continue;
        }

        trimmed = trim_copy(trimmed.substr(2));
        if (starts_with_ci(trimmed, "@dottalk.usage v1")) {
            finish_contract();
            in_contract = true;
            current.source_file = path;
            continue;
        }
        if (!in_contract) {
            continue;
        }

        if (trimmed.empty()) {
            continue;
        }

        const auto colon = trimmed.find(':');
        if (colon != std::string::npos) {
            current_key = lower_ascii(trim_copy(trimmed.substr(0, colon)));
            auto value = trim_copy(trimmed.substr(colon + 1));

            if (current_key == "owner") {
                current.owner = value;
            } else if (current_key == "command") {
                current.command = upper_ascii(value);
            } else if (current_key == "aliases") {
                current.aliases = split_contract_list(value);
            } else if (current_key == "category") {
                current.category = value;
            } else if (current_key == "status") {
                current.status = lower_ascii(value);
            } else if (current_key == "noargs") {
                current.noargs = value;
            } else if (current_key == "usage-access") {
                current.usage_access = value;
            } else if (current_key == "usage" && !value.empty()) {
                current.usage_lines.push_back(value);
            }
            continue;
        }

        if (current_key == "usage") {
            current.usage_lines.push_back(trimmed);
        }
    }

    finish_contract();
    return contracts;
}

std::vector<UsageContract> collect_usage_contracts(const CollectOptions& options,
                                                   const fs::path& workspace_root) {
    std::vector<UsageContract> contracts;
    std::error_code ec;
    const auto root = workspace_root / "src" / "cli";
    const std::unordered_set<std::string> dev_only_commands = {
        "BETA"
    };
    if (!fs::exists(root, ec)) {
        return contracts;
    }

    for (fs::recursive_directory_iterator it(root, fs::directory_options::skip_permission_denied, ec), end;
         it != end && !ec;
         it.increment(ec)) {
        if (ec || !it->is_regular_file()) {
            continue;
        }
        const auto path = it->path();
        if (path.extension() != ".cpp" || path.filename().string().rfind("cmd_", 0) != 0) {
            continue;
        }
        for (auto& contract : parse_usage_contracts(path)) {
            if (contract.status == "supported") {
                if (!options.include_dev_command_contracts &&
                    dev_only_commands.find(contract.command) != dev_only_commands.end()) {
                    continue;
                }
                contracts.push_back(std::move(contract));
            }
        }
    }

    std::sort(contracts.begin(), contracts.end(),
              [](const UsageContract& a, const UsageContract& b) {
                  return a.command < b.command;
              });
    return contracts;
}

struct RegistryCommand {
    std::string token;
    std::string handler;
    std::string source_file;
    std::size_t source_line = 0;
};

std::string normalize_command_name(std::string value) {
    return upper_ascii(squeeze_ws(std::move(value)));
}

std::string compact_command_name(std::string value) {
    value = normalize_command_name(std::move(value));
    value.erase(std::remove_if(value.begin(), value.end(), [](char ch) {
        return ch == ' ' || ch == '_' || ch == '-';
    }), value.end());
    return value;
}

std::string mask_cpp_comments(const std::string& text) {
    enum class State { Normal, LineComment, BlockComment, String, Character };
    State state = State::Normal;
    std::string out = text;
    bool escaped = false;

    for (std::size_t i = 0; i < text.size(); ++i) {
        const char ch = text[i];
        const char next = i + 1 < text.size() ? text[i + 1] : '\0';

        switch (state) {
        case State::Normal:
            if (ch == '/' && next == '/') {
                out[i] = out[i + 1] = ' ';
                ++i;
                state = State::LineComment;
            } else if (ch == '/' && next == '*') {
                out[i] = out[i + 1] = ' ';
                ++i;
                state = State::BlockComment;
            } else if (ch == '"') {
                state = State::String;
                escaped = false;
            } else if (ch == '\'') {
                state = State::Character;
                escaped = false;
            }
            break;
        case State::LineComment:
            if (ch == '\n') {
                state = State::Normal;
            } else {
                out[i] = ' ';
            }
            break;
        case State::BlockComment:
            if (ch == '*' && next == '/') {
                out[i] = out[i + 1] = ' ';
                ++i;
                state = State::Normal;
            } else if (ch != '\n' && ch != '\r') {
                out[i] = ' ';
            }
            break;
        case State::String:
            if (!escaped && ch == '"') {
                state = State::Normal;
            }
            escaped = !escaped && ch == '\\';
            if (ch != '\\') {
                escaped = false;
            }
            break;
        case State::Character:
            if (!escaped && ch == '\'') {
                state = State::Normal;
            }
            escaped = !escaped && ch == '\\';
            if (ch != '\\') {
                escaped = false;
            }
            break;
        }
    }
    return out;
}

std::size_t matching_paren(const std::string& text, std::size_t open) {
    int depth = 0;
    bool in_string = false;
    bool in_character = false;
    bool escaped = false;
    for (std::size_t i = open; i < text.size(); ++i) {
        const char ch = text[i];
        if (in_string || in_character) {
            const char quote = in_string ? '"' : '\'';
            if (!escaped && ch == quote) {
                in_string = false;
                in_character = false;
            }
            escaped = !escaped && ch == '\\';
            if (ch != '\\') {
                escaped = false;
            }
            continue;
        }
        if (ch == '"') {
            in_string = true;
            escaped = false;
        } else if (ch == '\'') {
            in_character = true;
            escaped = false;
        } else if (ch == '(') {
            ++depth;
        } else if (ch == ')' && --depth == 0) {
            return i;
        }
    }
    return std::string::npos;
}

std::vector<RegistryCommand> collect_static_registry_commands(const fs::path& workspace_root) {
    std::vector<fs::path> files;
    std::error_code ec;
    const auto source_root = workspace_root / "src";
    if (!fs::exists(source_root, ec)) {
        return {};
    }
    for (fs::recursive_directory_iterator it(source_root, fs::directory_options::skip_permission_denied, ec), end;
         it != end && !ec;
         it.increment(ec)) {
        if (it->is_regular_file() && it->path().extension() == ".cpp" && !is_ignored_path(it->path())) {
            files.push_back(it->path());
        }
    }
    std::sort(files.begin(), files.end());

    const std::regex registration(
        R"METAREGEX((?:registry\s*\(\s*\)\s*\.\s*add|register_(?:extension_)?command)\s*\(\s*"([^"]+)")METAREGEX");
    const std::regex called_handler_symbol(R"(\b((?:cmd|edu)_[A-Za-z0-9_]+)\s*\()");
    const std::regex direct_handler_symbol(
        R"(,\s*&?\s*((?:cmd|edu)_[A-Za-z0-9_]+)\s*(?:,|\)))");
    std::vector<RegistryCommand> commands;

    for (const auto& file : files) {
        const auto original = read_text_file(file);
        const auto text = mask_cpp_comments(original);
        for (std::sregex_iterator it(text.begin(), text.end(), registration), end; it != end; ++it) {
            const auto match_pos = static_cast<std::size_t>((*it).position());
            const auto token_pos = static_cast<std::size_t>((*it).position(1));
            const auto open = text.rfind('(', token_pos);
            if (open == std::string::npos) {
                continue;
            }
            const auto close = matching_paren(text, open);
            if (close == std::string::npos) {
                continue;
            }

            RegistryCommand command;
            command.token = normalize_command_name((*it)[1].str());
            command.source_file = path_for_fact(workspace_root, file);
            command.source_line = 1U + static_cast<std::size_t>(
                std::count(text.begin(), text.begin() + static_cast<std::ptrdiff_t>(match_pos), '\n'));

            const auto statement = text.substr(match_pos, close - match_pos + 1U);
            std::smatch handler_match;
            if (std::regex_search(statement, handler_match, called_handler_symbol)) {
                command.handler = handler_match[1].str();
            } else if (std::regex_search(statement, handler_match, direct_handler_symbol)) {
                command.handler = handler_match[1].str();
            } else {
                command.handler = "inline_registry_lambda";
            }
            if (!command.token.empty()) {
                commands.push_back(std::move(command));
            }
        }
    }

    std::sort(commands.begin(), commands.end(), [](const RegistryCommand& a, const RegistryCommand& b) {
        const bool a_central = a.source_file == "src/cli/shell_commands.cpp";
        const bool b_central = b.source_file == "src/cli/shell_commands.cpp";
        if (a.token != b.token) return a.token < b.token;
        if (a_central != b_central) return a_central;
        if (a.source_file != b.source_file) return a.source_file < b.source_file;
        return a.source_line < b.source_line;
    });
    commands.erase(std::unique(commands.begin(), commands.end(),
                               [](const RegistryCommand& a, const RegistryCommand& b) {
                                   return a.token == b.token;
                               }), commands.end());
    return commands;
}

std::vector<UsageContract> collect_command_usage_contracts(const fs::path& workspace_root) {
    std::vector<UsageContract> contracts;
    std::vector<fs::path> files;
    std::error_code ec;
    const auto source_root = workspace_root / "src";
    if (!fs::exists(source_root, ec)) {
        return contracts;
    }
    for (fs::recursive_directory_iterator it(source_root, fs::directory_options::skip_permission_denied, ec), end;
         it != end && !ec;
         it.increment(ec)) {
        if (it->is_regular_file() && it->path().extension() == ".cpp" && !is_ignored_path(it->path())) {
            files.push_back(it->path());
        }
    }
    std::sort(files.begin(), files.end());
    for (const auto& file : files) {
        for (auto& contract : parse_usage_contracts(file)) {
            contract.command = normalize_command_name(contract.command);
            for (auto& alias : contract.aliases) {
                alias = normalize_command_name(std::move(alias));
            }
            contracts.push_back(std::move(contract));
        }
    }
    std::sort(contracts.begin(), contracts.end(), [](const UsageContract& a, const UsageContract& b) {
        if (a.command != b.command) return a.command < b.command;
        return a.source_file.string() < b.source_file.string();
    });
    return contracts;
}

bool is_developer_command(const std::string& token, const UsageContract* contract) {
    static const std::unordered_set<std::string> explicit_dev = {
        "AREA51", "BETA", "CANARY"
    };
    if (explicit_dev.find(token) != explicit_dev.end()) {
        return true;
    }
    if (!contract) {
        return false;
    }
    return contract->status == "developer" || contract->status == "dev-canary";
}

std::vector<SysCmdSeedRow> build_syscmd_seed_rows(const CollectOptions& options,
                                                  const fs::path& workspace_root) {
    const auto registrations = collect_static_registry_commands(workspace_root);
    const auto contracts = collect_command_usage_contracts(workspace_root);

    std::unordered_map<std::string, const UsageContract*> contract_by_name;
    std::unordered_map<std::string, std::string> name_by_compact;
    std::unordered_set<std::string> ambiguous_compact;
    std::unordered_map<std::string, std::string> canonical_by_alias;
    std::unordered_set<std::string> ambiguous_alias;

    for (const auto& contract : contracts) {
        contract_by_name.emplace(contract.command, &contract);
        const auto compact = compact_command_name(contract.command);
        const auto compact_it = name_by_compact.find(compact);
        if (compact_it == name_by_compact.end()) {
            name_by_compact.emplace(compact, contract.command);
        } else if (compact_it->second != contract.command) {
            ambiguous_compact.insert(compact);
        }
        for (const auto& alias : contract.aliases) {
            const auto alias_it = canonical_by_alias.find(alias);
            if (alias_it == canonical_by_alias.end()) {
                canonical_by_alias.emplace(alias, contract.command);
            } else if (alias_it->second != contract.command) {
                ambiguous_alias.insert(alias);
            }
        }
    }

    static const std::unordered_set<std::string> syntax_commands = {
        "CASE", "CONTINUE", "ELSE", "ENDIF", "ENDLOOP", "ENDSCAN",
        "ENDUNTIL", "ENDWHILE", "IF", "LOOP", "SCAN", "UNTIL", "WHILE"
    };

    struct RankedRow {
        SysCmdSeedRow row;
        int score = 0;
        std::string source_file;
    };
    std::map<std::string, RankedRow> by_canonical;

    for (const auto& registration : registrations) {
        std::string canonical = registration.token;
        auto contract_it = contract_by_name.find(canonical);

        const auto alias_it = canonical_by_alias.find(registration.token);
        if (contract_it == contract_by_name.end() &&
            alias_it != canonical_by_alias.end() &&
            ambiguous_alias.find(registration.token) == ambiguous_alias.end()) {
            canonical = alias_it->second;
            contract_it = contract_by_name.find(canonical);
        } else if (contract_it == contract_by_name.end()) {
            const auto compact = compact_command_name(registration.token);
            const auto compact_it = name_by_compact.find(compact);
            if (compact_it != name_by_compact.end() &&
                ambiguous_compact.find(compact) == ambiguous_compact.end()) {
                canonical = compact_it->second;
                contract_it = contract_by_name.find(canonical);
            }
        }

        const UsageContract* contract = contract_it == contract_by_name.end()
            ? nullptr
            : contract_it->second;
        const bool developer = is_developer_command(registration.token, contract) ||
                               is_developer_command(canonical, contract);
        if (developer && !options.include_dev_command_contracts) {
            continue;
        }

        const auto symbol = sanitize_symbol(canonical);
        if (symbol.empty()) {
            continue;
        }

        SysCmdSeedRow row;
        row.cmd_id = "CMD_" + symbol;
        row.can_name = canonical;
        row.type = syntax_commands.find(canonical) == syntax_commands.end()
            ? "command"
            : "syntax-command";
        row.vis = developer ? "developer" : "public";
        row.handler = registration.handler;
        row.active = true;

        int score = registration.token == canonical ? 0 : 20;
        if (registration.token != canonical &&
            compact_command_name(registration.token) == compact_command_name(canonical)) {
            score = 10;
        }
        if (registration.source_file != "src/cli/shell_commands.cpp") {
            ++score;
        }

        auto existing = by_canonical.find(canonical);
        if (existing == by_canonical.end() || score < existing->second.score ||
            (score == existing->second.score && registration.source_file < existing->second.source_file)) {
            by_canonical[canonical] = {std::move(row), score, registration.source_file};
        }
    }

    std::vector<SysCmdSeedRow> rows;
    rows.reserve(by_canonical.size());
    for (auto& [canonical, ranked] : by_canonical) {
        (void)canonical;
        rows.push_back(std::move(ranked.row));
    }
    return rows;
}

std::vector<SysArgSeedRow> build_sysargs_seed_rows(const CollectOptions& options,
                                                   const fs::path& workspace_root) {
    const auto contracts = collect_usage_contracts(options, workspace_root);
    std::unordered_map<std::string, SysArgAggregate> aggregates;

    for (const auto& contract : contracts) {
        int non_usage_variants = 0;
        for (const auto& raw_usage_line : contract.usage_lines) {
            auto usage_line = strip_command_prefix(raw_usage_line, contract.command);
            if (usage_line.empty()) {
                continue;
            }

            const bool usage_mode = looks_like_usage_mode(raw_usage_line);
            if (!usage_mode) {
                ++non_usage_variants;
            }

            const auto tokens = tokenize_usage_syntax(usage_line);
            for (const auto& token : tokens) {
                std::string arg_name;
                std::string arg_kind;
                std::string val_shape;

                if (token.kind == "placeholder") {
                    arg_name = sanitize_symbol(token.raw.substr(1, token.raw.size() - 2));
                    arg_kind = "placeholder";
                    val_shape = infer_shape_from_placeholder(arg_name);
                } else {
                    arg_name = sanitize_symbol(token.raw);
                    arg_kind = "keyword";
                    val_shape = "literal";
                }

                if (arg_name.empty()) {
                    continue;
                }

                if (token.kind == "keyword" && !options.include_usage_keyword_args) {
                    continue;
                }

                const auto aggregate_key = contract.command + "|" + arg_kind + "|" + arg_name;
                auto& agg = aggregates[aggregate_key];
                if (agg.row.arg_id.empty()) {
                    agg.row.arg_id = "ARG_" + sanitize_symbol(contract.command) + "_" + arg_name;
                    agg.row.owner_knd = "command";
                    agg.row.owner_nam = contract.command;
                    agg.row.arg_name = arg_name;
                    agg.row.def_locale = "en-US";
                    agg.row.region_id = "GLOBAL";
                    agg.row.arg_kind = arg_kind;
                    agg.row.val_shape = val_shape;
                    agg.row.src_auth = "usage_contract_v1";
                    agg.row.src_file = path_for_fact(workspace_root, contract.source_file);
                    agg.row.active = true;
                }

                if (!val_shape.empty() && agg.row.val_shape.empty()) {
                    agg.row.val_shape = val_shape;
                }
                if (token.repeated) {
                    agg.row.repeat = true;
                }
                if (!usage_mode && token.kind == "placeholder") {
                    ++agg.non_usage_variants_seen;
                    if (!token.optional) {
                        ++agg.required_variants_seen;
                    }
                }

                if (!contract.noargs.empty()) {
                    agg.notes.insert("noargs=" + contract.noargs);
                }
                if (!contract.usage_access.empty()) {
                    agg.notes.insert("usage_access=" + contract.usage_access);
                }
                agg.notes.insert("usage=" + squeeze_ws(raw_usage_line));
            }
        }

        for (auto& [key, agg] : aggregates) {
            if (agg.row.owner_nam != contract.command) {
                continue;
            }
            if (agg.row.arg_kind == "placeholder" && non_usage_variants > 0) {
                agg.row.required = agg.required_variants_seen == non_usage_variants;
            }
        }
    }

    std::vector<SysArgSeedRow> rows;
    rows.reserve(aggregates.size());
    for (auto& [key, agg] : aggregates) {
        (void)key;
        std::vector<std::string> notes(agg.notes.begin(), agg.notes.end());
        std::sort(notes.begin(), notes.end());
        agg.row.notes = join_flat(notes, " ; ");
        rows.push_back(std::move(agg.row));
    }

    std::sort(rows.begin(), rows.end(),
              [](const SysArgSeedRow& a, const SysArgSeedRow& b) {
                  if (a.owner_nam != b.owner_nam) {
                      return a.owner_nam < b.owner_nam;
                  }
                  if (a.arg_kind != b.arg_kind) {
                      return a.arg_kind < b.arg_kind;
                  }
                  return a.arg_name < b.arg_name;
              });
    return rows;
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
    const std::regex function_doc_vector(
        R"METAREGEX(FunctionDoc\s*\{\s*"([^"]+)")METAREGEX",
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

    std::unordered_set<std::string> seen_function_catalogs;
    for (const auto& fact : facts) {
        if (fact.domain == MetaFactDomain::Function &&
            fact.evidence_kind == MetaFactEvidenceKind::SourceCatalog &&
            fact.source_file == rel) {
            seen_function_catalogs.insert(fact.canonical_name);
        }
    }

    for (std::sregex_iterator it(text.begin(), text.end(), function_doc_vector), end; it != end; ++it) {
        const auto name = (*it)[1].str();
        const auto canonical = upper_ascii(name);
        if (!seen_function_catalogs.insert(canonical).second) {
            continue;
        }
        add_fact(facts,
                 MetaFactDomain::Function,
                 MetaFactEvidenceKind::SourceCatalog,
                 name,
                 name,
                 "function-catalog",
                 rel,
                 "FunctionDoc vector literal",
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

std::string value_any(const DDictRow& row, std::initializer_list<const char*> keys) {
    for (const auto* key : keys) {
        const auto value = dottalk::datadict::trim_copy(dottalk::datadict::value_of(row, key));
        if (!value.empty()) {
            return value;
        }
    }
    return {};
}

bool value_bool_any(const DDictRow& row,
                    std::initializer_list<const char*> keys,
                    bool default_value = false) {
    for (const auto* key : keys) {
        const auto raw = value_any(row, {key});
        if (!raw.empty()) {
            const auto v = upper_ascii(raw);
            return v == "T" || v == "Y" || v == "1" || v == "TRUE";
        }
    }
    return default_value;
}

std::string normalize_fact_name(std::string value) {
    return upper_ascii(dottalk::datadict::trim_copy(std::move(value)));
}

std::string metadata_table_relpath(const fs::path& workspace_root,
                                   const fs::path& metadata_root,
                                   const std::string& table_name) {
    return path_for_fact(workspace_root, metadata_root / (table_name + ".dbf"));
}

void add_metadata_row_fact(std::vector<MetaFact>& facts,
                           MetaFactDomain domain,
                           const fs::path& workspace_root,
                           const fs::path& metadata_root,
                           const std::string& table_name,
                           const DDictRow& row) {
    MetaFact fact;
    fact.domain = domain;
    fact.evidence_kind = MetaFactEvidenceKind::MetadataTable;
    fact.owner = value_any(row, {"OWNER", "HELP_OWNR", "PARENT", "TOPIC_KEY"});
    fact.visibility_tier = value_any(row, {"VIS_TIER", "VISIBILITY", "VIS", "AUDIENCE"});
    fact.implementation_status = value_any(row, {"IMPL_STAT", "STATUS", "STATE"});
    fact.source_authority = value_any(row, {"SRC_AUTH", "SOURCE", "AUTHORITY"});
    fact.source_file = metadata_table_relpath(workspace_root, metadata_root, table_name);
    fact.handler = value_any(row, {"HANDLER", "CMD_HDLR", "FN_HDLR"});
    fact.dispatch_reachable = value_bool_any(row, {"DISP_REACH", "DISPATCH", "HAS_HDLR"});
    fact.public_surface = value_bool_any(row, {"PUB_SURF", "PUBLIC", "VISIBLE"});
    fact.self_registered = value_bool_any(row, {"SELF_REG"});
    fact.generated = value_bool_any(row, {"GENERATED"});
    fact.curated = value_bool_any(row, {"CURATED"});
    fact.active = value_bool_any(row, {"ACTIVE"}, true);

    switch (domain) {
    case MetaFactDomain::Command:
        fact.canonical_name = normalize_fact_name(value_any(row, {"CAN_NAME", "CMD_NAME", "NAME"}));
        fact.display_name = value_any(row, {"DISP_NAME", "DISPLAY", "NAME"});
        break;
    case MetaFactDomain::Function:
        fact.canonical_name = normalize_fact_name(value_any(row, {"CAN_NAME", "FUNC_NAME", "NAME"}));
        fact.display_name = value_any(row, {"DISP_NAME", "DISPLAY", "NAME"});
        break;
    case MetaFactDomain::Subcommand:
        fact.canonical_name = normalize_fact_name(value_any(row, {"QUAL_NAME", "CAN_NAME", "NAME"}));
        fact.display_name = value_any(row, {"DISP_NAME", "DISPLAY", "NAME"});
        break;
    case MetaFactDomain::EntryVariant:
        fact.canonical_name = normalize_fact_name(value_any(row, {"QUAL_NAME", "VAR_NAME", "NAME"}));
        fact.display_name = value_any(row, {"DISP_NAME", "DISPLAY", "NAME"});
        break;
    case MetaFactDomain::Argument:
        fact.canonical_name = normalize_fact_name(value_any(row, {"ARG_KEY", "ARG_NAME", "NAME"}));
        fact.display_name = value_any(row, {"DISP_NAME", "DISPLAY", "NAME"});
        break;
    case MetaFactDomain::HelpText:
        fact.canonical_name = normalize_fact_name(value_any(row, {"HELP_KEY", "TOPIC_KEY", "NAME"}));
        fact.display_name = value_any(row, {"TITLE", "DISP_NAME", "NAME"});
        break;
    case MetaFactDomain::Message: {
        const auto symbol = value_any(row, {"MSG_KEY", "SYMBOL", "CAN_NAME", "NAME"});
        const auto locale = value_any(row, {"LOCALE", "LANG", "LANGUAGE"});
        fact.canonical_name = normalize_fact_name(symbol);
        fact.display_name = symbol;
        if (!locale.empty()) {
            fact.notes = "locale=" + locale;
        }
        break;
    }
    case MetaFactDomain::FieldDictionary:
        fact.canonical_name = normalize_fact_name(value_any(row, {"FIELD_NAME", "FLD_NAME", "NAME"}));
        fact.display_name = value_any(row, {"DISPLAY", "DISP_NAME", "FIELD_NAME", "NAME"});
        break;
    case MetaFactDomain::RuntimeProof:
    case MetaFactDomain::Unknown:
    default:
        break;
    }

    const auto row_id = value_any(row, {"CMD_ID", "FUNC_ID", "MSG_ID", "HELP_ID", "ID", "ROW_ID"});
    fact.evidence_value = row_id.empty() ? table_name : (table_name + ":" + row_id);
    if (fact.notes.empty()) {
        fact.notes = "Metadata table row imported read-only.";
    } else {
        fact.notes += "; Metadata table row imported read-only.";
    }

    if (!fact.canonical_name.empty()) {
        facts.push_back(std::move(fact));
    }
}

void collect_metadata_table(std::vector<MetaFact>& facts,
                            std::vector<std::string>& warnings,
                            const fs::path& workspace_root,
                            const fs::path& metadata_root,
                            const std::string& table_name,
                            MetaFactDomain domain) {
    const auto path = metadata_root / (table_name + ".dbf");
    if (!fs::exists(path)) {
        warnings.push_back("metadata table not found: " + path.string());
        return;
    }

    const auto rows = dottalk::datadict::read_dbf_table(metadata_root, table_name);
    if (rows.empty()) {
        if (dbf_record_count(path) == 0U) {
            warnings.push_back("metadata table has zero rows: " + path.string());
        } else {
            warnings.push_back("metadata table unreadable or unsupported row shape: " + path.string());
        }
        return;
    }

    for (const auto& row : rows) {
        add_metadata_row_fact(facts, domain, workspace_root, metadata_root, table_name, row);
    }
}

void collect_metadata_facts(std::vector<MetaFact>& facts,
                            std::vector<std::string>& warnings,
                            const CollectOptions& options,
                            const fs::path& workspace_root) {
    const fs::path metadata_root = options.metadata_dbf_root.empty()
        ? default_metadata_root(workspace_root)
        : fs::path(options.metadata_dbf_root);

    if (!fs::exists(metadata_root)) {
        warnings.push_back("metadata root not found: " + metadata_root.string());
        return;
    }

    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSCMD", MetaFactDomain::Command);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSFUNC", MetaFactDomain::Function);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSSUBCMD", MetaFactDomain::Subcommand);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSENTVAR", MetaFactDomain::EntryVariant);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSARGS", MetaFactDomain::Argument);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSHELP", MetaFactDomain::HelpText);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSMSG", MetaFactDomain::Message);
    collect_metadata_table(facts, warnings, workspace_root, metadata_root, "SYSFLDDIC", MetaFactDomain::FieldDictionary);
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

    if (options.include_source_catalogs) {
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
    }

    if (options.include_metadata_tables) {
        collect_metadata_facts(result.facts, result.warnings, options, workspace_root);
    }

    return result;
}

std::vector<CompareIssue> compare_catalog_facts(const std::vector<MetaFact>& facts) {
    using Key = std::pair<std::string, std::string>;

    std::map<Key, MetaFact> source_catalog;
    std::map<Key, MetaFact> metadata_catalog;

    auto domain_key = [](MetaFactDomain domain) -> std::string {
        return std::string(to_string(domain));
    };

    for (const auto& fact : facts) {
        if (fact.canonical_name.empty() || !fact.active) {
            continue;
        }

        const Key key{domain_key(fact.domain), normalize_fact_name(fact.canonical_name)};
        if ((fact.domain == MetaFactDomain::Command || fact.domain == MetaFactDomain::Function) &&
            fact.evidence_kind == MetaFactEvidenceKind::SourceCatalog) {
            source_catalog.emplace(key, fact);
        }
        if ((fact.domain == MetaFactDomain::Command || fact.domain == MetaFactDomain::Function) &&
            fact.evidence_kind == MetaFactEvidenceKind::MetadataTable) {
            metadata_catalog.emplace(key, fact);
        }
    }

    std::vector<CompareIssue> issues;

    for (const auto& [key, source_fact] : source_catalog) {
        if (metadata_catalog.find(key) == metadata_catalog.end()) {
            issues.push_back({
                "WARN",
                "SOURCE_ONLY",
                key.first,
                key.second,
                source_fact.source_file,
                "",
                "Source catalog fact is missing from metadata tables."
            });
        }
    }

    for (const auto& [key, metadata_fact] : metadata_catalog) {
        if (source_catalog.find(key) == source_catalog.end()) {
            issues.push_back({
                "WARN",
                "METADATA_ONLY",
                key.first,
                key.second,
                "",
                metadata_fact.source_file,
                "Metadata fact is missing from source catalog extraction."
            });
        }
    }

    return issues;
}

std::vector<SysFuncSeedRow> collect_sysfunc_seed_rows() {
    return build_sysfunc_seed_rows();
}

std::vector<SysCmdSeedRow> collect_syscmd_seed_rows(const CollectOptions& options) {
    const fs::path workspace_root = options.workspace_root.empty()
        ? fs::current_path()
        : fs::path(options.workspace_root);
    return build_syscmd_seed_rows(options, workspace_root);
}

std::vector<SysArgSeedRow> collect_sysargs_seed_rows(const CollectOptions& options) {
    const fs::path workspace_root = options.workspace_root.empty()
        ? fs::current_path()
        : fs::path(options.workspace_root);
    return build_sysargs_seed_rows(options, workspace_root);
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

void write_compare_issues_csv(std::ostream& out, const std::vector<CompareIssue>& issues) {
    out << "severity,code,domain,canonical_name,source_file,metadata_table,message\n";
    for (const auto& issue : issues) {
        csv_cell(out, issue.severity); out << ',';
        csv_cell(out, issue.code); out << ',';
        csv_cell(out, issue.domain); out << ',';
        csv_cell(out, issue.canonical_name); out << ',';
        csv_cell(out, issue.source_file); out << ',';
        csv_cell(out, issue.metadata_table); out << ',';
        csv_cell(out, issue.message); out << '\n';
    }
}

void write_syscmd_seed_csv(std::ostream& out, const std::vector<SysCmdSeedRow>& rows) {
    out << "CMD_ID,CAN_NAME,TYPE,VIS,HANDLER,ACTIVE\n";

    for (const auto& row : rows) {
        csv_cell(out, row.cmd_id); out << ',';
        csv_cell(out, row.can_name); out << ',';
        csv_cell(out, row.type); out << ',';
        csv_cell(out, row.vis); out << ',';
        csv_cell(out, row.handler); out << ',';
        out << csv_bool(row.active) << '\n';
    }
}

void write_sysfunc_seed_csv(std::ostream& out, const std::vector<SysFuncSeedRow>& rows) {
    out << "FUNC_ID,CAN_NAME,DISP_NAME,DEF_LOCALE,REGION_ID,FUNC_CAT,MIN_ARGS,MAX_ARGS,"
           "IMPL_STAT,VIS_TIER,OWNER,SRC_AUTH,SRC_FILE,HANDLER,CALC_CALL,PUB_SURF,"
           "SELF_REG,MSG_CAT,ACTIVE,VER_AT,NOTES\n";

    for (const auto& row : rows) {
        csv_cell(out, row.func_id); out << ',';
        csv_cell(out, row.can_name); out << ',';
        csv_cell(out, row.disp_name); out << ',';
        csv_cell(out, row.def_locale); out << ',';
        csv_cell(out, row.region_id); out << ',';
        csv_cell(out, row.func_cat); out << ',';
        out << row.min_args << ',';
        out << row.max_args << ',';
        csv_cell(out, row.impl_stat); out << ',';
        csv_cell(out, row.vis_tier); out << ',';
        csv_cell(out, row.owner); out << ',';
        csv_cell(out, row.src_auth); out << ',';
        csv_cell(out, row.src_file); out << ',';
        csv_cell(out, row.handler); out << ',';
        out << csv_bool(row.calc_call) << ',';
        out << csv_bool(row.pub_surf) << ',';
        out << csv_bool(row.self_reg) << ',';
        out << csv_bool(row.msg_cat) << ',';
        out << csv_bool(row.active) << ',';
        csv_cell(out, row.ver_at); out << ',';
        csv_cell(out, row.notes); out << '\n';
    }
}

void write_sysargs_seed_csv(std::ostream& out, const std::vector<SysArgSeedRow>& rows) {
    out << "ARG_ID,OWNER_KND,OWNER_NAM,ARG_NAME,DEF_LOCALE,REGION_ID,ARG_KIND,VAL_SHAPE,"
           "REQUIRED,REPEAT,SRC_AUTH,SRC_FILE,ACTIVE,VER_AT,NOTES\n";

    for (const auto& row : rows) {
        csv_cell(out, row.arg_id); out << ',';
        csv_cell(out, row.owner_knd); out << ',';
        csv_cell(out, row.owner_nam); out << ',';
        csv_cell(out, row.arg_name); out << ',';
        csv_cell(out, row.def_locale); out << ',';
        csv_cell(out, row.region_id); out << ',';
        csv_cell(out, row.arg_kind); out << ',';
        csv_cell(out, row.val_shape); out << ',';
        out << csv_bool(row.required) << ',';
        out << csv_bool(row.repeat) << ',';
        csv_cell(out, row.src_auth); out << ',';
        csv_cell(out, row.src_file); out << ',';
        out << csv_bool(row.active) << ',';
        csv_cell(out, row.ver_at); out << ',';
        csv_cell(out, row.notes); out << '\n';
    }
}

} // namespace dt::meta
