// @dottalk.usage v1
// owner: DOT|TUPVALIDATE
// command: TUPVALIDATE
// category: tuple
// status: supported
// noargs: report
// effect: validate
// mutates: cursor
// usage-access: TUPVALIDATE USAGE
// summary:
//   Validate tuple graph rows for the current table using the tuple graph cursor
//   and relation-aware tuple validation layer.
//
// usage:
//   TUPVALIDATE
//   TUPVALIDATE USAGE
//   TUPVALIDATE *
//   TUPVALIDATE <tuple-spec>
//   TUPVALIDATE * FOR <expr>
//   TUPVALIDATE * FOR <expr> MAX <n>
//   TUPVALIDATE * FOR <expr> TRACE
//
// examples:
//   TUPVALIDATE LNAME,FNAME
//   TUPVALIDATE STUDENTS.*,MAJORS.* FOR MAJORS.NAME = CS
//
// notes:
//   TUPVALIDATE with no arguments validates the default star tuple spec.
//   TUPVALIDATE USAGE prints usage and does not require an open table.
//   The tuple graph cursor uses active ordering and relation context.
//   Validation checks tuple cells against their source work areas when available.
//   Cursor restoration is reported after validation.
//   TUPVALIDATE is read-only for table data but moves cursors during validation.
//
// risk:
//   reads_table_records: yes
//   reads_relation_context: yes
//   mutates_cursor: temporary during validation
//   cursor_restore: best effort
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   TUPLE
//   TUPTALK
//   ERSATZ
//   REL
//

#include "cmd_tupvalidate.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "tuple/tuple_command_spec.hpp"
#include "tuple/tuple_graph_cursor.hpp"
#include "tuple/tuple_validate.hpp"

namespace {

static std::string table_name(const xbase::DbArea& A) {
    try {
        const std::string logical = A.logicalName();
        if (!logical.empty()) return logical;
    } catch (...) {}
    try {
        const std::string base = A.dbfBasename();
        if (!base.empty()) return base;
    } catch (...) {}
    try { return A.name(); } catch (...) {}
    return "<table>";
}

static int safe_recno(const xbase::DbArea& A) {
    try { return static_cast<int>(A.recno()); } catch (...) { return 0; }
}


static std::string join_recnos(const std::vector<int>& recnos) {
    if (recnos.empty()) return "";
    std::ostringstream oss;
    for (std::size_t i = 0; i < recnos.size(); ++i) {
        if (i) oss << ',';
        oss << recnos[i];
    }
    return oss.str();
}

static void print_root_accounting(const dottalk::tupleaugment::TupleGraphCursorStats& st) {
    std::cout << "Root input  : table " << st.root_table_rec_count
              << ", candidates " << st.root_candidate_recnos
              << ", collected " << st.root_recnos_collected << "\n";

    if (st.root_skipped_read || st.root_skipped_deleted || st.root_skipped_out_of_range) {
        std::cout << "Root skips  : read " << st.root_skipped_read
                  << ", deleted " << st.root_skipped_deleted
                  << ", out-of-range " << st.root_skipped_out_of_range << "\n";
        if (!st.root_skipped_read_recnos.empty()) {
            std::cout << "  skipped read recnos      : " << join_recnos(st.root_skipped_read_recnos) << "\n";
        }
        if (!st.root_skipped_deleted_recnos.empty()) {
            std::cout << "  skipped deleted recnos   : " << join_recnos(st.root_skipped_deleted_recnos) << "\n";
        }
        if (!st.root_skipped_out_of_range_recnos.empty()) {
            std::cout << "  skipped out-of-range recnos: " << join_recnos(st.root_skipped_out_of_range_recnos) << "\n";
        }
    }
}

static void print_usage() {
    std::cout << "Usage:\n"
              << "  TUPVALIDATE\n"
              << "  TUPVALIDATE USAGE\n"
              << "  TUPVALIDATE *\n"
              << "  TUPVALIDATE <tuple-spec>\n"
              << "  TUPVALIDATE * FOR <expr>\n"
              << "  TUPVALIDATE * FOR <expr> MAX <n>\n"
              << "  TUPVALIDATE * FOR <expr> TRACE\n"
              << "Examples:\n"
              << "  TUPVALIDATE LNAME,FNAME\n"
              << "  TUPVALIDATE STUDENTS.*,MAJORS.* FOR MAJORS.NAME = \"CS\"\n";
}

static std::string tupvalidate_trim(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string tupvalidate_up(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static bool is_tupvalidate_usage_request(const std::string& raw) {
    std::string t = tupvalidate_up(tupvalidate_trim(raw));
    if (t.rfind("TUPVALIDATE ", 0) == 0) {
        t = tupvalidate_up(tupvalidate_trim(t.substr(12)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

} // namespace

void cmd_TUPVALIDATE(xbase::DbArea& A, std::istringstream& args) {
    const std::string raw_args = args.str();
    if (is_tupvalidate_usage_request(raw_args)) {
        print_usage();
        return;
    }

    try {
        if (!A.isOpen()) {
            std::cout << "TUPVALIDATE: no file open\n";
            return;
        }
    } catch (...) {
        std::cout << "TUPVALIDATE: no file open\n";
        return;
    }

    auto spec = dottalk::tupleaugment::parse_tuple_validate_spec(args);
    if (spec.help) {
        print_usage();
        return;
    }

    dottalk::tupleaugment::TupleGraphCursorOptions opt;
    opt.tuple_spec = spec.tuple_spec.empty() ? "*" : spec.tuple_spec;
    opt.for_expr = spec.for_expr;
    opt.use_active_order = true;
    opt.include_deleted = spec.include_deleted;
    opt.only_deleted = spec.only_deleted;
    opt.strict_fields = false;
    opt.header_area_prefix = true;

    std::string error;
    dottalk::tupleaugment::TupleGraphCursor cursor(A, opt);
    if (!cursor.open(error)) {
        std::cout << "TUPVALIDATE: " << (error.empty() ? "unable to open tuple graph cursor" : error) << "\n";
        return;
    }

    std::size_t rows_checked = 0;
    std::size_t cells_checked = 0;
    std::vector<dottalk::tupleaugment::TupleValidationIssue> issues;

    dottalk::TupleRow row;
    for (;;) {
        error.clear();
        if (!cursor.next(row, error)) break;
        if (!error.empty()) {
            cursor.close();
            std::cout << "TUPVALIDATE: " << error << "\n";
            return;
        }

        // validate_tuple_row is relation-aware through TupleColumn.area_slot.
        auto vr = dottalk::tupleaugment::validate_tuple_row(row, &A);
        rows_checked += vr.rows_checked;
        cells_checked += vr.cells_checked;
        issues.insert(issues.end(), vr.issues.begin(), vr.issues.end());
    }

    if (!error.empty()) {
        cursor.close();
        std::cout << "TUPVALIDATE: " << error << "\n";
        return;
    }

    cursor.close();
    const auto& st = cursor.stats();

    std::cout << "TUPVALIDATE: " << table_name(A) << "\n";
    std::cout << "Spec        : " << opt.tuple_spec << "\n";
    if (!st.for_expr.empty()) std::cout << "FOR         : " << st.for_expr << "\n";
    if (!st.order_status.empty()) std::cout << "Order       : " << st.order_status << "\n";
    if (st.first_root_recno > 0 || st.last_root_recno > 0) {
        std::cout << "Root first/last: recno " << st.first_root_recno << " / " << st.last_root_recno << "\n";
    }
    print_root_accounting(st);
    std::cout << "Root visited : " << st.root_visited << "\n";
    std::cout << "Rows checked : " << rows_checked << "\n";
    std::cout << "Cells checked: " << cells_checked << "\n";
    std::cout << "Cursor      : "
              << (st.cursors_restored ? "workspace restored" : "restore incomplete")
              << "; current recno " << safe_recno(A) << "\n";

    if (issues.empty()) {
        std::cout << "Issues      : 0\n";
        return;
    }

    std::cout << "Issues      : " << issues.size() << "\n";

    const std::size_t max_print = spec.max_issues;
    const std::size_t n = std::min<std::size_t>(issues.size(), max_print);
    for (std::size_t i = 0; i < n; ++i) {
        const auto& issue = issues[i];
        std::cout << "AREA " << issue.area_slot
                  << " RECNO " << issue.recno
                  << " FIELD " << (issue.field.empty() ? "<unknown>" : issue.field)
                  << ": " << issue.message;
        if (!issue.raw.empty()) std::cout << " [raw='" << issue.raw << "']";
        std::cout << "\n";
    }

    if (issues.size() > max_print) {
        std::cout << "... " << (issues.size() - max_print)
                  << " more issue(s) not shown\n";
    }

    if (spec.trace) {
        std::cout << "TRACE: root_visited=" << st.root_visited
                  << " emitted=" << st.tuples_emitted
                  << " cursors_restored=" << (st.cursors_restored ? "yes" : "no") << "\n";
    }
}
