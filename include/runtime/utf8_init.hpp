// @dottalk.file v1
// subsystem: runtime
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once

// Header-only UTF-8 / VT init for DotTalk++
//
// Windows policy:
// - Console code pages are set to UTF-8.
// - VT OUTPUT is optional (colors / clears).
// - VT INPUT remains OFF (important for Turbo Vision / CLI key handling).
// - Do NOT force stdout/stderr into narrow text mode here.
//   True Unicode glyph rendering on Windows should use WriteConsoleW
//   (or a deliberate wide-output path) in the console layer.
//
// POSIX policy:
// - Install a UTF-8 locale if available.

#include <locale>

#if defined(_WIN32)
  #ifndef NOMINMAX
  #define NOMINMAX
  #endif
  #include <windows.h>
#endif

// ------------------------------------------------------------
// TEMP PERFORMANCE SWITCH
// 0 = VT OUTPUT OFF (FAST; ANSI colors/clears disabled)
// 1 = VT OUTPUT ON  (ANSI colors/clears enabled)
// ------------------------------------------------------------
#ifndef DOTTALK_ENABLE_VT_OUTPUT
#define DOTTALK_ENABLE_VT_OUTPUT 0
#endif

namespace dottalk {

inline void init_utf8() {
#if defined(_WIN32)
    // 1) Switch console code pages to UTF-8.
    // This helps for UTF-8 aware tools and narrow text that is genuinely UTF-8,
    // but true Unicode box drawing should still use WriteConsoleW in console_win.cpp.
    ::SetConsoleOutputCP(CP_UTF8);
    ::SetConsoleCP(CP_UTF8);

    // 2) VT OUTPUT (ANSI) -- optional.
    if (HANDLE hOut = ::GetStdHandle(STD_OUTPUT_HANDLE);
        hOut != INVALID_HANDLE_VALUE && hOut != nullptr) {
        DWORD mode = 0;
        if (::GetConsoleMode(hOut, &mode)) {
#if DOTTALK_ENABLE_VT_OUTPUT
            mode |= ENABLE_VIRTUAL_TERMINAL_PROCESSING;
#else
            mode &= ~ENABLE_VIRTUAL_TERMINAL_PROCESSING;
#endif
            ::SetConsoleMode(hOut, mode);
        }
    }

    // 3) ENSURE VT INPUT IS OFF (critical for classic key handling)
    if (HANDLE hIn = ::GetStdHandle(STD_INPUT_HANDLE);
        hIn != INVALID_HANDLE_VALUE && hIn != nullptr) {
        DWORD mode = 0;
        if (::GetConsoleMode(hIn, &mode)) {
            mode &= ~ENABLE_VIRTUAL_TERMINAL_INPUT;
            ::SetConsoleMode(hIn, mode);
        }
    }

    // 4) Locale only. Do not force stdout/stderr mode here.
    // Leave output mode decisions to the console layer.
    //
    // AIF-116: take the ENCODING from the native locale, but the NUMERIC
    // facets from "C". A bare std::locale("") installs the whole native
    // locale, numpunct included, so on a grouping host every un-imbued
    // stream in the process starts emitting "16,984" for 16984. That is
    // not cosmetic: xbase_locks serialised the owner pid through such a
    // stream, std::stoul read back 16, is_pid_alive said no, and every
    // live lock was classified stale and force-removed -- cross-process
    // mutual exclusion silently did not hold. AIF-031's ~20 imbue(classic)
    // calls are the same damage seen at other sites and patched one by one;
    // this is the same fix applied at the cause instead.
    try {
        std::locale native("");
        std::locale::global(std::locale(native, std::locale::classic(),
                                        std::locale::numeric));
    } catch (...) {
        // best effort only
    }

#else
    // POSIX: C.UTF-8 already carries classic numeric facets, so it is not
    // exposed to the AIF-116 defect. The en_US.UTF-8 fallback IS, so it gets
    // the same numeric override rather than being trusted.
    try {
        std::locale::global(std::locale("C.UTF-8"));
    } catch (...) {
        try {
            std::locale fallback("en_US.UTF-8");
            std::locale::global(std::locale(fallback, std::locale::classic(),
                                            std::locale::numeric));
        } catch (...) {
            // best effort only
        }
    }
#endif
}

} // namespace dottalk