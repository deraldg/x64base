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
//   Export the current DBF rowset, or an already-open named work area, to a delimited file.
//
// usage:
//   EXPORT USAGE
//   EXPORT [TO] <file> [CSV|PIPE]
//   EXPORT <open-area-token> TO <file> [CSV|PIPE]
//
// notes:
//   EXPORT [TO] <file> writes the current table to the named file.
//   EXPORT <open-area-token> TO <file> writes an already-open work area without changing
//   the user's selected area intentionally.
//   Named tokens may be an area number, #area, alias/name, logical name, DBF basename/stem,
//   filename, or full path, if those values resolve uniquely to an open area.
//   Named EXPORT does not auto-open tables from disk.
//   CSV is the default format; PIPE uses a pipe delimiter.
//   A missing extension is added automatically (.csv for CSV, .txt for PIPE).
//   EXPORT writes a header row.
//   EXPORT honors the active SET FILTER for the exported area.
//   EXPORT reads records in physical table order.
//   EXPORT may report file/write errors and still emit a summary when appropriate.
//
// risk:
//   reads_table_records: yes
//   writes_files: yes
//   overwrites_output_file: yes if target exists
//   mutates_table_data: no
//   mutates_cursor: current-area form preserves existing cursor behavior;
//                   named-area form uses WorkAreaCursorRestore safety guard
//
// related:
//   DUMP
//   LIST
//   COPY TO
//   DDL
//   WORKSPACE
//   WSREPORT
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <fstream>
#include <memory>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "textio.hpp"
#include "filters/filter_registry.hpp"
#include "cli/workarea_cursor_restore.hpp"

using namespace xbase;

namespace {

namespace fs = std::filesystem;

extern "C" xbase::XBaseEngine* shell_engine();

struct NamedAreaMatch {
    int slot = -1;
    xbase::DbArea* area = nullptr;
    std::string label;
    std::string matched_by;
};

struct NamedAreaResolveResult {
    bool ok = false;
    bool ambiguous = false;
    std::vector<NamedAreaMatch> matches;
    std::string error;
};

static std::string export_trim(std::string s)
{
    return textio::trim(std::move(s));
}

static std::string export_upper(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    return s;
}

static std::string export_lower(std::string s)
{
    for (char& ch : s) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
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
    cli::cmdout::print_message(dottalk::helpdata::MessageId::ExportUsageText);
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

static bool try_parse_area_number(const std::string& token, int& out)
{
    std::string t = export_trim(token);
    if (t.empty()) return false;
    if (t[0] == '#') t.erase(t.begin());
    if (t.empty()) return false;

    for (char c : t) {
        if (!std::isdigit(static_cast<unsigned char>(c))) return false;
    }

    try {
        out = std::stoi(t);
        return true;
    } catch (...) {
        return false;
    }
}

static bool safe_is_open(xbase::DbArea& area)
{
    try { return area.isOpen(); } catch (...) { return false; }
}

static std::string safe_filename(xbase::DbArea& area)
{
    try { return area.filename(); } catch (...) { return {}; }
}

static std::string safe_name(xbase::DbArea& area)
{
    try { return area.name(); } catch (...) { return {}; }
}

static std::string safe_logical_name(xbase::DbArea& area)
{
    try { return area.logicalName(); } catch (...) { return {}; }
}

static std::string safe_dbf_basename(xbase::DbArea& area)
{
    try { return area.dbfBasename(); } catch (...) { return {}; }
}

static std::string safe_area_label(int slot, xbase::DbArea& area)
{
    const std::string logical = safe_logical_name(area);
    if (!logical.empty()) return logical;
    const std::string name = safe_name(area);
    if (!name.empty()) return name;
    const std::string base = safe_dbf_basename(area);
    if (!base.empty()) return base;
    const std::string filename = safe_filename(area);
    if (!filename.empty()) {
        try { return fs::path(filename).stem().string(); } catch (...) { return filename; }
    }
    return "area " + std::to_string(slot);
}

static void add_candidate(std::vector<std::pair<std::string, std::string>>& out,
                          std::string value,
                          std::string kind)
{
    value = export_trim(std::move(value));
    if (value.empty()) return;
    out.push_back({ export_lower(value), std::move(kind) });
}

static std::vector<std::pair<std::string, std::string>> area_candidates(int slot,
                                                                        xbase::DbArea& area)
{
    std::vector<std::pair<std::string, std::string>> c;
    add_candidate(c, std::to_string(slot), "area number");
    add_candidate(c, "#" + std::to_string(slot), "#area number");

    const std::string filename = safe_filename(area);
    add_candidate(c, safe_name(area), "name/alias");
    add_candidate(c, safe_logical_name(area), "logical name");
    add_candidate(c, safe_dbf_basename(area), "dbf basename");

    if (!filename.empty()) {
        add_candidate(c, filename, "full path");
        try {
            fs::path p(filename);
            add_candidate(c, p.filename().string(), "filename");
            add_candidate(c, p.stem().string(), "filename stem");
        } catch (...) {}
    }

    return c;
}

static NamedAreaResolveResult resolve_open_area_token(const std::string& token)
{
    NamedAreaResolveResult r;
    std::string needle = export_lower(export_trim(token));
    if (needle.empty()) {
        r.error = "empty area token";
        return r;
    }

    auto* eng = shell_engine();
    if (!eng) {
        r.error = "engine not available";
        return r;
    }

    int numeric = -1;
    if (try_parse_area_number(needle, numeric)) {
        if (numeric < 0 || numeric >= xbase::MAX_AREA) {
            r.error = "area out of range: " + std::to_string(numeric);
            return r;
        }
        try {
            xbase::DbArea& area = eng->area(numeric);
            if (!safe_is_open(area)) {
                r.error = "area is not open: " + std::to_string(numeric);
                return r;
            }
            r.matches.push_back({ numeric, &area, safe_area_label(numeric, area), "area number" });
            r.ok = true;
            return r;
        } catch (const std::exception& ex) {
            r.error = ex.what();
            return r;
        } catch (...) {
            r.error = "unable to resolve area number";
            return r;
        }
    }

    for (int slot = 0; slot < xbase::MAX_AREA; ++slot) {
        try {
            xbase::DbArea& area = eng->area(slot);
            if (!safe_is_open(area)) continue;

            for (const auto& cand : area_candidates(slot, area)) {
                if (cand.first == needle) {
                    bool already = false;
                    for (const auto& m : r.matches) {
                        if (m.slot == slot) { already = true; break; }
                    }
                    if (!already) {
                        r.matches.push_back({ slot, &area, safe_area_label(slot, area), cand.second });
                    }
                    break;
                }
            }
        } catch (...) {}
    }

    if (r.matches.empty()) {
        r.error = "no open area matches '" + token + "'";
        return r;
    }

    if (r.matches.size() > 1) {
        r.ambiguous = true;
        r.error = "ambiguous area token '" + token + "'";
        return r;
    }

    r.ok = true;
    return r;
}

static void print_ambiguous_export_token(const std::string& token,
                                         const NamedAreaResolveResult& r)
{
    std::string matches;
    if (!r.matches.empty()) {
        matches = ": ";
        for (std::size_t i = 0; i < r.matches.size(); ++i) {
            if (i) matches += ", ";
            matches += "area " + std::to_string(r.matches[i].slot) + " " + r.matches[i].label;
        }
    }
    cli::cmdout::print_prefixed_message(
        "EXPORT", dottalk::helpdata::MessageId::ExportAmbiguousTokenText,
        {{"token", token}, {"matches", matches}});
}

static bool export_area_to_file(xbase::DbArea& area,
                                std::string dest,
                                char delimiter,
                                bool restore_cursors)
{
    add_default_export_extension(dest, delimiter);

    std::unique_ptr<dottalk::tupleaugment::WorkAreaCursorRestore> restore_guard;
    if (restore_cursors) {
        restore_guard = std::make_unique<dottalk::tupleaugment::WorkAreaCursorRestore>();
    }

    std::ofstream out(dest, std::ios::binary);
    if (!out) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::ExportUnableToOpenText, {{"dest", dest}});
        return false;
    }

    const auto& fields = area.fields();

    std::vector<std::string> header;
    header.reserve(fields.size());
    for (const auto& f : fields) header.push_back(f.name);
    write_delimited_row(out, header, delimiter);

    std::size_t exported = 0;
    const int nrecs = area.recCount();

    for (int recno = 1; recno <= nrecs; ++recno) {
        try {
            (void)area.gotoRec(recno);
            (void)area.readCurrent();
        } catch (...) {
            continue;
        }

        // Honor persistent SET FILTER. Null FOR AST means no additional ad-hoc predicate.
        if (!filter::visible(&area, nullptr)) continue;

        std::vector<std::string> row;
        row.reserve(fields.size());
        for (std::size_t i = 0; i < fields.size(); ++i) {
            row.push_back(area.get(static_cast<int>(i + 1)));
        }
        write_delimited_row(out, row, delimiter);
        ++exported;
    }

    if (!out) {
        cli::cmdout::print_prefixed_message(
            "ERROR", dottalk::helpdata::MessageId::ExportWriteFailedText, {{"dest", dest}});
    }

    if (restore_guard) {
        std::string restore_error;
        if (!restore_guard->restore(restore_error)) {
            cli::cmdout::print_prefixed_message(
                "WARNING", dottalk::helpdata::MessageId::ExportCursorRestoreWarningText,
                {{"detail", restore_error}});
        }
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::ExportedCountText,
        {{"count", std::to_string(exported)}, {"dest", dest}});
    return true;
}

} // namespace

void cmd_EXPORT(DbArea& a, std::istringstream& iss) {
    const std::string raw_args = iss.str();
    if (is_export_usage_request(raw_args)) {
        print_export_usage();
        return;
    }

    // Accepted forms:
    //   EXPORT <file> [CSV|PIPE]
    //   EXPORT TO <file> [CSV|PIPE]
    //   EXPORT <open-area-token> TO <file> [CSV|PIPE]
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
        if (!a.isOpen()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ExportNoFileOpenText);
            return;
        }
        dest = toks[1];
        (void)export_area_to_file(a, dest, delimiter, false);
        return;
    }

    if (toks.size() >= 3 && ieq_to(toks[1])) {
        // EXPORT <open-area-token> TO <file>
        if (toks.size() != 3 || toks[0].empty() || toks[2].empty()) {
            print_export_usage();
            return;
        }

        const std::string token = toks[0];
        dest = toks[2];

        NamedAreaResolveResult resolved = resolve_open_area_token(token);
        if (!resolved.ok) {
            if (resolved.ambiguous) print_ambiguous_export_token(token, resolved);
            else cli::cmdout::print_prefixed_message(
                "EXPORT", dottalk::helpdata::MessageId::ExportErrorDetailText,
                {{"detail", resolved.error}});
            return;
        }
        if (resolved.matches.empty() || !resolved.matches[0].area) {
            cli::cmdout::print_prefixed_message(
                "EXPORT", dottalk::helpdata::MessageId::ExportNoOpenAreaMatchText,
                {{"token", token}});
            return;
        }

        (void)export_area_to_file(*resolved.matches[0].area, dest, delimiter, true);
        return;
    }

    if (toks.size() == 1) {
        // EXPORT <file>
        if (!a.isOpen()) {
            cli::cmdout::print_message(dottalk::helpdata::MessageId::ExportNoFileOpenText);
            return;
        }
        dest = toks[0];
        (void)export_area_to_file(a, dest, delimiter, false);
        return;
    }

    print_export_usage();
}
