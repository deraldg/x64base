// @dottalk.usage v1
// owner: DOT|IMPORT
// command: IMPORT
// category: io
// status: supported
// noargs: usage
// effect: import
// mutates: table-data cursor
// usage-access: IMPORT USAGE
// summary:
//   Import records from a CSV file into the current open table by matching CSV
//   headers to field names case-insensitively.
//
// usage:
//   IMPORT USAGE
//   IMPORT <csvfile>
//
// notes:
//   IMPORT requires an open table except for IMPORT USAGE.
//   IMPORT appends .csv to the file name when the extension is omitted.
//   The first CSV row is interpreted as headers.
//   Headers are mapped to current table fields case-insensitively.
//   Each data row appends a blank record, sets mapped fields, and writes the record.
//   Unmapped CSV columns are ignored.
//   IMPORT mutates table data by appending records.
//
// risk:
//   reads_files: yes
//   appends_records: yes
//   writes_table_data: yes
//   mutates_cursor: yes
//   requires_open_table: yes except usage
//
// related:
//   EXPORT
//   APPEND
//   APPEND_BLANK
//   DDL
//

#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <vector>
#include <cstdint>
#include <string_view>
#include "xbase.hpp"
#include "cli/memo_field_store.hpp"
#include "xbase_64.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"
#include "csv.hpp"
#include "textio.hpp"
#include "predicates.hpp"

using namespace xbase;


namespace {
static std::string import_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_import_usage_request(std::string raw)
{
    std::string t = import_upper(textio::trim(std::move(raw)));
    if (t.rfind("IMPORT ", 0) == 0) {
        t = import_upper(textio::trim(t.substr(7)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void strip_import_trailing_cr(std::string& line)
{
    if (!line.empty() && line.back() == '\r') {
        line.pop_back();
    }
}

static void strip_import_utf8_bom(std::string& s)
{
    if (s.size() >= 3 &&
        static_cast<unsigned char>(s[0]) == 0xEF &&
        static_cast<unsigned char>(s[1]) == 0xBB &&
        static_cast<unsigned char>(s[2]) == 0xBF) {
        s.erase(0, 3);
    }
}

static std::vector<std::string> split_import_csv_record(std::string line, bool stripFirstColumnBom)
{
    strip_import_trailing_cr(line);
    std::vector<std::string> cols = csv::split_line(line);
    if (stripFirstColumnBom && !cols.empty()) {
        strip_import_utf8_bom(cols[0]);
    }
    return cols;
}


static void print_import_usage()
{
    std::cout
        << "Usage:\n"
        << "  IMPORT USAGE\n"
        << "  IMPORT <csvfile>\n"
        << "Notes:\n"
        << "  - IMPORT requires an open table except for IMPORT USAGE.\n"
        << "  - CSV headers are matched to field names case-insensitively.\n"
        << "  - IMPORT appends records to the current table.\n";
}
} // namespace

void cmd_IMPORT(DbArea& a, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_import_usage_request(raw_args)) {
        print_import_usage();
        return;
    }

    if (!a.isOpen()) { std::cout << "No file open\n"; return; }
    std::string csvfile; iss >> csvfile;
    if (csvfile.empty()) { print_import_usage(); return; }
    if (!textio::ends_with_ci(csvfile, ".csv")) csvfile += ".csv";

    std::ifstream in(csvfile, std::ios::binary);
    if (!in) { std::cout << "Cannot open " << csvfile << " for read.\n"; return; }

    std::string record;
    if (!csv::read_record(in, record)) { std::cout << "Empty CSV.\n"; return; }
    auto headers = split_import_csv_record(record, true);

    std::vector<int> col2fld; col2fld.reserve(headers.size());
    for (auto &h : headers)
        col2fld.push_back(predicates::field_index_ci(a, textio::trim(h)));

    int imported = 0;
    while (csv::read_record(in, record)) {
        auto cols = split_import_csv_record(record, false);
        if (cols.empty()) continue;
        if (!a.appendBlank()) { std::cout << "Append failed.\n"; break; }
        for (size_t c = 0; c < cols.size() && c < col2fld.size(); ++c) {
            int fi = col2fld[c];
            if (fi > 0) {
                std::string import_err;
                if (!dottalk::cli::memo_field_store::store_user_value(a, fi, cols[c], import_err)) {
                    std::cout << "IMPORT: " << import_err
                              << " at rec " << a.recno()
                              << ", column " << (c + 1) << ".\n";
                    break;
                }
            }
        }
        if (!a.writeCurrent()) { std::cout << "Write failed at rec " << a.recno() << "\n"; break; }
        ++imported;
    }
    std::cout << "Imported " << imported << " records from " << csvfile << "\n";
}



