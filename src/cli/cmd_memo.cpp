// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|MEMO
// command: MEMO
// category: memo
// status: supported
// noargs: usage
// effect: mixed
// mutates: memo-storage filesystem
// usage-access: MEMO USAGE
// summary:
//   Inspect and maintain x64 memo sidecar/object storage for the current work
//   area or all open work areas.
//
// usage:
//   MEMO USAGE
//   MEMO STATUS
//   MEMO STATUS ALL
//   MEMO VERIFY
//   MEMO VERIFY ALL
//   MEMO GC
//   MEMO GC ALL
//   MEMO GC CONFIRM
//   MEMO GC ALL CONFIRM
//
// notes:
//   MEMO with no arguments prints usage.
//   STATUS reports memo object/ref statistics, and prints the reason when the
//     scan reported one (2026-10-20). Before that it printed "status : ERROR"
//     with no explanation, where VERIFY had always printed "VERIFY: error: ...".
//     The counts above an error line are not measurements; the reason says so.
//   VERIFY scans memo references and reports missing/orphaned objects.
//   GC without CONFIRM is a dry run.
//   GC with CONFIRM may remove orphan memo objects and reclaim storage.
//   ALL targets all open work areas; otherwise the current work area is used.
//   A TABLE THIS SCANNER CANNOT READ REPORTS "NOT SCANNED" AND GC DOES NOT RUN
//     (2026-10-13). Memo references are decoded only as the x64 uint64 object-id
//     slot, M(8). A memo field of any other width -- M(16), which holds a
//     MemoRef token, as WORKSPACES.SNAPSHOT does -- cannot be decoded here, so
//     STATUS/VERIFY name the field and refuse rather than reporting zero
//     orphans. Before this, such a table reported "orphan objects 0 /
//     reclaimable 0" for every possible state of its store, which is a zero
//     meaning "I did not look". The refusal fires even when decodable fields
//     are also present: a partial scan would classify the undecodable field's
//     objects as orphans, and GC CONFIRM would erase live data.
//
// risk:
//   reads_memo_storage: yes
//   writes_memo_storage: MEMO GC CONFIRM forms
//   mutates_table_data: no direct DBF record mutation
//   requires_open_area: yes except usage
//
// related:
//   CALCWRITE
//   REPLACE
//   PACK
//

#include <algorithm>
#include <cctype>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

#include "memo/memo_verify.hpp"
#include "workareas.hpp"
#include "xbase.hpp"

namespace {

std::string up(std::string s)
{
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

bool is_open_area(std::size_t slot)
{
    try {
        auto* a = workareas::at(slot);
        return a && a->isOpen();
    } catch (...) {
        return false;
    }
}

std::vector<int> target_slots(bool all_flag)
{
    std::vector<int> out;

    if (!all_flag) {
        out.push_back(static_cast<int>(workareas::current_slot()));
        return out;
    }

    for (std::size_t i = 0; i < workareas::count(); ++i) {
        if (is_open_area(i)) out.push_back(static_cast<int>(i));
    }
    return out;
}

void print_memo_usage()
{
    std::cout
        << "Usage:\n"
        << "  MEMO USAGE\n"
        << "  MEMO STATUS [ALL]\n"
        << "  MEMO VERIFY [ALL]\n"
        << "  MEMO GC [ALL] [CONFIRM]\n"
        << "Notes:\n"
        << "  - MEMO GC without CONFIRM is a dry run.\n"
        << "  - MEMO GC with CONFIRM may remove orphan memo objects.\n";
}

void print_verify(const dottalk::memo::MemoScanResult& s)
{
    std::cout << "MEMO VERIFY\n";
    std::cout << "  area           : " << s.area_slot << "\n";
    std::cout << "  table          : " << s.table_name << "\n";
    std::cout << "  x64 memo fields: " << s.x64_memo_fields << "\n";
    std::cout << "  records scanned: " << s.records_scanned << "\n";
    std::cout << "  memo refs found: " << s.memo_refs_found << "\n";
    std::cout << "  empty refs     : " << s.empty_refs << "\n";
    std::cout << "  bad ids        : " << s.bad_ids << "\n";
    std::cout << "  missing objects: " << s.missing_objects << "\n";
    std::cout << "  orphan objects : " << s.orphan_objects << "\n";

    if (!s.error.empty()) {
        std::cout << "VERIFY: error: " << s.error << "\n";
    } else if (s.ok && s.orphan_objects == 0) {
        std::cout << "VERIFY: OK\n";
    } else if (s.ok) {
        std::cout << "VERIFY: warnings found.\n";
    } else {
        std::cout << "VERIFY: problems found.\n";
    }
}

void print_status(const dottalk::memo::MemoScanResult& s)
{
    std::string status = "OK";
    if (!s.ok) status = "ERROR";
    else if (s.orphan_objects > 0) status = "WARN";

    std::cout << "MEMO STATUS\n";
    std::cout << "  area           : " << s.area_slot << "\n";
    std::cout << "  table          : " << s.table_name << "\n";
    std::cout << "  backend        : DTX\n";
    std::cout << "  x64 memo fields: " << s.x64_memo_fields << "\n";
    std::cout << "  records        : " << s.records_scanned << "\n";
    std::cout << "  memo refs      : " << s.memo_refs_found << "\n";
    std::cout << "  live objects   : " << s.live_objects << "\n";
    std::cout << "  orphan objects : " << s.orphan_objects << "\n";
    std::cout << "  missing refs   : " << s.missing_objects << "\n";
    std::cout << "  empty refs     : " << s.empty_refs << "\n";
    std::cout << "  dtx bytes      : " << s.dtx_append_bytes << "\n";
    std::cout << "  largest memo   : " << s.largest_live_object_bytes << "\n";
    std::cout << "  status         : " << status << "\n";

    // A RED THAT DOES NOT SAY WHY IS HALF AN INSTRUMENT. print_verify has always
    // printed this line and print_status never did, so STATUS reported
    // "status : ERROR" sitting directly beneath "orphan objects : 0" with no
    // reason given -- a zero that is not a measurement, next to a failure that
    // does not explain itself. Found 2026-10-20 by the run that PROVED the
    // undecodable-width refusal: the refusal worked, and STATUS was the one
    // surface that would not say so.
    if (!s.error.empty()) {
        std::cout << "STATUS: error: " << s.error << "\n";
    }
}

void print_gc(const dottalk::memo::MemoScanResult& s,
              bool confirm,
              std::uint64_t removed_objects,
              std::uint64_t reclaimed_bytes,
              const std::string& error)
{
    std::cout << "MEMO GC\n";
    std::cout << "  area            : " << s.area_slot << "\n";
    std::cout << "  table           : " << s.table_name << "\n";
    std::cout << "  mode            : " << (confirm ? "confirm" : "dry-run") << "\n";
    std::cout << "  orphan objects  : " << s.orphan_objects << "\n";
    std::cout << "  reclaimable     : " << s.reclaimable_bytes << "\n";

    if (confirm) {
        std::cout << "  removed objects : " << removed_objects << "\n";
        std::cout << "  reclaimed bytes : " << reclaimed_bytes << "\n";
    }

    if (!error.empty()) {
        std::cout << "GC: error: " << error << "\n";
    } else if (!confirm) {
        std::cout << "GC: no changes made.\n";
    } else {
        std::cout << "GC complete.\n";
    }
}

} // namespace

void cmd_MEMO(xbase::DbArea& /*unused*/, std::istringstream& iss)
{
    std::string subcmd;
    iss >> subcmd;
    subcmd = up(subcmd);

    bool all_flag = false;
    bool confirm = false;

    std::string tok;
    while (iss >> tok) {
        tok = up(tok);
        if (tok == "ALL") all_flag = true;
        else if (tok == "CONFIRM") confirm = true;
    }

    if (subcmd.empty() || subcmd == "USAGE" || subcmd == "HELP" || subcmd == "?") {
        print_memo_usage();
        return;
    }

    const std::vector<int> slots = target_slots(all_flag);
    if (slots.empty()) {
        std::cout << "MEMO: no open areas.\n";
        return;
    }

    for (std::size_t i = 0; i < slots.size(); ++i) {
        const int slot = slots[i];
        auto* area = workareas::at(static_cast<std::size_t>(slot));
        if (!area || !area->isOpen()) continue;

        dottalk::memo::MemoScanResult scan;
        if (!dottalk::memo::scan_x64_memos_in_area(area->db(), slot, scan)) {
            if (subcmd == "VERIFY") print_verify(scan);
            else if (subcmd == "STATUS") print_status(scan);
            else if (subcmd == "GC") {
                std::uint64_t removed = 0;
                std::uint64_t reclaimed = 0;
                print_gc(scan, confirm, removed, reclaimed, scan.error);
            }
            if (i + 1 < slots.size()) std::cout << "\n";
            continue;
        }

        if (subcmd == "VERIFY") {
            print_verify(scan);
        } else if (subcmd == "STATUS") {
            print_status(scan);
        } else if (subcmd == "GC") {
            std::uint64_t removed = 0;
            std::uint64_t reclaimed = 0;
            std::string error;

            if (!dottalk::memo::gc_orphan_memos_in_area(area->db(),
                                                        scan,
                                                        confirm,
                                                        removed,
                                                        reclaimed,
                                                        error))
            {
                print_gc(scan, confirm, removed, reclaimed, error);
            } else {
                print_gc(scan, confirm, removed, reclaimed, error);
            }
        } else {
            print_memo_usage();
            return;
        }

        if (i + 1 < slots.size()) std::cout << "\n";
    }
}