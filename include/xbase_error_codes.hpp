#pragma once
// xbase_error_codes.hpp
// Canonical cross-platform error codes for xBase_64.
// MS-conformal layout, HRESULT-style packing, stable ABI.

#include <cstdint>
#include <string>

namespace xbase {
namespace error {

// ------------------------------------------------------------
// 1. Severity
// ------------------------------------------------------------
enum class severity : uint8_t
{
    success = 0,
    warning = 1,
    error   = 2
};

// ------------------------------------------------------------
// 2. Facility (subsystem)
// ------------------------------------------------------------
enum class facility : uint16_t
{
    general   = 0x0001,
    dbf64     = 0x0002,
    fpt64     = 0x0003,
    security  = 0x0004,
    cli       = 0x0005,
    io        = 0x0006,
    runtime   = 0x0007
};

// ------------------------------------------------------------
// 3. Canonical Error Code (32-bit, HRESULT-like)
// ------------------------------------------------------------
// Layout (bit positions):
//  31      : sign bit (always 1 for xBase_64 codes)
//  30..29  : severity (2 bits)
//  28..16  : facility (13 bits)
//  15..0   : code (16 bits)
using code_type = std::uint32_t;

struct code
{
    code_type value;

    constexpr code() : value(0) {}
    constexpr explicit code(code_type v) : value(v) {}

    constexpr severity get_severity() const noexcept
    {
        return static_cast<severity>((value >> 29) & 0x3);
    }

    constexpr facility get_facility() const noexcept
    {
        return static_cast<facility>((value >> 16) & 0x1FFF);
    }

    constexpr std::uint16_t get_number() const noexcept
    {
        return static_cast<std::uint16_t>(value & 0xFFFF);
    }

    constexpr bool ok() const noexcept
    {
        return get_severity() == severity::success;
    }

    constexpr bool failed() const noexcept
    {
        return !ok();
    }
};

// ------------------------------------------------------------
// 4. Packing helpers
// ------------------------------------------------------------
constexpr code make_code(severity sev,
                         facility fac,
                         std::uint16_t num) noexcept
{
    code_type v = 0;
    v |= (1u << 31); // sign bit set for xBase_64 codes
    v |= (static_cast<code_type>(sev) & 0x3u) << 29;
    v |= (static_cast<code_type>(fac) & 0x1FFFu) << 16;
    v |= static_cast<code_type>(num);
    return code{v};
}

// ------------------------------------------------------------
// 5. Canonical error constants
// ------------------------------------------------------------

// General
constexpr code ok() noexcept
{
    return code{0};
}

constexpr code e_unknown() noexcept
{
    return make_code(severity::error, facility::general, 0x0001);
}

constexpr code e_invalid_argument() noexcept
{
    return make_code(severity::error, facility::general, 0x0002);
}

constexpr code e_not_implemented() noexcept
{
    return make_code(severity::error, facility::general, 0x0003);
}

// DBF_64
constexpr code e_dbf_header_invalid() noexcept
{
    return make_code(severity::error, facility::dbf64, 0x0001);
}

constexpr code e_dbf_record_out_of_range() noexcept
{
    return make_code(severity::error, facility::dbf64, 0x0002);
}

// FPT64
constexpr code e_fpt_block_invalid() noexcept
{
    return make_code(severity::error, facility::fpt64, 0x0001);
}

// Security
constexpr code e_security_policy_violation() noexcept
{
    return make_code(severity::error, facility::security, 0x0001);
}

constexpr code e_security_elevated_write_forbidden() noexcept
{
    return make_code(severity::error, facility::security, 0x0002);
}

// CLI
constexpr code e_cli_parse_error() noexcept
{
    return make_code(severity::error, facility::cli, 0x0001);
}

constexpr code e_no_table_open() noexcept
{
    return make_code(severity::error, facility::cli, 0x0002);
}

constexpr code e_invalid_record_number() noexcept
{
    return make_code(severity::error, facility::cli, 0x0003);
}

constexpr code e_invalid_current_record() noexcept
{
    return make_code(severity::error, facility::cli, 0x0004);
}

constexpr code e_missing_argument() noexcept
{
    return make_code(severity::error, facility::cli, 0x0005);
}

constexpr code e_unrecognized_command_form() noexcept
{
    return make_code(severity::error, facility::cli, 0x0006);
}

constexpr code e_area_qualifier_not_supported() noexcept
{
    return make_code(severity::error, facility::cli, 0x0007);
}

constexpr code e_order_unavailable() noexcept
{
    return make_code(severity::error, facility::cli, 0x0008);
}

constexpr code w_for_clause_ignored() noexcept
{
    return make_code(severity::warning, facility::cli, 0x0009);
}

constexpr code w_order_fallback_physical() noexcept
{
    return make_code(severity::warning, facility::cli, 0x000A);
}

// IO
constexpr code e_io_write_failed() noexcept
{
    return make_code(severity::error, facility::io, 0x0001);
}

// ------------------------------------------------------------
// 6. String helpers
// ------------------------------------------------------------
inline const char* to_severity_string(severity s)
{
    switch (s) {
        case severity::success: return "success";
        case severity::warning: return "warning";
        case severity::error:   return "error";
        default:                return "unknown";
    }
}

inline const char* to_facility_string(facility f)
{
    switch (f) {
        case facility::general:  return "general";
        case facility::dbf64:    return "dbf64";
        case facility::fpt64:    return "fpt64";
        case facility::security: return "security";
        case facility::cli:      return "cli";
        case facility::io:       return "io";
        case facility::runtime:  return "runtime";
        default:                 return "unknown";
    }
}

// ------------------------------------------------------------
// 7. Message mapping
// ------------------------------------------------------------
inline std::string to_string(code c)
{
    switch (c.value) {
        case 0:
            return "OK";

        case e_unknown().value:
            return "Unknown error";

        case e_invalid_argument().value:
            return "Invalid argument";

        case e_not_implemented().value:
            return "Not implemented";

        case e_dbf_header_invalid().value:
            return "DBF_64 header invalid";

        case e_dbf_record_out_of_range().value:
            return "DBF_64 record out of range";

        case e_fpt_block_invalid().value:
            return "FPT64 block invalid";

        case e_security_policy_violation().value:
            return "Security policy violation";

        case e_security_elevated_write_forbidden().value:
            return "Security: elevated write forbidden";

        case e_cli_parse_error().value:
            return "CLI parse error";

        case e_no_table_open().value:
            return "No table open.";

        case e_invalid_record_number().value:
            return "Invalid record number.";

        case e_invalid_current_record().value:
            return "Invalid current record.";

        case e_missing_argument().value:
            return "Missing required argument.";

        case e_unrecognized_command_form().value:
            return "Unrecognized command form.";

        case e_area_qualifier_not_supported().value:
            return "Area qualifier not supported yet.";

        case e_order_unavailable().value:
            return "Ordered backend unavailable.";

        case w_for_clause_ignored().value:
            return "FOR clause ignored.";

        case w_order_fallback_physical().value:
            return "Falling back to physical order.";

        case e_io_write_failed().value:
            return "I/O write failed.";

        default:
            return "Unrecognized xBase_64 error code";
    }
}

inline code_type to_hresult(code c) noexcept
{
    return c.value;
}

inline code from_hresult(code_type v) noexcept
{
    return code{v};
}

inline const char* symbol(code c) noexcept
{
    switch (c.value) {
        case ok().value:                                  return "OK";
        case e_unknown().value:                           return "E_UNKNOWN";
        case e_invalid_argument().value:                  return "E_INVALID_ARGUMENT";
        case e_not_implemented().value:                   return "E_NOT_IMPLEMENTED";
        case e_dbf_header_invalid().value:                return "E_DBF_HEADER_INVALID";
        case e_dbf_record_out_of_range().value:           return "E_DBF_RECORD_OUT_OF_RANGE";
        case e_fpt_block_invalid().value:                 return "E_FPT_BLOCK_INVALID";
        case e_security_policy_violation().value:         return "E_SECURITY_POLICY_VIOLATION";
        case e_security_elevated_write_forbidden().value: return "E_SECURITY_ELEVATED_WRITE_FORBIDDEN";
        case e_cli_parse_error().value:                   return "E_CLI_PARSE_ERROR";
        case e_no_table_open().value:                     return "E_NO_TABLE_OPEN";
        case e_invalid_record_number().value:             return "E_INVALID_RECORD_NUMBER";
        case e_invalid_current_record().value:            return "E_INVALID_CURRENT_RECORD";
        case e_missing_argument().value:                  return "E_MISSING_ARGUMENT";
        case e_unrecognized_command_form().value:         return "E_UNRECOGNIZED_COMMAND_FORM";
        case e_area_qualifier_not_supported().value:      return "E_AREA_QUALIFIER_NOT_SUPPORTED";
        case e_order_unavailable().value:                 return "E_ORDER_UNAVAILABLE";
        case w_for_clause_ignored().value:                return "W_FOR_CLAUSE_IGNORED";
        case w_order_fallback_physical().value:           return "W_ORDER_FALLBACK_PHYSICAL";
        case e_io_write_failed().value:                   return "E_IO_WRITE_FAILED";
        default:                                          return "E_UNRECOGNIZED";
    }
}

} // namespace error
} // namespace xbase
