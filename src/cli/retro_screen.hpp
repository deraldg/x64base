#pragma once

#include <cstddef>
#include <string_view>

namespace dottalk::retro {

enum class ScreenFamily {
    Basic8Bit,
    DosPc,
    Terminal,
    Workstation,
    Console,
    DisplayAdapter
};

enum class RetroStyle {
    Plain,
    Green,
    Amber,
    Mda,
    Cga,
    Vga,
    Vt100,
    C64Blue,
    AmigaWorkbench,
    GameBoyLcd,
    Ps2Blue,
    XboxGreen
};

struct Screen {
    const char* id;
    const char* title;
    ScreenFamily family;
    int cols;
    int rows;
    RetroStyle native_style;
    const char* native_art;
    const char* ascii_art;
    const char* legacy_art;
    const char* profile_note;
};

const Screen* screens();
std::size_t screen_count();

const Screen* find_screen_by_key(std::string_view key);

const char* family_name(ScreenFamily family);
const char* style_name(RetroStyle style);

} // namespace dottalk::retro
