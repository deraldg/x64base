// edu_christmas.cpp
// Retro ASCII Christmas tree for DotTalk++ terminal.
// Uses segment-level ANSI coloring so visible width and raw output width stay sane.

// @dottalk.usage v1
// owner: EDU|CHRISTMAS
// command: CHRISTMAS
// category: education-demo
// status: supported
// noargs: report-tree
// effect: report
// mutates: none
// usage-access: CHRISTMAS USAGE
// summary:
//   Print the retro colored ASCII Christmas tree demo.
//
// usage:
//   CHRISTMAS USAGE
//   CHRISTMAS
//
// examples:
//   CHRISTMAS
//
// notes:
//   CHRISTMAS USAGE/HELP/? prints usage before emitting the tree.
//   Non-usage arguments are ignored to preserve prior demo behavior.
//
// risk:
//   mutates_table_data: no
//

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"        // defines xbase::DbArea
#include <cctype>

static inline void ansi(const char* seq) {
    std::cout << seq;
}

static const char* colorFor(char c,
                            const char* green,
                            const char* red,
                            const char* yellow,
                            const char* cyan,
                            const char* white,
                            const char* reset)
{
    switch (c) {
    case '^': return green;
    case '*': return yellow;
    case 'o': return red;
    case '+': return yellow;
    case '#': return cyan;
    case '|': return white;
    default:  return reset;
    }
}

static void printColoredLine(const char* line,
                             const char* green,
                             const char* red,
                             const char* yellow,
                             const char* cyan,
                             const char* white,
                             const char* reset)
{
    const char* active = nullptr;

    for (const char* p = line; *p; ++p) {
        const char c = *p;
        const char* desired = colorFor(c, green, red, yellow, cyan, white, reset);

        if (desired != active) {
            ansi(desired);
            active = desired;
        }

        std::cout << c;
    }

    ansi(reset);
    std::cout << '\n';
}

static std::string christmas_upper_contract(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_christmas_usage_contract()
{
    std::cout
        << "Usage:\n"
        << "  CHRISTMAS USAGE\n"
        << "  CHRISTMAS\n"
        << "Examples:\n"
        << "  CHRISTMAS\n"
        << "Notes:\n"
        << "  - CHRISTMAS USAGE does not print the tree.\n";
}
void edu_CHRISTMAS(xbase::DbArea& A, std::istringstream& in)
{
    // CHRISTMAS_USAGE_CONTRACT_BRANCH
    {
        const std::streampos usage_pos = in.tellg();
        std::string usage_tok;
        if (in >> usage_tok) {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }

            const std::string u = christmas_upper_contract(usage_tok);
            if (u == "USAGE" || u == "HELP" || u == "?") {
                print_christmas_usage_contract();
                return;
            }
        } else {
            in.clear();
            if (usage_pos != std::streampos(-1)) {
                in.seekg(usage_pos);
            }
        }
    }

    // Command handler signature is fixed by the shell registry.
    // CHRISTMAS does not need the current work area or argument stream.
    (void)A;
    const char* GREEN  = "\033[32m";
    const char* RED    = "\033[31m";
    const char* YELLOW = "\033[33m";
    const char* CYAN   = "\033[36m";
    const char* WHITE  = "\033[37m";
    const char* RESET  = "\033[0m";

    // Fixed art, not random: prettier, reproducible, and safe for startup banners.
    // Keep the cone odd-width so centering stays stable in both portrait and landscape.
    const char* tree[] = {
        "         *",
        "         ^",
        "        ^o^",
        "       ^^#^^",
        "      ^^^*^^^",
        "     ^^+^^^^^^",
        "    ^^^^^o^^^^^",
        "   ^^^#^^^^^+^^^",
        "  ^^o^^^^*^^^^^^^",
        " ^^^^^+^^^^^^o^^^^",
        "^^^^#^^^^o^^^^+^^^^",
        "         |||",
        "         |||"
    };

    for (const char* line : tree) {
        printColoredLine(line, GREEN, RED, YELLOW, CYAN, WHITE, RESET);
    }
}
