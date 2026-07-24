// Field-type codec registry (FIELDTYPE lane, M1).
//
// M1 ships the fixed-width text codec (byte-for-byte the legacy behavior for
// C/N/F/D/L/M) and the `I` int32 codec (4-byte little-endian), which retires the
// `SID I` truncation (AIF-017). B/Y/T binary codecs and custom-type examples land
// in later milestones; until registered, those types keep the text codec.

#include "xbase/field_codec.hpp"
#include "xbase.hpp"   // xbase::FieldDef

#include <array>
#include <cerrno>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iomanip>
#include <locale>
#include <sstream>
#include <string>

namespace xbase::fieldcodec {
namespace {

std::string rtrim_copy(std::string s) {
    // Match DbArea::rtrim exactly (trailing spaces only) so the text codec is a
    // byte-for-byte replacement for the legacy fixed-width decode.
    while (!s.empty() && s.back() == ' ') s.pop_back();
    return s;
}

bool all_spaces(const char* b, std::size_t n) {
    for (std::size_t i = 0; i < n; ++i) {
        if (b[i] != ' ') return false;
    }
    return true;
}

// Drop spaces so a space-padded field region parses like its trimmed value.
std::string strip_spaces(const std::string& t) {
    std::string s;
    s.reserve(t.size());
    for (char c : t) {
        if (c != ' ') s.push_back(c);
    }
    return s;
}

// ---- explicit little-endian byte assembly (host-endian independent) ----
std::uint32_t rd_u32le(const char* b) {
    return static_cast<std::uint32_t>(static_cast<unsigned char>(b[0]))
         | (static_cast<std::uint32_t>(static_cast<unsigned char>(b[1])) << 8)
         | (static_cast<std::uint32_t>(static_cast<unsigned char>(b[2])) << 16)
         | (static_cast<std::uint32_t>(static_cast<unsigned char>(b[3])) << 24);
}
void wr_u32le(char* o, std::uint32_t v) {
    o[0] = static_cast<char>(v & 0xFFu);
    o[1] = static_cast<char>((v >> 8) & 0xFFu);
    o[2] = static_cast<char>((v >> 16) & 0xFFu);
    o[3] = static_cast<char>((v >> 24) & 0xFFu);
}
std::uint64_t rd_u64le(const char* b) {
    std::uint64_t v = 0;
    for (int i = 0; i < 8; ++i)
        v |= static_cast<std::uint64_t>(static_cast<unsigned char>(b[i])) << (8 * i);
    return v;
}
void wr_u64le(char* o, std::uint64_t v) {
    for (int i = 0; i < 8; ++i)
        o[i] = static_cast<char>((v >> (8 * i)) & 0xFFu);
}
double rd_f64le(const char* b) {
    const std::uint64_t u = rd_u64le(b);
    double d = 0.0;
    std::memcpy(&d, &u, sizeof(d));
    return d;
}
void wr_f64le(char* o, double d) {
    std::uint64_t u = 0;
    std::memcpy(&u, &d, sizeof(u));
    wr_u64le(o, u);
}

// Canonical decimal for a double: fixed 10dp, trailing zeros/point trimmed,
// classic locale (no thousands separators).  Mirrors the engine's existing
// to_string_trim(v, 10) convention for B fields.
std::string fmt_double_canonical(double d) {
    std::ostringstream o;
    o.imbue(std::locale::classic());
    o << std::fixed << std::setprecision(10) << d;
    std::string s = o.str();
    if (s.find('.') != std::string::npos) {
        while (!s.empty() && s.back() == '0') s.pop_back();
        if (!s.empty() && s.back() == '.') s.pop_back();
    }
    return s.empty() ? "0" : s;
}

// int64 scaled by 10^4 -> decimal text (4dp, trailing zeros/point trimmed).
std::string fmt_scaled_1e4(std::int64_t scaled) {
    const bool neg = scaled < 0;
    // Magnitude without UB at INT64_MIN.
    std::uint64_t a = neg ? (~static_cast<std::uint64_t>(scaled) + 1ULL)
                          : static_cast<std::uint64_t>(scaled);
    const std::uint64_t ip = a / 10000ULL;
    const std::uint64_t fp = a % 10000ULL;
    char frac[8];
    std::snprintf(frac, sizeof(frac), "%04llu", static_cast<unsigned long long>(fp));
    std::string s = (neg ? "-" : "") + std::to_string(ip) + "." + frac;
    while (!s.empty() && s.back() == '0') s.pop_back();
    if (!s.empty() && s.back() == '.') s.pop_back();
    return s;
}

// Exact decimal parse -> int64 scaled by 10^4 (no float rounding error).
bool parse_scaled_1e4(const std::string& s, std::int64_t& out) {
    std::size_t i = 0;
    bool neg = false;
    if (i < s.size() && (s[i] == '+' || s[i] == '-')) { neg = (s[i] == '-'); ++i; }
    std::string ip, fp;
    bool dot = false, any = false;
    for (; i < s.size(); ++i) {
        const char c = s[i];
        if (c == '.') { if (dot) return false; dot = true; continue; }
        if (c < '0' || c > '9') return false;
        any = true;
        (dot ? fp : ip).push_back(c);
    }
    if (!any) return false;
    while (fp.size() < 4) fp.push_back('0');
    if (fp.size() > 4) fp.resize(4);           // truncate beyond 4dp
    long long ipv = 0, fpv = 0;
    try {
        if (!ip.empty()) ipv = std::stoll(ip);
        fpv = std::stoll(fp);
    } catch (...) { return false; }
    if (ipv > (INT64_MAX - fpv) / 10000) return false;   // overflow guard
    const long long scaled = ipv * 10000 + fpv;
    out = neg ? -scaled : scaled;
    return true;
}

// ---- Gregorian <-> Julian Day Number (VFP DateTime date part) ----
std::int32_t gregorian_to_jdn(int y, int m, int d) {
    const int a = (14 - m) / 12;
    const int yy = y + 4800 - a;
    const int mm = m + 12 * a - 3;
    return d + (153 * mm + 2) / 5 + 365 * yy + yy / 4 - yy / 100 + yy / 400 - 32045;
}
void jdn_to_gregorian(std::int32_t jdn, int& y, int& m, int& d) {
    long a = jdn + 32044;
    long b = (4 * a + 3) / 146097;
    long c = a - (146097 * b) / 4;
    long dd = (4 * c + 3) / 1461;
    long e = c - (1461 * dd) / 4;
    long mm = (5 * e + 2) / 153;
    d = static_cast<int>(e - (153 * mm + 2) / 5 + 1);
    m = static_cast<int>(mm + 3 - 12 * (mm / 10));
    y = static_cast<int>(100 * b + dd - 4800 + mm / 10);
}

// ---- text (default) codec: exactly the legacy fixed-width behavior ----
std::string text_decode(const char* bytes, std::size_t len, const FieldDef& /*f*/) {
    return rtrim_copy(std::string(bytes, bytes + len));
}
bool text_encode(const std::string& text, const FieldDef& f, char* out,
                 std::string* /*err*/) {
    // Caller pre-filled the region with spaces; copy up to f.length (legacy: a
    // longer value is truncated, a shorter one stays space-padded).
    const std::size_t n = (text.size() <= f.length) ? text.size()
                                                     : static_cast<std::size_t>(f.length);
    if (n) std::memcpy(out, text.data(), n);
    return true;
}

// ---- I: 4-byte little-endian int32 (explicit LE, not host-endian dependent) ----
std::string i32_decode(const char* bytes, std::size_t len, const FieldDef& /*f*/) {
    // Freshly appended / blank records carry spaces; treat that as empty, not garbage.
    if (len < 4 || all_spaces(bytes, len)) return {};
    const std::uint32_t u =
          static_cast<std::uint32_t>(static_cast<unsigned char>(bytes[0]))
        | (static_cast<std::uint32_t>(static_cast<unsigned char>(bytes[1])) << 8)
        | (static_cast<std::uint32_t>(static_cast<unsigned char>(bytes[2])) << 16)
        | (static_cast<std::uint32_t>(static_cast<unsigned char>(bytes[3])) << 24);
    return std::to_string(static_cast<std::int32_t>(u));
}
bool i32_encode(const std::string& text, const FieldDef& /*f*/, char* out,
                std::string* err) {
    std::string s;
    for (char c : text) {
        if (c != ' ') s.push_back(c);
    }
    std::int32_t v = 0;
    if (!s.empty()) {
        try {
            std::size_t pos = 0;
            const long long ll = std::stoll(s, &pos);
            if (pos != s.size()) {                 // reject trailing non-digits ("12x")
                if (err) *err = "invalid int32";
                return false;
            }
            if (ll < static_cast<long long>(INT32_MIN) ||
                ll > static_cast<long long>(INT32_MAX)) {
                if (err) *err = "int32 out of range";
                return false;
            }
            v = static_cast<std::int32_t>(ll);
        } catch (...) {
            if (err) *err = "invalid int32";
            return false;
        }
    }
    const std::uint32_t u = static_cast<std::uint32_t>(v);
    out[0] = static_cast<char>(u & 0xFFu);
    out[1] = static_cast<char>((u >> 8) & 0xFFu);
    out[2] = static_cast<char>((u >> 16) & 0xFFu);
    out[3] = static_cast<char>((u >> 24) & 0xFFu);
    return true;
}

// ---- B: 8-byte IEEE-754 double (little-endian) ----
std::string dbl_decode(const char* bytes, std::size_t len, const FieldDef& /*f*/) {
    if (len < 8 || all_spaces(bytes, len)) return {};
    return fmt_double_canonical(rd_f64le(bytes));
}
bool dbl_encode(const std::string& text, const FieldDef& /*f*/, char* out,
                std::string* err) {
    const std::string s = strip_spaces(text);
    double d = 0.0;
    if (!s.empty()) {
        errno = 0;
        char* end = nullptr;
        d = std::strtod(s.c_str(), &end);
        if (end == s.c_str() || *end != '\0' || errno == ERANGE || !std::isfinite(d)) {
            if (err) *err = "invalid double";
            return false;
        }
    }
    wr_f64le(out, d);
    return true;
}

// ---- Y: 8-byte int64 currency, value scaled by 10^4 (little-endian) ----
std::string cur_decode(const char* bytes, std::size_t len, const FieldDef& /*f*/) {
    if (len < 8 || all_spaces(bytes, len)) return {};
    return fmt_scaled_1e4(static_cast<std::int64_t>(rd_u64le(bytes)));
}
bool cur_encode(const std::string& text, const FieldDef& /*f*/, char* out,
                std::string* err) {
    const std::string s = strip_spaces(text);
    std::int64_t scaled = 0;
    if (!s.empty() && !parse_scaled_1e4(s, scaled)) {
        if (err) *err = "invalid currency";
        return false;
    }
    wr_u64le(out, static_cast<std::uint64_t>(scaled));
    return true;
}

// ---- T: 8-byte datetime = 4-byte JDN + 4-byte milliseconds (little-endian) ----
// Canonical engine text is "YYYYMMDDHHMMSS"; encode also accepts "YYYYMMDD"
// (midnight).  All-zero bytes decode to blank (append-blank / cleared datetime).
std::string dt_decode(const char* bytes, std::size_t len, const FieldDef& /*f*/) {
    if (len < 8 || all_spaces(bytes, len)) return {};
    const std::int32_t jdn = static_cast<std::int32_t>(rd_u32le(bytes));
    const std::int32_t ms  = static_cast<std::int32_t>(rd_u32le(bytes + 4));
    if (jdn == 0 && ms == 0) return {};
    int y = 0, m = 0, d = 0;
    jdn_to_gregorian(jdn, y, m, d);
    const int totsec = (ms >= 0 ? ms : 0) / 1000;
    const int hh = totsec / 3600;
    const int mi = (totsec % 3600) / 60;
    const int ss = totsec % 60;
    char buf[16];
    std::snprintf(buf, sizeof(buf), "%04d%02d%02d%02d%02d%02d", y, m, d, hh, mi, ss);
    return std::string(buf);
}
bool dt_encode(const std::string& text, const FieldDef& /*f*/, char* out,
               std::string* err) {
    const std::string s = strip_spaces(text);
    if (s.empty()) { wr_u32le(out, 0); wr_u32le(out + 4, 0); return true; }
    if (s.size() != 8 && s.size() != 14) {
        if (err) *err = "invalid datetime (expected YYYYMMDD or YYYYMMDDHHMMSS)";
        return false;
    }
    for (char c : s) {
        if (c < '0' || c > '9') { if (err) *err = "invalid datetime"; return false; }
    }
    auto num = [&](std::size_t off, std::size_t n) {
        return std::atoi(s.substr(off, n).c_str());
    };
    const int y = num(0, 4), m = num(4, 2), d = num(6, 2);
    int hh = 0, mi = 0, ss = 0;
    if (s.size() == 14) { hh = num(8, 2); mi = num(10, 2); ss = num(12, 2); }
    if (m < 1 || m > 12 || d < 1 || d > 31 ||
        hh > 23 || mi > 59 || ss > 59) {
        if (err) *err = "invalid datetime (out of range)";
        return false;
    }
    wr_u32le(out, static_cast<std::uint32_t>(gregorian_to_jdn(y, m, d)));
    wr_u32le(out + 4, static_cast<std::uint32_t>(((hh * 60 + mi) * 60 + ss) * 1000));
    return true;
}

// ============================================================================
//  DEMO CUSTOM TYPE  'X'  — pronoun / preferred form of address.
//
//  FIELDTYPE M4 worked example.  Its whole point: a field type the base engine
//  has never heard of plugs into the SAME Codec model as the built-ins, with
//  nothing X-specific in the storage seam.  An out-of-tree extension would define
//  exactly this and call `fieldcodec::register_codec('X', ...)` at startup; here
//  it is registered alongside the built-ins so the demo needs no init wiring.
//
//  Shape: a fixed-width, depth-N *stack* of pronoun-set codes (1 byte each),
//  byte 0 = primary / top of stack.  Canonical text is the ordered sets joined
//  by "; ", each shown as "subject/object" (e.g. "she/her; they/them").
//
//  A pronoun set is 3-dimensional grammatically — subject / object / possessive
//  (she / her / hers).  The codec stores one code per set; the three forms are
//  derivable from it (a future PSUBJ/POBJ/PPOSS function layer).  The codec's job
//  stops at faithful bytes<->text: context-aware resolution ("which set here")
//  and push/pop of the stack are left to a function/command layer above, so
//  storage stays pure.
// ============================================================================
struct PronounSet {
    std::uint8_t code;
    const char* subject;
    const char* object;
    const char* possessive;
};
const PronounSet kPronounSets[] = {
    {0x01, "she",  "her",  "hers"},
    {0x02, "he",   "him",  "his"},
    {0x03, "they", "them", "theirs"},
    {0x04, "ze",   "zir",  "zirs"},
    {0x05, "xe",   "xem",  "xyrs"},
    {0x06, "it",   "it",   "its"},
    {0xFF, "ask",  "ask",  "ask"},   // prefers to be asked / custom
};

std::string lc_copy(const std::string& s) {
    std::string r = s;
    for (char& c : r)
        if (c >= 'A' && c <= 'Z') c = static_cast<char>(c - 'A' + 'a');
    return r;
}
std::string trim_ws(const std::string& s) {
    std::size_t a = 0, b = s.size();
    while (a < b && (s[a] == ' ' || s[a] == '\t')) ++a;
    while (b > a && (s[b - 1] == ' ' || s[b - 1] == '\t')) --b;
    return s.substr(a, b - a);
}
const PronounSet* pronoun_set_for_code(std::uint8_t code) {
    for (const auto& p : kPronounSets)
        if (p.code == code) return &p;
    return nullptr;
}
// Match a user token ("she", "she/her", "she/her/hers") to a set code; 0 = none.
std::uint8_t pronoun_code_for_token(const std::string& tok_in) {
    const std::string tok = lc_copy(trim_ws(tok_in));
    if (tok.empty()) return 0x00;
    for (const auto& p : kPronounSets) {
        const std::string sub = p.subject;
        const std::string so  = sub + "/" + p.object;
        const std::string sop = so + "/" + p.possessive;
        if (tok == sub || tok == so || tok == sop) return p.code;
    }
    return 0x00;
}

std::string pronoun_decode(const char* bytes, std::size_t len, const FieldDef& /*f*/) {
    if (len == 0 || all_spaces(bytes, len)) return {};
    std::string out;
    for (std::size_t i = 0; i < len; ++i) {
        const std::uint8_t code =
            static_cast<std::uint8_t>(static_cast<unsigned char>(bytes[i]));
        if (code == 0x00 || code == 0x20) break;     // end of stack
        const PronounSet* p = pronoun_set_for_code(code);
        if (!p) continue;                            // skip an unknown byte
        if (!out.empty()) out += "; ";
        out += p->subject;
        if (std::strcmp(p->subject, p->object) != 0) {   // "she/her" but just "ask"/"it"
            out += '/';
            out += p->object;
        }
    }
    return out;
}
bool pronoun_encode(const std::string& text, const FieldDef& f, char* out,
                    std::string* err) {
    std::memset(out, 0x00, f.length);                // clear stack (0x00 = empty)
    const std::string t = trim_ws(text);
    if (t.empty()) return true;                      // blank clears
    std::size_t slot = 0, start = 0;
    for (;;) {
        const std::size_t semi = t.find(';', start);
        std::string tok = (semi == std::string::npos) ? t.substr(start)
                                                       : t.substr(start, semi - start);
        tok = trim_ws(tok);
        if (!tok.empty()) {
            const std::uint8_t code = pronoun_code_for_token(tok);
            if (code == 0x00) {
                if (err) *err = "unknown pronoun set '" + tok + "'";
                return false;
            }
            if (slot >= f.length) {
                if (err) *err = "too many pronoun sets (max " +
                                std::to_string(f.length) + ")";
                return false;
            }
            out[slot++] = static_cast<char>(code);
        }
        if (semi == std::string::npos) break;
        start = semi + 1;
    }
    return true;
}

const Codec kText     { text_decode, text_encode, "text" };
const Codec kInt32    { i32_decode,  i32_encode,  "int32" };
const Codec kDouble   { dbl_decode,  dbl_encode,  "double" };
const Codec kCurrency { cur_decode,  cur_encode,  "currency" };
const Codec kDateTime { dt_decode,   dt_encode,   "datetime" };
const Codec kPronoun  { pronoun_decode, pronoun_encode, "pronoun" };

std::array<Codec, 256>& table() {
    static std::array<Codec, 256> t = [] {
        std::array<Codec, 256> a{};
        for (auto& c : a) c = kText;                    // default every type to text
        a[static_cast<unsigned char>('I')] = kInt32;    // built-in int32
        a[static_cast<unsigned char>('B')] = kDouble;   // built-in IEEE-754 double
        a[static_cast<unsigned char>('Y')] = kCurrency; // built-in int64/10^4 currency
        a[static_cast<unsigned char>('T')] = kDateTime; // built-in JDN+ms datetime
        a[static_cast<unsigned char>('X')] = kPronoun;  // custom type 'X' (M4/M4b)
        return a;
    }();
    return t;
}

// Field-type metadata used by the CREATE / validation chain (M4b).  Everything a
// registered type needs lives here, in ONE place, so the chain never needs a
// per-type switch edit.  The demo type 'X' is registered here — codec above,
// metadata below — and nowhere else (no datatype-catalog / supports_type_now /
// create-width edits).
std::array<FieldTypeMeta, 256>& meta_table() {
    static std::array<FieldTypeMeta, 256> m = [] {
        std::array<FieldTypeMeta, 256> a{};   // every slot registered = false
        a[static_cast<unsigned char>('X')] = FieldTypeMeta{
            8u,                                                   // fixed width
            static_cast<unsigned short>(FT_FMT_VFP | FT_FMT_X64), // eligible formats
            "Pronoun",                                            // STRUCT display
            true                                                  // registered
        };
        return a;
    }();
    return m;
}

}  // namespace

const Codec& codec_for(char type) noexcept {
    return table()[static_cast<unsigned char>(type)];
}

void register_codec(char type, Codec codec) {
    table()[static_cast<unsigned char>(type)] = codec;
}

void register_field_type(char type, Codec codec, FieldTypeMeta meta) {
    meta.registered = true;
    table()[static_cast<unsigned char>(type)]      = codec;
    meta_table()[static_cast<unsigned char>(type)] = meta;
}

bool field_type_registered(char type) noexcept {
    return meta_table()[static_cast<unsigned char>(type)].registered;
}
unsigned int field_type_fixed_width(char type) noexcept {
    return meta_table()[static_cast<unsigned char>(type)].fixed_width;
}
unsigned short field_type_formats(char type) noexcept {
    return meta_table()[static_cast<unsigned char>(type)].formats;
}
const char* field_type_display_name(char type) noexcept {
    return meta_table()[static_cast<unsigned char>(type)].display_name;
}

}  // namespace xbase::fieldcodec
