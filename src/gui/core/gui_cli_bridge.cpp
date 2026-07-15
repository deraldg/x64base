#include "gui_cli_bridge.hpp"

#include "common/path_state.hpp"

#include <array>
#include <chrono>
#include <cstdlib>
#include <cstdio>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>

#ifdef _WIN32
#include <windows.h>
#endif

namespace dottalk::gui {

namespace {

std::string trim_ascii(std::string value) {
    auto is_space = [](unsigned char ch) {
        return ch == ' ' || ch == '\t' || ch == '\r' || ch == '\n';
    };
    while (!value.empty() && is_space(static_cast<unsigned char>(value.front()))) {
        value.erase(value.begin());
    }
    while (!value.empty() && is_space(static_cast<unsigned char>(value.back()))) {
        value.pop_back();
    }
    return value;
}

std::string quote_command_arg(const std::filesystem::path& path) {
    std::string text = path.string();
#ifdef _WIN32
    std::string quoted = "\"";
    for (char ch : text) {
        if (ch == '"') {
            quoted += "\\\"";
        } else {
            quoted += ch;
        }
    }
    quoted += "\"";
    return quoted;
#else
    std::string quoted = "'";
    for (char ch : text) {
        if (ch == '\'') {
            quoted += "'\\''";
        } else {
            quoted += ch;
        }
    }
    quoted += "'";
    return quoted;
#endif
}

std::string build_script_command(const std::filesystem::path& exe, const std::filesystem::path& script) {
    std::string command = quote_command_arg(exe) + " --script " + quote_command_arg(script) + " 2>&1";
#ifdef _WIN32
    // _popen routes through cmd.exe. When the program path is the first quoted
    // token, cmd.exe needs the whole command wrapped or it can drop arguments.
    command = "\"" + command + "\"";
#endif
    return command;
}

bool script_token_needs_quoting(const std::filesystem::path& path) {
    const std::string text = path.string();
    return text.find_first_of(" \t\r\n\"'") != std::string::npos;
}

std::filesystem::path module_path() {
#ifdef _WIN32
    std::wstring buffer(32768, L'\0');
    const DWORD len = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (len == 0 || len >= buffer.size()) {
        return {};
    }
    buffer.resize(len);
    return std::filesystem::path(buffer);
#else
    return {};
#endif
}

void add_if_regular(std::vector<std::filesystem::path>& out, const std::filesystem::path& path) {
    if (path.empty()) {
        return;
    }
    try {
        if (std::filesystem::exists(path) && std::filesystem::is_regular_file(path)) {
            out.push_back(std::filesystem::absolute(path));
        }
    } catch (...) {
    }
}

std::filesystem::path executable_name() {
#ifdef _WIN32
    return "dottalkpp.exe";
#else
    return "dottalkpp";
#endif
}

std::filesystem::path find_dottalkpp_executable() {
    std::vector<std::filesystem::path> candidates;
    const auto exe_name = executable_name();

    if (const char* env = std::getenv("DOTTALKPP_GUI_CLI")) {
        add_if_regular(candidates, std::filesystem::path(env));
    }
    if (const char* env = std::getenv("DOTTALKPP_EXE")) {
        add_if_regular(candidates, std::filesystem::path(env));
    }

    const auto mod = module_path();
    if (!mod.empty()) {
        std::filesystem::path dir = mod.parent_path();
        for (int depth = 0; depth < 8 && !dir.empty(); ++depth) {
            add_if_regular(candidates, dir / exe_name);
            add_if_regular(candidates, dir / "Release" / exe_name);
            add_if_regular(candidates, dir / "Debug" / exe_name);
            add_if_regular(candidates, dir / "RelWithDebInfo" / exe_name);
            const auto parent = dir.parent_path();
            if (parent == dir) {
                break;
            }
            dir = parent;
        }
    }

#ifdef DOTTALK_GUI_BINARY_DIR
    const std::filesystem::path binary_root(DOTTALK_GUI_BINARY_DIR);
    add_if_regular(candidates, binary_root / "src" / "Release" / exe_name);
    add_if_regular(candidates, binary_root / "src" / "Debug" / exe_name);
    add_if_regular(candidates, binary_root / "src" / "RelWithDebInfo" / exe_name);
    add_if_regular(candidates, binary_root / exe_name);
#endif

#ifdef DOTTALK_GUI_SOURCE_ROOT
    const std::filesystem::path source_root(DOTTALK_GUI_SOURCE_ROOT);
    add_if_regular(candidates, source_root / "build" / "src" / "Release" / exe_name);
    add_if_regular(candidates, source_root / "build-msvc" / "src" / "Release" / exe_name);
    add_if_regular(candidates, source_root / "build-wx-fixed-local" / "src" / "Release" / exe_name);
#endif

    if (!candidates.empty()) {
        return candidates.front();
    }
    return {};
}

std::filesystem::path temp_script_path() {
    const auto stamp = std::chrono::steady_clock::now().time_since_epoch().count();
    std::ostringstream name;
    name << "dottalk_gui_cli_"
         << stamp << "_"
         << std::hash<std::thread::id>{}(std::this_thread::get_id())
         << ".dts";
    return std::filesystem::temp_directory_path() / name.str();
}

std::string first_token_lower(const std::string& text) {
    std::istringstream stream(text);
    std::string token;
    stream >> token;
    for (char& ch : token) {
        if (ch >= 'A' && ch <= 'Z') {
            ch = static_cast<char>(ch - 'A' + 'a');
        }
    }
    return token;
}

bool should_seed_active_table(const std::string& command) {
    const std::string verb = first_token_lower(command);
    return !(verb.empty() ||
             verb == "help" ||
             verb == "?" ||
             verb == "about" ||
             verb == "do" ||
             verb == "dotscript" ||
             verb == "workspace" ||
             verb == "use" ||
             verb == "close" ||
             verb == "quit" ||
             verb == "exit");
}

void emit_active_index_seed(std::ofstream& out, const RuntimeCliRequest& request) {
    if (request.active_index_container.empty()) {
        out << "SET ORDER TO 0\n";
        return;
    }

    if (script_token_needs_quoting(request.active_index_container)) {
        out << "* GUI CLI bridge skipped active-index seeding because the path needs shell quoting.\n";
        return;
    }

    out << "SET INDEX TO " << request.active_index_container.string() << "\n";
    const std::string tag = trim_ascii(request.active_index_tag);
    if (!tag.empty()) {
        out << "SET ORDER TO " << tag << "\n";
    }
    out << (request.active_index_ascending ? "ASCEND\n" : "DESCEND\n");
}

std::filesystem::path gui_data_root_for_cli() {
    const auto data = dottalk::paths::get_slot(dottalk::paths::Slot::DATA);
    if (!data.empty()) {
        return data;
    }
    if (const char* env = std::getenv("DOTTALKPP_DATA")) {
        return std::filesystem::path(env);
    }
    if (const char* env = std::getenv("DOTTALK_DATA")) {
        return std::filesystem::path(env);
    }
    return {};
}

std::string read_pipe_output(const std::string& command, int& exit_code) {
    std::array<char, 4096> buffer {};
#ifdef _WIN32
    FILE* pipe = _popen(command.c_str(), "r");
#else
    FILE* pipe = popen(command.c_str(), "r");
#endif
    if (!pipe) {
        exit_code = -1;
        return {};
    }

    std::string output;
    while (fgets(buffer.data(), static_cast<int>(buffer.size()), pipe) != nullptr) {
        output += buffer.data();
    }

#ifdef _WIN32
    exit_code = _pclose(pipe);
#else
    exit_code = pclose(pipe);
#endif
    return output;
}

} // namespace

RuntimeCliResult run_runtime_cli_command(const RuntimeCliRequest& request) {
    RuntimeCliResult result;
    const std::string command = trim_ascii(request.command);
    if (command.empty()) {
        result.detail = "No CLI command text was provided.";
        return result;
    }
    const auto exe = find_dottalkpp_executable();
    if (exe.empty()) {
        result.detail =
            "DotTalk++ CLI bridge is not available. Set DOTTALKPP_GUI_CLI or DOTTALKPP_EXE to dottalkpp.";
        return result;
    }

    const auto script = temp_script_path();
    {
        std::ofstream out(script, std::ios::binary);
        if (!out.is_open()) {
            result.detail = "Unable to create a temporary DotTalk++ script.";
            return result;
        }

        const auto data_root = gui_data_root_for_cli();
        if (!data_root.empty()) {
            if (!script_token_needs_quoting(data_root)) {
                out << "SETPATH DATA " << data_root.string() << "\n";
            } else {
                out << "* GUI CLI bridge skipped DATA path seeding because the path needs shell quoting.\n";
            }
        }
        if (!request.active_table_path.empty() && should_seed_active_table(command)) {
            if (!script_token_needs_quoting(request.active_table_path)) {
                out << "USE " << request.active_table_path.string() << " NOINDEX\n";
                emit_active_index_seed(out, request);
                if (request.active_record_number > 0) {
                    out << "GOTO " << request.active_record_number << "\n";
                }
            } else {
                out << "* GUI CLI bridge skipped active-table seeding because the path needs shell quoting.\n";
            }
        }
        out << command << "\n";
    }

    result.attempted = true;
    result.executable = exe;
    const std::string shell_command = build_script_command(exe, script);

    result.output = read_pipe_output(shell_command, result.exit_code);
    result.ok = result.exit_code == 0;

    std::error_code ignored;
    std::filesystem::remove(script, ignored);

    if (result.output.empty() && !result.ok) {
        result.detail = "DotTalk++ CLI command did not produce output.";
    }
    return result;
}

std::filesystem::path find_runtime_cli_executable() {
    return find_dottalkpp_executable();
}

} // namespace dottalk::gui
