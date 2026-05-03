#include "memo/memo_ref.hpp"

#include <cctype>
#include <cstdint>
#include <iomanip>
#include <sstream>
#include <string>

namespace dottalk::memo {
namespace {

bool parse_dec_u64(const std::string& s, std::uint64_t& out) noexcept
{
    if (s.empty()) return false;
    std::uint64_t v = 0;
    for (char ch : s) {
        const unsigned char c = static_cast<unsigned char>(ch);
        if (!std::isdigit(c)) return false;
        const std::uint64_t digit = static_cast<std::uint64_t>(ch - '0');
        v = (v * 10u) + digit;
    }
    out = v;
    return true;
}

int hex_value(char ch) noexcept
{
    if (ch >= '0' && ch <= '9') return ch - '0';
    if (ch >= 'a' && ch <= 'f') return ch - 'a' + 10;
    if (ch >= 'A' && ch <= 'F') return ch - 'A' + 10;
    return -1;
}

bool parse_hex_u64(const std::string& s, std::uint64_t& out) noexcept
{
    if (s.empty() || s.size() > 16u) return false;
    std::uint64_t v = 0;
    for (char ch : s) {
        const int hv = hex_value(ch);
        if (hv < 0) return false;
        v = (v << 4u) | static_cast<std::uint64_t>(hv);
    }
    out = v;
    return true;
}

std::string upper_hex16(std::uint64_t v)
{
    std::ostringstream os;
    os << std::uppercase << std::hex << std::setw(16) << std::setfill('0') << v;
    return os.str();
}

bool parse_old_oo_form(const std::string& text, std::uint64_t& out_object_id) noexcept
{
    const std::string prefix = "memo:v";
    if (text.rfind(prefix, 0) != 0) return false;

    const std::size_t p1 = text.find(':', prefix.size());
    const std::size_t p2 = (p1 == std::string::npos) ? std::string::npos : text.find(':', p1 + 1);
    const std::size_t p3 = (p2 == std::string::npos) ? std::string::npos : text.find(':', p2 + 1);
    if (p1 == std::string::npos || p2 == std::string::npos || p3 == std::string::npos) return false;

    std::uint64_t obj = 0;
    if (!parse_dec_u64(text.substr(p2 + 1, p3 - p2 - 1), obj)) return false;
    out_object_id = obj;
    return true;
}

} // namespace

MemoRef make_x64_ref(std::uint64_t object_id)
{
    if (object_id == 0) return MemoRef{};
    return MemoRef{upper_hex16(object_id)};
}

std::string to_string(const MemoRef& ref)
{
    return ref.token;
}

bool parse_memo_ref(const std::string& text, MemoRef& out)
{
    out = MemoRef{};
    if (text.empty()) return true;

    std::uint64_t object_id = 0;

    // Older OO skeleton form: memo:v1:x64:<id>:<flags>
    if (parse_old_oo_form(text, object_id)) {
        out = make_x64_ref(object_id);
        return true;
    }

    // Existing x64/DTX canonical token: 16-char hex.
    if (text.size() == 16u && parse_hex_u64(text, object_id)) {
        out = MemoRef{text};
        return true;
    }

    // Transition convenience: bare decimal object id.
    if (parse_dec_u64(text, object_id)) {
        out = make_x64_ref(object_id);
        return true;
    }

    return false;
}

bool try_object_id_from_ref(const MemoRef& ref, std::uint64_t& out_object_id) noexcept
{
    out_object_id = 0;
    if (ref.token.empty()) return true;

    if (ref.token.size() == 16u && parse_hex_u64(ref.token, out_object_id)) {
        return true;
    }

    if (parse_dec_u64(ref.token, out_object_id)) {
        return true;
    }

    std::uint64_t old_id = 0;
    if (parse_old_oo_form(ref.token, old_id)) {
        out_object_id = old_id;
        return true;
    }

    return false;
}

} // namespace dottalk::memo
