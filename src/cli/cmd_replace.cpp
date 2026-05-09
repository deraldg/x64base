// src/cli/cmd_replace.cpp — REPLACE by field INDEX or NAME
// Usage:
//   REPLACE <field_index> WITH <value>
//   REPLACE <field_name>  WITH <value>
//
// Contract (current iteration):
// - TABLE ON: writes are buffered into the table buffer change list.
//   No OS record locking occurs here; COMMIT owns locking.
// - TABLE OFF: REPLACE locks + writes immediately.
// - CLI remains responsible for:
//     * parsing
//     * RHS evaluation
//     * x64 memo text -> stored object-id conversion
//     * field-level validation of the stored value
//     * table-buffer dirty/stale bookkeeping
//
// @dottalk.usage v1
// owner: DOT|REPLACE
// command: REPLACE
// category: data
// status: supported
// noargs: usage
// effect: mutate
// mutates: table-data table-buffer memo stale-state index
// usage-access: REPLACE USAGE
// summary:
//   Replace one field in the current record by field name or field index,
//   preserving RHS expression evaluation, type validation, memo conversion,
//   and table-buffer semantics.
//
// usage:
//   REPLACE USAGE
//   REPLACE <field_index> WITH <value>
//   REPLACE <field_name> WITH <value>
//
// examples:
//   REPLACE LNAME WITH "Smith"
//   REPLACE 3 WITH TODAY
//   REPLACE NOTES WITH "updated memo text"
//
// notes:
//   REPLACE requires an open table and a current record.
//   REPLACE resolves fields by standard field index/name rules.
//   RHS values pass through the expression/RHS evaluator and legacy string/date function handling.
//   X64 memo text is converted into stored object-id text before DBF storage.
//   Field values are validated and normalized before storage.
//   When TABLE buffering is ON, REPLACE records a buffered field change and marks the field stale/dirty.
//   When TABLE buffering is OFF, REPLACE writes immediately through DbArea storage.
//   COMMIT owns durable application of buffered table changes.
//   REPLACE is a table-data mutation command; do not classify it as read-only.
//
// risk:
//   writes_dbf_record: when TABLE buffering is OFF
//   writes_table_buffer: when TABLE buffering is ON
//   writes_memo: when replacing x64 memo fields with non-empty text
//   clears_memo_field: when replacing x64 memo fields with empty text
//   marks_dirty: when TABLE buffering is ON
//   marks_stale_field: yes
//   requires_current_record: yes
//   requires_open_table: yes
//   record_locking: immediate-write path relies on DbArea/write backend locking behavior
//
// related:
//   REPLACE_MULTI
//   TABLE
//   COMMIT
//   ROLLBACK
//   STRUCT
//   FIELDS
//

#include <algorithm>
#include <cctype>
#include <charconv>
#include <climits>
#include <cmath>
#include <cstdlib>
#include <cerrno>
#include <cstdio>
#include <ctime>
#include <iostream>
#include <stdexcept>
#include <limits>
#include <sstream>
#include <string>
#include <string_view>
#include <vector>
#include <cstdint>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase_field_getters.hpp"
#include "xbase_locks.hpp"
#include "textio.hpp"
#include "cli/settings.hpp"
#include "cli/table_state.hpp"
#include "cli/cli_currency.hpp"

#include "cli/expr/fn_string.hpp"
#include "cli/expr/fn_date.hpp"
#include "cli/expr/rhs_eval.hpp"
#include "cli/expr/value_eval.hpp"

#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

using cli::Settings;

static std::string to_upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

namespace {

struct Tok {
    enum Kind { Ident, Number, String, LParen, RParen, Comma, Plus, End } kind{};
    std::string text;
};

static std::string up_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

static std::string trim_copy(std::string s) {
    std::size_t a = 0;
    while (a < s.size() && std::isspace(static_cast<unsigned char>(s[a]))) ++a;

    std::size_t b = s.size();
    while (b > a && std::isspace(static_cast<unsigned char>(s[b - 1]))) --b;

    return s.substr(a, b - a);
}

static bool is_ident_start(char c) {
    return std::isalpha(static_cast<unsigned char>(c)) || c=='_' || c=='$';
}

static bool is_ident_char(char c) {
    return std::isalnum(static_cast<unsigned char>(c)) || c=='_' || c=='$';
}

static std::vector<Tok> lex(const std::string& src) {
    std::vector<Tok> out;
    std::size_t i = 0;

    auto skip_ws = [&](){
        while (i < src.size() && std::isspace(static_cast<unsigned char>(src[i]))) ++i;
    };

    skip_ws();
    while (i < src.size()) {
        char c = src[i];
        if (std::isspace(static_cast<unsigned char>(c))) { skip_ws(); continue; }
        if (c == '(') { out.push_back({Tok::LParen, "("}); ++i; continue; }
        if (c == ')') { out.push_back({Tok::RParen, ")"}); ++i; continue; }
        if (c == ',') { out.push_back({Tok::Comma, ","}); ++i; continue; }
        if (c == '+') { out.push_back({Tok::Plus, "+"}); ++i; continue; }

        if (c == '\'' || c == '\"') {
            const char q = c;
            ++i;
            std::string s;
            while (i < src.size()) {
                char d = src[i++];
                if (d == q) {
                    if (i < src.size() && src[i] == q) { s.push_back(q); ++i; continue; }
                    break;
                }
                s.push_back(d);
            }
            out.push_back({Tok::String, s});
            continue;
        }

        if (std::isdigit(static_cast<unsigned char>(c)) ||
            (c=='.' && i+1<src.size() && std::isdigit(static_cast<unsigned char>(src[i+1])))) {
            std::size_t j = i;
            bool dot = false;
            while (j < src.size()) {
                char d = src[j];
                if (std::isdigit(static_cast<unsigned char>(d))) { ++j; continue; }
                if (d == '.' && !dot) { dot = true; ++j; continue; }
                break;
            }
            out.push_back({Tok::Number, src.substr(i, j-i)});
            i = j;
            continue;
        }

        if (is_ident_start(c)) {
            std::size_t j = i+1;
            while (j < src.size() && is_ident_char(src[j])) ++j;
            out.push_back({Tok::Ident, src.substr(i, j-i)});
            i = j;
            continue;
        }

        break;
    }

    out.push_back({Tok::End, ""});
    return out;
}

static int resolve_field_index_by_name_ci(xbase::DbArea& A, const std::string& name) {
    try {
        const std::string want = up_copy(name);
        const auto defs = A.fields();
        for (std::size_t i = 0; i < defs.size(); ++i) {
            if (up_copy(defs[i].name) == want) return static_cast<int>(i) + 1;
        }
    } catch (...) {}
    return 0;
}

static char field_type_upper(const xbase::DbArea& A, int field1) {
    try {
        if (field1 < 1 || field1 > A.fieldCount()) return '\0';
        return (char)std::toupper((unsigned char)A.fields()[(std::size_t)(field1 - 1)].type);
    } catch (...) {
        return '\0';
    }
}

static int field_length(const xbase::DbArea& A, int field1) {
    try {
        if (field1 < 1 || field1 > A.fieldCount()) return 0;
        return (int)A.fields()[(std::size_t)(field1 - 1)].length;
    } catch (...) {
        return 0;
    }
}

static int field_decimals(const xbase::DbArea& A, int field1) {
    try {
        if (field1 < 1 || field1 > A.fieldCount()) return 0;
        return (int)A.fields()[(std::size_t)(field1 - 1)].decimals;
    } catch (...) {
        return 0;
    }
}

static bool is_x64_memo_field(const xbase::DbArea& A, int field1) {
    if (field1 < 1 || field1 > A.fieldCount()) return false;
    if (A.versionByte() != xbase::DBF_VERSION_64) return false;

    const auto& f = A.fields()[static_cast<std::size_t>(field1 - 1)];
    return (f.type == 'M' || f.type == 'm') &&
           f.length == xbase::X64_MEMO_FIELD_LEN;
}

static std::uint64_t parse_u64_or_zero(const std::string& s) {
    if (s.empty()) return 0;
    try {
        std::size_t used = 0;
        const unsigned long long v = std::stoull(s, &used, 10);
        if (used != s.size()) return 0;
        return static_cast<std::uint64_t>(v);
    } catch (...) {
        return 0;
    }
}

static dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& A) noexcept {
    auto* backend = cli_memo::memo_backend_for(A);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

static bool parse_i32_strict(const std::string& s, std::int32_t& out) {
    const std::string t = trim_copy(s);
    if (t.empty()) return false;

    const char* first = t.data();
    const char* last  = t.data() + t.size();

    std::int32_t v = 0;
    auto r = std::from_chars(first, last, v);
    if (r.ec != std::errc() || r.ptr != last) return false;

    out = v;
    return true;
}

static bool parse_double_strict(const std::string& s, double& out) {
    const std::string t = trim_copy(s);
    if (t.empty()) return false;

    errno = 0;
    char* end = nullptr;
    const double v = std::strtod(t.c_str(), &end);

    if (end == t.c_str()) return false;
    if (*end != '\0') return false;
    if (errno == ERANGE) return false;
    if (!std::isfinite(v)) return false;

    out = v;
    return true;
}

static bool parse_currency_strict(const std::string& s, std::int64_t& out_scaled) {
    double v = 0.0;
    if (!parse_double_strict(s, v)) return false;

    const double scaled = v * 10000.0;
    if (!std::isfinite(scaled)) return false;

    const double lo = static_cast<double>(std::numeric_limits<std::int64_t>::min());
    const double hi = static_cast<double>(std::numeric_limits<std::int64_t>::max());
    if (scaled < lo || scaled > hi) return false;

    out_scaled = static_cast<std::int64_t>(std::llround(scaled));
    return true;
}

static bool is_valid_yyyymmdd(const std::string& s) {
    if (s.size() != 8) return false;
    for (char c : s) {
        if (!std::isdigit((unsigned char)c)) return false;
    }

    const int y = std::stoi(s.substr(0, 4));
    const int m = std::stoi(s.substr(4, 2));
    const int d = std::stoi(s.substr(6, 2));

    if (m < 1 || m > 12) return false;

    static const int mdays[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    int maxd = mdays[m - 1];

    if (m == 2) {
        const bool leap = (y % 4 == 0) && ((y % 100 != 0) || (y % 400 == 0));
        if (leap) maxd = 29;
    }

    return d >= 1 && d <= maxd;
}

static std::string today_yyyymmdd() {
    std::time_t t = std::time(nullptr);
    std::tm tmv{};
#ifdef _WIN32
    localtime_s(&tmv, &t);
#else
    localtime_r(&t, &tmv);
#endif

    char buf[9];
    std::snprintf(buf, sizeof(buf), "%04d%02d%02d",
                  tmv.tm_year + 1900,
                  tmv.tm_mon + 1,
                  tmv.tm_mday);
    return std::string(buf);
}

static bool normalize_date_value(const std::string& raw, std::string& out) {
    std::string s = trim_copy(raw);
    const std::string u = up_copy(s);

    if (u == "TODAY") {
        out = today_yyyymmdd();
        return true;
    }

    if (is_valid_yyyymmdd(s)) {
        out = s;
        return true;
    }

    if (s.size() == 10 && s[2] == '/' && s[5] == '/') {
        const std::string mm = s.substr(0, 2);
        const std::string dd = s.substr(3, 2);
        const std::string yy = s.substr(6, 4);
        const std::string canon = yy + mm + dd;
        if (is_valid_yyyymmdd(canon)) {
            out = canon;
            return true;
        }
    }

    return false;
}

static bool normalize_logical_value(const std::string& raw, std::string& out) {
    const std::string s = up_copy(trim_copy(raw));

    if (s == "T" || s == ".T." || s == "TRUE" || s == "Y" || s == "1") {
        out = "T";
        return true;
    }

    if (s == "F" || s == ".F." || s == "FALSE" || s == "N" || s == "0") {
        out = "F";
        return true;
    }

    return false;
}

static bool normalize_numeric_value(const std::string& raw,
                                    int flen,
                                    int fdec,
                                    std::string& out)
{
    std::string s = trim_copy(raw);
    if (s.empty()) return false;

    bool seen_dot = false;
    int digits_before = 0;
    int digits_after = 0;
    std::size_t i = 0;

    if (s[i] == '+' || s[i] == '-') ++i;
    if (i >= s.size()) return false;

    for (; i < s.size(); ++i) {
        const char c = s[i];
        if (std::isdigit((unsigned char)c)) {
            if (seen_dot) ++digits_after;
            else ++digits_before;
            continue;
        }
        if (c == '.' && !seen_dot) {
            seen_dot = true;
            continue;
        }
        return false;
    }

    if (digits_before == 0 && digits_after == 0) return false;

    if (fdec <= 0) {
        if (seen_dot) return false;
        const int sign_chars = (!s.empty() && (s[0] == '+' || s[0] == '-')) ? 1 : 0;
        if ((digits_before + sign_chars) > flen) return false;
        out = s;
        return true;
    }

    if (digits_after > fdec) return false;

    const int sign_chars = (!s.empty() && (s[0] == '+' || s[0] == '-')) ? 1 : 0;
    const int total_chars = digits_before + sign_chars + 1 + digits_after;
    if (total_chars > flen) return false;

    out = s;
    return true;
}

static bool validate_field_value_for_store(const xbase::DbArea& A,
                                           int field1,
                                           const std::string& stored_value,
                                           std::string& err_out)
{
    err_out.clear();
    const char t = field_type_upper(A, field1);
    std::string norm;

    switch (t) {
        case 'D':
            if (!normalize_date_value(stored_value, norm)) {
                err_out = "invalid date for field";
                return false;
            }
            return true;

        case 'L':
            if (!normalize_logical_value(stored_value, norm)) {
                err_out = "invalid logical for field";
                return false;
            }
            return true;

        case 'N':
            if (!normalize_numeric_value(stored_value,
                                         field_length(A, field1),
                                         field_decimals(A, field1),
                                         norm)) {
                err_out = "invalid numeric for field";
                return false;
            }
            return true;

        case 'F':
            if (!normalize_numeric_value(stored_value,
                                         field_length(A, field1),
                                         field_decimals(A, field1),
                                         norm)) {
                err_out = "invalid float for field";
                return false;
            }
            return true;

        case 'I': {
            std::int32_t tmp = 0;
            if (!parse_i32_strict(stored_value, tmp)) {
                err_out = "invalid int32 for field";
                return false;
            }
            return true;
        }

        case 'B': {
            double tmp = 0.0;
            if (!parse_double_strict(stored_value, tmp)) {
                err_out = "invalid double for field";
                return false;
            }
            return true;
        }

        case 'Y': {
            std::int64_t scaled = 0;
            if (!parse_currency_strict(stored_value, scaled)) {
                err_out = "invalid currency for field";
                return false;
            }
            return true;
        }

        default:
            return true;
    }
}

class Parser {
public:
    Parser(xbase::DbArea& A, const std::vector<Tok>& t) : area_(A), toks_(t) {}
    bool parse_expr(std::string& out) {
        if (!parse_primary(out)) return false;
        while (accept(Tok::Plus)) {
            std::string rhs;
            if (!parse_primary(rhs)) return false;
            out += rhs;
        }
        return true;
    }

    bool at_end() const { return peek().kind == Tok::End; }

private:
    xbase::DbArea& area_;
    const std::vector<Tok>& toks_;
    std::size_t pos_ = 0;

    const Tok& peek() const { return toks_[pos_]; }
    bool accept(Tok::Kind k) { if (peek().kind == k) { ++pos_; return true; } return false; }
    bool expect(Tok::Kind k) { return accept(k); }

    bool parse_primary(std::string& out) {
        const Tok& t = peek();

        if (t.kind == Tok::String) { out = t.text; ++pos_; return true; }
        if (t.kind == Tok::Number) { out = t.text; ++pos_; return true; }

        if (t.kind == Tok::Ident) {
            std::string ident = t.text;
            ++pos_;

            if (accept(Tok::LParen)) {
                std::vector<std::string> args;
                if (!accept(Tok::RParen)) {
                    while (true) {
                        std::string a;
                        if (!parse_expr(a)) return false;
                        args.push_back(a);
                        if (accept(Tok::Comma)) continue;
                        if (!expect(Tok::RParen)) return false;
                        break;
                    }
                }

                const std::string fn = up_copy(ident);

                {
                    const auto* specs = dottalk::expr::string_fn_specs();
                    const std::size_t n = dottalk::expr::string_fn_specs_count();
                    for (std::size_t i = 0; i < n; ++i) {
                        const auto& s = specs[i];
                        if (fn == s.name) {
                            const int argc = static_cast<int>(args.size());
                            if (argc < s.min_args || argc > s.max_args) return false;
                            out = s.fn(args);
                            return true;
                        }
                    }
                }

                {
                    const auto* specs = dottalk::expr::date_fn_specs();
                    const std::size_t n = dottalk::expr::date_fn_specs_count();
                    for (std::size_t i = 0; i < n; ++i) {
                        const auto& s = specs[i];
                        if (fn == s.name) {
                            const int argc = static_cast<int>(args.size());
                            if (argc < s.min_args || argc > s.max_args) return false;
                            out = s.fn(args);
                            return true;
                        }
                    }
                }

                return false;
            }

            const int fld = resolve_field_index_by_name_ci(area_, ident);
            if (fld > 0) {
                try {
                    if (is_x64_memo_field(area_, fld)) {
                        const std::uint64_t oid = parse_u64_or_zero(area_.get(fld));
                        std::string txt;
                        if (auto* store = memo_store_for_area(area_); store && oid) {
                            (void)store->get_text_id(oid, txt, nullptr);
                        }
                        out = txt;
                    } else {
                        out = area_.get(fld);
                    }
                }
                catch (...) { out.clear(); }
                return true;
            }

            out = ident;
            return true;
        }

        return false;
    }
};


static bool eval_legacy_replace_expr(xbase::DbArea& A,
                                     const std::string& raw,
                                     std::string& out)
{
    const std::string t = trim_copy(raw);
    if (t.empty()) {
        out.clear();
        return true;
    }

    // Preserve the older REPLACE lexer/parser path.  The newer rhs_eval
    // layer handles most modern expression cases, but this local parser still
    // protects classic REPLACE behavior for quoted strings, string function
    // calls, field references, and + concatenation in this command.
    const std::vector<Tok> toks = lex(t);
    Parser parser(A, toks);

    std::string parsed;
    if (!parser.parse_expr(parsed)) {
        return false;
    }

    if (!parser.at_end()) {
        return false;
    }

    out = parsed;
    return true;
}

// Convert user text for an x64 memo field into the stored object-id string.
// On success, stored_value_out becomes either "" (no memo) or decimal object-id text.
static bool build_x64_memo_stored_value(xbase::DbArea& A,
                                        int field1,
                                        const std::string& user_value,
                                        std::string& stored_value_out,
                                        std::string& err_out)
{
    stored_value_out.clear();
    err_out.clear();

    if (!is_x64_memo_field(A, field1)) {
        stored_value_out = user_value;
        return true;
    }

    auto* store = memo_store_for_area(A);
    if (!store) {
        err_out = "memo backend not attached";
        return false;
    }

    std::uint64_t old_object_id = 0;
    try {
        old_object_id = parse_u64_or_zero(A.get(field1));
    } catch (...) {
        old_object_id = 0;
    }

    // Empty memo clears the field.
    if (user_value.empty()) {
        stored_value_out.clear();
        return true;
    }

    std::uint64_t new_object_id = 0;
    if (!store->update_text_id(old_object_id,
                               std::string_view(user_value),
                               new_object_id,
                               nullptr))
    {
        err_out = "memo store update failed";
        return false;
    }

    if (new_object_id == 0) {
        stored_value_out.clear();
    } else {
        stored_value_out = std::to_string(new_object_id);
    }

    return true;
}

extern "C" xbase::XBaseEngine* shell_engine(void);

static int resolve_current_index(xbase::DbArea& A) {
    xbase::XBaseEngine* eng = shell_engine();
    if (!eng) return -1;
    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        if (&eng->area(i) == &A) return i;
    }
    return -1;
}

struct RecordLockGuard {
    xbase::DbArea& A;
    uint32_t rn = 0;
    bool locked = false;

    RecordLockGuard(xbase::DbArea& area, uint32_t recno, bool acquire) : A(area), rn(recno) {
        if (!acquire) return;
        std::string err;
        locked = xbase::locks::try_lock_record(A, rn, &err);
        if (!locked) throw std::runtime_error(err.empty() ? "lock failed" : err);
    }

    ~RecordLockGuard() {
        if (locked) xbase::locks::unlock_record(A, rn);
    }

    RecordLockGuard(const RecordLockGuard&) = delete;
    RecordLockGuard& operator=(const RecordLockGuard&) = delete;
};


static bool is_replace_usage_request(const std::string& raw)
{
    std::string t = up_copy(trim_copy(raw));

    // Dispatch normally passes only the tail ("USAGE"), but accept full raw
    // input too ("REPLACE USAGE") so usage stays robust across shell paths.
    if (t.rfind("REPLACE ", 0) == 0) {
        t = trim_copy(t.substr(8));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_replace_usage()
{
    std::cout
        << "Usage:\n"
        << "  REPLACE USAGE\n"
        << "  REPLACE <field_index> WITH <value>\n"
        << "  REPLACE <field_name>  WITH <value>\n"
        << "Examples:\n"
        << "  REPLACE LNAME WITH \"Smith\"\n"
        << "  REPLACE 3 WITH TODAY\n"
        << "Notes:\n"
        << "  - REPLACE requires an open table and a current record.\n"
        << "  - RHS values are evaluated before validation/storage.\n"
        << "  - X64 memo text is converted to stored memo object-id text.\n"
        << "  - TABLE ON buffers field changes and marks fields stale/dirty.\n"
        << "  - TABLE OFF writes immediately through DbArea storage.\n";
}

} // namespace

void cmd_REPLACE(xbase::DbArea& A, std::istringstream& in) {
    const std::string raw_args = in.str();
    if (is_replace_usage_request(raw_args)) {
        print_replace_usage();
        return;
    }

    if (!A.isOpen()) {
        std::cout << "REPLACE: no file open.\n";
        return;
    }

    std::string field_name, with, value_raw;
    in >> field_name >> with;
    if (to_upper_copy(with) != "WITH") {
        print_replace_usage();
        return;
    }

    std::getline(in, value_raw);
    value_raw = textio::trim(value_raw);

    const int fldIndex0 = xfg::resolve_field_index_std(A, field_name);
    if (fldIndex0 < 0) {
        std::cout << "REPLACE: field not found.\n";
        return;
    }

    const int field1 = fldIndex0 + 1;
    const uint32_t rn = static_cast<uint32_t>(A.recno());
    if (rn == 0) {
        std::cout << "REPLACE: no current record.\n";
        return;
    }

    const int area0 = resolve_current_index(A);
    if (area0 < 0) {
        std::cout << "REPLACE: cannot determine current area.\n";
        return;
    }

    std::string user_value = value_raw;
    {
        std::string err;
        const dottalk::expr::EvalValue ev =
            dottalk::expr::eval_rhs(&A, value_raw, &err);

        if (ev.kind != dottalk::expr::EvalValue::K_None) {
            switch (ev.kind) {
                case dottalk::expr::EvalValue::K_String:
                    user_value = ev.text;
                    break;

                case dottalk::expr::EvalValue::K_Number: {
                    std::ostringstream os;
                    os << ev.number;
                    user_value = os.str();
                    break;
                }

                case dottalk::expr::EvalValue::K_Bool:
                    user_value = ev.tf ? "T" : "F";
                    break;

                case dottalk::expr::EvalValue::K_Date:
                    user_value = std::to_string(ev.date8);
                    break;

                default:
                    break;
            }
        } else {
            std::string legacy_value;
            if (eval_legacy_replace_expr(A, value_raw, legacy_value)) {
                user_value = legacy_value;
            }
        }
    }

    std::string stored_value = user_value;
    std::string memo_err;

    std::string currency_norm;
    std::string currency_err;
    if (!cli_currency::validate_and_normalize_currency_pair_field(A, field1, user_value, currency_norm, currency_err)) {
        std::cout << "REPLACE: " << currency_err << ".\n";
        return;
    }
    user_value = currency_norm;

    if (!build_x64_memo_stored_value(A, field1, user_value, stored_value, memo_err)) {
        std::cout << "REPLACE: " << memo_err << ".\n";
        return;
    }

    std::string validate_err;
    if (!validate_field_value_for_store(A, field1, stored_value, validate_err)) {
        std::cout << "REPLACE: " << validate_err << ".\n";
        return;
    }

    if (dottalk::table::is_enabled(area0)) {
        auto& tb = dottalk::table::get_tb(area0);

        std::uint64_t field_mask[dottalk::table::kWords]{};
        const int word = fldIndex0 / 64;
        const int bit  = fldIndex0 % 64;
        if (word >= 0 && word < dottalk::table::kWords) {
            field_mask[word] |= (std::uint64_t{1} << bit);
        }

        tb.add_change((int)rn, dottalk::table::CHANGE_UPDATE, field_mask, field1, stored_value);

        if (!dottalk::table::is_dirty(area0)) dottalk::table::set_dirty(area0, true);
        dottalk::table::mark_stale_field(area0, field1);

        if (Settings::instance().talk_on.load()) {
            std::cout << "REPLACE: buffered field #" << field1 << " at rec " << rn << ".\n";
        }
        return;
    }

    std::string before;
    std::string after;

    try {
        try { before = A.get(field1); } catch (...) { before.clear(); }

        std::string write_err;
        const bool ok = A.replaceFieldStored(field1, stored_value, &write_err);

        if (!ok) {
            std::cout << "REPLACE: "
                      << (write_err.empty() ? "write failed" : write_err)
                      << ".\n";
            return;
        }

        try { after = A.get(field1); } catch (...) { after.clear(); }

        if (before != after) dottalk::table::mark_stale_field(area0, field1);

        if (Settings::instance().talk_on.load()) {
            std::cout << "Replaced field #" << field1 << " at rec " << A.recno() << ".\n";
        }
    } catch (const std::exception& e) {
        std::cout << "REPLACE: write failed (" << e.what() << ").\n";
    } catch (...) {
        std::cout << "REPLACE: write failed.\n";
    }
}
