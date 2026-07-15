// src/cli/cmd_color.cpp
// @dottalk.usage v1
// owner: DOT|COLOR
// command: COLOR
// category: ui
// status: supported
// noargs: report
// effect: configure
// mutates: ui-theme tree-color-setting
// usage-access: COLOR USAGE
// summary:
//   Report or set the console color theme and tree-color behavior.
//
// usage:
//   COLOR
//   COLOR USAGE
//   COLOR DEFAULT
//   COLOR GREEN
//   COLOR AMBER
//   COLOR TREE ON
//   COLOR TREE OFF
//   COLOR TREECOLOR ON
//   COLOR TREECOLOR OFF
//
// notes:
//   COLOR with no arguments reports the current theme, tree-color setting, and tree palette levels.
//   COLOR DEFAULT, GREEN, AMBER, and other parseable theme names apply the console theme.
//   COLOR TREE ON and COLOR TREE OFF toggle tree-color behavior.
//   COLOR TREECOLOR is accepted as an alias for COLOR TREE.
//   COLOR mutates UI presentation settings only.
//
// risk:
//   mutates_table_data: no
//   mutates_session_ui: yes
//   writes_files: no
//
// related:
//   CLEAR
//   TREE
//   HELP
//

#include "xbase.hpp"
#include "colors.hpp"
#include "cli/command_output.hpp"

#include <iostream>
#include <cctype>
#include <sstream>
#include <string>

using xbase::DbArea;


namespace {
static std::string color_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static void print_color_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ColorUsageText);
}
} // namespace

void cmd_COLOR(DbArea& /*A*/, std::istringstream& iss) {
    using namespace dli::colors;

    std::string arg;
    if (!(iss >> arg)) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ColorStatusText,
            {{"value", themeName(currentTheme())}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ColorTreeColorStatusText,
            {{"value", treeColorEnabled() ? "ON" : "OFF"}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ColorTreePaletteHeaderText,
            {{"count", std::to_string(treePaletteSize())}});
        for (std::size_t i = 0; i < treePaletteSize(); ++i) {
            const Theme t = treeThemeForLevel(static_cast<int>(i));
            emitTheme(t);
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::ColorTreeLevelLineText,
                {
                    {"level", std::to_string(i)},
                    {"value", themeName(t)}
                });
            emitCurrentTheme();
        }
        return;
    }

    const std::string ARG = color_upper(arg);
    if (ARG == "USAGE" || ARG == "HELP" || ARG == "?") {
        print_color_usage();
        return;
    }

    std::string sub;
    if (ARG == "TREE" || ARG == "TREECOLOR") {
        if (!(iss >> sub)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::ColorTreeColorStatusText,
                {{"value", treeColorEnabled() ? "ON" : "OFF"}});
            return;
        }

        for (char& ch : sub) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));

        if (sub == "ON") {
            setTreeColorEnabled(true);
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::ColorTreeSetStatusText,
                {{"value", "ON"}});
            return;
        }
        if (sub == "OFF") {
            setTreeColorEnabled(false);
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::ColorTreeSetStatusText,
                {{"value", "OFF"}});
            return;
        }

        print_color_usage();
        return;
    }

    // Accept COLOR DEFAULT | GREEN | AMBER | etc.
    Theme t = parseTheme(arg);
    applyTheme(t);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ColorSetStatusText,
        {{"value", themeName(t)}});
}
