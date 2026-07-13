// src/cli/cmd_retro.cpp
//
// RETRO command v4 split-file edition.
//
// The command parser stays thin. Screen profiles live in retro_screen.* and
// rendering policy lives in retro_render.*.

// @dottalk.usage v1
// owner: DOT|RETRO
// command: RETRO
// category: display
// status: supported
// noargs: usage
// effect: display
// mutates: console-output
// usage-access: RETRO USAGE
// summary:
//   Display retro computer/system splash screens with system-specific terminal profiles.
//
// usage:
//   RETRO USAGE
//   RETRO LIST
//   RETRO LIST LONG
//   RETRO STYLES
//   RETRO MODES
//   RETRO SHOW <system>
//   RETRO SHOW <system> NATIVE
//   RETRO SHOW <system> ASCII
//   RETRO SHOW <system> LEGACY
//   RETRO SHOW <system> STYLE <style>
//   RETRO SHOW <system> NOCLEAR
//   RETRO SHOW <system> NOCAPTION
//   RETRO <system>
//   RETRO <system> INFO
//   RETRO HELP
//
// examples:
//   RETRO C64
//   RETRO C64 ASCII NOCLEAR
//   RETRO C64 STYLE GREEN
//   RETRO IBMPC NATIVE
//   RETRO IBMPC STYLE MDA
//   RETRO VT100
//   RETRO AMIGA NATIVE
//   RETRO GBC NATIVE
//   RETRO PS2 NATIVE
//   RETRO XBOX NATIVE
//   RETRO C64 INFO
//
// notes:
//   NATIVE uses a system-specific profile and default ANSI style.
//   ASCII uses the system-specific plate without ANSI color.
//   LEGACY uses the older framed catalog plate where available.
//   STYLE overrides the NATIVE default color treatment.
//   NOCLEAR is useful for DotScript logs, tests, and transcript capture.
//   RETRO writes console output only and does not mutate table data.
//
// risk:
//   writes_console: yes
//   mutates_table_data: no
//
// related:
//   ABOUT
//   TVISION
//

#include "shell_commands.hpp"
#include "retro_render.hpp"
#include "retro_screen.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

using std::cout;
using std::string;
using std::vector;

namespace {

string trim(const string& s) {
    const std::size_t first = s.find_first_not_of(" \t\r\n");
    if (first == string::npos) return "";
    const std::size_t last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

string upper_copy(string s) {
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char ch) { return static_cast<char>(std::toupper(ch)); });
    return s;
}

vector<string> split_words(const string& s) {
    std::istringstream iss(s);
    vector<string> out;
    string word;
    while (iss >> word) {
        out.push_back(word);
    }
    return out;
}

string join_words(const vector<string>& words) {
    string out;
    for (const string& word : words) {
        if (!out.empty()) out += ' ';
        out += word;
    }
    return out;
}

string read_tail(std::istringstream& args) {
    string tail;
    std::getline(args, tail);
    return trim(tail);
}

void print_help() {
    cout << "Usage:\n";
    cout << "  RETRO USAGE\n";
    cout << "  RETRO LIST\n";
    cout << "  RETRO LIST LONG\n";
    cout << "  RETRO STYLES\n";
    cout << "  RETRO MODES\n";
    cout << "  RETRO SHOW <system> [NATIVE|ASCII|LEGACY] [STYLE <style>] [CLEAR|NOCLEAR] [CAPTION|NOCAPTION]\n";
    cout << "  RETRO <system> [NATIVE|ASCII|LEGACY] [STYLE <style>] [CLEAR|NOCLEAR] [CAPTION|NOCAPTION]\n";
    cout << "  RETRO <system> INFO\n";
    cout << "  RETRO HELP\n";
    cout << "\nExamples:\n";
    cout << "  RETRO C64\n";
    cout << "  RETRO C64 ASCII NOCLEAR\n";
    cout << "  RETRO IBMPC STYLE MDA\n";
    cout << "  RETRO VT100\n";
    cout << "  RETRO AMIGA NATIVE\n";
    cout << "  RETRO PS2 NATIVE\n";
}

void list_screens(bool long_form) {
    using namespace dottalk::retro;

    cout << "Available retro screens:\n\n";
    const Screen* all = screens();
    const std::size_t count = screen_count();
    for (std::size_t i = 0; i < count; ++i) {
        const Screen& s = all[i];
        cout << "  " << s.id << "  " << s.title;
        if (long_form) {
            cout << "  [" << family_name(s.family) << ", " << s.cols << "x" << s.rows
                 << ", native=" << style_name(s.native_style) << "]";
        }
        cout << "\n";
    }
}

bool consume_render_options(
    const vector<string>& input,
    std::size_t begin,
    vector<string>& system_words,
    dottalk::retro::RenderOptions& options,
    string& error)
{
    using namespace dottalk::retro;

    for (std::size_t i = begin; i < input.size(); ++i) {
        const string u = upper_copy(input[i]);

        if (u == "STYLE") {
            if (i + 1 >= input.size()) {
                error = "RETRO STYLE requires a style name.";
                return false;
            }

            RetroStyle style = RetroStyle::Plain;
            if (!parse_style(input[i + 1], style)) {
                error = "Unknown RETRO style: " + input[i + 1];
                return false;
            }

            options.style = style;
            options.style_set = true;
            ++i;
            continue;
        }

        if (u == "MODE") {
            if (i + 1 >= input.size()) {
                error = "RETRO MODE requires NATIVE, ASCII, or LEGACY.";
                return false;
            }

            RetroMode mode = RetroMode::Native;
            if (!parse_mode(input[i + 1], mode)) {
                error = "Unknown RETRO mode: " + input[i + 1];
                return false;
            }

            options.mode = mode;
            ++i;
            continue;
        }

        RetroMode mode = RetroMode::Native;
        if (parse_mode(input[i], mode)) {
            options.mode = mode;
            continue;
        }

        if (u == "CLEAR") {
            options.clear_first = true;
            continue;
        }
        if (u == "NOCLEAR" || u == "NOCLS") {
            options.clear_first = false;
            continue;
        }
        if (u == "CAPTION") {
            options.caption = true;
            continue;
        }
        if (u == "NOCAPTION") {
            options.caption = false;
            continue;
        }
        if (u == "INFO" || u == "PROFILE") {
            options.info = true;
            options.clear_first = false;
            continue;
        }

        RetroStyle direct = RetroStyle::Plain;
        // Only treat direct style tokens as styles after a system has started.
        // This lets RETRO CGA, RETRO VGA, RETRO MDA, and RETRO VT100 select
        // those screens instead of being consumed as style-only commands.
        if (!system_words.empty() && is_direct_style_token(input[i], direct)) {
            options.style = direct;
            options.style_set = true;
            continue;
        }

        system_words.push_back(input[i]);
    }

    return true;
}

} // namespace

void cmd_RETRO(xbase::DbArea& area, std::istringstream& args) {
    (void)area;

    using namespace dottalk::retro;

    const string tail = read_tail(args);

    if (tail.empty()) {
        print_help();
        return;
    }

    const vector<string> words = split_words(tail);
    if (words.empty()) {
        print_help();
        return;
    }

    const string verb = words[0];
    const string upperVerb = upper_copy(verb);

    if (upperVerb == "USAGE" || upperVerb == "HELP" || upperVerb == "/?" || upperVerb == "?") {
        print_help();
        return;
    }

    if (upperVerb == "STYLES" || upperVerb == "STYLE") {
        print_styles(cout);
        return;
    }

    if (upperVerb == "MODES" || upperVerb == "MODE") {
        print_modes(cout);
        return;
    }

    if (upperVerb == "LIST") {
        bool long_form = false;
        for (std::size_t i = 1; i < words.size(); ++i) {
            const string u = upper_copy(words[i]);
            if (u == "LONG" || u == "DETAIL" || u == "DETAILS") {
                long_form = true;
            } else {
                cout << "Unknown RETRO LIST option: " << words[i] << "\n";
                return;
            }
        }
        list_screens(long_form);
        return;
    }

    RenderOptions options;
    vector<string> system_words;
    string error;

    if (upperVerb == "SHOW") {
        if (!consume_render_options(words, 1, system_words, options, error)) {
            cout << error << "\n";
            return;
        }

        if (system_words.empty()) {
            cout << "RETRO SHOW requires a system name or id.\n";
            return;
        }
    } else {
        if (!consume_render_options(words, 0, system_words, options, error)) {
            cout << error << "\n";
            return;
        }
    }

    const string key = join_words(system_words);
    const Screen* s = find_screen_by_key(key);
    if (!s) {
        cout << "Unknown retro system: " << key << "\n";
        cout << "Use RETRO LIST to see available systems.\n";
        return;
    }

    show_screen(cout, *s, options);
}
