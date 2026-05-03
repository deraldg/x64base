#ifdef _WIN32
#ifndef NOMINMAX
#define NOMINMAX
#endif

#include "cli/console.hpp"

#include <conio.h>
#include <windows.h>

#include <iostream>
#include <string>

// ====== Config ==============================================================
static constexpr bool kUseAsciiFrame = false;

static const char* kReset      = "\x1b[0m";
static const char* kFrameStyle = "\x1b[30;43m";
// ============================================================================

static void write_w(HANDLE h, int x, int y, const std::wstring& s)
{
    if (h == INVALID_HANDLE_VALUE || h == nullptr) return;

    COORD pos{};
    pos.X = static_cast<SHORT>(x);
    pos.Y = static_cast<SHORT>(y);
    SetConsoleCursorPosition(h, pos);

    DWORD written = 0;
    WriteConsoleW(h, s.c_str(), static_cast<DWORD>(s.size()), &written, nullptr);
}

struct WinConsole : Console
{
    HANDLE hOut{ INVALID_HANDLE_VALUE };

    WinConsole()
    {
        hOut = GetStdHandle(STD_OUTPUT_HANDLE);

        if (hOut != INVALID_HANDLE_VALUE && hOut != nullptr) {
            DWORD mode = 0;
            if (GetConsoleMode(hOut, &mode)) {
                SetConsoleMode(hOut, mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING);
            }
        }

        SetConsoleOutputCP(CP_UTF8);
    }

    void clear() override
    {
        std::cout << "\x1b[2J\x1b[H";
    }

    void move_to(int x, int y) override
    {
        std::cout << "\x1b[" << (y + 1) << ";" << (x + 1) << "H";
    }

    void draw_text(int x, int y, const std::string& s, int clip = -1) override
    {
        move_to(x, y);
        if (clip >= 0 && static_cast<int>(s.size()) > clip)
            std::cout << s.substr(0, static_cast<std::size_t>(clip));
        else
            std::cout << s;
    }

    void draw_frame(int l, int t, int w, int h) override
    {
        if (w < 2 || h < 2) return;

        if (kUseAsciiFrame) {
            for (int i = 0; i < w; ++i) {
                draw_text(l + i, t, "-");
                draw_text(l + i, t + h - 1, "-");
            }
            for (int y = t; y < t + h; ++y) {
                draw_text(l, y, "|");
                draw_text(l + w - 1, y, "|");
            }
            draw_text(l, t, "+");
            draw_text(l + w - 1, t, "+");
            draw_text(l, t + h - 1, "+");
            draw_text(l + w - 1, t + h - 1, "+");
            return;
        }

        const wchar_t TL = L'\u250C'; // ┌
        const wchar_t TR = L'\u2510'; // ┐
        const wchar_t BL = L'\u2514'; // └
        const wchar_t BR = L'\u2518'; // ┘
        const wchar_t H  = L'\u2500'; // ─
        const wchar_t V  = L'\u2502'; // │

        std::wstring top;
        top += TL;
        top.append(static_cast<std::size_t>(w - 2), H);
        top += TR;

        std::wstring mid;
        mid += V;
        mid.append(static_cast<std::size_t>(w - 2), L' ');
        mid += V;

        std::wstring bot;
        bot += BL;
        bot.append(static_cast<std::size_t>(w - 2), H);
        bot += BR;

        write_w(hOut, l, t, top);

        for (int i = 1; i < h - 1; ++i) {
            write_w(hOut, l, t + i, mid);
        }

        write_w(hOut, l, t + h - 1, bot);
    }

    int get_key() override
    {
        return _getch();
    }

    Size size() override
    {
        Size s{80, 25};
        CONSOLE_SCREEN_BUFFER_INFO info{};
        if (hOut != INVALID_HANDLE_VALUE && hOut != nullptr &&
            GetConsoleScreenBufferInfo(hOut, &info)) {
            s.cols = info.srWindow.Right  - info.srWindow.Left + 1;
            s.rows = info.srWindow.Bottom - info.srWindow.Top  + 1;
        }
        return s;
    }
};

Console* make_console()
{
    return new WinConsole();
}

#endif // _WIN32