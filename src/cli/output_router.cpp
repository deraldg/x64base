#include "cli/output_router.hpp"
#include "cli/settings.hpp"

#include <algorithm>
#include <fstream>
#include <iostream>
#include <mutex>
#include <ostream>
#include <streambuf>
#include <string>
#include <vector>

#ifdef _WIN32
#include <conio.h>
#include <windows.h>
#else
#include <sys/ioctl.h>
#include <termios.h>
#include <unistd.h>
#endif

namespace cli {
namespace {

enum class PagerAction {
    Continue,
    All,
    Quit
};

static bool console_is_interactive()
{
#ifdef _WIN32
    DWORD in_mode = 0;
    DWORD out_mode = 0;
    HANDLE hIn  = GetStdHandle(STD_INPUT_HANDLE);
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hIn == INVALID_HANDLE_VALUE || hOut == INVALID_HANDLE_VALUE) return false;
    if (!GetConsoleMode(hIn, &in_mode)) return false;
    if (!GetConsoleMode(hOut, &out_mode)) return false;
    return true;
#else
    return ::isatty(STDIN_FILENO) && ::isatty(STDOUT_FILENO);
#endif
}

static int visible_console_rows()
{
#ifdef _WIN32
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut == INVALID_HANDLE_VALUE) return 24;

    CONSOLE_SCREEN_BUFFER_INFO csbi{};
    if (!GetConsoleScreenBufferInfo(hOut, &csbi)) return 24;

    const int rows = static_cast<int>(csbi.srWindow.Bottom - csbi.srWindow.Top + 1);
    return (rows > 0) ? rows : 24;
#else
    struct winsize ws{};
    if (::ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_row > 0) {
        return static_cast<int>(ws.ws_row);
    }
    return 24;
#endif
}

static int visible_console_cols()
{
#ifdef _WIN32
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut == INVALID_HANDLE_VALUE) return 80;

    CONSOLE_SCREEN_BUFFER_INFO csbi{};
    if (!GetConsoleScreenBufferInfo(hOut, &csbi)) return 80;

    const int cols = static_cast<int>(csbi.srWindow.Right - csbi.srWindow.Left + 1);
    return (cols > 0) ? cols : 80;
#else
    struct winsize ws{};
    if (::ioctl(STDOUT_FILENO, TIOCGWINSZ, &ws) == 0 && ws.ws_col > 0) {
        return static_cast<int>(ws.ws_col);
    }
    return 80;
#endif
}

static PagerAction read_pager_action()
{
#ifdef _WIN32
    for (;;) {
        const int ch = _getch();

        if (ch == '\r' || ch == '\n') return PagerAction::Continue;

        if (ch == 0 || ch == 224) {
            (void)_getch();
            continue;
        }

        if (ch == 'a' || ch == 'A') return PagerAction::All;
        if (ch == 'q' || ch == 'Q' || ch == 27) return PagerAction::Quit;

        return PagerAction::Continue;
    }
#else
    termios oldt{};
    if (::tcgetattr(STDIN_FILENO, &oldt) != 0) return PagerAction::Continue;

    termios raw = oldt;
    raw.c_lflag &= static_cast<unsigned>(~(ICANON | ECHO));
    raw.c_cc[VMIN]  = 1;
    raw.c_cc[VTIME] = 0;

    if (::tcsetattr(STDIN_FILENO, TCSANOW, &raw) != 0) return PagerAction::Continue;

    unsigned char ch = 0;
    const ssize_t n = ::read(STDIN_FILENO, &ch, 1);
    (void)::tcsetattr(STDIN_FILENO, TCSANOW, &oldt);

    if (n <= 0) return PagerAction::Continue;
    if (ch == '\r' || ch == '\n') return PagerAction::Continue;
    if (ch == 'a' || ch == 'A') return PagerAction::All;
    if (ch == 'q' || ch == 'Q' || ch == 27) return PagerAction::Quit;

    return PagerAction::Continue;
#endif
}

static std::string trim_copy(std::string s)
{
    const auto not_space = [](unsigned char ch) { return std::isspace(ch) == 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(), not_space));
    s.erase(std::find_if(s.rbegin(), s.rend(), not_space).base(), s.end());
    return s;
}

} // anonymous namespace

struct OutputRouter::Impl {
    bool console_on   = true;
    bool alternate_on = false;
    bool talk_on      = false;
    bool echo_on      = false;

    OutputDest dest = OutputDest::Console;

    bool paging_on_global          = false;
    bool paging_this_command       = false;
    bool paging_all_this_command   = false;
    bool paging_abort_this_command = false;
    bool shell_input_interactive   = false;
    int  lines_on_page             = 0;
    int  page_len                  = 22;

    bool wrap_on_console = true;
    int  console_cols    = 80;
    int  col_on_line     = 0;

    std::string   prn_file_path;
    std::ofstream prn_file;

    std::string printer_name;
    bool use_default_printer = true;
    std::string printer_spool_buffer;

    std::string   alt_path;
    std::ofstream alt_file;

    std::streambuf* console_buf = nullptr;
    std::vector<std::streambuf*> cout_redirect_stack;

    struct NullBuf : public std::streambuf {
        int overflow(int ch) override { return ch != EOF ? ch : EOF; }
        std::streamsize xsputn(const char*, std::streamsize n) override { return n; }
    };

    NullBuf      null_buf;
    std::ostream null_stream{&null_buf};

    std::mutex mtx;

    bool should_page_console_locked() const {
        return console_on
            && dest == OutputDest::Console
            && paging_on_global
            && paging_this_command
            && shell_input_interactive
            && !paging_all_this_command
            && !paging_abort_this_command;
    }

    void recompute_page_metrics_locked() {
        const int rows = visible_console_rows();
        page_len = std::max(3, rows - 2);
        console_cols = std::max(1, visible_console_cols());
    }

    void write_direct_console_locked(const char* s, std::streamsize n) {
        if (!console_buf || !s || n <= 0) return;
        console_buf->sputn(s, n);
        console_buf->pubsync();
    }

    void write_direct_console_char_locked(char c) {
        if (!console_buf) return;
        console_buf->sputc(c);
        if (c == '\n') console_buf->pubsync();
    }

    void clear_more_prompt_locked() {
        static constexpr const char* wipe =
            "\r                                                                                \r";
        write_direct_console_locked(
            wipe,
            static_cast<std::streamsize>(std::char_traits<char>::length(wipe))
        );
    }

    void prompt_more_locked() {
        static constexpr const char* prompt =
            "-- More -- (Enter=Continue, A=All, Q=Quit)";
        write_direct_console_locked(
            prompt,
            static_cast<std::streamsize>(std::char_traits<char>::length(prompt))
        );

        switch (read_pager_action()) {
        case PagerAction::Continue:
            break;
        case PagerAction::All:
            paging_all_this_command = true;
            break;
        case PagerAction::Quit:
            paging_abort_this_command = true;
            break;
        }

        clear_more_prompt_locked();
        lines_on_page = 0;
        recompute_page_metrics_locked();
    }

    void note_newline_and_maybe_pause_locked() {
        if (!should_page_console_locked()) return;
        ++lines_on_page;
        if (lines_on_page >= page_len) {
            prompt_more_locked();
        }
    }

    void write_console_locked(const char* s, std::streamsize n) {
        if (!console_on || !s || n <= 0) return;
        if (paging_abort_this_command) return;

        if (!should_page_console_locked() && wrap_on_console) {
            write_direct_console_locked(s, n);
            return;
        }

        for (std::streamsize i = 0; i < n; ++i) {
            if (paging_abort_this_command) break;

            const char c = s[i];

            if (c == '\n') {
                write_direct_console_char_locked(c);
                col_on_line = 0;
                note_newline_and_maybe_pause_locked();
                continue;
            }

            if (!wrap_on_console) {
                if (col_on_line < console_cols) {
                    write_direct_console_char_locked(c);
                }
                ++col_on_line;
                continue;
            }

            write_direct_console_char_locked(c);
            ++col_on_line;
        }
    }

    struct MultiBuf : public std::streambuf {
        Impl* impl;

        explicit MultiBuf(Impl* p) : impl(p) {}

        int overflow(int ch) override {
            if (ch == traits_type::eof()) return traits_type::not_eof(ch);
            const char c = static_cast<char>(ch);

            std::lock_guard<std::mutex> guard(impl->mtx);

            if (impl->paging_abort_this_command) {
                return ch;
            }

            switch (impl->dest) {
            case OutputDest::Console:
                impl->write_console_locked(&c, 1);
                break;
            case OutputDest::File:
                if (impl->prn_file.is_open()) {
                    impl->prn_file.put(c);
                    if (c == '\n') impl->prn_file.flush();
                }
                break;
            case OutputDest::Printer:
                impl->printer_spool_buffer.push_back(c);
                break;
            case OutputDest::Null:
                break;
            }

            if (impl->alternate_on && impl->alt_file.is_open()) {
                impl->alt_file.put(c);
                if (c == '\n') impl->alt_file.flush();
            }

            return ch;
        }

        std::streamsize xsputn(const char* s, std::streamsize n) override {
            if (!s || n <= 0) return 0;

            std::lock_guard<std::mutex> guard(impl->mtx);

            if (impl->paging_abort_this_command) {
                return n;
            }

            switch (impl->dest) {
            case OutputDest::Console:
                impl->write_console_locked(s, n);
                break;
            case OutputDest::File:
                if (impl->prn_file.is_open()) {
                    impl->prn_file.write(s, n);
                    impl->prn_file.flush();
                }
                break;
            case OutputDest::Printer:
                impl->printer_spool_buffer.append(s, static_cast<std::size_t>(n));
                break;
            case OutputDest::Null:
                break;
            }

            if (impl->alternate_on && impl->alt_file.is_open()) {
                impl->alt_file.write(s, n);
                impl->alt_file.flush();
            }

            return n;
        }
    };

    MultiBuf     multi_buf{this};
    std::ostream routed_stream{&multi_buf};

    Impl() : console_buf(std::cout.rdbuf()) {}
};

OutputRouter& OutputRouter::instance() {
    // Process-lifetime singleton: avoid late static destruction ordering
    // problems during shutdown when std::cout / console state is already
    // partially torn down.
    static OutputRouter* global = new OutputRouter();
    return *global;
}

OutputRouter::OutputRouter() : impl_(std::make_unique<Impl>()) {}
OutputRouter::~OutputRouter() = default;

std::ostream& OutputRouter::out() {
    return impl_->routed_stream;
}

void OutputRouter::console_note(const std::string& line) {
    std::lock_guard<std::mutex> guard(impl_->mtx);
    impl_->write_direct_console_locked(
        line.c_str(),
        static_cast<std::streamsize>(line.size())
    );
    impl_->write_direct_console_locked("\n", 1);
}

void OutputRouter::talk_line(const std::string& line) {
    std::lock_guard<std::mutex> guard(impl_->mtx);
    if (!cli::Settings::instance().talk_on.load()) return;

    switch (impl_->dest) {
    case OutputDest::Console:
        impl_->write_console_locked(
            line.c_str(),
            static_cast<std::streamsize>(line.size())
        );
        impl_->write_console_locked("\n", 1);
        break;
    case OutputDest::File:
        if (impl_->prn_file.is_open()) {
            impl_->prn_file << line << '\n';
            impl_->prn_file.flush();
        }
        break;
    case OutputDest::Printer:
        impl_->printer_spool_buffer += line;
        impl_->printer_spool_buffer.push_back('\n');
        break;
    case OutputDest::Null:
        break;
    }
}

void OutputRouter::set_echo(bool on)      { std::lock_guard<std::mutex> lk(impl_->mtx); impl_->echo_on = on; }
void OutputRouter::set_alternate(bool on) { std::lock_guard<std::mutex> lk(impl_->mtx); impl_->alternate_on = on; }
void OutputRouter::set_talk(bool on)
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->talk_on = on;
    cli::Settings::instance().talk_on.store(on);
}
void OutputRouter::set_paging(bool on)    { std::lock_guard<std::mutex> lk(impl_->mtx); impl_->paging_on_global = on; }
void OutputRouter::set_wrap(bool on)      { std::lock_guard<std::mutex> lk(impl_->mtx); impl_->wrap_on_console = on; }

void OutputRouter::set_console(bool on)
{
    cli::Settings::instance().console_on.store(on);
    if (on) {
        set_dest_console();
    } else {
        std::lock_guard<std::mutex> lk(impl_->mtx);
        if (impl_->dest == OutputDest::Console) impl_->dest = OutputDest::Null;
        impl_->console_on = on;
        cli::Settings::instance().device_target = "NULL";
    }
}

void OutputRouter::set_print(bool on)
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    cli::Settings::instance().print_on.store(on);
    if (on) {
        if (!impl_->prn_file_path.empty() && impl_->prn_file.is_open()) {
            impl_->dest = OutputDest::File;
            cli::Settings::instance().device_target = "FILE";
        }
    } else if (impl_->dest == OutputDest::File) {
        impl_->dest = OutputDest::Null;
        cli::Settings::instance().device_target = "NULL";
    }
}

bool OutputRouter::console_on() const   { std::lock_guard<std::mutex> lk(impl_->mtx); return impl_->dest == OutputDest::Console && impl_->console_on; }
bool OutputRouter::print_on() const     { std::lock_guard<std::mutex> lk(impl_->mtx); return impl_->dest == OutputDest::File; }
bool OutputRouter::alternate_on() const { std::lock_guard<std::mutex> lk(impl_->mtx); return impl_->alternate_on; }
bool OutputRouter::talk_on() const      { return cli::Settings::instance().talk_on.load(); }
bool OutputRouter::echo_on() const      { std::lock_guard<std::mutex> lk(impl_->mtx); return impl_->echo_on; }
bool OutputRouter::paging_on() const    { std::lock_guard<std::mutex> lk(impl_->mtx); return impl_->paging_on_global; }
bool OutputRouter::wrap_on() const      { std::lock_guard<std::mutex> lk(impl_->mtx); return impl_->wrap_on_console; }

void OutputRouter::begin_shell_command(bool interactive_input) {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->shell_input_interactive   = interactive_input && console_is_interactive();
    impl_->paging_this_command       = impl_->paging_on_global && impl_->shell_input_interactive;
    impl_->paging_all_this_command   = false;
    impl_->paging_abort_this_command = false;
    impl_->lines_on_page             = 0;
    impl_->col_on_line               = 0;
    impl_->recompute_page_metrics_locked();

    if (impl_->dest == OutputDest::Printer) {
        impl_->printer_spool_buffer.clear();
    }
}

void OutputRouter::end_shell_command() {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    // Intentional for shakedown phase:
    // PRINTER mode only stages output in memory.
    // No OS handoff is attempted here.
    impl_->paging_this_command       = false;
    impl_->paging_all_this_command   = false;
    impl_->paging_abort_this_command = false;
    impl_->shell_input_interactive   = false;
    impl_->lines_on_page             = 0;
    impl_->col_on_line               = 0;
}

void OutputRouter::push_cout_redirect() {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->cout_redirect_stack.push_back(std::cout.rdbuf());
    std::cout.rdbuf(impl_->routed_stream.rdbuf());
}

void OutputRouter::pop_cout_redirect() {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    if (impl_->cout_redirect_stack.empty()) return;
    std::streambuf* prev = impl_->cout_redirect_stack.back();
    impl_->cout_redirect_stack.pop_back();
    std::cout.rdbuf(prev);
}

bool OutputRouter::command_aborted() const {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->paging_abort_this_command;
}

void OutputRouter::set_dest_console()
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->dest = OutputDest::Console;
    impl_->console_on = true;
    cli::Settings::instance().console_on.store(true);
    cli::Settings::instance().print_on.store(false);
    cli::Settings::instance().device_target = "SCREEN";
    cli::Settings::instance().printer_target.clear();
}

bool OutputRouter::set_dest_file(const std::string& path)
{
    std::lock_guard<std::mutex> lk(impl_->mtx);

    impl_->prn_file.close();
    impl_->prn_file_path.clear();

    const std::string trimmed = trim_copy(path);
    if (trimmed.empty()) return false;

    impl_->prn_file.open(trimmed, std::ios::out | std::ios::app | std::ios::binary);
    if (!impl_->prn_file.is_open()) return false;

    impl_->prn_file_path = trimmed;
    impl_->dest = OutputDest::File;
    cli::Settings::instance().console_on.store(false);
    cli::Settings::instance().print_on.store(true);
    cli::Settings::instance().device_target = "FILE";
    cli::Settings::instance().printer_target.clear();
    return true;
}

bool OutputRouter::set_dest_printer(const std::string& printer_name)
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->printer_name = trim_copy(printer_name);
    impl_->use_default_printer = impl_->printer_name.empty();
    impl_->printer_spool_buffer.clear();
    impl_->dest = OutputDest::Printer;
    cli::Settings::instance().console_on.store(false);
    cli::Settings::instance().print_on.store(false);
    cli::Settings::instance().device_target = "PRINTER";
    cli::Settings::instance().printer_target = impl_->printer_name;
    return true;
}

void OutputRouter::set_dest_null()
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->dest = OutputDest::Null;
    cli::Settings::instance().console_on.store(false);
    cli::Settings::instance().print_on.store(false);
    cli::Settings::instance().device_target = "NULL";
    cli::Settings::instance().printer_target.clear();
}

OutputDest OutputRouter::dest() const
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->dest;
}

std::string OutputRouter::describe_dest() const
{
    std::lock_guard<std::mutex> lk(impl_->mtx);

    switch (impl_->dest) {
    case OutputDest::Console:
        return "CONSOLE";
    case OutputDest::File:
        return impl_->prn_file_path.empty()
            ? std::string("FILE")
            : std::string("FILE -> ") + impl_->prn_file_path;
    case OutputDest::Printer:
        return impl_->use_default_printer || impl_->printer_name.empty()
            ? "PRINTER -> (system default) [staged only]"
            : std::string("PRINTER -> ") + impl_->printer_name + " [staged only]";
    case OutputDest::Null:
        return "NULL";
    }

    return "UNKNOWN";
}

bool OutputRouter::set_print_to(const std::string& path) {
    return set_dest_file(path);
}

void OutputRouter::close_print_to() {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->prn_file.close();
    impl_->prn_file_path.clear();
    if (impl_->dest == OutputDest::File) impl_->dest = OutputDest::Null;
}

bool OutputRouter::set_alternate_to(const std::string& path) {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->alt_file.close();
    impl_->alt_path.clear();

    const std::string trimmed = trim_copy(path);
    if (trimmed.empty()) return false;

    impl_->alt_file.open(trimmed, std::ios::out | std::ios::app | std::ios::binary);
    if (!impl_->alt_file.is_open()) return false;

    impl_->alt_path = trimmed;
    impl_->alternate_on = true;
    return true;
}

void OutputRouter::close_alternate_to() {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    impl_->alt_file.close();
    impl_->alt_path.clear();
    impl_->alternate_on = false;
}

std::string OutputRouter::print_to_path() const {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->prn_file_path;
}

std::string OutputRouter::alternate_to_path() const {
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->alt_path;
}

std::string OutputRouter::prn_file_path() const
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->prn_file_path;
}

std::string OutputRouter::prn_printer_name() const
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->printer_name;
}

bool OutputRouter::prn_uses_default_printer() const
{
    std::lock_guard<std::mutex> lk(impl_->mtx);
    return impl_->use_default_printer;
}

} // namespace cli
