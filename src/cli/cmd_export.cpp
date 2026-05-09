// src/cli/cmd_export.cpp
// @dottalk.usage v1
// owner: DOT|EXPORT
// command: EXPORT
// category: io
// status: supported
// noargs: usage
// effect: export
// mutates: filesystem
// usage-access: EXPORT USAGE
// summary:
//   Export the current DBF rowset to a delimited file.
//
// usage:
//   EXPORT USAGE
//   EXPORT [TO] <file> [CSV|PIPE]
//   EXPORT <table> TO <file> [CSV|PIPE]
//
// notes:
//   EXPORT requires an open table except for EXPORT USAGE.
//   EXPORT [TO] <file> writes the current table to the named file.
//   EXPORT <table> TO <file> accepts a legacy table token but exports the current area.
//   CSV is the default format; PIPE uses a pipe delimiter.
//   A missing extension is added automatically (.csv for CSV, .txt for PIPE).
//   EXPORT writes a header row.
//   EXPORT honors the active SET FILTER for the current area.
//   EXPORT reads records in physical table order.
//   EXPORT may report file/write errors and still emit a summary when appropriate.
//
// risk:
//   reads_table_records: yes
//   writes_files: yes
//   overwrites_output_file: yes if target exists
//   mutates_table_data: no
//   mutates_cursor: yes, scans physical records
//
// related:
//   DUMP
//   LIST
//   COPY TO
//   DDL
//

#include <cctype>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "textio.hpp"
#include "filters/filter_registry.hpp"

using namespace xbase;

namespace {

static std::string export_trim(std::string s)
{
    return textio::trim(std::move(s));
}

static std::string export_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_export_usage_request(std::string raw)
{
    std::string t = export_upper(export_trim(std::move(raw)));

    // Some dispatch paths pass the whole raw line ("EXPORT USAGE")
    // instead of only the command tail ("USAGE"). Accept both.
    if (t.rfind("EXPORT ", 0) == 0) {
        t = export_upper(export_trim(t.substr(7)));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_export_usage()
{
    std::cout
        << "Usage:\n"
        << "  EXPORT USAGE\n"
        << "  EXPORT [TO] <file> [CSV|PIPE]\n"
        << "  EXPORT <table> TO <file> [CSV|PIPE]\n"
        << "Notes:\n"
        << "  - EXPORT writes the current table as CSV by default.\n"
        << "  - PIPE uses | as the delimiter.\n"
        << "  - A missing extension is added automatically (.csv for CSV, .txt for PIPE).\n"
        << "  - EXPORT honors the active SET FILTER for the current area.\n"
        << "  - EXPORT requires an open table except for EXPORT USAGE.\n";
}

static bool ieq_to(const std::string& s) {
    if (s.size() != 2) return false;
    return (s[0] == 'T' || s[0] == 't') && (s[1] == 'O' || s[1] == 'o');
}

static bool has_any_extension(const std::string& path) {
    const std::size_t slash = path.find_last_of("/\\");
    const std::size_t dot = path.find_last_of('.');
    return dot != std::string::npos && (slash == std::string::npos || dot > slash);
}

static void add_default_export_extension(std::string& dest, char delimiter) {
    if (has_any_extension(dest)) return;
    dest += (delimiter == '|') ? ".txt" : ".csv";
}

static void write_delimited_cell(std::ostream& out, const std::string& value, char delimiter)
{
    bool quote = false;
    for (char c : value) {
        if (c == delimiter || c == '"' || c == '\r' || c == '\n') {
            quote = true;
            break;
        }
    }

    if (!quote) {
        out << value;
        return;
    }

    out << '"';
    for (char c : value) {
        if (c == '"') out << "\"\"";
        else out << c;
    }
    out << '"';
}

static void write_delimited_row(std::ostream& out, const std::vector<std::string>& cells, char delimiter)
{
    for (std::size_t i = 0; i < cells.size(); ++i) {
        if (i) out << delimiter;
        write_delimited_cell(out, cells[i], delimiter);
    }
    out << "\n";
}

} // namespace

void cmd_EXPORT(DbArea& a, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_export_usage_request(raw_args)) {
        print_export_usage();
        return;
    }

    if (!a.isOpen()) {
        std::cout << "No file open\n";
        return;
    }

    // Accepted forms:
    //   EXPORT <file> [CSV|PIPE]
    //   EXPORT TO <file> [CSV|PIPE]
    //   EXPORT <table> TO <file> [CSV|PIPE]
    //
    // Canary fix: "EXPORT TO tmp\\x PIPE" must not treat literal TO as
    // the filename. Parse optional TO and format keywords before selecting dest.
    std::vector<std::string> toks;
    for (std::string t; iss >> t; ) toks.push_back(t);

    char delimiter = ',';
    if (!toks.empty()) {
        const std::string last = export_upper(toks.back());
        if (last == "CSV") {
            delimiter = ',';
            toks.pop_back();
        } else if (last == "PIPE") {
            delimiter = '|';
            toks.pop_back();
        }
    }

    std::string dest;
    if (toks.empty()) {
        print_export_usage();
        return;
    }

    if (ieq_to(toks[0])) {
        // EXPORT TO <file>
        if (toks.size() != 2 || toks[1].empty()) {
            print_export_usage();
            return;
        }
        dest = toks[1];
    } else if (toks.size() >= 3 && ieq_to(toks[1])) {
        // EXPORT <table> TO <file> -- legacy table token is accepted but
        // the current area remains the exported source.
        if (toks.size() != 3 || toks[2].empty()) {
            print_export_usage();
            return;
        }
        dest = toks[2];
    } else if (toks.size() == 1) {
        // EXPORT <file>
        dest = toks[0];
    } else {
        print_export_usage();
        return;
    }

    add_default_export_extension(dest, delimiter);

    std::ofstream out(dest, std::ios::binary);
    if (!out) {
        std::cout << "Unable to open " << dest << " for write\n";
        return;
    }

    const auto& fields = a.fields();

    std::vector<std::string> header;
    header.reserve(fields.size());
    for (const auto& f : fields) header.push_back(f.name);
    write_delimited_row(out, header, delimiter);

    std::size_t exported = 0;
    const int nrecs = a.recCount();

    for (int recno = 1; recno <= nrecs; ++recno) {
        try {
            (void)a.gotoRec(recno);
            (void)a.readCurrent();
        } catch (...) {
            continue;
        }

        // Honor persistent SET FILTER. Null FOR AST means no additional ad-hoc predicate.
        if (!filter::visible(&a, nullptr)) continue;

        std::vector<std::string> row;
        row.reserve(fields.size());
        for (std::size_t i = 0; i < fields.size(); ++i) {
            row.push_back(a.get(static_cast<int>(i + 1)));
        }
        write_delimited_row(out, row, delimiter);
        ++exported;
    }

    if (!out) {
        std::cout << "ERROR: write failed while exporting " << dest << "\n";
    }

    std::cout << "Exported " << exported << " records to " << dest << "\n";
}
