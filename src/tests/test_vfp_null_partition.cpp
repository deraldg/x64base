// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- THE `_NullFlags` PARTITION, AND THE OFFSET HAZARD UNDER IT.
//
// VFP stores per-row nullability in a hidden trailing column named `_NullFlags`:
// field type '0', system flag 0x01 at byte 18. It must be kept OUT of the visible
// field vector -- otherwise it is surfaced as a junk binary column -- while the
// record still physically contains it, so its position has to be remembered.
//
// THE HAZARD THIS TEST EXISTS FOR. `DbArea::fieldByteOffset_()` computes a field's
// position by ACCUMULATING the lengths of the fields before it (record_view.cpp);
// it ignores the descriptor's own `displacement` at bytes 12-15. So removing ANY
// field from the vector shifts every field after it. VFP writes `_NullFlags` last,
// which makes the partition safe -- but that is an assumption about someone else's
// writer, and an assumption in a comment is how this lane's original defect
// survived. `partitionTrailingSystemField()` DECLINES when a system field appears
// anywhere but last, and case (3) below is what proves it declines.
//
// Declining leaves the column visible, which is merely ugly and is exactly today's
// behaviour. Partitioning a non-final field would shift every subsequent offset and
// decode the whole record wrong. Degrade to the status quo loudly, not to
// corruption quietly.
//
// NO REAL FILE CAN EXERCISE THIS. No tracked table carries 0x01 at byte 18, because
// no writer has ever set it -- so unlike the binary bit (which real VFP forms prove,
// see dottalkpp_vfp_real_fixture_flags_test) these descriptors are BUILT HERE. That
// is legitimate: what is under test is our own partition arithmetic, not the
// meaning of the wire format. It is stated because the distinction is the whole
// lesson of this lane -- a hand-built fixture proves our logic and cannot prove our
// reading of someone else's format.

#include "xbase.hpp"
#include "xbase_vfp.hpp"

#include <cstdio>
#include <cstring>
#include <sstream>
#include <string>
#include <vector>

namespace {

int g_failures = 0;

void check(bool ok, const std::string& what)
{
    if (ok) return;
    std::printf("  FAIL: %s\n", what.c_str());
    ++g_failures;
}

void check_eq(long long got, long long want, const std::string& what)
{
    if (got == want) return;
    std::printf("  FAIL: %s -- got %lld, want %lld\n", what.c_str(), got, want);
    ++g_failures;
}

struct Desc {
    const char*   name;
    char          type;
    std::uint8_t  length;
    std::uint8_t  flags;      // byte 18
};

// Build a VFP field-descriptor block: 32 bytes per field, 0x0D terminator, then
// the 263-byte backlink block the VFP loader skips. Anything short of the
// backlink makes readFields throw, which would be a confusing way to fail.
std::string descriptor_block(const std::vector<Desc>& ds)
{
    std::string out;
    std::uint32_t disp = 1;                      // byte 0 is the deleted flag
    for (const Desc& d : ds) {
        char rec[32];
        std::memset(rec, 0, sizeof(rec));
        std::strncpy(rec, d.name, 11);
        rec[11] = d.type;
        std::memcpy(rec + 12, &disp, sizeof(disp));   // little-endian on target
        rec[16] = static_cast<char>(d.length);
        rec[17] = 0;
        rec[18] = static_cast<char>(d.flags);
        out.append(rec, sizeof(rec));
        disp += d.length;
    }
    out.push_back(static_cast<char>(0x0D));
    out.append(263, '\0');
    return out;
}

void load(const std::vector<Desc>& ds, xbase::DbArea& area)
{
    const std::string blob = descriptor_block(ds);
    std::istringstream in(blob, std::ios::binary);

    area.setVersionByte(0x30);                   // VFP flavor
    std::vector<xbase::VfpFieldExtras> extras;
    xbase::vfp_loader::readFields(area, in, extras);
}

// (1) The ordinary case: two real columns and a trailing _NullFlags.
void partitions_trailing_null_flags()
{
    std::printf("(1) trailing _NullFlags is partitioned out\n");

    xbase::DbArea area;
    load({ {"LNAME", 'C', 10, 0x00},
           {"AGE",   'N',  5, 0x00},
           {"_NullFlags", '0', 1, 0x01} }, area);

    check_eq(static_cast<long long>(area.fields().size()), 2,
             "the hidden column is NOT in the visible field vector");
    check_eq(static_cast<long long>(area.fieldExtras().size()), 2,
             "extras stays parallel to fields after the partition");

    const xbase::NullFlagsColumn& nf = area.nullFlagsColumn();
    check(nf.present, "the null bitmap is recorded as present");
    // 1 (deleted flag) + 10 (LNAME) + 5 (AGE)
    check_eq(static_cast<long long>(nf.offset), 16,
             "bitmap offset counts the deleted flag byte plus every visible field");
    check_eq(static_cast<long long>(nf.length), 1, "bitmap width");
    check(nf.name == "_NullFlags", "the column name is kept as the descriptor spelled it");
    check(!area.systemFieldNotLast(), "no anomaly flagged in the ordinary case");
}

// (2) THE HAZARD ITSELF: the visible fields must land where they landed before.
// If the partition ever shifted offsets, this is what would catch it.
void visible_field_offsets_are_unchanged()
{
    std::printf("(2) partitioning does not move any visible field\n");

    xbase::DbArea with_flags;
    load({ {"LNAME", 'C', 10, 0x00},
           {"AGE",   'N',  5, 0x00},
           {"_NullFlags", '0', 1, 0x01} }, with_flags);

    xbase::DbArea without;
    load({ {"LNAME", 'C', 10, 0x00},
           {"AGE",   'N',  5, 0x00} }, without);

    check_eq(static_cast<long long>(with_flags.fields().size()),
             static_cast<long long>(without.fields().size()),
             "same visible field count with and without the hidden column");

    for (std::size_t i = 0; i < without.fields().size(); ++i) {
        check(with_flags.fields()[i].name == without.fields()[i].name,
              "field " + std::to_string(i) + " has the same name");
        check_eq(with_flags.fields()[i].length, without.fields()[i].length,
                 "field " + std::to_string(i) + " has the same length");
    }
}

// (3) A system field that is NOT last: the partition must be DECLINED, the field
// must stay visible, and the anomaly must be reported rather than swallowed.
void declines_when_system_field_is_not_last()
{
    std::printf("(3) a system field that is not last blocks the partition\n");

    xbase::DbArea area;
    load({ {"_Weird", '0', 1, 0x01},          // system, but FIRST
           {"LNAME",  'C', 10, 0x00} }, area);

    check_eq(static_cast<long long>(area.fields().size()), 2,
             "the field stays VISIBLE -- declining leaves today's behaviour intact");
    check(!area.nullFlagsColumn().present,
          "no bitmap is claimed when the partition was declined");
    check(area.systemFieldNotLast(),
          "the anomaly is REPORTED, not swallowed");
}

// (4) The overwhelmingly common case today: no system field at all. Nothing must
// change, and nothing must be claimed.
void no_system_field_changes_nothing()
{
    std::printf("(4) a table with no system field is untouched\n");

    xbase::DbArea area;
    load({ {"LNAME", 'C', 10, 0x00},
           {"AGE",   'N',  5, 0x00} }, area);

    check_eq(static_cast<long long>(area.fields().size()), 2, "both fields visible");
    check(!area.nullFlagsColumn().present, "no bitmap claimed");
    check(!area.systemFieldNotLast(), "no anomaly flagged");
    check_eq(static_cast<long long>(area.fieldExtras().size()), 2,
             "extras present and parallel even when nothing is nullable");
}

// (5) extras must actually reach the area -- the promotion, not just the parse.
// This is the seam that a promotion written in DbArea::readFields() would have
// missed for x64, because that function returns early on the x64 branch.
void extras_are_promoted_onto_the_area()
{
    std::printf("(5) decoded flags reach DbArea, not just the loader's local\n");

    xbase::DbArea area;
    load({ {"PLAIN",  'C', 10, 0x00},
           {"NULLOK", 'C', 10, 0x02},          // nullable
           {"BLOB",   'M',  4, 0x04} }, area);  // binary

    check_eq(static_cast<long long>(area.fieldExtras().size()), 3, "three entries");
    if (area.fieldExtras().size() != 3) return;

    check(!area.fieldExtras()[0].nullable, "PLAIN is not nullable");
    check(area.fieldExtras()[1].nullable,  "NULLOK is nullable (0x02 at byte 18)");
    check(!area.fieldExtras()[1].binary,   "NULLOK is not binary");
    check(area.fieldExtras()[2].binary,    "BLOB is binary (0x04 at byte 18)");
    check(!area.fieldExtras()[2].nullable, "BLOB is not nullable");
}

} // namespace

int main()
{
    std::printf("AIF-091 M1 -- _NullFlags partition and the offset hazard\n");
    std::printf("  Field offsets are computed by ACCUMULATION, so removing a field\n");
    std::printf("  shifts every field after it. Only a TRAILING system field is safe.\n\n");

    partitions_trailing_null_flags();
    visible_field_offsets_are_unchanged();
    declines_when_system_field_is_not_last();
    no_system_field_changes_nothing();
    extras_are_promoted_onto_the_area();

    if (g_failures == 0) {
        std::printf("\nPASS -- the hidden column is hidden, and nothing else moved.\n");
        return 0;
    }
    std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
    return 1;
}
