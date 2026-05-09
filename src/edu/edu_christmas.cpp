// edu_christmas.cpp
// Retro ASCII Christmas tree for DotTalk++ terminal.
// Uses segment-level ANSI coloring so visible width and raw output width stay sane.

#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"        // defines xbase::DbArea

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

void cmd_CHRISTMAS(xbase::DbArea& A, std::istringstream& in)
{
    // Command handler signature is fixed by the shell registry.
    // CHRISTMAS does not need the current work area or argument stream.
    (void)A;
    (void)in;

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
