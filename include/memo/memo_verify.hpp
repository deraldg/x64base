// @dottalk.file v1
// subsystem: memo
// layer: header
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#pragma once
// @dottalk.contract
// file: include/memo/memo_verify.hpp
// subsystem: memo
// role: Declares memo or large-object interfaces for DotTalk++ storage workflows
// authority: canonical-header-contract
// mutation: token-authorized
// notes: canonical contract annotation inserted by guarded SelfDoc apply script

#include <cstdint>
#include <string>
#include <vector>

namespace xbase { class DbArea; }

namespace dottalk::memo {

struct MemoScanResult
{
    int area_slot = -1;
    std::string table_name;

    int x64_memo_fields = 0;

    // MEMO-TYPED FIELDS THIS SCANNER CANNOT DECODE -- M(n) with n != 8.
    //
    // A table with any of these was NOT SCANNED and every count below it is
    // meaningless. It is recorded rather than ignored because the old code
    // returned a clean zero for such a table, and a zero that means "I did not
    // look" is indistinguishable from a zero that means "there is no garbage".
    // scan_x64_memos_in_area() now returns false and fills `error` instead.
    int undecodable_memo_fields = 0;
    std::vector<std::string> undecodable_field_names;

    std::uint64_t records_scanned = 0;
    std::uint64_t memo_refs_found = 0;
    std::uint64_t empty_refs = 0;
    std::uint64_t bad_ids = 0;
    std::uint64_t missing_objects = 0;

    std::uint64_t live_objects = 0;
    std::uint64_t orphan_objects = 0;

    std::uint64_t largest_live_object_bytes = 0;
    std::uint64_t reclaimable_bytes = 0;
    std::uint64_t dtx_append_bytes = 0;

    std::vector<std::uint64_t> referenced_ids;
    std::vector<std::uint64_t> orphan_ids;

    bool ok = true;
    std::string error;
};

bool scan_x64_memos_in_area(xbase::DbArea& area,
                            int area_slot,
                            MemoScanResult& out);

bool gc_orphan_memos_in_area(xbase::DbArea& area,
                             const MemoScanResult& scan,
                             bool confirm,
                             std::uint64_t& removed_objects,
                             std::uint64_t& reclaimed_bytes,
                             std::string& error);

} // namespace dottalk::memo
