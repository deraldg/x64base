// ==============================
// File: src/main.cpp
// ==============================

#include <exception>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

#include "runtime/utf8_init.hpp"

#ifdef _WIN32
#include <windows.h>
#endif

int run_shell(); // implemented elsewhere

namespace {

struct CinRedirectGuard {
    std::streambuf* saved = nullptr;

    CinRedirectGuard() = default;
    CinRedirectGuard(const CinRedirectGuard&) = delete;
    CinRedirectGuard& operator=(const CinRedirectGuard&) = delete;

    void redirect(std::istream& in, std::streambuf* replacement) {
        restore(in);
        if (replacement) {
            saved = in.rdbuf(replacement);
        }
    }

    void restore(std::istream& in) {
        if (saved) {
            in.rdbuf(saved);
            saved = nullptr;
        }
    }

    ~CinRedirectGuard() {
        restore(std::cin);
    }
};

static void print_usage(const char* exe) {
    std::cerr
        << "Usage:\n"
        << "  " << exe << "                 (interactive)\n"
        << "  " << exe << " --script <file>  (feed file to stdin; prompts may still print)\n"
        << "  " << exe << " --help\n"
        << "\n"
        << "Also supported:\n"
        << "  " << exe << " < file.dts\n";
}

#ifdef _WIN32

static void warn_if_vt_input_enabled(const char* where) {
#ifndef NDEBUG
    DWORD mode = 0;
    HANDLE hIn = GetStdHandle(STD_INPUT_HANDLE);
    if (hIn != INVALID_HANDLE_VALUE &&
        GetConsoleMode(hIn, &mode) &&
        (mode & ENABLE_VIRTUAL_TERMINAL_INPUT)) {
        std::cerr
            << "[DotTalk++ WARN] VT INPUT ENABLED at " << where
            << " - Foxtalk/CLI key handling will break.\n";
    }
#else
    (void)where;
#endif
}

static void dbg_print_console_state(const char* where) {
#ifndef NDEBUG
    std::cerr << "[DBG] " << where;

    const UINT inCp  = GetConsoleCP();
    const UINT outCp = GetConsoleOutputCP();
    std::cerr << " IN_CP=" << inCp << " OUT_CP=" << outCp;

    DWORD outMode = 0;
    HANDLE hOut = GetStdHandle(STD_OUTPUT_HANDLE);
    if (hOut != INVALID_HANDLE_VALUE && GetConsoleMode(hOut, &outMode)) {
        std::cerr << " VT_OUT="
                  << ((outMode & ENABLE_VIRTUAL_TERMINAL_PROCESSING) ? "ON" : "OFF");
    } else {
        std::cerr << " VT_OUT=(n/a)";
    }

    DWORD inMode = 0;
    HANDLE hIn = GetStdHandle(STD_INPUT_HANDLE);
    if (hIn != INVALID_HANDLE_VALUE && GetConsoleMode(hIn, &inMode)) {
        std::cerr << " VT_IN="
                  << ((inMode & ENABLE_VIRTUAL_TERMINAL_INPUT) ? "ON" : "OFF");
    } else {
        std::cerr << " VT_IN=(n/a)";
    }

    std::cerr << "\n";
#else
    (void)where;
#endif
}

static void warn_if_not_utf8_console(const char* where) {
#ifndef NDEBUG
    const UINT inCp  = GetConsoleCP();
    const UINT outCp = GetConsoleOutputCP();

    if (inCp != CP_UTF8 || outCp != CP_UTF8) {
        std::cerr
            << "[DotTalk++ WARN] Console not fully UTF-8 at " << where
            << " (IN_CP=" << inCp << ", OUT_CP=" << outCp << ").\n";
    }
#else
    (void)where;
#endif
}

#else

static void warn_if_vt_input_enabled(const char* where) {
    (void)where;
}

static void dbg_print_console_state(const char* where) {
    (void)where;
}

static void warn_if_not_utf8_console(const char* where) {
    (void)where;
}

#endif

static int run_with_optional_script(int argc, char** argv) {
    std::ifstream script;
    CinRedirectGuard cin_guard;

    if (argc >= 2) {
        const std::string a1 = argv[1];

        if (a1 == "--help" || a1 == "-h" || a1 == "/?") {
            print_usage(argv[0]);
            return 0;
        }

        if (a1 == "--script") {
            if (argc < 3) {
                std::cerr << "Error: --script requires a file path.\n";
                print_usage(argv[0]);
                return 2;
            }

            const std::string path = argv[2];
            script.open(path, std::ios::in);
            if (!script.is_open()) {
                std::cerr << "Error: cannot open script: " << path << "\n";
                return 2;
            }

            cin_guard.redirect(std::cin, script.rdbuf());
        } else {
            std::cerr << "Error: unknown option: " << a1 << "\n";
            print_usage(argv[0]);
            return 2;
        }
    }

    return run_shell();
}

} // namespace

int main(int argc, char** argv) {
    try {
        // Must happen before any real console output.
        dottalk::init_utf8();

        dbg_print_console_state("after init_utf8");
        warn_if_not_utf8_console("main() after init_utf8");
        warn_if_vt_input_enabled("main() after init_utf8");

        return run_with_optional_script(argc, argv);

    } catch (const std::exception& ex) {
        std::cerr << "Fatal error: " << ex.what() << "\n";
        return 1;
    } catch (...) {
        std::cerr << "Fatal error: unknown exception\n";
        return 1;
    }
}