// src/cli/cmd_christmas.cpp
// Retro ASCII Christmas tree for DotTalk++ terminal.

#include <cstdlib>
#include <iostream>
#include <sstream>
#include <string>

#include "xbase.hpp"        // defines xbase::DbArea

static inline void ansi(const char* seq) {
    std::cout << seq;
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
    const char* WHITE  = "\033[37m";
    const char* RESET  = "\033[0m";

    const char* tree[] = {
        "         ^",
        "        ^^^",
        "       ^^^^^",
        "      ^^^^^^^",
        "     ^^^^^^^^^",
        "    ^^^^^^^^^^^",
        "   ^^^^^^^^^^^^^",
        "  ^^^^^^^^^^^^^^^",
        " ^^^^^^^^^^^^^^^^^",
        "^^^^^^^^^^^^^^^^^^^^"
    };

    const char* ornaments[] = { "*", "o", "+", "#" };
    const int ornamentCount = 4;

    // Star
    ansi(YELLOW);
    std::cout << "         *\n";

    // Tree body
    for (int i = 0; i < 10; i++) {
        const std::string line = tree[i];

        for (char c : line) {
            if (c == '^') {
                const int r = std::rand() % 20;

                if (r == 0) {
                    ansi(RED);
                    std::cout << ornaments[std::rand() % ornamentCount];
                } else if (r == 1) {
                    ansi(YELLOW);
                    std::cout << ornaments[std::rand() % ornamentCount];
                } else {
                    ansi(GREEN);
                    std::cout << "^";
                }
            } else {
                ansi(WHITE);
                std::cout << c;
            }
        }
        std::cout << "\n";
    }

    // Trunk
    ansi(WHITE);
    std::cout << "         |||\n";
    std::cout << "         |||\n";

    ansi(RESET);
}