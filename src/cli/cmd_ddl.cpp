// @dottalk.file v1
// subsystem: cli
// layer: command
// owns: 
// project: project.x64base.runtime
// lane: 
// owner: member.derald
// status: supported

// @dottalk.usage v1
// owner: DOT|DDL
// command: DDL
// category: schema
// status: supported
// noargs: usage
// effect: mixed
// mutates: filesystem schema dbf sidecar
// usage-access: DDL USAGE
// summary:
//   Fetch schema files, validate schema files, and create DBF tables from
//   JSON schema definitions with optional seed rows and sidecar metadata.
//
// usage:
//   DDL USAGE
//   DDL FETCH <url> TO <file>
//   DDL FETCH <url> TO <file> OVERWRITE
//   DDL VALIDATE <schema.json> USING <validator.json>
//   DDL CREATE DBF <out.dbf> FROM <schema.json>
//   DDL CREATE DBF <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> <out.dbf> FROM <schema.json>
//   DDL CREATE DBF <out.dbf> FROM <schema.json> OVERWRITE
//   DDL CREATE DBF <out.dbf> FROM <schema.json> SEED CSV <path.csv>
//   DDL CREATE DBF <out.dbf> FROM <schema.json> SEED BLANK <n>
//   DDL CREATE DBF <out.dbf> FROM <schema.json> REJECTS <rejects.csv>
//   DDL CREATE DBF <out.dbf> FROM <schema.json> EMIT SIDECARS
//
// notes:
//   DDL with no arguments shows usage.
//   FETCH writes a schema-side file and refuses overwrite unless OVERWRITE is supplied.
//   VALIDATE parses both inputs and enforces the in-tree schema_json_v1 contract subset.
//   CREATE DBF writes a DBF file from schema field definitions.
//   CREATE DBF defaults to the legacy MSDOS/DBASE flavor unless a flavor token is supplied.
//   CREATE DBF refuses existing output unless OVERWRITE is supplied.
//   Relative schema inputs resolve under SCHEMAS.
//   Relative FETCH outputs resolve under SCHEMAS.
//   Relative CREATE DBF outputs resolve under TMP.
//   EMIT SIDECARS writes companion schema, load, and index metadata files.
//   SEED CSV is recognized but not yet implemented in this drop-in.
//
// risk:
//   reads_files: yes
//   writes_files: yes
//   writes_dbf: DDL CREATE DBF
//   writes_sidecars: when EMIT SIDECARS is supplied
//   overwrites_files: only when OVERWRITE is supplied
//   network_fetch: DDL FETCH
//   mutates_table_data: no open table mutation
//
// related:
//   CREATE
//   WORKSPACE
//   USE
//   STRUCT
//   FIELDMGR
//

#include "cmd_ddl.hpp"

#include <algorithm>
#include <cctype>
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <set>
#include <sstream>
#include <string>
#include <vector>

#include <nlohmann/json.hpp>
#include "xbase.hpp"
#include "xbase/dbf_create.hpp"
#include "xbase/field_name_policy.hpp"

#if __has_include("cli/path_resolver.hpp") && __has_include("cli/cmd_setpath.hpp")
  #include "cli/path_resolver.hpp"
  #include "cli/cmd_setpath.hpp"
  #define HAVE_PATHS 1
#else
  #define HAVE_PATHS 0
#endif

#ifdef _WIN32
#include <windows.h>
#include <winhttp.h>
#pragma comment(lib, "winhttp.lib")
#endif

namespace fs = std::filesystem;
using nlohmann::json;
using DbfFlavor = xbase::dbf_create::Flavor;

// ---------- small helpers ---------------------------------------------------

static inline std::string up(std::string s) {
    for (auto& c : s) c = (char)std::toupper((unsigned char)c);
    return s;
}

static inline std::string trim_copy(std::string s) {
    auto is_space = [](unsigned char ch){ return std::isspace(ch) != 0; };
    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [&](unsigned char c){ return !is_space(c); }));
    s.erase(std::find_if(s.rbegin(), s.rend(),
        [&](unsigned char c){ return !is_space(c); }).base(), s.end());
    return s;
}

static bool is_digits(const std::string& s) {
    if (s.empty()) return false;
    for (unsigned char ch : s) if (!std::isdigit(ch)) return false;
    return true;
}

static std::string read_word(std::istringstream& iss) {
    std::string w;
    iss >> w;
    return w;
}

static std::string read_pathish(std::istringstream& iss) {
    iss >> std::ws;
    if (iss.peek() == '"' || iss.peek() == '\'') {
        const char q = (char)iss.get();
        std::string out;
        char c = '\0';
        while (iss.get(c)) {
            if (c == q) break;
            out.push_back(c);
        }
        return out;
    }
    std::string w;
    iss >> w;
    return w;
}

static std::string s8(const fs::path& p) {
#if defined(_WIN32)
    auto u = p.u8string();
    return std::string(u.begin(), u.end());
#else
    return p.string();
#endif
}

static fs::path weak_can(const fs::path& p) {
    std::error_code ec;
    fs::path r = fs::weakly_canonical(p, ec);
    return ec ? p : r;
}

static bool file_exists(const fs::path& p) {
    std::error_code ec;
    return fs::exists(p, ec) && !ec && fs::is_regular_file(p, ec) && !ec;
}

static bool ensure_parent_dir(const fs::path& p) {
    std::error_code ec;
    if (!p.parent_path().empty()) fs::create_directories(p.parent_path(), ec);
    return !ec;
}

#if HAVE_PATHS
namespace paths = dottalk::paths;

static inline fs::path schemas_root() { return paths::get_slot(paths::Slot::SCHEMAS); }
static inline fs::path tmp_root()     { return paths::get_slot(paths::Slot::TMP); }
static inline fs::path dbf_root()     { return paths::get_slot(paths::Slot::DBF); }
#else
static inline fs::path schemas_root() { return fs::current_path(); }
static inline fs::path tmp_root()     { return fs::current_path(); }
static inline fs::path dbf_root()     { return fs::current_path(); }
#endif

// Resolve relative input files under SCHEMAS first, then current working directory.
static fs::path resolve_ddl_input(const std::string& raw) {
    fs::path p(raw);
    if (p.is_absolute()) return weak_can(p);

    const fs::path c1 = weak_can(schemas_root() / p);
    if (file_exists(c1)) return c1;

    const fs::path c2 = weak_can(fs::current_path() / p);
    if (file_exists(c2)) return c2;

    return c1;
}

// Relative FETCH output should land under SCHEMAS.
static fs::path resolve_ddl_fetch_output(const std::string& raw) {
    fs::path p(raw);
    if (p.is_absolute()) return weak_can(p);
    return weak_can(schemas_root() / p);
}

// Relative DBF output should land under TMP by default.
static fs::path resolve_ddl_dbf_output(const std::string& raw) {
    fs::path p(raw);
    if (p.is_absolute()) return weak_can(p);
    return weak_can(tmp_root() / p);
}

// Relative CSV inputs for seeding should try TMP, then SCHEMAS, then CWD.
static fs::path resolve_seed_csv_input(const std::string& raw) {
    fs::path p(raw);
    if (p.is_absolute()) return weak_can(p);

    const fs::path t = weak_can(tmp_root() / p);
    if (file_exists(t)) return t;

    const fs::path s = weak_can(schemas_root() / p);
    if (file_exists(s)) return s;

    const fs::path c = weak_can(fs::current_path() / p);
    if (file_exists(c)) return c;

    return t;
}

// Relative rejects files should land under TMP.
static fs::path resolve_rejects_output(const std::string& raw) {
    fs::path p(raw);
    if (p.is_absolute()) return weak_can(p);
    return weak_can(tmp_root() / p);
}

static std::string now_utc_iso() {
    using clock = std::chrono::system_clock;
    const auto t = clock::now();
    std::time_t tt = clock::to_time_t(t);
    std::tm tm{};
#if defined(_WIN32)
    gmtime_s(&tm, &tt);
#else
    gmtime_r(&tt, &tm);
#endif
    std::ostringstream os;
    os << std::put_time(&tm, "%Y-%m-%dT%H:%M:%SZ");
    return os.str();
}

static bool write_text_file(const fs::path& path, const std::string& contents) {
    if (!ensure_parent_dir(path)) return false;
    std::ofstream f(path, std::ios::binary | std::ios::trunc);
    if (!f) return false;
    f << contents;
    return (bool)f;
}

static bool copy_file_safe(const fs::path& src, const fs::path& dst) {
    std::error_code ec;
    if (!dst.parent_path().empty()) fs::create_directories(dst.parent_path(), ec);
    fs::copy_file(src, dst, fs::copy_options::overwrite_existing, ec);
    return !ec;
}

// ---------- URL fetch helpers -----------------------------------------------

#ifdef _WIN32

struct ParsedUrl {
    std::wstring host;
    std::wstring path;
    INTERNET_PORT port = 0;
    bool secure = false;
};

static bool parse_url(const std::string& url, ParsedUrl& out) {
    std::wstring wurl(url.begin(), url.end());

    URL_COMPONENTS uc{};
    wchar_t host[256]{};
    wchar_t path[2048]{};

    uc.dwStructSize = sizeof(uc);
    uc.lpszHostName = host;
    uc.dwHostNameLength = (DWORD)std::size(host);
    uc.lpszUrlPath = path;
    uc.dwUrlPathLength = (DWORD)std::size(path);

    if (!WinHttpCrackUrl(wurl.c_str(), 0, 0, &uc)) return false;

    out.host.assign(uc.lpszHostName, uc.dwHostNameLength);
    out.path.assign(uc.lpszUrlPath, uc.dwUrlPathLength);
    if (out.path.empty()) out.path = L"/";
    out.port = uc.nPort;
    out.secure = (uc.nScheme == INTERNET_SCHEME_HTTPS);
    return true;
}

static bool http_get_bytes(const std::string& url, std::vector<char>& outBytes, std::string& err) {
    ParsedUrl pu;
    if (!parse_url(url, pu)) {
        err = "invalid URL";
        return false;
    }

    HINTERNET session = WinHttpOpen(
        L"DotTalk++ DDL",
        WINHTTP_ACCESS_TYPE_DEFAULT_PROXY,
        WINHTTP_NO_PROXY_NAME,
        WINHTTP_NO_PROXY_BYPASS,
        0);

    if (!session) {
        err = "WinHttpOpen failed";
        return false;
    }

    HINTERNET connect = WinHttpConnect(session, pu.host.c_str(), pu.port, 0);
    if (!connect) {
        err = "WinHttpConnect failed";
        WinHttpCloseHandle(session);
        return false;
    }

    HINTERNET request = WinHttpOpenRequest(
        connect,
        L"GET",
        pu.path.c_str(),
        nullptr,
        WINHTTP_NO_REFERER,
        WINHTTP_DEFAULT_ACCEPT_TYPES,
        pu.secure ? WINHTTP_FLAG_SECURE : 0);

    if (!request) {
        err = "WinHttpOpenRequest failed";
        WinHttpCloseHandle(connect);
        WinHttpCloseHandle(session);
        return false;
    }

    BOOL ok = WinHttpSendRequest(
        request,
        WINHTTP_NO_ADDITIONAL_HEADERS,
        0,
        WINHTTP_NO_REQUEST_DATA,
        0,
        0,
        0);

    if (!ok) {
        err = "WinHttpSendRequest failed";
        WinHttpCloseHandle(request);
        WinHttpCloseHandle(connect);
        WinHttpCloseHandle(session);
        return false;
    }

    ok = WinHttpReceiveResponse(request, nullptr);
    if (!ok) {
        err = "WinHttpReceiveResponse failed";
        WinHttpCloseHandle(request);
        WinHttpCloseHandle(connect);
        WinHttpCloseHandle(session);
        return false;
    }

    DWORD statusCode = 0;
    DWORD statusSize = sizeof(statusCode);
    if (WinHttpQueryHeaders(
            request,
            WINHTTP_QUERY_STATUS_CODE | WINHTTP_QUERY_FLAG_NUMBER,
            WINHTTP_HEADER_NAME_BY_INDEX,
            &statusCode,
            &statusSize,
            WINHTTP_NO_HEADER_INDEX)) {
        if (statusCode >= 400) {
            err = "HTTP error " + std::to_string(statusCode);
            WinHttpCloseHandle(request);
            WinHttpCloseHandle(connect);
            WinHttpCloseHandle(session);
            return false;
        }
    }

    outBytes.clear();

    while (true) {
        DWORD avail = 0;
        if (!WinHttpQueryDataAvailable(request, &avail)) {
            err = "WinHttpQueryDataAvailable failed";
            WinHttpCloseHandle(request);
            WinHttpCloseHandle(connect);
            WinHttpCloseHandle(session);
            return false;
        }

        if (avail == 0) break;

        std::vector<char> buf(avail);
        DWORD read = 0;
        if (!WinHttpReadData(request, buf.data(), avail, &read)) {
            err = "WinHttpReadData failed";
            WinHttpCloseHandle(request);
            WinHttpCloseHandle(connect);
            WinHttpCloseHandle(session);
            return false;
        }

        outBytes.insert(outBytes.end(), buf.begin(), buf.begin() + read);
    }

    WinHttpCloseHandle(request);
    WinHttpCloseHandle(connect);
    WinHttpCloseHandle(session);
    return true;
}

static bool save_bytes_file(const fs::path& path, const std::vector<char>& bytes, std::string& err) {
    if (!ensure_parent_dir(path)) {
        err = "unable to create parent directory";
        return false;
    }

    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out) {
        err = "unable to open output file";
        return false;
    }

    if (!bytes.empty()) out.write(bytes.data(), (std::streamsize)bytes.size());
    if (!out) {
        err = "write failed";
        return false;
    }
    return true;
}

static int ddl_fetch_url_to_file(const std::string& url,
                                 const fs::path& out_file,
                                 bool overwrite)
{
    if (url.empty()) {
        std::cout << "DDL FETCH: missing URL\n";
        return 1;
    }
    if (out_file.empty()) {
        std::cout << "DDL FETCH: missing output file\n";
        return 1;
    }
    if (!overwrite && file_exists(out_file)) {
        std::cout << "DDL FETCH: output exists (use OVERWRITE): " << s8(out_file) << "\n";
        return 1;
    }

    std::vector<char> bytes;
    std::string err;
    if (!http_get_bytes(url, bytes, err)) {
        std::cout << "DDL FETCH: " << err << "\n";
        return 1;
    }
    if (!save_bytes_file(out_file, bytes, err)) {
        std::cout << "DDL FETCH: " << err << "\n";
        return 1;
    }

    std::cout << "DDL FETCH: wrote " << bytes.size()
              << " byte(s) to " << s8(out_file) << "\n";
    return 0;
}

#else

static int ddl_fetch_url_to_file(const std::string&,
                                 const fs::path&,
                                 bool)
{
    std::cout << "DDL FETCH: URL fetch not implemented on this platform\n";
    return 1;
}

#endif

// ---------- DBF writer ------------------------------------------------------

struct FieldDef {
    std::string name;
    char        type;
    uint32_t    length;
    uint8_t     decimals;
    std::string descriptor_name;
};

static std::string ddl_flavor_name(DbfFlavor flavor) {
    return xbase::dbf_create::flavor_name(flavor);
}

static std::string default_index_engine_for_flavor(DbfFlavor flavor) {
    switch (flavor) {
        case DbfFlavor::X64: return "CDX";
        case DbfFlavor::VFP: return "CDX";
        case DbfFlavor::FOX26: return "CNX";
        case DbfFlavor::MSDOS:
        default: return "CNX";
    }
}

static std::optional<DbfFlavor> parse_dbf_flavor_token(const std::string& token) {
    const std::string u = up(token);
    if (u == "MSDOS" || u == "DBASE") return DbfFlavor::MSDOS;
    if (u == "FOX26" || u == "FOXPRO" || u == "FOXPRO26") return DbfFlavor::FOX26;
    if (u == "VFP") return DbfFlavor::VFP;
    if (u == "X64") return DbfFlavor::X64;
    return std::nullopt;
}

static uint32_t safe_len_for_type(char t, int declared_len, DbfFlavor flavor) {
    switch (t) {
        case 'C':
            if (flavor == DbfFlavor::X64) {
                return static_cast<uint32_t>(std::max(declared_len, 1));
            }
            return static_cast<uint32_t>(std::clamp(declared_len > 0 ? declared_len : 1, 1, 255));
        case 'N':
        case 'F':
            return static_cast<uint32_t>(std::clamp(declared_len > 0 ? declared_len : 1, 1, 255));
        case 'D': return 8;
        case 'L': return 1;
        case 'M': return (flavor == DbfFlavor::X64) ? 8u : 10u;
        case 'I': return 4;
        case 'B': return 8;
        case 'Y': return 8;
        case 'T': return 8;
        default:  return 1;
    }
}

static uint8_t safe_decimals_for_type(char t, int declared_dec) {
    if (t == 'N') return (uint8_t)std::clamp(declared_dec >= 0 ? declared_dec : 0, 0, 15);
    return 0;
}

static bool is_identifier_token(const std::string& s) {
    if (s.empty()) return false;
    for (unsigned char c : s) {
        if (std::isalnum(c) == 0 && c != '_') return false;
    }
    return true;
}

static std::string json_type_name(const json& value) {
    if (value.is_null()) return "null";
    if (value.is_boolean()) return "boolean";
    if (value.is_number_integer()) return "integer";
    if (value.is_number()) return "number";
    if (value.is_string()) return "string";
    if (value.is_array()) return "array";
    if (value.is_object()) return "object";
    return "unknown";
}

static void add_validation_error(std::vector<std::string>& errors,
                                 const std::string& path,
                                 const std::string& message) {
    errors.push_back(path + ": " + message);
}

static bool has_string_value(const json& obj,
                             const char* key,
                             const std::string& path,
                             std::vector<std::string>& errors) {
    if (!obj.contains(key)) {
        add_validation_error(errors, path + "." + key, "required property is missing");
        return false;
    }
    if (!obj[key].is_string()) {
        add_validation_error(errors, path + "." + key,
                             "expected string, got " + json_type_name(obj[key]));
        return false;
    }
    return true;
}

static bool string_in_set(const std::string& value,
                          std::initializer_list<const char*> allowed) {
    for (const char* item : allowed) {
        if (value == item) return true;
    }
    return false;
}

static void validate_enum_string(const json& obj,
                                 const char* key,
                                 const std::string& path,
                                 std::initializer_list<const char*> allowed,
                                 std::vector<std::string>& errors) {
    if (!has_string_value(obj, key, path, errors)) return;
    if (!string_in_set(obj[key].get<std::string>(), allowed)) {
        add_validation_error(errors, path + "." + key, "value is outside the allowed enum");
    }
}

static bool validate_optional_integer_range(const json& obj,
                                            const char* key,
                                            const std::string& path,
                                            int min_value,
                                            int max_value,
                                            std::vector<std::string>& errors) {
    if (!obj.contains(key)) return true;
    if (!obj[key].is_number_integer()) {
        add_validation_error(errors, path + "." + key,
                             "expected integer, got " + json_type_name(obj[key]));
        return false;
    }
    const int value = obj[key].get<int>();
    if (value < min_value || value > max_value) {
        add_validation_error(errors, path + "." + key,
                             "integer is outside the allowed range");
        return false;
    }
    return true;
}

static bool validate_schema_v1_contract(const json& schema,
                                        const json& validator,
                                        std::vector<std::string>& errors) {
    if (!validator.is_object()) {
        add_validation_error(errors, "validator", "expected JSON object");
        return false;
    }
    if (!validator.contains("$id") ||
        !validator["$id"].is_string() ||
        validator["$id"].get<std::string>().find("schema_json_v1.schema.json") == std::string::npos) {
        add_validation_error(errors, "validator.$id",
                             "expected DotTalk++ schema_json_v1 validator");
    }
    if (!validator.contains("properties") ||
        !validator["properties"].is_object() ||
        !validator["properties"].contains("fields")) {
        add_validation_error(errors, "validator.properties.fields",
                             "validator does not expose the fields contract");
    }

    if (!schema.is_object()) {
        add_validation_error(errors, "$", "expected JSON object");
        return errors.empty();
    }

    for (const char* key : {"version", "name", "encoding", "date_policy",
                            "null_policy", "logical_policy", "fields"}) {
        if (!schema.contains(key)) {
            add_validation_error(errors, std::string("$.") + key,
                                 "required property is missing");
        }
    }

    if (schema.contains("version")) {
        if (!schema["version"].is_string()) {
            add_validation_error(errors, "$.version",
                                 "expected string, got " + json_type_name(schema["version"]));
        } else if (schema["version"].get<std::string>() != "1.0") {
            add_validation_error(errors, "$.version", "expected const value 1.0");
        }
    }
    if (schema.contains("name") && has_string_value(schema, "name", "$", errors) &&
        !is_identifier_token(schema["name"].get<std::string>())) {
        add_validation_error(errors, "$.name", "expected identifier token [A-Za-z0-9_]+");
    }
    if (schema.contains("encoding")) {
        (void)has_string_value(schema, "encoding", "$", errors);
    }
    if (schema.contains("date_policy")) {
        validate_enum_string(schema, "date_policy", "$", {"ISO", "FOX"}, errors);
    }
    if (schema.contains("null_policy")) {
        validate_enum_string(schema, "null_policy", "$",
                             {"EMPTY_AS_EMPTY", "EMPTY_AS_NULL"}, errors);
    }
    if (schema.contains("logical_policy")) {
        validate_enum_string(schema, "logical_policy", "$", {"TF", "ZERO_ONE"}, errors);
    }

    std::set<std::string> field_names;
    if (schema.contains("fields")) {
        const json& fields = schema["fields"];
        if (!fields.is_array()) {
            add_validation_error(errors, "$.fields",
                                 "expected array, got " + json_type_name(fields));
        } else if (fields.empty()) {
            add_validation_error(errors, "$.fields", "must contain at least one field");
        } else {
            for (std::size_t i = 0; i < fields.size(); ++i) {
                const std::string path = "$.fields[" + std::to_string(i) + "]";
                const json& fld = fields[i];
                if (!fld.is_object()) {
                    add_validation_error(errors, path,
                                         "expected object, got " + json_type_name(fld));
                    continue;
                }
                const bool has_name = has_string_value(fld, "name", path, errors);
                const bool has_type = has_string_value(fld, "type", path, errors);
                std::string name;
                if (has_name) {
                    name = fld["name"].get<std::string>();
                    if (!is_identifier_token(name)) {
                        add_validation_error(errors, path + ".name",
                                             "expected identifier token [A-Za-z0-9_]+");
                    }
                    const std::string key = up(name);
                    if (!field_names.insert(key).second) {
                        add_validation_error(errors, path + ".name",
                                             "duplicate field name");
                    }
                }
                char type = '\0';
                if (has_type) {
                    const std::string ty = fld["type"].get<std::string>();
                    if (ty.size() != 1 ||
                        !string_in_set(ty, {"C", "N", "F", "D", "L", "M", "I", "B", "Y", "T"})) {
                        add_validation_error(errors, path + ".type",
                                             "value is outside the allowed field type enum");
                    } else {
                        type = ty[0];
                    }
                }
                validate_optional_integer_range(fld, "length", path, 1, 2147483647, errors);
                validate_optional_integer_range(fld, "decimals", path, 0, 15, errors);
                if (type == 'C' || type == 'N' || type == 'F') {
                    if (!fld.contains("length")) {
                        add_validation_error(errors, path + ".length",
                                             "required for C/N/F fields");
                    }
                }
                if (type == 'D' && fld.contains("length") &&
                    fld["length"].is_number_integer() && fld["length"].get<int>() != 8) {
                    add_validation_error(errors, path + ".length",
                                         "D fields must have length 8 when length is supplied");
                }
                if ((type == 'N' || type == 'F') &&
                    fld.contains("length") && fld.contains("decimals") &&
                    fld["length"].is_number_integer() && fld["decimals"].is_number_integer() &&
                    fld["decimals"].get<int>() > fld["length"].get<int>()) {
                    add_validation_error(errors, path + ".decimals",
                                         "decimal count exceeds field length");
                }
                if ((type == 'L' || type == 'M') && fld.contains("decimals")) {
                    add_validation_error(errors, path + ".decimals",
                                         "not valid for L/M fields");
                }
            }
        }
    }

    if (schema.contains("indexes")) {
        const json& indexes = schema["indexes"];
        if (!indexes.is_array()) {
            add_validation_error(errors, "$.indexes",
                                 "expected array, got " + json_type_name(indexes));
        } else {
            for (std::size_t i = 0; i < indexes.size(); ++i) {
                const std::string path = "$.indexes[" + std::to_string(i) + "]";
                const json& idx = indexes[i];
                if (!idx.is_object()) {
                    add_validation_error(errors, path,
                                         "expected object, got " + json_type_name(idx));
                    continue;
                }
                if (has_string_value(idx, "name", path, errors) &&
                    !is_identifier_token(idx["name"].get<std::string>())) {
                    add_validation_error(errors, path + ".name",
                                         "expected identifier token [A-Za-z0-9_]+");
                }
                validate_enum_string(idx, "engine", path,
                                     {"DBF", "INX", "CNX", "CDX", "LMDB", "SQLite"}, errors);
                if (!idx.contains("order")) {
                    add_validation_error(errors, path + ".order",
                                         "required property is missing");
                } else if (!idx["order"].is_array()) {
                    add_validation_error(errors, path + ".order",
                                         "expected array, got " + json_type_name(idx["order"]));
                } else if (idx["order"].empty()) {
                    add_validation_error(errors, path + ".order",
                                         "must contain at least one field reference");
                } else {
                    for (std::size_t j = 0; j < idx["order"].size(); ++j) {
                        const std::string opath = path + ".order[" + std::to_string(j) + "]";
                        if (!idx["order"][j].is_string()) {
                            add_validation_error(errors, opath,
                                                 "expected string, got " + json_type_name(idx["order"][j]));
                            continue;
                        }
                        const std::string ref = up(idx["order"][j].get<std::string>());
                        if (!field_names.empty() && field_names.find(ref) == field_names.end()) {
                            add_validation_error(errors, opath,
                                                 "field reference is not declared in $.fields");
                        }
                    }
                }
            }
        }
    }

    if (schema.contains("relations")) {
        const json& relations = schema["relations"];
        if (!relations.is_array()) {
            add_validation_error(errors, "$.relations",
                                 "expected array, got " + json_type_name(relations));
        } else {
            for (std::size_t i = 0; i < relations.size(); ++i) {
                const std::string path = "$.relations[" + std::to_string(i) + "]";
                const json& rel = relations[i];
                if (!rel.is_object()) {
                    add_validation_error(errors, path,
                                         "expected object, got " + json_type_name(rel));
                    continue;
                }
                (void)has_string_value(rel, "name", path, errors);
                (void)has_string_value(rel, "parent_table", path, errors);
                (void)has_string_value(rel, "child_table", path, errors);
                validate_enum_string(rel, "cardinality", path,
                                     {"1:1", "1:N", "N:1", "N:N"}, errors);
                if (!rel.contains("on")) {
                    add_validation_error(errors, path + ".on",
                                         "required property is missing");
                } else if (!rel["on"].is_array() || rel["on"].empty()) {
                    add_validation_error(errors, path + ".on",
                                         "expected non-empty array");
                } else {
                    for (std::size_t j = 0; j < rel["on"].size(); ++j) {
                        const std::string on_path = path + ".on[" + std::to_string(j) + "]";
                        const json& pair = rel["on"][j];
                        if (!pair.is_object()) {
                            add_validation_error(errors, on_path,
                                                 "expected object, got " + json_type_name(pair));
                            continue;
                        }
                        (void)has_string_value(pair, "parent", on_path, errors);
                        (void)has_string_value(pair, "child", on_path, errors);
                    }
                }
            }
        }
    }

    return errors.empty();
}

static std::string descriptor_token_for(const std::string& name) {
    std::string out = name;
    if (out.size() > 10) out.resize(10);
    return up(out);
}

static void apply_descriptor_policy(std::vector<FieldDef>& fields, DbfFlavor flavor) {
    if (flavor == DbfFlavor::X64) {
        std::vector<std::string> names;
        names.reserve(fields.size());
        for (const auto& f : fields) names.push_back(f.name);
        const auto plans = xbase::field_name_policy::plan_x64_unique_fallback(names);
        for (std::size_t i = 0; i < fields.size(); ++i) {
            fields[i].descriptor_name = plans[i].descriptor_name;
        }
        return;
    }

    std::set<std::string> seen;
    for (auto& f : fields) {
        f.descriptor_name = f.name.substr(0, 10);
        const std::string token = descriptor_token_for(f.descriptor_name);
        if (!seen.insert(token).second) {
            throw std::runtime_error(
                "schema creates duplicate 10-byte DBF descriptor token: " + token);
        }
    }
}

static std::vector<FieldDef> parse_fields_from_schema(const fs::path& schema_path,
                                                      DbfFlavor flavor) {
    std::ifstream f(schema_path);
    if (!f) throw std::runtime_error("cannot open schema: " + s8(schema_path));

    json j = json::parse(f, nullptr, true, true);

    if (!j.contains("fields") || !j["fields"].is_array())
        throw std::runtime_error("schema missing 'fields' array");

    std::vector<FieldDef> out;
    out.reserve(j["fields"].size());

    for (const auto& fld : j["fields"]) {
        if (!fld.contains("name") || !fld.contains("type")) continue;

        const std::string name = fld["name"].get<std::string>();
        const std::string ty   = fld["type"].get<std::string>();
        const char t = ty.empty() ? 'C' : (char)std::toupper((unsigned char)ty[0]);

        const int len = fld.contains("length")   ? fld["length"].get<int>()   : 0;
        const int dec = fld.contains("decimals") ? fld["decimals"].get<int>() : 0;

        FieldDef d;
        d.name     = name;
        d.type     = xbase::dbf_create::supports_type_now(t, flavor) ? t : '\0';
        if (d.type == '\0') {
            throw std::runtime_error(
                "field '" + name + "' type '" + std::string(1, t) +
                "' is not supported by " + ddl_flavor_name(flavor));
        }
        d.length   = safe_len_for_type(d.type, len, flavor);
        d.decimals = safe_decimals_for_type(d.type, dec);

        if (d.type == 'D') { d.length = 8;  d.decimals = 0; }
        if (d.type == 'L') { d.length = 1;  d.decimals = 0; }
        if (d.type == 'M') { d.length = (flavor == DbfFlavor::X64) ? 8u : 10u; d.decimals = 0; }
        if (d.type == 'I') { d.length = 4;  d.decimals = 0; }
        if (d.type == 'B') { d.length = 8;  d.decimals = 0; }
        if (d.type == 'Y') { d.length = 8;  d.decimals = 4; }
        if (d.type == 'T') { d.length = 8;  d.decimals = 0; }
        if ((d.type == 'N' || d.type == 'F') && d.decimals > d.length) {
            throw std::runtime_error("field '" + name + "' decimal count exceeds length");
        }

        out.push_back(d);
    }

    if (out.empty()) out.push_back(FieldDef{"_STUB", 'C', 1, 0, {}});
    apply_descriptor_policy(out, flavor);
    return out;
}

static std::vector<xbase::dbf_create::FieldSpec> to_field_specs(const std::vector<FieldDef>& fields) {
    std::vector<xbase::dbf_create::FieldSpec> specs;
    specs.reserve(fields.size());
    for (const auto& f : fields) {
        xbase::dbf_create::FieldSpec spec;
        spec.name = f.name;
        spec.type = f.type;
        spec.len = f.length;
        spec.dec = f.decimals;
        spec.descriptor_name = f.descriptor_name;
        specs.push_back(std::move(spec));
    }
    return specs;
}

static json load_schema_index_declarations(const fs::path& schema_path,
                                           DbfFlavor flavor) {
    std::ifstream f(schema_path);
    if (!f) throw std::runtime_error("cannot open schema: " + s8(schema_path));

    json j = json::parse(f, nullptr, true, true);
    json out = json::array();
    if (!j.contains("indexes") || !j["indexes"].is_array()) return out;

    for (const auto& item : j["indexes"]) {
        if (!item.is_object()) continue;
        json idx = item;
        if (!idx.contains("engine")) {
            idx["engine"] = default_index_engine_for_flavor(flavor);
        }
        idx["status"] = "metadata_only";
        idx["physical_index_built"] = false;
        out.push_back(std::move(idx));
    }
    return out;
}

static void write_empty_dbf(const fs::path& out_dbf,
                            const std::vector<FieldDef>& fields,
                            DbfFlavor flavor)
{
    if (!ensure_parent_dir(out_dbf))
        throw std::runtime_error("cannot create parent directory for: " + s8(out_dbf));

    std::string err;
    if (!xbase::dbf_create::create_dbf(s8(out_dbf), to_field_specs(fields), flavor, err)) {
        throw std::runtime_error(err.empty() ? ("cannot write: " + s8(out_dbf)) : err);
    }
}

static void append_blank_records(const fs::path& out_dbf,
                                 uint32_t count)
{
    if (count == 0) return;

    xbase::DbArea area;
    area.open(s8(out_dbf));
    for (uint32_t i = 0; i < count; ++i) {
        if (!area.appendBlank()) throw std::runtime_error("failed to append blank record");
    }
    area.close();
}

// ---------- command core ----------------------------------------------------

static int ddl_validate_schema_v1(const fs::path& schema, const fs::path& validator) {
    if (!file_exists(schema)) {
        std::cout << "DDL VALIDATE: schema file not found: " << s8(schema) << "\n";
        return 1;
    }
    if (!file_exists(validator)) {
        std::cout << "DDL VALIDATE: validator file not found: " << s8(validator) << "\n";
        return 1;
    }

    json schema_json;
    json validator_json;
    try {
        std::ifstream sf(schema);
        schema_json = json::parse(sf, nullptr, true, true);
    } catch (const std::exception& ex) {
        std::cout << "DDL VALIDATE: schema parse failed: " << ex.what() << "\n";
        return 1;
    }
    try {
        std::ifstream vf(validator);
        validator_json = json::parse(vf, nullptr, true, true);
    } catch (const std::exception& ex) {
        std::cout << "DDL VALIDATE: validator parse failed: " << ex.what() << "\n";
        return 1;
    }

    std::vector<std::string> errors;
    const bool ok = validate_schema_v1_contract(schema_json, validator_json, errors);
    if (!ok) {
        std::cout << "DDL VALIDATE: FAILED\n";
        std::cout << "  schema    = " << s8(schema) << "\n";
        std::cout << "  validator = " << s8(validator) << "\n";
        std::cout << "  errors    = " << errors.size() << "\n";
        for (const auto& err : errors) {
            std::cout << "  - " << err << "\n";
        }
        return 1;
    }

    std::cout << "DDL VALIDATE: OK\n";
    std::cout << "  schema    = " << s8(schema) << "\n";
    std::cout << "  validator = " << s8(validator) << "\n";
    std::cout << "  contract  = schema_json_v1\n";
    return 0;
}

static int ddl_create_dbf_real(
    const fs::path&    out_dbf,
    const fs::path&    schema,
    DbfFlavor          flavor,
    bool               overwrite,
    const fs::path&    seed_csv,
    uint32_t           seed_blank,
    const fs::path&    rejects_csv,
    bool               emit_sidecars)
{
    if (!file_exists(schema)) {
        std::cout << "DDL CREATE DBF: schema file not found: " << s8(schema) << "\n";
        return 1;
    }
    if (!overwrite && file_exists(out_dbf)) {
        std::cout << "DDL CREATE DBF: output exists (use OVERWRITE): " << s8(out_dbf) << "\n";
        return 1;
    }

    std::vector<FieldDef> fields;
    json declared_indexes = json::array();
    try {
        fields = parse_fields_from_schema(schema, flavor);
        declared_indexes = load_schema_index_declarations(schema, flavor);
        write_empty_dbf(out_dbf, fields, flavor);
    } catch (const std::exception& ex) {
        std::cout << "DDL CREATE DBF: " << ex.what() << "\n";
        return 1;
    }

    uint32_t rows_written = 0;
    uint32_t rows_rejected = 0;

    try {
        if (seed_blank > 0) {
            append_blank_records(out_dbf, seed_blank);
            rows_written += seed_blank;
        } else if (!seed_csv.empty()) {
            if (!file_exists(seed_csv)) {
                std::cout << "DDL CREATE DBF: SEED CSV failed: cannot open CSV: "
                          << s8(seed_csv) << "\n";
                return 1;
            }
            std::cout << "DDL CREATE DBF: SEED CSV not yet implemented in this drop-in\n";
            return 1;
        }
    } catch (const std::exception& ex) {
        std::cout << "DDL CREATE DBF: seeding failed: " << ex.what() << "\n";
        return 1;
    }

    const std::string table = out_dbf.stem().string();
    const fs::path sidecar_dir = out_dbf.parent_path().empty() ? fs::path(".") : out_dbf.parent_path();

    if (emit_sidecars) {
        json ddl = json::object();
        ddl["table"] = table;
        ddl["engine"] = "DBF";
        ddl["dbf_flavor"] = ddl_flavor_name(flavor);
        ddl["schema_version"] = "1.0";
        ddl["fields"] = json::array();
        ddl["indexes"] = declared_indexes;
        ddl["relations"] = json::array();

        json notes = json::array();
        notes.push_back("DBF header written");
        ddl["engine_notes"] = notes;

        for (const auto& f : fields) {
            json jf = json::object();
            jf["name"] = f.name;
            jf["type"] = std::string(1, f.type);
            jf["length"] = f.length;
            jf["decimals"] = f.decimals;
            if (!f.descriptor_name.empty()) jf["descriptor_name"] = f.descriptor_name;
            ddl["fields"].push_back(jf);
        }

        write_text_file(sidecar_dir / (table + ".ddl.json"), ddl.dump(2));

        std::string operation = "CREATE";
        if (!seed_csv.empty()) operation = "SEED";
        else if (seed_blank > 0) operation = "SEED_BLANK";

        json source = json::object();
        if (!seed_csv.empty()) {
            source["type"] = "CSV";
            source["path"] = s8(seed_csv);
        } else if (seed_blank > 0) {
            source["type"]  = "BLANK";
            source["count"] = seed_blank;
        } else {
            source["type"] = "NONE";
        }

        json result = json::object();
        result["rows_written"]  = rows_written;
        result["rows_rejected"] = rows_rejected;
        if (!rejects_csv.empty()) result["rejects_path"] = s8(rejects_csv);

        json schema_obj = json::object();
        schema_obj["name"] = table;
        schema_obj["version"] = "1.0";
        schema_obj["path"] = s8(schema);

        json engine_obj = json::object();
        engine_obj["name"] = "dottalkpp";
        engine_obj["version"] = "alpha";
        engine_obj["platform"] = "dbf-create-backend";
        engine_obj["dbf_flavor"] = ddl_flavor_name(flavor);

        json timestamps = json::object();
        timestamps["finished"] = now_utc_iso();

        json load = json::object();
        load["table"] = table;
        load["schema"] = schema_obj;
        load["operation"] = operation;
        load["source"] = source;
        load["result"] = result;
        load["engine"] = engine_obj;
        load["timestamps"] = timestamps;

        write_text_file(sidecar_dir / (table + ".load.json"), load.dump(2));

        json idx = json::object();
        idx["table"] = table;
        idx["engine"] = default_index_engine_for_flavor(flavor);
        idx["dbf_flavor"] = ddl_flavor_name(flavor);
        idx["indexes"] = declared_indexes;
        idx["warnings"] = json::array();
        idx["warnings"].push_back("Index declarations are metadata-only in this DDL milestone; no physical index was built.");

        write_text_file(sidecar_dir / (table + ".indexes.json"), idx.dump(2));

        copy_file_safe(schema, sidecar_dir / (table + ".schema.copy.json"));
    }

    if (!rejects_csv.empty() && rows_rejected > 0) {
        write_text_file(rejects_csv, "ERROR_CODE,MESSAGE,FIELD,VALUE,ROWNUM\n");
    }

    std::ostringstream ok;
    ok << "DDL CREATE DBF: OK";
    ok << "\n  schema = " << s8(schema);
    ok << "\n  output = " << s8(out_dbf);
    ok << "\n  flavor = " << ddl_flavor_name(flavor);
    if (rows_written > 0) ok << "\n  blank_rows = " << rows_written;
    if (emit_sidecars) ok << "\n  sidecars = " << s8(sidecar_dir);
    ok << "\n";
    std::cout << ok.str();
    return 0;
}


static void print_ddl_usage()
{
    std::cout
        << "Usage:\n"
        << "  DDL USAGE\n"
        << "  DDL FETCH <url> TO <file> [OVERWRITE]\n"
        << "  DDL VALIDATE <schema.json> USING <validator.json>\n"
        << "  DDL CREATE DBF <out.dbf> FROM <schema.json> [OVERWRITE]\n"
        << "  DDL CREATE DBF <MSDOS|DBASE|FOX26|FOXPRO|VFP|X64> <out.dbf> FROM <schema.json> [OVERWRITE]\n"
        << "      [SEED CSV <path.csv>] [SEED BLANK <n>]\n"
        << "      [REJECTS <rejects.csv>] [EMIT SIDECARS]\n"
        << "Path rules:\n"
        << "  - Relative schema inputs resolve under SCHEMAS.\n"
        << "  - Relative FETCH outputs resolve under SCHEMAS.\n"
        << "  - Relative CREATE DBF outputs resolve under TMP.\n"
        << "Notes:\n"
        << "  - CREATE DBF defaults to MSDOS/DBASE unless a flavor token is supplied.\n"
        << "  - CREATE DBF refuses existing output unless OVERWRITE is supplied.\n"
        << "  - EMIT SIDECARS writes companion schema/load/index metadata.\n";
}

// ---------- command entry ---------------------------------------------------

void cmd_DDL(xbase::DbArea& /*area*/, std::istringstream& iss) {
    const std::string subcmd = up(read_word(iss));

    if (subcmd.empty() || subcmd == "USAGE" || subcmd == "HELP" ||
        subcmd == "?" || subcmd == "/?" || subcmd == "-H" || subcmd == "--HELP") {
        print_ddl_usage();
        return;
    }

    if (subcmd == "FETCH") {
        const std::string url = read_pathish(iss);
        const std::string to_kw = up(read_word(iss));
        if (to_kw != "TO") {
            std::cout << "DDL FETCH: expected TO <file>\n";
            return;
        }
        const std::string out_raw = read_pathish(iss);

        bool overwrite = false;
        while (iss && !iss.eof()) {
            const std::string tok = up(read_word(iss));
            if (tok.empty()) break;
            if (tok == "OVERWRITE") {
                overwrite = true;
                continue;
            }
            break;
        }

        const fs::path out_file = resolve_ddl_fetch_output(out_raw);
        (void)ddl_fetch_url_to_file(url, out_file, overwrite);
        return;
    }

    if (subcmd == "VALIDATE") {
        const std::string schema_raw = read_pathish(iss);
        const std::string using_kw = up(read_word(iss));
        if (using_kw != "USING") {
            std::cout << "DDL VALIDATE: expected USING <validator.json>\n";
            return;
        }
        const std::string validator_raw = read_pathish(iss);

        const fs::path schema = resolve_ddl_input(schema_raw);
        const fs::path validator = resolve_ddl_input(validator_raw);
        (void)ddl_validate_schema_v1(schema, validator);
        return;
    }

    if (subcmd == "CREATE") {
        const std::string kind = up(read_word(iss));
        if (kind != "DBF") {
            std::cout << "DDL CREATE: only DBF supported\n";
            return;
        }

        DbfFlavor flavor = DbfFlavor::MSDOS;
        std::string out_dbf_raw = read_pathish(iss);
        if (auto parsed_flavor = parse_dbf_flavor_token(out_dbf_raw)) {
            flavor = *parsed_flavor;
            out_dbf_raw = read_pathish(iss);
        } else if (up(out_dbf_raw) == "AS") {
            const std::string flavor_raw = read_word(iss);
            auto parsed = parse_dbf_flavor_token(flavor_raw);
            if (!parsed) {
                std::cout << "DDL CREATE DBF: expected DBF flavor after AS\n";
                return;
            }
            flavor = *parsed;
            out_dbf_raw = read_pathish(iss);
        }

        const std::string from_kw = up(read_word(iss));
        if (from_kw == "AS") {
            const std::string flavor_raw = read_word(iss);
            auto parsed = parse_dbf_flavor_token(flavor_raw);
            if (!parsed) {
                std::cout << "DDL CREATE DBF: expected DBF flavor after AS\n";
                return;
            }
            flavor = *parsed;
        } else if (from_kw != "FROM") {
            std::cout << "DDL CREATE DBF: expected FROM <schema.json>\n";
            return;
        }
        const std::string actual_from_kw = (from_kw == "AS") ? up(read_word(iss)) : from_kw;
        if (actual_from_kw != "FROM") {
            std::cout << "DDL CREATE DBF: expected FROM <schema.json>\n";
            return;
        }
        const std::string schema_raw = read_pathish(iss);

        bool overwrite = false;
        std::string seed_csv_raw;
        uint32_t    seed_blank = 0;
        std::string rejects_raw;
        bool emit_sidecars = false;

        while (iss && !iss.eof()) {
            std::streampos p = iss.tellg();
            const std::string tok = up(read_word(iss));
            if (tok.empty()) break;

            if (tok == "OVERWRITE") {
                overwrite = true;
                continue;
            }

            if (tok == "SEED") {
                const std::string mode_kw = up(read_word(iss));
                if (mode_kw == "CSV") {
                    seed_csv_raw = read_pathish(iss);
                    continue;
                } else if (mode_kw == "BLANK") {
                    const std::string n = read_word(iss);
                    if (!is_digits(n)) {
                        std::cout << "DDL CREATE DBF: expected SEED BLANK <N>\n";
                        return;
                    }
                    seed_blank = (uint32_t)std::stoul(n);
                    continue;
                } else {
                    std::cout << "DDL CREATE DBF: expected CSV or BLANK after SEED\n";
                    return;
                }
            }

            if (tok == "REJECTS") {
                rejects_raw = read_pathish(iss);
                continue;
            }

            if (tok == "EMIT") {
                const std::string sc_kw = up(read_word(iss));
                if (sc_kw != "SIDECARS") {
                    std::cout << "DDL CREATE DBF: expected SIDECARS after EMIT\n";
                    return;
                }
                emit_sidecars = true;
                continue;
            }

            iss.clear();
            iss.seekg(p);
            break;
        }

        if (!seed_csv_raw.empty() && seed_blank > 0) {
            std::cout << "DDL CREATE DBF: both SEED CSV and SEED BLANK provided; CSV takes precedence.\n";
        }

        const fs::path out_dbf = resolve_ddl_dbf_output(out_dbf_raw);
        const fs::path schema = resolve_ddl_input(schema_raw);
        const fs::path seed_csv = seed_csv_raw.empty() ? fs::path{} : resolve_seed_csv_input(seed_csv_raw);
        const fs::path rejects_csv = rejects_raw.empty() ? fs::path{} : resolve_rejects_output(rejects_raw);

        (void)ddl_create_dbf_real(out_dbf, schema, flavor, overwrite, seed_csv, seed_blank, rejects_csv, emit_sidecars);
        return;
    }

    print_ddl_usage();
}
