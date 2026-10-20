// @dottalk.file v1
// subsystem: cli
// layer: helper
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

#include "memo/memo_verify.hpp"

#include <algorithm>
#include <cstdint>
#include <set>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase/x64_memo_slot.hpp"
#include "memo/memo_auto.hpp"
#include "memo/memostore.hpp"

namespace dottalk::memo {
namespace {

// THE PREDICATE AND THE PARSER HAVE ONE OWNER -- xbase/x64_memo_slot.hpp (R149).
// What stood here were two of ten identical private bodies. Deleting them is
// the point: this predicate decides what a field READ returns, whether a value
// may be treated as an object id, and whether a WRITE lays down raw bytes --
// three layers that must not be able to disagree.
using xbase::is_x64_memo_field;
using xbase::parse_u64_or_zero;

static dottalk::memo::MemoStore* memo_store_for_area(xbase::DbArea& area) noexcept
{
    auto* backend = cli_memo::memo_backend_for(area);
    if (!backend) return nullptr;
    return dynamic_cast<dottalk::memo::MemoStore*>(backend);
}

// Memo-typed fields whose WIDTH this scanner cannot decode. See the long note
// in scan_x64_memos_in_area() for why their presence refuses the scan outright.
static std::vector<std::string> collect_undecodable_memo_fields(const xbase::DbArea& area)
{
    std::vector<std::string> out;
    if (area.versionByte() != xbase::DBF_VERSION_64) return out;

    // ONE OWNER FOR THE WIDTH QUESTION (R149) -- the tenth place this predicate
    // was written down, and the one that decides whether GC may run at all.
    for (const auto& f : area.fields()) {
        if (xbase::is_undecodable_x64_memo_field(f, /*is_x64=*/true)) {
            out.push_back(f.name);
        }
    }
    return out;
}

static std::vector<int> collect_x64_memo_fields(const xbase::DbArea& area)
{
    std::vector<int> out;
    if (area.versionByte() != xbase::DBF_VERSION_64) return out;

    for (int i = 1; i <= area.fieldCount(); ++i) {
        if (is_x64_memo_field(area, i))
            out.push_back(i);
    }
    return out;
}

} // namespace

bool scan_x64_memos_in_area(xbase::DbArea& area,
                            int area_slot,
                            MemoScanResult& out)
{
    out = MemoScanResult{};
    out.area_slot = area_slot;

    try {
        out.table_name = area.logicalName().empty() ? area.name() : area.logicalName();
    } catch (...) {
        out.table_name.clear();
    }

    if (!area.isOpen()) {
        out.ok = false;
        out.error = "area is not open";
        return false;
    }

    auto* store = memo_store_for_area(area);
    if (!store) {
        out.ok = false;
        out.error = "memo backend not attached";
        return false;
    }

    const std::vector<int> memo_fields = collect_x64_memo_fields(area);
    out.x64_memo_fields = static_cast<int>(memo_fields.size());

    // A STORE THIS SCANNER CANNOT READ MUST NOT REPORT A CLEAN ZERO.
    //
    // is_x64_memo_field() matches type 'M' at exactly X64_MEMO_FIELD_LEN (8) --
    // the uint64 object-id slot. A SECOND CONVENTION EXISTS: WORKSPACES.SNAPSHOT
    // is M(16), a 16-hex MemoRef token, deliberately built that way and read
    // back with get_by_name() like a character field. For that table
    // collect_x64_memo_fields() returns EMPTY, and until 2026-10-13 this
    // function then took the early return below -- ABOVE the orphan computation
    // -- so MEMO VERIFY and MEMO GC reported `orphan objects 0` and
    // `reclaimable 0` FOR EVERY POSSIBLE STATE OF THE STORE. Not a judgement
    // that the payloads were reachable; it had never looked at the field.
    //
    // THAT ZERO WAS PROTECTING THE WORKSPACE LINEAGE BY ACCIDENT, and an
    // accident is not a guarantee. It equally hid any REAL orphan in that store,
    // which is the same instrument-that-cannot-fail shape this tree keeps
    // finding: a green that means "I did not look".
    //
    // THE MIXED CASE IS THE DANGEROUS ONE and is why this refuses even when
    // decodable fields exist. A table holding BOTH an M(8) and an M(16) field
    // would scan the M(8) references, miss the M(16) ones, and then report the
    // objects those tokens name as ORPHANS -- and MEMO GC CONFIRM would erase
    // live data. So the test is "any undecodable field", not "no decodable
    // fields".
    //
    // Returning false is the whole mechanism: cmd_MEMO's caller prints `error`
    // and SKIPS gc_orphan_memos_in_area entirely, so GC cannot run on a store
    // that was never scanned. Widening the predicate instead would make those
    // payloads collectable, and that is a retention ruling, not a scanner's
    // decision.
    out.undecodable_field_names = collect_undecodable_memo_fields(area);
    out.undecodable_memo_fields = static_cast<int>(out.undecodable_field_names.size());

    if (out.undecodable_memo_fields > 0) {
        std::string names;
        for (std::size_t i = 0; i < out.undecodable_field_names.size(); ++i) {
            if (i) names += ", ";
            names += out.undecodable_field_names[i];
        }
        out.dtx_append_bytes = store->append_bytes();
        out.live_objects = store->live_object_count();
        out.ok = false;
        out.error = "NOT SCANNED -- " + std::to_string(out.undecodable_memo_fields)
                  + " memo field(s) of a width this scanner cannot decode ("
                  + names + "); M(n) with n != 8 is not an object-id slot."
                  + " The counts in this report are therefore not measurements,"
                  + " and GC was not run.";
        return false;
    }

    if (memo_fields.empty()) {
        out.dtx_append_bytes = store->append_bytes();
        out.live_objects = store->live_object_count();
        return true;
    }

    std::set<std::uint64_t> referenced_ids_set;

    const int recs = area.recCount();
    for (int r = 1; r <= recs; ++r) {
        if (!area.gotoRec(r)) continue;
        if (!area.readCurrent()) continue;

        ++out.records_scanned;

        for (int field1 : memo_fields) {
            std::string raw;
            try {
                raw = area.get(field1);
            } catch (...) {
                raw.clear();
            }

            if (raw.empty()) {
                ++out.empty_refs;
                continue;
            }

            bool parse_ok = true;
            const std::uint64_t id = parse_u64_or_zero(raw, parse_ok);

            if (!parse_ok) {
                ++out.bad_ids;
                continue;
            }

            if (id == 0) {
                ++out.empty_refs;
                continue;
            }

            ++out.memo_refs_found;
            referenced_ids_set.insert(id);

            if (!store->exists_id(id)) {
                ++out.missing_objects;
            }
        }
    }

    out.referenced_ids.assign(referenced_ids_set.begin(), referenced_ids_set.end());

    std::vector<std::uint64_t> live_ids;
    if (!store->list_live_ids(live_ids)) {
        out.ok = false;
        out.error = "could not enumerate live memo ids";
        return false;
    }

    out.live_objects = static_cast<std::uint64_t>(live_ids.size());
    out.dtx_append_bytes = store->append_bytes();

    std::set<std::uint64_t> live_set(live_ids.begin(), live_ids.end());

    for (std::uint64_t id : live_ids) {
        std::uint64_t bytes = 0;
        std::string ignored;
        if (store->get_object_size_id(id, bytes, &ignored)) {
            if (bytes > out.largest_live_object_bytes)
                out.largest_live_object_bytes = bytes;
        }

        if (referenced_ids_set.find(id) == referenced_ids_set.end()) {
            out.orphan_ids.push_back(id);
            ++out.orphan_objects;
            out.reclaimable_bytes += bytes;
        }
    }

    out.ok = (out.bad_ids == 0 && out.missing_objects == 0);
    return true;
}

bool gc_orphan_memos_in_area(xbase::DbArea& area,
                             const MemoScanResult& scan,
                             bool confirm,
                             std::uint64_t& removed_objects,
                             std::uint64_t& reclaimed_bytes,
                             std::string& error)
{
    removed_objects = 0;
    reclaimed_bytes = 0;
    error.clear();

    if (!area.isOpen()) {
        error = "area is not open";
        return false;
    }

    auto* store = memo_store_for_area(area);
    if (!store) {
        error = "memo backend not attached";
        return false;
    }

    if (!confirm) {
        reclaimed_bytes = scan.reclaimable_bytes;
        return true;
    }

    for (std::uint64_t id : scan.orphan_ids) {
        std::uint64_t bytes = 0;
        std::string ignored;
        (void)store->get_object_size_id(id, bytes, &ignored);

        if (!store->erase_id(id, &error)) {
            return false;
        }

        ++removed_objects;
        reclaimed_bytes += bytes;
    }

    return true;
}

} // namespace dottalk::memo