// src/cli/expr/fn_numeric.cpp
// FoxPro-style numeric builtins for DotTalk++
//
// Notes:
// - Builtins operate on the current expression-layer contract:
//     arguments arrive as strings, results are returned as strings.
// - This file implements scalar numeric functions only.
// - Table/column aggregate commands such as SUM / AVG / COUNT / aggregate
//   MIN / MAX remain separate in the command layer.
//
// Implemented here:
//   ABS(n)
//   INT(n)
//   ROUND(n [, decimals])
//   MIN(a, b [, c ...])
//   MAX(a, b [, c ...])
//   BETWEEN(expr, low, high)
//   MOD(n1, n2)
//   SQRT(n)
//   CEILING(n)
//   FLOOR(n)
//   EXP(n)
//   LOG(n)
//   LOG10(n)
//   SIN(n)
//   COS(n)
//   TAN(n)
//   ASIN(n)
//   ACOS(n)
//   ATAN(n)
//   RAND()

#include "cli/expr/fn_string.hpp"   // brings in BuiltinFnSpec definition
#include "cli/expr/fn_numeric.hpp"

#include <cmath>
#include <iomanip>
#include <limits>
#include <random>
#include <sstream>
#include <string>
#include <vector>

namespace dottalk::expr {

namespace {

static bool parse_double_arg(const std::string& s, double& out) {
    try {
        std::size_t idx = 0;
        out = std::stod(s, &idx);

        while (idx < s.size()) {
            const unsigned char c = static_cast<unsigned char>(s[idx]);
            if (c != ' ' && c != '\t' && c != '\r' && c != '\n') {
                return false;
            }
            ++idx;
        }
        return true;
    } catch (...) {
        return false;
    }
}

static bool parse_int_arg(const std::string& s, int& out) {
    try {
        std::size_t idx = 0;
        out = std::stoi(s, &idx);

        while (idx < s.size()) {
            const unsigned char c = static_cast<unsigned char>(s[idx]);
            if (c != ' ' && c != '\t' && c != '\r' && c != '\n') {
                return false;
            }
            ++idx;
        }
        return true;
    } catch (...) {
        return false;
    }
}

static std::string format_number(double v) {
    if (std::isnan(v) || std::isinf(v)) return "0";

    std::ostringstream oss;
    oss << std::setprecision(15) << v;
    std::string s = oss.str();

    if (s.find('e') != std::string::npos || s.find('E') != std::string::npos) {
        return s;
    }

    const std::size_t dot = s.find('.');
    if (dot != std::string::npos) {
        while (!s.empty() && s.back() == '0') s.pop_back();
        if (!s.empty() && s.back() == '.') s.pop_back();
    }

    if (s == "-0") s = "0";
    if (s.empty()) s = "0";
    return s;
}

static std::string num_abs(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";
    double v = 0.0;
    if (!parse_double_arg(argv[0], v)) return "0";
    return format_number(std::fabs(v));
}

static std::string num_int(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";
    double v = 0.0;
    if (!parse_double_arg(argv[0], v)) return "0";

    // Truncate toward zero.
    const double t = (v >= 0.0) ? std::floor(v) : std::ceil(v);
    return format_number(t);
}

static std::string num_round(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double v = 0.0;
    if (!parse_double_arg(argv[0], v)) return "0";

    int dec = 0;
    if (argv.size() >= 2) {
        if (!parse_int_arg(argv[1], dec)) dec = 0;
    }

    const double factor = std::pow(10.0, static_cast<double>(dec));
    if (!std::isfinite(factor) || factor == 0.0) {
        return format_number(v);
    }

    const double r = std::round(v * factor) / factor;
    return format_number(r);
}

static std::string num_min(const std::vector<std::string>& argv) {
    if (argv.size() < 2) return "0";

    double best = 0.0;
    if (!parse_double_arg(argv[0], best)) return "0";

    for (std::size_t i = 1; i < argv.size(); ++i) {
        double v = 0.0;
        if (!parse_double_arg(argv[i], v)) return "0";
        if (v < best) best = v;
    }

    return format_number(best);
}

static std::string num_max(const std::vector<std::string>& argv) {
    if (argv.size() < 2) return "0";

    double best = 0.0;
    if (!parse_double_arg(argv[0], best)) return "0";

    for (std::size_t i = 1; i < argv.size(); ++i) {
        double v = 0.0;
        if (!parse_double_arg(argv[i], v)) return "0";
        if (v > best) best = v;
    }

    return format_number(best);
}

static std::string num_between(const std::vector<std::string>& argv) {
    if (argv.size() < 3) return ".F.";

    double x = 0.0, lo = 0.0, hi = 0.0;
    if (!parse_double_arg(argv[0], x))  return ".F.";
    if (!parse_double_arg(argv[1], lo)) return ".F.";
    if (!parse_double_arg(argv[2], hi)) return ".F.";

    return (x >= lo && x <= hi) ? ".T." : ".F.";
}

static std::string num_mod(const std::vector<std::string>& argv) {
    if (argv.size() < 2) return "0";

    double a = 0.0, b = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";
    if (!parse_double_arg(argv[1], b)) return "0";
    if (std::fabs(b) < 1e-12) return "0";

    double r = std::fmod(a, b);

    // Make remainder follow divisor sign.
    if ((r < 0.0 && b > 0.0) || (r > 0.0 && b < 0.0)) {
        r += b;
    }

    return format_number(r);
}

static std::string num_sqrt(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";
    if (a < 0.0) return "0";

    return format_number(std::sqrt(a));
}

static std::string num_ceiling(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    return format_number(std::ceil(a));
}

static std::string num_floor(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    return format_number(std::floor(a));
}

static std::string num_exp(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    const double r = std::exp(a);
    if (!std::isfinite(r)) return "0";
    return format_number(r);
}

static std::string num_log(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";
    if (a <= 0.0) return "0";

    return format_number(std::log(a));
}

static std::string num_log10(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";
    if (a <= 0.0) return "0";

    return format_number(std::log10(a));
}

static std::string num_sin(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    return format_number(std::sin(a));
}

static std::string num_cos(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    return format_number(std::cos(a));
}

static std::string num_tan(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    const double r = std::tan(a);
    if (!std::isfinite(r)) return "0";
    return format_number(r);
}

static std::string num_asin(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";
    if (a < -1.0 || a > 1.0) return "0";

    return format_number(std::asin(a));
}

static std::string num_acos(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";
    if (a < -1.0 || a > 1.0) return "0";

    return format_number(std::acos(a));
}

static std::string num_atan(const std::vector<std::string>& argv) {
    if (argv.empty()) return "0";

    double a = 0.0;
    if (!parse_double_arg(argv[0], a)) return "0";

    return format_number(std::atan(a));
}

static std::string num_rand(const std::vector<std::string>& /*argv*/) {
    static std::mt19937_64 rng{std::random_device{}()};
    static std::uniform_real_distribution<double> dist(
        0.0,
        std::nextafter(1.0, 0.0)
    );

    return format_number(dist(rng));
}

static const BuiltinFnSpec kNumericFns[] = {
    { "ABS",      1, 1,  &num_abs },
    { "INT",      1, 1,  &num_int },
    { "ROUND",    1, 2,  &num_round },
    { "MIN",      2, 32, &num_min },
    { "MAX",      2, 32, &num_max },
    { "BETWEEN",  3, 3,  &num_between },
    { "MOD",      2, 2,  &num_mod },
    { "SQRT",     1, 1,  &num_sqrt },
    { "CEILING",  1, 1,  &num_ceiling },
    { "FLOOR",    1, 1,  &num_floor },
    { "EXP",      1, 1,  &num_exp },
    { "LOG",      1, 1,  &num_log },
    { "LOG10",    1, 1,  &num_log10 },
    { "SIN",      1, 1,  &num_sin },
    { "COS",      1, 1,  &num_cos },
    { "TAN",      1, 1,  &num_tan },
    { "ASIN",     1, 1,  &num_asin },
    { "ACOS",     1, 1,  &num_acos },
    { "ATAN",     1, 1,  &num_atan },
    { "RAND",     0, 0,  &num_rand },
};

static constexpr std::size_t kCount =
    sizeof(kNumericFns) / sizeof(kNumericFns[0]);

} // namespace

const BuiltinFnSpec* numeric_fn_specs() {
    return kNumericFns;
}

std::size_t numeric_fn_specs_count() {
    return kCount;
}

} // namespace dottalk::expr