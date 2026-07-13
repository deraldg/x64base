// edu_hanukkah.cpp
// Retro ASCII Hanukkah menorah + dreidel for DotTalk++ terminal.
// Uses segment-level ANSI coloring so visible width and raw output width stay sane.

// @dottalk.usage v1
// owner: EDU|HANUKKAH
// command: HANUKKAH
// category: education-demo
// status: supported
// noargs: report-hanukkah
// effect: report
// mutates: none
// usage-access: HANUKKAH USAGE
// summary:
//   Print the retro colored ASCII Hanukkah menorah demo.
//
// usage:
//   HANUKKAH USAGE
//   HANUKKAH
//
// examples:
//   HANUKKAH
//
// notes:
//   HANUKKAH USAGE/HELP/? prints usage before emitting the art.
//   Non-usage arguments are ignored to preserve demo behavior.
//
// risk:
//   mutates_table_data: no
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"
#include <cctype>

static inline void ansi(const char* seq) {
    std::cout << seq;
}

static const char* colorFor(char c,
                            const char* blue,
                            const char* gold,
                            const char* yellow,
                            const char* cyan,
                            const char* white,
                            const char* reset)
{
    switch (c) {
    case '^': return yellow;
    case '*': return gold;
    case '|': return white;
    case '#': return cyan;
    case '+': return gold;
    case 'o': return yellow;
    case '/':
    case '\\':
    case '_': return blue;
    default:  return reset;
    }
}

static void printColoredLine(const char* line,
                             const char* blue,
                             const char* gold,
                             const char* yellow,
                             const char* cyan,
                             const char* white,
                             const char* reset)
{
    const char* active = nullptr;

    for (const char* p = line; *p; ++p) {
        const char c = *p;
        const char* desired = colorFor(c, blue, gold, yellow, cyan, white, reset);

        if (desired != active) {
            ansi(desired);
            active = desired;
        }

        std::cout << c;
    }

    ansi(reset);
    std::cout << '\n';
}

static std::string hanukkah_upper_contract(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_hanukkah_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  HANUKKAH USAGE\n"
        << "  HANUKKAH\n"
        << "Examples:\n"
        << "  HANUKKAH\n"
        << "Notes:\n"
        << "  - HANUKKAH USAGE does not print the menorah.\n";
}

void edu_HANUKKAH(xbase::DbArea& A, std::istringstream& in)
{
    {
        const std::streampos usage_pos = in.tellg();
        std::string usage_tok;
        if (in >> usage_tok) {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }

            const std::string u = hanukkah_upper_contract(usage_tok);
            if (u == "USAGE" || u == "HELP" || u == "?") {
                print_hanukkah_usage_contract();
                return;
            }
        } else {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }
        }
    }

    (void)A;

    const char* BLUE   = "\033[34m";
    const char* GOLD   = "\033[33m";
    const char* YELLOW = "\033[93m";
    const char* CYAN   = "\033[36m";
    const char* WHITE  = "\033[37m";
    const char* RESET  = "\033[0m";

    const char* art[] = {
        "           ^",
        "          ^*^",
        "         ^   ^",
        "        ^     ^",
        "       ^       ^",
        "      ^         ^",
        "     ^           ^",
        "    ^             ^",
        "   ^               ^",
        "          |||",
        "          |||",
        "       ++++++++",
        "      o  DREIDEL o",
        "       ++++++++"
    };

    for (const char* line : art) {
        printColoredLine(line, BLUE, GOLD, YELLOW, CYAN, WHITE, RESET);
    }
}
