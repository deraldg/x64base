// 

// src/cli/cmd_help.cpp
// @dottalk.usage v1
// owner: DOT|HELP
// command: HELP
// category: help
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: HELP USAGE
// summary:
//   Route user help requests across DotTalk command, function, FoxPro,
//   PowerShell, SQL, beta, predicate, and educational help surfaces.
//
// usage:
//   HELP
//   HELP USAGE
//   HELP GIANT
//   HELP BETA
//   HELP PS
//   HELP SQL
//   HELP PREDICATES
//   HELP FUNCTIONS
//   HELP FUNCTION <name>
//   HELP /FOX <topic>
//   HELP /DOT <topic>
//   HELP /ED <topic>
//   HELP <command>
//
// notes:
//   HELP with no arguments prints the top-level help router.
//   HELP <command> normalizes through the reflected command catalog first.
//   HELP FUNCTION <name> checks reflected function metadata and catalog docs.
//   HELP GIANT delegates to the full command catalog.
//   HELP is read-only for table data and path state.
//
// risk:
//   reads_help_metadata: yes
//   mutates_table_data: no
//   mutates_cursor: no
//
// related:
//   CMDHELP
//   CMDHELPCHK
//   FOXHELP
//   PREDHELP
//

#include "cmd_help.hpp"
#include "help_router.hpp"
#include "help_beta.hpp"
#include "foxref.hpp"
#include "dotref.hpp"
#include "edref.hpp"
#include "cli/command_catalog.hpp"
#include "cli/output_router.hpp"
#include "cli/settings.hpp"
#include "cli/expr/function_catalog.hpp"
#include "help/reference_collection.hpp"
#include "help/message_catalog.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"

extern void cmd_CMDHELP(xbase::DbArea&, std::istringstream&);
extern void cmd_FOXHELP(xbase::DbArea&, std::istringstream&);
extern void cmd_PREDHELP(xbase::DbArea&, std::istringstream&);

extern void show_pshell_help(const std::string&);
extern void show_sql_help(const std::string&);

namespace {

using dottalk::help_grouped::show_function_index_grouped;
using dottalk::help_grouped::try_show_function_category;

inline std::ostream& out()
{
    return cli::OutputRouter::instance().out();
}

inline std::string uptrim(std::string s)
{
    auto notspace = [](unsigned char c) { return !std::isspace(c); };
    s.erase(std::begin(s), std::find_if(std::begin(s), std::end(s), notspace));
    s.erase(std::find_if(std::rbegin(s), std::rend(s), notspace).base(), std::end(s));
    std::transform(std::begin(s), std::end(s), std::begin(s),
                   [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

inline bool show_new_catalog_topic(const std::string& term)
{
    const auto* doc = dottalk::doc::get(term);
    if (!doc) return false;

    out() << doc->name << " - " << doc->summary << "\n";

    if (!doc->syntax.empty()) {
        out() << "\nSyntax:\n";
        for (const auto& s : doc->syntax) {
            out() << "  " << s << "\n";
        }
    }

    if (!doc->samples.empty()) {
        out() << "\nExamples:\n";
        for (const auto& s : doc->samples) {
            out() << "  " << s << "\n";
        }
    }

    if (!doc->notes.empty()) {
        out() << "\nNotes:\n";
        for (const auto& s : doc->notes) {
            out() << "  " << s << "\n";
        }
    }

    if (!doc->warnings.empty()) {
        out() << "\nWarnings:\n";
        for (const auto& s : doc->warnings) {
            out() << "  " << s << "\n";
        }
    }

    return true;
}

inline bool show_function_topic_from_doc_catalog(const std::string& term)
{
    const auto* doc = dottalk::expr::get_function_doc(term);
    if (!doc) return false;

    out() << doc->name << " - " << doc->summary << "\n";
    out() << "\nCategory: " << dottalk::expr::to_string(doc->category) << "\n";
    out() << "Arguments: " << doc->min_args << ".." << doc->max_args << "\n";

    if (!doc->aliases.empty()) {
        out() << "Aliases:";
        for (const auto& a : doc->aliases) {
            out() << " " << a;
        }
        out() << "\n";
    }

    if (!doc->syntax.empty()) {
        out() << "\nSyntax:\n";
        for (const auto& s : doc->syntax) {
            out() << "  " << s << "\n";
        }
    }

    if (!doc->examples.empty()) {
        out() << "\nExamples:\n";
        for (const auto& s : doc->examples) {
            out() << "  " << s << "\n";
        }
    }

    if (!doc->notes.empty()) {
        out() << "\nNotes:\n";
        for (const auto& s : doc->notes) {
            out() << "  " << s << "\n";
        }
    }

    if (!doc->warnings.empty()) {
        out() << "\nWarnings:\n";
        for (const auto& s : doc->warnings) {
            out() << "  " << s << "\n";
        }
    }

    return true;
}

inline bool show_dot_topic(const std::string& term)
{
    if (term.empty()) return false;
    if (const auto* it = dotref::find(term)) {
        out() << it->name << "\n"
              << "  " << it->syntax << "\n"
              << "  " << it->summary << "\n";
        return true;
    }
    return false;
}

inline bool show_ed_topic(const std::string& term)
{
    if (term.empty()) return false;
    if (const auto* it = edref::find(term)) {
        out() << it->topic << "\n"
              << "  " << it->syntax << "\n"
              << it->summary << "\n";
        return true;
    }
    return false;
}

inline bool show_fox_topic_local(const std::string& term)
{
    if (term.empty()) return false;
    if (const auto* it = foxref::find(term)) {
        out() << it->name << "\n"
              << "  " << it->syntax << "\n"
              << "  " << it->summary << "\n";
        return true;
    }
    return false;
}

inline void show_fox(xbase::DbArea& area, const std::string& term)
{
    std::istringstream iss(term);
    cmd_FOXHELP(area, iss);
}

inline void show_predicates(xbase::DbArea& area)
{
    std::istringstream empty;
    cmd_PREDHELP(area, empty);
}

inline void show_beta_router(const std::string& restUp)
{
    std::string term;
    if (restUp.size() > 4) {
        term = restUp.substr(4);
        while (!term.empty() && std::isspace(static_cast<unsigned char>(term.front()))) {
            term.erase(term.begin());
        }
        if (term == "CHECKLIST" || term == "STATUS") {
            term.clear();
        }
    }
    dottalk::help::show_beta(term);
}

inline void print_help_usage()
{
    out() << "DotTalk++ Help System\n\n"
          << "  HELP GIANT            - full command catalog\n"
          << "  HELP BETA             - beta checklist\n"
          << "  HELP PS / PSHELL      - PowerShell helpers\n"
          << "  HELP SQL              - SQL reference (SQLite + MSSQL)\n"
          << "  HELP PREDICATES       - COUNT/LOCATE syntax\n"
          << "  HELP FUNCTION <name>  - expression function help\n"
          << "  HELP FUNCTIONS        - list documented expression functions\n"
          << "  HELP /FOX <topic>     - FoxPro compatibility reference\n"
          << "  HELP /DOT <topic>     - DotTalk-native command reference\n"
          << "  HELP /ED <topic>      - educational/system concepts\n"
          << "  HELP <command>        - default topic lookup\n";
}

// Normalize HELP topic via EntryVariantInfo.
// Exact-match only for now.
inline std::string normalize_help_topic(const std::string& raw)
{
    using namespace refsys;

    const std::string t = uptrim(raw);
    const ReferenceCollection rc = build_reference_collection();

    for (const auto& ev : rc.entry_variants) {
        if (uptrim(ev.token) == t) {
            return uptrim(ev.canonical_command);
        }
    }

    return t;
}


// MSG-022S1 BEGIN HELP_HINT_COMMAND active provider helper
inline void help_apply_placeholder(std::string& text,
                                   const std::string& placeholder,
                                   const std::string& value)
{
    const std::string token1 = "{" + placeholder + "}";
    const std::string token2 = "{" + uptrim(placeholder) + "}";

    std::size_t pos = 0;
    while ((pos = text.find(token1, pos)) != std::string::npos) {
        text.replace(pos, token1.size(), value);
        pos += value.size();
    }

    pos = 0;
    while ((pos = text.find(token2, pos)) != std::string::npos) {
        text.replace(pos, token2.size(), value);
        pos += value.size();
    }
}

inline bool show_active_help_hint_command(const std::string& command_token)
{
    const auto status = dottalk::helpdata::active_message_catalog_status();
    if (!status.active_catalog_loaded) {
        return false;
    }

    const std::string locale = cli::Settings::instance().message_locale.empty()
        ? std::string("en-US")
        : cli::Settings::instance().message_locale;

    std::string text = dottalk::helpdata::format_message_catalog(locale, "HELP_HINT_COMMAND");
    if (text.empty()) {
        return false;
    }

    help_apply_placeholder(text, "command", command_token);
    out() << text << "\n";

    if (dottalk::helpdata::message_routing_proof_enabled()) {
        out() << "Message routing proof: active_dbf HELP_HINT_COMMAND\n";
    }

    return true;
}
// MSG-022S1 END HELP_HINT_COMMAND active provider helper


inline bool show_reflected_command_topic(const std::string& term_up)
{
    using namespace refsys;

    const ReferenceCollection rc = build_reference_collection();

    for (const auto& cmd : rc.commands) {
        if (uptrim(cmd.canonical_name) != term_up) continue;

        out() << cmd.canonical_name << "\n";

        if (!cmd.summary.empty()) {
            out() << "\n" << cmd.summary << "\n";
        }

        if (!cmd.syntax.empty()) {
            out() << "\nSyntax:\n";
            for (const auto& line : cmd.syntax) {
                out() << "  " << line << "\n";
            }
        }

        std::vector<SubcommandInfo> public_subs;
        std::vector<SubcommandInfo> dev_subs;

        for (const auto& sc : rc.subcommands) {
            if (sc.parent_command != cmd.canonical_name) continue;
            if (sc.public_surface) public_subs.push_back(sc);
            else dev_subs.push_back(sc);
        }

        std::sort(public_subs.begin(), public_subs.end(),
                  [](const SubcommandInfo& a, const SubcommandInfo& b) {
                      return a.name < b.name;
                  });

        std::sort(dev_subs.begin(), dev_subs.end(),
                  [](const SubcommandInfo& a, const SubcommandInfo& b) {
                      return a.name < b.name;
                  });

        if (!public_subs.empty()) {
            out() << "\nSubcommands:\n";
            for (const auto& sc : public_subs) {
                out() << "  " << sc.name << "\n";
            }
        }

        if (!dev_subs.empty()) {
            out() << "\nDev / Transitional:\n";
            for (const auto& sc : dev_subs) {
                out() << "  " << sc.name << "\n";
            }
        }

        if (!cmd.notes.empty()) {
            out() << "\nNotes:\n";
            for (const auto& line : cmd.notes) {
                out() << "  " << line << "\n";
            }
        }

        if (!cmd.warnings.empty()) {
            out() << "\nWarnings:\n";
            for (const auto& line : cmd.warnings) {
                out() << "  " << line << "\n";
            }
        }

        return true;
    }

    return false;
}

inline bool show_reflected_subcommand_topic(const std::string& term_up)
{
    using namespace refsys;

    const ReferenceCollection rc = build_reference_collection();

    for (const auto& sc : rc.subcommands) {
        if (uptrim(sc.qualified_name) != term_up) continue;

        out() << sc.qualified_name << "\n";

        if (!sc.summary.empty()) {
            out() << "\n" << sc.summary << "\n";
        }

        if (!sc.syntax.empty()) {
            out() << "\nSyntax:\n";
            for (const auto& line : sc.syntax) {
                out() << "  " << line << "\n";
            }
        }

        if (!sc.notes.empty()) {
            out() << "\nNotes:\n";
            for (const auto& line : sc.notes) {
                out() << "  " << line << "\n";
            }
        }

        if (!sc.warnings.empty()) {
            out() << "\nWarnings:\n";
            for (const auto& line : sc.warnings) {
                out() << "  " << line << "\n";
            }
        }

        return true;
    }

    return false;
}

inline bool show_reflected_function_topic(const std::string& term_up)
{
    using namespace refsys;

    const ReferenceCollection rc = build_reference_collection();

    for (const auto& fn : rc.functions) {
        if (uptrim(fn.canonical_name) != term_up) continue;

        out() << fn.canonical_name << "\n";

        if (!fn.summary.empty()) {
            out() << "\n" << fn.summary << "\n";
        }

        out() << "\nCategory: " << fn.category << "\n";
        out() << "Arguments: " << fn.min_args << ".." << fn.max_args << "\n";

        if (!fn.aliases.empty()) {
            out() << "Aliases:";
            for (const auto& a : fn.aliases) {
                out() << " " << a;
            }
            out() << "\n";
        }

        out() << "\nSyntax:\n";
        if (!fn.syntax.empty()) {
            for (const auto& s : fn.syntax) {
                out() << "  " << s << "\n";
            }
        } else {
            out() << "  " << fn.canonical_name << "(...)\n";
        }

        if (!fn.examples.empty()) {
            out() << "\nExamples:\n";
            for (const auto& s : fn.examples) {
                out() << "  " << s << "\n";
            }
        }

        if (!fn.notes.empty()) {
            out() << "\nNotes:\n";
            for (const auto& s : fn.notes) {
                out() << "  " << s << "\n";
            }
        }

        if (!fn.warnings.empty()) {
            out() << "\nWarnings:\n";
            for (const auto& s : fn.warnings) {
                out() << "  " << s << "\n";
            }
        }

        return true;
    }

    return false;
}

} // anonymous namespace

void cmd_HELP(xbase::DbArea& area, std::istringstream& args)
{
    using namespace dottalk::help;

    std::string rest;
    {
        std::ostringstream oss;
        oss << args.rdbuf();
        rest = oss.str();
    }
    const std::string restUp = uptrim(rest);

    if (restUp == "GIANT" || restUp == "/GIANT") {
        std::istringstream empty;
        cmd_CMDHELP(area, empty);
        return;
    }

    if (restUp == "BETA" || restUp.rfind("BETA ", 0) == 0) {
        show_beta_router(restUp);
        return;
    }
    if (restUp.rfind("BETA-", 0) == 0) {
        dottalk::help::show_beta(restUp);
        return;
    }

    if (restUp == "PS" || restUp == "PSHELL" || restUp == "POWERSHELL" ||
        restUp.rfind("PS ", 0) == 0 ||
        restUp.rfind("PSHELL ", 0) == 0 ||
        restUp.rfind("POWERSHELL ", 0) == 0) {
        std::string ps_arg;
        const size_t space = rest.find(' ');
        if (space != std::string::npos) {
            ps_arg = rest.substr(space + 1);
        }
        show_pshell_help(ps_arg);
        return;
    }

    if (restUp == "SQL" || restUp == "SQLHELP" ||
        restUp.rfind("SQL ", 0) == 0 ||
        restUp.rfind("SQLHELP ", 0) == 0) {
        std::string sql_arg;
        const size_t space = rest.find(' ');
        if (space != std::string::npos) {
            sql_arg = rest.substr(space + 1);
        }
        show_sql_help(sql_arg);
        return;
    }

    if (restUp == "PREDICATES" || restUp == "PREDHELP") {
        show_predicates(area);
        return;
    }

    if (restUp == "FUNCTIONS" || restUp == "FUNCTION") {
        show_function_index_grouped();
        return;
    }

    if (try_show_function_category(restUp)) {
        return;
    }

    if (restUp.rfind("FUNCTION ", 0) == 0) {
        std::string fn = rest.substr(9);
        const std::string fn_norm = normalize_help_topic(fn);

        if (show_reflected_function_topic(fn_norm)) {
            return;
        }

        if (show_function_topic_from_doc_catalog(fn_norm)) {
            return;
        }

        out() << "No function help found for: " << fn << "\n";
        return;
    }

    if (restUp.empty() || restUp == "USAGE" || restUp == "/?" || restUp == "?") {
        print_help_usage();
        return;
    }

    auto opts = parse_opts(rest);

    if (opts.isBuild) {
        std::istringstream build_iss("BUILD");
        cmd_CMDHELP(area, build_iss);
        return;
    }
    if (opts.predOnly) {
        show_predicates(area);
        return;
    }
    if (opts.onlyFox) {
        show_fox(area, opts.term);
        return;
    }
    if (opts.onlyDot) {
        if (!show_dot_topic(opts.term)) {
            out() << "No DotTalk help found for: " << opts.term << "\n";
        }
        return;
    }
    if (opts.onlyEd) {
        if (!show_ed_topic(opts.term)) {
            out() << "No educational help found for: " << opts.term << "\n";
        }
        return;
    }

    if (!opts.term.empty()) {
        const std::string term_effective = normalize_help_topic(opts.term);
        const std::string term_original_up = uptrim(opts.term);

        // 1. Reflected qualified subcommand help
        if (term_effective.rfind("SET ", 0) == 0) {
            if (show_reflected_subcommand_topic(term_effective)) return;
        }

        // 2. Reflected top-level command help
        if (show_reflected_command_topic(term_effective)) return;

        // 3. Reflected function help
        if (show_reflected_function_topic(term_effective)) return;

        // 4. Catalog-backed command / function docs
        if (show_new_catalog_topic(term_effective)) return;
        if (show_function_topic_from_doc_catalog(term_effective)) return;

        if (term_effective == "BETA" || term_effective.rfind("BETA ", 0) == 0) {
            show_beta_router(term_effective);
            return;
        }

        // 5. Legacy fallback only if normalization did not change the term
        if (term_effective == term_original_up) {
            if (show_dot_topic(opts.term)) return;
            if (show_ed_topic(opts.term)) return;
            // MSG-022S1_3 BEGIN HELP_HINT_COMMAND active provider route before fox local fallback
            if (show_active_help_hint_command(opts.term)) return;
            // MSG-022S1_3 END HELP_HINT_COMMAND active provider route before fox local fallback

            if (show_fox_topic_local(opts.term)) return;

            show_fox(area, opts.term);
            return;
        }

        out() << "No help found for: " << opts.term << "\n";
        return;
    }

    out() << "Type HELP GIANT, HELP BETA, HELP PS, HELP SQL, HELP FUNCTION <name>, or HELP <command>\n";
}