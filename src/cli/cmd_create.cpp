// @dottalk.usage v1
// owner: DOT|CREATE
// command: CREATE
// category: schema
// status: supported
// noargs: usage
// effect: create
// mutates: filesystem session schema
// usage-access: CREATE USAGE
// summary:
//   Create a DBF table in the configured DBF path slot using the requested
//   xBase/DBF flavor and field specification.
//
// usage:
//   CREATE USAGE
//   CREATE <name> (<field> <type>[, ...])
//   CREATE MSDOS <name> (<field> <type>[, ...])
//   CREATE DBASE <name> (<field> <type>[, ...])
//   CREATE FOX26 <name> (<field> <type>[, ...])
//   CREATE FOXPRO <name> (<field> <type>[, ...])
//   CREATE VFP <name> (<field> <type>[, ...])
//   CREATE X64 <name> (<field> <type>[, ...])
//
// examples:
//   CREATE students (sid N(6), lname C(20), fname C(15))
//   CREATE X64 teachers (teacher_id I, full_name C(80), bio M)
//   CREATE VFP ledger (acct C(12), amount Y, posted D)
//
// notes:
//   CREATE with no usable table/field specification shows usage and does not create a file.
//   Relative table names resolve through the configured DBF path slot.
//   CREATE clears active order state and closes the current area before writing the new table.
//   After a successful write, CREATE opens the created table in the current area.
//   If any field is M, CREATE attempts automatic memo attach after opening the table.
//   X64 CREATE applies descriptor fallback/name policy for DBF descriptor safety.
//   Long, duplicate, or descriptor-unsafe X64 field names may receive fallback tokens.
//   X64 logical/authoritative metadata names are preserved when they fit the current x64 metadata limits.
//   CREATE is a filesystem/schema mutation command; do not classify it as a read-only report command.
//
// risk:
//   creates_files: yes
//   opens_area: yes
//   closes_current_area: yes
//   clears_order_state: yes
//   writes_dbf: yes
//   writes_memo: when M fields are present
//   possible_overwrite: depends on dbf_create backend behavior for existing paths
//
// related:
//   USE
//   STRUCT
//   FIELDS
//   WORKSPACE
//   SETPATH
//

#include "xbase.hpp"
#include "xbase_64.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/field_codec.hpp"
#include "xbase/field_name_policy.hpp"
#include "cli/command_output.hpp"
#include "datatype_index.hpp"
#include "memo/memo_auto.hpp"

// Optional path slot support (SETPATH). If present, resolve relative DBF paths against Slot::DBF.
#if __has_include("cli/cmd_setpath.hpp")
  #include "cli/cmd_setpath.hpp"
  #define HAVE_SETPATH 1
#else
  #define HAVE_SETPATH 0
#endif

#include "cli/order_state.hpp"

#include <algorithm>
#include <cctype>
#include <cstdint>
#include <filesystem>
#include <sstream>
#include <string>
#include <utility>
#include <vector>

namespace {

namespace dt = dottalk::types;
using Flavor = xbase::dbf_create::Flavor;
using FieldSpec = xbase::dbf_create::FieldSpec;

static inline std::string s8(const std::filesystem::path& p)
{
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static inline std::filesystem::path dbf_slot_root_fallback()
{
#if HAVE_SETPATH
    try { return dottalk::paths::get_slot(dottalk::paths::Slot::DBF); } catch (...) {}
#endif
    return std::filesystem::current_path();
}

static inline std::filesystem::path resolve_dbf_slot_path(std::filesystem::path p)
{
    if (p.empty()) return p;
    if (p.is_absolute()) return p;
    return dbf_slot_root_fallback() / p;
}

static std::string trim(std::string s)
{
    auto sp = [](unsigned char c) {
        return c == ' ' || c == '\t' || c == '\r' || c == '\n';
    };
    while (!s.empty() && sp((unsigned char)s.front())) s.erase(s.begin());
    while (!s.empty() && sp((unsigned char)s.back()))  s.pop_back();
    return s;
}

static std::string up_copy(std::string s)
{
    std::transform(
        s.begin(), s.end(), s.begin(),
        [](unsigned char c) { return static_cast<char>(std::toupper(c)); });
    return s;
}

static dt::EngineFormat engine_format_for(Flavor flavor) noexcept
{
    switch (flavor)
    {
    case Flavor::MSDOS: return dt::EngineFormat::MSDOS_DBASE;
    case Flavor::FOX26: return dt::EngineFormat::FOX26;
    case Flavor::VFP:   return dt::EngineFormat::VFP;
    case Flavor::X64:   return dt::EngineFormat::VFP; // compatibility-first
    }
    return dt::EngineFormat::Unknown;
}

static bool parse_u16_param(const std::string& raw,
                            const std::string& label,
                            std::uint16_t min_value,
                            std::uint16_t max_value,
                            std::uint16_t& out,
                            std::string& err)
{
    const std::string text = trim(raw);
    if (text.empty()) {
        err = "CREATE: missing " + label + ".";
        return false;
    }

    std::size_t pos = 0;
    long value = 0;
    try {
        value = std::stol(text, &pos, 10);
    }
    catch (const std::exception&) {
        err = "CREATE: invalid " + label + " '" + text + "'.";
        return false;
    }

    if (pos != text.size()) {
        err = "CREATE: invalid " + label + " '" + text + "'.";
        return false;
    }
    if (value < static_cast<long>(min_value) || value > static_cast<long>(max_value)) {
        err = "CREATE: " + label + " must be between " +
              std::to_string(min_value) + " and " + std::to_string(max_value) + ".";
        return false;
    }

    out = static_cast<std::uint16_t>(value);
    return true;
}

static bool parse_u8_param(const std::string& raw,
                           const std::string& label,
                           std::uint8_t& out,
                           std::string& err)
{
    std::uint16_t value = 0;
    if (!parse_u16_param(raw, label, 0, 255, value, err)) {
        return false;
    }
    out = static_cast<std::uint8_t>(value);
    return true;
}

static bool parse_field_len_param(const std::string& raw,
                                  const std::string& label,
                                  Flavor flavor,
                                  char type,
                                  decltype(FieldSpec{}.len)& out,
                                  std::string& err)
{
    const std::uint16_t max_len =
        (flavor == Flavor::X64 && static_cast<char>(std::toupper(static_cast<unsigned char>(type))) == 'C')
            ? 4096
            : 255;

    std::uint16_t value = 0;
    if (!parse_u16_param(raw, label, 1, max_len, value, err)) {
        return false;
    }

    out = static_cast<decltype(FieldSpec{}.len)>(value);
    return true;
}

static std::vector<std::string> split_top(const std::string& inside)
{
    std::vector<std::string> out;
    int depth = 0;
    size_t start = 0;

    for (size_t i = 0; i < inside.size(); ++i) {
        const char c = inside[i];
        if (c == '(') ++depth;
        else if (c == ')' && depth > 0) --depth;
        else if ((c == ',' || c == ';') && depth == 0) {
            out.emplace_back(trim(inside.substr(start, i - start)));
            start = i + 1;
        }
    }

    if (start < inside.size()) out.emplace_back(trim(inside.substr(start)));
    return out;
}

static bool parse_one(const std::string& part,
                      FieldSpec& fs,
                      dt::EngineFormat fmt,
                      Flavor flavor,
                      std::string& err)
{
    std::istringstream ps(part);
    std::string fname, typeAndParams;
    if (!(ps >> fname >> typeAndParams)) {
        err = "Invalid field clause: '" + part + "'";
        return false;
    }
    if (fname.empty() || typeAndParams.empty()) {
        err = "Invalid field clause: '" + part + "'";
        return false;
    }

    fs.name = fname;
    const char T = (char)std::toupper((unsigned char)typeAndParams[0]);

    const dt::ValidationResult vr = dt::validate_type_for_format(T, fmt);
    if (!vr.ok) {
        // Not a static-catalog type.  Accept iff a runtime-registered custom
        // field type exists for this code AND it is eligible for this CREATE
        // flavor (FIELDTYPE M4b: the registry IS the validated chain — no
        // per-type switch edit needed here or in the catalog / supports_type_now).
        if (!xbase::fieldcodec::field_type_registered(T)) {
            err = "CREATE: field type '" + std::string(1, T) +
                  "' is not supported for this format.";
            return false;
        }
        unsigned short want = 0;
        switch (flavor) {
            case Flavor::MSDOS: want = xbase::fieldcodec::FT_FMT_MSDOS; break;
            case Flavor::FOX26: want = xbase::fieldcodec::FT_FMT_FOX26; break;
            case Flavor::VFP:   want = xbase::fieldcodec::FT_FMT_VFP;   break;
            case Flavor::X64:   want = xbase::fieldcodec::FT_FMT_X64;   break;
            default:            want = 0;                                break;
        }
        if ((xbase::fieldcodec::field_type_formats(T) & want) == 0) {
            err = "CREATE: field type '" + std::string(1, T) +
                  "' is not supported for this format.";
            return false;
        }
        // registered + eligible: accept (the static supports_type_now gate below
        // is only for catalog types).
    }
    else if (!xbase::dbf_create::supports_type_now(T, flavor)) {
        err = "CREATE: field type '" + std::string(1, T) +
              "' is not implemented for this CREATE flavor.";
        return false;
    }

    std::string params;
    const auto lp = typeAndParams.find('(');
    if (lp != std::string::npos) {
        const auto rp = typeAndParams.find_last_of(')');
        if (rp == std::string::npos || rp < lp) {
            err = "Malformed type parameter list in '" + part + "'";
            return false;
        }
        params = typeAndParams.substr(lp + 1, rp - lp - 1);
    }

    fs.type = T;
    fs.dec  = 0;
    fs.len  = 0;

    try
    {
        if (T == 'C') {
            if (params.empty()) {
                err = "CREATE: C type requires a length, e.g. C(20).";
                return false;
            }
            if (!parse_field_len_param(params, "C type length", flavor, T, fs.len, err)) {
                return false;
            }
            if (fs.len == 0) {
                err = "CREATE: C type length must be greater than zero.";
                return false;
            }
        }
        else if (T == 'N' || T == 'F') {
            if (params.empty()) {
                err = "CREATE: numeric/float type requires length, e.g. N(10,2).";
                return false;
            }
            const auto comma = params.find(',');
            if (comma == std::string::npos) {
                if (!parse_field_len_param(params, "numeric/float length", flavor, T, fs.len, err)) {
                    return false;
                }
                fs.dec = 0;
            } else {
                if (!parse_field_len_param(params.substr(0, comma), "numeric/float length", flavor, T, fs.len, err)) {
                    return false;
                }
                if (!parse_u8_param(params.substr(comma + 1), "numeric/float decimal count", fs.dec, err)) {
                    return false;
                }
            }
            if (fs.len == 0) {
                err = "CREATE: numeric/float length must be greater than zero.";
                return false;
            }
            if (fs.dec > fs.len) {
                err = "CREATE: decimal count cannot exceed field length.";
                return false;
            }
        }
        else if (T == 'D') {
            fs.len = 8;
            fs.dec = 0;
        }
        else if (T == 'L') {
            fs.len = 1;
            fs.dec = 0;
        }
        else if (T == 'M') {
            if (flavor == Flavor::X64) {
                fs.len = 8;
            } else {
                fs.len = 10;
            }
            fs.dec = 0;
        }
        else if (T == 'I') {
            fs.len = 4;
            fs.dec = 0;
        }
        else if (T == 'B') {
            fs.len = 8;
            fs.dec = 0;
        }
        else if (T == 'Y') {
            fs.len = 8;
            fs.dec = 4;
        }
        else if (T == 'T') {
            fs.len = 8;
            fs.dec = 0;
        }
        else if (xbase::fieldcodec::field_type_registered(T)) {
            // Registered custom field type (FIELDTYPE M4b): width comes from the
            // registry, not a hand-maintained switch.  0 => the type takes a
            // CREATE length param (none of the current custom types do).
            fs.len = static_cast<std::uint16_t>(xbase::fieldcodec::field_type_fixed_width(T));
            fs.dec = 0;
        }
        else {
            err = "CREATE: unsupported field type parser path for '" + std::string(1, T) + "'";
            return false;
        }
    }
    catch (const std::exception&)
    {
        err = "CREATE: invalid type parameter list in '" + part + "'";
        return false;
    }

    return true;
}


static void apply_x64_descriptor_name_policy(std::vector<FieldSpec>& fields)
{
    std::vector<std::string> names;
    names.reserve(fields.size());
    for (const auto& f : fields) names.push_back(f.name);

    const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(names);

    for (std::size_t i = 0; i < fields.size(); ++i) {
        fields[i].descriptor_name = plans[i].descriptor_name;

        const bool metadata_fits = xbase::x64_field_name_fits(plans[i].logical_name.size());

        std::string suffix;
        if (plans[i].mangled) {
            suffix += "; token was mangled to avoid a fallback collision";
        }
        if (plans[i].sanitized) {
            suffix += "; token was normalized for DBF descriptor safety";
        }

        if (!metadata_fits) {
            cli::cmdout::print_prefixed_message(
                "CREATE X64 WARNING",
                dottalk::helpdata::MessageId::CreateX64NameTooLongWarningText,
                {{"name", plans[i].logical_name},
                 {"limit", std::to_string(xbase::X64_FIELD_NAME_LENGTH_MAX)},
                 {"token", plans[i].descriptor_name},
                 {"suffix", suffix}});
            continue;
        }

        if (plans[i].truncated || plans[i].mangled || plans[i].sanitized) {
            cli::cmdout::print_prefixed_message(
                "CREATE X64 WARNING",
                dottalk::helpdata::MessageId::CreateX64FallbackTokenWarningText,
                {{"name", plans[i].logical_name},
                 {"token", plans[i].descriptor_name},
                 {"suffix", suffix}});
        }
    }
}


static bool is_create_usage_request(const std::string& raw)
{
    std::string t = up_copy(trim(raw));

    // Some dispatch paths pass only the command tail ("USAGE"), while the
    // current CREATE path has historically exposed the full raw line
    // ("CREATE USAGE") to cmd_CREATE.  Accept both so CREATE USAGE is a
    // true usage request and does not fall through to parse/create logic.
    if (t.rfind("CREATE ", 0) == 0) {
        t = trim(t.substr(7));
    }

    return t == "USAGE" || t == "HELP" || t == "?";
}

static void print_create_usage()
{
    cli::cmdout::print_message(dottalk::helpdata::MessageId::CreateUsageText);
}


static bool parse_field_list(std::istringstream& args,
                             std::vector<FieldSpec>& out,
                             std::string& tableName,
                             Flavor& flavor,
                             std::string& err)
{
    flavor = Flavor::MSDOS;

    std::string first;
    if (!(args >> first)) {
        err = "CREATE: missing table name.";
        return false;
    }

    const std::string firstUp = up_copy(first);

    if (firstUp == "MSDOS" || firstUp == "DBASE") {
        flavor = Flavor::MSDOS;
        if (!(args >> tableName)) {
            err = "CREATE: missing table name after MSDOS/DBASE.";
            return false;
        }
    }
    else if (firstUp == "FOX26" || firstUp == "FOXPRO26" || firstUp == "FOXPRO") {
        flavor = Flavor::FOX26;
        if (!(args >> tableName)) {
            err = "CREATE: missing table name after FOX26/FOXPRO.";
            return false;
        }
    }
    else if (firstUp == "VFP") {
        flavor = Flavor::VFP;
        if (!(args >> tableName)) {
            err = "CREATE: missing table name after VFP.";
            return false;
        }
    }
    else if (firstUp == "X64") {
        flavor = Flavor::X64;
        if (!(args >> tableName)) {
            err = "CREATE: missing table name after X64.";
            return false;
        }
    }
    else {
        tableName = first;
    }

    char ch;
    if (!(args >> ch) || ch != '(') {
        err = "CREATE: expected '(' after table name.";
        return false;
    }

    std::string inside;
    int depth = 1;
    char c;

    while (args.get(c))
    {
        if (c == '(') ++depth;
        else if (c == ')')
        {
            if (--depth == 0) break;
        }
        inside.push_back(c);
    }
    if (depth != 0) {
        err = "CREATE: unmatched parentheses in field list.";
        return false;
    }

    auto parts = split_top(inside);
    out.clear();

    const dt::EngineFormat fmt = engine_format_for(flavor);

    for (const auto& p : parts)
    {
        if (p.empty()) continue;
        FieldSpec fs;
        if (!parse_one(p, fs, fmt, flavor, err)) return false;
        out.push_back(fs);
    }

    if (out.empty()) {
        err = "CREATE: no fields specified.";
        return false;
    }

    return true;
}

} // namespace

void cmd_CREATE(xbase::DbArea& area, std::istringstream& args)
{
    const std::string raw_args = args.str();

    if (is_create_usage_request(raw_args)) {
        print_create_usage();
        return;
    }

    std::vector<FieldSpec> fields;
    std::string table;
    Flavor flavor = Flavor::MSDOS;
    std::string err;

    if (!parse_field_list(args, fields, table, flavor, err))
    {
        if (!err.empty()) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CreateDetailText, {{"detail", err}});
        }
        print_create_usage();
        return;
    }

    if (flavor == Flavor::X64) {
        apply_x64_descriptor_name_policy(fields);
    }

    {
        std::uint64_t rec_width = 1; // delete flag
        for (const auto& f : fields) rec_width += f.len;
        if (rec_width > xbase::X64_RECORD_SIZE_ADVISORY) {
            cli::cmdout::print_note(
                "CREATE",
                "fixed record width " + std::to_string(rec_width) + " bytes exceeds " +
                std::to_string(xbase::X64_RECORD_SIZE_ADVISORY) +
                " bytes; consider memo (M) fields for large or variable data");
        }
    }

    if (area.isOpen())
    {
        orderstate::clearOrder(area);
        area.close();
    }

    const std::filesystem::path outp =
        resolve_dbf_slot_path(std::filesystem::path(xbase::dbNameWithExt(table)));
    const std::string path = s8(outp);

    if (!xbase::dbf_create::create_dbf(path, fields, flavor, err))
    {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CreateFailedText, {{"detail", err}});
        return;
    }

    try
    {
        area.open(path);
    }
    catch (const std::exception& ex)
    {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CreateReopenFailedDetailText,
            {{"detail", ex.what()}});
        return;
    }
    catch (...)
    {
        cli::cmdout::print_message(
            dottalk::helpdata::MessageId::CreateReopenFailedText);
        return;
    }

    const bool hasMemo = std::any_of(
        fields.begin(), fields.end(),
        [](const FieldSpec& f) { return f.type == 'M' || f.type == 'm'; });

    if (hasMemo) {
        const std::string openedPath = area.filename().empty() ? path : area.filename();
        std::string memo_err;
        if (!cli_memo::memo_auto_on_use(area, openedPath, true, memo_err)) {
            cli::cmdout::print_message(
                dottalk::helpdata::MessageId::CreateMemoAttachFailedText,
                {{"detail", memo_err}});
        }
    }

    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CreatedText,
        {{"path", path},
         {"flavor", xbase::dbf_create::flavor_name(flavor)},
         {"memo", hasMemo ? " (+ memo)" : ""}});
    cli::cmdout::print_message(
        dottalk::helpdata::MessageId::CreateOpenedText,
        {{"file", area.filename()}, {"count", std::to_string(area.recCount())}});
}