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
//   HELP GIANT USAGE
//   HELP GIANT TOPICS
//   HELP GIANT KIND
//   HELP GIANT SOURCE
//   HELP GIANT <topic>
//   HELP /GIANT
//   HELP /GIANT USAGE
//   HELP /GIANT TOPICS
//   HELP /GIANT KIND
//   HELP /GIANT SOURCE
//   HELP /GIANT <topic>
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
//   HELP GIANT is the readable full HELP DATA report surface.
//   HELP GIANT TOPICS/KIND/SOURCE expose organized report slices.
//   HELP GIANT <topic> renders the assembled topic through current HELP DATA.
//   HELP GIANT respects normal shell paging via SET PAGING ON|OFF.
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
// @dottalk.location v1
// id: DOTSRC-DOTTALKPP-CLI-CMD-HELP
// home: src/cli
// canonical-path: src/cli/cmd_help.cpp
// project: dottalkpp
// role: command-implementation
// @dottalk.end

#include "cmd_help.hpp"
#include "help_router.hpp"
#include "help_beta.hpp"
#include "foxref.hpp"
#include "dotref.hpp"
#include "edref.hpp"
#include "cli/text_match.hpp"
#include "cli/command_catalog.hpp"
#include "cli/command_output.hpp"
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

inline void print_heading(dottalk::helpdata::MessageId id)
{
    out() << "\n" << cli::cmdout::message_text(id) << "\n";
}

inline void print_indented_lines(const std::vector<std::string>& lines)
{
    for (const auto& line : lines) {
        out() << "  " << line << "\n";
    }
}

inline std::string join_space(const std::vector<std::string>& values)
{
    std::string joined;
    for (std::size_t i = 0; i < values.size(); ++i) {
        if (i) joined += " ";
        joined += values[i];
    }
    return joined;
}

inline void print_labeled_line(
    dottalk::helpdata::MessageId id,
    const std::unordered_map<std::string, std::string>& vars)
{
    out() << cli::cmdout::message_text(id, vars) << "\n";
}

inline bool show_new_catalog_topic(const std::string& term)
{
    const auto* doc = dottalk::doc::get(term);
    if (!doc) return false;

    out() << doc->name << " - " << doc->summary << "\n";

    if (!doc->syntax.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalSyntaxTitle);
        print_indented_lines(doc->syntax);
    }

    if (!doc->samples.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalExamplesTitle);
        print_indented_lines(doc->samples);
    }

    if (!doc->notes.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalNotesTitle);
        print_indented_lines(doc->notes);
    }

    if (!doc->warnings.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalWarningsTitle);
        print_indented_lines(doc->warnings);
    }

    return true;
}

inline bool show_function_topic_from_doc_catalog(const std::string& term)
{
    const auto* doc = dottalk::expr::get_function_doc(term);
    if (!doc) return false;

    out() << doc->name << " - " << doc->summary << "\n";
    print_labeled_line(
        dottalk::helpdata::MessageId::GlobalCategoryLine,
        {{"value", dottalk::expr::to_string(doc->category)}});
    print_labeled_line(
        dottalk::helpdata::MessageId::GlobalArgumentsLine,
        {{"min", std::to_string(doc->min_args)}, {"max", std::to_string(doc->max_args)}});

    if (!doc->aliases.empty()) {
        print_labeled_line(
            dottalk::helpdata::MessageId::GlobalAliasesLine,
            {{"value", join_space(doc->aliases)}});
    }

    if (!doc->syntax.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalSyntaxTitle);
        print_indented_lines(doc->syntax);
    }

    if (!doc->examples.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalExamplesTitle);
        print_indented_lines(doc->examples);
    }

    if (!doc->notes.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalNotesTitle);
        print_indented_lines(doc->notes);
    }

    if (!doc->warnings.empty()) {
        print_heading(dottalk::helpdata::MessageId::GlobalWarningsTitle);
        print_indented_lines(doc->warnings);
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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::HelpUsageText);
}

inline void print_help_giant_usage()
{
    out()
        << "HELP GIANT\n"
        << "  Full HELP DATA console report.\n\n"
        << "Usage:\n"
        << "  HELP GIANT\n"
        << "  HELP GIANT USAGE\n"
        << "  HELP GIANT TOPICS\n"
        << "  HELP GIANT KIND\n"
        << "  HELP GIANT SOURCE\n"
        << "  HELP GIANT <topic>\n"
        << "  HELP /GIANT\n"
        << "  HELP /GIANT USAGE\n"
        << "  HELP /GIANT TOPICS\n"
        << "  HELP /GIANT KIND\n"
        << "  HELP /GIANT SOURCE\n"
        << "  HELP /GIANT <topic>\n\n"
        << "Notes:\n"
        << "  HELP GIANT is the readable front door over CMDHELP report surfaces.\n"
        << "  HELP /GIANT is an alias for the same surface.\n"
        << "  HELP GIANT TOPICS lists current topic keys.\n"
        << "  HELP GIANT KIND groups help rows by KIND and shows topic membership.\n"
        << "  HELP GIANT SOURCE groups help rows by SOURCE and shows topic membership.\n"
        << "  HELP GIANT <topic> renders the assembled topic from current HELP DATA.\n"
        << "  Output paging is controlled by SET PAGING ON|OFF.\n";
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
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::MessageRoutingProofLine,
            {{"provider", "active_dbf"}, {"symbol", "HELP_HINT_COMMAND"}});
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
            print_heading(dottalk::helpdata::MessageId::GlobalSyntaxTitle);
            print_indented_lines(cmd.syntax);
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
            print_heading(dottalk::helpdata::MessageId::GlobalSubcommandsTitle);
            for (const auto& sc : public_subs) {
                out() << "  " << sc.name << "\n";
            }
        }

        if (!dev_subs.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalDevTransitionalTitle);
            for (const auto& sc : dev_subs) {
                out() << "  " << sc.name << "\n";
            }
        }

        if (!cmd.notes.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalNotesTitle);
            print_indented_lines(cmd.notes);
        }

        if (!cmd.warnings.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalWarningsTitle);
            print_indented_lines(cmd.warnings);
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
            print_heading(dottalk::helpdata::MessageId::GlobalSyntaxTitle);
            print_indented_lines(sc.syntax);
        }

        if (!sc.notes.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalNotesTitle);
            print_indented_lines(sc.notes);
        }

        if (!sc.warnings.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalWarningsTitle);
            print_indented_lines(sc.warnings);
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

        print_labeled_line(
            dottalk::helpdata::MessageId::GlobalCategoryLine,
            {{"value", fn.category}});
        print_labeled_line(
            dottalk::helpdata::MessageId::GlobalArgumentsLine,
            {{"min", std::to_string(fn.min_args)}, {"max", std::to_string(fn.max_args)}});

        if (!fn.aliases.empty()) {
            print_labeled_line(
                dottalk::helpdata::MessageId::GlobalAliasesLine,
                {{"value", join_space(fn.aliases)}});
        }

        print_heading(dottalk::helpdata::MessageId::GlobalSyntaxTitle);
        if (!fn.syntax.empty()) {
            print_indented_lines(fn.syntax);
        } else {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::GlobalFunctionFallbackSyntaxLine,
                {{"name", fn.canonical_name}});
        }

        if (!fn.examples.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalExamplesTitle);
            print_indented_lines(fn.examples);
        }

        if (!fn.notes.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalNotesTitle);
            print_indented_lines(fn.notes);
        }

        if (!fn.warnings.empty()) {
            print_heading(dottalk::helpdata::MessageId::GlobalWarningsTitle);
            print_indented_lines(fn.warnings);
        }

        return true;
    }

    return false;
}

} // anonymous namespace

// --- AIF-047: unified not-found + did-you-mean --------------------------------

inline std::vector<std::string> gather_help_candidates()
{
    std::vector<std::string> names;
    for (const auto& it : dotref::catalog()) if (it.name)  names.emplace_back(it.name);
    for (const auto& it : foxref::catalog()) if (it.name)  names.emplace_back(it.name);
    for (const auto& it : edref::catalog())  if (it.topic) names.emplace_back(it.topic);
    for (const auto* fd : dottalk::expr::all_function_docs()) if (fd) names.push_back(fd->name);
    // HELP's own router keywords (not commands, so absent from the reference catalogs) —
    // so e.g. HELP GAINT can suggest GIANT.
    for (const char* kw : {"GIANT", "BETA", "FUNCTIONS", "FUNCTION", "PREDICATES",
                           "PS", "SQL", "USAGE", "TOPICS", "SOURCE", "KIND"})
        names.emplace_back(kw);
    return names;
}

// HELP owns its miss: the general not-found message + soundex/edit-distance suggestions
// drawn from the reference/function catalogs (reuses the SOUNDEX helper). Replaces the old
// silent delegation to FOXHELP's fox-scoped fallback.
inline void help_not_found(const std::string& term)
{
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::HelpNoTopicFound, {{"command", term}});

    const auto sugg = dottalk::text::rank_suggestions(term, gather_help_candidates(), 5);
    if (!sugg.empty()) {
        out() << "  Did you mean: ";
        for (std::size_t i = 0; i < sugg.size(); ++i) out() << (i ? ", " : "") << sugg[i];
        out() << "?\n";
    }
}

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
        std::istringstream giant("REPORT");
        cmd_CMDHELP(area, giant);
        return;
    }

    if (restUp.rfind("GIANT ", 0) == 0 || restUp.rfind("/GIANT ", 0) == 0) {
        const bool slash = restUp.rfind("/GIANT ", 0) == 0;
        const std::size_t prefix_len = slash ? 7u : 6u;
        std::string giant_rest = rest.substr(prefix_len);
        const std::string giant_up = uptrim(giant_rest);

        if (giant_up == "USAGE" || giant_up == "HELP" || giant_up == "?") {
            print_help_giant_usage();
            return;
        }

        if (giant_up == "TOPICS" || giant_up == "KIND" || giant_up == "SOURCE") {
            std::istringstream giant(std::string("REPORT ") + giant_up);
            cmd_CMDHELP(area, giant);
            return;
        }

        std::istringstream giant(giant_rest);
        cmd_CMDHELP(area, giant);
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

        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::HelpNoFunctionFound,
            {{"command", fn}});
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
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::HelpNoDotTalkTopicFound,
                {{"command", opts.term}});
        }
        return;
    }
    if (opts.onlyEd) {
        if (!show_ed_topic(opts.term)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::HelpNoEducationalTopicFound,
                {{"command", opts.term}});
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
            if (show_fox_topic_local(opts.term)) return;

            // AIF-047: HELP owns the miss with a unified not-found + did-you-mean.
            // (The old HELP_HINT_COMMAND route printed a self-referential "Type HELP <x>
            //  for more information" for every unknown term — the reported "circle" — and
            //  short-circuited this; removed from the unknown-term fallback.)
            help_not_found(opts.term);
            return;
        }

        help_not_found(opts.term);
        return;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::HelpTopLevelHint);
}
