#pragma once
// xbase_error_context.hpp
// Canonical engine-wide error context for xBase_64.
// Provides thread-local last-error tracking and RAII guards.

#include "xbase_error_codes.hpp"

#include <cctype>
#include <cstdint>
#include <cstdlib>
#include <string>
#include <string_view>

namespace xbase {
namespace error {

// -----------------------------------------------------------------------------
// Thread-local last error
// -----------------------------------------------------------------------------
inline thread_local code tls_last_error = ok();

// Monotonic counter bumped on every set_last_error. Lets a caller detect whether
// a *new* last-error was recorded across a unit of work (e.g. one script line)
// without pre-clearing the sticky thread-local last error.
inline thread_local std::uint64_t tls_error_generation = 0;

// -----------------------------------------------------------------------------
// Set/Get
// -----------------------------------------------------------------------------
inline void set_last_error(code c) noexcept
{
    tls_last_error = c;
    ++tls_error_generation;
}

inline code get_last_error() noexcept
{
    return tls_last_error;
}

inline std::uint64_t error_generation() noexcept
{
    return tls_error_generation;
}

// -----------------------------------------------------------------------------
// Clear
// -----------------------------------------------------------------------------
inline void clear_last_error() noexcept
{
    tls_last_error = ok();
}

// -----------------------------------------------------------------------------
// stop_on_error[severity] policy  (STOP_ON_ERROR command / SET ERRORSTOP TO)
//
// A DotScript run aborts when a NEW last-error at or above this severity
// threshold is recorded. `off` never aborts (default; preserves legacy
// behavior). The threshold is seeded once from the DOTTALK_ERRORSTOP environment
// variable (OFF|NONE|0, WARNING|WARN|1, ERROR|FATAL|2) and overridden at runtime
// by the STOP_ON_ERROR command or SET ERRORSTOP TO <severity>.
//
// "Errors derive from messaging": the severity compared here is the severity
// carried by the canonical error code recorded through emit_error/set_last_error
// (the message-catalog path), never an ad-hoc flag.
// -----------------------------------------------------------------------------
enum class errorstop_level : std::uint8_t
{
    off     = 0,   // never abort
    warning = 1,   // abort on warning-or-worse
    error   = 2    // abort on error only
};

inline errorstop_level parse_errorstop_level(std::string_view s, bool* ok = nullptr) noexcept
{
    std::string u;
    u.reserve(s.size());
    for (char c : s) u.push_back(static_cast<char>(std::toupper(static_cast<unsigned char>(c))));
    if (ok) *ok = true;
    if (u == "OFF"     || u == "NONE"  || u == "0") return errorstop_level::off;
    if (u == "WARNING" || u == "WARN"  || u == "1") return errorstop_level::warning;
    if (u == "ERROR"   || u == "FATAL" || u == "2") return errorstop_level::error;
    if (ok) *ok = false;
    return errorstop_level::off;
}

inline const char* errorstop_level_name(errorstop_level lvl) noexcept
{
    switch (lvl) {
        case errorstop_level::warning: return "WARNING";
        case errorstop_level::error:   return "ERROR";
        case errorstop_level::off:
        default:                       return "OFF";
    }
}

// Backing state; seeds once from DOTTALK_ERRORSTOP on first access.
inline errorstop_level& errorstop_state() noexcept
{
    static thread_local errorstop_level lvl = errorstop_level::off;
    static thread_local bool env_loaded = false;
    if (!env_loaded) {
        env_loaded = true;
        if (const char* e = std::getenv("DOTTALK_ERRORSTOP")) {
            bool ok = false;
            const errorstop_level parsed = parse_errorstop_level(e, &ok);
            if (ok) lvl = parsed;
        }
    }
    return lvl;
}

inline void set_errorstop(errorstop_level lvl) noexcept
{
    errorstop_state() = lvl;   // touch first so the env seed cannot clobber a later set
}

inline errorstop_level get_errorstop() noexcept
{
    return errorstop_state();
}

// True if a NEW last-error at/above the configured threshold was recorded since
// gen_before (captured with error_generation() before the unit of work).
inline bool errorstop_tripped(std::uint64_t gen_before) noexcept
{
    const errorstop_level thresh = get_errorstop();
    if (thresh == errorstop_level::off)     return false;
    if (tls_error_generation == gen_before) return false;   // nothing new recorded
    const auto sev = static_cast<std::uint8_t>(get_last_error().get_severity());
    return sev >= static_cast<std::uint8_t>(thresh);
}

// -----------------------------------------------------------------------------
// RAII Guard
// -----------------------------------------------------------------------------
class error_guard
{
public:
    error_guard() noexcept
        : saved_(tls_last_error)
    {
        tls_last_error = ok();
    }

    ~error_guard()
    {
        tls_last_error = saved_;
    }

private:
    code saved_;
};

} // namespace error
} // namespace xbase