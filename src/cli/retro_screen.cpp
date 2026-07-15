#include "retro_screen.hpp"

#include <algorithm>
#include <cctype>
#include <string>

namespace dottalk::retro {
namespace {

std::string trim_copy(std::string s) {
    const std::size_t first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos) return "";
    const std::size_t last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

std::string upper_copy(std::string s) {
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char ch) { return static_cast<char>(std::toupper(ch)); });
    return s;
}

bool iequals(std::string_view a, std::string_view b) {
    if (a.size() != b.size()) return false;
    for (std::size_t i = 0; i < a.size(); ++i) {
        const unsigned char ca = static_cast<unsigned char>(a[i]);
        const unsigned char cb = static_cast<unsigned char>(b[i]);
        if (std::toupper(ca) != std::toupper(cb)) return false;
    }
    return true;
}

bool contains_icase(std::string_view haystack, std::string_view needle) {
    const std::string h = upper_copy(std::string(haystack));
    const std::string n = upper_copy(std::string(needle));
    return h.find(n) != std::string::npos;
}

// -----------------------------------------------------------------------------
// NATIVE / ASCII plates
// -----------------------------------------------------------------------------
// These are terminal approximations. They intentionally favor recognizable
// geometry, boot language, and display character over large decorative banners.

static const char* NATIVE_C64 = R"TEXT(
****************************************
*      COMMODORE 64 BASIC V2           *
*                                      *
*64K RAM SYSTEM  38911 BASIC BYTES FREE*
*                                      *
* READY.                               *
*                                      *
****************************************
)TEXT";

static const char* ASCII_C64 = R"TEXT(
**** COMMODORE 64 BASIC V2 ****

 64K RAM SYSTEM  38911 BASIC BYTES FREE

READY.
)TEXT";

static const char* NATIVE_C128 = R"TEXT(
****************************************
*       COMMODORE 128 BASIC 7.0        *
*                                      *
* 122365 BYTES FREE                    *
*                                      *
* GRAPHIC CLR                          *
* READY.                               *
****************************************
)TEXT";

static const char* ASCII_C128 = R"TEXT(
COMMODORE 128 BASIC 7.0
122365 BYTES FREE

READY.
)TEXT";

static const char* NATIVE_VIC20 = R"TEXT(
**********************
* COMMODORE VIC-20   *
* BASIC V2           *
*                    *
* 3583 BYTES FREE    *
*                    *
* READY.             *
**********************
)TEXT";

static const char* ASCII_VIC20 = R"TEXT(
COMMODORE VIC-20 BASIC V2
3583 BYTES FREE

READY.
)TEXT";

static const char* NATIVE_TRS80 = R"TEXT(
TRS-80 MODEL III BASIC
MEMORY SIZE?

RADIO SHACK LEVEL II BASIC
READY
>
)TEXT";

static const char* ASCII_TRS80 = R"TEXT(
TRS-80 MODEL III BASIC
READY
>
)TEXT";

static const char* NATIVE_IBMPC = R"TEXT(
IBM PERSONAL COMPUTER

640KB OK

IBM BASIC VERSION C1.10
(C) COPYRIGHT IBM CORP 1981

The IBM Personal Computer Basic
Version C1.10 Copyright IBM Corp 1981
Ok
)TEXT";

static const char* ASCII_IBMPC = R"TEXT(
IBM PERSONAL COMPUTER
640KB OK
IBM BASIC VERSION C1.10
Ok
)TEXT";

static const char* NATIVE_MSDOS = R"TEXT(
Starting MS-DOS...

HIMEM is testing extended memory...done.

Microsoft(R) MS-DOS(R) Version 5.00
             (C)Copyright Microsoft Corp 1981-1991.

C:\>
)TEXT";

static const char* ASCII_MSDOS = R"TEXT(
Microsoft MS-DOS Version 5.00

C:\>
)TEXT";

static const char* NATIVE_TANDY1000 = R"TEXT(
TANDY 1000 PERSONAL COMPUTER

Phoenix ROM BIOS PLUS Version 1.10
Copyright 1985, 1986 Phoenix Technologies Ltd.

640K System RAM Passed

A>_
)TEXT";

static const char* ASCII_TANDY1000 = R"TEXT(
TANDY 1000 PERSONAL COMPUTER
640K System RAM Passed
A>_
)TEXT";

static const char* NATIVE_CPM = R"TEXT(
CP/M 2.2

A>DIR
A: ASM      COM : DDT      COM : DUMP     COM : ED       COM
A: LOAD     COM : PIP      COM : STAT     COM : SUBMIT   COM

A>_
)TEXT";

static const char* ASCII_CPM = R"TEXT(
CP/M 2.2
A>_
)TEXT";

static const char* NATIVE_VT100 = R"TEXT(
DEC VT100

SET-UP A

TO EXIT PRESS SET-UP


login: _
)TEXT";

static const char* ASCII_VT100 = R"TEXT(
DEC VT100  80x24
login: _
)TEXT";

static const char* NATIVE_UNIX = R"TEXT(

UNIX System V Release 3.2

Console Login: _




)TEXT";

static const char* ASCII_UNIX = R"TEXT(
UNIX System V Release 3.2
login: _
)TEXT";

static const char* NATIVE_SUNOS = R"TEXT(
Sun Workstation
ROM Rev. 2.9, 32 MB memory installed, Serial #00000000.
Ethernet address 8:0:20:0:0:0, Host ID: 00000000.

Testing 32 megs of memory... completed.
Boot device: net  File and args:

ok _
)TEXT";

static const char* ASCII_SUNOS = R"TEXT(
Sun Workstation OpenBoot
ok _
)TEXT";

static const char* NATIVE_AMIGA = R"TEXT(

                 .-------------------.
                /   WORKBENCH 1.3   /|
               /-------------------/ |
              |  .---------------. | |
              |  |               | | /
              |  |       []      | |/
              |  '---------------' |
              '-------------------'

              Insert Workbench disk

)TEXT";

static const char* ASCII_AMIGA = R"TEXT(
AMIGA KICKSTART
[ insert Workbench disk ]
)TEXT";

static const char* NATIVE_GBC = R"TEXT(


             N I N T E N D O


        -------------------------
        GAME BOY        C O L O R
        -------------------------


)TEXT";

static const char* ASCII_GBC = R"TEXT(
NINTENDO
GAME BOY COLOR
)TEXT";

static const char* NATIVE_PS2 = R"TEXT(


        Sony Computer Entertainment

             | |          | |
             | |    ||    | |
        | |  | |    ||    | |  | |
        | |        ||||        | |
                  ||||||

                 PlayStation 2

)TEXT";

static const char* ASCII_PS2 = R"TEXT(
Sony Computer Entertainment
PlayStation 2
)TEXT";

static const char* NATIVE_XBOX = R"TEXT(


                    .-.
                 .-'   '-.
              .-'   .X.   '-.
                 .-'   '-.
                    '-'

                    XBOX
                  Microsoft

)TEXT";

static const char* ASCII_XBOX = R"TEXT(
XBOX
Microsoft
)TEXT";

static const char* NATIVE_MDA = R"TEXT(
IBM MONOCHROME DISPLAY ADAPTER
80 x 25 TEXT MODE

Foreground: high-intensity white
Background: black
Graphics: text / box drawing only

C:\>_
)TEXT";

static const char* ASCII_MDA = R"TEXT(
IBM MDA 80x25 monochrome text
C:\>_
)TEXT";

static const char* NATIVE_CGA = R"TEXT(
IBM COLOR/GRAPHICS ADAPTER

CGA MODE SAMPLE

  0 BLACK    1 BLUE     2 GREEN    3 CYAN
  4 RED      5 MAGENTA  6 BROWN    7 WHITE

[ ][ ][ ][ ][ ][ ][ ][ ]
)TEXT";

static const char* ASCII_CGA = R"TEXT(
IBM CGA text/color sample
BLACK BLUE GREEN CYAN RED MAGENTA BROWN WHITE
)TEXT";

static const char* NATIVE_VGA = R"TEXT(
VGA BIOS
Video Graphics Array Compatible
80 x 25 Color Text Mode

Resolution families: 640x480 and beyond
Text attribute mode active

C:\>_
)TEXT";

static const char* ASCII_VGA = R"TEXT(
VGA compatible text mode
C:\>_
)TEXT";

// -----------------------------------------------------------------------------
// Legacy v1/v2-style framed plates
// -----------------------------------------------------------------------------

static const char* LEGACY_C64 = R"TEXT(
+--------------------------------------------------------------------------+
|                      COMMODORE 64 BASIC V2                               |
|                  64K RAM SYSTEM  38911 BASIC BYTES FREE                  |
|                             READY.                                       |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_C128 = R"TEXT(
+--------------------------------------------------------------------------+
|                        COMMODORE 128 SYSTEM                              |
|                        BASIC 7.0  (C) COMMODORE                          |
|                        122365 BYTES FREE                                 |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_VIC20 = R"TEXT(
+--------------------------------------------------------------------------+
|                     COMMODORE VIC-20 BASIC V2                            |
|                            3583 BYTES FREE                               |
|                               READY.                                     |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_AMIGA = R"TEXT(
+--------------------------------------------------------------------------+
|                         A M I G A   K I C K S T A R T                    |
|                          [ insert Workbench disk ]                        |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_TRS80 = R"TEXT(
+--------------------------------------------------------------------------+
|                        TRS-80 MODEL III BASIC                            |
|                               READY                                      |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_TANDY1000 = R"TEXT(
+--------------------------------------------------------------------------+
|                     TANDY 1000 PERSONAL COMPUTER                         |
|                        MS-DOS COMPATIBLE SYSTEM                          |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_IBMPC = R"TEXT(
---------------------------------------------------------------------------
 IBM PERSONAL COMPUTER
 640KB OK
 IBM BASIC VERSION C1.10
---------------------------------------------------------------------------
)TEXT";

static const char* LEGACY_MSDOS = R"TEXT(
+--------------------------------------------------------------------------+
|                      M S - D O S   V E R S I O N   5 . 0                 |
| C:\>                                                                     |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_UNIX = R"TEXT(
+--------------------------------------------------------------------------+
|                        UNIX SYSTEM V  RELEASE 3.2                        |
| login:                                                                   |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_SUNOS = R"TEXT(
+--------------------------------------------------------------------------+
|                           SUN WORKSTATION                                |
|                            SunOS Release 4.x                             |
|                                     ok>                                  |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_CPM = R"TEXT(
+--------------------------------------------------------------------------+
|                            CP/M VERSION 2.2                              |
|                                   A>                                     |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_GBC = R"TEXT(
+--------------------------------------------------------------------------+
|                             N I N T E N D O                              |
|                            GAME BOY COLOR                                |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_PS2 = R"TEXT(
+--------------------------------------------------------------------------+
|                SONY COMPUTER ENTERTAINMENT                               |
|                         PLAYSTATION 2                                    |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_XBOX = R"TEXT(
+--------------------------------------------------------------------------+
|                                 XBOX                                     |
|                               MICROSOFT                                  |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_MDA = R"TEXT(
+--------------------------------------------------------------------------+
|                   IBM MONOCHROME DISPLAY ADAPTER                         |
|                         80 x 25 TEXT MODE                                |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_CGA = R"TEXT(
+--------------------------------------------------------------------------+
|                    IBM COLOR/GRAPHICS ADAPTER                            |
|                    4-COLOR / 16-COLOR TEXT ERA                           |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_VGA = R"TEXT(
+--------------------------------------------------------------------------+
|                         VIDEO GRAPHICS ARRAY                             |
|                         80 x 25 COLOR TEXT                               |
+--------------------------------------------------------------------------+
)TEXT";

static const char* LEGACY_VT100 = R"TEXT(
+--------------------------------------------------------------------------+
|                              DEC VT100                                   |
|                         80 x 24 TERMINAL                                 |
| login:                                                                   |
+--------------------------------------------------------------------------+
)TEXT";

static const Screen kScreens[] = {
    {"C64",   "Commodore 64",          ScreenFamily::Basic8Bit,      40, 25, RetroStyle::C64Blue,        NATIVE_C64,       ASCII_C64,       LEGACY_C64,       "40-column blue BASIC V2 startup profile."},
    {"C128",  "Commodore 128",         ScreenFamily::Basic8Bit,      40, 25, RetroStyle::C64Blue,        NATIVE_C128,      ASCII_C128,      LEGACY_C128,      "Commodore 128 BASIC 7.0 style profile."},
    {"VIC20", "Commodore VIC-20",      ScreenFamily::Basic8Bit,      22, 23, RetroStyle::C64Blue,        NATIVE_VIC20,     ASCII_VIC20,     LEGACY_VIC20,     "Small-memory VIC BASIC startup profile."},
    {"TRS80", "TRS-80 Model III",      ScreenFamily::Basic8Bit,      64, 16, RetroStyle::Green,          NATIVE_TRS80,     ASCII_TRS80,     LEGACY_TRS80,     "Green/monochrome BASIC prompt profile."},
    {"IBMPC", "IBM PC/XT/AT BIOS",     ScreenFamily::DosPc,          80, 25, RetroStyle::Mda,            NATIVE_IBMPC,     ASCII_IBMPC,     LEGACY_IBMPC,     "Sparse IBM PC POST/BASIC text profile."},
    {"MSDOS", "MS-DOS 5.0",            ScreenFamily::DosPc,          80, 25, RetroStyle::Vga,            NATIVE_MSDOS,     ASCII_MSDOS,     LEGACY_MSDOS,     "DOS command-prompt text-mode profile."},
    {"T1000", "Tandy 1000",            ScreenFamily::DosPc,          80, 25, RetroStyle::Cga,            NATIVE_TANDY1000, ASCII_TANDY1000, LEGACY_TANDY1000, "Tandy-compatible DOS-era PC profile."},
    {"CPM",   "CP/M 2.2",              ScreenFamily::Terminal,       80, 24, RetroStyle::Green,          NATIVE_CPM,       ASCII_CPM,       LEGACY_CPM,       "CP/M A> prompt and directory-era profile."},
    {"VT100", "DEC VT100",             ScreenFamily::Terminal,       80, 24, RetroStyle::Vt100,          NATIVE_VT100,     ASCII_VT100,     LEGACY_VT100,     "DEC terminal setup/login profile."},
    {"UNIX",  "UNIX System V R3.2",    ScreenFamily::Terminal,       80, 24, RetroStyle::Vt100,          NATIVE_UNIX,      ASCII_UNIX,      LEGACY_UNIX,      "Plain serial console login profile."},
    {"SUNOS", "SunOS / OpenBoot PROM", ScreenFamily::Workstation,    80, 34, RetroStyle::Amber,          NATIVE_SUNOS,     ASCII_SUNOS,     LEGACY_SUNOS,     "Sun workstation PROM ok-prompt profile."},
    {"AMIGA", "Amiga Kickstart",       ScreenFamily::Workstation,    80, 32, RetroStyle::AmigaWorkbench, NATIVE_AMIGA,     ASCII_AMIGA,     LEGACY_AMIGA,     "Kickstart insert-Workbench-disk style profile."},
    {"GBC",   "Game Boy Color",        ScreenFamily::Console,        20, 18, RetroStyle::GameBoyLcd,     NATIVE_GBC,       ASCII_GBC,       LEGACY_GBC,       "Handheld boot logo/text profile."},
    {"PS2",   "PlayStation 2",         ScreenFamily::Console,        64, 32, RetroStyle::Ps2Blue,        NATIVE_PS2,       ASCII_PS2,       LEGACY_PS2,       "Dark blue console boot field approximation."},
    {"XBOX",  "Xbox Original",         ScreenFamily::Console,        64, 32, RetroStyle::XboxGreen,      NATIVE_XBOX,      ASCII_XBOX,      LEGACY_XBOX,      "Green original-Xbox boot identity approximation."},
    {"MDA",   "IBM MDA Display",       ScreenFamily::DisplayAdapter, 80, 25, RetroStyle::Mda,            NATIVE_MDA,       ASCII_MDA,       LEGACY_MDA,       "Monochrome text display adapter profile."},
    {"CGA",   "IBM CGA Display",       ScreenFamily::DisplayAdapter, 80, 25, RetroStyle::Cga,            NATIVE_CGA,       ASCII_CGA,       LEGACY_CGA,       "Early IBM color/text display adapter profile."},
    {"VGA",   "IBM VGA Display",       ScreenFamily::DisplayAdapter, 80, 25, RetroStyle::Vga,            NATIVE_VGA,       ASCII_VGA,       LEGACY_VGA,       "VGA-compatible color text display profile."}
};

constexpr std::size_t kScreenCount = sizeof(kScreens) / sizeof(kScreens[0]);

} // namespace

const Screen* screens() {
    return kScreens;
}

std::size_t screen_count() {
    return kScreenCount;
}

const Screen* find_screen_by_key(std::string_view key) {
    const std::string want = trim_copy(std::string(key));
    if (want.empty()) return nullptr;

    for (std::size_t i = 0; i < kScreenCount; ++i) {
        const Screen& s = kScreens[i];
        if (iequals(want, s.id) || iequals(want, s.title)) {
            return &s;
        }
    }

    for (std::size_t i = 0; i < kScreenCount; ++i) {
        const Screen& s = kScreens[i];
        if (contains_icase(s.title, want)) {
            return &s;
        }
    }

    return nullptr;
}

const char* family_name(ScreenFamily family) {
    switch (family) {
    case ScreenFamily::Basic8Bit:      return "8-bit BASIC";
    case ScreenFamily::DosPc:          return "DOS/PC";
    case ScreenFamily::Terminal:       return "terminal";
    case ScreenFamily::Workstation:    return "workstation";
    case ScreenFamily::Console:        return "console";
    case ScreenFamily::DisplayAdapter: return "display-adapter";
    }
    return "unknown";
}

const char* style_name(RetroStyle style) {
    switch (style) {
    case RetroStyle::Plain:           return "PLAIN";
    case RetroStyle::Green:           return "GREEN";
    case RetroStyle::Amber:           return "AMBER";
    case RetroStyle::Mda:             return "MDA";
    case RetroStyle::Cga:             return "CGA";
    case RetroStyle::Vga:             return "VGA";
    case RetroStyle::Vt100:           return "VT100";
    case RetroStyle::C64Blue:         return "C64BLUE";
    case RetroStyle::AmigaWorkbench:  return "AMIGA";
    case RetroStyle::GameBoyLcd:      return "GAMEBOY";
    case RetroStyle::Ps2Blue:         return "PS2BLUE";
    case RetroStyle::XboxGreen:       return "XBOXGREEN";
    }
    return "PLAIN";
}

} // namespace dottalk::retro
