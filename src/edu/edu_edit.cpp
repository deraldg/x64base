// src/cli/cmd_edit.cpp
// External editor launcher for DotTalk++
//
// Command surface:
//   EDIT <file>
//
// Runtime settings dependency:
//   cli::Settings::instance().editor.mode
//   cli::Settings::instance().editor.command
//
// Expected settings types in cli/settings.hpp:
//
//   enum class EditorMode {
//       Default,
//       Custom,
//       Off
//   };
//
//   struct EditorSettings {
//       EditorMode mode = EditorMode::Default;
//       std::string command;
//   };
//
//   struct Settings {
//       ...
//       EditorSettings editor;
//       ...
//   };

// @dottalk.usage v1
// owner: EDU|EDIT
// command: EDIT
// category: utility-editor
// status: supported
// noargs: usage
// effect: launch-editor
// mutates: filesystem-through-editor
// usage-access: EDIT USAGE
// summary:
//   Launch the configured external editor for a file path.
//
// usage:
//   EDIT USAGE
//   EDIT <file>
//
// examples:
//   EDIT notes.txt
//   EDIT scripts\demo.dts
//
// notes:
//   EDIT USAGE/HELP/? returns before launching an external editor.
//   EDIT may create or modify files through the configured editor.
//
// risk:
//   launches_external_process: yes except usage
//   mutates_filesystem: through editor
//   mutates_table_data: no
//

#include "xbase.hpp"

#include <cctype>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "cli/output_router.hpp"
#include "cli/settings.hpp"

namespace {

std::string ltrim_copy(const std::string& s) {
    std::size_t i = 0;
    while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) {
        ++i;
    }
    return s.substr(i);
}

std::string rtrim_copy(const std::string& s) {
    if (s.empty()) return s;
    std::size_t i = s.size();
    while (i > 0 && std::isspace(static_cast<unsigned char>(s[i - 1]))) {
        --i;
    }
    return s.substr(0, i);
}

std::string trim_copy(const std::string& s) {
    return rtrim_copy(ltrim_copy(s));
}

std::string strip_outer_quotes(const std::string& s) {
    if (s.size() >= 2) {
        const char a = s.front();
        const char b = s.back();
        if ((a == '"' && b == '"') || (a == '\'' && b == '\'')) {
            return s.substr(1, s.size() - 2);
        }
    }
    return s;
}

std::string shell_quote(const std::string& s) {
#ifdef _WIN32
    // Minimal Windows quoting: wrap in double quotes and escape inner quotes.
    std::string out = "\"";
    for (char c : s) {
        if (c == '"') out += '\\';
        out += c;
    }
    out += "\"";
    return out;
#else
    // POSIX-safe single-quote wrapping.
    std::string out = "'";
    for (char c : s) {
        if (c == '\'') {
            out += "'\\''";
        } else {
            out += c;
        }
    }
    out += "'";
    return out;
#endif
}

bool file_exists(const std::string& path) {
    std::ifstream f(path.c_str(), std::ios::binary);
    return f.good();
}

bool command_exists(const std::string& name) {
#ifdef _WIN32
    // 'where' returns 0 if found.
    const std::string cmd = "where " + shell_quote(name) + " >nul 2>nul";
#else
    // 'command -v' returns 0 if found.
    const std::string cmd = "command -v " + shell_quote(name) + " >/dev/null 2>&1";
#endif
    return std::system(cmd.c_str()) == 0;
}

bool env_nonempty(const char* key, std::string& out) {
    const char* p = std::getenv(key);
    if (!p || !*p) return false;
    out = p;
    return !out.empty();
}

bool running_under_wsl() {
#ifdef _WIN32
    return false;
#else
    std::ifstream f("/proc/sys/kernel/osrelease");
    if (!f) return false;

    std::string line;
    std::getline(f, line);

    for (char& c : line) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }

    return line.find("microsoft") != std::string::npos ||
           line.find("wsl") != std::string::npos;
#endif
}

std::string resolve_default_editor() {
#ifdef _WIN32
    return "notepad.exe";
#else
    std::string value;
    if (env_nonempty("VISUAL", value)) return value;
    if (env_nonempty("EDITOR", value)) return value;

    if (command_exists("nano")) return "nano";
    if (command_exists("vi"))   return "vi";
    if (command_exists("vim"))  return "vim";

    if (running_under_wsl() && command_exists("notepad.exe")) {
        return "notepad.exe";
    }

    return "";
#endif
}

std::string build_launch_command(const std::string& editor_cmd,
                                 const std::string& file_path) {
    // Keep this simple and old-school:
    // - preserve the editor command string exactly as configured
    // - append one safely quoted file argument
    return editor_cmd + " " + shell_quote(file_path);
}

void print_edit_usage(std::ostream& out) {
    out << "Usage:\n";
    out << "  EDIT USAGE\n";
    out << "  EDIT <file>\n";
    out << "Examples:\n";
    out << "  EDIT notes.txt\n";
    out << "  EDIT scripts\\demo.dts\n";
    out << "Notes:\n";
    out << "  - EDIT USAGE does not launch an editor.\n";
}

} // namespace

void cmd_EDIT(xbase::DbArea&, std::istringstream& args) {
    auto& out = cli::OutputRouter::instance().out();
    auto& S   = cli::Settings::instance();

    std::string raw;
    std::getline(args, raw);
    raw = trim_copy(raw);

    // EDIT_USAGE_CONTRACT_BRANCH
    {
        std::string u = raw;
        for (char& ch : u) {
            ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
        }
        if (u == "USAGE" || u == "HELP" || u == "?") {
            print_edit_usage(out);
            return;
        }
    }
    if (raw.empty()) {
        print_edit_usage(out);
        return;
    }

    const std::string file_arg = strip_outer_quotes(raw);
    if (file_arg.empty()) {
        print_edit_usage(out);
        return;
    }

    // Explicit OFF means no launch.
    if (S.editor.mode == cli::EditorMode::Off) {
        out << "EDIT: external editor is OFF\n";
        return;
    }

    std::string editor_cmd;

    if (S.editor.mode == cli::EditorMode::Custom) {
        editor_cmd = trim_copy(S.editor.command);
        if (editor_cmd.empty()) {
            out << "EDIT: custom editor is empty\n";
            return;
        }
    } else {
        editor_cmd = resolve_default_editor();
        if (editor_cmd.empty()) {
            out << "EDIT: no editor configured and no default editor found\n";
            return;
        }
    }

    // For text/script editing, allow opening a non-existent file.
    // We only report that it does not exist; we do not block launch.
    if (!file_exists(file_arg)) {
        out << "EDIT: file does not exist yet, editor may create it: "
            << file_arg << "\n";
    }

    const std::string launch_cmd = build_launch_command(editor_cmd, file_arg);
    const int rc = std::system(launch_cmd.c_str());

    if (rc != 0) {
        out << "EDIT: unable to launch editor\n";
        return;
    }
}