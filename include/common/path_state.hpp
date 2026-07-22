// common/path_state.hpp
#pragma once

#include <filesystem>
#include <optional>
#include <string>
#include <vector>

namespace dottalk::paths {

namespace fs = std::filesystem;

enum class Slot {
    BIN,
    DATA,
    DOCS,
    SYSTEM_DIAGRAMS,
    DIAGRAMS = SYSTEM_DIAGRAMS,
    USER_DIAGRAMS,
    DBF,
    XDBF,
    xDBF = XDBF,
    DBF_X32,
    DBF_X64,
    INDEXES,
    INDEXES_X32,
    INDEXES_X64,
    LMDB,
    RAM,            // AIF-043 in-memory tables: relocatable virtual-disk root
    WORKSPACES,
    SCHEMAS,
    PROJECTS,
    SCRIPTS,
    TESTS,
    HELP,
    LOGS,
    TMP,
    TMP_OUT,
    TMP_SYSTEM,

    USER,
    USER_PUBLIC,
    USER_DEFAULT,
    USER_CURRENT,

    PUB_WORKSPACES,
    PUB_SCRIPTS,
    PUB_SECURITY,
    PUB_STORAGE,
    PUB_PREFS,
    PUB_LOGS,
    PUB_TMP,

    DEF_WORKSPACES,
    DEF_SCRIPTS,
    DEF_SECURITY,
    DEF_STORAGE,
    DEF_PREFS,
    DEF_LOGS,
    DEF_TMP,

    CUR_WORKSPACES,
    CUR_SCRIPTS,
    CUR_SECURITY,
    CUR_STORAGE,
    CUR_PREFS,
    CUR_LOGS,
    CUR_TMP
};

struct State {
    fs::path root;
    fs::path bin_root;
    fs::path data_root;
    fs::path docs_root;
    fs::path system_diagrams_root;
    fs::path user_diagrams_root;

    fs::path dbf_root;
    fs::path xdbf_root;
    fs::path dbf_x32_root;
    fs::path dbf_x64_root;

    fs::path indexes_root;
    fs::path indexes_x32_root;
    fs::path indexes_x64_root;

    fs::path lmdb_root;
    fs::path ram_root;
    fs::path workspaces_root;
    fs::path schemas_root;
    fs::path projects_root;
    fs::path scripts_root;
    fs::path tests_root;
    fs::path help_root;
    fs::path logs_root;
    fs::path tmp_root;
    fs::path tmp_out_root;
    fs::path tmp_system_root;

    fs::path user_root;
    fs::path user_public_root;
    fs::path user_default_root;
    fs::path user_current_root;

    fs::path pub_workspaces_root;
    fs::path pub_scripts_root;
    fs::path pub_security_root;
    fs::path pub_storage_root;
    fs::path pub_prefs_root;
    fs::path pub_logs_root;
    fs::path pub_tmp_root;

    fs::path def_workspaces_root;
    fs::path def_scripts_root;
    fs::path def_security_root;
    fs::path def_storage_root;
    fs::path def_prefs_root;
    fs::path def_logs_root;
    fs::path def_tmp_root;

    fs::path cur_workspaces_root;
    fs::path cur_scripts_root;
    fs::path cur_security_root;
    fs::path cur_storage_root;
    fs::path cur_prefs_root;
    fs::path cur_logs_root;
    fs::path cur_tmp_root;

    std::string current_user = "default";
};

State& state();

void initialize(const fs::path& bin_root,
                const fs::path& data_root,
                std::string current_user = "default");

void initialize_from_bin(const fs::path& bin_root,
                         std::string current_user = "default");

void set_current_user(std::string current_user);
const std::string& current_user();

fs::path get_slot(Slot slot);
void set_slot(Slot slot, const fs::path& value);
void set_slot_from_value(Slot slot, const fs::path& value);

// legacy compatibility expected by SETPATH
void reset();
void init_defaults(const fs::path& data_root);
std::string dump();

std::optional<Slot> slot_from_string(const std::string& name);
bool slot_from_string(const std::string& name, Slot& out);
std::string slot_name(Slot slot);

std::vector<fs::path> workspace_search_roots();
std::vector<fs::path> script_search_roots();

void ensure_directories();
std::string describe();

} // namespace dottalk::paths