// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// src/cli/cmd_dbarea.cpp
#include "workarea_util.hpp"
#include "cli/cmd_dbarea.hpp"

#include <algorithm>
#include <cctype>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

#include "xbase.hpp"
#include "xbase/workspace_membership.hpp"
#include "cli/command_output.hpp"
#include "cli/order_state.hpp"
#include "cli/order_report.hpp"

// engine access: compute area slot without changing DbArea API
extern "C" xbase::XBaseEngine* shell_engine();

// @dottalk.usage v1
// owner: DOT|DBAREA
// command: DBAREA
// category: workspace
// status: supported
// noargs: report
// effect: report
// mutates: no
// usage-access: DBAREA USAGE
// summary:
//   Report the current DbArea/work-area state, including file identity,
//   the workspace that OWNS the area and the session's CURRENT workspace,
//   logical name, record counts, current record, active order/index status,
//   and field structure.
//
// usage:
//   DBAREA
//   DBAREA USAGE
//
// notes:
//   DBAREA reports BOTH workspaces even when they are the same. They differ
//   whenever SELECT has reached an area another workspace owns, and a report
//   naming only the session would describe something other than the area
//   beneath it.
//   An area owned by no workspace reads "(none)". That is a real state, not
//   an error -- see reconcile_unregistered_areas() in cmd_workspace.cpp --
//   and DBAREA is the only place it is visible for a single area.
//
// risk:
//   reads_table_records: no -- structure and counts only
//   reads_workspace_membership: yes -- owner of this slot, plus current handle
//   mutates_cursor: no
//   mutates_table_data: no
//
// notes:
//   DBAREA with no arguments is a read-only report for the current work area.
//   The current implementation receives an argument stream but does not consume it.
//   Slot, ALL, and relation-context report forms are currently implemented by DBAREAS.
//   Keep DBAREA focused as the canonical single-area report.
//
// related:
//   DBAREAS
//   WORKSPACE
//   STATUS
//   STRUCT
//

namespace {
static inline std::string rtrim_copy(std::string s){
    while (!s.empty() && std::isspace(static_cast<unsigned char>(s.back()))) s.pop_back();
    return s;
}
static inline std::string ltrim_copy(std::string s){
    size_t i=0; while (i<s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
    return s.substr(i);
}
static inline std::string trim_copy(std::string s){ return rtrim_copy(ltrim_copy(std::move(s))); }

static inline const char* type_name(char t){
    switch (t){
        case 'C': case 'c': return "Character";
        case 'N': case 'n': return "Numeric";
        case 'D': case 'd': return "Date";
        case 'L': case 'l': return "Logical";
        case 'M': case 'm': return "Memo";
        default:            return "Other";
    }
}
static inline void kv(const std::string& k, const std::string& v, int w=20){
    std::cout << std::left << std::setw(w) << k << ": " << v << "\n";
}
static inline void kv(const std::string& k, int v, int w=20){
    std::cout << std::left << std::setw(w) << k << ": " << v << "\n";
}

// Compute real area slot by identity compare against engine slots.
static int area_slot_of(xbase::DbArea& a){
    // AIF-120 I1.1 sweep completed 2026-08-22 (AIF-078 GUI design sec 8, O5).
    // This was a MAX_AREA pointer-identity scan. The engine stamps the same
    // number into DbArea::_engine_slot once at construction, so the scan
    // recovered a value the area already carried. Body only -- the signature
    // and every call site are unchanged, which is how I1.1 did it.
    return cli::slot_of_area(&a);
}
} // namespace

void cmd_DBAREA(xbase::DbArea& a, std::istringstream& iss){
    using namespace xbase;

    std::string raw = iss.str();
    std::transform(raw.begin(), raw.end(), raw.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    if (raw.find("USAGE") != std::string::npos ||
        raw.find("HELP")  != std::string::npos ||
        raw.find("?")     != std::string::npos) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaUsageText);
        return;
    }

    if (!a.isOpen()){
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaNoTableOpenText);
        return;
    }

    const std::string dbf_abs  = a.filename();
    const std::string logical  = a.name();
    const int32_t recs         = a.recCount();
    const int     reclen       = a.recLength();
    const int     nfields      = a.fieldCount();
    const int32_t crn          = a.recno();
    const auto&   fdefs        = a.fields();

    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaBannerDividerText);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaBannerTitle);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaBannerDividerText);

    // Area slot
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaAreaSlotLineText), area_slot_of(a));

    // 2026-08-29, owner instruction. BOTH workspaces, ALWAYS, even when they
    // agree. The R112 ambiguity ledger's rule applied to a second instrument:
    // it prints at zero so that "they agree" and "this build does not check"
    // cannot look alike. They diverge the moment SELECT reaches an area another
    // workspace owns -- the session is in one, the area belongs to the other --
    // and a report naming only the session would be a label describing
    // something other than the thing beneath it. AIF-148, written the same day,
    // is exactly that failure one layer down.
    //
    // owner 0 renders "(none)", which is a REAL state and not an error: an area
    // can be open and belong to no workspace, which reconcile_unregistered_areas
    // calls a defect in registration. This line is therefore an instrument for
    // that too, and it is the only place it would be visible on one area.
    {
        const std::int32_t  slot    = static_cast<std::int32_t>(area_slot_of(a));
        const std::uint64_t owner_h = xbase::workspace::owner_of_slot(slot);
        const std::uint64_t cur_h   = xbase::workspace::current_handle();
        auto describe = [](std::uint64_t h) -> std::string {
            if (h == 0) return std::string("(none)");
            return xbase::workspace::name_of(h) + "  handle " + std::to_string(h);
        };
        kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaOwningWorkspaceLineText),
           describe(owner_h));
        kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaCurrentWorkspaceLineText),
           describe(cur_h));
    }

    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaDbfAbsoluteLineText), dbf_abs);
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaLogicalNameLineText), logical);
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaLegacyNameLineText), logical);

    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaRecordsLineText), static_cast<int>(recs));
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaRecordLengthLineText), reclen);
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaRecordLengthMethodLineText), a.recordLength());
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaFieldsCountLineText), nfields);
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaRecnoLineText), static_cast<int>(crn));
    kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaDeletedFlagLineText), a.isDeleted()? 1 : 0);

    std::cout << "\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaIndexOrderTitle);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaSectionDividerText);

    // Echo index file path explicitly for parity with `area` command
    try {
        const std::string idx_path = orderstate::orderName(a);
        kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaIndexFileLineText),
           idx_path.empty() ? std::string("(none)") : idx_path);
    } catch (...) {
        kv(cli::cmdout::message_text(dottalk::helpdata::MessageId::DbareaIndexFileLineText), std::string("(unknown)"));
    }

    // Detailed status (direction, tag, etc.)
    orderreport::print_status_block(std::cout, a);

    std::cout << "\n";
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaFieldsTitle);
    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaSectionDividerText);
    if (fdefs.empty()){
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaFieldsNoneText);
    } else {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaFieldColumnHeaderText);
        cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaFieldDividerText);
        for (int i=0; i<static_cast<int>(fdefs.size()); ++i){
            const auto& f = fdefs[i];
            std::cout << std::left
                      << std::setw(5)  << (i+1)
                      << std::setw(18) << trim_copy(f.name)
                      << std::setw(10) << type_name(f.type)
                      << std::setw(8)  << static_cast<int>(f.length)
                      << std::setw(8)  << static_cast<int>(f.decimals)
                      << "\n";
        }
    }

    cli::cmdout::print_message(dottalk::helpdata::MessageId::DbareaBannerDividerText);
    std::cout.flush();
}
