#include "cmd_tupexport.hpp"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include "tuple/tuple_command_spec.hpp"
#include "tuple/tuple_graph_cursor.hpp"

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

static std::string csv_quote(const std::string& in) {
    bool need_quote = false;
    for (char c : in) {
        if (c == ',' || c == '"' || c == '\n' || c == '\r') {
            need_quote = true;
            break;
        }
    }
    if (!need_quote) return in;

    std::string out;
    out.reserve(in.size() + 2);
    out.push_back('"');
    for (char c : in) {
        if (c == '"') out += "\"\"";
        else out.push_back(c);
    }
    out.push_back('"');
    return out;
}

static void write_csv_line(std::ofstream& out, const std::vector<std::string>& vals) {
    for (std::size_t i = 0; i < vals.size(); ++i) {
        if (i) out << ',';
        out << csv_quote(vals[i]);
    }
    out << '\n';
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
    std::cout << "TUPEXPORT usage:\n"
              << "  TUPEXPORT CSV <path>\n"
              << "  TUPEXPORT CSV <path> <tuple-spec>\n"
              << "  TUPEXPORT CSV <path> FIELDS <field-list>\n"
              << "  TUPEXPORT CSV <path> * FOR <expr>\n"
              << "Examples:\n"
              << "  TUPEXPORT CSV tmp\\students.csv\n"
              << "  TUPEXPORT CSV tmp\\students_names.csv FIELDS LNAME,FNAME\n"
              << "  TUPEXPORT CSV tmp\\students_major.csv STUDENTS.*,MAJORS.* FOR MAJORS.NAME = \"CS\"\n";
}

static bool ensure_parent_dir(const std::string& path, std::string& error) {
    try {
        const std::filesystem::path p(path);
        const std::filesystem::path parent = p.parent_path();
        if (parent.empty()) return true;

        std::error_code ec;
        if (std::filesystem::exists(parent, ec)) return true;
        if (ec) {
            error = ec.message();
            return false;
        }
        if (!std::filesystem::create_directories(parent, ec) && ec) {
            error = ec.message();
            return false;
        }
        return true;
    } catch (const std::exception& ex) {
        error = ex.what();
        return false;
    } catch (...) {
        error = "unable to create parent directory";
        return false;
    }
}

static std::vector<std::string> header_values_from_row(const dottalk::TupleRow& row) {
    std::vector<std::string> out;
    out.reserve(row.columns.size());
    for (const auto& col : row.columns) out.push_back(col.name.empty() ? col.field : col.name);
    return out;
}

} // namespace

void cmd_TUPEXPORT(xbase::DbArea& A, std::istringstream& args) {
    try {
        if (!A.isOpen()) {
            std::cout << "TUPEXPORT: no file open\n";
            return;
        }
    } catch (...) {
        std::cout << "TUPEXPORT: no file open\n";
        return;
    }

    auto spec = dottalk::tupleaugment::parse_tuple_export_spec(args);
    if (spec.help) {
        print_usage();
        return;
    }

    if (spec.format != "CSV") {
        std::cout << "TUPEXPORT: unsupported format '" << spec.format << "' (CSV only for now)\n";
        return;
    }
    if (spec.path.empty()) {
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
        std::cout << "TUPEXPORT: " << (error.empty() ? "unable to open tuple graph cursor" : error) << "\n";
        return;
    }

    std::string dir_error;
    if (!ensure_parent_dir(spec.path, dir_error)) {
        cursor.close();
        std::cout << "TUPEXPORT: unable to create output directory: " << dir_error << "\n";
        return;
    }

    std::ofstream out(spec.path, std::ios::binary | std::ios::trunc);
    if (!out) {
        cursor.close();
        std::cout << "TUPEXPORT: unable to open output file: " << spec.path << "\n";
        return;
    }

    std::size_t rows_written = 0;
    bool wrote_header = false;

    dottalk::TupleRow row;
    for (;;) {
        error.clear();
        if (!cursor.next(row, error)) break;
        if (!error.empty()) {
            out.close();
            cursor.close();
            std::cout << "TUPEXPORT: " << error << "\n";
            return;
        }

        if (!wrote_header) {
            write_csv_line(out, header_values_from_row(row));
            wrote_header = true;
        }

        write_csv_line(out, row.values);
        ++rows_written;
    }

    if (!error.empty()) {
        out.close();
        cursor.close();
        std::cout << "TUPEXPORT: " << error << "\n";
        return;
    }

    out.close();
    cursor.close();
    const auto& st = cursor.stats();

    std::cout << "TUPEXPORT CSV: " << table_name(A) << "\n";
    std::cout << "File        : " << spec.path << "\n";
    std::cout << "Spec        : " << opt.tuple_spec << "\n";
    if (!st.for_expr.empty()) std::cout << "FOR         : " << st.for_expr << "\n";
    if (!st.order_status.empty()) std::cout << "Order       : " << st.order_status << "\n";
    print_root_accounting(st);
    std::cout << "Root visited: " << st.root_visited << "\n";
    std::cout << "Rows written: " << rows_written << "\n";
    if (st.first_root_recno > 0 || st.last_root_recno > 0) {
        std::cout << "Root first/last: recno " << st.first_root_recno << " / " << st.last_root_recno << "\n";
    }
    std::cout << "Cursor      : "
              << (st.cursors_restored ? "workspace restored" : "restore incomplete")
              << "; current recno " << safe_recno(A) << "\n";
}
