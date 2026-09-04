// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_replace_multi.cpp -- multi-field replace with one record lock + one write
//
// Maintenance note, 2026-05-01:
//   MULTIREP must evaluate/dequote RHS values before validation/storage,
//   matching REPLACE behavior for string literals, TODAY, booleans, and
//   numeric values. Presentation formatting must not enter stored values.
//
// CLI usage:
//   MULTIREP <field> WITH <value>[, <field> WITH <value>]...
//
// Also provides a programmatic overload:
//   bool cmd_REPLACE_MULTI(xbase::DbArea& A,
//                          const std::vector<FieldUpdate>& updates,
//                          std::string* error)
//
// Rule (AIF-151, 2026-09-04 -- MULTIREP now honours TABLE ON):
//   - TABLE ON  => stages into the table buffer, takes NO OS lock, marks DIRTY
//     and marks each assigned field STALE. Applied by COMMIT, discardable by
//     ROLLBACK, and journaled under RamJournal.
//   - TABLE OFF => unchanged: one record lock, one physical write, immediate
//     index maintenance through IndexManager simple-field tag logic, and
//     field-level STALE only if that maintenance fails.
//   - ONE PHYSICAL WRITE SURVIVES BUFFERING. add_change stages one field per
//     call, and COMMIT's aggregate_for_recno folds every entry for a recno back
//     into one set() loop and one writeCurrent().
//   - MEMO: buffering defers the POINTER, NOT THE PAYLOAD. The memo object is
//     written immediately and only its handle is buffered, so ROLLBACK leaves a
//     reclaimable orphan that MEMO GC finds and reports. Same as REPLACE.
//
// Notes:
//   - Compound/computed tags are deferred.
//   - Simple first-pass policy: field-name == tag-name via IndexManager.
//   - Still single-area, current-record, multi-field: no alias qualification,
//     so writing across tables is a separate upgrade (see AIF-151's row).

// @dottalk.usage v1
// owner: DOT|MULTIREP
// command: MULTIREP
// aliases:
// category: data
// status: supported
// noargs: usage
// effect: mutate
// mutates: table-data memo index stale-state
// usage-access: MULTIREP USAGE
// summary:
//   Replace multiple fields in the current record with one record lock and
//   one physical write, preserving RHS evaluation, validation, memo handling,
//   and direct index maintenance.
//
// usage:
//   MULTIREP <field> WITH <value>[, <field> WITH <value>]...
//
// examples:
//   MULTIREP LNAME WITH "Smith", FNAME WITH "John"
//   MULTIREP DOB WITH 20000101, ACTIVE WITH .T.
//
// notes:
//   MULTIREP requires an open table and a current record.
//   MULTIREP validates all assignments before applying the physical write.
//   RHS values are evaluated/dequoted before validation and storage.
//   Memo fields are written through the memo backend before storing the memo token.
//   With TABLE ON, MULTIREP stages its assignments in the table buffer, takes no
//   record lock, marks the buffer DIRTY and marks each assigned field STALE.
//   COMMIT applies them as one physical write; ROLLBACK discards them.
//   With TABLE OFF, MULTIREP writes directly to the DBF with one record lock and
//   one physical write, captures before/after index snapshots and applies direct
//   index maintenance; if that fails, changed fields are marked STALE.
//   Buffered memo assignments write the memo payload immediately and buffer only
//   the stored handle, so a ROLLBACK leaves an orphan memo object that MEMO GC
//   can find and reclaim.
//   MULTIREP is a table-data mutation command; do not classify it as read-only.
//   cmd_REPLACE_MULTI is the internal handler name; REPLACE_MULTI is not a registered command.
//
// risk:
//   writes_dbf_record: yes
//   writes_memo: when replacing memo fields
//   one_record_lock: TABLE OFF only; no OS lock is taken when buffering
//   one_physical_write: yes (buffered assignments are folded by COMMIT)
//   marks_dirty: yes when TABLE ON; no when TABLE OFF
//   buffered_when_table_on: yes (AIF-151)
//   rollback_discards: yes when TABLE ON, except a memo payload already written
//   marks_stale_field: only if index maintenance fails for changed fields
//   index_maintenance: direct before/after snapshot application
//   requires_current_record: yes
//   requires_open_table: yes
//
// related:
//   REPLACE
//   TABLE
//   COMMIT
//   ROLLBACK
//   STRUCT
//   FIELDS
//

#include <algorithm>
#include <cctype>
#include <cerrno>
#include <charconv>
#include <cmath>
#include <cstdlib>
#include <cstdint>
#include <cstdio>
#include <ctime>
#include <limits>
#include <iomanip>
#include <locale>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "xbase.hpp"
#include "xbase_locks.hpp"

#include "cli/command_output.hpp"
#include "cli/table_state.hpp"
#include "workarea_util.hpp"          // AIF-151: cli::slot_of_area
#include "cli/cli_currency.hpp"
#include "cli/expr/rhs_eval.hpp"
#include "cli/expr/value_eval.hpp"
#include "memo/memo_auto.hpp"

// Added: direct index maintenance seam
#include "xindex/index_manager.hpp"
#include "xindex/attach.hpp"

// Provided by the interactive shell.
extern "C" xbase::XBaseEngine* shell_engine(void);

// --------- If you already have FieldUpdate in a header, include it instead ----------
struct FieldUpdate {
    std::string name;   // field name OR numeric string index (e.g. "3")
    std::string value;  // raw value
};
// -----------------------------------------------------------------------------------

namespace {

static std::string up_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c){ return (char)std::toupper(c); });
    return s;
}

static void trim_inplace(std::string& s) {
    size_t a = 0;
    while (a < s.size() && std::isspace((unsigned char)s[a])) ++a;
    size_t b = s.size();
    while (b > a && std::isspace((unsigned char)s[b - 1])) --b;
    s = s.substr(a, b - a);
}

static std::string trim_copy(std::string s) {
    trim_inplace(s);
    return s;
}

static bool try_parse_int(const std::string& s, int& out) {
    if (s.empty()) return false;
    size_t i = 0;
    if (s[0] == '+' || s[0] == '-') i = 1;
    for (; i < s.size(); ++i) {
        if (!std::isdigit((unsigned char)s[i])) return false;
    }
    try {
        long long v = std::stoll(s);
        if (v < std::numeric_limits<int>::min() || v > std::numeric_limits<int>::max()) return false;
        out = (int)v;
        return true;
    } catch (...) {
        return false;
    }
}

static bool is_ident_start(char c) {
    return std::isalpha(static_cast<unsigned char>(c)) || c == '_' || c == '$';
}

static bool is_ident_char(char c) {
    return std::isalnum(static_cast<unsigned char>(c)) || c == '_' || c == '$';
}

// Resolve a field name (case-insensitive) to 1-based index.
static int resolve_field_index_by_name_ci(xbase::DbArea& A, const std::string& name) {
    try {
        const std::string want = up_copy(name);
        const auto defs = A.fields();
        for (std::size_t i = 0; i < defs.size(); ++i) {
            if (up_copy(defs[i].name) == want) return (int)i + 1;
        }
    } catch (...) {}
    return 0;
}

static bool values_equal_for_stale_check(const std::string& before, const std::string& after) {
    return before == after;
}

static char field_type_upper(xbase::DbArea& A, int fld1) {
    try {
        const auto defs = A.fields();
        const int idx0 = fld1 - 1;
        if (idx0 < 0 || idx0 >= (int)defs.size()) return '\0';
        return (char)std::toupper((unsigned char)defs[(std::size_t)idx0].type);
    } catch (...) {
        return '\0';
    }
}

static int field_length(xbase::DbArea& A, int fld1) {
    try {
        const auto defs = A.fields();
        const int idx0 = fld1 - 1;
        if (idx0 < 0 || idx0 >= (int)defs.size()) return 0;
        return (int)defs[(std::size_t)idx0].length;
    } catch (...) {
        return 0;
    }
}

static int field_decimals(xbase::DbArea& A, int fld1) {
    try {
        const auto defs = A.fields();
        const int idx0 = fld1 - 1;
        if (idx0 < 0 || idx0 >= (int)defs.size()) return 0;
        return (int)defs[(std::size_t)idx0].decimals;
    } catch (...) {
        return 0;
    }
}

static bool is_memo_field_type(xbase::DbArea& A, int fld1) {
    const char t = field_type_upper(A, fld1);
    return t == 'M';
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


static std::string format_number_for_internal_transfer(double value) {
    const double rounded = std::round(value);
    std::ostringstream os;
    os.imbue(std::locale::classic());

    if (std::fabs(value - rounded) < 1e-9) {
        os << static_cast<long long>(rounded);
        return os.str();
    }

    os << std::fixed << std::setprecision(10) << value;
    std::string out = os.str();
    while (!out.empty() && out.find('.') != std::string::npos && out.back() == '0') out.pop_back();
    if (!out.empty() && out.back() == '.') out.pop_back();
    return out.empty() ? "0" : out;
}

static std::string rhs_to_user_value(xbase::DbArea& A, const std::string& raw) {
    std::string err;
    const dottalk::expr::EvalValue ev = dottalk::expr::eval_rhs(&A, raw, &err);

    switch (ev.kind) {
        case dottalk::expr::EvalValue::K_String:
            return ev.text;

        case dottalk::expr::EvalValue::K_Number:
            return format_number_for_internal_transfer(ev.number);

        case dottalk::expr::EvalValue::K_Bool:
            return ev.tf ? "T" : "F";

        case dottalk::expr::EvalValue::K_Date:
            return std::to_string(ev.date8);

        default:
            return trim_copy(raw);
    }
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

static bool validate_new_scalar_field_value(xbase::DbArea& A,
                                            int fld1,
                                            const std::string& value,
                                            std::string& err)
{
    const char t = field_type_upper(A, fld1);

    switch (t) {
        case 'D': {
            std::string norm;
            if (!normalize_date_value(value, norm)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidDateForFieldText);
                return false;
            }
            return true;
        }

        case 'L': {
            std::string norm;
            if (!normalize_logical_value(value, norm)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidLogicalForFieldText);
                return false;
            }
            return true;
        }

        case 'N': {
            std::string norm;
            if (!normalize_numeric_value(value, field_length(A, fld1), field_decimals(A, fld1), norm)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidNumericForFieldText);
                return false;
            }
            return true;
        }

        case 'F': {
            std::string norm;
            if (!normalize_numeric_value(value, field_length(A, fld1), field_decimals(A, fld1), norm)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidFloatForFieldText);
                return false;
            }
            return true;
        }

        case 'I': {
            std::int32_t tmp = 0;
            if (!parse_i32_strict(value, tmp)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidInt32ForFieldText);
                return false;
            }
            return true;
        }

        case 'B': {
            double tmp = 0.0;
            if (!parse_double_strict(value, tmp)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidDoubleForFieldText);
                return false;
            }
            return true;
        }

        case 'Y': {
            std::int64_t scaled = 0;
            if (!parse_currency_strict(value, scaled)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidCurrencyForFieldText);
                return false;
            }
            return true;
        }

        default:
            return true;
    }
}

// Parse: <field> WITH <value>[, <field> WITH <value>]...
static bool parse_assignments(std::istringstream& iss,
                              xbase::DbArea& A,
                              std::vector<FieldUpdate>& out,
                              std::string& err)
{
    out.clear();

    while (true) {
        iss >> std::ws;
        if (!iss.good()) break;

        std::string fieldTok;
        if (!(iss >> fieldTok)) break;

        if (up_copy(fieldTok) == "FIELD") {
            if (!(iss >> fieldTok)) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiExpectedFieldAfterFieldText);
                return false;
            }
        }

        std::string withTok;
        if (!(iss >> withTok) || up_copy(withTok) != "WITH") {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiExpectedWithAfterFieldText);
            return false;
        }

        std::string value;
        std::getline(iss, value, ',');
        trim_inplace(value);
        if (value.empty()) {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiEmptyValueText);
            return false;
        }

        trim_inplace(fieldTok);

        int dummy = 0;
        if (!try_parse_int(fieldTok, dummy)) {
            if (fieldTok.empty() || !is_ident_start(fieldTok[0])) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidFieldTokenText,
                    {{"field", fieldTok}});
                return false;
            }
            for (char c : fieldTok) {
                if (!is_ident_char(c)) {
                    err = cli::cmdout::message_text(
                        dottalk::helpdata::MessageId::ReplaceMultiInvalidFieldTokenText,
                        {{"field", fieldTok}});
                    return false;
                }
            }
        }

        int fld = 0;
        if (!try_parse_int(fieldTok, fld)) fld = resolve_field_index_by_name_ci(A, fieldTok);
        if (fld <= 0) {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiUnknownFieldText,
                {{"field", fieldTok}});
            return false;
        }

        out.push_back({fieldTok, value});

        if (!iss.good()) break;
    }

    if (out.empty()) {
        err = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::ReplaceMultiNoAssignmentsText);
        return false;
    }
    return true;
}


static bool is_replace_multi_usage_request(const std::string& raw)
{
    std::string t = up_copy(trim_copy(raw));

    if (t == "MULTIREP") {
        return true;
    }

    // Dispatch normally passes only the tail ("USAGE"), but accept full raw
    // input too ("MULTIREP USAGE").
    if (t.rfind("MULTIREP ", 0) == 0) {
        t = trim_copy(t.substr(9));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_replace_multi_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ReplaceMultiUsageText);
}

} // namespace

// AIF-151 -- structures and steps shared by the BUFFERED and DIRECT-WRITE paths.
//
// Hoisted out of cmd_REPLACE_MULTI so that adding buffering did not fork the
// validation or the memo write into a second copy. This file already carries
// the scar of the other kind: its index maintenance MIRRORS
// DbArea::replaceFieldStored rather than calling it, and when the trigger fire
// was later added to the original the mirror did not inherit it.
struct Resolved {
    int field1{};
    std::string value;       // raw user value
    std::string storeValue;  // normalized value actually written or buffered
    std::string before;
    bool isMemo{false};
};

// Type, width and decimals validation plus canonicalisation. Memo fields are
// skipped here and handled by multirep_take_memo_handle.
static bool multirep_validate_and_normalize(xbase::DbArea& A,
                                            std::vector<Resolved>& resolved,
                                            std::string& local_error)
{
    for (auto& r : resolved) {
        if (r.isMemo) {
            r.storeValue = r.value;
            continue;
        }

        if (!validate_new_scalar_field_value(A, r.field1, r.value, local_error)) {
            return false;
        }

        r.storeValue = r.value;

        const char t = field_type_upper(A, r.field1);

        if (t == 'D') {
            std::string norm;
            if (!normalize_date_value(r.value, norm)) {
                local_error = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidDateForFieldText);
                return false;
            }
            r.storeValue = norm;
        }
        else if (t == 'L') {
            std::string norm;
            if (!normalize_logical_value(r.value, norm)) {
                local_error = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidLogicalForFieldText);
                return false;
            }
            r.storeValue = norm;
        }
        else if (t == 'N') {
            std::string norm;
            if (!normalize_numeric_value(r.value,
                                         field_length(A, r.field1),
                                         field_decimals(A, r.field1),
                                         norm)) {
                local_error = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidNumericForFieldText);
                return false;
            }
            r.storeValue = norm;
        }
        else if (t == 'F') {
            std::string norm;
            if (!normalize_numeric_value(r.value,
                                         field_length(A, r.field1),
                                         field_decimals(A, r.field1),
                                         norm)) {
                local_error = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiInvalidFloatForFieldText);
                return false;
            }
            r.storeValue = norm;
        }

        std::string normCur;
        std::string curErr;
        if (!cli_currency::validate_and_normalize_currency_pair_field(
                A, r.field1, r.storeValue, normCur, curErr)) {
            local_error = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiDetailText,
                {{"detail", curErr + "."}});
            return false;
        }
        r.storeValue = normCur;
    }
    return true;
}

// Write a memo field's PAYLOAD and hand back the HANDLE that goes in the record.
//
// BUFFERING DEFERS THE POINTER, NOT THE PAYLOAD. The memo object is written and
// durable the moment this runs; only the reference to it waits for COMMIT. So a
// ROLLBACK of a buffered memo edit leaves an orphan object -- named, detectable
// and reclaimable by MEMO GC, which reports reclaimable_bytes before touching
// anything, not silent loss.
//
// This matches REPLACE, which builds its stored memo value at
// cmd_replace.cpp:928, BEFORE its buffering branch at :946. Matching it is
// deliberate: two commands with different memo semantics under one TABLE ON
// would be worse than the orphan.
//
// KNOWN EDGE, not solved here and shared with REPLACE: old_ref is read from the
// CURRENT RECORD, so a second buffered edit to the same memo field before
// COMMIT updates the committed object rather than the one the first edit made.
static bool multirep_take_memo_handle(xbase::DbArea& A,
                                      Resolved& r,
                                      std::string& local_error)
{
    auto* store = cli_memo::memo_store_for(A);
    if (!store || !store->is_open()) {
        local_error = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::ReplaceMultiMemoBackendNotAttachedText);
        return false;
    }

    dottalk::memo::MemoRef old_ref{};
    try {
        old_ref.token = A.get(r.field1);
    } catch (...) {
        old_ref.token.clear();
    }

    dottalk::memo::MemoPutResult mr =
        store->is_null_ref(old_ref)
            ? store->put_text(r.value)
            : store->update_text(old_ref, r.value);

    if (!mr.ok) {
        local_error = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::ReplaceMultiMemoWriteFailedText,
            {{"detail", mr.error.empty() ? std::string() : " (" + mr.error + ")"}});
        return false;
    }

    r.storeValue = mr.ref.token;
    return true;
}

bool cmd_REPLACE_MULTI(xbase::DbArea& A,
                       const std::vector<FieldUpdate>& updates,
                       std::string* error)
{
    if (!A.isOpen()) {
        if (error) {
            *error = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiNoFileOpenText);
        }
        return false;
    }

    const std::uint64_t rn = A.recno64();
    if (rn == 0) {
        if (error) {
            *error = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiNoCurrentRecordText);
        }
        return false;
    }

    std::vector<Resolved> resolved;
    resolved.reserve(updates.size());

    for (const auto& u : updates) {
        int fld = 0;
        if (!try_parse_int(u.name, fld)) {
            fld = resolve_field_index_by_name_ci(A, u.name);
        }
        if (fld <= 0) {
            if (error) {
                *error = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::ReplaceMultiUnknownFieldText,
                    {{"field", u.name}});
            }
            return false;
        }

        Resolved r;
        r.field1 = fld;
        r.value = rhs_to_user_value(A, u.value);
        r.storeValue = r.value;
        r.isMemo = is_memo_field_type(A, fld);
        try { r.before = A.get(fld); } catch (...) { r.before.clear(); }
        resolved.push_back(std::move(r));
    }

    // ---------------------------------------------------------------------
    // AIF-151 -- BUFFERED PATH. Taken before the record lock ON PURPOSE.
    //
    // COMMIT's own contract says "TABLE ON buffers changes; no OS locking should
    // occur during REPLACE/DELETE" -- the edit stages, it does not reach the DBF.
    // MULTIREP used to ignore TABLE ON entirely and lock-and-write regardless,
    // so a MULTIREP inside a buffered session was durable before COMMIT ran and
    // ROLLBACK did not undo it.
    //
    // ONE PHYSICAL WRITE SURVIVES THE UPGRADE. add_change stages ONE FIELD per
    // call, so N fields become N entries -- and cmd_commit.cpp's
    // aggregate_for_recno folds every entry for a recno back into ONE set()
    // loop and ONE writeCurrent(). MULTIREP's defining property is preserved at
    // commit time rather than at statement time.
    //
    // And it is now visible to triggers. Staged edits arrive at commit entry,
    // where AIF-087's BEFORE phase asks once per record with the whole
    // changed-field set -- which is exactly why M2a made the fire unit the
    // physical write rather than the field.
    const int area0 = cli::slot_of_area(&A);
    if (area0 >= 0 && dottalk::table::is_enabled(area0)) {
        std::string buf_error;

        if (!multirep_validate_and_normalize(A, resolved, buf_error)) {
            if (error) *error = buf_error;
            return false;
        }

        // Memo payloads are written NOW and only the handle is buffered; see
        // multirep_take_memo_handle for why, and for what ROLLBACK leaves behind.
        for (auto& r : resolved) {
            if (!r.isMemo) continue;
            if (!multirep_take_memo_handle(A, r, buf_error)) {
                if (error) *error = buf_error;
                return false;
            }
        }

        auto& tb = dottalk::table::get_tb(area0);
        for (const auto& r : resolved) {
            std::uint64_t field_mask[dottalk::table::kWords]{};
            const int fldIndex0 = r.field1 - 1;
            const int word = fldIndex0 / 64;
            const int bit  = fldIndex0 % 64;
            if (word >= 0 && word < dottalk::table::kWords) {
                field_mask[word] |= (std::uint64_t{1} << bit);
            }

            const int je_priority = tb.add_change(
                rn, dottalk::table::CHANGE_UPDATE, field_mask, r.field1, r.storeValue);

            // Write-ahead redo, only under RamJournal. Journal the exact buffered
            // edit with the priority add_change assigned, so history mode keeps
            // every retained edit per field rather than a last-write-wins snapshot.
            if (dottalk::table::is_persistent_enabled(area0)) {
                dottalk::table::ChangeEntry je;
                je.recno = rn;
                je.dirty_flags = dottalk::table::CHANGE_UPDATE;
                je.priority = je_priority;
                je.new_values[r.field1] = r.storeValue;
                (void)dottalk::table::journal_note_change(area0, je);
            }

            dottalk::table::mark_stale_field(area0, r.field1);
        }

        if (!dottalk::table::is_dirty(area0)) dottalk::table::set_dirty(area0, true);
        return true;
    }
    // ---------------------------------------------------------------------

    std::string lock_err;
    if (!xbase::locks::try_lock_record(A, rn, &lock_err)) {
        if (error) {
            *error = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiRecordLockedText,
                {{"detail", lock_err}});
        }
        return false;
    }

    // Canonical direct-write index mutation seam:
    // capture all currently active tag keys before the multi-field record edit,
    // perform one DBF write, then capture/apply the after snapshot once.
    // This preserves REPLACE_MULTI's one-lock / one-write design while avoiding
    // the older simple field-name == tag-name maintenance path.
#if DOTTALK_HAS_XINDEX
    xindex::IndexManager::DeleteSnapshot before_snap;
    bool before_snap_ok = false;
    try {
        before_snap = xindex::ensure_manager(A).capture_delete_snapshot_for_current_record();
        before_snap_ok = true;
    } catch (...) {
        before_snap_ok = false;
    }
#endif

    bool ok = true;
    std::string local_error;

    try {
        // Pass 1: validate everything and compute normalized store values.
        if (!multirep_validate_and_normalize(A, resolved, local_error)) ok = false;

        if (ok) {
            // Pass 2: apply all changes to the in-memory current record.
            for (auto& r : resolved) {
                if (r.isMemo) {
                    if (!multirep_take_memo_handle(A, r, local_error)) {
                        ok = false;
                        break;
                    }

                    if (!A.set(r.field1, r.storeValue)) {
                        local_error = cli::cmdout::message_text(
                            dottalk::helpdata::MessageId::ReplaceMultiStoreMemoTokenFailedText);
                        ok = false;
                        break;
                    }
                } else {
                    if (!A.set(r.field1, r.storeValue)) {
                        local_error = cli::cmdout::message_text(
                            dottalk::helpdata::MessageId::ReplaceMultiFieldSetFailedText);
                        ok = false;
                        break;
                    }
                }
            }
        }

        if (ok) ok = A.writeCurrent();
    } catch (...) {
        ok = false;
        if (local_error.empty()) {
            local_error = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::ReplaceMultiExceptionDuringWriteText);
        }
    }

    xbase::locks::unlock_record(A, rn);

    if (!ok) {
        if (error) {
            *error = local_error.empty()
                ? cli::cmdout::message_text(dottalk::helpdata::MessageId::ReplaceMultiWriteFailedText)
                : local_error;
        }
        return false;
    }

    // Direct-write CRUD index maintenance through the canonical multi-tag
    // snapshot path. This mirrors DbArea::replaceFieldStored(), but keeps
    // REPLACE_MULTI's single lock and single physical write.
    std::vector<int> changed_fields;
    changed_fields.reserve(resolved.size());

    for (const auto& r : resolved) {
        std::string after;
        try { after = A.get(r.field1); } catch (...) { after.clear(); }

        if (!values_equal_for_stale_check(r.before, after)) {
            changed_fields.push_back(r.field1);
        }
    }

    bool idx_ok = true;

    if (!changed_fields.empty()) {
#if DOTTALK_HAS_XINDEX
        xindex::IndexManager::DeleteSnapshot after_snap;
        bool after_snap_ok = false;

        try {
            after_snap = xindex::ensure_manager(A).capture_delete_snapshot_for_current_record();
            after_snap_ok = true;
        } catch (...) {
            after_snap_ok = false;
        }

        if (before_snap_ok && after_snap_ok) {
            if (!before_snap.empty() || !after_snap.empty()) {
                try {
                    idx_ok = xindex::ensure_manager(A).apply_replace_snapshot(
                        before_snap,
                        after_snap,
                        static_cast<xindex::RecNo>(rn));
                } catch (...) {
                    idx_ok = false;
                }
            }
        } else {
            idx_ok = false;
        }
#endif
    }

    if (!idx_ok) {
        // AIF-151: marks stale on THE AREA BEING WRITTEN, not on whatever area
        // happens to be current. This read `eng->currentArea()`, which is the
        // same slot only when A is the current area -- and the programmatic
        // overload above takes ANY DbArea&. On a non-current area that marked
        // the wrong area's field: the index that actually failed maintenance
        // read clean, and an untouched one read stale. Surfaced by a C4456
        // shadow warning when the buffered path introduced a second, correct
        // derivation of the same fact; there is now one.
        if (area0 >= 0) {
            for (const int field1 : changed_fields) {
                dottalk::table::mark_stale_field(area0, field1);
            }
        }
    }

    return true;
}

void cmd_REPLACE_MULTI(xbase::DbArea& A, std::istringstream& iss)
{
    const std::string raw_args = iss.str();
    if (trim_copy(raw_args).empty() || is_replace_multi_usage_request(raw_args)) {
        print_replace_multi_usage();
        return;
    }

    std::string err;
    std::vector<FieldUpdate> updates;

    if (!parse_assignments(iss, A, updates, err)) {
        cli::cmdout::print_line(err);
        print_replace_multi_usage();
        return;
    }

    if (!cmd_REPLACE_MULTI(A, updates, &err)) {
        cli::cmdout::print_prefixed_message(
            "MULTIREP",
            dottalk::helpdata::MessageId::ReplaceMultiDetailText,
            {{"detail", err}});
        return;
    }

    cli::cmdout::print_prefixed_message(
        "MULTIREP",
        dottalk::helpdata::MessageId::ReplaceMultiUpdatedFieldsText,
        {{"count", std::to_string(updates.size())}});
}
