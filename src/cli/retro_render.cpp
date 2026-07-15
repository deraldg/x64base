#include "retro_render.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <ostream>
#include <string>

namespace dottalk::retro {
namespace {

std::string upper_copy(std::string s) {
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char ch) { return static_cast<char>(std::toupper(ch)); });
    return s;
}

const char* ansi_prefix(RetroStyle style) {
    switch (style) {
    case RetroStyle::Plain:          return "";
    case RetroStyle::Green:          return "\x1b[0;32m";
    case RetroStyle::Amber:          return "\x1b[0;33m";
    case RetroStyle::Mda:            return "\x1b[0;37m";
    case RetroStyle::Cga:            return "\x1b[0;36m";
    case RetroStyle::Vga:            return "\x1b[1;37m";
    case RetroStyle::Vt100:          return "\x1b[0;32m";
    case RetroStyle::C64Blue:        return "\x1b[44;96m";
    case RetroStyle::AmigaWorkbench: return "\x1b[47;34m";
    case RetroStyle::GameBoyLcd:     return "\x1b[42;30m";
    case RetroStyle::Ps2Blue:        return "\x1b[40;34m";
    case RetroStyle::XboxGreen:      return "\x1b[40;92m";
    }
    return "";
}

const char* ansi_suffix(RetroStyle style) {
    return style == RetroStyle::Plain ? "" : "\x1b[0m";
}

const char* art_for(const Screen& s, RetroMode mode) {
    switch (mode) {
    case RetroMode::Native: return s.native_art ? s.native_art : s.ascii_art;
    case RetroMode::Ascii:  return s.ascii_art ? s.ascii_art : s.native_art;
    case RetroMode::Legacy: return s.legacy_art ? s.legacy_art : (s.ascii_art ? s.ascii_art : s.native_art);
    }
    return s.ascii_art ? s.ascii_art : s.native_art;
}

RetroStyle effective_style(const Screen& s, const RenderOptions& options) {
    if (options.mode == RetroMode::Ascii) {
        return RetroStyle::Plain;
    }
    if (options.style_set) {
        return options.style;
    }
    if (options.mode == RetroMode::Native) {
        return s.native_style;
    }
    return RetroStyle::Plain;
}

void clear_screen(std::ostream& os) {
    os << "\x1b[2J\x1b[H";
}

} // namespace

const char* mode_name(RetroMode mode) {
    switch (mode) {
    case RetroMode::Native: return "NATIVE";
    case RetroMode::Ascii:  return "ASCII";
    case RetroMode::Legacy: return "LEGACY";
    }
    return "NATIVE";
}

bool parse_mode(const std::string& token, RetroMode& out) {
    const std::string u = upper_copy(token);
    if (u == "NATIVE" || u == "AUTHENTIC" || u == "PROFILE") {
        out = RetroMode::Native;
        return true;
    }
    if (u == "ASCII" || u == "TEXT") {
        out = RetroMode::Ascii;
        return true;
    }
    if (u == "LEGACY" || u == "OLD" || u == "V2") {
        out = RetroMode::Legacy;
        return true;
    }
    return false;
}

bool parse_style(const std::string& token, RetroStyle& out) {
    const std::string u = upper_copy(token);

    if (u == "PLAIN" || u == "NONE" || u == "NOANSI") {
        out = RetroStyle::Plain;
        return true;
    }
    if (u == "GREEN" || u == "PHOSPHOR" || u == "GREENPHOSPHOR") {
        out = RetroStyle::Green;
        return true;
    }
    if (u == "AMBER" || u == "ORANGE") {
        out = RetroStyle::Amber;
        return true;
    }
    if (u == "MDA" || u == "MONO" || u == "MONOCHROME") {
        out = RetroStyle::Mda;
        return true;
    }
    if (u == "CGA") {
        out = RetroStyle::Cga;
        return true;
    }
    if (u == "VGA") {
        out = RetroStyle::Vga;
        return true;
    }
    if (u == "VT100" || u == "VT") {
        out = RetroStyle::Vt100;
        return true;
    }
    if (u == "C64BLUE" || u == "C64" || u == "COMMODORE") {
        out = RetroStyle::C64Blue;
        return true;
    }
    if (u == "AMIGA" || u == "WORKBENCH" || u == "KICKSTART") {
        out = RetroStyle::AmigaWorkbench;
        return true;
    }
    if (u == "GAMEBOY" || u == "GBC" || u == "LCD") {
        out = RetroStyle::GameBoyLcd;
        return true;
    }
    if (u == "PS2" || u == "PS2BLUE") {
        out = RetroStyle::Ps2Blue;
        return true;
    }
    if (u == "XBOX" || u == "XBOXGREEN") {
        out = RetroStyle::XboxGreen;
        return true;
    }

    return false;
}

bool is_direct_style_token(const std::string& token, RetroStyle& out) {
    const std::string u = upper_copy(token);
    if (u == "STYLE" || u == "MODE" || u == "NATIVE" || u == "AUTHENTIC" ||
        u == "LEGACY" || u == "TEXT" || u == "ASCII") {
        return false;
    }
    return parse_style(token, out);
}

void print_styles(std::ostream& os) {
    os << "Available RETRO styles:\n\n";
    os << "  PLAIN      ASCII output, no ANSI color\n";
    os << "  GREEN      green phosphor ANSI foreground\n";
    os << "  AMBER      amber phosphor ANSI foreground\n";
    os << "  MDA        white monochrome ANSI foreground\n";
    os << "  CGA        cyan ANSI foreground\n";
    os << "  VGA        bright white ANSI foreground\n";
    os << "  VT100      green terminal-style ANSI foreground\n";
    os << "  C64BLUE    cyan-on-blue Commodore-style profile\n";
    os << "  AMIGA      blue-on-white Workbench/Kickstart-style profile\n";
    os << "  GAMEBOY    black-on-green handheld LCD-style profile\n";
    os << "  PS2BLUE    dark blue console-style profile\n";
    os << "  XBOXGREEN  bright green console-style profile\n";
}

void print_modes(std::ostream& os) {
    os << "Available RETRO modes:\n\n";
    os << "  NATIVE  system-specific geometry/text/color profile\n";
    os << "  ASCII   system-specific plain text, no ANSI color\n";
    os << "  LEGACY  older framed v1/v2-style plate\n";
}

void show_info(std::ostream& os, const Screen& s) {
    os << s.id << " - " << s.title << "\n";
    os << "  family : " << family_name(s.family) << "\n";
    os << "  profile: " << s.cols << "x" << s.rows << "\n";
    os << "  native : " << style_name(s.native_style) << "\n";
    os << "  note   : " << (s.profile_note ? s.profile_note : "") << "\n";
}

void show_screen(std::ostream& os, const Screen& s, const RenderOptions& options) {
    if (options.info) {
        show_info(os, s);
        return;
    }

    if (options.clear_first) {
        clear_screen(os);
    }

    const RetroStyle style = effective_style(s, options);
    os << ansi_prefix(style);
    os << art_for(s, options.mode) << "\n";
    os << ansi_suffix(style);

    if (options.caption) {
        os << "\n[" << s.id << "] " << s.title
           << "  family=" << family_name(s.family)
           << "  profile=" << s.cols << "x" << s.rows
           << "  mode=" << mode_name(options.mode)
           << "  style=" << style_name(style) << "\n";
    }
}

} // namespace dottalk::retro
