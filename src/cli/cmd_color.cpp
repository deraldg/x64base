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
    std::cout
        << "Usage:\n"
        << "  COLOR\n"
        << "  COLOR USAGE\n"
        << "  COLOR DEFAULT\n"
        << "  COLOR GREEN\n"
        << "  COLOR AMBER\n"
        << "  COLOR TREE ON\n"
        << "  COLOR TREE OFF\n"
        << "  COLOR TREECOLOR ON\n"
        << "  COLOR TREECOLOR OFF\n"
        << "Notes:\n"
        << "  - COLOR with no arguments reports current theme and tree palette state.\n"
        << "  - COLOR TREE/TREECOLOR toggles tree-color behavior.\n";
}
} // namespace

void cmd_COLOR(DbArea& /*A*/, std::istringstream& iss) {
    using namespace dli::colors;

    std::string arg;
    if (!(iss >> arg)) {
        std::cout << "COLOR is " << themeName(currentTheme()) << "\n";
        std::cout << "TREECOLOR is " << (treeColorEnabled() ? "ON" : "OFF") << "\n";
        std::cout << "TREE palette rotates across " << treePaletteSize() << " levels:\n";
        for (std::size_t i = 0; i < treePaletteSize(); ++i) {
            const Theme t = treeThemeForLevel(static_cast<int>(i));
            emitTheme(t);
            std::cout << "  Level " << i << ": " << themeName(t) << "\n";
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
            std::cout << "TREECOLOR is " << (treeColorEnabled() ? "ON" : "OFF") << "\n";
            return;
        }

        for (char& ch : sub) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));

        if (sub == "ON") {
            setTreeColorEnabled(true);
            std::cout << "TREECOLOR set to ON\n";
            return;
        }
        if (sub == "OFF") {
            setTreeColorEnabled(false);
            std::cout << "TREECOLOR set to OFF\n";
            return;
        }

        print_color_usage();
        return;
    }

    // Accept COLOR DEFAULT | GREEN | AMBER | etc.
    Theme t = parseTheme(arg);
    applyTheme(t);
    std::cout << "COLOR set to " << themeName(t) << "\n";
}
