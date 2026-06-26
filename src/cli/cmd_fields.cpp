// @dottalk.usage v1
// owner: DOT|FIELDS
// command: FIELDS
// category: report
// status: supported
// noargs: report
// effect: report
// mutates: none
// usage-access: FIELDS USAGE
// summary:
//   Report the field list for the current work area with aligned field number,
//   name, type, length, and decimal columns.
//
// usage:
//   FIELDS
//   FIELDS USAGE
//
// notes:
//   FIELDS with no arguments reports field metadata.
//   FIELDS is read-only and does not mutate table data or cursor position.
//   If no fields are available, FIELDS prints a no-fields message.
//
// risk:
//   reads_schema: yes
//   mutates_table_data: no
//   mutates_cursor: no
//
// related:
//   STRUCT
//   FIELDMGR
//   DUMP
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include <cctype>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
#include <algorithm>
#include <sstream>

using xbase::DbArea;
using xbase::FieldDef;

namespace {


static std::string fields_trim(std::string s) {
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) s.erase(s.begin());
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}

static std::string fields_upper(std::string s) {
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static bool is_fields_usage_request(const std::string& raw) {
    std::string t = fields_upper(fields_trim(raw));
    if (t.rfind("FIELDS ", 0) == 0) {
        t = fields_upper(fields_trim(t.substr(7)));
    }
    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_fields_usage() {
    cli::cmdout::print_message(dottalk::helpdata::MessageId::FieldsUsageText);
}

// compute the width in digits for numbering column (?#?)
static int digits(std::size_t n) {
    int d = 1;
    while (n >= 10) { n /= 10; ++d; }
    return d;
}

} // namespace

// FIELDS
// Shows the field list with aligned columns.
void cmd_FIELDS(DbArea& area, std::istringstream& args)
{
    const std::string raw_args = args.str();
    if (is_fields_usage_request(raw_args)) {
        print_fields_usage();
        return;
    }

    const auto& defs = area.fields();
    const std::size_t n = static_cast<std::size_t>(area.fieldCount());

    if (n == 0) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::FieldsNoFieldsText);
        return;
    }

    // Column widths
    int w_idx  = std::max(1, digits(n));                // '#'
    int w_name = 4;                                     // 'Name'
    int w_type = 4;                                     // 'Type'
    int w_len  = 3;
    int w_dec  = 3;                                     // 'Len'

    for (const FieldDef& f : defs) {
        w_name = std::max<int>(w_name, static_cast<int>(f.name.size()));
        w_type = std::max<int>(w_type, 1);              // single letter
        w_len  = std::max<int>(w_len,  (f.length > 0 ? (f.length < 10 ? 1 : (f.length < 100 ? 2 : 3)) : 1));
    }

    // Header
    std::cout
        << std::right << std::setw(w_idx)  << "#"  << ' '
        << std::left  << std::setw(w_name) << "Name" << ' '
        << std::left  << std::setw(w_type) << "Type" << ' '
        << std::right << std::setw(w_len)  << "Len"  << "\n";

    // Ruler
    auto dash = [](int w){ for (int i=0;i<w;++i) std::cout << '-'; };
    dash(w_idx);  std::cout << ' ';
    dash(w_name); std::cout << ' ';
    dash(w_type); std::cout << ' ';
    dash(w_len);  std::cout << ' '; dash(w_dec);  std::cout << "\n";

    // Rows
    for (std::size_t i = 0; i < n; ++i) {
        const FieldDef& f = defs[i];
        std::cout
            << std::right << std::setw(w_idx)  << (i+1) << ' '
            << std::left  << std::setw(w_name) << f.name << ' '
            << std::left  << std::setw(w_type) << f.type << ' '
            << std::right << std::setw(w_len)  << static_cast<int>(f.length) << ' '
            << std::right << std::setw(w_dec)  << static_cast<int>(f.decimals)
            << "\n";
    }
}



