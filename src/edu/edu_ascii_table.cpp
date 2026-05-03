#include "xbase.hpp"
#include "textio.hpp"

#include <algorithm>
#include <array>
#include <cctype>
#include <cstdint>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

// -----------------------------------------------------------------------------
// EDU ASCII TABLE
// Domain: edu_ (instructional/reference)
// Command surface: EDU ASCII TABLE [ASCII|EXT|CTRL|PRINT|RANGE a b|HELP]
// Signature matches house style.
// -----------------------------------------------------------------------------

namespace {

struct AsciiRow {
    int dec;
    int hex;
    int oct;
    std::string bin;
    std::string glyph;
    std::string name;
};

std::string upper_copy(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
        [](unsigned char c){ return static_cast<char>(std::toupper(c)); });
    return s;
}

std::string to_binary8(int v) {
    std::string out; out.reserve(8);
    for (int b = 7; b >= 0; --b)
        out.push_back((v & (1 << b)) ? '1' : '0');
    return out;
}

std::string control_name(int c) {
    static const std::array<const char*, 33> n = {
        "NUL","SOH","STX","ETX","EOT","ENQ","ACK","BEL",
        "BS","HT","LF","VT","FF","CR","SO","SI",
        "DLE","DC1","DC2","DC3","DC4","NAK","SYN","ETB",
        "CAN","EM","SUB","ESC","FS","GS","RS","US","DEL"
    };
    if (c >= 0 && c <= 31) return n[(size_t)c];
    if (c == 127) return n[32];
    return {};
}

std::string control_desc(int c) {
    switch (c) {
        case 0: return "Null"; case 1: return "Start of Heading"; case 2: return "Start of Text";
        case 3: return "End of Text"; case 4: return "End of Transmission"; case 5: return "Enquiry";
        case 6: return "Acknowledge"; case 7: return "Bell"; case 8: return "Backspace";
        case 9: return "Horizontal Tab"; case 10: return "Line Feed"; case 11: return "Vertical Tab";
        case 12: return "Form Feed"; case 13: return "Carriage Return"; case 14: return "Shift Out";
        case 15: return "Shift In"; case 16: return "Data Link Escape"; case 17: return "Device Control 1";
        case 18: return "Device Control 2"; case 19: return "Device Control 3"; case 20: return "Device Control 4";
        case 21: return "Negative Acknowledge"; case 22: return "Synchronous Idle"; case 23: return "End Transmission Block";
        case 24: return "Cancel"; case 25: return "End of Medium"; case 26: return "Substitute";
        case 27: return "Escape"; case 28: return "File Separator"; case 29: return "Group Separator";
        case 30: return "Record Separator"; case 31: return "Unit Separator"; case 127: return "Delete";
        default: return {};
    }
}

std::string cp437_name(int c) {
    // condensed labels for extended set
    switch (c) {
        case 176: return "Light shade"; case 177: return "Medium shade"; case 178: return "Dark shade";
        case 179: return "Box vertical"; case 196: return "Box horizontal"; case 197: return "Box crossing";
        case 219: return "Full block"; case 220: return "Lower half"; case 221: return "Left half";
        case 222: return "Right half"; case 223: return "Upper half"; case 248: return "Degree";
        case 241: return "Plus-minus"; case 246: return "Division"; case 251: return "Sqrt";
        default: return "Extended";
    }
}

std::string glyph(int c) {
    if (c >= 32 && c <= 126) {
        if (c == 32) return "SPC";
        return std::string(1, static_cast<char>(c));
    }
    if (c == 127) return "DEL";
    if (c <= 31) return control_name(c);
    return std::string(1, static_cast<char>(static_cast<unsigned char>(c)));
}

std::string name(int c) {
    if (c <= 31) return control_desc(c);
    if (c == 32) return "Space";
    if (c <= 126) return "Printable";
    if (c == 127) return "Delete";
    return cp437_name(c);
}

std::vector<AsciiRow> build() {
    std::vector<AsciiRow> r; r.reserve(256);
    for (int c = 0; c <= 255; ++c)
        r.push_back({c, c, c, to_binary8(c), glyph(c), name(c)});
    return r;
}

void sep() {
    std::cout << "+-----+-----+-----+----------+-------+------------------------------\n";
}

void header() {
    sep();
    std::cout << "| DEC | HEX | OCT | BINARY   | GLYPH | NAME                         |\n";
    sep();
}

void row(const AsciiRow& r) {
    std::ostringstream hx; hx << std::uppercase << std::hex << r.hex;
    std::ostringstream oc; oc << std::oct << r.oct;
    std::cout
        << "| " << std::setw(3) << std::right << r.dec
        << " | " << std::setw(3) << std::right << hx.str()
        << " | " << std::setw(3) << std::right << oc.str()
        << " | " << std::setw(8) << std::left  << r.bin
        << " | " << std::setw(5) << std::left  << r.glyph
        << " | " << std::setw(28) << std::left << r.name
        << " |\n";
}

void print_range(const std::vector<AsciiRow>& v, int a, int b) {
    int lo = std::max(0, a), hi = std::min(255, b);
    header();
    for (const auto& r : v) if (r.dec >= lo && r.dec <= hi) row(r);
    sep();
}

void print_ctrl(const std::vector<AsciiRow>& v) {
    header();
    for (const auto& r : v)
        if ((r.dec >= 0 && r.dec <= 31) || r.dec == 127) row(r);
    sep();
}

void usage() {
    std::cout
        << "Usage:\n"
        << "  EDU ASCII TABLE\n"
        << "  EDU ASCII TABLE ASCII\n"
        << "  EDU ASCII TABLE EXT\n"
        << "  EDU ASCII TABLE CTRL\n"
        << "  EDU ASCII TABLE PRINT\n"
        << "  EDU ASCII TABLE RANGE a b\n";
}

bool to_int(const std::string& s, int& out) {
    try { size_t p=0; int v = std::stoi(s, &p, 10); if (p!=s.size()) return false; out=v; return true; }
    catch (...) { return false; }
}

} // anon

// -----------------------------------------------------------------------------
// Command entry (house style)
// -----------------------------------------------------------------------------

void edu_ASCII_TABLE(xbase::DbArea&, std::istringstream& iss)
{
    auto toks = textio::tokenize(iss);

    const std::string a1 = toks.size() > 0 ? textio::upper(toks[0]) : "";
    const std::string a2 = toks.size() > 1 ? toks[1] : "";
    const std::string a3 = toks.size() > 2 ? toks[2] : "";

    const auto rows = build();

    if (a1.empty()) {
        print_range(rows, 0, 255);
        return;
    }

    if (a1 == "HELP" || a1 == "/?") {
        usage();
        return;
    }

    if (a1 == "ASCII") {
        print_range(rows, 0, 127);
        return;
    }

    if (a1 == "EXT" || a1 == "EXTENDED" || a1 == "OEM") {
        print_range(rows, 128, 255);
        return;
    }

    if (a1 == "PRINT" || a1 == "PRINTABLE") {
        print_range(rows, 32, 126);
        return;
    }

    if (a1 == "CTRL" || a1 == "CONTROL") {
        print_ctrl(rows);
        return;
    }

    if (a1 == "RANGE") {
        int lo=0, hi=0;
        if (!to_int(a2, lo) || !to_int(a3, hi)) {
            std::cout << "RANGE requires two decimal values.\n";
            usage();
            return;
        }
        if (lo > hi) std::swap(lo, hi);
        print_range(rows, lo, hi);
        return;
    }

    std::cout << "Unknown option: " << a1 << "\n";
    usage();
}

// -----------------------------------------------------------------------------
// Registration (example)
// -----------------------------------------------------------------------------
// Wire this in your registrar alongside other edu_ modules.
//
// registry.add({"EDU ASCII TABLE", "Extended ASCII reference", edu_ASCII_TABLE});
