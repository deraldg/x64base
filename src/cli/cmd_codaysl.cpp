// src/cli/cmd_codasyl.cpp
//
// CODASYL teaching adapter for LabTalk / DotTalk++
//
// Purpose:
//   - Provide a thin historical command veneer over the existing DotTalk++ runtime
//   - Simulate CODASYL-style OWNER / MEMBER / SET traversal without introducing
//     a second storage engine
//
// Current model:
//   - Uses already-open work areas
//   - Uses named "set" definitions (owner alias / member alias / fields)
//   - Traversal is computed dynamically by scanning the member area for matches
//   - "Ring" behavior is simulated by GET FIRST / GET NEXT over a snapshot vector
//
// Deliberate non-goals:
//   - No physical owner/member pointers
//   - No on-disk CODASYL storage
//   - No bypass of DbArea or the existing engine
//
// Notes:
//   - LOAD currently installs a predefined world definition only.
//     It does NOT auto-run SCHEMAS LOAD here. Keep this layer thin.
//   - This is a LabTalk-facing teaching command, not a new backend.

// @dottalk.usage v1
// owner: DOT|CODASYL
// command: CODASYL
// category: education
// status: supported
// noargs: usage
// effect: teaching
// mutates: codasyl-teaching-state cursor
// usage-access: CODASYL USAGE
// summary:
//   Provide a thin CODASYL teaching veneer over already-open DotTalk++ work areas,
//   simulating owner/member set traversal without a second storage engine.
//
// usage:
//   CODASYL USAGE
//   CODASYL HELP
//   CODASYL MODE ON
//   CODASYL MODE OFF
//   CODASYL LOAD <world>
//   CODASYL SETS
//   CODASYL SHOW SET <name>
//   CODASYL FIND OWNER <set> <value>
//   CODASYL FIND OWNER <owner_alias> <value>
//   CODASYL GET FIRST
//   CODASYL GET FIRST <set>
//   CODASYL GET FIRST <member_alias>
//   CODASYL GET NEXT
//   CODASYL GET NEXT <set>
//   CODASYL GET NEXT <member_alias>
//   CODASYL WALK
//   CODASYL WALK <set>
//   CODASYL WALK <member_alias>
//   CODASYL STATUS
//
// notes:
//   CODASYL with no arguments shows usage.
//   This is a teaching adapter and does not create physical CODASYL storage.
//   It uses already-open work areas and named set definitions.
//   LOAD installs a predefined set map for a named lesson world.
//   FIND OWNER captures the current owner and builds a member snapshot.
//   GET FIRST and GET NEXT move through the simulated member ring.
//   WALK prints a simulated owner/member ring and preserves the member-area cursor best-effort.
//   STATUS reports CODASYL teaching state.
//
// risk:
//   reads_open_work_areas: yes
//   changes_current_area_cursor: GET FIRST GET NEXT
//   restores_cursor_best_effort: WALK
//   mutates_table_data: no
//   creates_files: no
//   separate_storage_engine: no
//
// related:
//   WORKSPACE
//   REL
//   BROWSE
//   USE
//

#include <algorithm>
#include <cctype>
#include <filesystem>
#include <iostream>
#include <optional>
#include <sstream>
#include <string>
#include <vector>

#include "xbase.hpp"
#include "textio.hpp"
#include "cli/command_registry.hpp"

extern "C" xbase::XBaseEngine* shell_engine(void);

namespace fs = std::filesystem;

namespace {

struct CursorRestore {
    xbase::DbArea* area{nullptr};
    int32_t saved_recno{0};
    bool active{false};

    explicit CursorRestore(xbase::DbArea& a) : area(&a) {
        try {
            saved_recno = a.recno();
            active = (saved_recno >= 1 && saved_recno <= a.recCount());
        } catch (...) {
            active = false;
        }
    }

    ~CursorRestore() {
        if (!active || !area) return;
        try {
            if (saved_recno >= 1 && saved_recno <= area->recCount()) {
                (void)area->gotoRec(saved_recno);
                (void)area->readCurrent();
            }
        } catch (...) {
        }
    }

    CursorRestore(const CursorRestore&) = delete;
    CursorRestore& operator=(const CursorRestore&) = delete;
};

static std::string trim_copy(std::string s) {
    return textio::trim(std::move(s));
}

static std::string up_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
    }
    return s;
}

static std::string low_copy(std::string s) {
    for (auto& c : s) {
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    }
    return s;
}

static bool ieq(const std::string& a, const std::string& b) {
    return up_copy(a) == up_copy(b);
}

static std::vector<std::string> split_ws(const std::string& s) {
    std::vector<std::string> out;
    std::istringstream iss(s);
    for (std::string t; iss >> t; ) out.push_back(t);
    return out;
}

static void print_usage() {
    std::cout
        << "Usage:\n"
        << "  CODASYL USAGE\n"
        << "  CODASYL HELP\n"
        << "  CODASYL MODE ON\n"
        << "  CODASYL MODE OFF\n"
        << "  CODASYL LOAD <world>\n"
        << "  CODASYL SETS\n"
        << "  CODASYL SHOW SET <name>\n"
        << "  CODASYL FIND OWNER <set> <value>\n"
        << "  CODASYL FIND OWNER <owner_alias> <value>\n"
        << "  CODASYL GET FIRST [<set or member_alias>]\n"
        << "  CODASYL GET NEXT  [<set or member_alias>]\n"
        << "  CODASYL WALK      [<set or member_alias>]\n"
        << "  CODASYL STATUS\n"
        << "\n"
        << "Notes:\n"
        << "  - Thin teaching layer only; no physical CODASYL storage is created.\n"
        << "  - Assumes the relevant tables are already open in the workspace.\n"
        << "  - LOAD installs a predefined set map for a named lesson world.\n";
}

struct CodasylSetDef {
    std::string set_name;
    std::string owner_alias;
    std::string member_alias;
    std::string owner_field;
    std::string member_field;
    std::string note;
};

struct CodasylState {
    bool enabled{false};
    std::string world;

    std::vector<CodasylSetDef> sets;

    std::string current_set;
    std::string owner_alias;
    std::string member_alias;

    int current_owner_recno{0};
    std::vector<uint32_t> member_recnos;
    std::size_t member_index{0};
};

static CodasylState g_codasyl;

// -----------------------------------------------------------------------------
// World definitions
// -----------------------------------------------------------------------------

static std::vector<CodasylSetDef> make_world_mcc() {
    return {
        {"MAJOR_STUDENTS", "MAJORS",   "STUDENTS", "MAJOR",   "MAJOR",  "Major owner to student members"},
        {"STUD_ENROLL",    "STUDENTS", "ENROLL",   "SID",     "SID",    "Student owner to enrollment members"},
        {"ENROLL_CLASS",   "ENROLL",   "CLASSES",  "CLS_ID",  "CLS_ID", "Enrollment owner to class members"},
        {"CLASS_TASSIGN",  "CLASSES",  "TASSIGN",  "CLS_ID",  "CLS_ID", "Class owner to teaching assignment members"},
        {"TASSIGN_TEACH",  "TASSIGN",  "TEACHERS", "TID",     "TID",    "Teaching assignment owner to teacher members"},
        {"COURSE_DEPT",    "COURSES",  "DEPT",     "DEPT_ID", "DEPT_ID","Course owner to department members"},
        {"ROOM_BUILDING",  "ROOMS",    "BUILDING", "BLDG",    "BLDG",   "Room owner to building members"}
    };
}

static std::vector<CodasylSetDef> make_world_factory() {
    // Teaching placeholder. Replace aliases/fields to match your manufacturing lab.
    return {
        {"PLANT_DEPT",     "PLANT",    "DEPT",      "PLANT_ID", "PLANT_ID", "Plant owner to department members"},
        {"DEPT_EMP",       "DEPT",     "EMPLOYEE",  "DEPT_ID",  "DEPT_ID",  "Department owner to employee members"},
        {"EMP_PAYROLL",    "EMPLOYEE", "PAYROLL",   "EMP_ID",   "EMP_ID",   "Employee owner to payroll members"},
        {"JOB_ROUTE",      "JOB",      "ROUTE",     "JOB_ID",   "JOB_ID",   "Job owner to routing members"},
        {"ITEM_INVENTORY", "ITEM",     "INVENTORY", "ITEM_ID",  "ITEM_ID",  "Item owner to inventory members"}
    };
}

static std::vector<CodasylSetDef> sets_for_world(const std::string& world) {
    const std::string w = up_copy(world);
    if (w == "MCC" || w == "COLLEGE") return make_world_mcc();
    if (w == "FACTORY" || w == "MFG" || w == "MANUFACTURING") return make_world_factory();
    return {};
}

// -----------------------------------------------------------------------------
// Area / field resolution
// -----------------------------------------------------------------------------

static std::string area_name_key(xbase::DbArea& A) {
    try {
        if (!A.logicalName().empty()) return up_copy(A.logicalName());
    } catch (...) {}

    try {
        if (!A.dbfBasename().empty()) return up_copy(A.dbfBasename());
    } catch (...) {}

    try {
        if (!A.name().empty()) {
            fs::path p(A.name());
            const std::string stem = p.stem().string();
            if (!stem.empty()) return up_copy(stem);
            return up_copy(A.name());
        }
    } catch (...) {}

    try {
        if (!A.filename().empty()) {
            fs::path p(A.filename());
            const std::string stem = p.stem().string();
            if (!stem.empty()) return up_copy(stem);
        }
    } catch (...) {}

    return {};
}

static xbase::DbArea* find_open_area_by_alias(const std::string& alias) {
    auto* eng = shell_engine();
    if (!eng) return nullptr;

    const std::string want = up_copy(alias);

    for (int i = 0; i < xbase::MAX_AREA; ++i) {
        xbase::DbArea& A = eng->area(i);
        if (!A.isOpen()) continue;

        if (area_name_key(A) == want) return &A;

        try {
            if (up_copy(A.logicalName()) == want) return &A;
        } catch (...) {}
        try {
            if (up_copy(A.dbfBasename()) == want) return &A;
        } catch (...) {}
    }

    return nullptr;
}

static int field_index_by_name(xbase::DbArea& A, const std::string& field_name) {
    try {
        const auto defs = A.fields();
        const std::string want = up_copy(field_name);

        for (std::size_t i = 0; i < defs.size(); ++i) {
            if (up_copy(defs[i].name) == want) {
                return static_cast<int>(i) + 1;
            }
        }
    } catch (...) {}

    return -1;
}

// -----------------------------------------------------------------------------
// Set resolution
// -----------------------------------------------------------------------------

static const CodasylSetDef* find_set_by_name(const std::string& set_name) {
    const std::string want = up_copy(set_name);
    for (const auto& s : g_codasyl.sets) {
        if (up_copy(s.set_name) == want) return &s;
    }
    return nullptr;
}

static const CodasylSetDef* find_first_set_by_owner_alias(const std::string& owner_alias) {
    const std::string want = up_copy(owner_alias);
    for (const auto& s : g_codasyl.sets) {
        if (up_copy(s.owner_alias) == want) return &s;
    }
    return nullptr;
}

static const CodasylSetDef* find_set_by_member_alias(const std::string& member_alias) {
    const std::string want = up_copy(member_alias);
    for (const auto& s : g_codasyl.sets) {
        if (up_copy(s.member_alias) == want) return &s;
    }
    return nullptr;
}

static const CodasylSetDef* resolve_set_reference(const std::string& token) {
    if (token.empty()) {
        if (g_codasyl.current_set.empty()) return nullptr;
        return find_set_by_name(g_codasyl.current_set);
    }

    if (const auto* s = find_set_by_name(token)) return s;
    if (const auto* s = find_set_by_member_alias(token)) return s;
    if (const auto* s = find_first_set_by_owner_alias(token)) return s;

    return nullptr;
}

// -----------------------------------------------------------------------------
// Traversal
// -----------------------------------------------------------------------------

static void clear_traversal_state() {
    g_codasyl.current_set.clear();
    g_codasyl.owner_alias.clear();
    g_codasyl.member_alias.clear();
    g_codasyl.current_owner_recno = 0;
    g_codasyl.member_recnos.clear();
    g_codasyl.member_index = 0;
}

static std::optional<std::string> current_owner_key_value(const CodasylSetDef& def) {
    xbase::DbArea* owner = find_open_area_by_alias(def.owner_alias);
    if (!owner || !owner->isOpen()) return std::nullopt;

    const int f1 = field_index_by_name(*owner, def.owner_field);
    if (f1 < 1) return std::nullopt;

    try {
        if (!owner->readCurrent()) return std::nullopt;
        return trim_copy(owner->get(f1));
    } catch (...) {
        return std::nullopt;
    }
}

static std::vector<uint32_t> collect_member_recnos_for_owner(const CodasylSetDef& def,
                                                             const std::string& owner_value) {
    std::vector<uint32_t> out;

    xbase::DbArea* member = find_open_area_by_alias(def.member_alias);
    if (!member || !member->isOpen()) return out;

    const int mf1 = field_index_by_name(*member, def.member_field);
    if (mf1 < 1) return out;

    CursorRestore restore(*member);

    const std::string want = up_copy(trim_copy(owner_value));
    const int32_t total = member->recCount();

    for (int32_t rn = 1; rn <= total; ++rn) {
        if (!member->gotoRec(rn)) continue;
        if (!member->readCurrent()) continue;

        const std::string got = up_copy(trim_copy(member->get(mf1)));
        if (got == want) {
            out.push_back(static_cast<uint32_t>(rn));
        }
    }

    return out;
}

static bool goto_member_recno(const CodasylSetDef& def, uint32_t rn) {
    xbase::DbArea* member = find_open_area_by_alias(def.member_alias);
    if (!member || !member->isOpen()) return false;
    if (!member->gotoRec(static_cast<int32_t>(rn))) return false;
    return member->readCurrent();
}

static void print_member_position(const CodasylSetDef& def, std::size_t pos, uint32_t rn) {
    xbase::DbArea* member = find_open_area_by_alias(def.member_alias);
    if (!member || !member->isOpen()) {
        std::cout << "CODASYL: member area not open: " << def.member_alias << "\n";
        return;
    }

    std::cout << "CODASYL GET: set=" << def.set_name
              << " owner=" << def.owner_alias << "#" << g_codasyl.current_owner_recno
              << " member=" << def.member_alias
              << " recno=" << rn
              << " position=" << (pos + 1) << " of " << g_codasyl.member_recnos.size()
              << "\n";
}

static bool refresh_current_member_snapshot(const CodasylSetDef& def) {
    xbase::DbArea* owner = find_open_area_by_alias(def.owner_alias);
    if (!owner || !owner->isOpen()) {
        std::cout << "CODASYL: owner area not open: " << def.owner_alias << "\n";
        return false;
    }

    const int owner_recno = owner->recno();
    if (owner_recno < 1 || owner_recno > owner->recCount()) {
        std::cout << "CODASYL: no current owner position in " << def.owner_alias << "\n";
        return false;
    }

    const auto key = current_owner_key_value(def);
    if (!key) {
        std::cout << "CODASYL: unable to read owner key " << def.owner_field << "\n";
        return false;
    }

    g_codasyl.current_set = def.set_name;
    g_codasyl.owner_alias = def.owner_alias;
    g_codasyl.member_alias = def.member_alias;
    g_codasyl.current_owner_recno = owner_recno;
    g_codasyl.member_recnos = collect_member_recnos_for_owner(def, *key);
    g_codasyl.member_index = 0;

    return true;
}

// -----------------------------------------------------------------------------
// Commands
// -----------------------------------------------------------------------------

static void codasyl_mode(const std::string& arg) {
    const std::string up = up_copy(trim_copy(arg));
    if (up == "ON") {
        g_codasyl.enabled = true;
        std::cout << "CODASYL MODE: ON\n";
        return;
    }
    if (up == "OFF") {
        g_codasyl.enabled = false;
        clear_traversal_state();
        std::cout << "CODASYL MODE: OFF\n";
        return;
    }
    std::cout << "Usage: CODASYL MODE ON|OFF\n";
}

static void codasyl_load(const std::string& arg) {
    const std::string world = trim_copy(arg);
    if (world.empty()) {
        std::cout << "Usage: CODASYL LOAD <world>\n";
        return;
    }

    // Preserve both normalizers deliberately:
    //   - low_copy() gives us a stable presentation/storage token for lesson worlds.
    //   - sets_for_world() remains case-insensitive internally through up_copy().
    // This keeps the teaching command tolerant of MCC/mcc/Mcc without leaving
    // low_copy() as a dead helper.
    const std::string world_key = low_copy(world);

    auto sets = sets_for_world(world_key);
    if (sets.empty()) {
        std::cout << "CODASYL LOAD: unknown world '" << world << "'.\n";
        return;
    }

    g_codasyl.enabled = true;
    g_codasyl.world = up_copy(world_key);
    g_codasyl.sets = std::move(sets);
    clear_traversal_state();

    std::cout << "CODASYL LOAD: world " << g_codasyl.world
              << " loaded (" << g_codasyl.sets.size() << " set(s)).\n";
    std::cout << "Note: this installs the teaching set map only.\n";
    std::cout << "      Open the workspace/tables separately if not already open.\n";
}

static void codasyl_sets() {
    if (g_codasyl.sets.empty()) {
        std::cout << "CODASYL SETS: no world loaded.\n";
        return;
    }

    std::cout << "CODASYL SETS (" << g_codasyl.world << ")\n";
    for (const auto& s : g_codasyl.sets) {
        std::cout << "  " << s.set_name
                  << "  OWNER=" << s.owner_alias
                  << "  MEMBER=" << s.member_alias
                  << "  KEY=" << s.owner_field << "=" << s.member_field
                  << "\n";
    }
}

static void codasyl_show_set(const std::string& arg) {
    const std::string set_name = trim_copy(arg);
    if (set_name.empty()) {
        std::cout << "Usage: CODASYL SHOW SET <name>\n";
        return;
    }

    const auto* s = find_set_by_name(set_name);
    if (!s) {
        std::cout << "CODASYL SHOW SET: unknown set '" << set_name << "'.\n";
        return;
    }

    std::cout << "SET: " << s->set_name << "\n";
    std::cout << "  OWNER : " << s->owner_alias << "\n";
    std::cout << "  MEMBER: " << s->member_alias << "\n";
    std::cout << "  KEY   : " << s->owner_field << " = " << s->member_field << "\n";
    if (!s->note.empty()) {
        std::cout << "  NOTE  : " << s->note << "\n";
    }
}

static void codasyl_find_owner(const std::string& arg) {
    auto toks = split_ws(arg);
    if (toks.size() < 2) {
        std::cout << "Usage: CODASYL FIND OWNER <set|owner_alias> <value>\n";
        return;
    }

    const std::string ref = toks[0];
    std::string value = trim_copy(arg.substr(arg.find(ref) + ref.size()));
    value = trim_copy(value);
    if (value.empty()) {
        std::cout << "Usage: CODASYL FIND OWNER <set|owner_alias> <value>\n";
        return;
    }

    // Strip surrounding quotes, if present.
    value = textio::unquote(value);

    const auto* def = resolve_set_reference(ref);
    if (!def) {
        std::cout << "CODASYL FIND OWNER: unknown set/owner '" << ref << "'.\n";
        return;
    }

    xbase::DbArea* owner = find_open_area_by_alias(def->owner_alias);
    if (!owner || !owner->isOpen()) {
        std::cout << "CODASYL FIND OWNER: owner area not open: " << def->owner_alias << "\n";
        return;
    }

    const int of1 = field_index_by_name(*owner, def->owner_field);
    if (of1 < 1) {
        std::cout << "CODASYL FIND OWNER: owner field not found: " << def->owner_field << "\n";
        return;
    }

    const std::string want = up_copy(trim_copy(value));
    CursorRestore restore(*owner);

    const int32_t total = owner->recCount();
    for (int32_t rn = 1; rn <= total; ++rn) {
        if (!owner->gotoRec(rn)) continue;
        if (!owner->readCurrent()) continue;

        const std::string got = up_copy(trim_copy(owner->get(of1)));
        if (got == want) {
            g_codasyl.current_set = def->set_name;
            g_codasyl.owner_alias = def->owner_alias;
            g_codasyl.member_alias = def->member_alias;
            g_codasyl.current_owner_recno = rn;
            g_codasyl.member_recnos.clear();
            g_codasyl.member_index = 0;

            // Leave owner positioned on the found record.
            restore.active = false;

            std::cout << "CODASYL FIND OWNER: set=" << def->set_name
                      << " owner=" << def->owner_alias
                      << " recno=" << rn
                      << " key=" << value
                      << "\n";
            return;
        }
    }

    std::cout << "CODASYL FIND OWNER: no owner found for value '" << value << "'.\n";
}

static void codasyl_get_first(const std::string& arg) {
    const auto* def = resolve_set_reference(trim_copy(arg));
    if (!def) {
        std::cout << "CODASYL GET FIRST: no set selected.\n";
        return;
    }

    if (!refresh_current_member_snapshot(*def)) return;

    if (g_codasyl.member_recnos.empty()) {
        std::cout << "CODASYL GET FIRST: no members in set " << def->set_name << ".\n";
        return;
    }

    g_codasyl.member_index = 0;
    const uint32_t rn = g_codasyl.member_recnos[g_codasyl.member_index];

    if (!goto_member_recno(*def, rn)) {
        std::cout << "CODASYL GET FIRST: failed to position member recno " << rn << ".\n";
        return;
    }

    print_member_position(*def, g_codasyl.member_index, rn);
}

static void codasyl_get_next(const std::string& arg) {
    const auto* def = resolve_set_reference(trim_copy(arg));
    if (!def) {
        std::cout << "CODASYL GET NEXT: no set selected.\n";
        return;
    }

    if (g_codasyl.current_set.empty() || !ieq(g_codasyl.current_set, def->set_name)) {
        if (!refresh_current_member_snapshot(*def)) return;
        if (g_codasyl.member_recnos.empty()) {
            std::cout << "CODASYL GET NEXT: no members in set " << def->set_name << ".\n";
            return;
        }
        g_codasyl.member_index = 0;
    } else if (g_codasyl.member_recnos.empty()) {
        if (!refresh_current_member_snapshot(*def)) return;
        if (g_codasyl.member_recnos.empty()) {
            std::cout << "CODASYL GET NEXT: no members in set " << def->set_name << ".\n";
            return;
        }
    } else {
        g_codasyl.member_index = (g_codasyl.member_index + 1) % g_codasyl.member_recnos.size();
    }

    const uint32_t rn = g_codasyl.member_recnos[g_codasyl.member_index];

    if (!goto_member_recno(*def, rn)) {
        std::cout << "CODASYL GET NEXT: failed to position member recno " << rn << ".\n";
        return;
    }

    print_member_position(*def, g_codasyl.member_index, rn);
}

static void codasyl_walk(const std::string& arg) {
    const auto* def = resolve_set_reference(trim_copy(arg));
    if (!def) {
        std::cout << "CODASYL WALK: no set selected.\n";
        return;
    }

    if (!refresh_current_member_snapshot(*def)) return;

    xbase::DbArea* owner = find_open_area_by_alias(def->owner_alias);
    xbase::DbArea* member = find_open_area_by_alias(def->member_alias);
    if (!owner || !member) {
        std::cout << "CODASYL WALK: owner/member area unavailable.\n";
        return;
    }

    const int owner_f1 = field_index_by_name(*owner, def->owner_field);
    const int member_show_f1 = 1; // keep simple for now; display first field if available
    const int member_name_f1 = field_index_by_name(*member, def->member_field);

    std::cout << "SET: " << def->set_name << "\n";
    std::cout << "  OWNER : " << def->owner_alias << " recno " << g_codasyl.current_owner_recno;

    if (owner_f1 >= 1) {
        try {
            if (owner->readCurrent()) {
                std::cout << "  key=" << owner->get(owner_f1);
            }
        } catch (...) {}
    }
    std::cout << "\n";

    if (g_codasyl.member_recnos.empty()) {
        std::cout << "  RING  : (no members)\n";
        return;
    }

    std::cout << "  RING\n";
    CursorRestore restore(*member);

    for (std::size_t i = 0; i < g_codasyl.member_recnos.size(); ++i) {
        const uint32_t rn = g_codasyl.member_recnos[i];
        std::cout << "    " << (i + 1) << " -> " << def->member_alias
                  << " recno " << rn;

        try {
            if (member->gotoRec(static_cast<int32_t>(rn)) && member->readCurrent()) {
                if (member_show_f1 >= 1 && member_show_f1 <= member->fieldCount()) {
                    std::cout << "  first_field=" << member->get(member_show_f1);
                }
                if (member_name_f1 >= 1 && member_name_f1 <= member->fieldCount()) {
                    std::cout << "  key=" << member->get(member_name_f1);
                }
            }
        } catch (...) {}

        std::cout << "\n";
    }

    std::cout << "    -> (back to first)\n";
}

static void codasyl_status() {
    std::cout << "CODASYL STATUS\n";
    std::cout << "  MODE          : " << (g_codasyl.enabled ? "ON" : "OFF") << "\n";
    std::cout << "  WORLD         : " << (g_codasyl.world.empty() ? "(none)" : g_codasyl.world) << "\n";
    std::cout << "  SET COUNT     : " << g_codasyl.sets.size() << "\n";
    std::cout << "  CURRENT SET   : " << (g_codasyl.current_set.empty() ? "(none)" : g_codasyl.current_set) << "\n";
    std::cout << "  OWNER         : " << (g_codasyl.owner_alias.empty() ? "(none)" : g_codasyl.owner_alias) << "\n";
    std::cout << "  MEMBER        : " << (g_codasyl.member_alias.empty() ? "(none)" : g_codasyl.member_alias) << "\n";
    std::cout << "  OWNER RECNO   : " << g_codasyl.current_owner_recno << "\n";
    std::cout << "  MEMBER COUNT  : " << g_codasyl.member_recnos.size() << "\n";
    if (!g_codasyl.member_recnos.empty()) {
        std::cout << "  MEMBER INDEX  : " << (g_codasyl.member_index + 1)
                  << " of " << g_codasyl.member_recnos.size() << "\n";
    }
}

} // namespace

void cmd_CODASYL(xbase::DbArea& area, std::istringstream& iss)
{
    (void)area;

    std::string sub;
    iss >> sub;
    const std::string SUB = up_copy(sub);

    std::string rest;
    std::getline(iss >> std::ws, rest);
    rest = trim_copy(rest);

    if (SUB.empty() || SUB == "USAGE" || SUB == "HELP" || SUB == "?" || SUB == "/?" || SUB == "-H" || SUB == "--HELP") {
        print_usage();
        return;
    }

    if (SUB == "MODE") {
        codasyl_mode(rest);
        return;
    }

    if (SUB == "LOAD") {
        codasyl_load(rest);
        return;
    }

    if (SUB == "SETS") {
        codasyl_sets();
        return;
    }

    if (SUB == "SHOW") {
        auto toks = split_ws(rest);
        if (toks.size() >= 2 && ieq(toks[0], "SET")) {
            codasyl_show_set(rest.substr(rest.find(toks[1])));
            return;
        }
        std::cout << "Usage: CODASYL SHOW SET <name>\n";
        return;
    }

    if (SUB == "FIND") {
        auto toks = split_ws(rest);
        if (!toks.empty() && ieq(toks[0], "OWNER")) {
            std::string arg = trim_copy(rest.substr(rest.find(toks[0]) + toks[0].size()));
            codasyl_find_owner(arg);
            return;
        }
        std::cout << "Usage: CODASYL FIND OWNER <set|owner_alias> <value>\n";
        return;
    }

    if (SUB == "GET") {
        auto toks = split_ws(rest);
        if (toks.empty()) {
            std::cout << "Usage: CODASYL GET FIRST|NEXT [<set|member_alias>]\n";
            return;
        }

        const std::string which = up_copy(toks[0]);
        std::string arg;
        if (rest.size() > toks[0].size()) {
            arg = trim_copy(rest.substr(toks[0].size()));
        }

        if (which == "FIRST") {
            codasyl_get_first(arg);
            return;
        }
        if (which == "NEXT") {
            codasyl_get_next(arg);
            return;
        }

        std::cout << "Usage: CODASYL GET FIRST|NEXT [<set|member_alias>]\n";
        return;
    }

    if (SUB == "WALK") {
        codasyl_walk(rest);
        return;
    }

    if (SUB == "STATUS") {
        codasyl_status();
        return;
    }

    std::cout << "CODASYL: unknown subcommand '" << sub << "'.\n";
    print_usage();
}

static bool s_registered = []() {
    dli::registry().add("CODASYL", &cmd_CODASYL);
    return true;
}();