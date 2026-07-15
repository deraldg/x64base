// @dottalk.usage v1
// owner: DOT|AUTODBF
// command: AUTODBF
// category: io schema
// status: experimental
// noargs: usage
// effect: create import
// mutates: filesystem session schema table-data cursor
// usage-access: AUTODBF USAGE
// summary:
//   Create an X64 DBF from a CSV file and import the CSV rows into the newly
//   created table.  CSV headers may become field names; when there is no header,
//   deterministic FIELDnnn names are generated.
//
// usage:
//   AUTODBF USAGE
//   AUTODBF <table> FROM <csvfile>
//   AUTODBF X64 <table> FROM <csvfile>
//   AUTODBF <table> FROM <csvfile> HEADER
//   AUTODBF <table> FROM <csvfile> NOHEADER
//   AUTODBF <table> FROM <csvfile> AUTO
//   AUTODBF <table> FROM <csvfile> TEXTONLY
//   AUTODBF <table> FROM <csvfile> INFER
//   AUTODBF <table> FROM <csvfile> OVERWRITE
//
// notes:
//   AUTODBF defaults to X64, AUTO header detection, INFER types, comma CSV.
//   AUTO is conservative: it chooses HEADER only when the first row looks like
//   names and later data strongly indicates typed data.  Use HEADER or NOHEADER
//   to remove ambiguity.
//   Field names are normalized to command-safe x64 logical names, uniquified,
//   capped to the current x64 logical-name limit, and then passed through the
//   existing x64 descriptor fallback/mangling policy.
//   Long text is not auto-promoted to M yet; values must fit current fixed-field
//   x64base limits.  This avoids silently writing memo object id 0.
//   Existing target DBFs are not overwritten unless OVERWRITE is supplied.
//
// risk:
//   reads_files: yes
//   creates_files: yes
//   possible_overwrite: only with OVERWRITE
//   closes_current_area: yes after validation succeeds
//   opens_area: yes
//   appends_records: yes
//   writes_table_data: yes
//
// related:
//   CREATE
//   IMPORT
//   IMPORTSQL
//   SETPATH
//   STRUCT
//

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/field_name_policy.hpp"
#include "cli/command_output.hpp"
#include "csv.hpp"
#include "textio.hpp"
#include "import/import_normalize.hpp"
#include "import/import_profile.hpp"

// Optional path slot support (SETPATH). If present, resolve relative DBF paths against Slot::DBF.
#if __has_include("cli/cmd_setpath.hpp")
  #include "cli/cmd_setpath.hpp"
  #define AUTODBF_HAVE_SETPATH 1
#else
  #define AUTODBF_HAVE_SETPATH 0
#endif

#include "cli/order_state.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <limits>
#include <sstream>
#include <string>
#include <unordered_set>
#include <utility>
#include <vector>

namespace {

using xbase::DbArea;
using FieldSpec = xbase::dbf_create::FieldSpec;
using ColumnProfile = dottalkpp::import::ColumnProfile;

constexpr int AUTODBF_MAX_FIXED_WIDTH = 254;

enum class HeaderMode {
    Auto,
    Header,
    NoHeader
};

struct AutoDbfOptions {
    std::string table;
    std::string csvfile;
    HeaderMode headerMode = HeaderMode::Auto;
    bool inferTypes = true;
    bool overwrite = false;
    int maxChar = AUTODBF_MAX_FIXED_WIDTH;
};

struct CsvScan {
    bool ok = false;
    bool firstRowIsHeader = false;
    std::size_t expectedColumns = 0;
    std::size_t dataRows = 0;
    std::size_t firstBadLine = 0;
    std::size_t actualColumns = 0;
    std::string error;
    std::vector<std::string> firstRow;
    std::vector<ColumnProfile> profiles;
};

struct AutoDbfColumn {
    std::string sourceName;
    std::string logicalName;
    std::string descriptorName;
    FieldSpec spec;
};

static std::string upper(std::string s)
{
    return textio::upper(std::move(s));
}

static bool is_usage_request(std::string raw)
{
    std::string t = textio::trim_upper(std::move(raw));
    if (t.rfind("AUTODBF ", 0) == 0) {
        t = textio::trim_upper(t.substr(8));
    }
    return t.empty() || t == "USAGE" || t == "HELP" || t == "?";
}

static void print_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalUsageTitle);
    cli::cmdout::print_line("  AUTODBF USAGE");
    cli::cmdout::print_line("  " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfUsageLine));
    cli::cmdout::print_line("  " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfUsageX64Line));
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalDefaultsTitle);
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfDefaultFlavorNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfDefaultHeaderNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfDefaultInferNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfDefaultOverwriteNote));
    cli::cmdout::print_message(dottalk::helpdata::MessageId::GlobalNotesTitle);
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfCsvParserNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfLongTextRejectedNote));
    cli::cmdout::print_line("  - " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfHeaderNormalizeNote));
}

static bool parse_args(std::istringstream& iss, AutoDbfOptions& opt, std::string& err)
{
    std::string first;
    if (!(iss >> first)) {
        err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfMissingTableName);
        return false;
    }

    if (upper(first) == "X64") {
        if (!(iss >> opt.table)) {
            err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfMissingTableNameAfterX64);
            return false;
        }
    } else {
        opt.table = first;
    }

    std::string from;
    if (!(iss >> from) || upper(from) != "FROM") {
        err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfExpectedFrom);
        return false;
    }

    if (!(iss >> opt.csvfile) || opt.csvfile.empty()) {
        err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfMissingCsvFile);
        return false;
    }

    std::string tok;
    while (iss >> tok) {
        const std::string u = upper(tok);
        if (u == "HEADER") {
            opt.headerMode = HeaderMode::Header;
        } else if (u == "NOHEADER" || u == "NO_HEADER") {
            opt.headerMode = HeaderMode::NoHeader;
        } else if (u == "AUTO") {
            opt.headerMode = HeaderMode::Auto;
        } else if (u == "TEXTONLY" || u == "TEXT") {
            opt.inferTypes = false;
        } else if (u == "INFER") {
            opt.inferTypes = true;
        } else if (u == "OVERWRITE") {
            opt.overwrite = true;
        } else if (u == "MAXCHAR") {
            std::string n;
            if (!(iss >> n)) {
                err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfMaxCharRequiresValue);
                return false;
            }
            try {
                opt.maxChar = std::stoi(n);
            } catch (...) {
                err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfInvalidMaxCharValue);
                return false;
            }
            if (opt.maxChar < 1 || opt.maxChar > AUTODBF_MAX_FIXED_WIDTH) {
                err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfMaxCharRange);
                return false;
            }
        } else {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfUnknownOption,
                {{"option", tok}});
            return false;
        }
    }

    return true;
}

static inline std::string path_to_string(const std::filesystem::path& p)
{
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static inline std::filesystem::path dbf_slot_root_fallback()
{
#if AUTODBF_HAVE_SETPATH
    try { return dottalk::paths::get_slot(dottalk::paths::Slot::DBF); } catch (...) {}
#endif
    return std::filesystem::current_path();
}

static inline std::filesystem::path resolve_dbf_slot_path(std::filesystem::path p)
{
    if (p.empty()) return p;
    if (p.is_absolute()) return p;
    return dbf_slot_root_fallback() / p;
}

static void strip_trailing_cr(std::string& line)
{
    if (!line.empty() && line.back() == '\r') line.pop_back();
}

static void strip_utf8_bom(std::string& s)
{
    if (s.size() >= 3 &&
        static_cast<unsigned char>(s[0]) == 0xEF &&
        static_cast<unsigned char>(s[1]) == 0xBB &&
        static_cast<unsigned char>(s[2]) == 0xBF) {
        s.erase(0, 3);
    }
}

static std::vector<std::string> split_csv_record(std::string line)
{
    strip_trailing_cr(line);
    std::vector<std::string> cols = csv::split_line(line);
    if (!cols.empty()) strip_utf8_bom(cols[0]);
    return cols;
}

static bool is_blank_line(const std::string& line)
{
    return textio::trim(line).empty();
}

static bool is_headerish_cell(const std::string& raw)
{
    const std::string s = textio::trim(raw);
    if (s.empty()) return false;
    if (dottalkpp::import::is_integer_text(s) ||
        dottalkpp::import::is_decimal_text(s) ||
        dottalkpp::import::is_date_text(s) ||
        dottalkpp::import::is_logical_text(s)) {
        return false;
    }

    bool sawAlpha = false;
    for (unsigned char c : s) {
        if (std::isalpha(c)) {
            sawAlpha = true;
            break;
        }
    }
    return sawAlpha;
}

static bool first_row_looks_like_names(const std::vector<std::string>& row)
{
    if (row.empty()) return false;

    std::unordered_set<std::string> seen;
    for (const auto& cell : row) {
        if (!is_headerish_cell(cell)) return false;
        const std::string norm = dottalkpp::import::normalize_field_name(textio::trim(cell));
        if (norm.empty()) return false;
        const std::string key = upper(norm);
        if (!seen.insert(key).second) return false;
    }
    return true;
}

static bool data_profiles_strongly_typed(const std::vector<ColumnProfile>& profiles)
{
    for (const auto& p : profiles) {
        const std::string klass = dottalkpp::import::classify_profile(p);
        if (klass == "INTEGER" || klass == "DECIMAL" || klass == "DATE" || klass == "LOGICAL") {
            return true;
        }
    }
    return false;
}

static bool decide_auto_header(const std::vector<std::string>& firstRow,
                               const std::vector<ColumnProfile>& dataOnlyProfiles)
{
    return first_row_looks_like_names(firstRow) && data_profiles_strongly_typed(dataOnlyProfiles);
}

static void profile_row(std::vector<ColumnProfile>& profiles, const std::vector<std::string>& cols)
{
    for (std::size_t i = 0; i < profiles.size() && i < cols.size(); ++i) {
        dottalkpp::import::update_profile(profiles[i], textio::trim(cols[i]));
    }
}

static CsvScan scan_csv_file(const AutoDbfOptions& opt)
{
    CsvScan scan;

    std::ifstream in(opt.csvfile, std::ios::binary);
    if (!in) {
        scan.error = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::AutoDbfCannotOpenRead,
            {{"path", opt.csvfile}});
        return scan;
    }

    std::string line;
    std::size_t lineNumber = 0;

    while (std::getline(in, line)) {
        ++lineNumber;
        if (is_blank_line(line)) continue;
        scan.firstRow = split_csv_record(line);
        break;
    }

    if (scan.firstRow.empty()) {
        scan.error = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfEmptyCsv);
        return scan;
    }

    scan.expectedColumns = scan.firstRow.size();
    std::vector<ColumnProfile> dataOnlyProfiles(scan.expectedColumns);

    while (std::getline(in, line)) {
        ++lineNumber;
        if (is_blank_line(line)) continue;

        const std::vector<std::string> cols = split_csv_record(line);
        if (cols.size() != scan.expectedColumns) {
            scan.firstBadLine = lineNumber;
            scan.actualColumns = cols.size();
            scan.error = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfColumnCountMismatch);
            return scan;
        }

        profile_row(dataOnlyProfiles, cols);
        ++scan.dataRows;
    }

    if (opt.headerMode == HeaderMode::Header) {
        scan.firstRowIsHeader = true;
    } else if (opt.headerMode == HeaderMode::NoHeader) {
        scan.firstRowIsHeader = false;
    } else {
        scan.firstRowIsHeader = decide_auto_header(scan.firstRow, dataOnlyProfiles);
    }

    scan.profiles.assign(scan.expectedColumns, ColumnProfile{});
    if (!scan.firstRowIsHeader) {
        profile_row(scan.profiles, scan.firstRow);
        ++scan.dataRows;
    }

    in.clear();
    in.seekg(0, std::ios::beg);
    lineNumber = 0;
    bool skippedFirstNonBlank = false;

    while (std::getline(in, line)) {
        ++lineNumber;
        if (is_blank_line(line)) continue;

        const std::vector<std::string> cols = split_csv_record(line);
        if (cols.size() != scan.expectedColumns) {
            scan.firstBadLine = lineNumber;
            scan.actualColumns = cols.size();
            scan.error = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfColumnCountMismatch);
            return scan;
        }

        if (scan.firstRowIsHeader && !skippedFirstNonBlank) {
            skippedFirstNonBlank = true;
            continue;
        }
        skippedFirstNonBlank = true;
        profile_row(scan.profiles, cols);
    }

    scan.ok = true;
    return scan;
}

static std::string ordinal_field_name(std::size_t index1)
{
    std::string n = std::to_string(index1);
    while (n.size() < 3) n.insert(n.begin(), '0');
    return "FIELD" + n;
}

static std::string make_base_logical_name(const std::string& raw, std::size_t index1)
{
    std::string t = textio::trim(raw);
    if (t.empty()) return ordinal_field_name(index1);

    std::string n = dottalkpp::import::normalize_field_name(t);
    if (n.empty()) n = ordinal_field_name(index1);
    return n;
}

static std::string cap_with_suffix(std::string base, const std::string& suffix)
{
    const std::size_t maxLen = xbase::X64_FIELD_NAME_LENGTH;
    if (suffix.size() >= maxLen) {
        return suffix.substr(0, maxLen);
    }
    if (base.size() + suffix.size() > maxLen) {
        base.resize(maxLen - suffix.size());
    }
    return base + suffix;
}

static std::vector<std::string> make_unique_logical_names(const std::vector<std::string>& sourceNames)
{
    std::vector<std::string> out;
    out.reserve(sourceNames.size());

    std::unordered_set<std::string> used;
    for (std::size_t i = 0; i < sourceNames.size(); ++i) {
        std::string base = make_base_logical_name(sourceNames[i], i + 1);
        if (base.size() > xbase::X64_FIELD_NAME_LENGTH) {
            base.resize(xbase::X64_FIELD_NAME_LENGTH);
        }
        if (base.empty()) base = ordinal_field_name(i + 1);

        std::string candidate = base;
        std::string key = upper(candidate);
        std::size_t n = 2;
        while (used.find(key) != used.end()) {
            candidate = cap_with_suffix(base, "_" + std::to_string(n));
            key = upper(candidate);
            ++n;
        }
        used.insert(key);
        out.push_back(std::move(candidate));
    }

    return out;
}

static bool build_field_spec_from_profile(const ColumnProfile& p,
                                          bool inferTypes,
                                          int maxChar,
                                          FieldSpec& fs,
                                          std::string& err)
{
    if (!inferTypes) {
        if (p.maxLen > static_cast<std::size_t>(maxChar)) {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfTextWidthExceedsLimit,
                {{"width", std::to_string(p.maxLen)},
                 {"limit", std::to_string(maxChar)}});
            return false;
        }
        fs.type = 'C';
        fs.len = static_cast<std::uint8_t>(std::max<std::size_t>(1, p.maxLen));
        fs.dec = 0;
        return true;
    }

    const std::string klass = dottalkpp::import::classify_profile(p);
    if (klass == "LONGTEXT") {
        err = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::AutoDbfLongTextRequiresBytes,
            {{"bytes", std::to_string(p.maxLen)}});
        return false;
    }

    fs.type = dottalkpp::import::proposed_target_type(p);
    int width = dottalkpp::import::proposed_target_width(p);
    int dec = dottalkpp::import::proposed_target_decimals(p);

    if (fs.type == 'M') {
        err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfMemoInferenceDisabled);
        return false;
    }

    if (fs.type == 'C') {
        if (p.maxLen > static_cast<std::size_t>(maxChar)) {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfTextWidthExceedsLimit,
                {{"width", std::to_string(p.maxLen)},
                 {"limit", std::to_string(maxChar)}});
            return false;
        }
        if (width > maxChar) width = maxChar;
        if (width < static_cast<int>(p.maxLen)) width = static_cast<int>(p.maxLen);
    }

    if (width < 1 || width > AUTODBF_MAX_FIXED_WIDTH) {
        err = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::AutoDbfFieldWidthOutOfRange,
            {{"width", std::to_string(width)}});
        return false;
    }
    if (dec < 0 || dec > width) {
        err = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::AutoDbfDecimalCountInvalid,
            {{"decimals", std::to_string(dec)},
             {"width", std::to_string(width)}});
        return false;
    }

    fs.len = static_cast<std::uint8_t>(width);
    fs.dec = static_cast<std::uint8_t>(dec);
    return true;
}

static bool build_columns(const AutoDbfOptions& opt,
                          const CsvScan& scan,
                          std::vector<AutoDbfColumn>& columns,
                          std::string& err)
{
    std::vector<std::string> sourceNames;
    sourceNames.reserve(scan.expectedColumns);

    if (scan.firstRowIsHeader) {
        for (std::size_t i = 0; i < scan.expectedColumns; ++i) {
            sourceNames.push_back(i < scan.firstRow.size() ? scan.firstRow[i] : ordinal_field_name(i + 1));
        }
    } else {
        for (std::size_t i = 0; i < scan.expectedColumns; ++i) {
            sourceNames.push_back(ordinal_field_name(i + 1));
        }
    }

    std::vector<std::string> logicalNames = make_unique_logical_names(sourceNames);
    const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(logicalNames);

    columns.clear();
    columns.reserve(scan.expectedColumns);

    for (std::size_t i = 0; i < scan.expectedColumns; ++i) {
        AutoDbfColumn col;
        col.sourceName = sourceNames[i];
        col.logicalName = logicalNames[i];
        col.descriptorName = plans[i].descriptor_name;

        FieldSpec fs;
        fs.name = col.logicalName;
        fs.descriptor_name = col.descriptorName;

        if (!build_field_spec_from_profile(scan.profiles[i], opt.inferTypes, opt.maxChar, fs, err)) {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfColumnDetail,
                {{"index", std::to_string(i + 1)},
                 {"name", col.logicalName},
                 {"detail", err}});
            return false;
        }

        col.spec = fs;
        columns.push_back(std::move(col));
    }

    return true;
}

static bool normalize_date_for_dbf(const std::string& input, std::string& output)
{
    const std::string s = textio::trim(input);
    if (s.empty()) {
        output.clear();
        return true;
    }
    if (!dottalkpp::import::is_date_text(s)) return false;
    output = s.substr(0, 4) + s.substr(5, 2) + s.substr(8, 2);
    return true;
}

static bool normalize_logical_for_dbf(const std::string& input, std::string& output)
{
    const std::string s = textio::trim(input);
    if (s.empty()) {
        output.clear();
        return true;
    }

    const std::string u = dottalkpp::import::normalize_field_name(s);
    if (u == "T" || u == "TRUE" || u == "Y" || u == "YES" || u == "1") {
        output = "T";
        return true;
    }
    if (u == "F" || u == "FALSE" || u == "N" || u == "NO" || u == "0") {
        output = "F";
        return true;
    }
    return false;
}

static bool convert_value_for_field(const std::string& raw,
                                    const FieldSpec& fs,
                                    std::string& out,
                                    std::string& err)
{
    const std::string s = textio::trim(raw);

    if (fs.type == 'C') {
        if (s.size() > fs.len) {
            err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfCharacterWidthOverflow);
            return false;
        }
        out = s;
        return true;
    }

    if (fs.type == 'N' || fs.type == 'F') {
        if (s.empty()) {
            out.clear();
            return true;
        }
        if (!(dottalkpp::import::is_integer_text(s) || dottalkpp::import::is_decimal_text(s))) {
            err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfInvalidNumericValue);
            return false;
        }
        if (s.size() > fs.len) {
            err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfNumericWidthOverflow);
            return false;
        }
        out = s;
        return true;
    }

    if (fs.type == 'D') {
        if (!normalize_date_for_dbf(s, out)) {
            err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfInvalidDateValue);
            return false;
        }
        return true;
    }

    if (fs.type == 'L') {
        if (!normalize_logical_for_dbf(s, out)) {
            err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfInvalidLogicalValue);
            return false;
        }
        return true;
    }

    err = cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfUnsupportedFieldType);
    return false;
}

static bool for_each_data_row(const AutoDbfOptions& opt,
                              bool firstRowIsHeader,
                              std::size_t expectedColumns,
                              const std::function<bool(std::size_t, const std::vector<std::string>&)>& fn,
                              std::string& err)
{
    std::ifstream in(opt.csvfile, std::ios::binary);
    if (!in) {
        err = cli::cmdout::message_text(
            dottalk::helpdata::MessageId::AutoDbfCannotOpenRead,
            {{"path", opt.csvfile}});
        return false;
    }

    std::string line;
    std::size_t lineNumber = 0;
    bool skippedFirstNonBlank = false;

    while (std::getline(in, line)) {
        ++lineNumber;
        if (is_blank_line(line)) continue;

        std::vector<std::string> cols = split_csv_record(line);
        if (cols.size() != expectedColumns) {
            err = cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfLineExpectedColumnsFound,
                {{"line", std::to_string(lineNumber)},
                 {"expected", std::to_string(expectedColumns)},
                 {"found", std::to_string(cols.size())}});
            return false;
        }

        if (firstRowIsHeader && !skippedFirstNonBlank) {
            skippedFirstNonBlank = true;
            continue;
        }
        skippedFirstNonBlank = true;

        if (!fn(lineNumber, cols)) return false;
    }

    return true;
}

static bool validate_all_rows(const AutoDbfOptions& opt,
                              const CsvScan& scan,
                              const std::vector<AutoDbfColumn>& columns,
                              std::string& err)
{
    return for_each_data_row(
        opt,
        scan.firstRowIsHeader,
        scan.expectedColumns,
        [&](std::size_t lineNumber, const std::vector<std::string>& cols) {
            for (std::size_t i = 0; i < cols.size(); ++i) {
                std::string converted;
                std::string valueErr;
                if (!convert_value_for_field(cols[i], columns[i].spec, converted, valueErr)) {
                    err = cli::cmdout::message_text(
                        dottalk::helpdata::MessageId::AutoDbfLineColumnDetail,
                        {{"line", std::to_string(lineNumber)},
                         {"column", std::to_string(i + 1)},
                         {"name", columns[i].logicalName},
                         {"detail", valueErr}});
                    return false;
                }
            }
            return true;
        },
        err);
}

static bool import_rows(DbArea& area,
                        const AutoDbfOptions& opt,
                        const CsvScan& scan,
                        const std::vector<AutoDbfColumn>& columns,
                        std::size_t& imported,
                        std::string& err)
{
    imported = 0;

    return for_each_data_row(
        opt,
        scan.firstRowIsHeader,
        scan.expectedColumns,
        [&](std::size_t lineNumber, const std::vector<std::string>& cols) {
            std::vector<std::string> converted(cols.size());
            for (std::size_t i = 0; i < cols.size(); ++i) {
                std::string valueErr;
                if (!convert_value_for_field(cols[i], columns[i].spec, converted[i], valueErr)) {
                    err = cli::cmdout::message_text(
                        dottalk::helpdata::MessageId::AutoDbfLineColumnDetail,
                        {{"line", std::to_string(lineNumber)},
                         {"column", std::to_string(i + 1)},
                         {"name", columns[i].logicalName},
                         {"detail", valueErr}});
                    return false;
                }
            }

            if (!area.appendBlank()) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::AutoDbfAppendBlankFailed,
                    {{"line", std::to_string(lineNumber)}});
                return false;
            }

            for (std::size_t i = 0; i < converted.size(); ++i) {
                if (!area.set(static_cast<int>(i + 1), converted[i])) {
                    err = cli::cmdout::message_text(
                        dottalk::helpdata::MessageId::AutoDbfSetFailed,
                        {{"line", std::to_string(lineNumber)},
                         {"column", std::to_string(i + 1)},
                         {"name", columns[i].logicalName}});
                    return false;
                }
            }

            if (!area.writeCurrent()) {
                err = cli::cmdout::message_text(
                    dottalk::helpdata::MessageId::AutoDbfWriteCurrentFailed,
                    {{"line", std::to_string(lineNumber)}});
                return false;
            }

            ++imported;
            return true;
        },
        err);
}

static void print_plan(const AutoDbfOptions& opt,
                       const CsvScan& scan,
                       const std::vector<AutoDbfColumn>& columns)
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::AutoDbfPlanTitle);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfPlanCsvLine,
        {{"path", opt.csvfile}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfPlanHeaderLine,
        {{"mode", scan.firstRowIsHeader ? "HEADER" : "NOHEADER"},
         {"suffix", opt.headerMode == HeaderMode::Auto ? " (AUTO)" : ""}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfPlanDataRowsLine,
        {{"count", std::to_string(scan.dataRows)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfPlanColumnsLine,
        {{"count", std::to_string(columns.size())}});

    for (std::size_t i = 0; i < columns.size(); ++i) {
        const AutoDbfColumn& c = columns[i];
        std::string line = "    " + std::to_string(i + 1) + "  " +
                           c.logicalName + "  " + std::string(1, c.spec.type);
        if (c.spec.type == 'N' || c.spec.type == 'F') {
            line += "(" + std::to_string(int(c.spec.len)) + "," + std::to_string(int(c.spec.dec)) + ")";
        } else if (c.spec.type == 'C') {
            line += "(" + std::to_string(int(c.spec.len)) + ")";
        }
        if (c.descriptorName != c.logicalName) {
            line += cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfPlanDescriptorSuffix,
                {{"name", c.descriptorName}});
        }
        if (scan.firstRowIsHeader && c.sourceName != c.logicalName) {
            line += cli::cmdout::message_text(
                dottalk::helpdata::MessageId::AutoDbfPlanSourceSuffix,
                {{"name", c.sourceName}});
        }
        cli::cmdout::print_line(line);
    }
}

} // namespace

void cmd_AUTODBF(DbArea& area, std::istringstream& iss)
{
    const std::string rawArgs = iss.str();
    if (is_usage_request(rawArgs)) {
        print_usage();
        return;
    }

    AutoDbfOptions opt;
    std::string err;

    if (!parse_args(iss, opt, err)) {
        cli::cmdout::print_info("AUTODBF", err);
        print_usage();
        return;
    }

    if (!textio::ends_with_ci(opt.csvfile, ".csv")) {
        opt.csvfile += ".csv";
    }

    const std::filesystem::path outPath =
        resolve_dbf_slot_path(std::filesystem::path(xbase::dbNameWithExt(opt.table)));
    const std::string dbfPath = path_to_string(outPath);

    if (std::filesystem::exists(outPath) && !opt.overwrite) {
        cli::cmdout::print_prefixed_message(
            "AUTODBF failed",
            dottalk::helpdata::MessageId::AutoDbfTargetExists,
            {{"path", dbfPath}});
        cli::cmdout::print_line(
            "  " + cli::cmdout::message_text(dottalk::helpdata::MessageId::AutoDbfUseOverwriteNote));
        return;
    }

    CsvScan scan = scan_csv_file(opt);
    if (!scan.ok) {
        if (scan.firstBadLine != 0) {
            cli::cmdout::print_prefixed_message(
                "AUTODBF failed",
                dottalk::helpdata::MessageId::AutoDbfScanFailedAtLine,
                {{"detail", scan.error},
                 {"line", std::to_string(scan.firstBadLine)},
                 {"expected", std::to_string(scan.expectedColumns)},
                 {"found", std::to_string(scan.actualColumns)}});
        } else {
            cli::cmdout::print_info("AUTODBF failed", scan.error);
        }
        return;
    }

    if (scan.dataRows == 0) {
        cli::cmdout::print_prefixed_message("AUTODBF failed", dottalk::helpdata::MessageId::AutoDbfNoDataRows);
        return;
    }

    std::vector<AutoDbfColumn> columns;
    if (!build_columns(opt, scan, columns, err)) {
        cli::cmdout::print_info("AUTODBF failed", err);
        return;
    }

    if (!validate_all_rows(opt, scan, columns, err)) {
        cli::cmdout::print_info("AUTODBF failed", err);
        return;
    }

    print_plan(opt, scan, columns);

    std::vector<FieldSpec> fields;
    fields.reserve(columns.size());
    for (const auto& c : columns) fields.push_back(c.spec);

    if (area.isOpen()) {
        orderstate::clearOrder(area);
        area.close();
    }

    if (!xbase::dbf_create::create_dbf(dbfPath, fields, xbase::dbf_create::Flavor::X64, err)) {
        cli::cmdout::print_prefixed_message(
            "AUTODBF failed",
            dottalk::helpdata::MessageId::AutoDbfCreateFailed,
            {{"detail", err}});
        return;
    }

    try {
        area.open(dbfPath);
    } catch (const std::exception& ex) {
        cli::cmdout::print_prefixed_message(
            "AUTODBF failed",
            dottalk::helpdata::MessageId::AutoDbfReopenFailedDetail,
            {{"detail", ex.what()}});
        return;
    } catch (...) {
        cli::cmdout::print_prefixed_message(
            "AUTODBF failed",
            dottalk::helpdata::MessageId::AutoDbfReopenFailedGeneric);
        return;
    }

    std::size_t imported = 0;
    if (!import_rows(area, opt, scan, columns, imported, err)) {
        cli::cmdout::print_prefixed_message(
            "AUTODBF failed",
            dottalk::helpdata::MessageId::AutoDbfImportFailed,
            {{"detail", err}});
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::AutoDbfPartialRowsImported,
            {{"count", std::to_string(imported)}});
        return;
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::AutoDbfOkTitle);
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfCreatedLine,
        {{"path", dbfPath}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfImportedRowsLine,
        {{"count", std::to_string(imported)}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::AutoDbfOpenedLine,
        {{"path", area.filename()}});
}
