// @dottalk.file v1
// subsystem: tests
// layer: smoke
// project: project.x64base.runtime
// lane: dbf-vfp-type-support
// status: experimental
//
// AIF-091 M1 -- THE FIELD FLAGS LIVE AT BYTE 18, AND THIS IS WHAT SAYS SO.
//
// Until 2026-09-04 `VfpField::flags` sat at BYTE 23. Byte 23 is the autoincrement
// STEP value; byte 18 is the field flags. So `ex.nullable = (vf.flags & 0x02)` read
// bit 1 of the step byte and the real flags byte was swallowed inside `reserved1`.
// The struct was a faithful dBASE III descriptor (work-area id at 20, SET FIELDS
// flag at 23) wearing a VFP name.
//
// WHY NOTHING CAUGHT IT: measured the same day, every VFP- and x64-flavor table in
// this repository carries ZERO at byte 18 AND ZERO at byte 23. The wrong byte and
// the right byte give the same answer on every file we own, so the decoder was
// correct by coincidence on all existing data and would have been silently wrong on
// the first real nullable table. A default that never changes on any path anyone
// runs cannot go red -- the AIF-123 shape.
//
// THE DISCRIMINATOR IS `descriptor_decoy_bytes`: it puts 0x02 (nullable) at byte 18
// and 0x04 (binary) at byte 23, so the two layouts give OPPOSITE answers. Under the
// corrected struct the field reads nullable-and-not-binary; under the old one it
// read binary-and-not-nullable.
//
// Source: Microsoft, "Table File Structure" (VFP field subrecord); Hentzen et al.,
// Hacker's Guide to Visual FoxPro s1c2 ("bit 0 of byte 18").

#include "xbase_vfp.hpp"

#include <cstdio>
#include <cstddef>
#include <cstring>

namespace {

int g_failures = 0;

void check(bool ok, const char* what)
{
    if (ok) return;
    std::printf("  FAIL: %s\n", what);
    ++g_failures;
}

void check_eq(long long got, long long want, const char* what)
{
    if (got == want) return;
    std::printf("  FAIL: %s -- got %lld, want %lld\n", what, got, want);
    ++g_failures;
}

using xbase::VfpField;
using xbase::FieldRec;
using xbase::decode_field_flags;
using xbase::descriptor_carries_field_flags;

// The documented layout, restated at runtime so a failure is readable rather than
// only a compile error. The static_asserts in the header are the real guard.
void layout()
{
    std::printf("VFP field subrecord layout (Microsoft table file structure)\n");
    check_eq(static_cast<long long>(sizeof(VfpField)), 32, "descriptor is 32 bytes");
    check_eq(static_cast<long long>(offsetof(VfpField, length)),       16, "length @16");
    check_eq(static_cast<long long>(offsetof(VfpField, decimals)),     17, "decimals @17");
    check_eq(static_cast<long long>(offsetof(VfpField, flags)),        18, "FIELD FLAGS @18");
    check_eq(static_cast<long long>(offsetof(VfpField, autoinc_next)), 19, "autoinc next @19");
    check_eq(static_cast<long long>(offsetof(VfpField, autoinc_step)), 23, "autoinc step @23");
    check_eq(static_cast<long long>(offsetof(VfpField, reserved)),     24, "reserved @24");

    // This is what lets an x64 table carry flags without changing its parse shape.
    check_eq(static_cast<long long>(offsetof(FieldRec, reserved)), 18,
             "classic reserved[0] IS byte 18 (x64 inherits the flags byte)");
}

void flag_decode()
{
    std::printf("Flag byte decode\n");

    auto ex = decode_field_flags(0x00);
    check(!ex.system && !ex.nullable && !ex.binary && !ex.autoincrement, "0x00 sets nothing");

    ex = decode_field_flags(0x01);
    check(ex.system,    "0x01 -> system column");
    check(!ex.nullable, "0x01 does not imply nullable");

    ex = decode_field_flags(0x02);
    check(ex.nullable, "0x02 -> can store null");
    check(!ex.binary,  "0x02 does not imply binary");

    ex = decode_field_flags(0x04);
    check(ex.binary,    "0x04 -> binary");
    check(!ex.nullable, "0x04 does not imply nullable");

    ex = decode_field_flags(0x06);
    check(ex.nullable && ex.binary, "0x06 -> nullable AND binary (MS lists it explicitly)");

    // THE SUBTLETY. 0x0C is 0x04|0x08, so a naive `& 0x04` calls an autoincrementing
    // column BINARY. It is not.
    ex = decode_field_flags(0x0C);
    check(ex.autoincrement, "0x0C -> autoincrementing");
    check(!ex.binary,       "0x0C is NOT binary, even though it carries the 0x04 bit");

    ex = decode_field_flags(0x0E);
    check(ex.autoincrement, "0x0E -> autoincrementing");
    check(ex.nullable,      "0x0E -> also nullable");
    check(!ex.binary,       "0x0E is still not binary");
}

void flavors()
{
    std::printf("Which flavors carry field flags at byte 18\n");
    check(descriptor_carries_field_flags(0x30), "0x30 VFP carries flags");
    check(descriptor_carries_field_flags(0x31), "0x31 VFP+autoinc carries flags");
    check(descriptor_carries_field_flags(0x32), "0x32 VFP+varchar carries flags");
    check(descriptor_carries_field_flags(0x64), "0x64 X64 carries flags BY INHERITANCE");

    // Classic flavors must NOT be read this way: in dBASE III that region is a
    // work-area id and a SET FIELDS flag, and reading it as flags would invent
    // nullability out of unrelated bytes.
    check(!descriptor_carries_field_flags(0x03), "0x03 classic does NOT");
    check(!descriptor_carries_field_flags(0x83), "0x83 classic+memo does NOT");
    check(!descriptor_carries_field_flags(0xF5), "0xF5 Fox 2.6 does NOT");
}

// THE DISCRIMINATOR: opposite answers under the two layouts.
void descriptor_decoy_bytes()
{
    std::printf("Decoy descriptor: 0x02 at byte 18, 0x04 at byte 23\n");

    unsigned char raw[32];
    std::memset(raw, 0, sizeof(raw));
    std::memcpy(raw, "GPA", 3);
    raw[11] = 'N';     // type
    raw[16] = 4;       // length
    raw[17] = 2;       // decimals
    raw[18] = 0x02;    // FIELD FLAGS: can store null
    raw[23] = 0x04;    // autoincrement STEP -- looks like "binary" if misread as flags

    VfpField vf{};
    std::memcpy(&vf, raw, sizeof(vf));

    check_eq(vf.flags,        0x02, "flags reads byte 18");
    check_eq(vf.autoinc_step, 0x04, "autoinc step reads byte 23");
    check_eq(vf.length,          4, "length still reads byte 16");
    check_eq(vf.decimals,        2, "decimals still reads byte 17");

    const auto ex = decode_field_flags(vf.flags);
    check(ex.nullable, "decoy field is NULLABLE  (under the old layout it was not)");
    check(!ex.binary,  "decoy field is NOT binary (under the old layout it was)");
}

} // namespace

int main()
{
    std::printf("AIF-091 M1 -- VFP/x64 field descriptor flags byte\n");
    std::printf("  Byte 18 is the field flags. Byte 23 is the autoincrement step.\n");
    std::printf("  x64 (0x64) inherits the descriptor, so it carries flags too.\n\n");

    layout();
    flag_decode();
    flavors();
    descriptor_decoy_bytes();

    if (g_failures == 0) {
        std::printf("\nPASS -- the flags byte is read where the format puts it.\n");
        return 0;
    }
    std::printf("\nFAIL -- %d expectation(s) missed.\n", g_failures);
    return 1;
}
