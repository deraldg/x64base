// src/tests/test_field_codec.cpp
//
// FIELDTYPE M2 boundary proof for the binary field-type codecs.
//
// Exercises the codec registry directly (no DBF): for each binary type it encodes
// a text value into a field-width byte region and decodes it back, asserting the
// round-trip and the exact on-disk encoding at boundaries.  The text default
// (C/N/F/D/L/M) is unaffected and covered elsewhere.
//
//   I  4-byte little-endian int32            (M1, regressed here)
//   B  8-byte IEEE-754 double
//   Y  8-byte int64 currency scaled 10^4
//   T  8-byte datetime = 4-byte JDN + 4-byte milliseconds
//
// The T test also pins a KNOWN Julian Day Number (1970-01-01 == 2440588) and a
// known millisecond-of-day, so the date/time math is anchored to real values, not
// merely self-consistent.

#include <cstdint>
#include <cstring>
#include <iostream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "xbase/field_codec.hpp"

namespace {

int failures = 0;

void check(bool cond, const std::string& msg) {
    if (!cond) {
        std::cerr << "FAIL: " << msg << "\n";
        ++failures;
    }
}

// Encode `in` for a `type` field of `len` bytes, then decode the region back.
std::string roundtrip(char type, std::uint32_t len, const std::string& in) {
    xbase::FieldDef f{};
    f.type = type;
    f.length = len;
    std::vector<char> buf(len, ' ');
    std::string err;
    const auto& c = xbase::fieldcodec::codec_for(type);
    if (!c.encode(in, f, buf.data(), &err))
        return std::string("<ENCODE-FAIL:") + err + ">";
    return c.decode(buf.data(), len, f);
}

bool encode_ok(char type, std::uint32_t len, const std::string& in) {
    xbase::FieldDef f{};
    f.type = type;
    f.length = len;
    std::vector<char> buf(len, ' ');
    std::string err;
    return xbase::fieldcodec::codec_for(type).encode(in, f, buf.data(), &err);
}

std::uint32_t raw_u32le(const std::vector<char>& b, std::size_t off) {
    return static_cast<std::uint32_t>(static_cast<unsigned char>(b[off]))
         | (static_cast<std::uint32_t>(static_cast<unsigned char>(b[off + 1])) << 8)
         | (static_cast<std::uint32_t>(static_cast<unsigned char>(b[off + 2])) << 16)
         | (static_cast<std::uint32_t>(static_cast<unsigned char>(b[off + 3])) << 24);
}

}  // namespace

int main() {
    // ---- I: int32 (M1 regression) ----
    check(roundtrip('I', 4, "50000000") == "50000000", "I 50000000 round-trip (AIF-017)");
    check(roundtrip('I', 4, "2147483647") == "2147483647", "I INT32_MAX round-trip");
    check(roundtrip('I', 4, "-2147483648") == "-2147483648", "I INT32_MIN round-trip");
    check(roundtrip('I', 4, "0") == "0", "I zero round-trip");
    check(!encode_ok('I', 4, "3000000000"), "I rejects > INT32_MAX");
    check(!encode_ok('I', 4, "-3000000000"), "I rejects < INT32_MIN");
    check(!encode_ok('I', 4, "12x"), "I rejects non-numeric");
    {
        xbase::FieldDef f{}; f.type = 'I'; f.length = 4;
        std::vector<char> buf(4, ' ');
        check(xbase::fieldcodec::codec_for('I').decode(buf.data(), 4, f).empty(),
              "I all-spaces decodes to blank");
    }

    // ---- B: IEEE-754 double ----
    check(roundtrip('B', 8, "3.14159") == "3.14159", "B 3.14159 round-trip");
    check(roundtrip('B', 8, "-2.5") == "-2.5", "B -2.5 round-trip");
    check(roundtrip('B', 8, "0") == "0", "B zero round-trip");
    check(roundtrip('B', 8, "123456.789") == "123456.789", "B 123456.789 round-trip");
    check(roundtrip('B', 8, "1000000") == "1000000", "B integral double no separators");
    check(!encode_ok('B', 8, "abc"), "B rejects non-numeric");
    {
        xbase::FieldDef f{}; f.type = 'B'; f.length = 8;
        std::vector<char> buf(8, ' ');
        check(xbase::fieldcodec::codec_for('B').decode(buf.data(), 8, f).empty(),
              "B all-spaces decodes to blank");
    }

    // ---- Y: currency int64 scaled 10^4 ----
    check(roundtrip('Y', 8, "12.3456") == "12.3456", "Y 12.3456 round-trip");
    check(roundtrip('Y', 8, "-99.9999") == "-99.9999", "Y -99.9999 round-trip");
    check(roundtrip('Y', 8, "0") == "0", "Y zero round-trip");
    check(roundtrip('Y', 8, "1000000.5") == "1000000.5", "Y 1000000.5 round-trip");
    check(roundtrip('Y', 8, "1.23456") == "1.2345", "Y truncates beyond 4dp");
    check(roundtrip('Y', 8, "922337203685477.5807") == "922337203685477.5807",
          "Y near-int64-max round-trip");
    check(!encode_ok('Y', 8, "1.2.3"), "Y rejects double decimal point");
    check(!encode_ok('Y', 8, "x"), "Y rejects non-numeric");

    // ---- T: datetime = JDN + milliseconds ----
    check(roundtrip('T', 8, "20240923143000") == "20240923143000",
          "T 2024-09-23 14:30:00 round-trip");
    check(roundtrip('T', 8, "19560214000000") == "19560214000000",
          "T 1956-02-14 midnight round-trip");
    check(roundtrip('T', 8, "20240101") == "20240101000000",
          "T 8-digit date expands to midnight");
    check(roundtrip('T', 8, "") == "", "T blank round-trip");
    check(!encode_ok('T', 8, "2024"), "T rejects short stamp");
    check(!encode_ok('T', 8, "20241301000000"), "T rejects month 13");
    check(!encode_ok('T', 8, "20240101250000"), "T rejects hour 25");

    // Anchor the date/time math to known values (VFP-consistent JDN).
    {
        xbase::FieldDef f{}; f.type = 'T'; f.length = 8;
        std::vector<char> buf(8, ' ');
        std::string err;
        xbase::fieldcodec::codec_for('T').encode("19700101000000", f, buf.data(), &err);
        check(raw_u32le(buf, 0) == 2440588u, "T 1970-01-01 encodes JDN 2440588");
        check(raw_u32le(buf, 4) == 0u, "T midnight encodes 0 ms");

        std::vector<char> buf2(8, ' ');
        xbase::fieldcodec::codec_for('T').encode("20240101143000", f, buf2.data(), &err);
        // 14:30:00 -> ((14*60+30)*60)*1000 = 52,200,000 ms
        check(raw_u32le(buf2, 4) == 52200000u, "T 14:30:00 encodes 52,200,000 ms");
    }

    // ---- X: pronoun (M4 demonstrative custom type) ----
    check(roundtrip('X', 8, "she/her") == "she/her", "X single set round-trip");
    check(roundtrip('X', 8, "she/her; they/them") == "she/her; they/them",
          "X stack (multi-set) round-trip");
    check(roundtrip('X', 8, "THEY/THEM") == "they/them", "X case-insensitive");
    check(roundtrip('X', 8, "she") == "she/her", "X subject-only expands to sub/obj");
    check(roundtrip('X', 8, "he/him/his") == "he/him", "X accepts full triple");
    check(roundtrip('X', 8, "ze/zir; ask") == "ze/zir; ask", "X neopronoun + ask");
    check(roundtrip('X', 8, "") == "", "X blank round-trip");
    check(!encode_ok('X', 8, "foo/bar"), "X rejects unknown set");
    check(encode_ok('X', 8, "she;he;they;ze;xe;it;ask;she"), "X depth-8 full stack OK");
    check(!encode_ok('X', 8, "she;he;they;ze;xe;it;ask;she;he"),
          "X rejects a 9th set past depth-8");

    // ---- register_codec: the public custom-type extension point ----
    // Prove a brand-new type char the engine has never heard of can be installed
    // at runtime and immediately round-trips through the same seam.
    {
        xbase::fieldcodec::Codec demo{};
        demo.name = "demo-upper";
        demo.encode = [](const std::string& text, const xbase::FieldDef& f,
                         char* out, std::string*) -> bool {
            std::memset(out, ' ', f.length);
            const std::size_t n = text.size() < f.length ? text.size() : f.length;
            for (std::size_t i = 0; i < n; ++i) {
                const char c = text[i];
                out[i] = (c >= 'a' && c <= 'z') ? static_cast<char>(c - 'a' + 'A') : c;
            }
            return true;
        };
        demo.decode = [](const char* bytes, std::size_t len,
                         const xbase::FieldDef&) -> std::string {
            std::string s(bytes, bytes + len);
            while (!s.empty() && s.back() == ' ') s.pop_back();
            return s;
        };
        xbase::fieldcodec::register_codec('~', demo);
        check(std::string(xbase::fieldcodec::codec_for('~').name) == "demo-upper",
              "register_codec installs a runtime custom type");
        check(roundtrip('~', 6, "abc") == "ABC",
              "runtime custom codec transforms + round-trips");
    }

    if (failures == 0) {
        std::cout << "field_codec: I/B/Y/T binary codecs round-trip at boundaries; "
                     "X pronoun stack round-trips; register_codec installs a runtime "
                     "custom type; JDN/ms anchored to known values. PASS\n";
        return 0;
    }
    std::cerr << "field_codec: " << failures << " check(s) failed.\n";
    return 1;
}
