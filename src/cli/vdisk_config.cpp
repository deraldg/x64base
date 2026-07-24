// src/cli/vdisk_config.cpp
// [vdisk] admin config parser + Layer-1 sizing (AIF-043). See cli/vdisk_config.hpp.

#include "cli/vdisk_config.hpp"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <string>

#if defined(_WIN32)
#  ifndef WIN32_LEAN_AND_MEAN
#    define WIN32_LEAN_AND_MEAN
#  endif
#  ifndef NOMINMAX
#    define NOMINMAX
#  endif
#  include <windows.h>
#else
#  include <unistd.h>
#endif

namespace dottalk::vdisk {

namespace {

std::string trim(std::string s)
{
    auto sp = [](unsigned char c) { return std::isspace(c) != 0; };
    while (!s.empty() && sp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && sp((unsigned char)s.back()))  s.pop_back();
    return s;
}

std::string lower(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return (char)std::tolower(c); });
    return s;
}

// Strip an inline comment starting at the first ';' or '#'. Windows paths do not
// contain those characters, so this is safe for the `root` value too.
std::string strip_inline_comment(std::string v)
{
    const auto pos = v.find_first_of(";#");
    if (pos != std::string::npos) v.erase(pos);
    return trim(std::move(v));
}

std::uint64_t to_u64(const std::string& v, std::uint64_t dflt)
{
    try {
        const std::string t = trim(v);
        if (t.empty()) return dflt;
        return static_cast<std::uint64_t>(std::stoull(t));
    } catch (...) {
        return dflt;
    }
}

bool truthy(const std::string& v)
{
    const std::string t = lower(trim(v));
    return t == "1" || t == "true" || t == "yes" || t == "on";
}

} // namespace

const char* mode_name(Mode m) noexcept
{
    switch (m) {
        case Mode::Fixed:   return "fixed";
        case Mode::Percent: return "percent";
        case Mode::Auto:
        default:            return "auto";
    }
}

const char* on_full_name(OnFull f) noexcept
{
    switch (f) {
        case OnFull::Spill: return "spill";
        case OnFull::Fail:  return "fail";
        case OnFull::Warn:
        default:            return "warn";
    }
}

VDiskConfig load_vdisk_config(const std::string& ini_path)
{
    VDiskConfig c;  // defaults
    std::ifstream in(ini_path);
    if (!in) return c;  // no file => present=false

    bool in_section = false;
    std::string line;
    while (std::getline(in, line)) {
        std::string t = trim(line);
        if (t.empty()) continue;
        const char lead = t.front();
        if (lead == ';' || lead == '#' || lead == '*') continue;  // full-line comment

        if (lead == '[') {
            const auto end = t.find(']');
            const std::string name = (end != std::string::npos)
                ? lower(trim(t.substr(1, end - 1))) : std::string();
            in_section = (name == "vdisk");
            if (in_section) c.present = true;
            continue;
        }
        if (!in_section) continue;

        const auto eq = t.find('=');
        if (eq == std::string::npos) continue;
        const std::string key = lower(trim(t.substr(0, eq)));
        const std::string val = strip_inline_comment(t.substr(eq + 1));

        if      (key == "enabled")  c.enabled  = truthy(val);
        else if (key == "root")     c.root     = val;
        else if (key == "mode") {
            const std::string m = lower(val);
            c.mode = (m == "fixed") ? Mode::Fixed
                   : (m == "percent") ? Mode::Percent
                   : Mode::Auto;
        }
        else if (key == "size_mb")  c.size_mb  = to_u64(val, c.size_mb);
        else if (key == "percent")  c.percent  = to_u64(val, c.percent);
        else if (key == "floor_mb") c.floor_mb = to_u64(val, c.floor_mb);
        else if (key == "ceil_mb")  c.ceil_mb  = to_u64(val, c.ceil_mb);
        else if (key == "warn_pct") c.warn_pct = to_u64(val, c.warn_pct);
        else if (key == "on_full") {
            const std::string f = lower(val);
            c.on_full = (f == "spill") ? OnFull::Spill
                      : (f == "fail")  ? OnFull::Fail
                      : OnFull::Warn;
        }
        // unknown keys ignored
    }
    return c;
}

std::uint64_t physical_ram_bytes()
{
#if defined(_WIN32)
    MEMORYSTATUSEX s; s.dwLength = sizeof(s);
    if (GlobalMemoryStatusEx(&s)) return static_cast<std::uint64_t>(s.ullTotalPhys);
    return 0;
#else
    const long pages = sysconf(_SC_PHYS_PAGES);
    const long psize = sysconf(_SC_PAGE_SIZE);
    if (pages > 0 && psize > 0) return static_cast<std::uint64_t>(pages) * static_cast<std::uint64_t>(psize);
    return 0;
#endif
}

std::uint64_t available_ram_bytes()
{
#if defined(_WIN32)
    MEMORYSTATUSEX s; s.dwLength = sizeof(s);
    if (GlobalMemoryStatusEx(&s)) return static_cast<std::uint64_t>(s.ullAvailPhys);
    return 0;
#else
#  if defined(_SC_AVPHYS_PAGES)
    const long pages = sysconf(_SC_AVPHYS_PAGES);
    const long psize = sysconf(_SC_PAGE_SIZE);
    if (pages > 0 && psize > 0) return static_cast<std::uint64_t>(pages) * static_cast<std::uint64_t>(psize);
#  endif
    return 0;
#endif
}

std::uint64_t recommended_budget_bytes(const VDiskConfig& c)
{
    const std::uint64_t MB = 1024ull * 1024ull;
    const std::uint64_t total = physical_ram_bytes();
    const std::uint64_t avail = available_ram_bytes();
    const std::uint64_t base  = avail ? avail : total;  // prefer available; fall back to total

    std::uint64_t budget;
    switch (c.mode) {
        case Mode::Fixed:
            budget = c.size_mb * MB;
            break;
        case Mode::Percent:
            budget = base * (c.percent ? c.percent : 25) / 100;
            break;
        case Mode::Auto:
        default:
            budget = base * 25 / 100;  // Layer-1 default: 25% of available
            break;
    }

    // floor/ceil clamp even explicit overrides
    const std::uint64_t floor = c.floor_mb * MB;
    const std::uint64_t ceil  = c.ceil_mb  * MB;
    if (budget < floor) budget = floor;
    if (ceil && budget > ceil) budget = ceil;

    // host hardcap: never exceed half of physical RAM
    if (total) {
        const std::uint64_t hardcap = total / 2;
        if (budget > hardcap) budget = hardcap;
    }
    return budget;
}

} // namespace dottalk::vdisk
