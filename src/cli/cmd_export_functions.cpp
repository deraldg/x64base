// src/cli/cmd_export_functions.cpp
// Export the function catalog to Markdown.
//
// Command surface:
//   EXPORTFUNCTIONS
//   EXPORTFUNCTIONS MD
//   EXPORTFUNCTIONS MD <path>
//   EXPORTFUNCTIONS <path>
//
// Default output path:
//   ./data/docs/functions.md
//
// Notes:
// - Keeps function_catalog as the single source of truth.
// - Does not depend on cmd_help.cpp internals.
// - Category order matches grouped HELP output.

#include "xbase.hpp"
#include "cli/expr/function_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <map>
#include <sstream>
#include <string>
#include <vector>

#if __has_include("dli/registry.hpp")
  #include "dli/registry.hpp"
  #define DT_HAVE_DLI_REGISTRY 1
#else
  #define DT_HAVE_DLI_REGISTRY 0
#endif

namespace fs = std::filesystem;

namespace {

std::string trim(std::string s)
{
    auto notspace = [](unsigned char c) { return !std::isspace(c); };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), notspace));
    s.erase(std::find_if(s.rbegin(), s.rend(), notspace).base(), s.end());
    return s;
}

std::string to_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

std::string md_escape(const std::string& s)
{
    std::string out;
    out.reserve(s.size());
    for (char ch : s) {
        switch (ch) {
            case '\\': out += "\\\\"; break;
            case '`':  out += "\\`";  break;
            case '*':  out += "\\*";  break;
            case '_':  out += "\\_";  break;
            case '[':  out += "\\[";  break;
            case ']':  out += "\\]";  break;
            case '#':  out += "\\#";  break;
            default:   out += ch;      break;
        }
    }
    return out;
}

std::vector<dottalk::expr::FunctionCategory> function_category_order()
{
    using dottalk::expr::FunctionCategory;
    return {
        FunctionCategory::Numeric,
        FunctionCategory::Date,
        FunctionCategory::String,
        FunctionCategory::Search,
        FunctionCategory::Logical,
        FunctionCategory::Construction,
        FunctionCategory::Conversion,
        FunctionCategory::Misc
    };
}

std::map<dottalk::expr::FunctionCategory, std::vector<const dottalk::expr::FunctionDoc*>>
group_function_docs()
{
    std::map<dottalk::expr::FunctionCategory, std::vector<const dottalk::expr::FunctionDoc*>> groups;

    for (const auto* doc : dottalk::expr::all_function_docs()) {
        if (!doc) continue;
        groups[doc->category].push_back(doc);
    }

    for (auto& [cat, vec] : groups) {
        (void)cat;
        std::sort(vec.begin(), vec.end(),
                  [](const dottalk::expr::FunctionDoc* a,
                     const dottalk::expr::FunctionDoc* b)
                  {
                      return a->name < b->name;
                  });
    }

    return groups;
}

void write_string_list(std::ofstream& out,
                       const char* heading,
                       const std::vector<std::string>& items)
{
    if (items.empty()) return;

    out << "**" << heading << "**\n\n";
    for (const auto& item : items) {
        out << "- " << md_escape(item) << "\n";
    }
    out << "\n";
}

void write_syntax_block(std::ofstream& out,
                        const std::vector<std::string>& syntax)
{
    if (syntax.empty()) return;

    out << "**Syntax**\n\n";
    out << "```text\n";
    for (const auto& line : syntax) {
        out << line << "\n";
    }
    out << "```\n\n";
}

void write_aliases(std::ofstream& out,
                   const std::vector<std::string>& aliases)
{
    if (aliases.empty()) return;

    out << "**Aliases:** ";
    for (std::size_t i = 0; i < aliases.size(); ++i) {
        if (i) out << ", ";
        out << "`" << md_escape(aliases[i]) << "`";
    }
    out << "\n\n";
}

bool export_functions_markdown(const fs::path& out_path,
                               std::string& error_message)
{
    try {
        if (out_path.has_parent_path()) {
            fs::create_directories(out_path.parent_path());
        }

        std::ofstream out(out_path, std::ios::binary);
        if (!out) {
            error_message = "Unable to open output file: " + out_path.string();
            return false;
        }

        const auto groups = group_function_docs();
        const auto order  = function_category_order();

        std::size_t total_count = 0;
        for (const auto& [cat, vec] : groups) {
            (void)cat;
            total_count += vec.size();
        }

        out << "# DotTalk++ Function Reference\n\n";
        out << "Generated from the runtime function catalog.\n\n";
        out << "Total functions documented: **" << total_count << "**\n\n";

        out << "## Categories\n\n";
        for (const auto cat : order) {
            const auto it = groups.find(cat);
            if (it == groups.end() || it->second.empty()) continue;

            const std::string cat_name = dottalk::expr::to_string(cat);
            out << "- [" << md_escape(cat_name) << "](#";
            for (char ch : cat_name) {
                const unsigned char uch = static_cast<unsigned char>(ch);
                if (std::isalnum(uch)) out << static_cast<char>(std::tolower(uch));
                else if (std::isspace(uch)) out << '-';
            }
            out << ") (" << it->second.size() << ")\n";
        }
        out << "\n";

        for (const auto cat : order) {
            const auto it = groups.find(cat);
            if (it == groups.end() || it->second.empty()) continue;

            const std::string cat_name = dottalk::expr::to_string(cat);
            out << "## " << md_escape(cat_name) << "\n\n";

            for (const auto* doc : it->second) {
                out << "### " << md_escape(doc->name) << "\n\n";
                out << md_escape(doc->summary) << "\n\n";
                out << "**Arguments:** " << doc->min_args << ".." << doc->max_args << "\n\n";

                write_aliases(out, doc->aliases);
                write_syntax_block(out, doc->syntax);
                write_string_list(out, "Examples", doc->examples);
                write_string_list(out, "Notes", doc->notes);
                write_string_list(out, "Warnings", doc->warnings);
            }
        }

        return true;
    }
    catch (const std::exception& ex) {
        error_message = ex.what();
        return false;
    }
}

void show_usage()
{
    std::cout
        << "Usage:\n"
        << "  EXPORTFUNCTIONS\n"
        << "  EXPORTFUNCTIONS MD\n"
        << "  EXPORTFUNCTIONS MD <path>\n"
        << "  EXPORTFUNCTIONS <path>\n\n"
        << "Default output:\n"
        << "  ./data/docs/functions.md\n";
}

} // namespace

void cmd_EXPORTFUNCTIONS(xbase::DbArea& /*area*/, std::istringstream& iss)
{
    std::string first;
    std::string second;

    iss >> first;
    std::getline(iss >> std::ws, second);
    second = trim(second);

    if (to_upper(first) == "HELP" || to_upper(first) == "/?" || to_upper(first) == "-?") {
        show_usage();
        return;
    }

    std::string format = "MD";
    fs::path out_path = fs::path(".") / "data" / "docs" / "functions.md";

    if (!first.empty()) {
        const std::string first_upper = to_upper(first);

        if (first_upper == "MD" || first_upper == "MARKDOWN") {
            format = "MD";
            if (!second.empty()) out_path = second;
        } else {
            out_path = first;
            if (!second.empty()) {
                out_path = fs::path(first + " " + second);
            }
        }
    }

    if (format != "MD") {
        std::cout << "Unsupported format: " << format << "\n";
        return;
    }

    std::string error;
    if (!export_functions_markdown(out_path, error)) {
        std::cout << "EXPORTFUNCTIONS failed: " << error << "\n";
        return;
    }

    std::cout << "Function reference exported to: " << out_path.string() << "\n";
}

#if DT_HAVE_DLI_REGISTRY
static bool s_exportfunctions_reg = []() {
    dli::registry().add("EXPORTFUNCTIONS", &cmd_EXPORTFUNCTIONS);
    return true;
}();
#endif
