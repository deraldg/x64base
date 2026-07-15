#include "area_kind_util.hpp"
#include "xbase.hpp"

namespace xbase {

const char* area_kind_token(AreaKind k) noexcept
{
    switch (k) {
        case AreaKind::V32:  return "v32";
        case AreaKind::V64:  return "v64";
        case AreaKind::V128: return "v128";
        case AreaKind::Tup:  return "tup";
        case AreaKind::Unknown:
        default:             return "unknown";
    }
}

const char* area_kind_label(AreaKind k) noexcept
{
    switch (k) {
        case AreaKind::V32:  return "DBF v32";
        case AreaKind::V64:  return "DBF v64";
        case AreaKind::V128: return "DBF v128";
        case AreaKind::Tup:  return "Tuple";
        case AreaKind::Unknown:
        default:             return "Unknown";
    }
}

const char* dbf_version_token(std::uint8_t ver) noexcept
{
    switch (ver) {
        case 0x03: return "v32";
        case 0x83: return "v32+memo";
        case 0xF5: return "fox26+memo";

        case 0x30: return "vfp";
        case 0x31: return "vfp-autoinc";
        case 0x32: return "vfp-varchar";

        case 0x64: return "v64";

        default:   return "unknown";
    }
}

const char* dbf_version_label(std::uint8_t ver) noexcept
{
    switch (ver) {
        case 0x03: return "dBASE/classic DBF";
        case 0x83: return "dBASE/classic DBF with memo";
        case 0xF5: return "FoxPro 2.x DBF with memo";

        case 0x30: return "Visual FoxPro DBF";
        case 0x31: return "Visual FoxPro DBF with autoincrement";
        case 0x32: return "Visual FoxPro DBF with varchar/varbinary";

        case 0x64: return "x64base DBF";

        default:   return "Unknown DBF version";
    }
}

} // namespace xbase
