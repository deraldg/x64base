#include "gui_shell_runtime.hpp"

#include "common/path_state.hpp"

#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <mutex>
#include <sstream>
#include <string>
#include <thread>
#include <utility>

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

bool command_token_needs_quoting(const std::filesystem::path& path) {
    const std::string text = path.string();
    return text.find_first_of(" \t\r\n\"'") != std::string::npos;
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
             verb == "exit" ||
             verb == "init" ||
             verb == "shutdown" ||
             verb == "setpath");
}

std::filesystem::path gui_data_root_for_shell() {
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

class ScriptShellRuntime final : public GuiShellRuntime {
public:
    RuntimeCliResult run(const RuntimeCliRequest& request) override {
        return run_runtime_cli_command(request);
    }

    std::string description() const override {
        return "external DotTalk++ script bridge";
    }

    bool persistent() const override {
        return false;
    }
};

#ifdef _WIN32
class PersistentProcessShellRuntime final : public GuiShellRuntime {
public:
    PersistentProcessShellRuntime() = default;

    ~PersistentProcessShellRuntime() override {
        stop_process();
    }

    RuntimeCliResult run(const RuntimeCliRequest& request) override {
        RuntimeCliResult result;
        const std::string command = trim_ascii(request.command);
        if (command.empty()) {
            result.detail = "No shell command text was provided.";
            return result;
        }

        std::lock_guard<std::mutex> run_lock(run_mutex_);
        if (!ensure_started(result)) {
            return fallback_.run(request);
        }

        result.attempted = true;
        result.executable = executable_;

        const std::uint64_t id = ++next_marker_id_;
        const std::string marker = "__DOTTALK_GUI_DONE_" + std::to_string(id) + "__";
        {
            std::lock_guard<std::mutex> lock(output_mutex_);
            output_.clear();
        }

        std::string payload = context_seed_payload(request, command);
        payload += command;
        if (payload.empty() || payload.back() != '\n') {
            payload.push_back('\n');
        }
        payload += "ECHO " + marker + "\n";

        DWORD written = 0;
        if (!WriteFile(stdin_write_, payload.data(), static_cast<DWORD>(payload.size()), &written, nullptr) ||
            written != payload.size()) {
            result.detail = "Unable to write command to persistent DotTalk++ shell.";
            result.ok = false;
            return result;
        }

        std::unique_lock<std::mutex> lock(output_mutex_);
        const bool complete = output_changed_.wait_for(lock, std::chrono::seconds(60), [&] {
            return output_.find(marker) != std::string::npos || process_exited_;
        });

        result.output = output_;
        const auto marker_pos = result.output.find(marker);
        if (marker_pos != std::string::npos) {
            result.output.erase(marker_pos);
            result.ok = true;
            result.exit_code = 0;
            result.output = trim_ascii(result.output);
            return result;
        }

        result.ok = false;
        result.exit_code = process_exited_ ? static_cast<int>(process_exit_code_) : -1;
        result.detail = complete
            ? "Persistent DotTalk++ shell exited before the command marker was observed."
            : "Timed out waiting for the persistent DotTalk++ shell command marker.";
        result.output = trim_ascii(result.output);
        return result;
    }

    std::string description() const override {
        return "persistent DotTalk++ shell bridge";
    }

    bool persistent() const override {
        return true;
    }

private:
    static std::wstring quote_command_line_arg(const std::filesystem::path& path) {
        std::wstring text = path.wstring();
        std::wstring quoted = L"\"";
        for (wchar_t ch : text) {
            if (ch == L'"') {
                quoted += L"\\\"";
            } else {
                quoted += ch;
            }
        }
        quoted += L"\"";
        return quoted;
    }

    bool ensure_started(RuntimeCliResult& result) {
        if (process_info_.hProcess != nullptr) {
            DWORD code = 0;
            if (GetExitCodeProcess(process_info_.hProcess, &code) && code == STILL_ACTIVE) {
                return true;
            }
            stop_process();
        }

        executable_ = find_runtime_cli_executable();
        result.executable = executable_;
        if (executable_.empty()) {
            result.detail =
                "DotTalk++ persistent shell is not available. Set DOTTALKPP_GUI_CLI or DOTTALKPP_EXE to dottalkpp.";
            return false;
        }

        SECURITY_ATTRIBUTES sa {};
        sa.nLength = sizeof(sa);
        sa.bInheritHandle = TRUE;

        HANDLE stdout_read = nullptr;
        HANDLE stdout_write = nullptr;
        HANDLE stdin_read = nullptr;
        HANDLE stdin_write = nullptr;

        if (!CreatePipe(&stdout_read, &stdout_write, &sa, 0)) {
            result.detail = "Unable to create persistent shell stdout pipe.";
            return false;
        }
        if (!SetHandleInformation(stdout_read, HANDLE_FLAG_INHERIT, 0)) {
            CloseHandle(stdout_read);
            CloseHandle(stdout_write);
            result.detail = "Unable to configure persistent shell stdout pipe.";
            return false;
        }
        if (!CreatePipe(&stdin_read, &stdin_write, &sa, 0)) {
            CloseHandle(stdout_read);
            CloseHandle(stdout_write);
            result.detail = "Unable to create persistent shell stdin pipe.";
            return false;
        }
        if (!SetHandleInformation(stdin_write, HANDLE_FLAG_INHERIT, 0)) {
            CloseHandle(stdout_read);
            CloseHandle(stdout_write);
            CloseHandle(stdin_read);
            CloseHandle(stdin_write);
            result.detail = "Unable to configure persistent shell stdin pipe.";
            return false;
        }

        STARTUPINFOW startup {};
        startup.cb = sizeof(startup);
        startup.dwFlags = STARTF_USESTDHANDLES;
        startup.hStdInput = stdin_read;
        startup.hStdOutput = stdout_write;
        startup.hStdError = stdout_write;

        PROCESS_INFORMATION pi {};
        std::wstring command_line = quote_command_line_arg(executable_);
        const std::wstring cwd = executable_.parent_path().wstring();

        BOOL ok = CreateProcessW(
            nullptr,
            command_line.data(),
            nullptr,
            nullptr,
            TRUE,
            CREATE_NO_WINDOW,
            nullptr,
            cwd.empty() ? nullptr : cwd.c_str(),
            &startup,
            &pi);

        CloseHandle(stdin_read);
        CloseHandle(stdout_write);

        if (!ok) {
            CloseHandle(stdout_read);
            CloseHandle(stdin_write);
            result.detail = "Unable to start persistent DotTalk++ shell process.";
            return false;
        }

        stdout_read_ = stdout_read;
        stdin_write_ = stdin_write;
        process_info_ = pi;
        process_exited_ = false;
        process_exit_code_ = 0;
        data_seeded_ = false;
        shell_active_table_path_.clear();
        shell_active_record_number_ = 0;
        reader_ = std::thread([this] { read_loop(); });

        // Drain the startup banner and prompt once. The persistent shell remains
        // alive, so subsequent commands do not repeat INIT/Hello/SHUTDOWN.
        std::this_thread::sleep_for(std::chrono::milliseconds(500));
        {
            std::lock_guard<std::mutex> lock(output_mutex_);
            output_.clear();
        }

        return true;
    }

    std::string context_seed_payload(const RuntimeCliRequest& request, const std::string& command) {
        std::ostringstream out;

        const auto data_root = gui_data_root_for_shell();
        if (!data_seeded_ && !data_root.empty()) {
            if (!command_token_needs_quoting(data_root)) {
                out << "SETPATH DATA " << data_root.string() << "\n";
                data_seeded_ = true;
            } else {
                out << "* GUI persistent bridge skipped DATA path seeding because the path needs shell quoting.\n";
                data_seeded_ = true;
            }
        }

        if (!request.active_table_path.empty() && should_seed_active_table(command)) {
            if (!command_token_needs_quoting(request.active_table_path)) {
                const std::filesystem::path active_path =
                    std::filesystem::absolute(request.active_table_path).lexically_normal();
                if (active_path != shell_active_table_path_) {
                    out << "USE " << active_path.string() << " NOINDEX\n";
                    shell_active_table_path_ = active_path;
                    shell_active_record_number_ = 0;
                }
                if (request.active_record_number > 0 &&
                    request.active_record_number != shell_active_record_number_) {
                    out << "GOTO " << request.active_record_number << "\n";
                    shell_active_record_number_ = request.active_record_number;
                }
            } else {
                out << "* GUI persistent bridge skipped active-table seeding because the path needs shell quoting.\n";
            }
        }

        return out.str();
    }

    void read_loop() {
        char buffer[4096];
        for (;;) {
            DWORD read = 0;
            if (!ReadFile(stdout_read_, buffer, static_cast<DWORD>(sizeof(buffer)), &read, nullptr) || read == 0) {
                DWORD code = 0;
                if (process_info_.hProcess && GetExitCodeProcess(process_info_.hProcess, &code)) {
                    process_exit_code_ = code == STILL_ACTIVE ? 0 : code;
                }
                {
                    std::lock_guard<std::mutex> lock(output_mutex_);
                    process_exited_ = true;
                }
                output_changed_.notify_all();
                return;
            }

            {
                std::lock_guard<std::mutex> lock(output_mutex_);
                output_.append(buffer, buffer + read);
            }
            output_changed_.notify_all();
        }
    }

    void stop_process() {
        if (stdin_write_) {
            const char* exit_line = "EXIT\n";
            DWORD written = 0;
            (void)WriteFile(stdin_write_, exit_line, static_cast<DWORD>(std::strlen(exit_line)), &written, nullptr);
            FlushFileBuffers(stdin_write_);
        }

        if (process_info_.hProcess) {
            const DWORD wait = WaitForSingleObject(process_info_.hProcess, 1500);
            if (wait == WAIT_TIMEOUT) {
                TerminateProcess(process_info_.hProcess, 1);
                WaitForSingleObject(process_info_.hProcess, 500);
            }
        }

        if (reader_.joinable()) {
            reader_.join();
        }
        if (stdin_write_) {
            CloseHandle(stdin_write_);
            stdin_write_ = nullptr;
        }
        if (stdout_read_) {
            CloseHandle(stdout_read_);
            stdout_read_ = nullptr;
        }
        if (process_info_.hThread) {
            CloseHandle(process_info_.hThread);
            process_info_.hThread = nullptr;
        }
        if (process_info_.hProcess) {
            CloseHandle(process_info_.hProcess);
            process_info_.hProcess = nullptr;
        }
        data_seeded_ = false;
        shell_active_table_path_.clear();
        shell_active_record_number_ = 0;
    }

    ScriptShellRuntime fallback_;
    std::mutex run_mutex_;
    std::mutex output_mutex_;
    std::condition_variable output_changed_;
    std::string output_;
    std::filesystem::path executable_;
    std::thread reader_;
    PROCESS_INFORMATION process_info_ {};
    HANDLE stdin_write_ {nullptr};
    HANDLE stdout_read_ {nullptr};
    std::atomic<std::uint64_t> next_marker_id_ {0};
    std::filesystem::path shell_active_table_path_;
    std::uint64_t shell_active_record_number_ {0};
    bool data_seeded_ {false};
    bool process_exited_ {false};
    DWORD process_exit_code_ {0};
};
#endif

} // namespace

std::unique_ptr<GuiShellRuntime> make_script_shell_runtime() {
#ifdef _WIN32
    if (const char* env = std::getenv("DOTTALKPP_GUI_PERSISTENT")) {
        if (std::string(env) == "0" || std::string(env) == "false" || std::string(env) == "FALSE") {
            return std::make_unique<ScriptShellRuntime>();
        }
    }
    return std::make_unique<PersistentProcessShellRuntime>();
#else
    return std::make_unique<ScriptShellRuntime>();
#endif
}

} // namespace dottalk::gui
