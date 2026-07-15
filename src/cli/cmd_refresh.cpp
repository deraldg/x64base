// src/cli/cmd_refresh.cpp

// @dottalk.usage v1
// owner: DOT|REFRESH
// command: REFRESH
// category: table
// status: supported
// noargs: execute
// effect: refresh
// mutates: work-area cursor order-state
// usage-access: REFRESH USAGE
// summary:
//   Reopen the current table from disk and restore cursor/order state best-effort.
//
// usage:
//   REFRESH
//   REFRESH USAGE
//
// notes:
//   REFRESH with no arguments reopens the current DBF file.
//   Cursor position is restored best-effort after reopen.
//   Active order/container/tag/direction state is restored best-effort.
//   REFRESH USAGE prints usage before open-table checks or reopening.
//
// risk:
//   reopens_table: yes
//   mutates_work_area: yes
//   mutates_cursor: yes
//   mutates_order_state: restore path
//   mutates_table_data: no
//   requires_open_table: yes except usage
//
// related:
//   USE
//   REINDEX
//   WORKSPACE
//

#include "xbase.hpp"
#include "cli/command_output.hpp"
#include "cli/order_state.hpp"   // src/cli/order_state.hpp (same folder as this .cpp)
#include "help/helpdata_messages.hpp"

#include <cctype>
#include <filesystem>
#include <sstream>
#include <string>
#include <system_error>

namespace {
static std::string refresh_upper(std::string s)
{
    for (char& ch : s) {
        ch = static_cast<char>(std::toupper(static_cast<unsigned char>(ch)));
    }
    return s;
}

static void print_refresh_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::RefreshUsageText);
}

static bool refresh_usage_request(std::istringstream& in)
{
    std::string tok;
    if (!(in >> tok)) {
        in.clear();
        in.seekg(0);
        return false;
    }

    const std::string u = refresh_upper(tok);
    if (u == "USAGE" || u == "HELP" || u == "?") {
        return true;
    }

    in.clear();
    in.seekg(0);
    return false;
}
} // namespace

void cmd_REFRESH(xbase::DbArea& a, std::istringstream& in) {
    if (refresh_usage_request(in)) {
        print_refresh_usage();
        return;
    }
    if (!a.isOpen()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::RefreshNoTableOpenText);
        return;
    }

    // Canonical absolute DBF path (DbArea::open expects abs path)
    const std::string abs_dbf = a.filename();
    if (abs_dbf.empty()) {
        cli::cmdout::print_message(dottalk::helpdata::MessageId::RefreshMissingFilenameText);
        return;
    }

    // Capture cursor + order state BEFORE reopening.
    const int32_t keep_recno = a.recno();

    const bool had_order = orderstate::hasOrder(a);
    const std::string order_container = had_order ? orderstate::orderName(a) : std::string{};
    const bool was_asc = orderstate::isAscending(a);

    const bool was_cnx = had_order ? orderstate::isCnx(a) : false;
    const std::string cnx_tag = (had_order && was_cnx) ? orderstate::activeTag(a) : std::string{};

    // Preflight existence so we don't accidentally close the area on a bad open attempt.
    {
        std::error_code ec;
        if (!std::filesystem::exists(abs_dbf, ec)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::RefreshFileNotFoundText,
                {{"path", abs_dbf}});
            return;
        }
    }

    try {
        // Reopen DBF (may clear existing order/index attachments internally).
        a.open(abs_dbf);

        // Restore record position (best-effort).
        if (keep_recno > 0 && keep_recno <= a.recCount()) {
            a.gotoRec(keep_recno);
        } else if (a.recCount() > 0) {
            a.top();
        }

        // Restore order state (best-effort; warn but keep DBF open if it fails).
        if (had_order && !order_container.empty()) {
            try {
                orderstate::setOrder(a, order_container);

                if (was_cnx && !cnx_tag.empty()) {
                    orderstate::setActiveTag(a, cnx_tag);
                }

                orderstate::setAscending(a, was_asc);
            } catch (const std::exception& e) {
                cli::cmdout::print_message(
                    dottalk::helpdata::MessageId::RefreshOrderRestoreWarningText,
                    {{"detail", e.what()}});
            }
        }

        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::RefreshSuccessText,
            {{"name", a.logicalName()}, {"count", std::to_string(a.recCount())}});
    }
    catch (const std::exception& e) {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::RefreshFailedText,
            {{"detail", e.what()}});
    }
}
