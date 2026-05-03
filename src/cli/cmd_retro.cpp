// src/cli/cmd_retro.cpp
//
// RETRO command
//
// Stable ASCII-safe edition.
// UTF-8/Unicode rendering can come later as polish.
//
// Usage:
//   RETRO LIST
//   RETRO SHOW <system>
//   RETRO <system>
//   RETRO HELP

#include "shell_commands.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <string_view>

using std::cout;
using std::string;
using std::string_view;

namespace {

struct Screen {
    const char* id;
    const char* title;
    const char* art;
};

// -----------------------------------------------------------------------------
// ASCII-safe plates
// -----------------------------------------------------------------------------

static const char* SCR_C64 = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                      COMMODORE 64 BASIC V2                               |
|                                                                          |
|                  64K RAM SYSTEM  38911 BASIC BYTES FREE                  |
|                                                                          |
|                             READY.                                       |
|                                                                          |
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_C128 = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                        COMMODORE 128 SYSTEM                              |
|                                                                          |
|                        BASIC 7.0  (C) COMMODORE                          |
|                                                                          |
|                        122365 BYTES FREE                                 |
|                                                                          |
|                        PRESS UP TO ENTER C64 MODE                        |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_VIC20 = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                     COMMODORE VIC-20 BASIC V2                            |
|                                                                          |
|                            3583 BYTES FREE                               |
|                                                                          |
|                               READY.                                     |
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_AMIGA = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                 \                                                        |
|                  \        .------------.                                  |
|                   \       |  .------.  |                                  |
|                    \      |  |      |  |                                  |
|                     \     |  |  []  |  |                                  |
|                      \    |  '------'  |                                  |
|                       \   '------------'                                  |
|                                                                          |
|                         A M I G A   K I C K S T A R T                    |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_TRS80 = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                        TRS-80 MODEL III BASIC                            |
|                                                                          |
|                     COPYRIGHT (C) TANDY CORPORATION                      |
|                                                                          |
|                               READY                                      |
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_TANDY1000 = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                     TANDY 1000 PERSONAL COMPUTER                         |
|                                                                          |
|                        MS-DOS COMPATIBLE SYSTEM                          |
|                                                                          |
|                        (C) TANDY CORPORATION                             |
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_IBM_BIOS = R"TEXT(
---------------------------------------------------------------------------
 IBM PERSONAL COMPUTER

 640KB OK

 IBM BASIC VERSION C1.10
 (C) COPYRIGHT IBM CORP

---------------------------------------------------------------------------
)TEXT";

static const char* SCR_MSDOS = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                      M S - D O S   V E R S I O N   5 . 0                 |
|                                                                          |
|                                                                          |
| C:\>                                                                     |
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_UNIX = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                        UNIX SYSTEM V  RELEASE 3.2                        |
|                                                                          |
|                                                                          |
| login:                                                                   |
|                                                                          |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_SUNOS = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                           SUN WORKSTATION                                |
|                            SunOS Release 4.x                             |
|                                                                          |
|                                     ok>                                  |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_CPM = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                            CP/M VERSION 2.2                              |
|                         (C) DIGITAL RESEARCH                             |
|                                                                          |
|                                   A>                                     |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_GBC = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                             N I N T E N D O                              |
|                                                                          |
|                            GAME BOY COLOR                                |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_PS2 = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                SONY COMPUTER ENTERTAINMENT                               |
|                                                                          |
|                         [==]        [==]                                 |
|                           [==]    [==]                                   |
|                             [======]                                     |
|                                                                          |
|                         PLAYSTATION 2                                    |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* SCR_XBOX = R"TEXT(
+--------------------------------------------------------------------------+
|                                                                          |
|                               \    /                                     |
|                                \  /                                      |
|                                 XX                                       |
|                                /  \                                      |
|                               /    \                                     |
|                                                                          |
|                                 XBOX                                     |
|                               MICROSOFT                                  |
|                                                                          |
+--------------------------------------------------------------------------+
)TEXT";

// -----------------------------------------------------------------------------
// Catalog
// -----------------------------------------------------------------------------

static const Screen kScreens[] = {
    {"C64",   "Commodore 64",         SCR_C64},
    {"C128",  "Commodore 128",        SCR_C128},
    {"VIC20", "Commodore VIC-20",     SCR_VIC20},
    {"AMIGA", "Amiga Kickstart",      SCR_AMIGA},
    {"TRS80", "TRS-80 Model III",     SCR_TRS80},
    {"T1000", "Tandy 1000",           SCR_TANDY1000},
    {"IBMPC", "IBM PC/XT/AT BIOS",    SCR_IBM_BIOS},
    {"MSDOS", "MS-DOS 5.0",           SCR_MSDOS},
    {"UNIX",  "UNIX System V R3.2",   SCR_UNIX},
    {"SUNOS", "SunOS / Solaris PROM", SCR_SUNOS},
    {"CPM",   "CP/M 2.2",             SCR_CPM},
    {"GBC",   "Game Boy Color",       SCR_GBC},
    {"PS2",   "PlayStation 2",        SCR_PS2},
    {"XBOX",  "Xbox (Original)",      SCR_XBOX}
};

constexpr size_t kScreenCount = sizeof(kScreens) / sizeof(kScreens[0]);

// -----------------------------------------------------------------------------
// Helpers
// -----------------------------------------------------------------------------

string trim(const string& s) {
    const size_t first = s.find_first_not_of(" \t\r\n");
    if (first == string::npos) return "";
    const size_t last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

string upper_copy(string s) {
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char ch) { return static_cast<char>(std::toupper(ch)); });
    return s;
}

bool iequals(string_view a, string_view b) {
    if (a.size() != b.size()) return false;
    for (size_t i = 0; i < a.size(); ++i) {
        const unsigned char ca = static_cast<unsigned char>(a[i]);
        const unsigned char cb = static_cast<unsigned char>(b[i]);
        if (std::toupper(ca) != std::toupper(cb)) return false;
    }
    return true;
}

bool contains_icase(string_view haystack, string_view needle) {
    const string h = upper_copy(string(haystack));
    const string n = upper_copy(string(needle));
    return h.find(n) != string::npos;
}

void clear_screen() {
    cout << "\x1b[2J\x1b[H";
}

const Screen* find_screen_by_key(const string& key) {
    const string want = trim(key);
    if (want.empty()) return nullptr;

    for (size_t i = 0; i < kScreenCount; ++i) {
        const Screen& s = kScreens[i];
        if (iequals(want, s.id) || iequals(want, s.title)) {
            return &s;
        }
    }

    for (size_t i = 0; i < kScreenCount; ++i) {
        const Screen& s = kScreens[i];
        if (contains_icase(s.title, want)) {
            return &s;
        }
    }

    return nullptr;
}

void print_help() {
    cout << "RETRO usage:\n";
    cout << " RETRO LIST\n";
    cout << " RETRO SHOW <system>\n";
    cout << " RETRO <system>\n";
    cout << " RETRO HELP\n";
}

void list_screens() {
    cout << "Available retro screens:\n";
    cout << "\n";
    for (size_t i = 0; i < kScreenCount; ++i) {
        cout << "  " << kScreens[i].id << "  " << kScreens[i].title << "\n";
    }
}

void show_screen(const Screen& s, bool clear_first = true) {
    if (clear_first) {
        clear_screen();
    }
    cout << s.art << "\n";
    cout << "\n[" << s.id << "] " << s.title << "\n";
}

string read_tail(std::istringstream& args) {
    string tail;
    std::getline(args, tail);
    return trim(tail);
}

} // namespace

void cmd_RETRO(xbase::DbArea& area, std::istringstream& args) {
    (void)area;

    const string tail = read_tail(args);

    if (tail.empty()) {
        print_help();
        return;
    }

    std::istringstream iss(tail);
    string verb;
    iss >> verb;

    string rest;
    std::getline(iss, rest);
    rest = trim(rest);

    const string upperVerb = upper_copy(verb);

    if (upperVerb == "HELP" || upperVerb == "/?" || upperVerb == "?") {
        print_help();
        return;
    }

    if (upperVerb == "LIST") {
        list_screens();
        return;
    }

    if (upperVerb == "SHOW") {
        if (rest.empty()) {
            cout << "RETRO SHOW requires a system name or id.\n";
            return;
        }

        const Screen* s = find_screen_by_key(rest);
        if (!s) {
            cout << "Unknown retro system: " << rest << "\n";
            return;
        }

        show_screen(*s, true);
        return;
    }

    const Screen* s = find_screen_by_key(tail);
    if (!s) {
        cout << "Unknown retro system: " << tail << "\n";
        cout << "Use RETRO LIST to see available systems.\n";
        return;
    }

    show_screen(*s, true);
}