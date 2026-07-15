#pragma once

#include "retro_screen.hpp"

#include <iosfwd>
#include <string>

namespace dottalk::retro {

enum class RetroMode {
    Native,
    Ascii,
    Legacy
};

struct RenderOptions {
    bool clear_first = true;
    bool caption = true;
    bool info = false;
    bool style_set = false;
    RetroMode mode = RetroMode::Native;
    RetroStyle style = RetroStyle::Plain;
};

const char* mode_name(RetroMode mode);

bool parse_mode(const std::string& token, RetroMode& out);
bool parse_style(const std::string& token, RetroStyle& out);
bool is_direct_style_token(const std::string& token, RetroStyle& out);

void print_styles(std::ostream& os);
void print_modes(std::ostream& os);
void show_info(std::ostream& os, const Screen& screen);
void show_screen(std::ostream& os, const Screen& screen, const RenderOptions& options);

} // namespace dottalk::retro
