// src/cli/cmd_catalogcanary.cpp
// @dottalk.usage v1
// owner: DOT|CATALOGCANARY
// command: CATALOGCANARY
// category: metadata-dev
// status: dev-canary
// noargs: inspect-current-area
// effect: report
// mutates: none
// usage-access: CATALOGCANARY USAGE
// summary:
//   Dev canary for the metadata catalog reader adapter. Reads the current
//   already-open SYSCMD area and reports adapter row/distribution counts.
//
// usage:
//   CATALOGCANARY
//   CATALOGCANARY USAGE
//
// notes:
//   CATALOGCANARY does not open SYSCMD.dbf.
//   CATALOGCANARY does not call USE or WORKSPACE OPEN.
//   CATALOGCANARY expects DotTalk++ to have already prepared the area:
//     DO METADATA
//     WORKSPACE OPEN DBF
//     SELECT SYSCMD
//   It calls load_commands_from_area(current_area).
//   Registration is intentionally left to the house shell command registry.
//
// risk:
//   mutates_table_data: no
//   writes_files: no
//   opens_files: no
//   direct_dbf_open: no
//   workspace_mutation: no explicit mutation, but adapter iteration moves the current area cursor
//
// related:
//   METADATA
//   WORKSPACE
//   USE
//   FIELDS
//   LIST
//   CMDHELPCHK
//

#include "xbase.hpp"
#include "cli/catalog_reader_adapter.hpp"

#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <sstream>
#include <string>

#if __has_include("cli/output_router.hpp")
  #include "cli/output_router.hpp"
  #define DOTTALK_CATALOGCANARY_HAS_OUTPUT_ROUTER 1
#else
  #define DOTTALK_CATALOGCANARY_HAS_OUTPUT_ROUTER 0
#endif

namespace {

static inline std::string cc_trim(std::string s)
{
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.front()))) {
        s.erase(s.begin());
    }
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) {
        s.pop_back();
    }
    return s;
}

static inline std::string cc_upper(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char ch) { return static_cast<char>(std::toupper(ch)); });
    return s;
}

static inline bool cc_ieq(const std::string& a, const std::string& b)
{
    return cc_upper(a) == cc_upper(b);
}

static bool cc_usage_request(std::string raw)
{
    raw = cc_trim(std::move(raw));
    if (raw.empty()) {
        return false;
    }

    std::string u = cc_upper(raw);
    if (u.rfind("CATALOGCANARY ", 0) == 0) {
        u = cc_trim(u.substr(14));
    }

    return u == "USAGE" || u == "HELP" || u == "?";
}

static void cc_print_usage(std::ostream& out)
{
    out
        << "Usage:\n"
        << "  CATALOGCANARY\n"
        << "  CATALOGCANARY USAGE\n"
        << "\n"
        << "Purpose:\n"
        << "  Dev canary for the area-first metadata catalog reader adapter.\n"
        << "\n"
        << "Expected setup:\n"
        << "  DO METADATA\n"
        << "  WORKSPACE OPEN DBF\n"
        << "  SELECT SYSCMD\n"
        << "  CATALOGCANARY\n"
        << "\n"
        << "Notes:\n"
        << "  This command does not open SYSCMD.dbf directly.\n"
        << "  It reads the current already-open area through load_commands_from_area().\n";
}

static bool cc_has_field_ci(const xbase::DbArea& area, const std::string& field_name)
{
    const auto& fields = area.fields();
    for (const auto& f : fields) {
        if (cc_ieq(f.name, field_name)) {
            return true;
        }
    }
    return false;
}

static bool cc_area_looks_like_syscmd(const xbase::DbArea& area, std::string& reason)
{
    const bool has_cmd_id = cc_has_field_ci(area, "CMD_ID");
    const bool has_can_name = cc_has_field_ci(area, "CAN_NAME");
    const bool has_type = cc_has_field_ci(area, "TYPE");
    const bool has_vis = cc_has_field_ci(area, "VIS");
    const bool has_handler = cc_has_field_ci(area, "HANDLER");
    const bool has_active = cc_has_field_ci(area, "ACTIVE");

    if (has_cmd_id && has_can_name && has_type && has_vis && has_handler && has_active) {
        return true;
    }

    reason = "current area does not have required SYSCMD fields: ";
    bool first = true;
    auto add_missing = [&](const char* name, bool present) {
        if (present) {
            return;
        }
        if (!first) {
            reason += ", ";
        }
        first = false;
        reason += name;
    };

    add_missing("CMD_ID", has_cmd_id);
    add_missing("CAN_NAME", has_can_name);
    add_missing("TYPE", has_type);
    add_missing("VIS", has_vis);
    add_missing("HANDLER", has_handler);
    add_missing("ACTIVE", has_active);

    return false;
}

static void cc_print_distribution(std::ostream& out,
                                  const std::string& label,
                                  const std::map<std::string, int>& values)
{
    out << label << ":\n";
    if (values.empty()) {
        out << "  <none> = 0\n";
        return;
    }
    for (const auto& kv : values) {
        out << "  " << (kv.first.empty() ? "<blank>" : kv.first)
            << " = " << kv.second << "\n";
    }
}

} // namespace

void cmd_CATALOGCANARY(xbase::DbArea& area, std::istringstream& in)
{
#if DOTTALK_CATALOGCANARY_HAS_OUTPUT_ROUTER
    auto& out = cli::OutputRouter::instance().out();
#else
    auto& out = std::cout;
#endif

    std::string rest;
    std::getline(in, rest);

    if (cc_usage_request(rest)) {
        cc_print_usage(out);
        return;
    }

    std::string reason;
    if (!cc_area_looks_like_syscmd(area, reason)) {
        out << "CATALOGCANARY: current area is not SYSCMD.\n";
        out << "  " << reason << "\n";
        out << "Expected setup:\n";
        out << "  DO METADATA\n";
        out << "  WORKSPACE OPEN DBF\n";
        out << "  SELECT SYSCMD\n";
        out << "  CATALOGCANARY\n";
        return;
    }

    const auto result = dottalk::metadata::load_commands_from_area(area);

    int errors = 0;
    int warnings = 0;
    int infos = 0;

    for (const auto& d : result.diagnostics) {
        const std::string sev = cc_upper(d.severity);
        if (sev == "ERROR") {
            ++errors;
        } else if (sev == "WARN" || sev == "WARNING") {
            ++warnings;
        } else {
            ++infos;
        }
    }

    std::map<std::string, int> type_counts;
    std::map<std::string, int> vis_counts;
    std::map<std::string, int> active_counts;

    for (const auto& row : result.rows) {
        ++type_counts[row.kind];
        ++vis_counts[row.visibility];
        ++active_counts[row.active ? "true" : "false"];
    }

    out << "CATALOGCANARY: area-first catalog reader\n";
    out << "Rows loaded: " << result.rows.size() << "\n";
    out << "Diagnostics: " << result.diagnostics.size()
        << " (errors=" << errors
        << ", warnings=" << warnings
        << ", info=" << infos << ")\n";

    cc_print_distribution(out, "TYPE", type_counts);
    cc_print_distribution(out, "VIS", vis_counts);
    cc_print_distribution(out, "ACTIVE", active_counts);

    if (errors > 0) {
        out << "Errors:\n";
        for (const auto& d : result.diagnostics) {
            if (cc_upper(d.severity) == "ERROR") {
                out << "  " << d.code << ": " << d.message;
                if (!d.row_key.empty()) {
                    out << " [" << d.row_key << "]";
                }
                out << "\n";
            }
        }
    }
}
