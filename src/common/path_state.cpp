// common/path_state.cpp
#include "common/path_state.hpp"

#include <algorithm>
#include <cctype>
#include <sstream>
#include <stdexcept>
#include <system_error>
#include <utility>

namespace dottalk::paths {

namespace {

std::string trim_copy(std::string s)
{
    auto is_space = [](unsigned char ch) { return std::isspace(ch) != 0; };

    s.erase(s.begin(), std::find_if(s.begin(), s.end(),
        [&](unsigned char c) { return !is_space(c); }));

    s.erase(std::find_if(s.rbegin(), s.rend(),
        [&](unsigned char c) { return !is_space(c); }).base(), s.end());

    return s;
}

std::string upper_copy(std::string s)
{
    for (auto& c : s)
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    return s;
}

std::string normalize_user_name(std::string name)
{
    name = trim_copy(std::move(name));
    if (name.empty())
        return "default";
    return name;
}

fs::path norm_abs(const fs::path& p)
{
    try {
        return fs::absolute(p).lexically_normal();
    } catch (...) {
        return p;
    }
}

void build_user_paths(State& s)
{
    s.user_root = s.root / "user";

    s.user_public_root = s.user_root / "public";
    s.user_default_root = s.user_root / "default";
    s.user_current_root = s.user_root / s.current_user;

    s.pub_workspaces_root = s.user_public_root / "workspaces";
    s.pub_scripts_root = s.user_public_root / "scripts";
    s.pub_security_root = s.user_public_root / "security";
    s.pub_storage_root = s.user_public_root / "storage";
    s.pub_prefs_root = s.user_public_root / "prefs";
    s.pub_logs_root = s.user_public_root / "logs";
    s.pub_tmp_root = s.user_public_root / "tmp";

    s.def_workspaces_root = s.user_default_root / "workspaces";
    s.def_scripts_root = s.user_default_root / "scripts";
    s.def_security_root = s.user_default_root / "security";
    s.def_storage_root = s.user_default_root / "storage";
    s.def_prefs_root = s.user_default_root / "prefs";
    s.def_logs_root = s.user_default_root / "logs";
    s.def_tmp_root = s.user_default_root / "tmp";

    s.cur_workspaces_root = s.user_current_root / "workspaces";
    s.cur_scripts_root = s.user_current_root / "scripts";
    s.cur_security_root = s.user_current_root / "security";
    s.cur_storage_root = s.user_current_root / "storage";
    s.cur_prefs_root = s.user_current_root / "prefs";
    s.cur_logs_root = s.user_current_root / "logs";
    s.cur_tmp_root = s.user_current_root / "tmp";
    s.user_diagrams_root = s.user_current_root / "diagrams";
}

void build_all_paths(State& s)
{
    if (s.data_root.empty())
        throw std::runtime_error("path_state: data_root must not be empty");

    s.root = s.data_root.parent_path();

    s.docs_root = s.root / "docs";
    s.system_diagrams_root = s.docs_root / "generated" / "diagrams";

    s.dbf_root = s.data_root / "dbf";
    s.xdbf_root = s.data_root / "xdbf";
    s.dbf_x32_root = s.dbf_root / "x32";
    s.dbf_x64_root = s.dbf_root / "x64";

    s.indexes_root = s.data_root / "indexes";
    s.indexes_x32_root = s.indexes_root / "x32";
    s.indexes_x64_root = s.indexes_root / "x64";

    s.lmdb_root = s.data_root / "lmdb";
    s.ram_root = s.data_root / "ram";
    s.workspaces_root = s.data_root / "workspaces";
    s.schemas_root = s.data_root / "schemas";
    s.projects_root = s.data_root / "projects";
    s.scripts_root = s.data_root / "scripts";
    s.tests_root = s.data_root / "tests";
    s.help_root = s.data_root / "help";
    s.logs_root = s.data_root / "logs";
    s.tmp_root = s.data_root / "tmp";
    s.tmp_out_root = s.tmp_root / "out";
    s.tmp_system_root = s.tmp_root / "system";

    build_user_paths(s);
}

} // namespace

State& state()
{
    static State s;
    return s;
}

void initialize(const fs::path& bin_root,
                const fs::path& data_root,
                std::string current_user_name)
{
    State& s = state();
    s.bin_root = norm_abs(bin_root);
    s.data_root = norm_abs(data_root);
    s.current_user = normalize_user_name(std::move(current_user_name));
    build_all_paths(s);
}

void initialize_from_bin(const fs::path& bin_root,
                         std::string current_user_name)
{
    const fs::path abs_bin = norm_abs(bin_root);
    const fs::path root = abs_bin.parent_path();
    initialize(abs_bin, root / "data", std::move(current_user_name));
}

void set_current_user(std::string current_user_name)
{
    State& s = state();
    s.current_user = normalize_user_name(std::move(current_user_name));
    build_user_paths(s);
}

const std::string& current_user()
{
    return state().current_user;
}

fs::path get_slot(Slot slot)
{
    const State& s = state();

    switch (slot) {
    case Slot::BIN: return s.bin_root;
    case Slot::DATA: return s.data_root;
    case Slot::DOCS: return s.docs_root;
    case Slot::SYSTEM_DIAGRAMS: return s.system_diagrams_root;
    case Slot::USER_DIAGRAMS: return s.user_diagrams_root;
    case Slot::DBF: return s.dbf_root;
    case Slot::XDBF: return s.xdbf_root;
    case Slot::DBF_X32: return s.dbf_x32_root;
    case Slot::DBF_X64: return s.dbf_x64_root;
    case Slot::INDEXES: return s.indexes_root;
    case Slot::INDEXES_X32: return s.indexes_x32_root;
    case Slot::INDEXES_X64: return s.indexes_x64_root;
    case Slot::LMDB: return s.lmdb_root;
    case Slot::RAM: return s.ram_root;
    case Slot::WORKSPACES: return s.workspaces_root;
    case Slot::SCHEMAS: return s.schemas_root;
    case Slot::PROJECTS: return s.projects_root;
    case Slot::SCRIPTS: return s.scripts_root;
    case Slot::TESTS: return s.tests_root;
    case Slot::HELP: return s.help_root;
    case Slot::LOGS: return s.logs_root;
    case Slot::TMP: return s.tmp_root;
    case Slot::TMP_OUT: return s.tmp_out_root;
    case Slot::TMP_SYSTEM: return s.tmp_system_root;

    case Slot::USER: return s.user_root;
    case Slot::USER_PUBLIC: return s.user_public_root;
    case Slot::USER_DEFAULT: return s.user_default_root;
    case Slot::USER_CURRENT: return s.user_current_root;

    case Slot::PUB_WORKSPACES: return s.pub_workspaces_root;
    case Slot::PUB_SCRIPTS: return s.pub_scripts_root;
    case Slot::PUB_SECURITY: return s.pub_security_root;
    case Slot::PUB_STORAGE: return s.pub_storage_root;
    case Slot::PUB_PREFS: return s.pub_prefs_root;
    case Slot::PUB_LOGS: return s.pub_logs_root;
    case Slot::PUB_TMP: return s.pub_tmp_root;

    case Slot::DEF_WORKSPACES: return s.def_workspaces_root;
    case Slot::DEF_SCRIPTS: return s.def_scripts_root;
    case Slot::DEF_SECURITY: return s.def_security_root;
    case Slot::DEF_STORAGE: return s.def_storage_root;
    case Slot::DEF_PREFS: return s.def_prefs_root;
    case Slot::DEF_LOGS: return s.def_logs_root;
    case Slot::DEF_TMP: return s.def_tmp_root;

    case Slot::CUR_WORKSPACES: return s.cur_workspaces_root;
    case Slot::CUR_SCRIPTS: return s.cur_scripts_root;
    case Slot::CUR_SECURITY: return s.cur_security_root;
    case Slot::CUR_STORAGE: return s.cur_storage_root;
    case Slot::CUR_PREFS: return s.cur_prefs_root;
    case Slot::CUR_LOGS: return s.cur_logs_root;
    case Slot::CUR_TMP: return s.cur_tmp_root;
    }

    throw std::runtime_error("path_state: unknown slot");
}

void set_slot(Slot slot, const fs::path& value)
{
    State& s = state();
    const fs::path abs = value.empty() ? fs::path{} : norm_abs(value);

    switch (slot) {
    case Slot::BIN: s.bin_root = abs; break;
    case Slot::DATA: s.data_root = abs; break;
    case Slot::DOCS: s.docs_root = abs; break;
    case Slot::SYSTEM_DIAGRAMS: s.system_diagrams_root = abs; break;
    case Slot::USER_DIAGRAMS: s.user_diagrams_root = abs; break;
    case Slot::DBF: s.dbf_root = abs; break;
    case Slot::XDBF: s.xdbf_root = abs; break;
    case Slot::DBF_X32: s.dbf_x32_root = abs; break;
    case Slot::DBF_X64: s.dbf_x64_root = abs; break;
    case Slot::INDEXES: s.indexes_root = abs; break;
    case Slot::INDEXES_X32: s.indexes_x32_root = abs; break;
    case Slot::INDEXES_X64: s.indexes_x64_root = abs; break;
    case Slot::LMDB: s.lmdb_root = abs; break;
    case Slot::RAM: s.ram_root = abs; break;
    case Slot::WORKSPACES: s.workspaces_root = abs; break;
    case Slot::SCHEMAS: s.schemas_root = abs; break;
    case Slot::PROJECTS: s.projects_root = abs; break;
    case Slot::SCRIPTS: s.scripts_root = abs; break;
    case Slot::TESTS: s.tests_root = abs; break;
    case Slot::HELP: s.help_root = abs; break;
    case Slot::LOGS: s.logs_root = abs; break;
    case Slot::TMP: s.tmp_root = abs; break;
    case Slot::TMP_OUT: s.tmp_out_root = abs; break;
    case Slot::TMP_SYSTEM: s.tmp_system_root = abs; break;

    case Slot::USER: s.user_root = abs; break;
    case Slot::USER_PUBLIC: s.user_public_root = abs; break;
    case Slot::USER_DEFAULT: s.user_default_root = abs; break;
    case Slot::USER_CURRENT: s.user_current_root = abs; break;

    case Slot::PUB_WORKSPACES: s.pub_workspaces_root = abs; break;
    case Slot::PUB_SCRIPTS: s.pub_scripts_root = abs; break;
    case Slot::PUB_SECURITY: s.pub_security_root = abs; break;
    case Slot::PUB_STORAGE: s.pub_storage_root = abs; break;
    case Slot::PUB_PREFS: s.pub_prefs_root = abs; break;
    case Slot::PUB_LOGS: s.pub_logs_root = abs; break;
    case Slot::PUB_TMP: s.pub_tmp_root = abs; break;

    case Slot::DEF_WORKSPACES: s.def_workspaces_root = abs; break;
    case Slot::DEF_SCRIPTS: s.def_scripts_root = abs; break;
    case Slot::DEF_SECURITY: s.def_security_root = abs; break;
    case Slot::DEF_STORAGE: s.def_storage_root = abs; break;
    case Slot::DEF_PREFS: s.def_prefs_root = abs; break;
    case Slot::DEF_LOGS: s.def_logs_root = abs; break;
    case Slot::DEF_TMP: s.def_tmp_root = abs; break;

    case Slot::CUR_WORKSPACES: s.cur_workspaces_root = abs; break;
    case Slot::CUR_SCRIPTS: s.cur_scripts_root = abs; break;
    case Slot::CUR_SECURITY: s.cur_security_root = abs; break;
    case Slot::CUR_STORAGE: s.cur_storage_root = abs; break;
    case Slot::CUR_PREFS: s.cur_prefs_root = abs; break;
    case Slot::CUR_LOGS: s.cur_logs_root = abs; break;
    case Slot::CUR_TMP: s.cur_tmp_root = abs; break;
    }

    if (slot == Slot::BIN || slot == Slot::DATA)
        build_all_paths(s);
}

void reset()
{
    State& s = state();

    if (!s.data_root.empty()) {
        const fs::path data_root = s.data_root;
        const fs::path bin_root = s.bin_root;
        const std::string user = s.current_user;
        initialize(bin_root.empty() ? (data_root.parent_path() / "bin") : bin_root,
                   data_root,
                   user);
        return;
    }

    s = State{};
}

std::optional<Slot> slot_from_string(const std::string& name)
{
    const std::string key = upper_copy(trim_copy(name));

    if (key == "BIN") return Slot::BIN;
    if (key == "DATA") return Slot::DATA;
    if (key == "DOCS") return Slot::DOCS;
    if (key == "SYSTEM_DIAGRAMS" || key == "SYSDIAGRAMS" || key == "SYS_DIAGRAMS" ||
        key == "DIAGRAMS" || key == "DRAWIO" || key == "DRAWIO_SYSTEM") return Slot::SYSTEM_DIAGRAMS;
    if (key == "USER_DIAGRAMS" || key == "USERDIAGRAMS" || key == "CUR_DIAGRAMS" ||
        key == "MY_DIAGRAMS" || key == "DRAWIO_USER") return Slot::USER_DIAGRAMS;
    if (key == "DBF") return Slot::DBF;
    if (key == "XDBF") return Slot::XDBF;
    if (key == "DBF_X32" || key == "DBFX32") return Slot::DBF_X32;
    if (key == "DBF_X64" || key == "DBFX64") return Slot::DBF_X64;
    if (key == "INDEXES") return Slot::INDEXES;
    if (key == "INDEXES_X32" || key == "INDEXX32") return Slot::INDEXES_X32;
    if (key == "INDEXES_X64" || key == "INDEXX64") return Slot::INDEXES_X64;
    if (key == "LMDB") return Slot::LMDB;
    if (key == "RAM" || key == "MEM") return Slot::RAM;
    if (key == "WORKSPACES") return Slot::WORKSPACES;
    if (key == "SCHEMAS") return Slot::SCHEMAS;
    if (key == "PROJECTS") return Slot::PROJECTS;
    if (key == "SCRIPTS") return Slot::SCRIPTS;
    if (key == "TESTS") return Slot::TESTS;
    if (key == "HELP") return Slot::HELP;
    if (key == "LOGS") return Slot::LOGS;
    if (key == "TMP") return Slot::TMP;
    if (key == "TMP_OUT" || key == "TMPOUT") return Slot::TMP_OUT;
    if (key == "TMP_SYSTEM" || key == "TMPSYSTEM") return Slot::TMP_SYSTEM;

    if (key == "USER") return Slot::USER;
    if (key == "USER_PUBLIC" || key == "PUBLIC") return Slot::USER_PUBLIC;
    if (key == "USER_DEFAULT" || key == "DEFAULT") return Slot::USER_DEFAULT;
    if (key == "USER_CURRENT" || key == "CURRENT") return Slot::USER_CURRENT;

    if (key == "PUB_WORK" || key == "PUB_WORKSPACES") return Slot::PUB_WORKSPACES;
    if (key == "PUB_SCRIPT" || key == "PUB_SCRIPTS") return Slot::PUB_SCRIPTS;
    if (key == "PUB_SECURITY" || key == "PUB_SEC") return Slot::PUB_SECURITY;
    if (key == "PUB_STORAGE" || key == "PUB_STORE") return Slot::PUB_STORAGE;
    if (key == "PUB_PREFS") return Slot::PUB_PREFS;
    if (key == "PUB_LOGS") return Slot::PUB_LOGS;
    if (key == "PUB_TMP") return Slot::PUB_TMP;

    if (key == "DEF_WORK" || key == "DEF_WORKSPACES") return Slot::DEF_WORKSPACES;
    if (key == "DEF_SCRIPT" || key == "DEF_SCRIPTS") return Slot::DEF_SCRIPTS;
    if (key == "DEF_SECURITY" || key == "DEF_SEC") return Slot::DEF_SECURITY;
    if (key == "DEF_STORAGE" || key == "DEF_STORE") return Slot::DEF_STORAGE;
    if (key == "DEF_PREFS") return Slot::DEF_PREFS;
    if (key == "DEF_LOGS") return Slot::DEF_LOGS;
    if (key == "DEF_TMP") return Slot::DEF_TMP;

    if (key == "CUR_WORK" || key == "CUR_WORKSPACES") return Slot::CUR_WORKSPACES;
    if (key == "CUR_SCRIPT" || key == "CUR_SCRIPTS") return Slot::CUR_SCRIPTS;
    if (key == "CUR_SECURITY" || key == "CUR_SEC") return Slot::CUR_SECURITY;
    if (key == "CUR_STORAGE" || key == "CUR_STORE") return Slot::CUR_STORAGE;
    if (key == "CUR_PREFS") return Slot::CUR_PREFS;
    if (key == "CUR_LOGS") return Slot::CUR_LOGS;
    if (key == "CUR_TMP") return Slot::CUR_TMP;

    return std::nullopt;
}

bool slot_from_string(const std::string& name, Slot& out)
{
    const auto found = slot_from_string(name);
    if (!found.has_value())
        return false;
    out = *found;
    return true;
}

std::string slot_name(Slot slot)
{
    switch (slot) {
    case Slot::BIN: return "BIN";
    case Slot::DATA: return "DATA";
    case Slot::DOCS: return "DOCS";
    case Slot::SYSTEM_DIAGRAMS: return "SYSTEM_DIAGRAMS";
    case Slot::USER_DIAGRAMS: return "USER_DIAGRAMS";
    case Slot::DBF: return "DBF";
    case Slot::XDBF: return "XDBF";
    case Slot::DBF_X32: return "DBF_X32";
    case Slot::DBF_X64: return "DBF_X64";
    case Slot::INDEXES: return "INDEXES";
    case Slot::INDEXES_X32: return "INDEXES_X32";
    case Slot::INDEXES_X64: return "INDEXES_X64";
    case Slot::LMDB: return "LMDB";
    case Slot::RAM: return "RAM";
    case Slot::WORKSPACES: return "WORKSPACES";
    case Slot::SCHEMAS: return "SCHEMAS";
    case Slot::PROJECTS: return "PROJECTS";
    case Slot::SCRIPTS: return "SCRIPTS";
    case Slot::TESTS: return "TESTS";
    case Slot::HELP: return "HELP";
    case Slot::LOGS: return "LOGS";
    case Slot::TMP: return "TMP";
    case Slot::TMP_OUT: return "TMP_OUT";
    case Slot::TMP_SYSTEM: return "TMP_SYSTEM";

    case Slot::USER: return "USER";
    case Slot::USER_PUBLIC: return "USER_PUBLIC";
    case Slot::USER_DEFAULT: return "USER_DEFAULT";
    case Slot::USER_CURRENT: return "USER_CURRENT";

    case Slot::PUB_WORKSPACES: return "PUB_WORKSPACES";
    case Slot::PUB_SCRIPTS: return "PUB_SCRIPTS";
    case Slot::PUB_SECURITY: return "PUB_SECURITY";
    case Slot::PUB_STORAGE: return "PUB_STORAGE";
    case Slot::PUB_PREFS: return "PUB_PREFS";
    case Slot::PUB_LOGS: return "PUB_LOGS";
    case Slot::PUB_TMP: return "PUB_TMP";

    case Slot::DEF_WORKSPACES: return "DEF_WORKSPACES";
    case Slot::DEF_SCRIPTS: return "DEF_SCRIPTS";
    case Slot::DEF_SECURITY: return "DEF_SECURITY";
    case Slot::DEF_STORAGE: return "DEF_STORAGE";
    case Slot::DEF_PREFS: return "DEF_PREFS";
    case Slot::DEF_LOGS: return "DEF_LOGS";
    case Slot::DEF_TMP: return "DEF_TMP";

    case Slot::CUR_WORKSPACES: return "CUR_WORKSPACES";
    case Slot::CUR_SCRIPTS: return "CUR_SCRIPTS";
    case Slot::CUR_SECURITY: return "CUR_SECURITY";
    case Slot::CUR_STORAGE: return "CUR_STORAGE";
    case Slot::CUR_PREFS: return "CUR_PREFS";
    case Slot::CUR_LOGS: return "CUR_LOGS";
    case Slot::CUR_TMP: return "CUR_TMP";
    }

    return "UNKNOWN";
}

std::vector<fs::path> workspace_search_roots()
{
    const State& s = state();
    return {
        s.cur_workspaces_root,
        s.pub_workspaces_root,
        s.def_workspaces_root,
        s.workspaces_root
    };
}

std::vector<fs::path> script_search_roots()
{
    const State& s = state();
    return {
        s.cur_scripts_root,
        s.pub_scripts_root,
        s.def_scripts_root,
        s.scripts_root
    };
}

void ensure_directories()
{
    const State& s = state();
    std::error_code ec;

    const std::vector<fs::path> dirs = {
        s.data_root,
        s.docs_root,
        s.system_diagrams_root,
        s.user_diagrams_root,
        s.dbf_root,
        s.xdbf_root,
        s.dbf_x32_root,
        s.dbf_x64_root,
        s.indexes_root,
        s.indexes_x32_root,
        s.indexes_x64_root,
        s.lmdb_root,
        s.workspaces_root,
        s.schemas_root,
        s.projects_root,
        s.scripts_root,
        s.tests_root,
        s.help_root,
        s.logs_root,
        s.tmp_root,
        s.tmp_out_root,
        s.tmp_system_root,

        s.user_root,
        s.user_public_root,
        s.user_default_root,
        s.user_current_root,

        s.pub_workspaces_root,
        s.pub_scripts_root,
        s.pub_security_root,
        s.pub_storage_root,
        s.pub_prefs_root,
        s.pub_logs_root,
        s.pub_tmp_root,

        s.def_workspaces_root,
        s.def_scripts_root,
        s.def_security_root,
        s.def_storage_root,
        s.def_prefs_root,
        s.def_logs_root,
        s.def_tmp_root,

        s.cur_workspaces_root,
        s.cur_scripts_root,
        s.cur_security_root,
        s.cur_storage_root,
        s.cur_prefs_root,
        s.cur_logs_root,
        s.cur_tmp_root
    };

    for (const auto& dir : dirs) {
        if (dir.empty())
            continue;
        fs::create_directories(dir, ec);
        ec.clear();
    }
}

std::string describe()
{
    const State& s = state();

    std::ostringstream out;
    out
        << "BIN        = " << s.bin_root.string() << "\n"
        << "DATA       = " << s.data_root.string() << "\n"
        << "DOCS       = " << s.docs_root.string() << "\n"
        << "SYS_DIAG   = " << s.system_diagrams_root.string() << "\n"
        << "USER_DIAG  = " << s.user_diagrams_root.string() << "\n"
        << "DBF        = " << s.dbf_root.string() << "\n"
        << "XDBF       = " << s.xdbf_root.string() << "\n"
        << "DBF_X32    = " << s.dbf_x32_root.string() << "\n"
        << "DBF_X64    = " << s.dbf_x64_root.string() << "\n"
        << "INDEXES    = " << s.indexes_root.string() << "\n"
        << "INDEX_X32  = " << s.indexes_x32_root.string() << "\n"
        << "INDEX_X64  = " << s.indexes_x64_root.string() << "\n"
        << "LMDB       = " << s.lmdb_root.string() << "\n"
        << "RAM        = " << s.ram_root.string() << "\n"
        << "WORKSPACES = " << s.workspaces_root.string() << "\n"
        << "SCHEMAS    = " << s.schemas_root.string() << "\n"
        << "PROJECTS   = " << s.projects_root.string() << "\n"
        << "SCRIPTS    = " << s.scripts_root.string() << "\n"
        << "TESTS      = " << s.tests_root.string() << "\n"
        << "HELP       = " << s.help_root.string() << "\n"
        << "LOGS       = " << s.logs_root.string() << "\n"
        << "TMP        = " << s.tmp_root.string() << "\n"
        << "TMP_OUT    = " << s.tmp_out_root.string() << "\n"
        << "TMP_SYSTEM = " << s.tmp_system_root.string() << "\n"
        << "USER       = " << s.user_root.string() << "\n"
        << "PUBLIC     = " << s.user_public_root.string() << "\n"
        << "DEFAULT    = " << s.user_default_root.string() << "\n"
        << "CURRENT    = " << s.user_current_root.string() << "\n"
        << "CUR_WORK   = " << s.cur_workspaces_root.string() << "\n"
        << "PUB_WORK   = " << s.pub_workspaces_root.string() << "\n"
        << "DEF_WORK   = " << s.def_workspaces_root.string() << "\n"
        << "DATA_WORK  = " << s.workspaces_root.string() << "\n"
        << "CUR_SCRIPT = " << s.cur_scripts_root.string() << "\n"
        << "PUB_SCRIPT = " << s.pub_scripts_root.string() << "\n"
        << "DEF_SCRIPT = " << s.def_scripts_root.string() << "\n"
        << "DATA_SCRIPT= " << s.scripts_root.string() << "\n";
    return out.str();
}

} // namespace dottalk::paths