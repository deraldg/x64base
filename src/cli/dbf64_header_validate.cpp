#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase_error_codes.hpp"
#include "xbase_error_context.hpp"

#include <cctype>
#include <cstdint>
#include <limits>

using namespace xbase::error;

namespace {

static bool fail_header()
{
    set_last_error(e_dbf_header_invalid());
    return false;
}

static char up_ascii(char c)
{
    return static_cast<char>(
        std::toupper(static_cast<unsigned char>(c))
    );
}

static bool is_known_field_type(char t)
{
    switch (up_ascii(t)) {
        case 'C':   // Character
        case 'N':   // Numeric
        case 'F':   // Float
        case 'D':   // Date
        case 'L':   // Logical
        case 'M':   // Memo
        case 'G':   // General
        case 'B':   // Double / binary double
        case 'I':   // Integer
        case 'Y':   // Currency
        case 'T':   // DateTime
        case 'V':   // Varchar / extended char
        case 'Q':   // Varbinary / extension
        case 'W':   // Blob / extension
            return true;

        default:
            return false;
    }
}

static bool valid_length_for_type(char t, std::uint32_t len, std::uint8_t dec)
{
    if (len == 0) {
        return false;
    }

    switch (up_ascii(t)) {
        case 'L':
            return len == 1;

        case 'D':
            return len == 8;

        case 'I':
            return len == 4;

        case 'Y':
        case 'T':
        case 'B':
            return len == 8;

        case 'N':
        case 'F':
            return dec < len;

        case 'M':
            // Preserve compatibility. Legacy memo refs are commonly 10 bytes;
            // x64 memo refs may differ. Do not over-restrict here.
            return true;

        case 'C':
        case 'G':
        case 'V':
        case 'Q':
        case 'W':
            return true;

        default:
            return false;
    }
}

} // namespace

bool dbf64_validate_header(const xbase::DbArea& h)
{
    error_guard guard;
    clear_last_error();

    // This function validates loaded runtime metadata.
    // Raw x64 header geometry belongs in xbase_64.hpp / x64_loader.
    if (!h.isOpen()) {
        return fail_header();
    }

    if (h.kind() != xbase::AreaKind::V64) {
        return fail_header();
    }

    if (h.versionByte() != xbase::DBF_VERSION_64) {
        return fail_header();
    }

    if (h.recLength() <= 1) {
        return fail_header();
    }

    const auto& fields = h.fields();

    if (fields.empty()) {
        return fail_header();
    }

    if (fields.size() > static_cast<std::size_t>(xbase::MAX_FIELDS)) {
        return fail_header();
    }

    if (h.fieldCount() != static_cast<int>(fields.size())) {
        return fail_header();
    }

    std::uint64_t computed_record_len = 1; // deletion flag byte

    for (const auto& f : fields) {
        if (f.name.empty()) {
            return fail_header();
        }

        if (!is_known_field_type(f.type)) {
            return fail_header();
        }

        if (!valid_length_for_type(f.type, f.length, f.decimals)) {
            return fail_header();
        }

        computed_record_len += static_cast<std::uint64_t>(f.length);

        if (computed_record_len >
            static_cast<std::uint64_t>(std::numeric_limits<int>::max())) {
            return fail_header();
        }
    }

    if (computed_record_len != static_cast<std::uint64_t>(h.recLength())) {
        return fail_header();
    }

    // Engine row-count ceiling is a build vector (AIF-044); default == int64_t::max(),
    // so this preserves the prior signed-64 acceptance limit exactly.
    if (h.recCount64() > dottalk::build::max_rows) {
        return fail_header();
    }

    set_last_error(ok());
    return true;
}