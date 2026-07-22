// src/cli/expr/fn_date.cpp
// FoxPro-style date/time builtins — centralized in the expression layer.

#include "cli/expr/fn_date.hpp"

#include "date/date_utils.hpp"
#include "date/date_arith.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdio>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <string>
#include <vector>

namespace dottalk::expr {

namespace {

// --------------------------------------------------
// Small local helpers
// --------------------------------------------------

static bool parse_ymd8(const std::string& s, int& y, int& m, int& d) {
    if (s.size() != 8) return false;
    for (char c : s) {
        if (!std::isdigit(static_cast<unsigned char>(c))) return false;
    }
    try {
        y = std::stoi(s.substr(0, 4));
        m = std::stoi(s.substr(4, 2));
        d = std::stoi(s.substr(6, 2));
        return true;
    } catch (...) {
        return false;
    }
}

// Sakamoto day-of-week: 0=Sunday .. 6=Saturday
static int day_of_week_sun0(int y, int m, int d) {
    static const int t[] = {0, 3, 2, 5, 0, 3, 5, 1, 4, 6, 2, 4};
    y -= (m < 3) ? 1 : 0;
    return (y + y/4 - y/100 + y/400 + t[m - 1] + d) % 7;
}

static int days_in_month(int y, int m) {
    static const int mdays[] = { 31,28,31,30,31,30,31,31,30,31,30,31 };
    int maxd = mdays[m - 1];
    if (m == 2) {
        const bool leap = ((y % 4 == 0 && y % 100 != 0) || (y % 400 == 0));
        if (leap) maxd = 29;
    }
    return maxd;
}

// --------------------------------------------------
// Builtin implementations
// --------------------------------------------------

static std::string dt_date(const std::vector<std::string>& /*argv*/) {
    return dottalk::date::now_local().date8;
}

static std::string dt_today(const std::vector<std::string>& /*argv*/) {
    return dottalk::date::now_local().date8;
}

static std::string dt_time(const std::vector<std::string>& /*argv*/) {
    return dottalk::date::now_local().time6;
}

static std::string dt_seconds(const std::vector<std::string>& /*argv*/) {
    // FoxPro SECONDS(): seconds elapsed since midnight, with sub-second
    // (millisecond) resolution. The prior implementation derived from the
    // HHMMSS time6 string, so it was integer-only — useless for benchmarking
    // and self-timing (deltas rounded to whole seconds). Use a real clock.
    using namespace std::chrono;
    const auto now = system_clock::now();
    const std::time_t tt = system_clock::to_time_t(now);
    std::tm lt{};
#if defined(_WIN32)
    localtime_s(&lt, &tt);
#else
    localtime_r(&tt, &lt);
#endif
    const auto since_epoch = now.time_since_epoch();
    const auto whole_secs  = duration_cast<seconds>(since_epoch);
    const long millis =
        static_cast<long>(duration_cast<milliseconds>(since_epoch - whole_secs).count());

    const double total = lt.tm_hour * 3600.0 + lt.tm_min * 60.0 + lt.tm_sec
                         + static_cast<double>(millis) / 1000.0;

    char buf[32];
    std::snprintf(buf, sizeof(buf), "%.3f", total);
    return std::string(buf);
}

static std::string dt_now(const std::vector<std::string>& /*argv*/) {
    return dottalk::date::now_local().datetime14;
}

static std::string dt_datetime(const std::vector<std::string>& /*argv*/) {
    return dottalk::date::now_local().datetime14;
}

static std::string dt_ctod(const std::vector<std::string>& argv) {
    if (argv.empty()) return " ";
    const auto d8 = dottalk::date::parse_ctod(argv[0]);
    return d8.empty() ? " " : d8;
}

static std::string dt_dtoc(const std::vector<std::string>& argv) {
    if (argv.empty()) return {};

    std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return {};

    // style support:
    //   0 = YYYYMMDD
    //   1 = YYYY-MM-DD
    //   2 = YYYY/MM/DD
    int style = 0;
    if (argv.size() >= 2) {
        try {
            std::string st = argv[1];
            st.erase(std::remove_if(st.begin(), st.end(),
                     [](unsigned char c) { return std::isspace(c) != 0; }),
                     st.end());
            if (!st.empty()) style = std::stoi(st);
        } catch (...) {
        }
    }

    if (style == 1) return s.substr(0, 4) + "-" + s.substr(4, 2) + "-" + s.substr(6, 2);
    if (style == 2) return s.substr(0, 4) + "/" + s.substr(4, 2) + "/" + s.substr(6, 2);
    return s;
}

static std::string dt_dtos(const std::vector<std::string>& argv) {
    if (argv.empty()) return {};
    std::string s = dottalk::date::parse_ctod(argv[0]);
    return s.empty() ? std::string{} : s;
}

static std::string dt_day(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";
    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return "0";

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return "0";
    return std::to_string(d);
}

static std::string dt_dow(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";
    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return "0";

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return "0";

    // Fox-style numbering: 1=Sunday .. 7=Saturday
    return std::to_string(day_of_week_sun0(y, m, d) + 1);
}

static std::string dt_month(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";
    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return "0";

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return "0";
    return std::to_string(m);
}

static std::string dt_year(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";
    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return "0";

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return "0";
    return std::to_string(y);
}

static std::string dt_cdow(const std::vector<std::string>& argv) {
    if (argv.empty()) return {};

    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return {};

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return {};

    static const char* names[] = {
        "Sunday", "Monday", "Tuesday", "Wednesday",
        "Thursday", "Friday", "Saturday"
    };

    const int dow = day_of_week_sun0(y, m, d);
    return names[dow];
}

static std::string dt_cmonth(const std::vector<std::string>& argv) {
    if (argv.empty()) return {};

    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return {};

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return {};

    static const char* names[] = {
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
    };

    if (m < 1 || m > 12) return {};
    return names[m - 1];
}

static std::string dt_gomonth(const std::vector<std::string>& argv) {
    if (argv.size() < 2) return {};

    const std::string s = dottalk::date::parse_ctod(argv[0]);
    if (s.empty()) return {};

    int y = 0, m = 0, d = 0;
    if (!parse_ymd8(s, y, m, d)) return {};

    int delta = 0;
    try {
        delta = std::stoi(argv[1]);
    } catch (...) {
        return {};
    }

    m += delta;
    while (m > 12) { m -= 12; ++y; }
    while (m < 1)  { m += 12; --y; }

    const int maxd = days_in_month(y, m);
    if (d > maxd) d = maxd;

    std::ostringstream o;
    o << std::setw(4) << std::setfill('0') << y
      << std::setw(2) << std::setfill('0') << m
      << std::setw(2) << std::setfill('0') << d;
    return o.str();
}

static std::string dt_dateadd(const std::vector<std::string>& argv) {
    if (argv.size() < 2) return " ";
    const auto base = dottalk::date::parse_ctod(argv[0]);
    if (base.empty()) return " ";
    try {
        const int delta = std::stoi(argv[1]);
        return dottalk::date::add_days(base, delta);
    } catch (...) {
        return " ";
    }
}

static std::string dt_datediff(const std::vector<std::string>& argv) {
    if (argv.size() < 2) return "0";
    const auto d1 = dottalk::date::parse_ctod(argv[0]);
    const auto d2 = dottalk::date::parse_ctod(argv[1]);
    if (d1.empty() || d2.empty()) return "0";
    const int diff = dottalk::date::diff_days(d1, d2);
    return std::to_string(diff);
}

// --------------------------------------------------
// Function table
// --------------------------------------------------

static const BuiltinFnSpec kDateFns[] = {
    { "DATE",      0, 0, &dt_date },
    { "TODAY",     0, 0, &dt_today },
    { "TIME",      0, 0, &dt_time },
    { "SECONDS",   0, 0, &dt_seconds },
    { "NOW",       0, 0, &dt_now },
    { "DATETIME",  0, 0, &dt_datetime },

    { "CTOD",      1, 1, &dt_ctod },
    { "DTOC",      1, 2, &dt_dtoc },
    { "DTOS",      1, 1, &dt_dtos },

    { "DAY",       1, 1, &dt_day },
    { "DOW",       1, 1, &dt_dow },
    { "MONTH",     1, 1, &dt_month },
    { "YEAR",      1, 1, &dt_year },
    { "CDOW",      1, 1, &dt_cdow },
    { "CMONTH",    1, 1, &dt_cmonth },
    { "GOMONTH",   2, 2, &dt_gomonth },

    { "DATEADD",   2, 2, &dt_dateadd },
    { "DATEDIFF",  2, 2, &dt_datediff },
};

static constexpr std::size_t kCount = sizeof(kDateFns) / sizeof(kDateFns[0]);

} // namespace

const BuiltinFnSpec* date_fn_specs() {
    return kDateFns;
}

std::size_t date_fn_specs_count() {
    return kCount;
}

} // namespace dottalk::expr